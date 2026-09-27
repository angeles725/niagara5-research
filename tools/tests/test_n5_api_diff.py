"""Tests for tools/n5-api-diff.py: source-mode package-rename-aware diff and
the --binary japicmp wrapper.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-api-diff.py")
JAPICMP_JAR = os.path.join(TOOLS_DIR, "decompilers", "japicmp-0.26.2-jar-with-dependencies.jar")
JAVA = "/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java"


def _load():
    spec = importlib.util.spec_from_file_location("n5_api_diff", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestPackageMapping(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_default_rule_maps_javax_baja_to_niagara(self):
        rules = self.mod.effective_rules([], no_default_map=False)
        self.assertEqual(self.mod.map_package("javax.baja.sys", rules), "niagara.sys")

    def test_default_rule_leaves_com_tridium_unchanged(self):
        rules = self.mod.effective_rules([], no_default_map=False)
        self.assertEqual(self.mod.map_package("com.tridium.alarm", rules), "com.tridium.alarm")

    def test_no_default_map_disables_builtin_rule(self):
        rules = self.mod.effective_rules([], no_default_map=True)
        self.assertEqual(self.mod.map_package("javax.baja.sys", rules), "javax.baja.sys")

    def test_custom_map_rule_applied_before_default(self):
        rules = self.mod.effective_rules(
            self.mod.parse_map_args(["javax.baja.sys=niagara.core.sys"]), no_default_map=False
        )
        self.assertEqual(self.mod.map_package("javax.baja.sys", rules), "niagara.core.sys")
        # unrelated javax.baja.* packages still fall through to the default rule
        self.assertEqual(self.mod.map_package("javax.baja.file", rules), "niagara.file")

    def test_parse_map_args_rejects_missing_equals(self):
        with self.assertRaises(ValueError):
            self.mod.parse_map_args(["not-a-valid-spec"])


class TestMethodExtraction(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_extracts_public_method_signature(self):
        src = """
package javax.baja.sys;
public final class Sys {
  public static String getLanguage() {
    return null;
  }
}
"""
        sigs = self.mod.extract_public_methods(src)
        self.assertIn("getLanguage()", sigs)

    def test_extracts_protected_method_with_params(self):
        src = """
package javax.baja.sys;
public class Foo {
  protected boolean isValidPathName(String name) {
    return true;
  }
}
"""
        sigs = self.mod.extract_public_methods(src)
        self.assertIn("isValidPathName(String)", sigs)

    def test_private_methods_are_not_extracted(self):
        src = """
package javax.baja.sys;
public class Foo {
  private void helper() {}
}
"""
        sigs = self.mod.extract_public_methods(src)
        self.assertEqual(sigs, [])

    def test_source_package_extracts_declared_package(self):
        src = "package niagara.sys;\npublic final class Sys {}\n"
        self.assertEqual(self.mod.source_package(src), "niagara.sys")


class TestSourceTreeCompare(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_renamed_package_matched_via_default_rule(self):
        n4_tree = {
            "javax.baja.sys": {
                "Sys": (
                    "package javax.baja.sys;\npublic final class Sys {\n"
                    "  public static String getLanguage() { return null; }\n"
                    "  public static void oldOnlyMethod() {}\n"
                    "}\n"
                )
            }
        }
        n5_tree = {
            "niagara.sys": {
                "Sys": (
                    "package niagara.sys;\npublic final class Sys {\n"
                    "  public static String getLanguageCode() { return null; }\n"
                    "  public static String getLanguage() { return null; }\n"
                    "}\n"
                )
            }
        }
        rules = self.mod.effective_rules([], no_default_map=False)
        result = self.mod.compare_source_trees(n4_tree, n5_tree, rules)
        self.assertEqual(len(result["packages"]), 1)
        pkg = result["packages"][0]
        self.assertTrue(pkg["renamed"])
        self.assertEqual(pkg["n4_package"], "javax.baja.sys")
        self.assertEqual(pkg["n5_package"], "niagara.sys")
        self.assertEqual(result["n4_packages_no_counterpart"], [])
        self.assertEqual(result["n5_packages_no_counterpart"], [])
        sys_type = pkg["types_common"][0]
        self.assertIn("getLanguageCode()", sys_type["methods_added"])
        self.assertIn("oldOnlyMethod()", sys_type["methods_removed"])

    def test_package_with_no_counterpart_after_mapping_is_reported(self):
        n4_tree = {"javax.baja.totallyGone": {"Foo": "package javax.baja.totallyGone;\npublic class Foo {}\n"}}
        n5_tree = {}
        rules = self.mod.effective_rules([], no_default_map=False)
        result = self.mod.compare_source_trees(n4_tree, n5_tree, rules)
        self.assertIn("javax.baja.totallyGone", result["n4_packages_no_counterpart"])

    def test_n5_only_package_has_no_counterpart(self):
        n4_tree = {}
        n5_tree = {"niagara.brandNew": {"Bar": "package niagara.brandNew;\npublic class Bar {}\n"}}
        rules = self.mod.effective_rules([], no_default_map=False)
        result = self.mod.compare_source_trees(n4_tree, n5_tree, rules)
        self.assertIn("niagara.brandNew", result["n5_packages_no_counterpart"])

    def test_same_name_package_marked_not_renamed(self):
        n4_tree = {"com.tridium.alarm": {"X": "package com.tridium.alarm;\npublic class X {}\n"}}
        n5_tree = {"com.tridium.alarm": {"X": "package com.tridium.alarm;\npublic class X {}\n"}}
        rules = self.mod.effective_rules([], no_default_map=False)
        result = self.mod.compare_source_trees(n4_tree, n5_tree, rules)
        self.assertFalse(result["packages"][0]["renamed"])


class TestBinaryModeCommandBuilding(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_build_command_joins_multiple_old_jars_with_semicolon(self):
        cmd = self.mod.build_japicmp_command(
            "java", "japicmp.jar",
            old_jars=["alarm-rt.jar", "alarm-ux.jar", "alarm-wb.jar"],
            new_jars=["alarm.jar"],
            xml_file="out.xml",
        )
        self.assertIn("-o", cmd)
        o_idx = cmd.index("-o")
        self.assertEqual(cmd[o_idx + 1], "alarm-rt.jar;alarm-ux.jar;alarm-wb.jar")
        n_idx = cmd.index("-n")
        self.assertEqual(cmd[n_idx + 1], "alarm.jar")
        self.assertIn("--ignore-missing-classes", cmd)

    def test_build_command_requires_old_jar(self):
        with self.assertRaises(self.mod.JapicmpError):
            self.mod.build_japicmp_command("java", "japicmp.jar", [], ["new.jar"], "out.xml")

    def test_build_command_requires_new_jar(self):
        with self.assertRaises(self.mod.JapicmpError):
            self.mod.build_japicmp_command("java", "japicmp.jar", ["old.jar"], [], "out.xml")


SAMPLE_JAPICMP_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<japicmp oldJar="old.jar" newJar="new.jar">
  <classes>
    <class fullyQualifiedName="a.Foo" changeStatus="MODIFIED" binaryCompatible="false">
      <methods>
        <method name="bar" changeStatus="REMOVED" binaryCompatible="false"/>
        <method name="baz" changeStatus="NEW" binaryCompatible="true"/>
        <method name="qux" changeStatus="UNCHANGED" binaryCompatible="true"/>
      </methods>
    </class>
    <class fullyQualifiedName="a.Gone" changeStatus="REMOVED" binaryCompatible="false"/>
    <class fullyQualifiedName="a.New" changeStatus="NEW" binaryCompatible="true"/>
    <class fullyQualifiedName="a.Same" changeStatus="UNCHANGED" binaryCompatible="true"/>
  </classes>
</japicmp>
"""


