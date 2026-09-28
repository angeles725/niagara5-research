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
    "fx/Other.java": """
        package fx;
        public class Other extends Base {
          public Object perm(String cx) { return "other"; }
        }
        """,
    "fx/CallerLeaf.java": """
        package fx;
        public class CallerLeaf {
          Object viaLeaf(Leaf l) {
            return l.perm(null);
          }
        }
        """,
    # fx.Other only OVERLOADS perm (perm(String), a different descriptor) -- it does NOT
    # override the inherited perm(Object), so a call through an fx.Other-typed receiver whose
    # argument is statically Object must still resolve to (and invoke) the INHERITED perm(Object),
    # with a symbolic invokevirtual owner of fx/Other (R2-001/R2-002/R3-003/R3-004: without this
    # real call site, "fx.Other must never be offered as a subtype-owner" was never actually
    # exercised -- there was nothing to observe the claim through).
    "fx/CallerOther.java": """
        package fx;
        public class CallerOther {
          Object viaOther(Other o) {
            Object arg = "via-other";
            return o.perm(arg);
          }
        }
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
        self.assertEqual(kinds, [("direct", "exact", "fx.Sub"), ("viaBase", "supertype-owner", "fx.Base"),
                                 ("viaLeaf", "subtype-owner", "fx.Leaf")])

    # R3-001: --cha must also accept a receiver whose static owner is a SUBTYPE that inherits the
    # method (invokevirtual/invokeinterface on a subclass that does not redeclare it). fx.Leaf
    # extends fx.Sub without overriding perm, so l.perm(null) in fx.CallerLeaf dispatches to
    # fx.Sub.perm at run time; the old CHA (supertypes-only) silently missed this real caller.
    def test_callers_cha_adds_inheriting_subtype_owner_sites(self):
        idx = self.mod.build_index(self.organized)
        res = self.mod.callers(idx, "fx.Sub", "perm", cha=True)
        kinds = sorted((r["caller_class"], r["kind"], r["owner"]) for r in res)
        self.assertIn(("fx.CallerLeaf", "subtype-owner", "fx.Leaf"), kinds)

    def test_callers_cha_subtype_owner_stops_at_a_redeclaring_override(self):
        # fx.Sub REDECLARES perm(Object) exactly (an @Override, same descriptor): it and its own
        # subtype fx.Leaf must never be offered as a subtype-owner for a DIRECT fx.Base.perm(Object)
        # query -- their calls dispatch through Sub's own override (already reachable via the
        # fx.Sub target itself, not via widening from fx.Base).
        idx = self.mod.build_index(self.organized)
        res = self.mod.callers(idx, "fx.Base", "perm", desc="(Ljava/lang/Object;)Ljava/lang/Object;", cha=True)
        owners = {r["owner"] for r in res}
        self.assertNotIn("fx.Sub", owners)
        self.assertNotIn("fx.Leaf", owners)
        # fx.Other only OVERLOADS perm (perm(String) -- a different descriptor); it does NOT
        # redeclare perm(Object), so it correctly remains eligible, and fx.CallerOther's real
        # invoke site on it (R2-001/R2-002/R3-003/R3-004 -- see fixture) proves the CHA widening
        # actually reaches it, rather than passing vacuously because no site touched fx.Other at
        # all (the old version of this test never had such a site).
        self.assertIn("fx.Other", owners)

    def test_subtypes_is_transitive(self):
        idx = self.mod.build_index(self.organized)
        self.assertEqual(self.mod.subtypes(idx, "fx.Base"), ["fx.Leaf", "fx.Other", "fx.Sub"])
        self.assertEqual(self.mod.subtypes(idx, "fx.Leaf"), [])

    def test_overriders_lists_classes_declaring_the_method(self):
        idx = self.mod.build_index(self.organized)
        self.assertEqual(self.mod.overriders(idx, "fx.Base", "perm"), ["fx.Base", "fx.Sub"])

    # R2-001: overriders must match name AND descriptor. fx.Other extends fx.Base and declares a
    # perm(String) overload -- same name, different descriptor -- so it is a real subtype but NOT
    # a real overrider of Base.perm(Object). The old name-only match reported it as a false
    # overrider.
    def test_overriders_excludes_name_match_with_different_descriptor(self):
        idx = self.mod.build_index(self.organized)
        self.assertNotIn("fx.Other", self.mod.overriders(idx, "fx.Base", "perm"))

    def test_overriders_explicit_desc_filters_to_that_overload(self):
        idx = self.mod.build_index(self.organized)
        self.assertEqual(self.mod.overriders(idx, "fx.Base", "perm", desc="(Ljava/lang/String;)Ljava/lang/Object;"),
                         ["fx.Other"])

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
        # exact (fx.Sub), supertype-owner (fx.Base) and subtype-owner (fx.Leaf, R3-001)
        self.assertEqual(len(data["sites"]), 3)
        self.assertEqual(data["target"], "fx.Sub.perm")
        self.assertEqual(data["parse_errors"], 0)
        self.assertEqual(data["duplicate_classes"], 0)

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


# R2-002/R3-004: _inheriting_subtypes must infer the base's own unambiguous descriptor when none
# is given, exactly like overriders() already does (R2-001) -- otherwise an unrelated overload
# (same method NAME, different descriptor) declared on a subtype is wrongly treated as a
# redeclaration of the base method. That stops CHA descent at that subtype, silently dropping
# every real subtype-owner candidate below it, even though the subtype never actually overrode
# the method being queried. Exercised directly against a hand-built index (no javac / real class
# files needed) so it always runs, unlike the FixtureTests below.
class InheritingSubtypesDescInferenceTests(unittest.TestCase):
    @staticmethod
    def _idx():
        return {
            "classes": {
                "p/Base": {"name": "p/Base", "methods": [{"name": "m", "desc": "()V"}]},
                # Overload only -- declares "m" but with a DIFFERENT descriptor than Base's "m".
                # It does NOT redeclare Base.m()V.
                "p/Overload": {"name": "p/Overload", "methods": [{"name": "m", "desc": "(I)V"}]},
                "p/Grandchild": {"name": "p/Grandchild", "methods": []},
                # A genuine redeclaration (same name AND descriptor) -- descent must stop here.
                "p/RealOverride": {"name": "p/RealOverride", "methods": [{"name": "m", "desc": "()V"}]},
                "p/OverrideChild": {"name": "p/OverrideChild", "methods": []},
            },
            "children": {
                "p/Base": ["p/Overload", "p/RealOverride"],
                "p/Overload": ["p/Grandchild"],
                "p/RealOverride": ["p/OverrideChild"],
            },
        }

    def test_unrelated_overload_does_not_stop_descent_when_desc_omitted(self):
        mod = _load()
        out = mod._inheriting_subtypes(self._idx(), "p.Base", "m", None)
        self.assertEqual(sorted(out), ["p/Grandchild", "p/Overload"])

    def test_real_override_still_stops_descent_when_desc_omitted(self):
        mod = _load()
        out = mod._inheriting_subtypes(self._idx(), "p.Base", "m", None)
        self.assertNotIn("p/RealOverride", out)
        self.assertNotIn("p/OverrideChild", out)


# R2-002: the same internal class name appearing in two modules must not be dropped silently.
@unittest.skipUnless(JAVAC, "needs a javac >= 25 (set N5_JAVAC)")
class DuplicateClassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.tmp = tempfile.mkdtemp(prefix="b118xref-dup-")
        src = os.path.join(cls.tmp, "src")
        p = os.path.join(src, "dup", "A.java")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(textwrap.dedent("""
                package dup;
                public class A {
                  public void m() { }
                }
                """))
        cls.organized = os.path.join(cls.tmp, "organized")
        for modname in ("mod1", "mod2"):
            root = os.path.join(cls.organized, modname, "extracted")
            os.makedirs(root)
            subprocess.run([JAVAC, "-g", "--release", "25", "-d", root, p], check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_build_index_reports_duplicate_class_and_its_modules(self):
        idx = self.mod.build_index(self.organized)
        self.assertIn("dup/A", idx["duplicates"])
        self.assertEqual(sorted(idx["duplicates"]["dup/A"]), ["mod1", "mod2"])
        # still indexed and queryable (kept, not dropped)
        self.assertIn("dup/A", idx["classes"])

    def test_cli_reports_duplicate_count(self):
        out = subprocess.run([sys.executable, SCRIPT, "--organized", self.organized, "subtypes", "dup.A", "--json"],
                              capture_output=True, text=True, check=True).stdout
        data = json.loads(out)
        self.assertEqual(data.get("duplicate_classes"), 1)


# R4: parse errors (classes javap/this parser failed on) must be surfaced in every subcommand's
# output, never silently skipped.
@unittest.skipUnless(JAVAC, "needs a javac >= 25 (set N5_JAVAC)")
class ParseErrorSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.tmp = tempfile.mkdtemp(prefix="b118xref-broken-")
        src = os.path.join(cls.tmp, "src")
        p = os.path.join(src, "pe", "Ok.java")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(textwrap.dedent("""
                package pe;
                public class Ok {
                  public void m() { }
                }
                """))
        cls.organized = os.path.join(cls.tmp, "organized")
        root = os.path.join(cls.organized, "pemod", "extracted")
        os.makedirs(root)
        subprocess.run([JAVAC, "-g", "--release", "25", "-d", root, p], check=True)
        with open(os.path.join(root, "Broken.class"), "wb") as f:
            f.write(b"not a class file at all, definitely bogus bytes")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run(self, *args):
        return subprocess.run([sys.executable, SCRIPT, "--organized", self.organized] + list(args),
                               capture_output=True, text=True, check=True)

    def test_build_index_records_the_parse_error(self):
        idx = self.mod.build_index(self.organized)
        self.assertEqual(len(idx["errors"]), 1)

    def test_subtypes_json_reports_parse_errors(self):
        out = json.loads(self._run("subtypes", "pe.Ok", "--json").stdout)
        self.assertEqual(out.get("parse_errors"), 1)

    def test_overriders_json_reports_parse_errors(self):
        out = json.loads(self._run("overriders", "pe.Ok", "m", "--json").stdout)
        self.assertEqual(out.get("parse_errors"), 1)

    def test_casts_json_reports_parse_errors(self):
        out = json.loads(self._run("casts", "pe.Ok", "--json").stdout)
        self.assertEqual(out.get("parse_errors"), 1)

    def test_subtypes_text_mentions_parse_errors(self):
        out = self._run("subtypes", "pe.Ok").stdout
        self.assertIn("parse error", out)

    def test_overriders_text_mentions_parse_errors(self):
        out = self._run("overriders", "pe.Ok", "m").stdout
        self.assertIn("parse error", out)

    def test_casts_text_mentions_parse_errors(self):
        out = self._run("casts", "pe.Ok").stdout
        self.assertIn("parse error", out)


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
