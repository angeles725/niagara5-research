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
    their classes are "missing" unless an upstream sources jar covers them by name, OR (fixed
    2026-09-28, orchestrator-found defect) a BYTE-IDENTICAL copy of that same jar was decompiled
    as its own population elsewhere -- e.g. devkit bundles both a raw LIB-INF copy AND a genuine
    decompiled organized/devkit/lib-inf/<jar>/ subtree of the SAME jar (same
    extracted/.jar_sha256). Every decompiled population's extracted/.jar_sha256 file (written at
    decompile time) is the identity key; a raw jar is hashed directly. Linking is by sha256 only,
    never by filename.
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

    def set_jar_sha256(self, mod, sha256):
        _write(self.root / mod / "extracted" / ".jar_sha256", sha256)


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

    def test_finds_lib_inf_3p_population(self):
        """T26b: organized/_lib-inf-3p/<jar-stem>-<sha256[:12]>/ (tools/n5-decompile.sh
        --third-party-libinf's dedup-by-sha256 output for non-Tridium nested LIB-INF jars) is a
        population root exactly like _bin-ext/_etc-m2/_lib -- discovered as "kind": "lib-inf-3p"."""
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_class(root / "_lib-inf-3p" / "prosys-1.0-abc123456789" / "extracted" / "com" / "P.class")
            pops = m.discover_populations(root)
            names = {p["name"] for p in pops}
            self.assertIn("_lib-inf-3p/prosys-1.0-abc123456789", names)
            match = [p for p in pops if p["name"] == "_lib-inf-3p/prosys-1.0-abc123456789"][0]
            self.assertEqual(match["kind"], "lib-inf-3p")

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
        return m.build_class_record(self.root, pop, class_key, upstream_index or ({}, {}),
                                     extract_dir or (self.root / "_extract"))

    def test_docsource_beats_everything(self):
        self.fx.add_docsource("modA", "pkg/DocClass")
        self.fx.add_rung("modA", "vineflower2", "pkg/DocClass")
        self.fx.add_rung("modA", "vineflower", "pkg/DocClass")
        rec = self._record("pkg/DocClass")
        self.assertEqual(rec["best_kind"], "docSource")
        self.assertTrue(rec["best"].endswith("docSource/modA/pkg/DocClass.java"))

    def test_upstream_beats_vineflower2(self):
        """An upstream match with a PROVEN identity verdict (resigned-identical: every class in
        the jar matched Central byte-for-byte) is trusted and wins over vineflower2."""
        jar_bytes = _jar_bytes({"pkg/UpstreamClass.java": b"// upstream original\n"})
        art_dir = self.root / "_upstream-sources" / "grp" / "art" / "1.0"
        art_dir.mkdir(parents=True)
        (art_dir / "art-1.0-sources.jar").write_bytes(jar_bytes)
        manifest = {
            "artifacts": [{
                "groupId": "grp", "artifactId": "art", "version": "1.0", "status": "fetched",
                "sources_jar_path": "organized/_upstream-sources/grp/art/1.0/art-1.0-sources.jar",
                "classdiff": {"sources_only": [], "binary_only": [], "common": 1},
                "content_identity": {"status": "resigned-identical"},
            }],
            "unidentified": [],
        }
        (self.root / "_upstream-sources" / "manifest.json").write_text(json.dumps(manifest))
        self.fx.add_rung("modA", "vineflower2", "pkg/UpstreamClass")
        m = _load()
        upstream_index = m.build_upstream_index(self.root)
        self.assertEqual(upstream_index[2].get("resigned-identical"), 1)
        rec = self._record("pkg/UpstreamClass", upstream_index=(upstream_index[0], upstream_index[1]))
        self.assertEqual(rec["best_kind"], "upstream")
        self.assertIn("resigned-identical", rec["reason"])
        self.assertIn("proven byte-identical", rec["reason"])
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
            name_index, _sha_index, _verdicts = m.build_upstream_index(root)
            self.assertNotIn("module-info", name_index)
            self.assertNotIn("org/thing/package-info", name_index)
            self.assertIn("org/thing/Real", name_index)


