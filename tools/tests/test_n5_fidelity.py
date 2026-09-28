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
        self.assertEqual(out[0], out[0])  # sanity: deterministic, see next assert
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

    def _run_with_fake_tool(self, jar_name):
        with tempfile.TemporaryDirectory() as td:
            tool_jar = Path(td) / jar_name
            tool_jar.write_bytes(b"not a real jar, just needs to exist")
            classfile = Path(td) / "Foo.class"
            classfile.write_bytes(b"")
            out_dir = Path(td) / "out"
            with mock.patch.object(self.mod.subprocess, "run") as run_mock:
                run_mock.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                self.mod._decompile_one_class_with("java", tool_jar, classfile, out_dir)
            self.assertEqual(run_mock.call_count, 1)
            return run_mock.call_args[0][0]

    def test_cfr_uses_outputdir_flag(self):
        argv = self._run_with_fake_tool("cfr-0.152.jar")
        self.assertIn("--outputdir", argv)
        self.assertNotIn("-od", argv)

    def test_procyon_uses_bare_dash_o_flag(self):
        argv = self._run_with_fake_tool("procyon-decompiler-0.6.0.jar")
        self.assertIn("-o", argv)
        self.assertNotIn("--outputdir", argv)
        self.assertNotIn("-od", argv)

    def test_jd_cli_uses_dash_od_before_the_class_argument(self):
        argv = self._run_with_fake_tool("jd-cli.jar")
        self.assertIn("-od", argv)
        # jd-cli's own CLI contract: -od <dir> must precede the file argument,
        # and the class file (last positional) must come after it
        self.assertTrue(argv[-1].endswith("Foo.class"))
        self.assertLess(argv.index("-od"), len(argv) - 1)


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
            self.assertEqual(rc, 0)
            good_fidelity = json.loads((organized_dir / "good" / "fidelity.json").read_text())
            self.assertEqual(good_fidelity["module"], "good")
            self.assertFalse((organized_dir / "bad" / "fidelity.json").exists())
            written_report = (organized_dir.parent / "docs" / "decompile-fidelity-report.md").read_text()
            self.assertIn("good", written_report)


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
        java_file = os.path.join(self.tmpdir, "Broken.java")
        with open(java_file, "w") as f:
            f.write("public class Broken { this is not java }\n")
        result = self.mod.recompile_and_grade(
            java_file=java_file,
            class_name="Broken",
            classpath="",
            ground_truth_class="/nonexistent/Broken.class",
            out_dir=self.tmpdir,
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


if __name__ == "__main__":
    unittest.main()
