#!/usr/bin/env python3
"""tools/n5-splice-methods.py (T21/F9): per-method source splice
(meta-decompilation). A method of the primary decompile that does not
round-trip is replaced, and nothing else is, by another engine's version of the
same method whose own recompile matches the shipped method; the splice counts
only when the whole spliced class then grades clean."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS_DIR = Path(__file__).resolve().parent.parent
SCRIPT = TOOLS_DIR / "n5-splice-methods.py"
JDK = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin"


def _load():
    spec = importlib.util.spec_from_file_location("n5_splice_methods", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _jdk() -> bool:
    return all(os.path.isfile(f"{JDK}/{t}") for t in ("javac", "java", "javap"))


class TestPure(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_import_planning(self):
        plan = self.mod.plan_type_import
        primary = {"package": "p", "imports": [{"static": False, "name": "q.List"},
                                               {"static": False, "name": "r.*"}],
                   "members": ["type|p/Foo$Node"]}
        ref = lambda s, q, b: {"simple": s, "qname": q, "binary": b, "nest": False}  # noqa: E731
        self.assertIsNone(plan(primary, ref("String", "java.lang.String", "java/lang/String")))
        self.assertIsNone(plan(primary, ref("Bar", "p.Bar", "p/Bar")))
        self.assertIsNone(plan(primary, ref("X", "r.X", "r/X")))
        self.assertEqual(plan(primary, ref("Map", "java.util.Map", "java/util/Map")), "java.util.Map")
        with self.assertRaises(self.mod.Refusal) as cm:
            plan(primary, ref("List", "java.util.List", "java/util/List"))
        self.assertEqual(cm.exception.reason, "import-conflict")
        with self.assertRaises(self.mod.Refusal) as cm:
            plan(primary, ref("Node", "z.Node", "z/Node"))
        self.assertEqual(cm.exception.reason, "import-conflict")

    def test_render_changes_only_the_spans_and_adds_imports(self):
        text = "package p;\n\nimport a.B;\n\nclass C {\n  int f() { return 1; }\n  int g() { return 2; }\n}\n"
        f_at = text.index("int f()")
        f_end = text.index("}", f_at) + 1
        out = self.mod.render_splice(text, [(f_at, f_end, "int f() { return 3; }")], ["x.Y"],
                                     {"package_end": text.index(";") + 1,
                                      "imports": [{"end": text.index("B;") + 2}]})
        self.assertEqual(out, text.replace("return 1;", "return 3;").replace("import a.B;", "import a.B;\nimport x.Y;"))


SHIPPED = """package p;
import java.util.List;
public class Foo {
  int k;
  public Foo(int k) { this.k = k; }
  static int f(int a, int b) { return a - b; }
  static int f(String s) { return s.length() * 3; }
  <T extends Comparable<T>> int g(List<T> xs, String... more) { return xs.size() + more.length; }
  int h() { return k + 1; }
}
"""
# primary: f(int,int) wrong (b - a) -- everything else right
PRIMARY = SHIPPED.replace("return a - b;", "return b - a;")
# cfr: f(int,int) right with other parameter names, h wrong
CFR = SHIPPED.replace("static int f(int a, int b) { return a - b; }",
                      "static int f(int x, int y) {\n    return x - y;\n  }").replace("return k + 1;", "return k + 2;")
# procyon: everything wrong in f(int,int)
PROCYON = SHIPPED.replace("return a - b;", "return a + b;")


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.td = tempfile.TemporaryDirectory()
        root = Path(cls.td.name)
        cls.root = root
        cls.helper = cls.mod.compile_helper(root / "helper", f"{JDK}/javac")

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def _module(self, name, shipped, primary, cfr, procyon, extra_shipped=None):
        mod_dir = self.root / "organized" / name
        src = self.root / f"src-{name}" / "p" / "Foo.java"
        src.parent.mkdir(parents=True)
        src.write_text(shipped)
        (mod_dir / "extracted").mkdir(parents=True)
        subprocess.run([f"{JDK}/javac", "--release", "25", "-g", "-d", str(mod_dir / "extracted"), str(src)],
                       check=True, capture_output=True)
        (mod_dir / "vineflower2" / "p").mkdir(parents=True)
        (mod_dir / "vineflower2" / "p" / "Foo.java").write_text(primary)
        donors = {"cfr": cfr, "procyon": procyon}

        def fake_decompile(java_bin, engine, tool_jar, classfile, out_dir, *a, **k):
            if donors.get(engine) is None:
                return None, None
            dest = Path(out_dir) / "p" / "Foo.java"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(donors[engine])
            return dest, None
        return mod_dir, fake_decompile

    def _splice(self, name, shipped, primary, cfr, procyon):
        mod_dir, fake = self._module(name, shipped, primary, cfr, procyon)
        with mock.patch.object(self.mod.FID, "_decompile_one_class_with", side_effect=fake):
            man = self.mod.splice_module(name, self.root / "organized", "vineflower2", "vineflower2s", ["p/Foo"],
                                         classpath="", helper_dir=self.helper, javac_bin=f"{JDK}/javac",
                                         javap_bin=f"{JDK}/javap", java_bin=f"{JDK}/java", tool_server=False)
        return mod_dir, man

    def test_spans_map_source_signatures_to_jvm_descriptors(self):
        d = self.root / "spans" / "p"
        d.mkdir(parents=True)
        (d / "Foo.java").write_text(SHIPPED)
        (d / "E.java").write_text("package p;\npublic enum E { A(1); final int v; E(int v) { this.v = v; } }\n")
        scans = self.mod.scan_spans([d / "Foo.java", d / "E.java"], self.helper, f"{JDK}/java", "")
        foo = scans[str(d / "Foo.java")]
        self.assertEqual(foo["errors"], [])
        got = {(m["name"], m["desc"]) for m in foo["methods"]}
        self.assertEqual(got, {("<init>", "(I)V"), ("f", "(II)I"), ("f", "(Ljava/lang/String;)I"),
                               ("g", "(Ljava/util/List;[Ljava/lang/String;)I"), ("h", "()I")})
        e = scans[str(d / "E.java")]
        self.assertIn(("<init>", "(Ljava/lang/String;II)V"), {(m["name"], m["desc"]) for m in e["methods"]})
        self.assertIn("p/E|values|()[Lp/E;", e["members"])

    def test_splice_needing_a_missing_synthetic_member_is_refused(self):
        shipped = SHIPPED.replace("int h() { return k + 1; }", "int h() { return k + 1; }\n  class In { }")
        primary = shipped.replace("return a - b;", "return b - a;")
        # the donor's f calls a synthetic-named helper only the donor declares
        donor = shipped.replace("static int f(int a, int b) { return a - b; }",
                                "static int f(int a, int b) { return access$000(a, b); }\n"
                                "  static int access$000(int a, int b) { return a - b; }")
        d = self.root / "synth"
        for eng, text in (("primary", primary), ("cfr", donor)):
            (d / eng / "p").mkdir(parents=True)
            (d / eng / "p" / "Foo.java").write_text(text)
        scans = self.mod.scan_spans([d / "primary/p/Foo.java", d / "cfr/p/Foo.java"], self.helper,
                                    f"{JDK}/java", "")
        with self.assertRaises(self.mod.Refusal) as cm:
            self.mod.plan_splice(primary, scans[str(d / "primary/p/Foo.java")],
                                 {"cfr": (donor, scans[str(d / "cfr/p/Foo.java")])},
                                 {("f", "(II)I"): "cfr"}, {("f", "(II)I"): False}, "Foo")
        self.assertEqual(cm.exception.reason, "synthetic-member")

    def test_local_class_in_the_donor_body_is_refused(self):
        donor = SHIPPED.replace("return a - b;", "Object o = new Object() { }; return a - b;")
        d = self.root / "local"
        for eng, text in (("primary", PRIMARY), ("cfr", donor)):
            (d / eng / "p").mkdir(parents=True)
            (d / eng / "p" / "Foo.java").write_text(text)
        scans = self.mod.scan_spans([d / "primary/p/Foo.java", d / "cfr/p/Foo.java"], self.helper,
                                    f"{JDK}/java", "")
        with self.assertRaises(self.mod.Refusal) as cm:
            self.mod.plan_splice(PRIMARY, scans[str(d / "primary/p/Foo.java")],
                                 {"cfr": (donor, scans[str(d / "cfr/p/Foo.java")])},
                                 {("f", "(II)I"): "cfr"}, {("f", "(II)I"): False}, "Foo")
        self.assertEqual(cm.exception.reason, "local-class")



if __name__ == "__main__":
    unittest.main()
