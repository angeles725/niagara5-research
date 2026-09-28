"""Tests for tools/n5-best-source.py: T25 per-class "best available representation" index.

Precedence (docs/writer-prompt.md "Source precedence for code claims", T20/T25):
  1. organized/docSource/<module>/<pkg>/<Class>.java  -- Tridium original source (byte-identical).
  2. organized/_upstream-sources/... fetched -sources.jar -- upstream third-party original source.
  3. organized/<pop>/vineflower2/... -- v2 decompile (recommended tree).
  4. organized/<pop>/vineflower/...  -- v1 decompile.
  5. organized/<pop>/fallback2/... then fallback/... -- CFR fallback.
  6. missing -- no representation at all (anti-silent-zero: still listed, never dropped).

A class graded worse on v2 than v1 (organized/<pop>/fidelity.vineflower2.json vs
fidelity.vineflower.json, using the same grade ranking n5-fidelity.py's _GRADE_RANK uses:
no-compile/timeout/harness-error < compiles-mismatch/bytecode-only < roundtrip-equivalent <
roundtrip-exact) falls back to v1, with a `reason` explaining why.

Real corpus facts this test suite encodes (verified against /home/cristian/niagara5-research/
organized 2026-09-28, read-only):
  - a population is any directory with a sibling "extracted/" dir: modules (organized/<mod>/),
    organized/_bin-ext/<jar>/, organized/_etc-m2/<jar>/, organized/_lib/<jar>/, and (one module
    only, devkit) organized/<mod>/lib-inf/<jar>/ -- a genuine decompiled subtree.
  - EVERY OTHER module's LIB-INF-nested third-party jars are raw, undecompiled files at
    organized/<mod>/extracted/LIB-INF/<jar>.jar (also duplicated raw under vineflower/,
    vineflower2/, etc.) -- there is no per-class decompile of them anywhere in the corpus, so
    their classes are "missing" unless an upstream sources jar covers them by name.
  - nested classes (Outer$Inner.class) are excluded from population enumeration; their source
    lives in the outer top-level class's file.
  - some _etc-m2 populations' decompilers wrote `.kt` instead of `.java` (Kotlin sources).
  - the conservative/line-mapped tree is organized/<pop>/vineflower-cons/... ; it is metadata
    (`line_mapped_view`), never itself a `best` candidate.

Unit tests build small synthetic organized/ trees in a temp dir; no dependency on the real
corpus being mounted.
"""
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-best-source.py")


