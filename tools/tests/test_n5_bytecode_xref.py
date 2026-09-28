"""Tests for tools/n5-bytecode-xref.py: bytecode-level (not decompiled-text) cross-reference.

The tool answers "who calls X", "who subclasses X" and "was this instanceof+cast written as a
classic cast statement" straight from the class files, so it is immune to decompiler
resugaring and to the receiver-type blindness of the source-text call graph
(module-navigator reports 0 callers of BRootHistoryFolder.getPermissions; the bytecode has 5).

Unit tests compile small fixture sources with a JDK 25 javac into a temp dir (skipped when no
javac >= 25 is found); a smoke test runs against the real organized/ tree when present.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-bytecode-xref.py")
ORGANIZED = os.path.join(os.path.dirname(TOOLS_DIR), "organized")
JAVAC_CANDIDATES = [
    os.environ.get("N5_JAVAC", ""),
    "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac",
    shutil.which("javac") or "",
]


def _load():
    spec = importlib.util.spec_from_file_location("n5_bytecode_xref", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _javac25():
    for c in JAVAC_CANDIDATES:
        if c and os.path.exists(c):
            try:
                out = subprocess.run([c, "-version"], capture_output=True, text=True).stdout + \
                    subprocess.run([c, "-version"], capture_output=True, text=True).stderr
                major = int(out.split()[1].split(".")[0])
                if major >= 25:
                    return c
            except Exception:
                continue
    return None


JAVAC = _javac25()

FIXTURES = {
    "fx/Base.java": """
        package fx;
        public class Base {
          public Object perm(Object cx) { return "base"; }
        }
        """,
    "fx/Sub.java": """
        package fx;
        public class Sub extends Base {
          @Override public Object perm(Object cx) { return "sub"; }
        }
        """,
    "fx/Leaf.java": """
        package fx;
        public class Leaf extends Sub { }
        """,
    "fx/Caller.java": """
        package fx;
        public class Caller {
          long big = 1234567890123L;
          double d = 2.5;
          Object direct() {
            Sub s = new Sub();
            return s.perm(null);
          }
          Object viaBase(Base b, int k) {
            switch (k) {
              case 1: k += 10; break;
              case 2: k += 20; break;
              case 3: k += 30; break;
              default: k = 0;
            }
            switch (k) {
              case 100: k = 1; break;
              case 90000: k = 2; break;
              default: k = 3;
            }
            return b.perm(null);
          }
        }
        """,
    "fx/Stat.java": """
        package fx;
        public class Stat {
          static void g() { }
          static void f()
          {
            g();
          }
        }
        """,
    "fx/Casts.java": """
        package fx;
        public class Casts {
          Object pattern(Object e)
          {
            if (e instanceof String s)
            {
              return s.length();
            }
            return null;
          }
          Object classic(Object e)
          {
            if (e instanceof String)
            {
              String s = (String)e;
              return s.length();
            }
            return null;
          }
          Object sameLine(Object e)
          {
            if (e instanceof String) { String s = (String)e;
              return s.length();
            }
            return null;
          }
        }
        """,
}


@unittest.skipUnless(JAVAC, "needs a javac >= 25 (set N5_JAVAC)")
class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.tmp = tempfile.mkdtemp(prefix="b118xref-")
        src = os.path.join(cls.tmp, "src")
        cls.root = os.path.join(cls.tmp, "organized", "fixmod", "extracted")
        os.makedirs(cls.root)
        files = []
        for rel, body in FIXTURES.items():
            p = os.path.join(src, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(textwrap.dedent(body))
            files.append(p)
        subprocess.run([JAVAC, "-g", "--release", "25", "-d", cls.root] + files, check=True)
        cls.organized = os.path.join(cls.tmp, "organized")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _cf(self, name):
        with open(os.path.join(self.root, *name.split(".")) + ".class", "rb") as f:
            return self.mod.parse_class(f.read())

    def test_parse_class_reads_names_and_major_version(self):
        c = self._cf("fx.Sub")
        self.assertEqual(c["name"], "fx/Sub")
        self.assertEqual(c["super"], "fx/Base")
        self.assertEqual(c["major"], 69)
        self.assertIn("perm", [m["name"] for m in c["methods"]])

    def test_invoke_sites_carry_original_line_numbers_after_switches_and_wide_constants(self):
        c = self._cf("fx.Caller")
        sites = [s for m in c["methods"] for s in m["invokes"] if s["name"] == "perm"]
        # direct(): s.perm(null) on source line 8; viaBase(): b.perm(null) on line 22
        self.assertEqual(sorted((s["owner"], s["line"]) for s in sites), [("fx/Base", 22), ("fx/Sub", 8)])

    def test_invoke_at_a_line_table_start_pc_gets_that_line(self):
        # invokestatic g() is at pc 0, exactly where the line-7 entry starts
        c = self._cf("fx.Stat")
        f = [m for m in c["methods"] if m["name"] == "f"][0]
        self.assertEqual([(s["pc"], s["line"]) for s in f["invokes"]], [(0, 7)])

    def test_callers_exact_owner_only_by_default(self):
        idx = self.mod.build_index(self.organized)
        res = self.mod.callers(idx, "fx.Sub", "perm")
        self.assertEqual([(r["caller_class"], r["caller_method"], r["line"], r["kind"]) for r in res],
                         [("fx.Caller", "direct", 8, "exact")])

    def test_callers_cha_adds_supertype_owner_sites(self):
        idx = self.mod.build_index(self.organized)
        res = self.mod.callers(idx, "fx.Sub", "perm", cha=True)
        kinds = sorted((r["caller_method"], r["kind"], r["owner"]) for r in res)
        self.assertEqual(kinds, [("direct", "exact", "fx.Sub"), ("viaBase", "supertype-owner", "fx.Base")])

    def test_subtypes_is_transitive(self):
        idx = self.mod.build_index(self.organized)
        self.assertEqual(self.mod.subtypes(idx, "fx.Base"), ["fx.Leaf", "fx.Sub"])
        self.assertEqual(self.mod.subtypes(idx, "fx.Leaf"), [])

    def test_overriders_lists_classes_declaring_the_method(self):
        idx = self.mod.build_index(self.organized)
        self.assertEqual(self.mod.overriders(idx, "fx.Base", "perm"), ["fx.Base", "fx.Sub"])

    def test_cast_lines_classify_classic_vs_pattern_or_same_line(self):
        c = self._cf("fx.Casts")
        got = {m["name"]: [s["verdict"] for s in self.mod.cast_sites(m)] for m in c["methods"]
               if m["name"] in ("pattern", "classic", "sameLine")}
        self.assertEqual(got, {"pattern": ["pattern-or-same-line"], "classic": ["classic-separate-line"],
                               "sameLine": ["pattern-or-same-line"]})

    def test_cli_callers_json(self):
        out = subprocess.run([sys.executable, SCRIPT, "--organized", self.organized, "callers", "fx.Sub", "perm",
                              "--cha", "--json"], capture_output=True, text=True, check=True).stdout
        data = json.loads(out)
        self.assertEqual(len(data["sites"]), 2)
        self.assertEqual(data["target"], "fx.Sub.perm")

    def test_cli_unknown_class_is_an_error_not_a_zero(self):
        p = subprocess.run([sys.executable, SCRIPT, "--organized", self.organized, "callers", "fx.Nope", "perm"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("not found", p.stderr)


class ParserEdgeTests(unittest.TestCase):
    def test_rejects_non_class_bytes(self):
        mod = _load()
        with self.assertRaises(ValueError):
            mod.parse_class(b"PK\x03\x04not a class")


@unittest.skipUnless(os.path.isdir(os.path.join(ORGANIZED, "history", "extracted")), "needs organized/")
class RealCorpusSmoke(unittest.TestCase):
    def test_brootHistoryFolder_getPermissions_has_five_bytecode_callers(self):
        mod = _load()
        idx = mod.build_index(ORGANIZED, modules=["history"])
        res = mod.callers(idx, "com.tridium.history.BRootHistoryFolder", "getPermissions")
        self.assertEqual(sorted((r["caller_class"].split(".")[-1], r["line"]) for r in res),
                         [("BFoxHistorySpace", 293), ("BFoxHistorySpace", 356), ("BFoxHistorySpace", 399),
                          ("BHistorySpace", 194), ("BHistorySpace", 205)])


if __name__ == "__main__":
    unittest.main()
