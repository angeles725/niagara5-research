#!/usr/bin/env python3
"""C4: `exact` mode of tools/n5-splice-methods.py. A canonical-only method is a target (the goal is
the shipped instruction stream, not an equivalent one), donors and hill-climb steps must reach
`exact`, and a class is emitted only when it grades roundtrip-exact as a whole."""
import unittest
from pathlib import Path
from unittest import mock

from test_n5_splice_methods import JDK, _SpliceFixture, _jdk

# the shipped shape has one *return per branch; the decompiler folds them into one expression
SHIPPED = """package p;
public class Foo {
  int z;
  boolean a(int x) {
    if ((x & 1) == 1) {
      return true;
    }
    return false;
  }
  int b(int x) { return x + z; }
}
"""
PRIMARY = SHIPPED.replace("    if ((x & 1) == 1) {\n      return true;\n    }\n    return false;\n",
                          "    return (x & 1) == 1;\n")


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class ExactBase(_SpliceFixture):
    def _fake(self, *a, **k):
        return None, "no donor"

    def _exact(self, name, mod_dir, **kw):
        with mock.patch.object(self.mod.FID, "_decompile_one_class_with", side_effect=self._fake):
            return self.mod.splice_module(name, self.root / "organized", "vineflower2", "vineflower2s", ["p/Foo"],
                                          classpath="", helper_dir=self.helper, javac_bin=f"{JDK}/javac",
                                          javap_bin=f"{JDK}/javap", java_bin=f"{JDK}/java", tool_server=False,
                                          decompilers=(), **kw)



class TestExactMode(ExactBase):
    def test_canonical_verdict_is_a_mismatch_in_exact_mode(self):
        mod_dir, _ = self._module("verdict", SHIPPED, PRIMARY, None, None)
        FID = self.mod.FID
        ship = FID.parse_javap_verbose(FID.run_javap_verbose(str(mod_dir / "extracted/p/Foo.class"),
                                                             javap_bin=f"{JDK}/javap"))
        ours = self.mod.compile_parse(mod_dir / "vineflower2/p/Foo.java", "Foo", "", f"{JDK}/javac", f"{JDK}/javap", False)
        key = ("a", "(I)Z")
        self.assertEqual(self.mod.per_method_verdicts(ship, ours)[0][key]["verdict"], "canonical")
        exact_v = self.mod.per_method_verdicts(ship, ours, exact=True)[0][key]
        self.assertEqual((exact_v["verdict"], exact_v["rules"]), ("mismatch", ["tail"]))

    def test_site_hypothesis_reaches_exact(self):
        mod_dir, _ = self._module("reach", SHIPPED, PRIMARY, None, None)
        man = self._exact("reach", mod_dir, exact=True, climb=True, hypotheses=("split-return-boolean",))
        rec = man["classes"]["p/Foo"]
        self.assertEqual(rec["self_grade"], "roundtrip-exact")
        self.assertIn("if ((x & 1) == 1)", (mod_dir / "vineflower2s/p/Foo.java").read_text())

    def test_without_exact_a_canonical_class_is_left_alone(self):
        mod_dir, _ = self._module("plain", SHIPPED, PRIMARY, None, None)
        man = self._exact("plain", mod_dir, climb=True, hypotheses=("split-return-boolean",))
        self.assertEqual(man["not_candidates"]["p/Foo"]["reason"], "already-clean")

    def test_unreachable_exact_is_refused_not_emitted_as_canonical(self):
        mod_dir, _ = self._module("stuck", SHIPPED, PRIMARY, None, None)
        man = self._exact("stuck", mod_dir, exact=True)
        self.assertEqual(man["classes"], {})
        self.assertIn(man["refused"]["p/Foo"]["reason"], ("no-donor",))

    def test_retargeted_class_keeps_its_earlier_splice_when_exact_fails(self):
        mod_dir, _ = self._module("keepx", SHIPPED, PRIMARY, None, None)
        first = self._exact("keepx", mod_dir, exact=True, climb=True, hypotheses=("split-return-boolean",))
        kept = (mod_dir / "vineflower2s/p/Foo.java").read_text()
        self.assertIn("p/Foo", first["classes"])
        # a later exact run on the same class cannot improve on it; the earlier splice must survive
        again = self._exact("keepx", mod_dir, exact=True, keep_existing=True)
        self.assertIn("p/Foo", again["classes"])
        self.assertEqual((mod_dir / "vineflower2s/p/Foo.java").read_text(), kept)


MANY = "".join(f"  boolean m{i}(int x) {{\n    return x == {i};\n  }}\n" for i in range(40))
SHIPPED_MANY = SHIPPED.replace("  boolean a(int x)", MANY + "  boolean a(int x)")
PRIMARY_MANY = PRIMARY.replace("  boolean a(int x)", MANY + "  boolean a(int x)")


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class TestClimbScope(ExactBase):
    def test_sites_outside_the_mismatching_methods_are_not_tried(self):
        # 40 already-exact `return x == i;` sites precede the one that matters (site cap is 30)
        mod_dir, _ = self._module("scope", SHIPPED_MANY, PRIMARY_MANY, None, None)
        man = self._exact("scope", mod_dir, exact=True, climb=True, hypotheses=("split-return-boolean",))
        self.assertEqual(man["classes"]["p/Foo"]["self_grade"], "roundtrip-exact")


if __name__ == "__main__":
    unittest.main()
