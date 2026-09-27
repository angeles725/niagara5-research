"""Tests for tools/n5-modules.py: N5 module inventory + N4/N5 diff.

Unit tests build small synthetic module jars (module.xml only — JPMS parsing
is already covered end-to-end by test_moduleinfo.py against a real N5 jar) so
the module.xml reading, profile-hint heuristic, and N4-suffix collapsing are
verified hermetically. A separate smoke-test class exercises the real N5
install / N4 install paths when present on this machine.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-modules.py")
N5_MODULES_DIR = "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
N4_MODULES_DIR = "/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules"


def _load():
    spec = importlib.util.spec_from_file_location("n5_modules", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MODULE_XML_TMPL = """<?xml version="1.0" encoding="UTF-8"?>
<module name="{name}" vendor="Tridium" vendorVersion="5.0.0.28" description="{desc}"
        moduleName="{name}" schemaVersion="5">
 <installation>
  <dependencies>
   {deps}
  </dependencies>
 </installation>
 <types>
  {types}
 </types>
</module>
"""


def _make_module_jar(dir_path, name, deps=(), types=()):
    dep_xml = "\n".join(
        f'<dependency name="{d}" vendor="Tridium" vendorVersion="5.0.0"/>' for d in deps
    )
    type_xml = "\n".join(
        f'<type class="{cls}" name="{cls.rsplit(".", 1)[-1]}"/>' for cls in types
    )
    xml = MODULE_XML_TMPL.format(name=name, desc=f"{name} module", deps=dep_xml, types=type_xml)
    jar_path = os.path.join(dir_path, f"{name}.jar")
    with zipfile.ZipFile(jar_path, "w") as z:
        z.writestr("META-INF/module.xml", xml)
    return jar_path


class TestN5ModulesHermetic(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_profile_hint_detects_ux_segment(self):
        cls = "com.tridium.alarm.ux.baja.BAlarmInstructionsTypeExt"
        self.assertEqual(self.mod.profile_hint_for_class(cls), "ux")

    def test_profile_hint_unclassified_when_no_segment_matches(self):
        cls = "com.tridium.alarm.BAlarmClass"
        self.assertEqual(self.mod.profile_hint_for_class(cls), "unclassified")

    def test_build_module_record_reads_module_xml(self):
        jar = _make_module_jar(
            self.tmp.name, "fooMod",
            deps=["baja"],
            types=["com.example.ux.BFooView", "com.example.BFooLogic"],
        )
        rec = self.mod.build_module_record(jar, include_jpms=False)
        self.assertEqual(rec["module"], "fooMod")
        self.assertEqual(rec["name"], "fooMod")
        self.assertEqual([d["name"] for d in rec["dependencies"]], ["baja"])
        self.assertEqual(rec["type_count"], 2)
        self.assertEqual(rec["profile_hints"].get("ux"), 1)
        self.assertEqual(rec["profile_hints"].get("unclassified"), 1)

    def test_build_module_record_no_jpms_flag_skips_module_info(self):
        jar = _make_module_jar(self.tmp.name, "barMod")
        rec = self.mod.build_module_record(jar, include_jpms=False)
        self.assertNotIn("jpms", rec)
        self.assertNotIn("jpms_error", rec)

    def test_build_module_record_missing_module_info_is_none_not_error(self):
        jar = _make_module_jar(self.tmp.name, "bazMod")
        rec = self.mod.build_module_record(jar, include_jpms=True)
        self.assertIsNone(rec["jpms"])

    def test_collapse_n4_modules_strips_known_suffixes(self):
        d = self.tmp.name
        for fname in ("alarm-rt.jar", "alarm-ux.jar", "alarm-wb.jar", "baja.jar"):
            open(os.path.join(d, fname), "w").close()
        collapsed = self.mod.collapse_n4_modules(d)
        self.assertEqual(sorted(collapsed["alarm"]), ["rt", "ux", "wb"])
        self.assertEqual(collapsed["baja"], ["main"])

    def test_diff_n4_cli_added_removed_common(self):
        n5_dir = os.path.join(self.tmp.name, "n5")
        n4_dir = os.path.join(self.tmp.name, "n4")
        os.makedirs(n5_dir)
        os.makedirs(n4_dir)
        _make_module_jar(n5_dir, "onlyInN5")
        _make_module_jar(n5_dir, "sharedMod")
        for fname in ("onlyInN4-rt.jar", "sharedMod.jar"):
            open(os.path.join(n4_dir, fname), "w").close()

        r = subprocess.run(
            [sys.executable, SCRIPT, "--modules-dir", n5_dir,
             "diff-n4", "--n4-modules-dir", n4_dir, "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        import json
        result = json.loads(r.stdout)
        self.assertIn("onlyInN5", result["added_in_n5"])
        removed_names = [x["module"] for x in result["removed_from_n4"]]
        self.assertIn("onlyInN4", removed_names)
        common_names = [x["module"] for x in result["common"]]
        self.assertIn("sharedMod", common_names)

    def test_deps_closure_follows_module_xml_dependencies(self):
        d = self.tmp.name
        _make_module_jar(d, "leafMod")
        _make_module_jar(d, "midMod", deps=["leafMod"])
        _make_module_jar(d, "topMod", deps=["midMod"])
        r = subprocess.run(
            [sys.executable, SCRIPT, "--modules-dir", d, "deps", "topMod", "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        import json
        rows = json.loads(r.stdout)
        names = [row["module"] for row in rows]
        self.assertIn("leafMod", names)
        self.assertIn("midMod", names)
        # topMod itself excluded unless --include-self
        self.assertNotIn("topMod", names)

    def test_show_unknown_module_exits_nonzero(self):
        d = self.tmp.name
        r = subprocess.run(
            [sys.executable, SCRIPT, "--modules-dir", d, "show", "doesNotExist"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(r.returncode, 0)


@unittest.skipUnless(os.path.isdir(N5_MODULES_DIR), "N5 install not present on this machine")
class TestN5ModulesAgainstRealInstall(unittest.TestCase):
    def test_list_json_runs_over_real_n5_modules(self):
        r = subprocess.run(
            [sys.executable, SCRIPT, "list", "--no-jpms", "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        import json
        rows = json.loads(r.stdout)
        self.assertGreater(len(rows), 100)
        names = {r["module"] for r in rows}
        self.assertIn("baja", names)

    def test_show_baja_reports_jpms_exports(self):
        r = subprocess.run(
            [sys.executable, SCRIPT, "show", "baja", "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        import json
        rec = json.loads(r.stdout)
        self.assertIsNotNone(rec.get("jpms"))
        self.assertIn("niagara.sys", rec["jpms"]["exports"])

    @unittest.skipUnless(os.path.isdir(N4_MODULES_DIR), "N4 install not present on this machine")
    def test_diff_n4_headline_counts_are_plausible(self):
        r = subprocess.run(
            [sys.executable, SCRIPT, "diff-n4", "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        import json
        result = json.loads(r.stdout)
        self.assertGreater(result["n4_module_count"], 100)
        self.assertGreater(result["n5_module_count"], 100)
        self.assertGreater(len(result["common"]), 50)


if __name__ == "__main__":
    unittest.main()
