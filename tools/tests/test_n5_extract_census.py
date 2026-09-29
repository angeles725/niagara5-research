"""Tests for tools/n5-extract-census.py: extraction completeness + integrity census.

The census answers "are the bytes the decompile pipeline analysed exactly the
vendor's bytes, and was anything inside the jar left unanalysed?" Unit tests
build small synthetic jars in a temp dir so every rule is verified hermetically;
a smoke test runs against one real N5 module when the install is present.
"""
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-extract-census.py")
N5_MODULES_DIR = "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
N5_ORGANIZED = os.path.join(os.path.dirname(TOOLS_DIR), "organized")


def _load():
    spec = importlib.util.spec_from_file_location("n5_extract_census", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CLASS_MAGIC = b"\xca\xfe\xba\xbe\x00\x00\x00\x45"  # major 69


def _jar_bytes(entries, manifest=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        if manifest is not None:
            zf.writestr("META-INF/MANIFEST.MF", manifest)
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def _pe_bytes():
    """Minimal DOS header + PE signature: e_lfanew (0x3c) -> 0x80, "PE\\0\\0" there."""
    buf = bytearray(0x100)
    buf[0:2] = b"MZ"
    buf[0x3c:0x40] = (0x80).to_bytes(4, "little")
    buf[0x80:0x84] = b"PE\x00\x00"
    return bytes(buf)


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


class TridiumShareTest(unittest.TestCase):
    def test_counts_tridium_namespaces(self):
        m = _load()
        names = [
            "com/tridium/a/A.class",
            "javax/baja/b/B.class",
            "niagara/c/C.class",
            "org/other/D.class",
            "com/tridium/x.lexicon",
        ]
        self.assertEqual(m.tridium_share(names), (3, 4))


class NestedJarTest(unittest.TestCase):
    def test_nested_jar_census_reports_classes_and_tridium(self):
        m = _load()
        inner = _jar_bytes({
            "com/tridium/slot/S.class": CLASS_MAGIC,
            "org/lib/L.class": CLASS_MAGIC,
        })
        info = m.nested_jar_census("LIB-INF/inner.jar", inner, release=25)
        self.assertEqual(info["classes"], 2)
        self.assertEqual(info["tridium_classes"], 1)
        self.assertFalse(info["multi_release"])
        self.assertEqual(info["sha256"], hashlib.sha256(inner).hexdigest())

    def test_nested_multi_release_selection_for_release(self):
        m = _load()
        inner = _jar_bytes(
            {
                "org/lib/A.class": CLASS_MAGIC,
                "META-INF/versions/9/org/lib/A.class": CLASS_MAGIC,
                "META-INF/versions/21/org/lib/A.class": CLASS_MAGIC,
                "META-INF/versions/26/org/lib/A.class": CLASS_MAGIC,
                "META-INF/versions/11/module-info.class": CLASS_MAGIC,
            },
            manifest="Manifest-Version: 1.0\r\nMulti-Release: true\r\n\r\n",
        )
        info = m.nested_jar_census("LIB-INF/mr.jar", inner, release=25)
        self.assertTrue(info["multi_release"])
        self.assertEqual(info["mr_versions"], [9, 11, 21, 26])
        # On release 25 the JVM loads versions/21 (highest <= 25), not base, not 26.
        self.assertEqual(info["mr_selected"]["org/lib/A.class"],
                         "META-INF/versions/21/org/lib/A.class")
        self.assertEqual(info["mr_overridden_classes"], 2)

    def test_versions_dir_without_manifest_flag_is_not_multi_release(self):
        m = _load()
        inner = _jar_bytes({
            "org/lib/A.class": CLASS_MAGIC,
            "META-INF/versions/9/org/lib/A.class": CLASS_MAGIC,
        })
        info = m.nested_jar_census("LIB-INF/x.jar", inner, release=25)
        self.assertFalse(info["multi_release"])
        self.assertEqual(info["mr_selected"], {})


class ByteExactTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()
        self.tmp = tempfile.mkdtemp()
        self.jar = os.path.join(self.tmp, "mod.jar")
        _write(self.jar, _jar_bytes({
            "com/tridium/a/A.class": CLASS_MAGIC + b"A",
            "com/tridium/a/B.class": CLASS_MAGIC + b"B",
            "com/tridium/a/x.lexicon": b"k=v\n",
            "LIB-INF/in.jar": _jar_bytes({"com/tridium/q/Q.class": CLASS_MAGIC}),
        }))
        self.moddir = os.path.join(self.tmp, "mod")
        _write(os.path.join(self.moddir, "extracted/com/tridium/a/A.class"), CLASS_MAGIC + b"A")
        _write(os.path.join(self.moddir, "extracted/com/tridium/a/B.class"), CLASS_MAGIC + b"TAMPERED")
        _write(os.path.join(self.moddir, "extracted/com/tridium/a/x.lexicon"), b"k=v\n")
        _write(os.path.join(self.moddir, "resources/com/tridium/a/x.lexicon"), b"k=v\n")
        # LIB-INF/in.jar missing from extracted/ and resources/ on purpose

    def test_detects_mismatch_and_missing(self):
        r = self.m.census_module(self.jar, self.moddir, release=25)
        self.assertEqual(r["classes"]["checked"], 2)
        self.assertEqual(r["classes"]["mismatched"], ["com/tridium/a/B.class"])
        self.assertEqual(r["classes"]["missing"], [])
        self.assertEqual(r["resources"]["expected"], 2)
        self.assertIn("LIB-INF/in.jar", r["resources"]["missing"])
        self.assertEqual(r["nested"][0]["name"], "LIB-INF/in.jar")
        self.assertEqual(r["nested"][0]["tridium_classes"], 1)
        self.assertEqual(r["nested_classes_total"], 1)
        self.assertEqual(r["nested_classes_decompiled"], 0)

    def test_clean_module_reports_no_mismatch(self):
        _write(os.path.join(self.moddir, "extracted/com/tridium/a/B.class"), CLASS_MAGIC + b"B")
        r = self.m.census_module(self.jar, self.moddir, release=25)
        self.assertEqual(r["classes"]["mismatched"], [])


class PayloadClassifierTest(unittest.TestCase):
    def test_native_magic(self):
        m = _load()
        self.assertEqual(m.native_format(_pe_bytes()), "PE")
        self.assertEqual(m.native_format(b"\x7fELF\x02\x01"), "ELF")
        self.assertEqual(m.native_format(b"\xcf\xfa\xed\xfe"), "Mach-O")
        self.assertIsNone(m.native_format(b"PK\x03\x04"))

    def test_mz_alone_is_not_a_pe(self):
        # "MZ" is two ASCII letters: plain text, a CSV or a resource can start with it. A PE needs
        # the e_lfanew pointer at 0x3c to land on the "PE\\0\\0" signature.
        m = _load()
        self.assertIsNone(m.native_format(b"MZ marks the spot\n" + b"x" * 100))
        self.assertIsNone(m.native_format(b"MZ\x90\x00" + b"\x00" * 60))  # e_lfanew = 0
        self.assertIsNone(m.native_format(b"MZ" + b"\x00" * 0x3a + b"\xff\xff\x00\x00"))  # points past EOF
        self.assertIsNone(m.native_format(b"MZ"))
        wrong_sig = bytearray(_pe_bytes())
        wrong_sig[0x80:0x84] = b"NE\x00\x00"
        self.assertIsNone(m.native_format(bytes(wrong_sig)))

    def test_census_does_not_report_mz_text_resource_as_native(self):
        m = _load()
        tmp = tempfile.mkdtemp()
        jar = os.path.join(tmp, "m.jar")
        _write(jar, _jar_bytes({"a/A.class": CLASS_MAGIC, "a/notes.txt": b"MZ text file " * 20,
                                "a/real.dll": _pe_bytes()}))
        moddir = os.path.join(tmp, "m")
        _write(os.path.join(moddir, "extracted/a/A.class"), CLASS_MAGIC)
        r = m.census_module(jar, moddir)
        self.assertEqual([n["name"] for n in r["natives"]], ["a/real.dll"])

    def test_minified_js(self):
        m = _load()
        readable = b"function f(a) {\n  return a + 1;\n}\n" * 50
        minified = b"!function(e){" + b"var a=1;" * 400 + b"}();"
        self.assertFalse(m.is_minified_js(readable))
        self.assertTrue(m.is_minified_js(minified))


class CliTest(unittest.TestCase):
    def test_cli_module_json(self):
        tmp = tempfile.mkdtemp()
        jar = os.path.join(tmp, "m.jar")
        _write(jar, _jar_bytes({"com/tridium/a/A.class": CLASS_MAGIC}))
        moddir = os.path.join(tmp, "m")
        _write(os.path.join(moddir, "extracted/com/tridium/a/A.class"), CLASS_MAGIC)
        out = subprocess.run(
            [sys.executable, SCRIPT, "module", jar, moddir, "--json"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        data = json.loads(out.stdout)
        self.assertEqual(data["classes"]["checked"], 1)

    def test_cli_exit_1_on_mismatch(self):
        tmp = tempfile.mkdtemp()
        jar = os.path.join(tmp, "m.jar")
        _write(jar, _jar_bytes({"com/tridium/a/A.class": CLASS_MAGIC}))
        moddir = os.path.join(tmp, "m")
        _write(os.path.join(moddir, "extracted/com/tridium/a/A.class"), b"x")
        out = subprocess.run(
            [sys.executable, SCRIPT, "module", jar, moddir, "--json"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(out.returncode, 1)


class ExitCodeTest(unittest.TestCase):
    """Exit-code contract: 0 clean, 1 census found a mismatch, 2 usage (argparse), 3 read/internal
    error. A crash must never masquerade as 1 (mismatch) nor a mismatch as 2 (usage)."""

    def _run(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
                              check=False)

    def test_missing_jar_is_exit_3(self):
        tmp = tempfile.mkdtemp()
        out = self._run("module", os.path.join(tmp, "nope.jar"), tmp)
        self.assertEqual(out.returncode, 3, out.stderr)

    def test_corrupt_jar_is_exit_3(self):
        tmp = tempfile.mkdtemp()
        jar = os.path.join(tmp, "bad.jar")
        _write(jar, b"this is not a zip")
        out = self._run("module", jar, tmp)
        self.assertEqual(out.returncode, 3, out.stderr)

    def test_unexpected_exception_is_exit_3_not_1(self):
        # A corrupt deflate stream raises BadZipFile/zlib.error; an uncaught traceback would
        # exit 1 == "mismatch".
        tmp = tempfile.mkdtemp()
        jar = os.path.join(tmp, "trunc.jar")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("a/A.class", CLASS_MAGIC + os.urandom(4000))
        raw = bytearray(buf.getvalue())
        raw[60:120] = b"\x00" * 60  # corrupt the deflate stream, keep the directory intact
        _write(jar, bytes(raw))
        out = self._run("module", jar, tmp)
        self.assertEqual(out.returncode, 3, out.stderr)
        self.assertNotIn("Traceback", out.stderr)

    def test_usage_error_is_exit_2(self):
        self.assertEqual(self._run().returncode, 2)


class SweepTest(unittest.TestCase):
    """sweep(): aggregation, selection, and per-module error isolation."""

    def setUp(self):
        self.m = _load()
        self.tmp = tempfile.mkdtemp()
        self.jars = os.path.join(self.tmp, "modules")
        self.org = os.path.join(self.tmp, "organized")
        os.makedirs(self.jars)

    def _module(self, name, entries, tamper=False, recon=True):
        _write(os.path.join(self.jars, name + ".jar"), _jar_bytes(entries))
        moddir = os.path.join(self.org, name)
        os.makedirs(moddir, exist_ok=True)
        if recon:
            _write(os.path.join(moddir, "recon.json"), b"{}")
        for entry, data in entries.items():
            sub = "extracted" if entry.endswith(".class") else "resources"
            _write(os.path.join(moddir, sub, entry), b"X" if tamper else data)

    def test_aggregates_and_lists_unclean_modules(self):
        self._module("good", {"a/A.class": CLASS_MAGIC + b"1", "a/r.txt": b"r"})
        self._module("bad", {"b/B.class": CLASS_MAGIC + b"2"}, tamper=True)
        agg, mods = self.m.sweep(self.jars, self.org)
        self.assertEqual(agg["modules"], 2)
        self.assertEqual(agg["classes_checked"], 2)
        self.assertEqual(agg["class_mismatches"], 1)
        self.assertEqual(agg["unclean_modules"], ["bad"])
        self.assertEqual([os.path.basename(x["moddir"]) for x in mods], ["bad", "good"])

    def test_jar_without_recon_is_reported_skipped_not_silently_dropped(self):
        self._module("good", {"a/A.class": CLASS_MAGIC})
        self._module("poc", {"p/P.class": CLASS_MAGIC}, recon=False)
        agg, _ = self.m.sweep(self.jars, self.org)
        self.assertEqual(agg["modules"], 1)
        self.assertEqual(agg["skipped_no_recon"], ["poc"])

    def test_one_corrupt_jar_does_not_abort_the_sweep(self):
        self._module("aaa", {"a/A.class": CLASS_MAGIC})
        _write(os.path.join(self.jars, "bbb.jar"), b"not a zip")
        _write(os.path.join(self.org, "bbb", "recon.json"), b"{}")
        self._module("ccc", {"c/C.class": CLASS_MAGIC})
        agg, mods = self.m.sweep(self.jars, self.org)
        self.assertEqual(agg["modules"], 2)  # aaa and ccc were still censused
        self.assertEqual([e["module"] for e in agg["errored_modules"]], ["bbb"])
        self.assertEqual(agg["unclean_modules"], [])

    def test_cli_sweep_exit_codes(self):
        self._module("good", {"a/A.class": CLASS_MAGIC})
        run = lambda: subprocess.run([sys.executable, SCRIPT, "sweep", self.jars, self.org],
                                     capture_output=True, text=True, check=False)
        self.assertEqual(run().returncode, 0)
        _write(os.path.join(self.jars, "bbb.jar"), b"not a zip")
        _write(os.path.join(self.org, "bbb", "recon.json"), b"{}")
        self.assertEqual(run().returncode, 3)  # unreadable module: cannot attest, not "clean"
        self._module("ddd", {"d/D.class": CLASS_MAGIC}, tamper=True)
        self.assertEqual(run().returncode, 1)  # a real mismatch outranks the read error


class EntryPathTest(unittest.TestCase):
    def test_safe_entry_path_normalizes_and_rejects_escapes(self):
        m = _load()
        self.assertEqual(m.safe_entry_path("a/b/C.class"), "a/b/C.class")
        self.assertEqual(m.safe_entry_path("a/./b//C.class"), "a/b/C.class")
        self.assertEqual(m.safe_entry_path("a/x/../C.class"), "a/C.class")
        for bad in ("../evil.class", "a/../../evil.class", "/abs/E.class", "a\\b.class",
                    "a/b\x00.class", "..", ""):
            self.assertIsNone(m.safe_entry_path(bad), bad)

    def test_traversal_entry_is_unsafe_and_never_read_outside_moddir(self):
        m = _load()
        tmp = tempfile.mkdtemp()
        # A file OUTSIDE the module dir whose bytes equal the hostile entry's bytes: the old
        # os.path.join(ext_dir, "../../decoy.class") would have "matched" it byte-exactly.
        _write(os.path.join(tmp, "decoy.class"), CLASS_MAGIC + b"E")
        moddir = os.path.join(tmp, "org", "mod")
        os.makedirs(os.path.join(moddir, "extracted"))
        jar = os.path.join(tmp, "m.jar")
        _write(jar, _jar_bytes({"../../decoy.class": CLASS_MAGIC + b"E",
                                "a/./A.class": CLASS_MAGIC + b"A"}))
        _write(os.path.join(moddir, "extracted/a/A.class"), CLASS_MAGIC + b"A")
        r = m.census_module(jar, moddir)
        self.assertEqual(r["unsafe_entries"], ["../../decoy.class"])
        self.assertEqual(r["classes"]["mismatched"], [])
        self.assertEqual(r["classes"]["missing"], [])  # a/./A.class resolved to a/A.class
        self.assertFalse(m.is_clean(r))


class NestedUnreadableTest(unittest.TestCase):
    def test_corrupt_nested_jar_is_reported_not_silently_skipped(self):
        m = _load()
        tmp = tempfile.mkdtemp()
        jar = os.path.join(tmp, "m.jar")
        broken = b"PK\x03\x04" + b"garbage" * 10
        _write(jar, _jar_bytes({"a/A.class": CLASS_MAGIC, "LIB-INF/broken.jar": broken}))
        moddir = os.path.join(tmp, "m")
        _write(os.path.join(moddir, "extracted/a/A.class"), CLASS_MAGIC)
        _write(os.path.join(moddir, "resources/LIB-INF/broken.jar"), broken)
        r = m.census_module(jar, moddir)
        self.assertEqual(r["nested"], [])
        self.assertEqual([n["name"] for n in r["nested_unreadable"]], ["LIB-INF/broken.jar"])
        self.assertEqual(r["nested_unreadable"][0]["sha256"], hashlib.sha256(broken).hexdigest())


@unittest.skipUnless(os.path.isfile(os.path.join(N5_MODULES_DIR, "control.jar"))
                     and os.path.isdir(os.path.join(N5_ORGANIZED, "control")),
                     "real N5 install / organized tree not present")
class RealInstallSmokeTest(unittest.TestCase):
    def test_control_module_is_byte_exact(self):
        m = _load()
        r = m.census_module(os.path.join(N5_MODULES_DIR, "control.jar"),
                            os.path.join(N5_ORGANIZED, "control"), release=25)
        self.assertEqual(r["classes"]["mismatched"], [])
        self.assertEqual(r["classes"]["missing"], [])
        self.assertGreater(r["classes"]["checked"], 0)


if __name__ == "__main__":
    unittest.main()
