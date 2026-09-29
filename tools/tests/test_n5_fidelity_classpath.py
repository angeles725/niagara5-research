#!/usr/bin/env python3
"""build_classpath must reproduce the module path N5's launcher builds.

Evidence (T21/F7, see odd/tasks/n5-full-grading.md): nre.dll's initPaths()
format strings are `%s\\bin\\ext`, `%s\\bin\\ext\\%s` (bcfips|bcstd, chosen by
initFips()), `%s\\bin\\ext\\jxbrowser`, `%s\\bin\\ext\\system`, plus the
separate `%s\\bin\\ext\\securityBridge`; the JVM is `<niagaraHome>\\jre`, whose
modules image carries the javafx.* / jfx.* modules. A grader classpath built
from bin/ext/*.jar alone (non-recursive) and a JDK without JavaFX made every
class touching BouncyCastle, JxBrowser, OrientDB or JavaFX a false no-compile.
"""
import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-fidelity.py")

REAL_BIN_EXT = Path("/home/cristian/niagara5-research-localcache/jar-mirror-5.0.0.28/bin-ext")
REAL_JRE = Path("/mnt/c/Program Files/Niagara/5.0.0.28/jre")
JIMAGE = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/jimage"


def _load():
    spec = importlib.util.spec_from_file_location("n5_fidelity", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _jar(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")


FAKE_JIMAGE = """#!/usr/bin/env python3
import os, sys, re
args = sys.argv[1:]
assert args[0] == "extract", args
out = args[args.index("--dir") + 1]
inc = args[args.index("--include") + 1]
assert inc.startswith("regex:"), inc
rx = re.compile(inc[len("regex:"):])
for m in ("java.base", "javafx.base", "javafx.graphics", "jfx.incubator.input"):
    if rx.fullmatch("/" + m + "/x/Y.class"):
        d = os.path.join(out, m, "x")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "Y.class"), "wb").close()
"""


class TestBinExtSubdirectories(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        self.td = tempfile.TemporaryDirectory()
        root = Path(self.td.name)
        self.bin_ext = root / "bin-ext"
        for rel in ("top.jar", "bcstd/bcprov.jar", "bcfips/bc-fips.jar", "jxbrowser/jx.jar",
                    "system/orientdb-core.jar", "securityBridge/securityBridge.jar", "unrelated/other.jar"):
            _jar(self.bin_ext / rel)
        self.modules = root / "modules"
        _jar(self.modules / "baja.jar")
        self.no_jre = root / "no-jre"

    def tearDown(self):
        self.td.cleanup()

    def _cp(self, cache, **kw):
        cp = self.mod.build_classpath(Path(self.td.name) / cache, self.modules, self.bin_ext,
                                      jre_dir=self.no_jre, **kw)
        return [Path(e).relative_to(self.bin_ext).as_posix() for e in cp.split(":")
                if e.startswith(str(self.bin_ext))]

    def test_default_variant_is_bcstd_plus_launcher_subdirs(self):
        rels = self._cp("c1")
        for rel in ("top.jar", "bcstd/bcprov.jar", "jxbrowser/jx.jar", "system/orientdb-core.jar",
                    "securityBridge/securityBridge.jar"):
            self.assertIn(rel, rels)
        self.assertNotIn("bcfips/bc-fips.jar", rels)
        # only the directories the launcher names -- never a blind recursive glob
        self.assertNotIn("unrelated/other.jar", rels)

    def test_bcfips_variant_replaces_bcstd(self):
        rels = self._cp("c2", bc_variant="bcfips")
        self.assertIn("bcfips/bc-fips.jar", rels)
        self.assertNotIn("bcstd/bcprov.jar", rels)

    def test_unknown_variant_is_rejected(self):
        with self.assertRaises(ValueError):
            self._cp("c3", bc_variant="bcother")

    def test_manifest_from_older_layout_is_rebuilt(self):
        cache = Path(self.td.name) / "c4"
        cache.mkdir()
        # an old-layout cache: top-level jars only, no inputs record
        (cache / "classpath.txt").write_text(str(self.bin_ext / "top.jar") + "\n")
        rels = self._cp("c4")
        self.assertIn("bcstd/bcprov.jar", rels)

    def test_variant_change_invalidates_cache(self):
        self._cp("c5")
        rels = self._cp("c5", bc_variant="bcfips")
        self.assertIn("bcfips/bc-fips.jar", rels)
        self.assertNotIn("bcstd/bcprov.jar", rels)


class TestJreFxModules(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        self.td = tempfile.TemporaryDirectory()
        root = Path(self.td.name)
        self.jre = root / "jre"
        (self.jre / "lib").mkdir(parents=True)
        (self.jre / "lib" / "modules").write_bytes(b"fake image")
        self.jimage = root / "jimage"
        self.jimage.write_text(FAKE_JIMAGE)
        self.jimage.chmod(self.jimage.stat().st_mode | stat.S_IEXEC)
        self.empty = root / "empty"
        self.empty.mkdir()

    def tearDown(self):
        self.td.cleanup()

    def test_fx_modules_of_the_n5_jre_are_on_the_classpath(self):
        cache = Path(self.td.name) / "cache"
        cp = self.mod.build_classpath(cache, self.empty, self.empty, jre_dir=self.jre,
                                      jimage_bin=str(self.jimage)).split(":")
        names = sorted(Path(e).name for e in cp)
        self.assertEqual(names, ["javafx.base", "javafx.graphics", "jfx.incubator.input"])
        for e in cp:
            self.assertTrue(Path(e).is_dir(), e)
        inputs = json.loads((cache / "classpath.inputs.json").read_text())
        self.assertEqual(inputs["jre_modules_sha256"],
                         self.mod.sha256_of(self.jre / "lib" / "modules"))
        # cache hit: same classpath without re-extracting
        self.jimage.write_text("#!/bin/sh\nexit 3\n")
        cp2 = self.mod.build_classpath(cache, self.empty, self.empty, jre_dir=self.jre,
                                       jimage_bin=str(self.jimage)).split(":")
        self.assertEqual(sorted(cp2), sorted(cp))

    def test_missing_jre_adds_nothing(self):
        cp = self.mod.build_classpath(Path(self.td.name) / "c", self.empty, self.empty,
                                      jre_dir=Path(self.td.name) / "nope", jimage_bin=str(self.jimage))
        self.assertEqual(cp, "")


@unittest.skipUnless(REAL_BIN_EXT.is_dir() and (REAL_JRE / "lib" / "modules").is_file()
                     and os.path.isfile(JIMAGE), "N5 jar mirror / N5 JRE / jimage not present")
class TestRealN5Classpath(unittest.TestCase):
    def test_real_classpath_resolves_the_previously_missing_packages(self):
        mod = _load()
        with tempfile.TemporaryDirectory() as td:
            empty = Path(td) / "empty"
            empty.mkdir()
            cp = mod.build_classpath(Path(td) / "cache", empty, REAL_BIN_EXT, jre_dir=REAL_JRE,
                                     jimage_bin=JIMAGE).split(":")
            needed = {
                "org/bouncycastle/asn1/x500/X500Name.class": None,
                "org/bouncycastle/tls/TlsClient.class": None,
                "com/teamdev/jxbrowser/browser/Browser.class": None,
                "com/orientechnologies/orient/core/db/ODatabaseSession.class": None,
                "javafx/application/Platform.class": None,
            }
            for e in cp:
                p = Path(e)
                for name in needed:
                    if needed[name]:
                        continue
                    if p.is_dir():
                        if (p / name).is_file():
                            needed[name] = e
                    else:
                        with zipfile.ZipFile(p) as zf:
                            if name in zf.namelist():
                                needed[name] = e
            self.assertEqual([n for n, v in needed.items() if v is None], [])
            self.assertIn("/bcstd/", needed["org/bouncycastle/tls/TlsClient.class"])


if __name__ == "__main__":
    unittest.main()
