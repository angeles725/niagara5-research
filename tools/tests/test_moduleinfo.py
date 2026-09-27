"""Tests for tools/lib/moduleinfo.py — the pure-Python module-info.class parser.

Ground truth for the real-module tests comes from `javap -v` on the same
module-info.class (see the coordinator's comparison run against
/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/javap), so this test both
exercises the hermetic synthetic case AND cross-checks against a real N5
module when the install is present on this machine.
"""
import importlib.util
import os
import subprocess
import unittest
import zipfile

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N5_MODULES_DIR = "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
JAVAP = "/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/javap"


def _load():
    spec = importlib.util.spec_from_file_location(
        "moduleinfo", os.path.join(TOOLS_DIR, "lib", "moduleinfo.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestModuleInfoParserErrors(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_bad_magic_raises(self):
        with self.assertRaises(self.mod.ClassFileError):
            self.mod.parse_module_info(b"not a classfile")

    def test_no_module_attribute_raises(self):
        # A minimal, well-formed classfile header with zero top-level
        # attributes never reaches a "Module" attribute.
        import struct
        data = struct.pack(">IHH", 0xCAFEBABE, 0, 52)
        data += struct.pack(">H", 1)          # constant_pool_count = 1 (empty pool)
        data += struct.pack(">HHH", 0, 0, 0)  # access_flags, this_class, super_class
        data += struct.pack(">H", 0)          # interfaces_count
        data += struct.pack(">H", 0)          # fields_count
        data += struct.pack(">H", 0)          # methods_count
        data += struct.pack(">H", 0)          # attributes_count
        with self.assertRaises(self.mod.ClassFileError):
            self.mod.parse_module_info(data)


@unittest.skipUnless(os.path.isdir(N5_MODULES_DIR), "N5 install not present on this machine")
class TestModuleInfoParserAgainstRealN5Jar(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        jar_path = os.path.join(N5_MODULES_DIR, "baja.jar")
        if not os.path.isfile(jar_path):
            self.skipTest("baja.jar not found")
        with zipfile.ZipFile(jar_path) as z:
            self.data = z.read("module-info.class")

    def test_parses_baja_module_name(self):
        info = self.mod.parse_module_info(self.data)
        self.assertEqual(info["name"], "niagara.baja")

    def test_exports_include_niagara_sys(self):
        info = self.mod.parse_module_info(self.data)
        packages = {e["package"] for e in info["exports"]}
        self.assertIn("niagara.sys", packages)

    def test_requires_include_niagara_nre_transitive(self):
        info = self.mod.parse_module_info(self.data)
        reqs = {r["name"]: r["transitive"] for r in info["requires"]}
        self.assertIn("niagara.nre", reqs)
        self.assertTrue(reqs["niagara.nre"])

    @unittest.skipUnless(os.path.isfile(JAVAP), "javap not present at the pinned path")
    def test_cross_checked_against_javap_requires_and_exports(self):
        r = subprocess.run([JAVAP, "-p", "-c"], input=self.data, capture_output=True)
        # javap -p on classfile bytes via stdin isn't supported; use the jar path instead.
        jar_path = os.path.join(N5_MODULES_DIR, "baja.jar")
        r = subprocess.run(
            ["unzip", "-p", jar_path, "module-info.class"], capture_output=True
        )
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cls_path = os.path.join(tmp, "module-info.class")
            with open(cls_path, "wb") as fh:
                fh.write(r.stdout)
            jp = subprocess.run([JAVAP, "-p", cls_path], capture_output=True, text=True, cwd=tmp)
        javap_out = jp.stdout
        info = self.mod.parse_module_info(self.data)
        for exp in info["exports"][:5]:
            self.assertIn(f"exports {exp['package']}", javap_out)
        for req in info["requires"]:
            if req["name"] == "java.base":
                continue
            self.assertIn(req["name"], javap_out)


if __name__ == "__main__":
    unittest.main()
