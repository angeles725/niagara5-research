"""Tests for tools/port-junit4-to-testng.py (recipe from niagara5-block29.md)."""
import importlib.util
import os
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location(
        "port_junit4", os.path.join(TOOLS_DIR, "port-junit4-to-testng.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SRC = """package x;
import org.junit.Test;
import static org.junit.Assert.*;
public class T {
  @Test public void a() {
    assertEquals(3, f(1, g(2)));
    assertEquals("msg, with comma", 5L, h(a, b));
    assertTrue("must hold", ok());
    assertFalse(bad());
    assertNull("n", v);
  }
}
"""


class TestPortJunit4ToTestng(unittest.TestCase):
    def setUp(self):
        self.out = _load().port_source(SRC)

    def test_imports_are_rewritten_to_testng(self):
        self.assertIn("import org.testng.annotations.Test;", self.out)
        self.assertIn("import org.testng.Assert;", self.out)
        self.assertNotIn("org.junit", self.out)

    def test_assert_equals_swaps_expected_and_actual_across_nested_calls(self):
        self.assertIn("Assert.assertEquals(f(1, g(2)), 3)", self.out)

    def test_message_moves_last_and_string_commas_are_not_split(self):
        self.assertIn('Assert.assertEquals(h(a, b), 5L, "msg, with comma")', self.out)
        self.assertIn('Assert.assertTrue(ok(), "must hold")', self.out)
        self.assertIn('Assert.assertNull(v, "n")', self.out)

    def test_single_argument_asserts_are_only_prefixed(self):
        self.assertIn("Assert.assertFalse(bad())", self.out)


if __name__ == "__main__":
    unittest.main()
