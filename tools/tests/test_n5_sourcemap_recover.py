"""Tests for tools/n5-sourcemap-recover.py (B119): recover original sources from shipped source maps.

Hermetic: a small fixture organized/ tree lives under tools/tests/fixtures/sourcemap/. A smoke test runs
against the real corpus when it is present.
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-sourcemap-recover.py")
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sourcemap", "corpus")
REAL_ORGANIZED = "/home/cristian/niagara5-research/organized"


def _load():
    spec = importlib.util.spec_from_file_location("n5_sourcemap_recover", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


class NormalizeSourceTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def test_webpack_triple_slash_prefix(self):
        self.assertEqual(self.m.normalize_source("webpack:///./src/b.js"), ("src/b.js", 0))

    def test_webpack_namespace_prefix(self):
        self.assertEqual(self.m.normalize_source("webpack://ns/src/n/c.js"), ("src/n/c.js", 0))

    def test_leading_parent_dirs_are_stripped_and_counted(self):
        self.assertEqual(self.m.normalize_source("../../../src/rc/a.js"), ("src/rc/a.js", 3))

    def test_rejects_absolute_and_drive_and_inner_dotdot_and_nul(self):
        for bad in ["/etc/shadow", "C:\\win\\x.js", "src/../../escape.js", "a/../b.js", "x\0y.js", "", "../..", "webpack:///"]:
            with self.subTest(bad=bad):
                self.assertIsNone(self.m.normalize_source(bad))

    def test_backslashes_become_slashes(self):
        self.assertEqual(self.m.normalize_source("src\\x\\y.js"), ("src/x/y.js", 0))


class RecoverCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out")
        self.addCleanup(self.tmp.cleanup)

    def _recover(self):
        r = _run("--organized-dir", FIXTURE, "--out-dir", self.out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.out, "manifest.json"), encoding="utf-8") as fh:
            return r, json.load(fh)

    def _entries(self, manifest, status=None):
        rows = [e for m in manifest["maps"] for e in m.get("sources", [])]
        return [e for e in rows if status is None or e["status"] == status]

    def test_recovers_byte_exact_content_with_hashes(self):
        _, mf = self._recover()
        p = os.path.join(self.out, "modA", "src", "rc", "a.js")
        data = open(p, "rb").read()
        self.assertEqual(data, "/** original A */\nconst f = () => 1;\n".encode())
        entry = [e for e in self._entries(mf, "recovered") if e["path"] == "modA/src/rc/a.js"][0]
        self.assertEqual(entry["content_sha256"], _sha(data))
        amap = [m for m in mf["maps"] if m["map"].endswith("modA/extracted/rc/a.js.map")][0]
        self.assertEqual(amap["map_sha256"], _sha(open(os.path.join(FIXTURE, "modA/extracted/rc/a.js.map"), "rb").read()))

    def test_only_extracted_tree_is_scanned(self):
        _, mf = self._recover()
        maps = [m["map"] for m in mf["maps"]]
        self.assertFalse(any("vineflower" in m for m in maps))
        self.assertFalse(any(m.startswith("_lib-inf-3p") for m in maps))
        self.assertEqual(sum(1 for m in maps if m.startswith("modA/")), 2)

    def test_map_without_sourcescontent_is_listed_but_writes_nothing(self):
        _, mf = self._recover()
        e = [e for e in self._entries(mf) if e["source"].endswith("modA.less")][0]
        self.assertEqual(e["status"], "no-sourcesContent")
        self.assertFalse(os.path.exists(os.path.join(self.out, "modA", "module")))

    def test_webpack_prefixes_and_leading_parent_dirs(self):
        _, mf = self._recover()
        self.assertEqual(open(os.path.join(self.out, "modB", "src", "b.js")).read(), "// b\n")
        self.assertEqual(open(os.path.join(self.out, "modB", "src", "nested", "c.js")).read(), "// c\n")
        e = [e for e in self._entries(mf, "recovered") if e["path"] == "modB/etc/passwd"][0]
        self.assertEqual(e["parent_dirs_stripped"], 4)

    def test_unsafe_paths_rejected_and_nothing_escapes_out_dir(self):
        _, mf = self._recover()
        rejected = {e["source"] for e in self._entries(mf, "rejected-unsafe-path")}
        self.assertEqual(rejected, {"/etc/shadow", "src/../../escape.js", "C:\\win\\x.js"})
        for root, _dirs, files in os.walk(self.tmp.name):
            for f in files:
                self.assertTrue(os.path.join(root, f).startswith(self.out + os.sep), os.path.join(root, f))
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "escape.js")))

    def test_collision_with_different_content_does_not_overwrite(self):
        _, mf = self._recover()
        self.assertEqual(open(os.path.join(self.out, "modB", "src", "b.js")).read(), "// b\n")
        col = self._entries(mf, "collision")
        self.assertEqual([e["path"] for e in col], ["modB/src/b.js"])

    def test_null_content_and_empty_string(self):
        _, mf = self._recover()
        self.assertEqual([e["source"] for e in self._entries(mf, "no-content")], ["src/null.js"])
        self.assertEqual(open(os.path.join(self.out, "modB", "src", "empty.js"), "rb").read(), b"")

    def test_non_json_map_is_recorded_not_parsed(self):
        _, mf = self._recover()
        bad = [m for m in mf["maps"] if m["map"].endswith("x.address.map")][0]
        self.assertEqual(bad["status"], "not-a-sourcemap")

    def test_manifest_is_deterministic_and_summarised(self):
        r, mf = self._recover()
        first = open(os.path.join(self.out, "manifest.json"), "rb").read()
        self._recover()
        self.assertEqual(first, open(os.path.join(self.out, "manifest.json"), "rb").read())
        s = mf["summary"]
        self.assertEqual((s["maps"], s["maps_with_sourcesContent"], s["recovered"]), (5, 3, 5))
        self.assertIn("recovered 5", r.stdout)

    def test_missing_organized_dir_is_usage_error(self):
        r = _run("--organized-dir", os.path.join(self.tmp.name, "nope"))
        self.assertEqual(r.returncode, 2)


@unittest.skipUnless(os.path.isdir(os.path.join(REAL_ORGANIZED, "driver", "extracted")), "real N5 corpus not present")
class RealCorpusSmokeTest(unittest.TestCase):
    def test_real_counts(self):
        with tempfile.TemporaryDirectory() as t:
            r = _run("--organized-dir", REAL_ORGANIZED, "--out-dir", t)
            self.assertEqual(r.returncode, 0, r.stderr)
            s = json.load(open(os.path.join(t, "manifest.json")))["summary"]
            self.assertEqual(s["recovered"], 42)
            self.assertEqual(s["rejected_unsafe_path"], 0)


if __name__ == "__main__":
    unittest.main()
