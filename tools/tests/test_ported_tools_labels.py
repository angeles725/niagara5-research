"""These tools (module-find.py, bog-nav.py, dashboard-preview.py) are used-as-is
from the N4 corpus: their logic is already version-agnostic (they operate on
a Java source tree / a bog ZIP / a dashboard rc/ folder given as an explicit
argument, with no N4-specific hardcoding). The only porting change is the
module docstring, which described the tool as being "for Niagara N4" only.
This test locks that relabel down.
"""
import os
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _docstring(fname):
    with open(os.path.join(TOOLS_DIR, fname), encoding="utf-8") as fh:
        head = fh.read(2000)
    return head


class TestPortedToolLabels(unittest.TestCase):
    def test_module_find_labels_n4_and_n5(self):
        doc = _docstring("module-find.py")
        self.assertIn("N4", doc)
        self.assertIn("N5", doc)

    def test_bog_nav_labels_n4_and_n5(self):
        doc = _docstring("bog-nav.py")
        self.assertIn("N4", doc)
        self.assertIn("N5", doc)

    def test_dashboard_preview_labels_n4_and_n5(self):
        doc = _docstring("dashboard-preview.py")
        self.assertIn("N4", doc)
        self.assertIn("N5", doc)


if __name__ == "__main__":
    unittest.main()