def _load():
    spec = importlib.util.spec_from_file_location("n5_best_source", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write(path: Path, content: str = "// stub\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _write_class(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # A minimal (invalid-as-bytecode, but that's fine -- nothing here runs javap) placeholder;
    # only the .class file's *existence and name* matter for population/class-key discovery.
    path.write_bytes(b"\xca\xfe\xba\xbe" + b"\x00" * 4)


def _jar_bytes(entries: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


class FixtureOrganized:
    """Builds a synthetic organized/ tree covering every precedence rung."""

    def __init__(self, root: Path):
        self.root = root

    # -- module population ("modA") -----------------------------------------
    def add_module_skeleton(self, mod="modA"):
        m = self.root / mod
        # every class this fixture cares about gets a .class in extracted/ (population source
        # of truth for "which classes exist").
        for cls in ("pkg/DocClass", "pkg/UpstreamClass", "pkg/V2Class", "pkg/V2Class$Inner",
                    "pkg/V1BetterClass", "pkg/FallbackClass", "pkg/OldFallbackClass",
                    "pkg/MissingClass", "pkg/KotlinClass"):
            _write_class(m / "extracted" / (cls + ".class"))
        return m

    def add_docsource(self, mod, class_key):
        _write(self.root / "docSource" / mod / (class_key + ".java"), "// docSource original\n")

    def add_rung(self, mod, rung, class_key, ext=".java", content="// decompiled\n"):
        _write(self.root / mod / rung / (class_key + ext), content)

    def add_fidelity(self, mod, variant, classes: dict):
        path = self.root / mod / f"fidelity.{variant}.json"
        _write(path, json.dumps({"module": mod, "classes": classes}))


class DiscoverPopulationsTest(unittest.TestCase):
    def test_finds_module_bin_ext_etc_m2_lib_and_module_lib_inf(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fx = FixtureOrganized(root)
            fx.add_module_skeleton("modA")
            _write_class(root / "_bin-ext" / "toolX" / "extracted" / "com" / "T.class")
            _write_class(root / "_etc-m2" / "libY-1.0" / "extracted" / "com" / "L.class")
            _write_class(root / "_lib" / "docletZ-1.0" / "extracted" / "com" / "D.class")
            # devkit-style genuine decompiled lib-inf subtree
            _write_class(root / "devkit" / "lib-inf" / "n-templates-1.0" / "extracted" / "com" / "N.class")
            pops = m.discover_populations(root)
            names = {p["name"] for p in pops}
            self.assertIn("modA", names)
            self.assertIn("_bin-ext/toolX", names)
            self.assertIn("_etc-m2/libY-1.0", names)
            self.assertIn("_lib/docletZ-1.0", names)
            self.assertIn("devkit/lib-inf/n-templates-1.0", names)

    def test_raw_lib_inf_nested_jar_is_its_own_population(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fx = FixtureOrganized(root)
            fx.add_module_skeleton("modA")
            jar_bytes = _jar_bytes({"org/thirdparty/Foo.class": b"stub"})
            jar_path = root / "modA" / "extracted" / "LIB-INF" / "thirdparty-1.0.jar"
            jar_path.parent.mkdir(parents=True, exist_ok=True)
            jar_path.write_bytes(jar_bytes)
            pops = m.discover_populations(root)
            raw = [p for p in pops if p["kind"] == "module-lib-inf-raw"]
            self.assertEqual(len(raw), 1)
            self.assertEqual(raw[0]["name"], "modA/lib-inf-raw/thirdparty-1.0")


class EnumerateClassesTest(unittest.TestCase):
    def test_excludes_nested_classes_but_not_top_level(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fx = FixtureOrganized(root)
            mod_root = fx.add_module_skeleton("modA")
            pop = {"kind": "module", "name": "modA", "root": mod_root, "docsource_name": "modA"}
            classes = set(m.enumerate_classes(pop))
            self.assertIn("pkg/V2Class", classes)
            self.assertNotIn("pkg/V2Class$Inner", classes)

    def test_raw_jar_population_enumerates_from_zip_excluding_nested(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            jar_bytes = _jar_bytes({
                "org/thirdparty/Foo.class": b"stub",
                "org/thirdparty/Foo$Bar.class": b"stub",
                "org/thirdparty/Baz.class": b"stub",
            })
            jar_path = root / "thirdparty-1.0.jar"
            jar_path.write_bytes(jar_bytes)
            pop = {"kind": "module-lib-inf-raw", "name": "modA/lib-inf-raw/thirdparty-1.0",
                   "root": None, "jar_path": jar_path, "docsource_name": None}
            classes = set(m.enumerate_classes(pop))
            self.assertEqual(classes, {"org/thirdparty/Foo", "org/thirdparty/Baz"})


class PrecedenceTest(unittest.TestCase):
    """End-to-end: build_class_record for each rung in isolation."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.root = Path(self.td.name)
        self.fx = FixtureOrganized(self.root)
        self.mod_root = self.fx.add_module_skeleton("modA")
        self.pop = {"kind": "module", "name": "modA", "root": self.mod_root,
                    "docsource_name": "modA"}

    def _record(self, class_key, upstream_index=None, extract_dir=None):
        m = _load()
        pop = dict(self.pop)
        pop["fidelity_v2"] = m.load_fidelity(self.mod_root, "vineflower2")
        pop["fidelity_v1"] = m.load_fidelity(self.mod_root, "vineflower")
        return m.build_class_record(self.root, pop, class_key, upstream_index or {},
                                     extract_dir or (self.root / "_extract"))

    def test_docsource_beats_everything(self):
        self.fx.add_docsource("modA", "pkg/DocClass")
        self.fx.add_rung("modA", "vineflower2", "pkg/DocClass")
        self.fx.add_rung("modA", "vineflower", "pkg/DocClass")
        rec = self._record("pkg/DocClass")
        self.assertEqual(rec["best_kind"], "docSource")
        self.assertTrue(rec["best"].endswith("docSource/modA/pkg/DocClass.java"))

    def test_upstream_beats_vineflower2(self):
        jar_bytes = _jar_bytes({"pkg/UpstreamClass.java": b"// upstream original\n"})
        art_dir = self.root / "_upstream-sources" / "grp" / "art" / "1.0"
        art_dir.mkdir(parents=True)
        (art_dir / "art-1.0-sources.jar").write_bytes(jar_bytes)
        manifest = {
            "artifacts": [{
                "groupId": "grp", "artifactId": "art", "version": "1.0", "status": "fetched",
                "sources_jar_path": "organized/_upstream-sources/grp/art/1.0/art-1.0-sources.jar",
                "classdiff": {"sources_only": [], "binary_only": [], "common": 1},
            }],
            "unidentified": [],
        }
        (self.root / "_upstream-sources" / "manifest.json").write_text(json.dumps(manifest))
        self.fx.add_rung("modA", "vineflower2", "pkg/UpstreamClass")
        m = _load()
        upstream_index = m.build_upstream_index(self.root)
        rec = self._record("pkg/UpstreamClass", upstream_index=upstream_index)
        self.assertEqual(rec["best_kind"], "upstream")
        self.assertEqual(rec["reason"], "upstream Maven sources jar match")
        extracted = self.root / "_extract" / "grp" / "art" / "1.0" / "pkg" / "UpstreamClass.java"
        self.assertTrue(extracted.is_file())
        self.assertEqual(extracted.read_text(), "// upstream original\n")

    def test_vineflower2_beats_vineflower_by_default(self):
        self.fx.add_rung("modA", "vineflower2", "pkg/V2Class", content="// v2\n")
        self.fx.add_rung("modA", "vineflower", "pkg/V2Class", content="// v1\n")
        rec = self._record("pkg/V2Class")
        self.assertEqual(rec["best_kind"], "vineflower2")
        self.assertTrue(rec["best"].endswith("vineflower2/pkg/V2Class.java"))

    def test_v1_preferred_when_graded_better_than_v2(self):
        self.fx.add_rung("modA", "vineflower2", "pkg/V1BetterClass", content="// v2, worse\n")
        self.fx.add_rung("modA", "vineflower", "pkg/V1BetterClass", content="// v1, better\n")
        self.fx.add_fidelity("modA", "vineflower2", {
            "pkg/V1BetterClass": {"grade": "compiles-mismatch"},
        })
        self.fx.add_fidelity("modA", "vineflower", {
            "pkg/V1BetterClass": {"grade": "roundtrip-exact"},
        })
        rec = self._record("pkg/V1BetterClass")
        self.assertEqual(rec["best_kind"], "vineflower")
        self.assertEqual(rec["grade"], "roundtrip-exact")
        self.assertIn("v1", rec["reason"].lower())
        self.assertIn("v2", rec["reason"].lower())

    def test_fallback2_used_when_no_vineflower_output(self):
        self.fx.add_rung("modA", "fallback2", "pkg/FallbackClass", content="// cfr fallback2\n")
        rec = self._record("pkg/FallbackClass")
        self.assertEqual(rec["best_kind"], "fallback2")

    def test_bare_fallback_used_when_only_that_exists(self):
        self.fx.add_rung("modA", "fallback", "pkg/OldFallbackClass", content="// cfr fallback v1\n")
        rec = self._record("pkg/OldFallbackClass")
        self.assertEqual(rec["best_kind"], "fallback")

    def test_missing_when_nothing_covers_it(self):
        rec = self._record("pkg/MissingClass")
        self.assertEqual(rec["best_kind"], "missing")
        self.assertIsNone(rec["best"])
        self.assertTrue(rec["reason"])

    def test_kotlin_output_extension_is_found(self):
        self.fx.add_rung("modA", "vineflower2", "pkg/KotlinClass", ext=".kt", content="// kotlin\n")
        rec = self._record("pkg/KotlinClass")
        self.assertEqual(rec["best_kind"], "vineflower2")
        self.assertTrue(rec["best"].endswith(".kt"))

    def test_line_mapped_view_recorded_when_cons_tree_exists(self):
        self.fx.add_rung("modA", "vineflower2", "pkg/V2Class", content="// v2\n")
        self.fx.add_rung("modA", "vineflower-cons", "pkg/V2Class", content="// v2 cons\n")
        rec = self._record("pkg/V2Class")
        self.assertIsNotNone(rec["line_mapped_view"])
        self.assertTrue(rec["line_mapped_view"].endswith("vineflower-cons/pkg/V2Class.java"))

    def test_line_mapped_view_absent_when_no_cons_tree(self):
        self.fx.add_rung("modA", "vineflower2", "pkg/V2Class", content="// v2\n")
        rec = self._record("pkg/V2Class")
        self.assertIsNone(rec["line_mapped_view"])


class UpstreamNonPortableNamesTest(unittest.TestCase):
    """module-info / package-info are per-artifact descriptor files: two different artifacts'
    module-info.java share a filename but never share content. Matching them like any other
    class name would silently swap in an unrelated artifact's descriptor (real corpus bug found
    2026-09-28: aaphp's module-info matched to org.eclipse.angus:jakarta.mail's)."""

    def test_module_info_and_package_info_excluded_from_upstream_index(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            jar_bytes = _jar_bytes({
                "module-info.java": b"module some.other.thing {}\n",
                "org/thing/package-info.java": b"// unrelated package\n",
                "org/thing/Real.java": b"// a real, legitimately-shared class\n",
            })
            art_dir = root / "_upstream-sources" / "grp" / "art" / "1.0"
            art_dir.mkdir(parents=True)
            (art_dir / "art-1.0-sources.jar").write_bytes(jar_bytes)
            manifest = {
                "artifacts": [{
                    "groupId": "grp", "artifactId": "art", "version": "1.0", "status": "fetched",
                    "sources_jar_path": "organized/_upstream-sources/grp/art/1.0/art-1.0-sources.jar",
                    "classdiff": {"sources_only": [], "binary_only": [], "common": 3},
                }],
                "unidentified": [],
            }
            (root / "_upstream-sources" / "manifest.json").write_text(json.dumps(manifest))
            m = _load()
            index = m.build_upstream_index(root)
            self.assertNotIn("module-info", index)
            self.assertNotIn("org/thing/package-info", index)
            self.assertIn("org/thing/Real", index)


class MainRunAndMaterializeTest(unittest.TestCase):
    """Full CLI-level pass: build index JSON + materialize a symlink tree."""

    def test_end_to_end_index_and_materialize(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "organized"
            fx = FixtureOrganized(root)
            fx.add_module_skeleton("modA")
            fx.add_docsource("modA", "pkg/DocClass")
            fx.add_rung("modA", "vineflower2", "pkg/V2Class")
            fx.add_rung("modA", "vineflower", "pkg/V2Class")
            fx.add_rung("modA", "fallback2", "pkg/FallbackClass")
            fx.add_rung("modA", "fallback", "pkg/OldFallbackClass")
            fx.add_rung("modA", "vineflower2", "pkg/KotlinClass", ext=".kt")
            # UpstreamClass and MissingClass: intentionally left with no rung files.

            out_dir = root / "_best"
            materialize_dir = out_dir / "tree"
            rc = m.main(["--organized", str(root), "--out", str(out_dir),
                         "--materialize", str(materialize_dir)])
            self.assertEqual(rc, 0)

            index_path = out_dir / "best-source.json"
            self.assertTrue(index_path.is_file())
            data = json.loads(index_path.read_text())
            self.assertIn("summary", data)
            self.assertIn("classes", data)

            by_key = {(c["module"], c["class"]): c for c in data["classes"]}
            self.assertEqual(by_key[("modA", "pkg/DocClass")]["best_kind"], "docSource")
            self.assertEqual(by_key[("modA", "pkg/V2Class")]["best_kind"], "vineflower2")
            self.assertEqual(by_key[("modA", "pkg/FallbackClass")]["best_kind"], "fallback2")
            self.assertEqual(by_key[("modA", "pkg/OldFallbackClass")]["best_kind"], "fallback")
            self.assertEqual(by_key[("modA", "pkg/MissingClass")]["best_kind"], "missing")
            self.assertEqual(by_key[("modA", "pkg/KotlinClass")]["best_kind"], "vineflower2")

            self.assertEqual(data["summary"]["missing_count"],
                              sum(1 for c in data["classes"] if c["best_kind"] == "missing"))
            self.assertGreaterEqual(data["summary"]["by_best_kind"].get("docSource", 0), 1)

            # materialize: symlink resolves to the real docSource file, relative.
            link = materialize_dir / "modA" / "pkg" / "DocClass.java"
            self.assertTrue(link.is_symlink())
            self.assertFalse(os.path.isabs(os.readlink(link)))
            self.assertTrue(link.resolve().is_file())
            self.assertEqual(link.resolve(), (root / "docSource" / "modA" / "pkg" / "DocClass.java").resolve())

            # kotlin file is materialized with its real .kt extension, not forced to .java.
            kt_link = materialize_dir / "modA" / "pkg" / "KotlinClass.kt"
            self.assertTrue(kt_link.is_symlink())

            # idempotent: running materialize again doesn't fail or duplicate.
            rc2 = m.main(["--organized", str(root), "--out", str(out_dir),
                          "--materialize", str(materialize_dir)])
            self.assertEqual(rc2, 0)
            self.assertTrue(link.is_symlink())

    def test_missing_classes_are_never_silently_dropped(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "organized"
            fx = FixtureOrganized(root)
            fx.add_module_skeleton("modA")
            out_dir = root / "_best"
            m.main(["--organized", str(root), "--out", str(out_dir)])
            data = json.loads((out_dir / "best-source.json").read_text())
            classes = {c["class"] for c in data["classes"]}
            # every .class under extracted/ must appear, even with no representation at all.
            self.assertIn("pkg/MissingClass", classes)
            self.assertIn("pkg/UpstreamClass", classes)


if __name__ == "__main__":
    unittest.main()
