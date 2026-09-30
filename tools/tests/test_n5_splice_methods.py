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

    def test_donors_prefer_exact_then_engine_order(self):
        m = ("f", "(I)I")
        verdicts = {"cfr": {m: {"verdict": "canonical", "rules": ["tail"]}},
                    "procyon": {m: {"verdict": "exact", "rules": []}}}
        self.assertEqual([d for d, _v in self.mod.donor_candidates(m, verdicts)], ["procyon", "cfr"])
        verdicts["procyon"][m] = {"verdict": "mismatch", "rules": []}
        self.assertEqual([d for d, _v in self.mod.donor_candidates(m, verdicts)], ["cfr"])
        verdicts["cfr"][m] = {"verdict": "missing", "rules": []}
        self.assertEqual(self.mod.donor_candidates(m, verdicts), [])

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


class TestToolServerBound(unittest.TestCase):
    """R4: a finished per-module class pool must not leave its tool-server JVMs
    behind (one JVM per dead thread accumulated to modules x class_jobs), and a
    module's classes run only on pool threads, so the long-lived per-module
    threads of --jobs never own a JVM: at most jobs x class_jobs are alive."""

    def test_servers_of_finished_module_pools_are_reaped(self):
        mod = _load()
        closed = []

        class FakeServer:
            def close(self):
                closed.append(self)

        def fake_splice_class(fqcn, *a, **k):
            import threading
            assert threading.current_thread() is not threading.main_thread()
            with mod.FID._tool_servers_lock:
                mod.FID._tool_servers.append((threading.current_thread(), FakeServer()))
            return {"status": "not-candidate", "reason": "x", "detail": ""}
        with tempfile.TemporaryDirectory() as td, \
                mock.patch.object(mod, "splice_class", side_effect=fake_splice_class):
            registered = 0
            for i, targets in enumerate((["a/A"], ["a/A", "a/B", "a/C", "a/D", "a/E"], ["a/A", "a/B"])):
                mod.splice_module(f"m{i}", Path(td), "vineflower2", "vineflower2s", targets, classpath="",
                                  helper_dir=Path(td), javac_bin="", javap_bin="", java_bin="", tool_server=True,
                                  class_jobs=4)
                registered += len(targets)
                alive = [s for t, s in mod.FID._tool_servers if t.is_alive()]
                self.assertEqual(alive, [])
                self.assertEqual(len(mod.FID._tool_servers), 0)
            self.assertEqual(len(closed), registered)


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

    def test_splice_replaces_only_the_mismatched_method_and_grades_exact(self):
        mod_dir, man = self._splice("ok", SHIPPED, PRIMARY, CFR, PROCYON)
        rec = man["classes"]["p/Foo"]
        self.assertEqual([(m["name"], m["descriptor"], m["donor"], m["reason"]) for m in rec["methods"]],
                         [("f", "(II)I", "cfr", "exact")])
        self.assertEqual(rec["self_grade"], "roundtrip-exact")
        out = (mod_dir / "vineflower2s" / "p" / "Foo.java").read_text()
        # only f(int,int) changed: every other byte of the primary is kept
        self.assertEqual(out, PRIMARY.replace("static int f(int a, int b) { return b - a; }",
                                              "static int f(int x, int y) {\n    return x - y;\n  }"))
        self.assertEqual(rec["original_sha256"], self.mod.sha256_text(PRIMARY))
        self.assertEqual(rec["spliced_sha256"], self.mod.sha256_text(out))
        self.assertEqual(rec["methods"][0]["donor_sha256"], self.mod.sha256_text(CFR))
        self.assertTrue((mod_dir / "vineflower2s" / "SPLICES.json").is_file())

    def test_wrong_donor_is_never_graded_clean(self):
        # soundness: force the mismatching Procyon f(int,int) into the primary
        mod_dir, fake = self._module("wrong", SHIPPED, PRIMARY, CFR, PROCYON)
        d = self.root / "wrongscan"
        for eng, text in (("primary", PRIMARY), ("procyon", PROCYON)):
            (d / eng / "p").mkdir(parents=True)
            (d / eng / "p" / "Foo.java").write_text(text)
        scans = self.mod.scan_spans([d / "primary/p/Foo.java", d / "procyon/p/Foo.java"], self.helper,
                                    f"{JDK}/java", "")
        text, _imports = self.mod.plan_splice(
            PRIMARY, scans[str(d / "primary/p/Foo.java")],
            {"procyon": (PROCYON, scans[str(d / "procyon/p/Foo.java")])},
            {("f", "(II)I"): "procyon"}, {("f", "(II)I"): False}, "Foo")
        self.assertIn("return a + b;", text)
        grade = self.mod.grade_text(text, "Foo", mod_dir / "extracted" / "p" / "Foo.class", "",
                                    f"{JDK}/javac", f"{JDK}/javap", False)
        self.assertEqual(grade["grade"], "compiles-mismatch")
        # and the module run never picks it: with no faithful donor nothing is written
        mod_dir, man = self._splice("nodonor", SHIPPED, PRIMARY, PROCYON, PROCYON)
        self.assertEqual(man["refused"]["p/Foo"]["reason"], "no-donor")
        self.assertFalse((mod_dir / "vineflower2s" / "p" / "Foo.java").exists())

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

    def test_this_and_super_are_not_nest_members(self):
        shipped = SHIPPED.replace("return k + 1;", "return this.k + super.hashCode();")
        primary = shipped.replace("this.k + super", "this.k - super")
        mod_dir, man = self._splice("this", shipped, primary, shipped, None)
        self.assertEqual(man["refused"], {})
        self.assertEqual(man["classes"]["p/Foo"]["methods"][0]["name"], "h")

    def test_donor_import_is_added_to_the_spliced_source(self):
        shipped = SHIPPED.replace("static int f(String s) { return s.length() * 3; }",
                                  "static int f(String s) { return new java.util.ArrayList<String>().size(); }")
        primary = shipped.replace("new java.util.ArrayList<String>().size()", "0")
        donor = ("package p;\nimport java.util.ArrayList;\n"
                 + shipped.split("\n", 1)[1].replace("new java.util.ArrayList<String>()", "new ArrayList<String>()"))
        mod_dir, man = self._splice("imp", shipped, primary, donor, None)
        rec = man["classes"]["p/Foo"]
        self.assertEqual(rec["imports_added"], ["java.util.ArrayList"])
        self.assertEqual(rec["self_grade"], "roundtrip-exact")
        self.assertIn("import java.util.ArrayList;", (mod_dir / "vineflower2s" / "p" / "Foo.java").read_text())