class TestJapicmpReportParsing(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        fd, self.path = tempfile.mkstemp(suffix=".xml")
        os.close(fd)
        with open(self.path, "w") as fh:
            fh.write(SAMPLE_JAPICMP_XML)
        self.addCleanup(lambda: os.remove(self.path))

    def test_counts_by_change_status(self):
        summary = self.mod.parse_japicmp_report(self.path)
        self.assertEqual(summary["total_classes_compared"], 4)
        self.assertEqual(summary["classes_removed"], 1)
        self.assertEqual(summary["classes_new"], 1)
        self.assertEqual(summary["classes_modified"], 1)
        self.assertEqual(summary["classes_unchanged"], 1)

    def test_binary_incompatible_count(self):
        summary = self.mod.parse_japicmp_report(self.path)
        # a.Foo (MODIFIED, binaryCompatible=false) + a.Gone (REMOVED, false)
        self.assertEqual(summary["binary_incompatible_classes"], 2)

    def test_removed_classes_and_methods_listed(self):
        summary = self.mod.parse_japicmp_report(self.path)
        self.assertIn("a.Gone", summary["removed_classes_sample"])
        self.assertIn("a.Foo#bar", summary["removed_methods_sample"])
        self.assertEqual(summary["added_methods_total"], 1)

    def test_malformed_xml_raises_typed_error(self):
        fd, bad_path = tempfile.mkstemp(suffix=".xml")
        os.close(fd)
        with open(bad_path, "w") as fh:
            fh.write("not xml at all <<<")
        try:
            with self.assertRaises(self.mod.JapicmpError):
                self.mod.parse_japicmp_report(bad_path)
        finally:
            os.remove(bad_path)


class TestJapicmpRunnerFailsClosed(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_missing_japicmp_jar_raises_typed_error_not_crash(self):
        with self.assertRaises(self.mod.JapicmpError):
            self.mod.run_japicmp(
                "java", "/nonexistent/japicmp.jar",
                old_jars=["old.jar"], new_jars=["new.jar"],
            )

    def test_missing_java_raises_typed_error(self):
        with tempfile.NamedTemporaryFile(suffix=".jar") as fake_jar:
            with self.assertRaises(self.mod.JapicmpError):
                self.mod.run_japicmp(
                    "/nonexistent/java", fake_jar.name,
                    old_jars=["old.jar"], new_jars=["new.jar"],
                )


@unittest.skipUnless(os.path.isfile(JAPICMP_JAR), "japicmp jar not present in tools/decompilers/")
@unittest.skipUnless(os.path.isfile(JAVA), "pinned java not present on this machine")
class TestJapicmpAgainstRealN4N5Jars(unittest.TestCase):
    N4_BAJA = "/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/baja.jar"
    N5_BAJA = "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar"

    @unittest.skipUnless(
        os.path.isfile("/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/baja.jar"),
        "N4 baja.jar not present",
    )
    def test_real_baja_jar_binary_diff_runs_and_parses(self):
        mod = _load()
        summary = mod.run_japicmp(JAVA, JAPICMP_JAR, [self.N4_BAJA], [self.N5_BAJA])
        self.assertGreater(summary["total_classes_compared"], 100)


if __name__ == "__main__":
    unittest.main()
