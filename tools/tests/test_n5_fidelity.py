"""Tests for tools/n5-fidelity.py: per-class semantic decompiler fidelity grading.

Stages (strict TDD, RED before each stage's implementation existed):
  1. bytecode normalizer (CP-index stripping, local-slot canonicalization,
     branch-target canonicalization) on synthetic javap-style text.
  2. structural comparator (fields / methods / class attributes) on synthetic
     parsed-class dicts.
  3. grader decisions (roundtrip-exact / roundtrip-equivalent / compiles-mismatch
     / no-compile / bytecode-only) including the allowlist mechanism.
  4. fallback/redundancy selection ladder (vineflower -> cfr -> procyon -> jd-cli).
  5. krak2 independent disassembly cross-check of the normalizer.
  6. consensus field + niagara_help.py member-set agreement.

Fixtures under tools/tests/fixtures/n5_fidelity/*.java are tiny synthetic classes
compiled with the local JDK in setUp(); any test that needs a real compiler or
`javap` is skipped (not failed) when that toolchain is absent, per the task's
"tests must not require the installs" constraint. Nothing here downloads or
touches the real N5 corpus.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-fidelity.py")
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "n5_fidelity")

JDK25_JAVAC = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac"
JDK25_JAVAP = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javap"


def _load():
    spec = importlib.util.spec_from_file_location("n5_fidelity", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    # register before exec: n5-fidelity.py uses @dataclass, whose introspection
    # needs sys.modules[cls.__module__] to resolve during class body execution
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _jdk_available():
    return os.path.isfile(JDK25_JAVAC) and os.path.isfile(JDK25_JAVAP)


def _krak2_available():
    return shutil.which("krak2") is not None


# ---------------------------------------------------------------------------
# Stage 1: normalizer
# ---------------------------------------------------------------------------
class TestStripCpIndices(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_drops_bare_method_ref_index(self):
        line = "         1: invokespecial #1                  // Method niagara/control/BNumericPoint.\"<init>\":()V"
        out = self.mod.strip_cp_indices(line)
        self.assertNotIn("#1", out)
        self.assertIn("invokespecial", out)
        self.assertIn('Method niagara/control/BNumericPoint."<init>":()V', out)

    def test_drops_double_index_class_field_form(self):
        line = "    #12 = Fieldref           #13.#14       // niagara/control/BNumericWritable.support:Lniagara/control/WritableSupport;"
        out = self.mod.strip_cp_indices(line)
        self.assertNotIn("#13", out)
        self.assertNotIn("#14", out)

    def test_annotation_index_stripped_leaves_symbolic_line_untouched(self):
        line = "      0: #329()"
        out = self.mod.strip_cp_indices(line)
        self.assertNotIn("#329", out)

    def test_instruction_with_no_cp_reference_is_unchanged_besides_whitespace(self):
        line = "         0: aload_0"
        out = self.mod.strip_cp_indices(line)
        self.assertIn("aload_0", out)


class TestNormalizeMethodInstructions(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_local_slots_canonicalized_by_first_use_order(self):
        # slot 2 is used before slot 1 in this synthetic method -> canonical
        # order must be [2->0, 1->1], independent of the raw numbering.
        raw = [
            "0: aload_2",
            "1: aload_1",
            "2: return",
        ]
        out = self.mod.normalize_method_instructions(raw)
        # both slot-bearing instructions become the same canonical opcode shape
        # -- falsifiable: slot 2 is the FIRST use, so it must become canonical
        # slot 0 ("aload_0"), not stay "aload_2" (the raw form) or become
        # slot 1 (aload_1's raw number).
        self.assertEqual(out[0], "insn0: aload_0")
        self.assertNotEqual(out[0], raw[0])
        # re-running normalization on an equivalent method that swaps the raw
        # slot numbers (long operand form, since only slots 0-3 have a short
        # mnemonic form) but preserves first-use ORDER must produce identical output
        raw_equiv_relabeled = [
            "0: aload         5",
            "1: aload         9",
            "2: return",
        ]
        out2 = self.mod.normalize_method_instructions(raw_equiv_relabeled)
        self.assertEqual(out, out2)

    def test_branch_targets_canonicalized_relative_to_instruction_position(self):
        raw = [
            "0: aload_0",
            "1: ifnull        12",
            "4: iconst_1",
            "5: goto          15",
            "12: iconst_0",
            "15: return",
        ]
        out = self.mod.normalize_method_instructions(raw)
        # a semantically identical method compiled with different (but
        # order-preserving) byte offsets must normalize identically
        raw_shifted = [
            "0: aload_0",
            "1: ifnull        20",
            "10: iconst_1",
            "11: goto          25",
            "20: iconst_0",
            "25: return",
        ]
        out2 = self.mod.normalize_method_instructions(raw_shifted)
        self.assertEqual(out, out2)

    def test_different_control_flow_shape_is_not_normalized_equal(self):
        raw_a = [
            "0: aload_0",
            "1: ifnull        12",
            "4: iconst_1",
            "5: goto          15",
            "12: iconst_0",
            "15: return",
        ]
        raw_b = [
            "0: aload_0",
            "1: ifnonnull     12",  # different opcode -> genuinely different
            "4: iconst_1",
            "5: goto          15",
            "12: iconst_0",
            "15: return",
        ]
        out_a = self.mod.normalize_method_instructions(raw_a)
        out_b = self.mod.normalize_method_instructions(raw_b)
        self.assertNotEqual(out_a, out_b)

    def test_switch_case_keys_are_preserved_not_normalized_away(self):
        # lookupswitch is printed by javap as a MULTI-LINE block; each
        # "<key>: <target>" row is switch OPERAND data, not a separate
        # instruction — it must not corrupt offset->position numbering for
        # the instructions that follow it (regression: a naive per-line
        # "<digits>: <mnemonic>" match treats "5: 28" as a fake instruction).
        raw = [
            "0: iload_1",
            "1: lookupswitch  { // 2",
            "               5: 28",
            "             200: 31",
            "         default: 34",
            "      }",
            "28: bipush        10",
            "30: ireturn",
            "31: bipush        20",
            "33: ireturn",
            "34: iconst_m1",
            "35: ireturn",
        ]
        out = self.mod.normalize_method_instructions(raw)
        joined = "\n".join(out)
        # case keys are semantic (which input selects which branch) and must
        # survive normalization literally
        self.assertIn("5", joined)
        self.assertIn("200", joined)
        # the instruction immediately after the switch block must be
        # recognized at its own canonical position, not swallowed/misaligned
        self.assertIn("bipush", joined)
        self.assertEqual(sum(1 for l in out if "bipush" in l), 2)

    def test_switch_with_swapped_key_target_mapping_is_not_normalized_equal(self):
        raw_a = [
            "0: iload_1",
            "1: lookupswitch  { // 2",
            "               5: 20",
            "               6: 23",
            "         default: 26",
            "      }",
            "20: bipush        1",
            "22: ireturn",
            "23: bipush        2",
            "25: ireturn",
            "26: iconst_m1",
            "27: ireturn",
        ]
        raw_b = [
            "0: iload_1",
            "1: lookupswitch  { // 2",
            "               5: 23",  # case 5 now targets what case 6 used to
            "               6: 20",
            "         default: 26",
            "      }",
            "20: bipush        1",
            "22: ireturn",
            "23: bipush        2",
            "25: ireturn",
            "26: iconst_m1",
            "27: ireturn",
        ]
        out_a = self.mod.normalize_method_instructions(raw_a)
        out_b = self.mod.normalize_method_instructions(raw_b)
        self.assertNotEqual(out_a, out_b)

    def test_negative_switch_case_keys_are_not_silently_dropped(self):
        # javap prints negative case keys bare, e.g. "-5: 36" (verified against
        # a real javac 25 compile) -- the old case-row regex only matched
        # \d+ keys, so a negative-key arm's "<key>: <target>" row failed to
        # match _SWITCH_CASE_RE and was silently skipped by _parse_code_stream
        # (never added to `entries`). Two methods differing ONLY in a
        # negative-key arm's target must NOT normalize equal (regression: the
        # old code produced this false-exact by dropping the row entirely).
        raw_a = [
            "0: iload_1",
            "1: lookupswitch  { // 2",
            "              -5: 36",
            "              -1: 41",
            "         default: 46",
            "      }",
            "36: bipush        1",
            "38: ireturn",
            "41: bipush        2",
            "43: ireturn",
            "46: iconst_m1",
            "47: ireturn",
        ]
        raw_b = [
            "0: iload_1",
            "1: lookupswitch  { // 2",
            "              -5: 41",  # -5 now targets what -1 used to target
            "              -1: 36",
            "         default: 46",
            "      }",
            "36: bipush        1",
            "38: ireturn",
            "41: bipush        2",
            "43: ireturn",
            "46: iconst_m1",
            "47: ireturn",
        ]
        out_a = self.mod.normalize_method_instructions(raw_a)
        out_b = self.mod.normalize_method_instructions(raw_b)
        self.assertNotEqual(out_a, out_b)
        # the negative key itself is semantic and must survive literally
        self.assertIn("-5", "\n".join(out_a))
        self.assertIn("-1", "\n".join(out_a))

    def test_iinc_with_comma_separated_operand_is_slot_canonicalized(self):
        # javap prints iinc as "iinc          2, 3" (comma-separated, verified
        # against a real javac 25 compile) -- the old regex required plain
        # whitespace between the slot and the increment amount, so it never
        # matched and the raw slot number leaked through uncanonicalized. Two
        # methods referencing the SAME local in the SAME first-use order, but
        # assigned different raw slot numbers by their respective compiles,
        # must still normalize identically once the iinc slot is canonicalized.
        raw_a = [
            "0: iload_1",
            "1: iinc          1, 3",
            "4: ireturn",
        ]
        raw_b = [
            "0: iload         4",  # javap has no short form past slot 3
            "1: iinc          4, 3",
            "4: ireturn",
        ]
        out_a = self.mod.normalize_method_instructions(raw_a)
        out_b = self.mod.normalize_method_instructions(raw_b)
        self.assertEqual(out_a, out_b)
        # the increment amount is semantic and must survive literally
        self.assertIn("3", "\n".join(out_a))

    def test_switch_case_target_shift_is_normalized_equal(self):
        # same key->target STRUCTURE, shifted absolute byte offsets
        raw_a = [
            "0: iload_1",
            "1: lookupswitch  { // 1",
            "               5: 15",
            "         default: 18",
            "      }",
            "15: bipush        1",
            "17: ireturn",
            "18: iconst_m1",
            "19: ireturn",
        ]
        raw_b = [
            "0: iload_1",
            "1: lookupswitch  { // 1",
            "               5: 30",
            "         default: 40",
            "      }",
            "30: bipush        1",
            "39: ireturn",
            "40: iconst_m1",
            "41: ireturn",
        ]
        out_a = self.mod.normalize_method_instructions(raw_a)
        out_b = self.mod.normalize_method_instructions(raw_b)
        self.assertEqual(out_a, out_b)

    def test_constant_pool_index_stripped_inside_instruction_stream(self):
        raw = [
            "0: aload_0",
            "1: getfield      #7                  // Field x:I",
            "4: ireturn",
        ]
        out = self.mod.normalize_method_instructions(raw)
        joined = "\n".join(out)
        self.assertNotIn("#7", joined)
        self.assertIn("Field x:I", joined)


# ---------------------------------------------------------------------------
# Stage 2: structural comparator
# ---------------------------------------------------------------------------
class TestExceptionTableNormalization(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_handler_type_mismatch_is_not_normalized_equal(self):
        raw = [
            "0: bipush 10",
            "2: iload_1",
            "3: idiv",
            "4: ireturn",
            "5: astore_2",
            "6: iconst_m1",
            "7: ireturn",
        ]
        rows_a = [(0, 4, 5, "Class java/lang/ArithmeticException")]
        rows_b = [(0, 4, 5, "Class java/io/IOException")]
        out_a = self.mod.normalize_exception_table(raw, rows_a)
        out_b = self.mod.normalize_exception_table(raw, rows_b)
        self.assertNotEqual(out_a, out_b)

    def test_shifted_offsets_with_same_structure_normalize_equal(self):
        # same instruction COUNT and POSITIONS, only the raw byte offsets
        # differ (e.g. a wide-operand encoding elsewhere in the constant pool
        # shifting every subsequent offset by a constant) — this must compare
        # equal, unlike an actual extra/missing instruction (a genuine
        # structural difference, which correctly does NOT compare equal).
        raw_a = ["0: bipush 10", "2: iload_1", "3: idiv", "4: ireturn", "5: astore_2", "6: iconst_m1", "7: ireturn"]
        raw_b = ["10: bipush 10", "12: iload_1", "13: idiv", "14: ireturn", "15: astore_2", "16: iconst_m1", "17: ireturn"]
        rows_a = [(0, 4, 5, "Class java/lang/ArithmeticException")]
        rows_b = [(10, 14, 15, "Class java/lang/ArithmeticException")]
        out_a = self.mod.normalize_exception_table(raw_a, rows_a)
        out_b = self.mod.normalize_exception_table(raw_b, rows_b)
        self.assertEqual(out_a, out_b)

    def test_extra_instruction_changes_structure_and_is_not_normalized_equal(self):
        # unlike a pure offset shift, an inserted instruction changes the
        # instruction COUNT/positions — the exception range genuinely covers
        # different code, and must not be silently treated as equivalent.
        raw_a = ["0: bipush 10", "2: iload_1", "3: idiv", "4: ireturn", "5: astore_2", "6: iconst_m1", "7: ireturn"]
        raw_b = ["0: bipush 10", "2: nop", "3: iload_1", "4: idiv", "5: ireturn", "6: astore_2", "7: iconst_m1", "8: ireturn"]
        rows_a = [(0, 4, 5, "Class java/lang/ArithmeticException")]
        rows_b = [(0, 5, 6, "Class java/lang/ArithmeticException")]
        out_a = self.mod.normalize_exception_table(raw_a, rows_a)
        out_b = self.mod.normalize_exception_table(raw_b, rows_b)
        self.assertNotEqual(out_a, out_b)

    def test_no_handlers_normalizes_to_empty_list(self):
        raw = ["0: return"]
        self.assertEqual(self.mod.normalize_exception_table(raw, []), [])


class TestParseJavapVerbose(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_exception_table_row_included_in_parsed_method(self):
        text = (
            "Classfile /tmp/Foo.class\n"
            "public class Foo\n"
            "  minor version: 0\n"
            "  major version: 69\n"
            "Constant pool:\n"
            "    #1 = Utf8 x\n"
            "{\n"
            "  public int compute(int);\n"
            "    descriptor: (I)I\n"
            "    flags: (0x0001) ACC_PUBLIC\n"
            "    Code:\n"
            "      stack=2, locals=3, args_size=2\n"
            "         0: bipush        10\n"
            "         2: iload_1\n"
            "         3: idiv\n"
            "         4: ireturn\n"
            "         5: astore_2\n"
            "         6: iconst_m1\n"
            "         7: ireturn\n"
            "      Exception table:\n"
            "         from    to  target type\n"
            "             0     4     5   Class java/lang/ArithmeticException\n"
            "      LineNumberTable:\n"
            "        line 1: 0\n"
            "}\n"
        )
        parsed = self.mod.parse_javap_verbose(text)
        method = parsed["methods"][("compute", "(I)I")]
        self.assertEqual(len(method["exception_table"]), 1)
        self.assertIn("ArithmeticException", method["exception_table"][0])
        # and the raw exception-table rows never leaked into the instruction stream
        self.assertFalse(any("ArithmeticException" in c for c in method["code"]))
        self.assertFalse(any(c.strip().startswith("from") for c in method["code"]))

    def test_static_initializer_parses_to_clinit_key(self):
        text = (
            "Classfile /tmp/Foo.class\n"
            "  Last modified Jan 1, 2026\n"
            "  SHA-256 checksum aaaa\n"
            "  Compiled from \"Foo.java\"\n"
            "public class Foo\n"
            "  minor version: 0\n"
            "  major version: 69\n"
            "Constant pool:\n"
            "    #1 = Utf8 x\n"
            "{\n"
            "  static {};\n"
            "    descriptor: ()V\n"
            "    flags: (0x0008) ACC_STATIC\n"
            "    Code:\n"
            "      stack=1, locals=0, args_size=0\n"
            "         0: return\n"
            "}\n"
        )
        parsed = self.mod.parse_javap_verbose(text)
        self.assertIn(("<clinit>", "()V"), parsed["methods"])


class TestDiffNormalizedClasses(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def _base_class(self):
        return {
            "class_decl": "public class Foo",
            "fields": {
                ("x", "I"): {"flags": ["ACC_PRIVATE"], "constant_value": None},
            },
            "methods": {
                ("bar", "()V"): {"flags": ["ACC_PUBLIC"], "code": ["0: return"], "exceptions": []},
            },
            "attributes": {
                "record": False,
                "permitted_subclasses": None,
                "nest_members": None,
                "inner_classes": None,
            },
        }

    def test_identical_classes_diff_clean(self):
        a = self._base_class()
        b = self._base_class()
        diff = self.mod.diff_normalized_classes(a, b)
        self.assertTrue(diff["fields_match"])
        self.assertTrue(diff["attrs_match"])
        self.assertEqual(diff["mismatched_methods"], [])
        self.assertEqual(diff["missing_methods"], [])
        self.assertEqual(diff["extra_methods"], [])

    def test_method_body_difference_reported_by_key(self):
        a = self._base_class()
        b = self._base_class()
        b["methods"][("bar", "()V")]["code"] = ["0: iconst_0", "1: return"]
        diff = self.mod.diff_normalized_classes(a, b)
        self.assertEqual(diff["mismatched_methods"], [("bar", "()V")])

    def test_missing_method_reported(self):
        a = self._base_class()
        b = self._base_class()
        del b["methods"][("bar", "()V")]
        diff = self.mod.diff_normalized_classes(a, b)
        self.assertEqual(diff["missing_methods"], [("bar", "()V")])

    def test_field_set_mismatch_reported(self):
        a = self._base_class()
        b = self._base_class()
        b["fields"][("y", "I")] = {"flags": ["ACC_PRIVATE"], "constant_value": None}
        diff = self.mod.diff_normalized_classes(a, b)
        self.assertFalse(diff["fields_match"])

    def test_constant_value_mismatch_reported(self):
        a = self._base_class()
        b = self._base_class()
        a["fields"][("x", "I")]["constant_value"] = "5"
        b["fields"][("x", "I")]["constant_value"] = "6"
        diff = self.mod.diff_normalized_classes(a, b)
        self.assertFalse(diff["fields_match"])

    def test_nest_members_mismatch_reported(self):
        a = self._base_class()
        b = self._base_class()
        b["attributes"]["nest_members"] = ["Foo$Inner"]
        diff = self.mod.diff_normalized_classes(a, b)
        self.assertFalse(diff["attrs_match"])


# ---------------------------------------------------------------------------
# Stage 3: grader decisions (incl. allowlist mechanism)
# ---------------------------------------------------------------------------
class TestGradeFromDiff(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_no_compile_when_recompile_failed(self):
        grade = self.mod.grade_class_result(compiled_ok=False, diff=None, first_error="cannot find symbol")
        self.assertEqual(grade["grade"], "no-compile")
        self.assertEqual(grade["first_error"], "cannot find symbol")

    def test_roundtrip_exact_when_diff_clean(self):
        diff = {
            "fields_match": True, "attrs_match": True,
            "mismatched_methods": [], "missing_methods": [], "extra_methods": [],
        }
        grade = self.mod.grade_class_result(compiled_ok=True, diff=diff, first_error=None)
        self.assertEqual(grade["grade"], "roundtrip-exact")

    def test_compiles_mismatch_when_method_body_genuinely_differs(self):
        diff = {
            "fields_match": True, "attrs_match": True,
            "mismatched_methods": [("bar", "()V")], "missing_methods": [], "extra_methods": [],
        }
        grade = self.mod.grade_class_result(compiled_ok=True, diff=diff, first_error=None)
        self.assertEqual(grade["grade"], "compiles-mismatch")
        self.assertEqual(grade["mismatched_methods"], [("bar", "()V")])

    def test_roundtrip_equivalent_when_only_allowlisted_pattern_differs(self):
        # a mismatch that the allowlist recognizes as safe must downgrade the
        # grade to roundtrip-equivalent and record which allowlist entry matched
        diff = {
            "fields_match": True, "attrs_match": True,
            "mismatched_methods": [("bar", "()V")], "missing_methods": [], "extra_methods": [],
            "method_bodies": {
                ("bar", "()V"): {
                    "a": ["0: invokedynamic InvokeDynamic makeConcatWithConstants:(...)"],
                    "b": ["0: invokedynamic InvokeDynamic makeConcatWithConstants:(...) "],
                }
            },
        }
        # register a trivial always-true allowlist entry for this test only
        self.mod.ALLOWLIST.append(
            self.mod.AllowlistEntry(
                name="test-whitespace-only",
                justification="unit-test-only: trailing whitespace never changes semantics",
                predicate=lambda a, b: [x.rstrip() for x in a] == [x.rstrip() for x in b],
            )
        )
        try:
            grade = self.mod.grade_class_result(compiled_ok=True, diff=diff, first_error=None)
        finally:
            self.mod.ALLOWLIST.pop()
        self.assertEqual(grade["grade"], "roundtrip-equivalent")
        self.assertEqual(grade["allowlist_matches"], ["test-whitespace-only"])

    def test_missing_or_extra_member_is_never_allowlisted(self):
        diff = {
            "fields_match": True, "attrs_match": True,
            "mismatched_methods": [], "missing_methods": [("bar", "()V")], "extra_methods": [],
        }
        grade = self.mod.grade_class_result(compiled_ok=True, diff=diff, first_error=None)
        self.assertEqual(grade["grade"], "compiles-mismatch")


class TestWideVariantAllowlist(unittest.TestCase):
    """JVMS 6.5: ldc/ldc_w, goto/goto_w, jsr/jsr_w each perform the IDENTICAL
    runtime operation -- only the operand-encoding WIDTH differs, a pure
    compiler encoding choice (constant-pool size for ldc, branch-offset range
    for goto/jsr), never semantic. A standalone single-class recompile (this
    grader's method) has a different local pool/offset size than the shipped
    module-wide compile, so it can legitimately pick a different width for
    the SAME constant/target -- a recompile-isolation artifact, not a
    decompiler-fidelity defect. See ALLOWLIST in tools/n5-fidelity.py.
    """

    def setUp(self):
        self.mod = _load()

    def test_ldc_vs_ldc_w_on_the_same_constant_is_allowlisted(self):
        entry = next(e for e in self.mod.ALLOWLIST if e.name == "ldc-vs-ldc_w-width")
        a = ["insn0: ldc // String foo", "insn1: areturn"]
        b = ["insn0: ldc_w // String foo", "insn1: areturn"]
        self.assertTrue(entry.predicate(a, b))

    def test_ldc_vs_ldc_w_on_a_DIFFERENT_constant_is_not_allowlisted(self):
        # falsifiable negative: same instruction pair, but the loaded
        # constant genuinely differs -- must NOT be waved through
        entry = next(e for e in self.mod.ALLOWLIST if e.name == "ldc-vs-ldc_w-width")
        a = ["insn0: ldc // String foo", "insn1: areturn"]
        b = ["insn0: ldc_w // String bar", "insn1: areturn"]
        self.assertFalse(entry.predicate(a, b))

    def test_goto_vs_goto_w_on_the_same_target_is_allowlisted(self):
        entry = next(e for e in self.mod.ALLOWLIST if e.name == "goto-vs-goto_w-width")
        a = ["insn0: iconst_0", "insn1: goto rel+2", "insn2: nop", "insn3: return"]
        b = ["insn0: iconst_0", "insn1: goto_w rel+2", "insn2: nop", "insn3: return"]
        self.assertTrue(entry.predicate(a, b))

    def test_goto_vs_goto_w_to_a_DIFFERENT_target_is_not_allowlisted(self):
        entry = next(e for e in self.mod.ALLOWLIST if e.name == "goto-vs-goto_w-width")
        a = ["insn0: iconst_0", "insn1: goto rel+2", "insn2: nop", "insn3: return"]
        b = ["insn0: iconst_0", "insn1: goto_w rel+1", "insn2: nop", "insn3: return"]
        self.assertFalse(entry.predicate(a, b))

    def test_jsr_vs_jsr_w_on_the_same_target_is_allowlisted(self):
        entry = next(e for e in self.mod.ALLOWLIST if e.name == "jsr-vs-jsr_w-width")
        a = ["insn0: jsr rel+3", "insn1: return"]
        b = ["insn0: jsr_w rel+3", "insn1: return"]
        self.assertTrue(entry.predicate(a, b))

    def test_jsr_vs_jsr_w_to_a_DIFFERENT_target_is_not_allowlisted(self):
        entry = next(e for e in self.mod.ALLOWLIST if e.name == "jsr-vs-jsr_w-width")
        a = ["insn0: jsr rel+3", "insn1: return"]
        b = ["insn0: jsr_w rel+9", "insn1: return"]
        self.assertFalse(entry.predicate(a, b))

    def test_an_unrelated_opcode_change_alongside_ldc_width_is_not_allowlisted(self):
        # the predicate must not accidentally wave through a genuine mismatch
        # just because an ldc/ldc_w pair ALSO happens to be present
        entry = next(e for e in self.mod.ALLOWLIST if e.name == "ldc-vs-ldc_w-width")
        a = ["insn0: ldc // String foo", "insn1: ireturn"]
        b = ["insn0: ldc_w // String foo", "insn1: areturn"]
        self.assertFalse(entry.predicate(a, b))

    def test_different_instruction_counts_are_never_allowlisted(self):
        entry = next(e for e in self.mod.ALLOWLIST if e.name == "ldc-vs-ldc_w-width")
        a = ["insn0: ldc // String foo", "insn1: areturn"]
        b = ["insn0: ldc_w // String foo", "insn1: nop", "insn2: areturn"]
        self.assertFalse(entry.predicate(a, b))

    def test_identical_code_is_not_matched_by_the_predicate(self):
        # not a mismatch at all -- grade_class_result never even consults the
        # allowlist for a clean diff, but the predicate itself should not
        # claim credit for "explaining" a non-difference
        entry = next(e for e in self.mod.ALLOWLIST if e.name == "ldc-vs-ldc_w-width")
        same = ["insn0: ldc // String foo", "insn1: areturn"]
        self.assertFalse(entry.predicate(list(same), list(same)))

    def test_end_to_end_ldc_width_mismatch_grades_roundtrip_equivalent(self):
        diff = {
            "fields_match": True, "attrs_match": True,
            "mismatched_methods": [("bar", "()Ljava/lang/String;")], "missing_methods": [], "extra_methods": [],
            "method_bodies": {
                ("bar", "()Ljava/lang/String;"): {
                    "a": ["insn0: ldc // String foo", "insn1: areturn"],
                    "b": ["insn0: ldc_w // String foo", "insn1: areturn"],
                }
            },
        }
        grade = self.mod.grade_class_result(compiled_ok=True, diff=diff, first_error=None)
        self.assertEqual(grade["grade"], "roundtrip-equivalent")
        self.assertIn("ldc-vs-ldc_w-width", grade["allowlist_matches"])


# ---------------------------------------------------------------------------
# Stage 4: fallback / redundancy ladder selection
# ---------------------------------------------------------------------------
class TestFallbackLadder(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_first_clean_engine_is_selected_as_best_decompiler(self):
        # vineflower fails, cfr reaches roundtrip-equivalent, procyon never tried
        attempts = [
            ("vineflower", {"grade": "compiles-mismatch"}),
            ("cfr", {"grade": "roundtrip-equivalent"}),
            ("procyon", {"grade": "roundtrip-exact"}),
        ]
        result = self.mod.select_best_decompiler(attempts)
        self.assertEqual(result["best_decompiler"], "cfr")
        self.assertEqual(result["grade"], "roundtrip-equivalent")
        # every engine that was actually attempted is recorded (redundancy/disagreement trail)
        self.assertEqual([n for n, _ in result["attempted"]], ["vineflower", "cfr", "procyon"])

    def test_no_clean_engine_falls_back_to_bytecode_only(self):
        attempts = [
            ("vineflower", {"grade": "compiles-mismatch"}),
            ("cfr", {"grade": "no-compile"}),
            ("procyon", {"grade": "compiles-mismatch"}),
        ]
        result = self.mod.select_best_decompiler(attempts)
        self.assertEqual(result["best_decompiler"], None)
        self.assertEqual(result["grade"], "bytecode-only")

    def test_ladder_short_circuits_and_does_not_run_later_engines(self):
        calls = []

        def make_engine(name, grade):
            def _run():
                calls.append(name)
                return {"grade": grade}
            return _run

        ladder = [
            ("vineflower", make_engine("vineflower", "roundtrip-exact")),
            ("cfr", make_engine("cfr", "roundtrip-exact")),
            ("procyon", make_engine("procyon", "roundtrip-exact")),
        ]
        result = self.mod.run_redundancy_ladder(ladder)
        self.assertEqual(calls, ["vineflower"])
        self.assertEqual(result["best_decompiler"], "vineflower")

    def test_ladder_continues_past_failing_engines(self):
        calls = []

        def make_engine(name, grade):
            def _run():
                calls.append(name)
                return {"grade": grade}
            return _run

        ladder = [
            ("vineflower", make_engine("vineflower", "no-compile")),
            ("cfr", make_engine("cfr", "compiles-mismatch")),
            ("procyon", make_engine("procyon", "roundtrip-exact")),
        ]
        result = self.mod.run_redundancy_ladder(ladder)
        self.assertEqual(calls, ["vineflower", "cfr", "procyon"])
        self.assertEqual(result["best_decompiler"], "procyon")


# ---------------------------------------------------------------------------
# Stage 5: krak2 independent cross-check of the normalizer
# ---------------------------------------------------------------------------
class TestDecompileOneClassWithCliContract(unittest.TestCase):
    """Each redundancy-ladder engine has its own single-class CLI contract
    (verified against the real jars in setUp/manual exploration — see
    docs/decompile-fidelity-report.md). A wrong flag silently produces zero
    output, which the ladder would then misreport as `no-compile` for an
    engine that was never actually invoked correctly — so the exact argv is
    worth locking down per engine, not just "did something get called".
    """

    def setUp(self):
        self.mod = _load()

    def _run_with_fake_tool(self, jar_name, engine):
        with tempfile.TemporaryDirectory() as td:
            tool_jar = Path(td) / jar_name
            tool_jar.write_bytes(b"not a real jar, just needs to exist")
            classfile = Path(td) / "Foo.class"
            classfile.write_bytes(b"")
            out_dir = Path(td) / "out"
            with mock.patch.object(self.mod.subprocess, "run") as run_mock:
                run_mock.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                self.mod._decompile_one_class_with("java", engine, tool_jar, classfile, out_dir)
            self.assertEqual(run_mock.call_count, 1)
            return run_mock.call_args[0][0]

    def test_cfr_uses_outputdir_flag(self):
        argv = self._run_with_fake_tool("cfr-0.152.jar", "cfr")
        self.assertIn("--outputdir", argv)
        self.assertNotIn("-od", argv)

    def test_procyon_uses_bare_dash_o_flag(self):
        argv = self._run_with_fake_tool("procyon-decompiler-0.6.0.jar", "procyon")
        self.assertIn("-o", argv)
        self.assertNotIn("--outputdir", argv)
        self.assertNotIn("-od", argv)

    def test_jd_cli_uses_dash_od_before_the_class_argument(self):
        argv = self._run_with_fake_tool("jd-cli.jar", "jd-cli")
        self.assertIn("-od", argv)
        # jd-cli's own CLI contract: -od <dir> must precede the file argument,
        # and the class file (last positional) must come after it
        self.assertTrue(argv[-1].endswith("Foo.class"))
        self.assertLess(argv.index("-od"), len(argv) - 1)

    def test_engine_selection_ignores_jar_filename_and_uses_the_explicit_engine_argument(self):
        # regression: engine selection used to be inferred from a substring
        # match on the jar's OWN filename ("cfr" in name / "jd-cli" in name /
        # else procyon) -- a jar renamed or differently pinned than expected
        # silently got the WRONG CLI contract. This jar's name says nothing
        # about which engine it is; only the explicit `engine` argument may
        # decide the CLI contract.
        argv = self._run_with_fake_tool("totally-unrelated-name.jar", "cfr")
        self.assertIn("--outputdir", argv)

    def test_unrecognized_engine_raises_instead_of_silently_defaulting_to_procyon(self):
        # the old filename-substring dispatch fell through to Procyon's flags
        # for ANYTHING that didn't match "cfr"/"jd-cli" -- silently. An
        # unrecognized engine must fail loudly, never guess.
        with tempfile.TemporaryDirectory() as td:
            tool_jar = Path(td) / "whatever.jar"
            tool_jar.write_bytes(b"not a real jar")
            classfile = Path(td) / "Foo.class"
            classfile.write_bytes(b"")
            with self.assertRaises(ValueError):
                self.mod._decompile_one_class_with("java", "not-a-real-engine", tool_jar, classfile, Path(td) / "out")

    def test_subprocess_timeout_returns_typed_timeout_reason(self):
        with tempfile.TemporaryDirectory() as td:
            tool_jar = Path(td) / "cfr.jar"
            tool_jar.write_bytes(b"not a real jar")
            classfile = Path(td) / "Foo.class"
            classfile.write_bytes(b"")
            with mock.patch.object(
                self.mod.subprocess, "run",
                side_effect=self.mod.subprocess.TimeoutExpired(cmd="java", timeout=1),
            ):
                result_path, reason = self.mod._decompile_one_class_with(
                    "java", "cfr", tool_jar, classfile, Path(td) / "out"
                )
            self.assertIsNone(result_path)
            self.assertEqual(reason, "timeout")


class TestKrak2CrossCheck(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_unavailable_when_krak2_binary_missing(self):
        result = self.mod.krak2_cross_check(
            "/nonexistent/Foo.class", ["insn0: return"], "foo", "()V", krak2_bin="/nonexistent/krak2"
        )
        self.assertEqual(result["status"], "unavailable")

    @unittest.skipUnless(_krak2_available(), "krak2 not installed")
    @unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
    def test_matches_normalizer_opcode_sequence_on_real_class(self):
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "Plain.java")
            with open(src, "w") as f:
                f.write(
                    "public class Plain {\n"
                    "    public int add(int a, int b) {\n"
                    "        if (a > b) { return a; }\n"
                    "        return b;\n"
                    "    }\n"
                    "}\n"
                )
            subprocess.run([JDK25_JAVAC, "--release", "25", "-g", "-d", td, src], check=True, capture_output=True)
            classfile = os.path.join(td, "Plain.class")
            # run_javap_instructions already returns the NORMALIZED code for one
            # method (it is what parse_javap_verbose stores per method) — the
            # cross-check compares that against an independently-disassembled
            # (krak2), un-normalized view of the SAME method, scoped by name+descriptor
            # so the class's other methods (e.g. the implicit constructor) never
            # pollute the comparison.
            normalized = self.mod.run_javap_instructions(classfile, "add", "(II)I", javap_bin=JDK25_JAVAP)
            result = self.mod.krak2_cross_check(classfile, normalized, "add", "(II)I")
            self.assertIn(result["status"], ("match", "mismatch"))
            # opcode mnemonic sequence (ignoring operands) must agree with an
            # independent disassembler on genuinely trivial, unambiguous code
            self.assertEqual(result["status"], "match")

    @unittest.skipUnless(_krak2_available(), "krak2 not installed")
    @unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
    def test_works_on_a_packaged_class_not_just_default_package(self):
        # regression: krak2 writes its .j output under <outdir>/<package-path>/,
        # exactly like javac's own -d output (see recompile_and_grade's earlier
        # fix) — a plain glob("*.j") at the top of the temp outdir only finds a
        # DEFAULT-PACKAGE class's output; every real N5 class is packaged
        # (com.tridium.*, niagara.*, ...), so this silently marked the krak2
        # cross-check "unavailable" for the entire real corpus.
        with tempfile.TemporaryDirectory() as td:
            src_dir = os.path.join(td, "pkg")
            os.makedirs(src_dir)
            src = os.path.join(src_dir, "Packaged.java")
            with open(src, "w") as f:
                f.write(
                    "package pkg;\n"
                    "public class Packaged {\n"
                    "    public int add(int a, int b) { return a + b; }\n"
                    "}\n"
                )
            subprocess.run([JDK25_JAVAC, "--release", "25", "-g", "-d", td, src], check=True, capture_output=True)
            classfile = os.path.join(td, "pkg", "Packaged.class")
            normalized = self.mod.run_javap_instructions(classfile, "add", "(II)I", javap_bin=JDK25_JAVAP)
            result = self.mod.krak2_cross_check(classfile, normalized, "add", "(II)I")
            self.assertEqual(result["status"], "match")

    @unittest.skipUnless(_krak2_available(), "krak2 not installed")
    @unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
    def test_constructor_falls_back_to_init_for_krak2_lookup(self):
        # parse_javap_verbose keys a constructor by the enclosing class's
        # simple name (matching javap's own printed declaration, e.g.
        # "public Packaged(int);"), but krak2's .j disassembly names every
        # constructor "<init>" — without a fallback, every constructor method
        # would show as krak2-"unavailable", which is exactly what the real
        # corpus sample showed before this fix.
        with tempfile.TemporaryDirectory() as td:
            src_dir = os.path.join(td, "pkg")
            os.makedirs(src_dir)
            src = os.path.join(src_dir, "Ctor.java")
            with open(src, "w") as f:
                f.write("package pkg;\npublic class Ctor {\n    public Ctor(int a) { }\n}\n")
            subprocess.run([JDK25_JAVAC, "--release", "25", "-g", "-d", td, src], check=True, capture_output=True)
            classfile = os.path.join(td, "pkg", "Ctor.class")
            normalized = self.mod.run_javap_instructions(classfile, "Ctor", "(I)V", javap_bin=JDK25_JAVAP)
            result = self.mod.krak2_cross_check(classfile, normalized, "Ctor", "(I)V")
            self.assertEqual(result["status"], "match")


# ---------------------------------------------------------------------------
# Stage 6: consensus field + niagara_help.py member-set agreement
# ---------------------------------------------------------------------------
class TestConsensus(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_consensus_counts_engines_reaching_roundtrip(self):
        attempted = [
            ("vineflower", {"grade": "roundtrip-exact"}),
            ("cfr", {"grade": "compiles-mismatch"}),
            ("procyon", {"grade": "roundtrip-equivalent"}),
        ]
        consensus = self.mod.compute_consensus(attempted)
        self.assertEqual(consensus["reaching_roundtrip"], ["vineflower", "procyon"])
        self.assertEqual(consensus["count"], 2)

    def test_consensus_zero_when_nothing_round_trips(self):
        attempted = [
            ("vineflower", {"grade": "compiles-mismatch"}),
            ("cfr", {"grade": "no-compile"}),
        ]
        consensus = self.mod.compute_consensus(attempted)
        self.assertEqual(consensus["count"], 0)
        self.assertEqual(consensus["reaching_roundtrip"], [])


class TestSampleIndependentCrossChecks(unittest.TestCase):
    """The per-module grading loop only does the expensive recompile-based
    grade; krak2 and niagara_help.py cross-checks are sampled separately at
    report time (sample_independent_cross_checks) so they don't slow down
    every single class of a full/sampled corpus run.
    """

    def setUp(self):
        self.mod = _load()

    def test_samples_are_capped_and_deterministic(self):
        module_results = [
            {
                "module": "m1",
                "classes": {"a/A": {}, "a/B": {}, "a/C": {}},
            },
            {
                "module": "m2",
                "classes": {"b/D": {}},
            },
        ]
        with mock.patch.object(self.mod, "parse_javap_verbose", return_value={"fields": {}, "methods": {}}), \
             mock.patch.object(self.mod, "run_javap_verbose", return_value=""), \
             mock.patch("os.path.isfile", return_value=True):
            first = self.mod.sample_independent_cross_checks(module_results, sample_size=2, seed=1)
            second = self.mod.sample_independent_cross_checks(module_results, sample_size=2, seed=1)
        self.assertEqual(len(first["sampled"]), 2)
        self.assertEqual(first["sampled"], second["sampled"])

    def test_member_check_recorded_when_slot_fields_and_docs_both_available(self):
        module_results = [{"module": "control", "classes": {"niagara/control/BNumericWritable": {}}}]
        parsed = {
            "fields": {("in1", "Lniagara/sys/Property;"): {}},
            "methods": {},
        }
        with mock.patch.object(self.mod, "parse_javap_verbose", return_value=parsed), \
             mock.patch.object(self.mod, "run_javap_verbose", return_value=""), \
             mock.patch.object(self.mod, "niagara_help_member_lookup", return_value={"in1", "extra"}), \
             mock.patch("os.path.isfile", return_value=True):
            result = self.mod.sample_independent_cross_checks(module_results, sample_size=1)
        self.assertEqual(len(result["member_checks"]), 1)
        self.assertEqual(result["member_checks"][0]["agreement"]["ratio"], 1.0)

    def test_krak2_check_recorded_for_first_method_when_available(self):
        module_results = [{"module": "m", "classes": {"p/C": {}}}]
        parsed = {
            "fields": {},
            "methods": {("foo", "()V"): {"code": ["insn0: return"]}},
        }
        with mock.patch.object(self.mod, "parse_javap_verbose", return_value=parsed), \
             mock.patch.object(self.mod, "run_javap_verbose", return_value=""), \
             mock.patch.object(self.mod, "krak2_cross_check", return_value={"status": "match"}), \
             mock.patch("os.path.isfile", return_value=True):
            result = self.mod.sample_independent_cross_checks(module_results, sample_size=1)
        self.assertEqual(len(result["krak2_checks"]), 1)
        self.assertEqual(result["krak2_checks"][0]["status"], "match")


class TestMemberSetAgreement(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_agreement_ratio_full_match(self):
        ours = {("foo", "()V"), ("bar", "(I)V")}
        theirs = {"foo", "bar"}
        result = self.mod.member_set_agreement(ours, theirs)
        self.assertEqual(result["ratio"], 1.0)
        self.assertEqual(result["missing_from_docs"], [])

    def test_agreement_ratio_partial_match_reports_gaps(self):
        ours = {("foo", "()V"), ("bar", "(I)V"), ("baz", "()V")}
        theirs = {"foo", "bar"}
        result = self.mod.member_set_agreement(ours, theirs)
        self.assertAlmostEqual(result["ratio"], 2 / 3)
        self.assertEqual(result["missing_from_docs"], ["baz"])

    def test_niagara_help_lookup_returns_none_when_tool_missing(self):
        members = self.mod.niagara_help_member_lookup(
            "niagara.control.BNumericWritable", niagara_help_script="/nonexistent/niagara_help.py"
        )
        self.assertIsNone(members)

    @unittest.skipUnless(
        os.path.isfile(os.path.join(TOOLS_DIR, "..", "niagara-help", "tools", "niagara_help.py")),
        "niagara-help/ (gitignored local bajadoc index) not present",
    )
    def test_niagara_help_lookup_on_real_class_matches_known_slots(self):
        members = self.mod.niagara_help_member_lookup("niagara.control.BNumericWritable")
        self.assertIsNotNone(members)
        # BNumericWritable's 16 numbered inputs are a stable, documented part
        # of this class's public contract (see docs/decompiler-bakeoff.md's
        # own control-module sampling) — a regression in the CLI's output
        # format would silently zero out slot_field_names cross-checks.
        self.assertIn("in1", members)
        self.assertIn("auto", members)

    def test_slot_field_names_selects_only_property_action_topic_fields(self):
        parsed = {
            "fields": {
                ("in1", "Lniagara/sys/Property;"): {},
                ("auto", "Lniagara/sys/Action;"): {},
                ("changed", "Lniagara/sys/Topic;"): {},
                ("support", "Lniagara/control/WritableSupport;"): {},
            }
        }
        selected = self.mod.slot_field_names(parsed)
        self.assertEqual(
            selected,
            {
                ("in1", "Lniagara/sys/Property;"),
                ("auto", "Lniagara/sys/Action;"),
                ("changed", "Lniagara/sys/Topic;"),
            },
        )


# ---------------------------------------------------------------------------
# End-to-end: real compile via the local JDK, no N5 install required
# ---------------------------------------------------------------------------
class TestGenerateReportBytecodeOnlyBreakdown(unittest.TestCase):
    """bytecode-only collapses two very different failure modes (a genuine
    cross-engine semantic mismatch vs. a class that never compiled on any
    engine, often a known single-class-isolation artifact) — the report must
    split them so a reader doesn't mistake a methodology limitation for a
    decompiler-fidelity defect.
    """

    def setUp(self):
        self.mod = _load()

    def test_splits_genuine_mismatch_from_compile_isolation_failure(self):
        module_results = [{
            "module": "m",
            "class_count": 3,
            "grade_counts": {"bytecode-only": 3},
            "classes": {
                "p/GenuineMismatch": {
                    "grade": "bytecode-only",
                    "attempted": [("vineflower", "compiles-mismatch"), ("cfr", "compiles-mismatch")],
                },
                "p/CompileIsolationOnly": {
                    "grade": "bytecode-only",
                    "attempted": [("vineflower", "no-compile"), ("cfr", "no-compile")],
                },
                "p/Mixed": {
                    "grade": "bytecode-only",
                    "attempted": [("vineflower", "no-compile"), ("cfr", "compiles-mismatch")],
                },
            },
        }]
        report = self.mod.generate_report(module_results)
        self.assertIn("genuine semantic mismatch", report)
        self.assertIn("p/GenuineMismatch", report)
        self.assertNotIn("p/CompileIsolationOnly\n", report.split("genuine semantic mismatch")[1].split("compile-isolation failure only")[0])
        self.assertIn("compile-isolation failure only (never compiled on any attempted engine): 1", report)
        self.assertIn("mixed (some engines compile-mismatch, some no-compile): 1", report)


class TestMainSurvivesOneModuleFailure(unittest.TestCase):
    """A single module blowing up (bad name, corrupt recon.json, an unhandled
    decompiler exception, ...) must not silently drop every OTHER module's
    already-computed grade, and must not skip --report for the whole batch —
    regression: an uncaught exception inside the ThreadPoolExecutor's mapped
    function previously propagated and killed the entire run before any
    report was written, even when N-1 other modules had already graded fine.

    It must ALSO be impossible to miss: main() exits non-zero
    (R4-module-failure-masked — the old code always returned 0, silently
    treating a grading failure as success), and the report shows the failure
    explicitly rather than an indistinguishable all-zero row.
    """

    def setUp(self):
        self.mod = _load()

    def test_one_module_raising_does_not_abort_the_batch_or_skip_the_report(self):
        with tempfile.TemporaryDirectory() as td:
            organized_dir = Path(td)
            for name in ("good", "bad"):
                mod_dir = organized_dir / name
                (mod_dir / "extracted").mkdir(parents=True)
                (mod_dir / "recon.json").write_text(json.dumps({"jar_sha256": f"sha-{name}"}))

            real_grade_module = self.mod.grade_module

            def fake_grade_module(module, **kwargs):
                if module == "bad":
                    raise RuntimeError("simulated corpus failure")
                return real_grade_module(module, **kwargs)

            report_path = organized_dir.parent / "report.md"
            with mock.patch.object(self.mod, "grade_module", side_effect=fake_grade_module), \
                 mock.patch.object(self.mod, "build_classpath", return_value=""), \
                 mock.patch.object(self.mod, "REPO_ROOT", organized_dir.parent):
                (organized_dir.parent / "docs").mkdir(exist_ok=True)
                rc = self.mod.main([
                    "--modules", "good,bad",
                    "--organized-dir", str(organized_dir),
                    "--classpath-cache-dir", str(organized_dir / "_cp"),
                    "--report",
                ])
            # a module failure must make the run exit non-zero, never silently 0
            self.assertEqual(rc, 1)
            good_fidelity = json.loads((organized_dir / "good" / "fidelity.vineflower.json").read_text())
            self.assertEqual(good_fidelity["module"], "good")
            self.assertFalse((organized_dir / "bad" / "fidelity.vineflower.json").exists())
            self.assertFalse((organized_dir / "bad" / "fidelity.json").exists())
            written_report = (organized_dir.parent / "docs" / "decompile-fidelity-report.md").read_text()
            self.assertIn("good", written_report)
            # the failure must be visible, not an indistinguishable zero row
            self.assertIn("Module failures", written_report)
            self.assertIn("bad", written_report.split("Module failures")[1])
            self.assertIn("simulated corpus failure", written_report)
            self.assertIn("GRADING FAILED", written_report)


class TestPrimaryTreeSelection(unittest.TestCase):
    """--tree lets the grader compare a second decompiled tree (e.g.
    'vineflower2', a library-context-aware pass some other writer produces)
    against the same ground-truth classes, without touching grade_module's
    default behavior for the normal 'vineflower' tree.
    """

    def setUp(self):
        self.mod = _load()

    def test_is_module_up_to_date_rejects_a_fidelity_json_from_a_different_tree(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            (mod_dir / "recon.json").write_text(json.dumps({"jar_sha256": "abc"}))
            (mod_dir / "fidelity.json").write_text(json.dumps({
                "schema_version": self.mod.SCHEMA_VERSION, "jar_sha256": "abc", "primary_tree": "vineflower",
            }))
            self.assertTrue(self.mod.is_module_up_to_date(mod_dir, primary_tree="vineflower"))
            self.assertFalse(self.mod.is_module_up_to_date(mod_dir, primary_tree="vineflower2"))

    def test_is_module_up_to_date_defaults_missing_primary_tree_to_vineflower(self):
        # a fidelity.json written before this field existed must still be
        # recognized as an up-to-date "vineflower" grade, not force a re-run
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            (mod_dir / "recon.json").write_text(json.dumps({"jar_sha256": "abc"}))
            (mod_dir / "fidelity.json").write_text(json.dumps({
                "schema_version": self.mod.SCHEMA_VERSION, "jar_sha256": "abc",
            }))
            self.assertTrue(self.mod.is_module_up_to_date(mod_dir, primary_tree="vineflower"))

    @unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
    def test_grade_module_reads_from_the_named_tree_directory(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td) / "fakemod"
            (mod_dir / "extracted" / "p").mkdir(parents=True)
            (mod_dir / "vineflower2" / "p").mkdir(parents=True)
            source = "package p;\npublic class Foo {\n    public int get() { return 42; }\n}\n"
            ground_dir = Path(td) / "ground"
            ground_src_dir = Path(td) / "ground_src" / "p"
            ground_src_dir.mkdir(parents=True)
            ground_src = ground_src_dir / "Foo.java"
            ground_src.write_text(source)
            subprocess.run([JDK25_JAVAC, "--release", "25", "-g", "-d", str(ground_dir), str(ground_src)],
                            check=True, capture_output=True)
            shutil.copy(ground_dir / "p" / "Foo.class", mod_dir / "extracted" / "p" / "Foo.class")
            (mod_dir / "vineflower2" / "p" / "Foo.java").write_text(source)
            # deliberately do NOT create a "vineflower" dir, so a fallback to
            # the wrong default would produce zero classes, not a false pass
            result = self.mod.grade_module(
                "fakemod", organized_dir=Path(td), classpath="", primary_tree="vineflower2",
                javac_bin=JDK25_JAVAC, javap_bin=JDK25_JAVAP,
            )
            self.assertEqual(result["primary_tree"], "vineflower2")
            self.assertEqual(result["classes"]["p/Foo"]["grade"], "roundtrip-exact")
            # regression: the redundancy ladder's first rung used to be
            # hardcoded as the literal string "vineflower" regardless of
            # --tree, so a vineflower2 grade was misattributed to vineflower
            # in `attempted` / `per_engine_mismatched_methods`.
            self.assertEqual(result["classes"]["p/Foo"]["attempted"][0][0], "vineflower2")

    @unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
    def test_grade_module_reports_harness_error_when_source_tree_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td) / "fakemod"
            (mod_dir / "extracted" / "p").mkdir(parents=True)
            source = "package p;\npublic class Foo { public int get() { return 42; } }\n"
            ground_dir = Path(td) / "ground"
            ground_src_dir = Path(td) / "ground_src" / "p"
            ground_src_dir.mkdir(parents=True)
            ground_src = ground_src_dir / "Foo.java"
            ground_src.write_text(source)
            subprocess.run([JDK25_JAVAC, "--release", "25", "-g", "-d", str(ground_dir), str(ground_src)],
                            check=True, capture_output=True)
            shutil.copy(ground_dir / "p" / "Foo.class", mod_dir / "extracted" / "p" / "Foo.class")
            # deliberately no "vineflower" (or any tree) dir at all
            result = self.mod.grade_module(
                "fakemod", organized_dir=Path(td), classpath="", primary_tree="vineflower",
                javac_bin=JDK25_JAVAC, javap_bin=JDK25_JAVAP,
            )
            self.assertEqual(result["classes"]["p/Foo"]["grade"], "harness-error")


class TestClassJobsParallelGrading(unittest.TestCase):
    """--class-jobs parallelizes per-class grading INSIDE one module; the
    result must be identical (content and key order) to the serial path."""

    NAMES = [f"C{i:02d}" for i in range(12)]

    def setUp(self):
        self.mod = _load()

    def _make_module(self, td):
        organized = Path(td)
        mod_dir = organized / "fakemod"
        (mod_dir / "extracted" / "p").mkdir(parents=True)
        (mod_dir / "vineflower" / "p").mkdir(parents=True)
        for n in self.NAMES:
            (mod_dir / "extracted" / "p" / f"{n}.class").write_bytes(b"x")
            (mod_dir / "vineflower" / "p" / f"{n}.java").write_text("class X {}")
        return organized

    def _fake_rag(self, fail_on=None):
        import random
        import time

        def fake(java_file, class_name, *a, **kw):
            time.sleep(random.random() * 0.01)
            if class_name == fail_on:
                raise RuntimeError("boom " + class_name)
            grade = "roundtrip-exact" if int(class_name[1:]) % 2 == 0 else "roundtrip-equivalent"
            return {"grade": grade, "first_error": None, "mismatched_methods": [], "allowlist_matches": []}
        return fake

    def test_class_jobs_matches_serial_content_and_order(self):
        with tempfile.TemporaryDirectory() as td:
            organized = self._make_module(td)
            with mock.patch.object(self.mod, "recompile_and_grade", side_effect=self._fake_rag()):
                serial = self.mod.grade_module("fakemod", organized_dir=organized, class_jobs=1)
                parallel = self.mod.grade_module("fakemod", organized_dir=organized, class_jobs=4)
            self.assertEqual(len(serial["classes"]), len(self.NAMES))
            self.assertEqual(list(parallel["classes"]), list(serial["classes"]))
            self.assertEqual(json.dumps(parallel, default=list), json.dumps(serial, default=list))

    def test_exception_in_one_class_propagates_with_class_jobs(self):
        with tempfile.TemporaryDirectory() as td:
            organized = self._make_module(td)
            with mock.patch.object(self.mod, "recompile_and_grade", side_effect=self._fake_rag(fail_on="C05")):
                with self.assertRaises(RuntimeError):
                    self.mod.grade_module("fakemod", organized_dir=organized, class_jobs=4)

    def test_main_passes_class_jobs_through(self):
        with tempfile.TemporaryDirectory() as td:
            organized_dir = Path(td)
            mod_dir = organized_dir / "m"
            (mod_dir / "extracted").mkdir(parents=True)
            (mod_dir / "recon.json").write_text(json.dumps({"jar_sha256": "sha-m"}))
            seen = {}

            def fake_grade_module(module, primary_tree="vineflower", limit=None, **kwargs):
                seen.update(kwargs)
                return {
                    "module": module, "schema_version": self.mod.SCHEMA_VERSION,
                    "jar_sha256": "sha-m", "primary_tree": primary_tree, "limit_per_module": limit,
                    "class_count": 0, "grade_counts": {}, "classes": {},
                }

            with mock.patch.object(self.mod, "grade_module", side_effect=fake_grade_module), \
                 mock.patch.object(self.mod, "build_classpath", return_value=""):
                rc = self.mod.main([
                    "--modules", "m", "--class-jobs", "3",
                    "--organized-dir", str(organized_dir),
                    "--classpath-cache-dir", str(organized_dir / "_cp"),
                ])
            self.assertEqual(rc, 0)
            self.assertEqual(seen.get("class_jobs"), 3)


class TestToolServer(unittest.TestCase):
    """--tool-server: javac/javap run in one long-lived in-process JVM per worker
    thread. Output must be byte-identical to the subprocess path."""

    SOURCE = (
        "package pk;\n"
        "public class Tiny {\n"
        "    private final int x;\n"
        "    public Tiny(int x) { this.x = x; }\n"
        "    public int getX() { return x + 1; }\n"
        "}\n"
    )
    JAVAC_OPTS = ["--release", "25", "-g", "-implicit:none", "-proc:none", "-nowarn"]

    def setUp(self):
        if not _jdk_available():
            self.skipTest("JDK 25 (javac/javap) not installed at the pinned brew path")
        self.mod = _load()
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)
        self.addCleanup(self.mod.shutdown_tool_servers)
        self.src = os.path.join(self.tmpdir, "Tiny.java")
        with open(self.src, "w") as f:
            f.write(self.SOURCE)

    def _server(self):
        server = self.mod.ToolServer(java_bin=self.mod.DEFAULT_JAVA)
        self.addCleanup(server.close)
        return server

    def _subprocess_compile(self, out_dir):
        os.makedirs(out_dir)
        subprocess.run([JDK25_JAVAC, *self.JAVAC_OPTS, "-d", out_dir, self.src], check=True, capture_output=True)
        return os.path.join(out_dir, "pk", "Tiny.class")

    def test_large_output_beyond_pipe_buffer_round_trips(self):
        # regression: raw unbuffered pipe reads return short; javap -v of a JDK class is >100 KB
        expected = subprocess.run([JDK25_JAVAP, "-v", "-p", "java.lang.String"], capture_output=True, text=True).stdout
        self.assertGreater(len(expected), 200_000)
        rc, out, err = self._server().run("javap", ["-v", "-p", "java.lang.String"], timeout=120)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out, expected)

    def test_javac_via_server_is_byte_identical_to_subprocess(self):
        ref = self._subprocess_compile(os.path.join(self.tmpdir, "ref"))
        srv_out = os.path.join(self.tmpdir, "srv")
        os.makedirs(srv_out)
        server = self._server()
        rc, out, err = server.run("javac", [*self.JAVAC_OPTS, "-d", srv_out, self.src], timeout=60)
        self.assertEqual(rc, 0, err)
        with open(ref, "rb") as a, open(os.path.join(srv_out, "pk", "Tiny.class"), "rb") as b:
            self.assertEqual(a.read(), b.read())

    def test_javac_error_text_and_exit_code_round_trip(self):
        bad = os.path.join(self.tmpdir, "Bad.java")
        with open(bad, "w") as f:
            f.write("class Bad { int f() { return \"\u00e9\"; } }\n")
        out_dir = os.path.join(self.tmpdir, "o")
        os.makedirs(out_dir)
        proc = subprocess.run([JDK25_JAVAC, *self.JAVAC_OPTS, "-d", out_dir, bad], capture_output=True, text=True)
        server = self._server()
        rc, out, err = server.run("javac", [*self.JAVAC_OPTS, "-d", out_dir, bad], timeout=60)
        self.assertNotEqual(rc, 0)
        self.assertEqual(rc, proc.returncode)
        self.assertEqual(err, proc.stderr)

    def test_javap_via_server_text_equals_subprocess(self):
        ref = self._subprocess_compile(os.path.join(self.tmpdir, "ref"))
        expected = self.mod.run_javap_verbose(ref, javap_bin=JDK25_JAVAP)
        got = self.mod.run_javap_verbose(ref, javap_bin=JDK25_JAVAP, tool_server=True)
        self.assertEqual(got, expected)
        self.assertIn("getX", got)

    def test_timeout_restarts_server_and_grade_is_timeout(self):
        server = self._server()
        out_dir = os.path.join(self.tmpdir, "t")
        os.makedirs(out_dir)
        with self.assertRaises(subprocess.TimeoutExpired):
            server.run("javac", [*self.JAVAC_OPTS, "-d", out_dir, self.src], timeout=0.001)
        rc, _, err = server.run("javac", [*self.JAVAC_OPTS, "-d", out_dir, self.src], timeout=60)
        self.assertEqual(rc, 0, err)
        ref = self._subprocess_compile(os.path.join(self.tmpdir, "ref"))
        result = self.mod.recompile_and_grade(
            self.src, "Tiny", "", ref, os.path.join(self.tmpdir, "g"),
            javac_bin=JDK25_JAVAC, javap_bin=JDK25_JAVAP, javac_timeout=0.001, tool_server=True,
        )
        self.assertEqual(result["grade"], "timeout")

    def test_server_start_failure_falls_back_to_subprocess_with_identical_grade(self):
        ref = self._subprocess_compile(os.path.join(self.tmpdir, "ref"))
        baseline = self.mod.recompile_and_grade(
            self.src, "Tiny", "", ref, os.path.join(self.tmpdir, "g1"),
            javac_bin=JDK25_JAVAC, javap_bin=JDK25_JAVAP,
        )
        with mock.patch.object(self.mod, "TOOL_SERVER_SRC", os.path.join(self.tmpdir, "missing", "ToolServer.java")):
            self.mod.shutdown_tool_servers()
            fallback = self.mod.recompile_and_grade(
                self.src, "Tiny", "", ref, os.path.join(self.tmpdir, "g2"),
                javac_bin=JDK25_JAVAC, javap_bin=JDK25_JAVAP, tool_server=True,
            )
        self.assertEqual(fallback, baseline)
        self.assertEqual(fallback["grade"], "roundtrip-exact")

    def test_recompile_and_grade_via_server_matches_subprocess(self):
        ref = self._subprocess_compile(os.path.join(self.tmpdir, "ref"))
        a = self.mod.recompile_and_grade(self.src, "Tiny", "", ref, os.path.join(self.tmpdir, "g1"),
                                         javac_bin=JDK25_JAVAC, javap_bin=JDK25_JAVAP)
        b = self.mod.recompile_and_grade(self.src, "Tiny", "", ref, os.path.join(self.tmpdir, "g2"),
                                         javac_bin=JDK25_JAVAC, javap_bin=JDK25_JAVAP, tool_server=True)
        self.assertEqual(a, b)

    def test_main_passes_tool_server_through(self):
        with tempfile.TemporaryDirectory() as td:
            organized_dir = Path(td)
            mod_dir = organized_dir / "m"
            (mod_dir / "extracted").mkdir(parents=True)
            (mod_dir / "recon.json").write_text(json.dumps({"jar_sha256": "sha-m"}))
            seen = {}

            def fake_grade_module(module, primary_tree="vineflower", limit=None, **kwargs):
                seen.update(kwargs)
                return {
                    "module": module, "schema_version": self.mod.SCHEMA_VERSION,
                    "jar_sha256": "sha-m", "primary_tree": primary_tree, "limit_per_module": limit,
                    "class_count": 0, "grade_counts": {}, "classes": {},
                }

            for argv_extra, expected in (([], False), (["--tool-server"], True)):
                seen.clear()
                with mock.patch.object(self.mod, "grade_module", side_effect=fake_grade_module), \
                     mock.patch.object(self.mod, "build_classpath", return_value=""):
                    rc = self.mod.main([
                        "--modules", "m", "--force", *argv_extra,
                        "--organized-dir", str(organized_dir),
                        "--classpath-cache-dir", str(organized_dir / "_cp"),
                    ])
                self.assertEqual(rc, 0)
                self.assertIs(seen.get("tool_server"), expected)


class TestHarnessErrorsAndTimeouts(unittest.TestCase):
    """Missing ground-truth/source files and subprocess timeouts are HARNESS
    problems, never a decompiler-fidelity finding -- distinct typed grades
    ("harness-error", "timeout") so a corpus/setup bug is never misread as
    "the decompiled source doesn't compile" (no-compile). None of these need
    a real JDK: the missing-file checks return before any subprocess call,
    and the timeout case mocks subprocess.run directly.
    """

    def setUp(self):
        self.mod = _load()

    def test_missing_ground_truth_class_is_harness_error_not_no_compile(self):
        with tempfile.TemporaryDirectory() as td:
            java_file = Path(td) / "Foo.java"
            java_file.write_text("public class Foo {}\n")
            result = self.mod.recompile_and_grade(
                java_file=str(java_file), class_name="Foo", classpath="",
                ground_truth_class=str(Path(td) / "does-not-exist.class"),
                out_dir=str(Path(td) / "out"),
            )
        self.assertEqual(result["grade"], "harness-error")
        self.assertIn("ground truth class file missing", result["first_error"])

    def test_missing_decompiled_source_is_harness_error_not_no_compile(self):
        with tempfile.TemporaryDirectory() as td:
            ground_truth = Path(td) / "Foo.class"
            ground_truth.write_bytes(b"not real bytecode, never reached")
            result = self.mod.recompile_and_grade(
                java_file=str(Path(td) / "does-not-exist.java"), class_name="Foo", classpath="",
                ground_truth_class=str(ground_truth),
                out_dir=str(Path(td) / "out"),
            )
        self.assertEqual(result["grade"], "harness-error")
        self.assertIn("decompiled source file missing", result["first_error"])

    def test_javac_timeout_returns_typed_timeout_grade(self):
        with tempfile.TemporaryDirectory() as td:
            java_file = Path(td) / "Foo.java"
            java_file.write_text("public class Foo {}\n")
            ground_truth = Path(td) / "Foo.class"
            ground_truth.write_bytes(b"not real bytecode, never reached")
            with mock.patch.object(
                self.mod.subprocess, "run",
                side_effect=self.mod.subprocess.TimeoutExpired(cmd="javac", timeout=1),
            ):
                result = self.mod.recompile_and_grade(
                    java_file=str(java_file), class_name="Foo", classpath="",
                    ground_truth_class=str(ground_truth), out_dir=str(Path(td) / "out"),
                    javac_timeout=1,
                )
        self.assertEqual(result["grade"], "timeout")

    def test_harness_error_and_timeout_are_never_clean_and_rank_with_no_compile(self):
        self.assertFalse(self.mod._is_clean("harness-error"))
        self.assertFalse(self.mod._is_clean("timeout"))
        self.assertEqual(self.mod._GRADE_RANK["harness-error"], self.mod._GRADE_RANK["no-compile"])
        self.assertEqual(self.mod._GRADE_RANK["timeout"], self.mod._GRADE_RANK["no-compile"])


class TestEndToEndRecompile(unittest.TestCase):
    def setUp(self):
        if not _jdk_available():
            self.skipTest("JDK 25 (javac/javap) not installed at the pinned brew path")
        self.mod = _load()
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)

    def _compile(self, src_name, src_text, out_dir):
        src = os.path.join(self.tmpdir, src_name)
        with open(src, "w") as f:
            f.write(src_text)
        subprocess.run(
            [JDK25_JAVAC, "--release", "25", "-g", "-implicit:none", "-proc:none", "-nowarn", "-d", out_dir, src],
            check=True, capture_output=True,
        )

    def test_identical_source_recompiles_roundtrip_exact(self):
        source = (
            "public class Plain {\n"
            "    private final int x;\n"
            "    public Plain(int x) { this.x = x; }\n"
            "    public int getX() { return x; }\n"
            "}\n"
        )
        ground_dir = os.path.join(self.tmpdir, "ground")
        recompiled_dir = os.path.join(self.tmpdir, "recompiled")
        os.makedirs(ground_dir)
        os.makedirs(recompiled_dir)
        self._compile("Plain.java", source, ground_dir)
        # simulate "decompiled" source == the same source (the strongest possible
        # case: a decompiler that reproduces the original byte-for-byte in source form)
        java_file = os.path.join(self.tmpdir, "Plain.java")
        result = self.mod.recompile_and_grade(
            java_file=java_file,
            class_name="Plain",
            classpath="",
            ground_truth_class=os.path.join(ground_dir, "Plain.class"),
            out_dir=recompiled_dir,
            javac_bin=JDK25_JAVAC,
            javap_bin=JDK25_JAVAP,
        )
        self.assertEqual(result["grade"], "roundtrip-exact")

    def test_packaged_class_recompiles_roundtrip_exact(self):
        # regression: javac writes output under <out_dir>/<package-path>/, not
        # flat into out_dir — almost every real N5 class is packaged (e.g.
        # com.tridium.*, niagara.*), so this is the common case, not an edge case.
        source = (
            "package com.example.pkg;\n"
            "public class Packaged {\n"
            "    public int value() { return 7; }\n"
            "}\n"
        )
        ground_dir = os.path.join(self.tmpdir, "ground_pkg")
        recompiled_dir = os.path.join(self.tmpdir, "recompiled_pkg")
        src_dir = os.path.join(self.tmpdir, "pkgsrc")
        os.makedirs(ground_dir)
        os.makedirs(recompiled_dir)
        os.makedirs(os.path.join(src_dir, "com", "example", "pkg"))
        java_file = os.path.join(src_dir, "com", "example", "pkg", "Packaged.java")
        with open(java_file, "w") as f:
            f.write(source)
        subprocess.run(
            [JDK25_JAVAC, "--release", "25", "-g", "-d", ground_dir, java_file],
            check=True, capture_output=True,
        )
        result = self.mod.recompile_and_grade(
            java_file=java_file,
            class_name="Packaged",
            classpath="",
            ground_truth_class=os.path.join(ground_dir, "com", "example", "pkg", "Packaged.class"),
            out_dir=recompiled_dir,
            javac_bin=JDK25_JAVAC,
            javap_bin=JDK25_JAVAP,
        )
        self.assertEqual(result["grade"], "roundtrip-exact")

    def test_never_silently_resolves_from_classpath_instead_of_fresh_output(self):
        # A decoy jar on the classpath contains a Plain.class that is BYTE-
        # IDENTICAL to ground truth. If the implementation ever located the
        # class under test by name resolution through the classpath (or by
        # any means other than the literal file javac JUST wrote to a fresh
        # -d dir), it could silently grade the decoy instead of the actual
        # decompiled source under test — a genuinely broken/altered source
        # would then falsely grade as compiling cleanly / matching.
        ground_source = (
            "package pkg;\n"
            "public class Plain {\n"
            "    public int getX() { return 1; }\n"
            "}\n"
        )
        ground_dir = os.path.join(self.tmpdir, "ground_silent")
        ground_src_dir = os.path.join(self.tmpdir, "ground_silent_src")
        os.makedirs(ground_dir)
        os.makedirs(os.path.join(ground_src_dir, "pkg"))
        ground_src = os.path.join(ground_src_dir, "pkg", "Plain.java")
        with open(ground_src, "w") as f:
            f.write(ground_source)
        subprocess.run([JDK25_JAVAC, "--release", "25", "-g", "-d", ground_dir, ground_src],
                        check=True, capture_output=True)
        ground_truth_class = os.path.join(ground_dir, "pkg", "Plain.class")

        # decoy: a jar, on the classpath, containing the SAME class byte-for-byte
        decoy_jar = os.path.join(self.tmpdir, "decoy.jar")
        jar_bin = os.path.join(os.path.dirname(JDK25_JAVAC), "jar")
        subprocess.run([jar_bin, "--create", "--file", decoy_jar, "-C", ground_dir, "pkg"],
                        check=True, capture_output=True)

        # case 1: genuinely broken source -> must be no-compile, never "resolved"
        # to the decoy's clean roundtrip via the classpath
        broken_dir = os.path.join(self.tmpdir, "broken_src")
        os.makedirs(os.path.join(broken_dir, "pkg"))
        broken_src = os.path.join(broken_dir, "pkg", "Plain.java")
        with open(broken_src, "w") as f:
            f.write("package pkg;\npublic class Plain { this is not java }\n")
        broken_out = os.path.join(self.tmpdir, "broken_out")
        os.makedirs(broken_out)
        result_broken = self.mod.recompile_and_grade(
            java_file=broken_src, class_name="Plain", classpath=decoy_jar,
            ground_truth_class=ground_truth_class, out_dir=broken_out,
            javac_bin=JDK25_JAVAC, javap_bin=JDK25_JAVAP,
        )
        self.assertEqual(result_broken["grade"], "no-compile")

        # case 2: compiles fine but the method body genuinely differs from
        # ground truth -> must be compiles-mismatch, never a false roundtrip-exact
        # (which is exactly what would happen if grading read the decoy's
        # byte-identical copy off the classpath instead of the fresh -d output)
        altered_dir = os.path.join(self.tmpdir, "altered_src")
        os.makedirs(os.path.join(altered_dir, "pkg"))
        altered_src = os.path.join(altered_dir, "pkg", "Plain.java")
        with open(altered_src, "w") as f:
            f.write("package pkg;\npublic class Plain {\n    public int getX() { return 999; }\n}\n")
        altered_out = os.path.join(self.tmpdir, "altered_out")
        os.makedirs(altered_out)
        result_altered = self.mod.recompile_and_grade(
            java_file=altered_src, class_name="Plain", classpath=decoy_jar,
            ground_truth_class=ground_truth_class, out_dir=altered_out,
            javac_bin=JDK25_JAVAC, javap_bin=JDK25_JAVAP,
        )
        self.assertEqual(result_altered["grade"], "compiles-mismatch")
        # and the recompiled class actually used must be under altered_out,
        # never anywhere on the classpath (e.g. an extracted decoy path)
        self.assertNotIn("decoy", " ".join(str(v) for v in result_altered.values()))

    def test_source_with_syntax_error_grades_no_compile(self):
        # a REAL (existing) ground-truth class is required here so this test
        # isolates "genuinely broken source" (no-compile) from "missing
        # ground-truth file" (harness-error, see TestHarnessErrorsAndTimeouts)
        # -- those are two different claims and must not be conflated.
        ground_dir = os.path.join(self.tmpdir, "ground")
        os.makedirs(ground_dir)
        self._compile("Broken.java", "public class Broken {}\n", ground_dir)
        java_file = os.path.join(self.tmpdir, "Broken.java")
        with open(java_file, "w") as f:
            f.write("public class Broken { this is not java }\n")
        result = self.mod.recompile_and_grade(
            java_file=java_file,
            class_name="Broken",
            classpath="",
            ground_truth_class=os.path.join(ground_dir, "Broken.class"),
            out_dir=os.path.join(self.tmpdir, "out"),
            javac_bin=JDK25_JAVAC,
            javap_bin=JDK25_JAVAP,
        )
        self.assertEqual(result["grade"], "no-compile")
        self.assertTrue(result["first_error"])

    def test_semantically_different_source_grades_compiles_mismatch(self):
        original = (
            "public class Diff {\n"
            "    public int compute(int a) { return a + 1; }\n"
            "}\n"
        )
        changed = (
            "public class Diff {\n"
            "    public int compute(int a) { return a + 2; }\n"
            "}\n"
        )
        ground_dir = os.path.join(self.tmpdir, "ground2")
        ground_src_dir = os.path.join(self.tmpdir, "ground2_src")
        recompiled_dir = os.path.join(self.tmpdir, "recompiled2")
        os.makedirs(ground_dir)
        os.makedirs(ground_src_dir)
        os.makedirs(recompiled_dir)
        # javac requires a public top-level class's file to be named after it,
        # so the ground-truth source lives in its own directory under Diff.java
        # (distinct from the "decompiled" Diff.java used for the actual grade).
        ground_src = os.path.join(ground_src_dir, "Diff.java")
        with open(ground_src, "w") as f:
            f.write(original)
        subprocess.run(
            [JDK25_JAVAC, "--release", "25", "-g", "-d", ground_dir, ground_src],
            check=True, capture_output=True,
        )
        java_file = os.path.join(self.tmpdir, "Diff.java")
        with open(java_file, "w") as f:
            f.write(changed)
        result = self.mod.recompile_and_grade(
            java_file=java_file,
            class_name="Diff",
            classpath="",
            ground_truth_class=os.path.join(ground_dir, "Diff.class"),
            out_dir=recompiled_dir,
            javac_bin=JDK25_JAVAC,
            javap_bin=JDK25_JAVAP,
        )
        self.assertEqual(result["grade"], "compiles-mismatch")
        self.assertIn(("compute", "(I)I"), result["mismatched_methods"])


# ---------------------------------------------------------------------------
# T20: per-tree output files + legacy migration + limit-per-module caching
# ---------------------------------------------------------------------------
class TestFidelityOutputPaths(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_output_path_is_tree_specific(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            self.assertEqual(
                self.mod.fidelity_output_path(mod_dir, "vineflower"),
                mod_dir / "fidelity.vineflower.json",
            )
            self.assertEqual(
                self.mod.fidelity_output_path(mod_dir, "vineflower2"),
                mod_dir / "fidelity.vineflower2.json",
            )

    def test_read_path_falls_back_to_legacy_fidelity_json_for_vineflower_only(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            (mod_dir / "fidelity.json").write_text("{}")
            self.assertEqual(self.mod.fidelity_read_path(mod_dir, "vineflower"), mod_dir / "fidelity.json")
            self.assertIsNone(self.mod.fidelity_read_path(mod_dir, "vineflower2"))

    def test_read_path_prefers_new_name_over_legacy(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            (mod_dir / "fidelity.json").write_text('{"which": "legacy"}')
            (mod_dir / "fidelity.vineflower.json").write_text('{"which": "new"}')
            p = self.mod.fidelity_read_path(mod_dir, "vineflower")
            self.assertEqual(json.loads(p.read_text())["which"], "new")

    def test_migrate_legacy_fidelity_json_renames_when_target_absent(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            (mod_dir / "fidelity.json").write_text('{"m": 1}')
            migrated = self.mod.migrate_legacy_fidelity_json(mod_dir)
            self.assertTrue(migrated)
            self.assertFalse((mod_dir / "fidelity.json").exists())
            self.assertEqual(json.loads((mod_dir / "fidelity.vineflower.json").read_text())["m"], 1)

    def test_migrate_legacy_fidelity_json_is_a_noop_when_target_already_exists(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            (mod_dir / "fidelity.json").write_text('{"m": "legacy"}')
            (mod_dir / "fidelity.vineflower.json").write_text('{"m": "new"}')
            migrated = self.mod.migrate_legacy_fidelity_json(mod_dir)
            self.assertFalse(migrated)
            # both files preserved untouched — never silently discard either
            self.assertTrue((mod_dir / "fidelity.json").exists())
            self.assertEqual(json.loads((mod_dir / "fidelity.vineflower.json").read_text())["m"], "new")

    def test_migrate_legacy_fidelity_json_is_a_noop_when_legacy_absent(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            migrated = self.mod.migrate_legacy_fidelity_json(mod_dir)
            self.assertFalse(migrated)

    def test_is_module_up_to_date_rejects_a_differently_limited_run(self):
        # a --limit-per-module run must never be mistaken for an up-to-date
        # cache of a full (or differently limited) run (R4-limited-run-cached-as-complete)
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            (mod_dir / "recon.json").write_text(json.dumps({"jar_sha256": "abc"}))
            (mod_dir / "fidelity.vineflower.json").write_text(json.dumps({
                "schema_version": self.mod.SCHEMA_VERSION, "jar_sha256": "abc",
                "primary_tree": "vineflower", "limit_per_module": 6,
            }))
            self.assertTrue(self.mod.is_module_up_to_date(mod_dir, primary_tree="vineflower", limit_per_module=6))
            self.assertFalse(self.mod.is_module_up_to_date(mod_dir, primary_tree="vineflower", limit_per_module=None))
            self.assertFalse(self.mod.is_module_up_to_date(mod_dir, primary_tree="vineflower", limit_per_module=3))

    def test_is_module_up_to_date_defaults_missing_limit_per_module_to_none(self):
        # a legacy fidelity.json written before this field existed was always
        # a FULL run -- it must be recognized as up to date for an unlimited
        # (limit_per_module=None) request, not force a re-run.
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td)
            (mod_dir / "recon.json").write_text(json.dumps({"jar_sha256": "abc"}))
            (mod_dir / "fidelity.json").write_text(json.dumps({
                "schema_version": self.mod.SCHEMA_VERSION, "jar_sha256": "abc",
            }))
            self.assertTrue(self.mod.is_module_up_to_date(mod_dir, primary_tree="vineflower", limit_per_module=None))


class TestPerTreeGradingWritesSeparateFiles(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_grading_two_trees_for_the_same_module_produces_two_files(self):
        with tempfile.TemporaryDirectory() as td:
            organized_dir = Path(td)
            mod_dir = organized_dir / "m"
            (mod_dir / "extracted").mkdir(parents=True)
            (mod_dir / "recon.json").write_text(json.dumps({"jar_sha256": "sha-m"}))

            def fake_grade_module(module, primary_tree="vineflower", limit=None, **kwargs):
                return {
                    "module": module, "schema_version": self.mod.SCHEMA_VERSION,
                    "jar_sha256": "sha-m", "primary_tree": primary_tree, "limit_per_module": limit,
                    "class_count": 1, "grade_counts": {"roundtrip-exact": 1},
                    "classes": {"p/X": {"grade": "roundtrip-exact"}},
                }

            with mock.patch.object(self.mod, "grade_module", side_effect=fake_grade_module), \
                 mock.patch.object(self.mod, "build_classpath", return_value=""):
                rc1 = self.mod.main([
                    "--modules", "m", "--tree", "vineflower",
                    "--organized-dir", str(organized_dir),
                    "--classpath-cache-dir", str(organized_dir / "_cp"),
                ])
                rc2 = self.mod.main([
                    "--modules", "m", "--tree", "vineflower2",
                    "--organized-dir", str(organized_dir),
                    "--classpath-cache-dir", str(organized_dir / "_cp"),
                ])
            self.assertEqual(rc1, 0)
            self.assertEqual(rc2, 0)
            vf_path = mod_dir / "fidelity.vineflower.json"
            vf2_path = mod_dir / "fidelity.vineflower2.json"
            self.assertTrue(vf_path.is_file())
            self.assertTrue(vf2_path.is_file())
            self.assertEqual(json.loads(vf_path.read_text())["primary_tree"], "vineflower")
            self.assertEqual(json.loads(vf2_path.read_text())["primary_tree"], "vineflower2")
            # neither run overwrote the other, and no legacy file was created
            self.assertFalse((mod_dir / "fidelity.json").exists())


# ---------------------------------------------------------------------------
# T20: --compare (per-class grade transition between two trees)
# ---------------------------------------------------------------------------
class TestCompareTreeGrades(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_transition_counts_and_worse_better_split(self):
        results_a = [{
            "module": "m1",
            "classes": {
                "p/A": {"grade": "roundtrip-exact"},
                "p/B": {"grade": "compiles-mismatch"},
                "p/C": {"grade": "bytecode-only"},
                "p/D": {"grade": "no-compile"},
            },
        }, {
            "module": "m2",
            "classes": {
                "p/E": {"grade": "roundtrip-exact"},
            },
        }]
        results_b = [{
            "module": "m1",
            "classes": {
                "p/A": {"grade": "roundtrip-exact"},   # unchanged: exact->exact
                "p/B": {"grade": "bytecode-only"},      # same rank (1->1): unchanged
                "p/C": {"grade": "roundtrip-exact"},    # got BETTER: bytecode-only->exact
                "p/D": {"grade": "no-compile"},         # unchanged: no-compile->no-compile
            },
        }, {
            "module": "m2",
            "classes": {
                "p/E": {"grade": "bytecode-only"},      # got WORSE: exact->bytecode-only
            },
        }]
        cmp_result = self.mod.compare_tree_grades(results_a, results_b, "vineflower", "vineflower2")
        self.assertEqual(cmp_result["tree_a"], "vineflower")
        self.assertEqual(cmp_result["tree_b"], "vineflower2")
        self.assertEqual(cmp_result["common_class_count"], 5)
        self.assertEqual(cmp_result["transition_counts"]["roundtrip-exact->roundtrip-exact"], 1)
        self.assertEqual(cmp_result["transition_counts"]["bytecode-only->roundtrip-exact"], 1)
        self.assertEqual(cmp_result["transition_counts"]["no-compile->no-compile"], 1)
        self.assertEqual(cmp_result["transition_counts"]["roundtrip-exact->bytecode-only"], 1)
        worse_classes = {(w["module"], w["class"]) for w in cmp_result["worse"]}
        better_classes = {(b["module"], b["class"]) for b in cmp_result["better"]}
        self.assertIn(("m2", "p/E"), worse_classes)
        self.assertIn(("m1", "p/C"), better_classes)
        # p/B: compiles-mismatch (rank1) -> bytecode-only (rank1) same rank => neither
        self.assertNotIn(("m1", "p/B"), worse_classes)
        self.assertNotIn(("m1", "p/B"), better_classes)
        self.assertEqual(
            cmp_result["per_module_transition_counts"]["m2"]["roundtrip-exact->bytecode-only"], 1
        )

    def test_class_present_in_only_one_tree_is_excluded(self):
        results_a = [{"module": "m", "classes": {"p/Only": {"grade": "roundtrip-exact"}}}]
        results_b = [{"module": "m", "classes": {}}]
        cmp_result = self.mod.compare_tree_grades(results_a, results_b, "a", "b")
        self.assertEqual(cmp_result["common_class_count"], 0)
        self.assertEqual(cmp_result["worse"], [])
        self.assertEqual(cmp_result["better"], [])

    def test_module_present_only_in_one_tree_is_excluded(self):
        results_a = [{"module": "only_a", "classes": {"p/X": {"grade": "roundtrip-exact"}}}]
        results_b = [{"module": "only_b", "classes": {"p/Y": {"grade": "roundtrip-exact"}}}]
        cmp_result = self.mod.compare_tree_grades(results_a, results_b, "a", "b")
        self.assertEqual(cmp_result["modules_common"], [])
        self.assertEqual(cmp_result["common_class_count"], 0)


class TestGenerateCompareReport(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_report_lists_transitions_and_worse_before_better(self):
        comparison = {
            "tree_a": "vineflower", "tree_b": "vineflower2",
            "modules_common": ["m1", "m2"],
            "common_class_count": 3,
            "transition_counts": {
                "roundtrip-exact->roundtrip-exact": 1,
                "roundtrip-exact->bytecode-only": 1,
                "bytecode-only->roundtrip-exact": 1,
            },
            "per_module_transition_counts": {
                "m1": {"roundtrip-exact->roundtrip-exact": 1, "bytecode-only->roundtrip-exact": 1},
                "m2": {"roundtrip-exact->bytecode-only": 1},
            },
            "worse": [{"module": "m2", "class": "p/E", "from": "roundtrip-exact", "to": "bytecode-only"}],
            "better": [{"module": "m1", "class": "p/C", "from": "bytecode-only", "to": "roundtrip-exact"}],
            "unchanged_count": 1,
        }
        report = self.mod.generate_compare_report(comparison, title="v1 vs v2 (library context)")
        self.assertIn("v1 vs v2 (library context)", report)
        self.assertIn("vineflower", report)
        self.assertIn("vineflower2", report)
        self.assertIn("roundtrip-exact->bytecode-only", report)
        self.assertIn("p/E", report)
        self.assertIn("p/C", report)
        worse_idx = report.index("got WORSE")
        better_idx = report.index("got better")
        self.assertLess(worse_idx, better_idx)
        self.assertIn("Recommendation", report)

    def test_recommendation_keeps_tree_a_when_tree_b_has_any_regression(self):
        # even if tree_b's overall round-trip rate looks equal or better,
        # a single regression disqualifies it as primary -- the worse-list
        # takes precedence over the raw rate.
        comparison = {
            "tree_a": "vineflower", "tree_b": "vineflower2",
            "modules_common": ["m"], "common_class_count": 2,
            "transition_counts": {
                "roundtrip-exact->bytecode-only": 1,
                "bytecode-only->roundtrip-exact": 1,
            },
            "per_module_transition_counts": {"m": {"roundtrip-exact->bytecode-only": 1, "bytecode-only->roundtrip-exact": 1}},
            "worse": [{"module": "m", "class": "p/A", "from": "roundtrip-exact", "to": "bytecode-only"}],
            "better": [{"module": "m", "class": "p/B", "from": "bytecode-only", "to": "roundtrip-exact"}],
            "unchanged_count": 0,
        }
        report = self.mod.generate_compare_report(comparison, title="t")
        self.assertIn("keep `vineflower`", report)
        self.assertIn("regression", report)

    def test_recommendation_adopts_tree_b_when_strictly_higher_rate_and_no_regressions(self):
        comparison = {
            "tree_a": "vineflower", "tree_b": "vineflower2",
            "modules_common": ["m"], "common_class_count": 2,
            "transition_counts": {
                "roundtrip-exact->roundtrip-exact": 1,
                "bytecode-only->roundtrip-exact": 1,
            },
            "per_module_transition_counts": {"m": {"roundtrip-exact->roundtrip-exact": 1, "bytecode-only->roundtrip-exact": 1}},
            "worse": [],
            "better": [{"module": "m", "class": "p/B", "from": "bytecode-only", "to": "roundtrip-exact"}],
            "unchanged_count": 1,
        }
        report = self.mod.generate_compare_report(comparison, title="t")
        self.assertIn("adopt `vineflower2`", report)

    def test_recommendation_no_change_when_rates_identical_and_no_regressions(self):
        comparison = {
            "tree_a": "vineflower", "tree_b": "vineflower2",
            "modules_common": ["m"], "common_class_count": 1,
            "transition_counts": {"roundtrip-exact->roundtrip-exact": 1},
            "per_module_transition_counts": {"m": {"roundtrip-exact->roundtrip-exact": 1}},
            "worse": [], "better": [], "unchanged_count": 1,
        }
        report = self.mod.generate_compare_report(comparison, title="t")
        self.assertIn("no change", report.lower())

    def test_notes_are_rendered_when_supplied_and_omitted_when_not(self):
        comparison = {
            "tree_a": "a", "tree_b": "b", "modules_common": ["m"], "common_class_count": 1,
            "transition_counts": {"roundtrip-exact->roundtrip-exact": 1},
            "per_module_transition_counts": {"m": {"roundtrip-exact->roundtrip-exact": 1}},
            "worse": [], "better": [], "unchanged_count": 1,
        }
        with_notes = self.mod.generate_compare_report(comparison, title="t", notes=["custom caveat text"])
        self.assertIn("### Notes", with_notes)
        self.assertIn("custom caveat text", with_notes)
        without_notes = self.mod.generate_compare_report(comparison, title="t")
        self.assertNotIn("### Notes", without_notes)


class TestUpsertMarkdownSection(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_appends_when_heading_absent(self):
        doc = "# Title\n\nSome content.\n"
        out = self.mod.upsert_markdown_section(doc, "## New Section", "Body text.\n")
        self.assertIn("## New Section", out)
        self.assertIn("Body text.", out)
        self.assertTrue(out.startswith("# Title"))

    def test_replaces_existing_section_in_place_preserving_surrounding_content(self):
        doc = (
            "# Title\n\n"
            "## Before\n\nkeep this\n\n"
            "## Target\n\nold body\nmore old\n\n"
            "## After\n\nkeep this too\n"
        )
        out = self.mod.upsert_markdown_section(doc, "## Target", "new body\n")
        self.assertIn("## Before", out)
        self.assertIn("keep this\n", out)
        self.assertIn("## After", out)
        self.assertIn("keep this too", out)
        self.assertIn("new body", out)
        self.assertNotIn("old body", out)
        self.assertLess(out.index("## Before"), out.index("## Target"))
        self.assertLess(out.index("## Target"), out.index("## After"))


class TestCompareCLIWritesReportSection(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_compare_flag_upserts_section_into_existing_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            organized_dir = root / "organized"
            mod_dir = organized_dir / "m"
            mod_dir.mkdir(parents=True)
            (mod_dir / "fidelity.vineflower.json").write_text(json.dumps({
                "module": "m", "classes": {"p/X": {"grade": "roundtrip-exact"}},
            }))
            (mod_dir / "fidelity.vineflower2.json").write_text(json.dumps({
                "module": "m", "classes": {"p/X": {"grade": "bytecode-only"}},
            }))
            docs_dir = root / "docs"
            docs_dir.mkdir(parents=True)
            report_path = docs_dir / "decompile-fidelity-report.md"
            report_path.write_text("# Decompile fidelity report\n\n## Overall\n\nsomething\n")

            with mock.patch.object(self.mod, "REPO_ROOT", root):
                rc = self.mod.main([
                    "--modules", "m",
                    "--organized-dir", str(organized_dir),
                    "--compare", "vineflower,vineflower2",
                    "--compare-title", "v1 vs v2 (library context)",
                    "--report",
                ])
            self.assertEqual(rc, 0)
            written = report_path.read_text()
            self.assertIn("v1 vs v2 (library context)", written)
            self.assertIn("p/X", written)
            self.assertIn("## Overall", written)  # untouched pre-existing section preserved
            # regression: generate_compare_report emits its own leading
            # "## {title}" heading, and upsert_markdown_section ALSO prepends
            # the heading it was given -- together these doubled the heading
            # line in the real docs/decompile-fidelity-report.md write.
            self.assertEqual(
                written.count("## v1 vs v2 (library context)"), 1,
                "the section heading must appear exactly once, not duplicated",
            )

    def test_compare_requires_exactly_two_trees(self):
        with tempfile.TemporaryDirectory() as td:
            organized_dir = Path(td) / "organized"
            (organized_dir / "m").mkdir(parents=True)
            with self.assertRaises(SystemExit):
                self.mod.main([
                    "--modules", "m",
                    "--organized-dir", str(organized_dir),
                    "--compare", "onlyone",
                ])


class TestLoadTreeResultsReportsSkippedModules(unittest.TestCase):
    """Review review-6f1c46518f56b786 R3-compare-silently-drops-modules: a missing or corrupt
    fidelity.<tree>.json must be REPORTED, never silently dropped from a --compare."""

    def test_missing_and_corrupt_modules_are_reported(self):
        mod = _load()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "good").mkdir()
            (root / "good" / "fidelity.vineflower2.json").write_text(json.dumps({"module": "good", "classes": {}}))
            (root / "broken").mkdir()
            (root / "broken" / "fidelity.vineflower2.json").write_text("{not json")
            (root / "absent").mkdir()
            skipped = []
            out = mod.load_tree_results(root, ["good", "broken", "absent"], "vineflower2", skipped=skipped)
            self.assertEqual([r["module"] for r in out], ["good"])
            self.assertEqual(sorted(m for m, _ in skipped), ["absent", "broken"])
            reasons = dict(skipped)
            self.assertIn("missing", reasons["absent"])
            self.assertIn("unreadable", reasons["broken"])



if __name__ == "__main__":
    unittest.main()