class TestCli(unittest.TestCase):
    def test_donor_and_primary_trees_reach_splice_module(self):
        mod = _load()
        with tempfile.TemporaryDirectory() as td:
            targets = Path(td) / "t.json"
            targets.write_text('[["m", "p/Foo"]]')
            with mock.patch.object(mod.FID, "build_classpath", return_value=""), \
                    mock.patch.object(mod, "compile_helper", return_value=Path(td)), \
                    mock.patch.object(mod.FID, "shutdown_tool_servers"), \
                    mock.patch.object(mod, "splice_module",
                                      return_value={"classes": {}, "refused": {}, "not_candidates": {}}) as sm:
                rc = mod.main(["--targets", str(targets), "--organized-dir", td, "--donor-trees",
                               "vineflower-cons, vineflower", "--primary-trees", "vineflower2m", "--keep-existing"])
        self.assertEqual(rc, 0)
        kw = sm.call_args.kwargs
        self.assertEqual((kw["donor_trees"], kw["primary_trees"], kw["keep_existing"]),
                         (("vineflower-cons", "vineflower"), ("vineflower2m",), True))
        self.assertEqual(kw["hypotheses"], ())
        self.assertEqual(kw["decompilers"], ("cfr", "procyon"))

    def test_hypotheses_flag_names_or_expands_all(self):
        mod = _load()
        for arg, want in (("compound-assign", ("compound-assign",)), ("all", tuple(mod.HYP.HYPOTHESES))):
            with tempfile.TemporaryDirectory() as td:
                targets = Path(td) / "t.json"
                targets.write_text('[["m", "p/Foo"]]')
                with mock.patch.object(mod.FID, "build_classpath", return_value=""), \
                        mock.patch.object(mod, "compile_helper", return_value=Path(td)), \
                        mock.patch.object(mod.FID, "shutdown_tool_servers"), \
                        mock.patch.object(mod, "splice_module",
                                          return_value={"classes": {}, "refused": {}, "not_candidates": {}}) as sm:
                    mod.main(["--targets", str(targets), "--organized-dir", td, "--hypotheses", arg])
            self.assertEqual(sm.call_args.kwargs["hypotheses"], want)


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class _SpliceFixture(unittest.TestCase):
    """Shared fixture of the C3d splice tests: real javac, fake CFR/Procyon."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.td = tempfile.TemporaryDirectory()
        cls.root = Path(cls.td.name)
        cls.helper = cls.mod.compile_helper(cls.root / "helper", f"{JDK}/javac")

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    _module = TestEndToEnd._module

    def _tree(self, mod_dir, tree, text):
        (mod_dir / tree / "p").mkdir(parents=True, exist_ok=True)
        (mod_dir / tree / "p" / "Foo.java").write_text(text)

    def _run(self, name, mod_dir, fake, **kw):
        with mock.patch.object(self.mod.FID, "_decompile_one_class_with", side_effect=fake):
            return self.mod.splice_module(name, self.root / "organized", "vineflower2", "vineflower2s", ["p/Foo"],
                                          classpath="", helper_dir=self.helper, javac_bin=f"{JDK}/javac",
                                          javap_bin=f"{JDK}/javap", java_bin=f"{JDK}/java", tool_server=False, **kw)


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class TestOnDiskDonorTrees(_SpliceFixture):
    """C3d: donors are not only CFR/Procyon: any decompile tree already on disk
    (vineflower-cons, vineflower, a flag variant) is a donor named `tree:<name>`,
    the primary can be the m/p patch stage, and a rerun keeps earlier splices."""

    def test_on_disk_tree_is_a_donor_when_cfr_and_procyon_are_not(self):
        mod_dir, fake = self._module("tree", SHIPPED, PRIMARY, PROCYON, PROCYON)
        self._tree(mod_dir, "vineflower-cons", SHIPPED.replace("return a - b;", "return (a - b);"))
        man = self._run("tree", mod_dir, fake, donor_trees=["vineflower-cons"])
        rec = man["classes"]["p/Foo"]
        self.assertEqual([(m["name"], m["donor"], m["reason"]) for m in rec["methods"]],
                         [("f", "tree:vineflower-cons", "exact")])
        self.assertEqual(man["donor_engines"], ["cfr", "procyon", "tree:vineflower-cons"])
        self.assertEqual(rec["self_grade"], "roundtrip-exact")

    def test_decompilers_can_be_switched_off(self):
        mod_dir, fake = self._module("nodec", SHIPPED, PRIMARY, CFR, PROCYON)
        calls = []

        def spy(*a, **k):
            calls.append(a[1])
            return fake(*a, **k)
        with mock.patch.object(self.mod.FID, "_decompile_one_class_with", side_effect=spy):
            man = self.mod.splice_module("nodec", self.root / "organized", "vineflower2", "vineflower2s", ["p/Foo"],
                                         classpath="", helper_dir=self.helper, javac_bin=f"{JDK}/javac",
                                         javap_bin=f"{JDK}/javap", java_bin=f"{JDK}/java", tool_server=False,
                                         decompilers=())
        self.assertEqual(calls, [])
        self.assertEqual(man["donor_engines"], [])
        self.assertEqual(man["refused"]["p/Foo"]["reason"], "no-donor")

    def test_missing_donor_tree_file_is_skipped_not_fatal(self):
        mod_dir, fake = self._module("notree", SHIPPED, PRIMARY, PROCYON, PROCYON)
        man = self._run("notree", mod_dir, fake, donor_trees=["vineflower-cons"])
        self.assertEqual(man["refused"]["p/Foo"]["reason"], "no-donor")

    def test_primary_preference_uses_the_patch_stage_tree(self):
        mod_dir, fake = self._module("prim", SHIPPED, PRIMARY, CFR, PROCYON)
        # the m stage fixed f but broke h; vineflower2 stays the graded baseline
        self._tree(mod_dir, "vineflower2m", SHIPPED.replace("return k + 1;", "return k + 5;"))
        man = self._run("prim", mod_dir, fake, primary_trees=["vineflower2m"])
        rec = man["classes"]["p/Foo"]
        self.assertEqual(rec["primary_tree"], "vineflower2m")
        self.assertEqual([m["name"] for m in rec["methods"]], ["h"])

    def test_first_compiling_primary_tree_wins_and_a_clean_one_is_emitted(self):
        # vineflower2 (the baseline) does not compile; the alternative tree is clean as it stands
        mod_dir, fake = self._module("alt", SHIPPED, "package p;\npublic class Foo { int broken( }\n", None, None)
        self._tree(mod_dir, "vf-alt", SHIPPED)
        man = self._run("alt", mod_dir, fake, primary_trees=["vf-missing", "vf-alt"])
        rec = man["classes"]["p/Foo"]
        self.assertEqual((rec["primary_tree"], rec["methods"], rec["self_grade"]), ("vf-alt", [], "roundtrip-exact"))
        self.assertEqual([t["kind"] for t in rec["pre_transforms"]], ["primary-tree"])
        self.assertEqual((mod_dir / "vineflower2s" / "p" / "Foo.java").read_text(), SHIPPED)

    def test_clean_baseline_primary_is_still_not_a_candidate(self):
        mod_dir, fake = self._module("base", SHIPPED, SHIPPED, None, None)
        man = self._run("base", mod_dir, fake)
        self.assertEqual(man["not_candidates"]["p/Foo"]["reason"], "already-clean")

    def test_keep_existing_carries_earlier_splices_over(self):
        mod_dir, fake = self._module("keep", SHIPPED, PRIMARY, CFR, PROCYON)
        first = self._run("keep", mod_dir, fake)
        self.assertIn("p/Foo", first["classes"])
        kept = (mod_dir / "vineflower2s" / "p" / "Foo.java").read_text()
        # second run targets nothing that splices; without keep_existing the earlier class is wiped
        with mock.patch.object(self.mod.FID, "_decompile_one_class_with", side_effect=fake):
            man = self.mod.splice_module("keep", self.root / "organized", "vineflower2", "vineflower2s", [],
                                         classpath="", helper_dir=self.helper, javac_bin=f"{JDK}/javac",
                                         javap_bin=f"{JDK}/javap", java_bin=f"{JDK}/java", tool_server=False,
                                         keep_existing=True)
        self.assertEqual(sorted(man["classes"]), ["p/Foo"])
        self.assertEqual((mod_dir / "vineflower2s" / "p" / "Foo.java").read_text(), kept)


CLINIT_SHIPPED = """package p;
public class Foo {
  static java.util.List<String> log = new java.util.ArrayList<>();
  static {
    log.add("a");
  }
  static int x = log.size();
  static int f(int a, int b) { return a - b; }
}
"""
# decompiler style: the field initializer hoisted before the static block; f wrong
CLINIT_PRIMARY = """package p;
public class Foo {
  static java.util.List<String> log = new java.util.ArrayList<>();
  static int x = log.size();
  static int f(int a, int b) { return b - a; }
  static {
    log.add("a");
  }
}
"""


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class TestClinitOrderPreTransform(_SpliceFixture):
    """C3d: a mismatching <clinit> is no longer refused when the static-initializer order is the
    only difference; the reordered source is the primary the method splice starts from."""

    def test_clinit_order_and_method_splice_together(self):
        cfr = CLINIT_SHIPPED
        mod_dir, fake = self._module("clinit", CLINIT_SHIPPED, CLINIT_PRIMARY, cfr, None)
        man = self._run("clinit", mod_dir, fake)
        rec = man["classes"]["p/Foo"]
        self.assertEqual(rec["self_grade"], "roundtrip-exact")
        self.assertEqual([m["name"] for m in rec["methods"]], ["f"])
        self.assertEqual([t["kind"] for t in rec["pre_transforms"]], ["clinit-order"])
        out = (mod_dir / "vineflower2s" / "p" / "Foo.java").read_text()
        self.assertIn("static int x;", out)
        self.assertEqual(rec["original_sha256"], self.mod.sha256_text(CLINIT_PRIMARY))
        self.assertRegex(rec["pre_transforms"][0]["sha256"], r"^[0-9a-f]{64}$")

    def test_clinit_order_alone_is_a_splice_with_no_donor_methods(self):
        primary = CLINIT_PRIMARY.replace("return b - a;", "return a - b;")
        mod_dir, fake = self._module("clinit2", CLINIT_SHIPPED, primary, None, None)
        man = self._run("clinit2", mod_dir, fake)
        rec = man["classes"]["p/Foo"]
        self.assertEqual(rec["methods"], [])
        self.assertEqual(rec["self_grade"], "roundtrip-exact")

    def test_unfixable_clinit_is_still_refused(self):
        primary = CLINIT_PRIMARY.replace('log.add("a")', 'log.add("zz")')
        mod_dir, fake = self._module("clinit3", CLINIT_SHIPPED, primary, CLINIT_SHIPPED, None)
        man = self._run("clinit3", mod_dir, fake)
        self.assertEqual(man["refused"]["p/Foo"]["reason"], "clinit")


HYP_SHIPPED = """package p;
public class Foo {
  byte[] buf = new byte[4];
  void set(boolean on) {
    if (on) {
      buf[3] |= 4;
    } else {
      buf[3] &= -5;
    }
  }
  int keep(int a) { return a + 1; }
}
"""
HYP_PRIMARY = HYP_SHIPPED.replace("buf[3] |= 4;", "buf[3] = (byte)(buf[3] | 4);").replace(
    "buf[3] &= -5;", "buf[3] = (byte)(buf[3] & -5);")


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class TestSourceHypothesisDonors(_SpliceFixture):
    """C3d: a source hypothesis (tools/n5_source_hypotheses.py) applied to the primary is one more
    donor named `hyp:<name>`; its methods count only when their recompiled Code matches."""

    def test_compound_assign_variant_donates_the_methods_it_fixes(self):
        mod_dir, fake = self._module("hyp", HYP_SHIPPED, HYP_PRIMARY, None, None)
        man = self._run("hyp", mod_dir, fake, hypotheses=["compound-assign"])
        rec = man["classes"]["p/Foo"]
        self.assertEqual([(m["name"], m["donor"]) for m in rec["methods"]], [("set", "hyp:compound-assign")])
        self.assertEqual(rec["self_grade"], "roundtrip-exact")
        out = (mod_dir / "vineflower2s" / "p" / "Foo.java").read_text()
        self.assertIn("buf[3] |= 4;", out)
        self.assertEqual(man["donor_engines"][-1], "hyp:compound-assign")

    def test_hypothesis_fixing_a_static_initializer_is_adopted_as_a_pre_transform(self):
        shipped = HYP_SHIPPED.replace("  int keep", "  static final byte[] T = new byte[2];\n  static {\n    T[1] |= 4;\n  }\n  int keep")
        primary = HYP_PRIMARY.replace("  int keep", "  static final byte[] T = new byte[2];\n  static {\n"
                                                      "    T[1] = (byte)(T[1] | 4);\n  }\n  int keep")
        mod_dir, fake = self._module("hyp3", shipped, primary, None, None)
        man = self._run("hyp3", mod_dir, fake, hypotheses=["compound-assign"])
        rec = man["classes"]["p/Foo"]
        self.assertEqual([t["kind"] for t in rec["pre_transforms"]], ["hyp:compound-assign"])
        self.assertEqual(rec["methods"], [])
        self.assertEqual(rec["self_grade"], "roundtrip-exact")

    def test_context_hypothesis_restores_a_dropped_null_check(self):
        shipped = HYP_SHIPPED.replace("int keep(int a) { return a + 1; }",
                                      "static Object keep(Object a) { java.util.Objects.requireNonNull(a); return a; }")
        primary = shipped.replace("java.util.Objects.requireNonNull(a); ", "")
        mod_dir, fake = self._module("hyp4", shipped, primary.replace("buf[3] |= 4;", "buf[3] = (byte)(buf[3] | 4);")
                                     .replace("buf[3] &= -5;", "buf[3] = (byte)(buf[3] & -5);"), None, None)
        man = self._run("hyp4", mod_dir, fake, hypotheses=["compound-assign", "restore-null-checks"])
        rec = man["classes"]["p/Foo"]
        self.assertEqual(sorted((m["name"], m["donor"]) for m in rec["methods"]),
                         [("keep", "hyp:restore-null-checks"), ("set", "hyp:compound-assign")])
        self.assertEqual(rec["self_grade"], "roundtrip-exact")
        self.assertIn("java.util.Objects.requireNonNull(a);", (mod_dir / "vineflower2s" / "p" / "Foo.java").read_text())

    def test_lvt_declared_type_hypothesis_fixes_a_mismatching_local(self):
        shipped = HYP_SHIPPED.replace("int keep(int a) { return a + 1; }",
                                      "static int keep(java.util.List<String> a) {\n    java.util.Collection<String> c = a;\n"
                                      "    return c.size();\n  }")
        primary = shipped.replace("java.util.Collection<String> c = a;", "java.util.List<String> c = a;").replace(
            "buf[3] |= 4;", "buf[3] = (byte)(buf[3] | 4);").replace("buf[3] &= -5;", "buf[3] = (byte)(buf[3] & -5);")
        mod_dir, fake = self._module("hyp5", shipped, primary, None, None)
        man = self._run("hyp5", mod_dir, fake, hypotheses=["compound-assign", "declared-local-types"])
        rec = man["classes"]["p/Foo"]
        self.assertIn(("keep", "hyp:declared-local-types"), [(m["name"], m["donor"]) for m in rec["methods"]])
        self.assertEqual(rec["self_grade"], "roundtrip-exact")

    def test_variant_identical_to_the_primary_is_skipped(self):
        mod_dir, fake = self._module("hyp2", HYP_SHIPPED, HYP_SHIPPED.replace("a + 1", "a + 2"), None, None)
        man = self._run("hyp2", mod_dir, fake, hypotheses=["compound-assign"])
        self.assertEqual(man["refused"]["p/Foo"]["reason"], "no-donor")


LAMBDA_SHIPPED = """package p;
import java.util.function.Function;
import java.util.function.Supplier;
public class Foo {
  static Object f(boolean b) {
    if (b) {
      return (Supplier<String>) () -> "a";
    } else {
      return (Function<String, Integer>) s -> s.length();
    }
  }
  static int g(int a) { return a + 1; }
}
"""
# the decompiler negated the condition and swapped the branches: javac numbers the lambdas the other way round
LAMBDA_PRIMARY = LAMBDA_SHIPPED.replace("""    if (b) {
      return (Supplier<String>) () -> "a";
    } else {
      return (Function<String, Integer>) s -> s.length();
    }""", """    if (!b) {
      return (Function<String, Integer>) s -> s.length();
    } else {
      return (Supplier<String>) () -> "a";
    }""")


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class TestStructuralPrimarySearch(_SpliceFixture):
    """C3d: a primary whose class structure differs from the shipped class (lambda numbering,
    accessors) can only be replaced as a whole: the first alternative tree that restores the
    structure becomes the primary, then the method splice continues from it."""

    def test_alternative_tree_restoring_the_structure_becomes_the_primary(self):
        mod_dir, fake = self._module("lam", LAMBDA_SHIPPED, LAMBDA_PRIMARY, None, None)
        self._tree(mod_dir, "vineflower-cons", LAMBDA_SHIPPED)
        man = self._run("lam", mod_dir, fake, donor_trees=["vineflower-cons"])
        rec = man["classes"]["p/Foo"]
        self.assertEqual(rec["self_grade"], "roundtrip-exact")
        self.assertEqual([(t["kind"], t["tree"]) for t in rec["pre_transforms"]], [("primary-tree", "vineflower-cons")])
        self.assertEqual((mod_dir / "vineflower2s" / "p" / "Foo.java").read_text(), LAMBDA_SHIPPED)

    def test_structure_that_no_alternative_restores_is_never_written(self):
        mod_dir, fake = self._module("lam2", LAMBDA_SHIPPED, LAMBDA_PRIMARY, None, None)
        self._tree(mod_dir, "vineflower-cons", LAMBDA_PRIMARY)
        man = self._run("lam2", mod_dir, fake, donor_trees=["vineflower-cons"])
        self.assertIn("p/Foo", man["refused"])
        self.assertNotIn("p/Foo", man["classes"])
        self.assertFalse((mod_dir / "vineflower2s" / "p" / "Foo.java").exists())


if __name__ == "__main__":
    unittest.main()
