#!/usr/bin/env python3
"""tools/n5-patch-doprivileged.py (T21/F8): bytecode-evidenced disambiguation of
SecurityUtil.doPrivileged calls. Runner: `cd tools/tests && python3 -m unittest
test_n5_patch_doprivileged`.

The end-to-end tests compile a self-written stub of the SecurityUtil overload set
(six overloads, same shapes as N5's) plus "shipped" sources that carry the casts
the original author must have written, strip the casts to get what a decompiler
emits, and require the patcher to put back exactly the shipped overload choice.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-patch-doprivileged.py")
JDK = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin"


def _load():
    spec = importlib.util.spec_from_file_location("n5_patch_doprivileged", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _jdk():
    return os.path.isfile(f"{JDK}/javac") and os.path.isfile(f"{JDK}/java") and os.path.isfile(f"{JDK}/javap")


STUBS = {
    "niagara/nre/security/privileged/PrivilegedAction.java":
        "package niagara.nre.security.privileged;\npublic interface PrivilegedAction<T> { T run(); }\n",
    "niagara/nre/security/privileged/PrivilegedExceptionAction.java":
        "package niagara.nre.security.privileged;\n"
        "public interface PrivilegedExceptionAction<T> { T run() throws Exception; }\n",
    "niagara/nre/security/privileged/PrivilegedSingleExceptionAction.java":
        "package niagara.nre.security.privileged;\n"
        "public interface PrivilegedSingleExceptionAction<T, E extends Exception> { T run() throws E; }\n",
    "niagara/nre/security/privileged/PrivilegedDoubleExceptionAction.java":
        "package niagara.nre.security.privileged;\n"
        "public interface PrivilegedDoubleExceptionAction<T, E1 extends Exception, E2 extends Exception> "
        "{ T run() throws E1, E2; }\n",
    "niagara/nre/util/SecurityUtil.java": """package niagara.nre.util;
public final class SecurityUtil {
  public static <T> T doPrivileged(java.security.PrivilegedAction<T> a) { return a.run(); }
  public static <T> T doPrivileged(niagara.nre.security.privileged.PrivilegedAction<T> a) { return a.run(); }
  public static <T, E extends Exception> T doPrivileged(
      niagara.nre.security.privileged.PrivilegedSingleExceptionAction<T, E> a) throws E { return a.run(); }
  public static <T, E1 extends Exception, E2 extends Exception> T doPrivileged(
      niagara.nre.security.privileged.PrivilegedDoubleExceptionAction<T, E1, E2> a) throws E1, E2 { return a.run(); }
  public static <T> T doPrivileged(niagara.nre.security.privileged.PrivilegedExceptionAction<T> a) {
    try { return a.run(); } catch (Exception e) { throw new RuntimeException(e); }
  }
  public static <T> T doPrivileged(java.security.PrivilegedExceptionAction<T> a)
      throws java.security.PrivilegedActionException {
    try { return a.run(); } catch (Exception e) { throw new java.security.PrivilegedActionException(e); }
  }
}
""",
}

NP = "niagara.nre.security.privileged."

SHIPPED = f"""package demo;

import java.io.IOException;
import niagara.nre.util.SecurityUtil;

public class Shipped {{
   private String name;

   String name() {{
      return this.name;
   }}

   public String a() {{
      return SecurityUtil.doPrivileged(({NP}PrivilegedAction<java.lang.String>) this::name);
   }}

   public Integer b(java.io.File f) throws IOException {{
      return SecurityUtil.doPrivileged(({NP}PrivilegedSingleExceptionAction<java.lang.Integer, java.io.IOException>) () -> {{
         if (f.exists()) {{
            throw new IOException("x");
         }}
         return 1;
      }});
   }}

   public void c() throws Exception {{
      SecurityUtil.doPrivileged((java.security.PrivilegedExceptionAction<java.lang.Void>) () -> {{
         this.name = "c";
         return null;
      }});
   }}