class JarIdentityFallbackTest(unittest.TestCase):
    """Orchestrator-found defect (2026-09-28): a lib-inf-raw population with no decompile of its
    own must fall back to a BYTE-IDENTICAL jar decompiled as some other population, keyed by
    sha256 only (never by filename) -- mirrors the real devkit case (a raw LIB-INF copy of
    n-templates/slotomatic sitting alongside a genuine decompiled organized/devkit/lib-inf/<jar>/
    subtree of the exact same jar)."""

    def _build(self, root):
        fx = FixtureOrganized(root)
        # "modA" bundles thirdparty.jar as a raw, undecompiled LIB-INF copy.
        mod_root = fx.add_module_skeleton("modA")
        jar_bytes = _jar_bytes({
            "org/thirdparty/Shared.class": b"stub",
            "org/thirdparty/OnlyInDecompiled.class": b"stub",
        })
        raw_jar_path = mod_root / "extracted" / "LIB-INF" / "thirdparty-1.0.jar"
        raw_jar_path.parent.mkdir(parents=True, exist_ok=True)
        raw_jar_path.write_bytes(jar_bytes)
        sha256 = m_hash(jar_bytes)

        # "modB" decompiled the exact same jar as its own module-lib-inf population.
        fx_b = FixtureOrganized(root)
        libinf_dir = root / "modB" / "lib-inf" / "thirdparty-1.0"
        _write_class(libinf_dir / "extracted" / "org" / "thirdparty" / "Shared.class")
        _write_class(libinf_dir / "extracted" / "org" / "thirdparty" / "OnlyInDecompiled.class")
        fx_b.add_rung("modB/lib-inf/thirdparty-1.0", "vineflower2", "org/thirdparty/Shared")
        fx_b.add_rung("modB/lib-inf/thirdparty-1.0", "vineflower2", "org/thirdparty/OnlyInDecompiled")
        (libinf_dir / "extracted" / ".jar_sha256").write_text(sha256)
        return root, sha256

    def test_raw_population_resolves_via_identical_jar_elsewhere(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            root, sha256 = self._build(root)
            out_dir = root / "_best"
            rc = m.main(["--organized", str(root), "--out", str(out_dir)])
            self.assertEqual(rc, 0)
            data = json.loads((out_dir / "best-source.json").read_text())
            by_key = {(c["module"], c["class"]): c for c in data["classes"]}
            rec = by_key[("modA/lib-inf-raw/thirdparty-1.0", "org/thirdparty/Shared")]
            self.assertEqual(rec["best_kind"], "vineflower2")
            self.assertTrue(rec["best"].endswith("modB/lib-inf/thirdparty-1.0/vineflower2/org/thirdparty/Shared.java"))
            self.assertIn(sha256[:12], rec["reason"])
            self.assertIn("modB/lib-inf/thirdparty-1.0", rec["reason"])

    def test_does_not_link_by_filename_when_sha256_differs(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fx = FixtureOrganized(root)
            mod_root = fx.add_module_skeleton("modA")
            raw_jar_path = mod_root / "extracted" / "LIB-INF" / "thirdparty-1.0.jar"
            raw_jar_path.parent.mkdir(parents=True, exist_ok=True)
            raw_jar_path.write_bytes(_jar_bytes({"org/thirdparty/Shared.class": b"stubA"}))

            libinf_dir = root / "modB" / "lib-inf" / "thirdparty-1.0"
            _write_class(libinf_dir / "extracted" / "org" / "thirdparty" / "Shared.class")
            fx2 = FixtureOrganized(root)
            fx2.add_rung("modB/lib-inf/thirdparty-1.0", "vineflower2", "org/thirdparty/Shared")
            # DIFFERENT sha256 -- same filename/artifact name, different bytes (e.g. a different
            # build/version). Must NOT be linked.
            (libinf_dir / "extracted" / ".jar_sha256").write_text("deadbeef" * 8)

            out_dir = root / "_best"
            m.main(["--organized", str(root), "--out", str(out_dir)])
            data = json.loads((out_dir / "best-source.json").read_text())
            by_key = {(c["module"], c["class"]): c for c in data["classes"]}
            rec = by_key[("modA/lib-inf-raw/thirdparty-1.0", "org/thirdparty/Shared")]
            self.assertEqual(rec["best_kind"], "missing")

    def test_missing_by_jar_in_summary(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fx = FixtureOrganized(root)
            fx.add_module_skeleton("modA")  # no rungs added at all: every class is "missing"
            out_dir = root / "_best"
            m.main(["--organized", str(root), "--out", str(out_dir)])
            data = json.loads((out_dir / "best-source.json").read_text())
            self.assertIn("missing_by_jar", data["summary"])
            missing_by_jar = data["summary"]["missing_by_jar"]
            self.assertIsInstance(missing_by_jar, list)
            # sorted desc by count
            counts = [entry["count"] for entry in missing_by_jar]
            self.assertEqual(counts, sorted(counts, reverse=True))
            total = sum(entry["count"] for entry in missing_by_jar)
            self.assertEqual(total, data["summary"]["missing_count"])


class UpstreamIdentityVerificationTest(unittest.TestCase):
    """2026-09-28 orchestrator-found defect fix: an upstream `-sources.jar` is trusted as `best`
    ONLY when manifest.json's own per-artifact identity verdict PROVES it byte-identical to the
    shipped binary jar -- never merely because it was successfully fetched. Real corpus example
    the old code got wrong: org.eclipse.paho.client.mqttv3 1.2.5 is vendor-rebuilt (0/110 classes
    byte-identical to Central, B117 "rebuilt-by-vendor"), yet was marked `best_kind: upstream` for
    96 of its classes because the old code trusted every "status": "fetched" artifact
    unconditionally."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.root = Path(self.td.name)
        self.fx = FixtureOrganized(self.root)
        self.mod_root = self.fx.add_module_skeleton("modA")
        self.pop = {"kind": "module", "name": "modA", "root": self.mod_root,
                    "docsource_name": "modA"}

    def _write_manifest(self, artifact: dict):
        (self.root / "_upstream-sources").mkdir(parents=True, exist_ok=True)
        (self.root / "_upstream-sources" / "manifest.json").write_text(
            json.dumps({"artifacts": [artifact], "unidentified": []}))

    def _write_sources_jar(self, gav, java_entries: dict) -> str:
        g, a, v = gav
        art_dir = self.root / "_upstream-sources" / g / a / v
        art_dir.mkdir(parents=True, exist_ok=True)
        jar_path = art_dir / f"{a}-{v}-sources.jar"
        jar_path.write_bytes(_jar_bytes(java_entries))
        return f"organized/_upstream-sources/{g}/{a}/{v}/{a}-{v}-sources.jar"

    def _record(self, class_key, upstream_index, jar_sha256=None, extract_dir=None):
        m = _load()
        pop = dict(self.pop)
        pop["fidelity_v2"] = m.load_fidelity(self.mod_root, "vineflower2")
        pop["fidelity_v1"] = m.load_fidelity(self.mod_root, "vineflower")
        if jar_sha256 is not None:
            pop["jar_sha256"] = jar_sha256
        return m.build_class_record(self.root, pop, class_key, upstream_index,
                                     extract_dir or (self.root / "_extract"))

    def test_whole_jar_sha1_match_is_trusted(self):
        """identification_method present with NO content_identity == T26a's "identified-by-sha1":
        the whole shipped binary jar's SHA-1 matched Central directly -- proven for every class."""
        m = _load()
        _write_class(self.mod_root / "extracted" / "pkg" / "ShaClass.class")
        sources_jar = self._write_sources_jar(("grp", "sha-art", "1.0"),
                                               {"pkg/ShaClass.java": b"// sha1-matched\n"})
        self._write_manifest({
            "groupId": "grp", "artifactId": "sha-art", "version": "1.0", "status": "fetched",
            "sources_jar_path": sources_jar,
            "classdiff": {"sources_only": [], "binary_only": [], "common": 1},
            "identification_method": "sha1-search",
        })
        name_index, sha_index, verdicts = m.build_upstream_index(self.root)
        self.assertEqual(verdicts.get("identified-by-sha1"), 1)
        rec = self._record("pkg/ShaClass", (name_index, sha_index))
        self.assertEqual(rec["best_kind"], "upstream")
        self.assertIn("identification_method=sha1-search", rec["reason"])

    def test_vendor_modified_artifact_never_trusted_paho_style(self):
        """The real paho-mqttv3 1.2.5 scenario: content_identity=vendor-modified must never be
        `best`; the decompile wins instead, and upstream is demoted to an alternate."""
        m = _load()
        _write_class(self.mod_root / "extracted" / "pkg" / "VendorClass.class")
        sources_jar = self._write_sources_jar(("org.eclipse.paho", "mqttv3", "1.2.5"),
                                               {"pkg/VendorClass.java": b"// not actually ours\n"})
        self._write_manifest({
            "groupId": "org.eclipse.paho", "artifactId": "mqttv3", "version": "1.2.5",
            "status": "fetched", "sources_jar_path": sources_jar,
            "classdiff": {"sources_only": [], "binary_only": [], "common": 1},
            "content_identity": {"status": "vendor-modified", "classes_identical": 0,
                                  "classes_different": 0, "classes_local_only": 1,
                                  "different_classes": [], "local_only_classes": []},
        })
        self.fx.add_rung("modA", "vineflower2", "pkg/VendorClass", content="// decompiled\n")
        name_index, sha_index, verdicts = m.build_upstream_index(self.root)
        self.assertEqual(verdicts.get("vendor-modified"), 1)
        rec = self._record("pkg/VendorClass", (name_index, sha_index))
        self.assertEqual(rec["best_kind"], "vineflower2")
        alt = [a for a in rec["alternates"] if a["kind"] == "upstream-different-build"]
        self.assertEqual(len(alt), 1)
        self.assertIn("vendor-modified", alt[0]["reason"])

    def test_partially_modified_trusts_only_the_identical_class(self):
        """A partially-modified jar: the class NOT in different_classes/local_only_classes is
        trusted; the class that IS listed there is not, and falls back to the decompile."""
        m = _load()
        _write_class(self.mod_root / "extracted" / "pkg" / "PartialSameClass.class")
        _write_class(self.mod_root / "extracted" / "pkg" / "PartialDiffClass.class")
        sources_jar = self._write_sources_jar(("grp", "partial-art", "2.0"), {
            "pkg/PartialSameClass.java": b"// identical to Central\n",
            "pkg/PartialDiffClass.java": b"// differs from Central\n",
        })
        self._write_manifest({
            "groupId": "grp", "artifactId": "partial-art", "version": "2.0", "status": "fetched",
            "sources_jar_path": sources_jar,
            "classdiff": {"sources_only": [], "binary_only": [], "common": 2},
            "content_identity": {
                "status": "partially-modified", "classes_identical": 1, "classes_different": 1,
                "classes_local_only": 0,
                "different_classes": ["pkg/PartialDiffClass.class"], "local_only_classes": [],
            },
        })
        self.fx.add_rung("modA", "vineflower2", "pkg/PartialDiffClass", content="// decompiled\n")
        name_index, sha_index, verdicts = m.build_upstream_index(self.root)
        self.assertEqual(verdicts.get("partially-modified"), 1)

        same_rec = self._record("pkg/PartialSameClass", (name_index, sha_index))
        self.assertEqual(same_rec["best_kind"], "upstream")

        diff_rec = self._record("pkg/PartialDiffClass", (name_index, sha_index))
        self.assertEqual(diff_rec["best_kind"], "vineflower2")
        alt = [a for a in diff_rec["alternates"] if a["kind"] == "upstream-different-build"]
        self.assertEqual(len(alt), 1)
        self.assertIn("partially-modified", alt[0]["reason"])

    def test_no_verdict_artifact_is_unproven_and_counted(self):
        """An artifact fetched but with NEITHER content_identity NOR identification_method -- the
        manifest carries no identity verdict at all for it -- is not proven and must not become
        `best`; it is counted in the artifact_verdict_counts / upstream_unproven_artifacts."""
        m = _load()
        _write_class(self.mod_root / "extracted" / "pkg" / "NoVerdictClass.class")
        sources_jar = self._write_sources_jar(("grp", "no-verdict-art", "1.0"),
                                               {"pkg/NoVerdictClass.java": b"// unverified\n"})
        self._write_manifest({
            "groupId": "grp", "artifactId": "no-verdict-art", "version": "1.0", "status": "fetched",
            "sources_jar_path": sources_jar,
            "classdiff": {"sources_only": [], "binary_only": [], "common": 1},
        })
        name_index, sha_index, verdicts = m.build_upstream_index(self.root)
        self.assertEqual(verdicts.get("no-verdict"), 1)
        rec = self._record("pkg/NoVerdictClass", (name_index, sha_index))
        self.assertEqual(rec["best_kind"], "missing")
        alt = [a for a in rec["alternates"] if a["kind"] == "upstream-unproven"]
        self.assertEqual(len(alt), 1)

        out_dir = self.root / "_best"
        rc = m.main(["--organized", str(self.root), "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "best-source.json").read_text())
        self.assertEqual(data["summary"]["upstream_unproven_artifacts"], 1)
        self.assertEqual(data["summary"]["upstream_artifact_verdicts"].get("no-verdict"), 1)

    def test_population_linked_by_jar_sha256_preferred_over_name_match(self):
        """When this population's own jar_sha256 equals a manifest artifact's recorded
        binary_sha256, that artifact's verdict is used via the sha256 join (reason says so);
        without a matching jar_sha256, the same class name still falls back to the weaker
        name-only index."""
        m = _load()
        _write_class(self.mod_root / "extracted" / "pkg" / "ShaLinkedClass.class")
        sources_jar = self._write_sources_jar(("grp", "sha-linked-art", "1.0"),
                                               {"pkg/ShaLinkedClass.java": b"// sha-linked\n"})
        binary_sha256 = "ab" * 32
        self._write_manifest({
            "groupId": "grp", "artifactId": "sha-linked-art", "version": "1.0", "status": "fetched",
            "sources_jar_path": sources_jar,
            "classdiff": {"sources_only": [], "binary_only": [], "common": 1},
            "content_identity": {"status": "resigned-identical"},
            "binary_sha256": binary_sha256,
        })
        name_index, sha_index, _verdicts = m.build_upstream_index(self.root)
        self.assertIn(binary_sha256, sha_index)

        linked_rec = self._record("pkg/ShaLinkedClass", (name_index, sha_index),
                                   jar_sha256=binary_sha256)
        self.assertEqual(linked_rec["best_kind"], "upstream")
        self.assertIn("population jar sha256", linked_rec["reason"])

        unlinked_rec = self._record("pkg/ShaLinkedClass", (name_index, sha_index),
                                     jar_sha256="ff" * 32)
        self.assertEqual(unlinked_rec["best_kind"], "upstream")
        self.assertIn("matched by class name only", unlinked_rec["reason"])

    def test_sha1_exact_content_identity_is_trusted_whole(self):
        """Orchestrator-found defect fix (2026-09-28): tools/n5-upstream-sources.py now records
        `content_identity: {"status": "sha1-exact", ...}` for a b117 whole-jar SHA-1 match --
        the STRONGEST possible proof (equivalent to identified-by-sha1 / resigned-identical) --
        and it must be trusted for the whole jar, not treated as an unrecognized/unproven status."""
        m = _load()
        _write_class(self.mod_root / "extracted" / "pkg" / "ExactClass.class")
        sources_jar = self._write_sources_jar(("grp", "exact-art", "1.0"),
                                               {"pkg/ExactClass.java": b"// b117 exact\n"})
        self._write_manifest({
            "groupId": "grp", "artifactId": "exact-art", "version": "1.0", "status": "fetched",
            "sources_jar_path": sources_jar,
            "classdiff": {"sources_only": [], "binary_only": [], "common": 1},
            "content_identity": {"status": "sha1-exact",
                                  "source": "evidence/b117/maven-repo1.json", "sha1": "deadbeef"},
        })
        name_index, sha_index, verdicts = m.build_upstream_index(self.root)
        self.assertEqual(verdicts.get("sha1-exact"), 1)
        rec = self._record("pkg/ExactClass", (name_index, sha_index))
        self.assertEqual(rec["best_kind"], "upstream")
        self.assertIn("sha1-exact", rec["reason"])

    def test_mixed_artifact_resolves_trust_per_occurrence_not_by_other_occurrence(self):
        """Orchestrator-found defect fix: when an artifact's occurrences disagree (b117 exact for
        one, genuinely different for another), tools/n5-upstream-sources.py records a "mixed"
        artifact-level content_identity and a per-OCCURRENCE content_identity + binary_sha256.
        A population linked (by its own jar_sha256) to the TRUSTED occurrence must be trusted;
        one linked to the UNTRUSTED occurrence must NOT be -- never by collapsing to whichever
        occurrence looks best, and never via the weak class-name-only index (which cannot tell
        which occurrence it corresponds to)."""
        m = _load()
        _write_class(self.mod_root / "extracted" / "pkg" / "MixedClass.class")
        sources_jar = self._write_sources_jar(("grp", "mixed-art", "1.0"),
                                               {"pkg/MixedClass.java": b"// shared sources\n"})
        trusted_sha256 = "aa" * 32
        untrusted_sha256 = "bb" * 32
        self._write_manifest({
            "groupId": "grp", "artifactId": "mixed-art", "version": "1.0", "status": "fetched",
            "sources_jar_path": sources_jar,
            "classdiff": {"sources_only": [], "binary_only": [], "common": 1},
            "content_identity": {"status": "mixed", "source": "per-occurrence",
                                  "reason": "occurrences disagree"},
            "occurrences": [
                {"kind": "LIB-INF", "name": "mod.jar!LIB-INF/mixed-art-1.0.jar",
                 "binary_sha256": trusted_sha256,
                 "content_identity": {"status": "sha1-exact",
                                       "source": "evidence/b117/maven-repo1.json"}},
                {"kind": "bin/ext", "name": "bin/ext/mixed-art-1.0.jar",
                 "binary_sha256": untrusted_sha256,
                 "content_identity": {"status": "vendor-modified", "classes_identical": 0,
                                       "classes_different": 0, "classes_local_only": 1,
                                       "different_classes": [], "local_only_classes": []}},
            ],
        })
        name_index, sha_index, verdicts = m.build_upstream_index(self.root)
        self.assertEqual(verdicts.get("mixed"), 1)
        self.assertIn(trusted_sha256, sha_index)
        self.assertIn(untrusted_sha256, sha_index)

        trusted_rec = self._record("pkg/MixedClass", (name_index, sha_index),
                                    jar_sha256=trusted_sha256)
        self.assertEqual(trusted_rec["best_kind"], "upstream")

        untrusted_rec = self._record("pkg/MixedClass", (name_index, sha_index),
                                      jar_sha256=untrusted_sha256)
        self.assertNotEqual(untrusted_rec["best_kind"], "upstream")
        alt = [a for a in untrusted_rec["alternates"] if a["kind"] == "upstream-different-build"]
        self.assertEqual(len(alt), 1)

        # No jar-sha256 link at all (name-only match): a mixed artifact is never blindly trusted
        # via the weak name-only index either -- it doesn't know which occurrence applies.
        unlinked_rec = self._record("pkg/MixedClass", (name_index, sha_index),
                                     jar_sha256="cc" * 32)
        self.assertNotEqual(unlinked_rec["best_kind"], "upstream")


def m_hash(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


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