   public Runnable d() {{
      return () -> SecurityUtil.doPrivileged(({NP}PrivilegedAction<java.lang.Object>) () -> this.name);
   }}

   public Object e() {{
      return new Object() {{
         public String toString() {{
            return SecurityUtil.doPrivileged(({NP}PrivilegedAction<java.lang.String>) () -> "anon");
         }}
      }};
   }}

   public String h(java.io.File file) throws IOException {{
      return SecurityUtil.doPrivileged(({NP}PrivilegedSingleExceptionAction<java.lang.String, java.io.IOException>) file::getCanonicalPath);
   }}

   public <T> T k(java.util.function.Supplier<T> s) {{
      return SecurityUtil.doPrivileged(({NP}PrivilegedAction<T>) s::get);
   }}

   static class Inner {{
      static String f() {{
         return SecurityUtil.doPrivileged((java.security.PrivilegedAction<java.lang.String>) () -> "inner");
      }}
   }}
}}
"""

SHIPPED_AS_PATCHED = SHIPPED.replace("<java.lang.String, java.io.IOException>) file::",
                                     "<java.lang.String, IOException>) file::")

REFUSED = f"""package demo;

import niagara.nre.util.SecurityUtil;

public class Refused {{
   public String g() {{
      try {{
         return "g";
      }} finally {{
         SecurityUtil.doPrivileged(({NP}PrivilegedAction<java.lang.String>) () -> "fin");
      }}
   }}
}}
"""

_CAST_RE = re.compile(r"\((?:niagara\.nre\.security\.privileged|java\.security)\.Privileged\w+(?:<[^()]*?>)?\) ")


def _strip_casts(text: str) -> str:
    return _CAST_RE.sub("", text)


class TestNames(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_internal_and_descriptor_names(self):
        self.assertEqual(self.mod.internal_name_to_source("java/util/Map$Entry"), "java.util.Map.Entry")
        self.assertIsNone(self.mod.internal_name_to_source("a/B$1"))
        self.assertEqual(self.mod.descriptor_to_source("[Ljava/lang/String;"), "java.lang.String[]")
        self.assertEqual(self.mod.descriptor_to_source("[[I"), "int[][]")
        self.assertEqual(self.mod.split_method_descriptor("(I[JLa/B;)V"), (["I", "[J", "La/B;"], "V"))

    def test_binary_names_follow_javac(self):
        classes = [
            {"id": 0, "parent": -1, "kind": "top", "name": "A", "supers": []},
            {"id": 1, "parent": 0, "kind": "anon", "name": "", "supers": ["Runnable"]},
            {"id": 2, "parent": 1, "kind": "anon", "name": "", "supers": ["Object"]},
            {"id": 3, "parent": 0, "kind": "member", "name": "In", "supers": []},
            {"id": 4, "parent": 3, "kind": "anon", "name": "", "supers": ["Object"]},
            {"id": 5, "parent": 0, "kind": "anon", "name": "", "supers": ["Object"]},
            {"id": 6, "parent": 0, "kind": "local", "name": "L", "supers": []},
        ]
        self.assertEqual(self.mod.binary_names(classes, "p.q"), {
            0: "p/q/A", 1: "p/q/A$1", 2: "p/q/A$1$1", 3: "p/q/A$In", 4: "p/q/A$In$1", 5: "p/q/A$2", 6: "p/q/A$1L"})

    def test_cast_candidates_use_the_evidence_then_raw(self):
        b = self.mod.BytecodeSite(offset=0, iface="niagara/nre/security/privileged/PrivilegedDoubleExceptionAction",
                                  indy=True, instantiated_return="Ljava/lang/String;",
                                  impl_throws=["java.io.IOException"])
        texts = [self.mod.cast_text(c) for c in self.mod.cast_candidates(b)]
        self.assertEqual(texts, [
            f"({NP}PrivilegedDoubleExceptionAction<java.lang.String, java.io.IOException, java.io.IOException>) ",
            f"({NP}PrivilegedDoubleExceptionAction) "])

    def test_rendered_offsets_map_back(self):
        ins = {5: "(X) ", 10: "(YY) "}
        text = self.mod.render("0123456789abcdef", ins)
        self.assertEqual(text, "01234(X) 56789(YY) abcdef")
        self.assertEqual(self.mod.rendered_to_original(text.index("5"), ins), 5)
        self.assertEqual(self.mod.rendered_to_original(text.index("a"), ins), 10)
        self.assertEqual(self.mod.rendered_to_original(6, ins), 5)  # inside an inserted cast

    def test_javac_error_offsets_use_the_caret_column(self):
        text = "class A {\n  void f() { x.doPrivileged(y); }\n}\n"
        stderr = ("/t/A.java:2: error: reference to doPrivileged is ambiguous\n"
                  "  void f() { x.doPrivileged(y); }\n"
                  "              ^\n")
        errs = self.mod.parse_javac_errors(stderr, text)
        self.assertEqual(len(errs), 1)
        self.assertEqual(text[errs[0]["offset"]], ".")


JAVAP_WIDE_OFFSETS = """Classfile /x/A.class
  this_class: #1                          // p/A
  super_class: #2                         // java/lang/Object
  minor version: 0
{
  public void f();
    descriptor: ()V
    flags: (0x0001) ACC_PUBLIC
    Code:
      stack=1, locals=1, args_size=1
         0: aload_0
       127: invokestatic  #9                  // Method niagara/nre/util/SecurityUtil.doPrivileged:(Lniagara/nre/security/privileged/PrivilegedAction;)Ljava/lang/Object;
      1333: invokestatic  #9                  // Method niagara/nre/util/SecurityUtil.doPrivileged:(Ljava/security/PrivilegedAction;)Ljava/lang/Object;
     65000: return
}
"""


class TestJavapParsing(unittest.TestCase):
    def test_instruction_offsets_of_every_width_are_read(self):
        mod = _load()
        bc = mod.parse_javap_classes(JAVAP_WIDE_OFFSETS)["p/A"]
        self.assertEqual([m.name for m in bc.methods], ["f"])
        self.assertEqual([(s.offset, s.iface) for s in bc.methods[0].sites],
                         [(127, "niagara/nre/security/privileged/PrivilegedAction"),
                          (1333, "java/security/PrivilegedAction")])


class TestMatching(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def _scan(self, n_sites, member=None, depth=0):
        member = member or {"kind": "method", "name": "f", "params": [], "static": False}
        sites = [{"inv_start": 100 * i, "inv_end": 100 * i + 50, "qualifier": "SecurityUtil", "nargs": 1,
                  "arg_kind": "LAMBDA_EXPRESSION", "arg_start": 100 * i + 20, "arg_end": 100 * i + 49,
                  "class_id": 0, "member": member, "lambda_depth": depth} for i in range(n_sites)]
        return {"classes": [{"id": 0, "parent": -1, "kind": "top", "name": "A", "supers": []}], "sites": sites}

    def _bc(self, methods):
        bc = self.mod.BytecodeClass("p/A", supers=["Object"])
        for name, sites in methods:
            m = self.mod.BytecodeMethod(name=name, descriptor="()V")
            m.sites = sites
            bc.methods.append(m)
        return {"p/A": bc}

    def _site(self, iface="niagara/nre/security/privileged/PrivilegedAction", ret="Ljava/lang/String;"):
        return self.mod.BytecodeSite(offset=1, iface=iface, indy=True, instantiated_return=ret)

    def test_counts_equal_pairs_in_order(self):
        a, b = self._site(), self._site(iface="java/security/PrivilegedAction")
        matched, refused = self.mod.match_sites(self._scan(2), "p", self._bc([("f", [a, b])]))
        self.assertEqual(refused, [])
        self.assertIs(matched[0]["bytecode"], a)
        self.assertIs(matched[100]["bytecode"], b)

    def test_count_mismatch_refuses_the_whole_method(self):
        matched, refused = self.mod.match_sites(self._scan(1), "p", self._bc([("f", [self._site(), self._site()])]))
        self.assertEqual(matched, {})
        self.assertEqual([r["reason"] for r in refused], ["count-mismatch"])

    def test_lambda_pool_needs_uniform_evidence(self):
        uniform = self._bc([("lambda$f$0", [self._site()]), ("lambda$f$1", [self._site()])])
        matched, refused = self.mod.match_sites(self._scan(2, depth=1), "p", uniform)
        self.assertEqual(len(matched), 2)
        mixed = self._bc([("lambda$f$0", [self._site()]), ("lambda$f$1", [self._site(ret="Ljava/lang/Void;")])])
        matched, refused = self.mod.match_sites(self._scan(2, depth=1), "p", mixed)
        self.assertEqual(matched, {})
        self.assertEqual({r["reason"] for r in refused}, {"lambda-pool-mixed-evidence"})

    def test_no_arg_constructor_is_not_confused_with_overloads(self):
        bc = self.mod.BytecodeClass("p/A", supers=["Object"])
        for desc in ("()V", "(Ljava/util/Properties;)V"):
            m = self.mod.BytecodeMethod(name="<init>", descriptor=desc)
            m.sites = [self._site()] if desc == "()V" else []
            bc.methods.append(m)
        ctor = {"kind": "ctor", "name": "<init>", "params": [], "static": False}
        matched, refused = self.mod.match_sites(self._scan(1, member=ctor), "p", {"p/A": bc})
        self.assertEqual(refused, [])
        self.assertEqual(matched[0]["method"], "<init>()V")

    def test_argument_kind_must_agree_with_invokedynamic(self):
        plain = self.mod.BytecodeSite(offset=1, iface="java/security/PrivilegedAction", indy=False)
        matched, refused = self.mod.match_sites(self._scan(1), "p", self._bc([("f", [plain])]))
        self.assertEqual([r["reason"] for r in refused], ["argument-kind-mismatch"])


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.fid = cls.mod._load_fidelity()
        cls.td = tempfile.TemporaryDirectory()
        root = Path(cls.td.name)
        stub_src = root / "stubsrc"
        for rel, text in STUBS.items():
            (stub_src / rel).parent.mkdir(parents=True, exist_ok=True)
            (stub_src / rel).write_text(text)
        cls.stubs = root / "stubs"
        subprocess.run([f"{JDK}/javac", "--release", "25", "-d", str(cls.stubs),
                        *map(str, stub_src.rglob("*.java"))], check=True, capture_output=True)
        cls.shipped_src = root / "shipped" / "demo"
        cls.shipped_src.mkdir(parents=True)
        cls.extracted = root / "mod" / "extracted"
        cls.tree = root / "mod" / "vineflower2" / "demo"
        cls.tree.mkdir(parents=True)
        for name, text in (("Shipped", SHIPPED), ("Refused", REFUSED)):
            (cls.shipped_src / f"{name}.java").write_text(text)
            (cls.tree / f"{name}.java").write_text(_strip_casts(text))
        subprocess.run([f"{JDK}/javac", "--release", "25", "-g", "-cp", str(cls.stubs), "-d", str(cls.extracted),
                        *map(str, cls.shipped_src.glob("*.java"))], check=True, capture_output=True)
        cls.helper = cls.mod.compile_helper(root / "helper", f"{JDK}/javac")

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def _patch(self, name):
        src = self.tree / f"{name}.java"
        scan = self.mod.scan_sources([src], self.helper, f"{JDK}/java")[str(src)]
        return self.mod.patch_class(f"demo/{name}", src, self.extracted, scan, classpath=str(self.stubs),
                                    fid=self.fid, javac_bin=f"{JDK}/javac", javap_bin=f"{JDK}/javap",
                                    tool_server=False, max_iterations=4)

    def test_decompiled_source_is_ambiguous_before_patching(self):
        proc = subprocess.run([f"{JDK}/javac", "--release", "25", "-cp", str(self.stubs), "-d",
                               str(Path(self.td.name) / "o0"), str(self.tree / "Shipped.java")],
                              capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("reference to doPrivileged is ambiguous", proc.stderr)

    def test_patch_restores_the_shipped_casts_and_round_trips(self):
        rec = self._patch("Shipped")
        self.assertEqual(rec["refused"], [])
        self.assertTrue(rec["compiles"])
        # javac names the thrown type by its simple name (imported here)
        self.assertEqual(rec["_text"], SHIPPED_AS_PATCHED)
        self.assertEqual(len(rec["patches"]), 8)
        tried = {p["line"]: p["candidates_tried"] for p in rec["patches"]}
        # javac feedback: a method reference's thrown type, and a type variable
        self.assertIn([f"({NP}PrivilegedSingleExceptionAction<java.lang.String, java.lang.RuntimeException>)",
                       f"({NP}PrivilegedSingleExceptionAction<java.lang.String, IOException>)"],
                      tried.values())
        self.assertIn([f"({NP}PrivilegedAction<java.lang.Object>)", f"({NP}PrivilegedAction)",
                       f"({NP}PrivilegedAction<T>)"], tried.values())
        self.assertEqual(rec["original_sha256"], self.mod.sha256_text(_strip_casts(SHIPPED)))
        self.assertEqual(rec["patched_sha256"], self.mod.sha256_text(SHIPPED_AS_PATCHED))
        by_line = {p["line"]: p for p in rec["patches"]}
        self.assertTrue(all(p["evidence"]["invokestatic_iface"] for p in rec["patches"]))
        self.assertIn("demo/Shipped$1", {p["class"] for p in rec["patches"]})
        self.assertIn("demo/Shipped$Inner", {p["class"] for p in rec["patches"]})
        self.assertEqual({p["scope"] for p in by_line.values()}, {"method", "lambda"})
        # the patched source recompiles to the shipped class (grader's own rung)
        patched = Path(self.td.name) / "patched" / "demo" / "Shipped.java"
        patched.parent.mkdir(parents=True, exist_ok=True)
        patched.write_text(rec["_text"])
        res = self.fid.recompile_and_grade(str(patched), "Shipped", str(self.stubs),
                                           str(self.extracted / "demo" / "Shipped.class"),
                                           str(Path(self.td.name) / "rg"), f"{JDK}/javac", f"{JDK}/javap")
        self.assertEqual(res["grade"], "roundtrip-exact")

    def test_finally_duplicated_site_is_refused_not_guessed(self):
        rec = self._patch("Refused")
        self.assertEqual(rec["patches"], [])
        self.assertEqual([r["reason"] for r in rec["refused"]], ["count-mismatch"])
        self.assertEqual(rec["refused"][0]["bytecode_count"], 2)

    def test_patch_module_writes_only_patched_classes_and_a_manifest(self):
        organized = Path(self.td.name)
        man = self.mod.patch_module("mod", organized, "vineflower2", "vineflower2p", classpath=str(self.stubs),
                                    fid=self.fid, helper_dir=self.helper, javac_bin=f"{JDK}/javac",
                                    javap_bin=f"{JDK}/javap", java_bin=f"{JDK}/java", tool_server=False,
                                    max_iterations=4)
        out = organized / "mod" / "vineflower2p"
        self.assertEqual(sorted(p.relative_to(out).as_posix() for p in out.rglob("*.java")), ["demo/Shipped.java"])
        self.assertEqual((out / "demo" / "Shipped.java").read_text(), SHIPPED_AS_PATCHED)
        written = json.loads((out / "PATCHES.json").read_text())
        self.assertEqual(written["source_tree"], "vineflower2")
        self.assertEqual(set(written["classes"]), {"demo/Shipped", "demo/Refused"})
        self.assertNotIn("_text", written["classes"]["demo/Shipped"])
        self.assertEqual(man["classes"]["demo/Refused"]["refused"][0]["reason"], "count-mismatch")
        # the input tree is untouched
        self.assertEqual((self.tree / "Shipped.java").read_text(), _strip_casts(SHIPPED))


# ---------------------------------------------------------------------------
# C3a: causes the F8 patcher left unpatched in the real N5 tree
# ---------------------------------------------------------------------------

PA = NP + "PrivilegedAction"
PEA = NP + "PrivilegedExceptionAction"
PSEA = NP + "PrivilegedSingleExceptionAction"

C3A_SOURCES = {
    # bridge method: run()Ljava/lang/Void; plus the synthetic run()Ljava/lang/Object;
    "Bridge": f"""package demo;

import niagara.nre.util.SecurityUtil;

public class Bridge {{
   static class Act implements {PEA}<Void> {{
      public Void run() throws Exception {{
         SecurityUtil.doPrivileged(({PA}<java.lang.String>) () -> "x");
         return null;
      }}
   }}
}}
""",
    # field initializers, an instance initializer and a constructor body share <init>
    "InitOne": f"""package demo;

import niagara.nre.util.SecurityUtil;

public class InitOne {{
   private final String a = SecurityUtil.doPrivileged(({PA}<java.lang.String>) () -> "a");
   private Integer b;
   {{
      this.b = SecurityUtil.doPrivileged(({PA}<java.lang.Integer>) () -> 1);
   }}

   public InitOne() {{
      SecurityUtil.doPrivileged(({PA}<java.lang.Long>) () -> 2L);
   }}
}}
""",
    # two constructors that call super(): the initializer code is duplicated in both
    "InitTwo": f"""package demo;

import niagara.nre.util.SecurityUtil;

public class InitTwo {{
   private final String a = SecurityUtil.doPrivileged(({PA}<java.lang.String>) () -> "a");

   public InitTwo() {{
   }}

   public InitTwo(int x) {{
      this();
   }}

   public InitTwo(String s) {{
   }}
}}
""",
    # the original source had a result cast the decompiler dropped
    "ResultCast": f"""package demo;

import niagara.nre.util.SecurityUtil;

public class ResultCast {{
   static byte[] key() {{
      return (byte[]) SecurityUtil.doPrivileged(({PEA}<java.lang.Object>) () -> new byte[1]);
   }}
}}
""",
    # a thrown type javac names by its simple name although the source never imports it
    "Unimported": f"""package demo;

import niagara.nre.util.SecurityUtil;

public class Unimported {{
   public String h(java.io.File file) throws java.io.IOException {{
      return SecurityUtil.doPrivileged(({PSEA}<java.lang.String, java.io.IOException>) file::getCanonicalPath);
   }}
}}
""",
    "Ctx": """package demo;

public class Ctx {
   public Object go(java.security.AccessControlContext ctx) throws Exception {
      return java.security.AccessController.doPrivileged(
         (java.security.PrivilegedExceptionAction<java.lang.Object>) () -> {
            return null;
         }, ctx);
   }
}
""",
}
C3A_DROPPED = {"ResultCast": ("(byte[]) ",)}
_C3A_CAST_RE = re.compile(r"\((?:niagara\.nre\.security\.privileged|java\.security)\.Privileged\w+(?:<[^()]*?>)?\) ")


def _c3a_decompiled(name):
    text = C3A_SOURCES[name]
    for drop in C3A_DROPPED.get(name, ()):
        text = text.replace(drop, "")
    return _C3A_CAST_RE.sub("", text)


class TestC3aCauses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.fid = cls.mod._load_fidelity()
        cls.td = tempfile.TemporaryDirectory()
        root = Path(cls.td.name)
        stub_src = root / "stubsrc"
        for rel, text in STUBS.items():
            (stub_src / rel).parent.mkdir(parents=True, exist_ok=True)
            (stub_src / rel).write_text(text)
        cls.stubs = root / "stubs"
        subprocess.run([f"{JDK}/javac", "--release", "25", "-d", str(cls.stubs),
                        *map(str, stub_src.rglob("*.java"))], check=True, capture_output=True)
        cls.shipped_src = root / "shipped" / "demo"
        cls.shipped_src.mkdir(parents=True)
        cls.extracted = root / "mod" / "extracted"
        cls.tree = root / "mod" / "vineflower2" / "demo"
        cls.tree.mkdir(parents=True)
        for name, text in C3A_SOURCES.items():
            (cls.shipped_src / f"{name}.java").write_text(text)
            (cls.tree / f"{name}.java").write_text(_c3a_decompiled(name))
        subprocess.run([f"{JDK}/javac", "--release", "25", "-g", "-nowarn", "-cp", str(cls.stubs), "-d",
                        str(cls.extracted), *map(str, cls.shipped_src.glob("*.java"))],
                       check=True, capture_output=True)
        cls.helper = cls.mod.compile_helper(root / "helper", f"{JDK}/javac")

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def _patch(self, name):
        src = self.tree / f"{name}.java"
        scan = self.mod.scan_sources([src], self.helper, f"{JDK}/java")[str(src)]
        return self.mod.patch_class(f"demo/{name}", src, self.extracted, scan, classpath=str(self.stubs),
                                    fid=self.fid, javac_bin=f"{JDK}/javac", javap_bin=f"{JDK}/javap",
                                    tool_server=False, max_iterations=4)

    def _grade(self, name, rec):
        patched = Path(self.td.name) / "patched" / "demo" / f"{name}.java"
        patched.parent.mkdir(parents=True, exist_ok=True)
        patched.write_text(rec["_text"])
        res = self.fid.recompile_and_grade(str(patched), name, str(self.stubs),
                                           str(self.extracted / "demo" / f"{name}.class"),
                                           str(Path(self.td.name) / "rg" / name), f"{JDK}/javac", f"{JDK}/javap")
        return res["grade"]

    def test_bridge_method_is_not_a_second_overload(self):
        rec = self._patch("Bridge")
        self.assertEqual(rec["refused"], [])
        self.assertTrue(rec["compiles"])
        self.assertEqual(rec["_text"], C3A_SOURCES["Bridge"])
        self.assertEqual(self._grade("Bridge", rec), "roundtrip-exact")

    def test_initializer_sites_match_the_constructor_prefix(self):
        rec = self._patch("InitOne")
        self.assertEqual(rec["refused"], [])
        self.assertTrue(rec["compiles"])
        self.assertEqual(rec["_text"], C3A_SOURCES["InitOne"])
        self.assertEqual({p["scope"] for p in rec["patches"]}, {"method", "init"})
        self.assertEqual(self._grade("InitOne", rec), "roundtrip-exact")

    def test_initializer_duplicated_across_constructors(self):
        rec = self._patch("InitTwo")
        self.assertEqual(rec["refused"], [])
        self.assertEqual(rec["_text"], C3A_SOURCES["InitTwo"])
        self.assertEqual(self._grade("InitTwo", rec), "roundtrip-exact")

    def test_access_controller_two_argument_form(self):
        rec = self._patch("Ctx")
        self.assertEqual(rec["refused"], [])
        self.assertTrue(rec["compiles"], rec["residual_errors"])
        self.assertEqual(rec["_text"], C3A_SOURCES["Ctx"])
        self.assertEqual(self._grade("Ctx", rec), "roundtrip-exact")


if __name__ == "__main__":
    unittest.main()
