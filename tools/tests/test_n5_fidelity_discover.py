#!/usr/bin/env python3
"""discover_top_level_classes (tools/n5-fidelity.py): a class file is top-level unless its simple
name is `Outer$Inner`; a simple name that itself STARTS with `$` (gson's `$Gson$Types`) is a
top-level class too (C2d-G2) -- unless a shorter `$`-boundary prefix is a class in the same
directory, which then owns it as a nested/anonymous class."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-fidelity.py")


def _load():
    spec = importlib.util.spec_from_file_location("n5_fidelity", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _tree(td, names):
    root = Path(td)
    for n in names:
        f = root / n
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"\xca\xfe\xba\xbe")
    return root


class DiscoverTopLevelClassesTest(unittest.TestCase):
    def test_plain_nested_and_anonymous_are_not_top_level(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = _tree(td, ["p/A.class", "p/A$B.class", "p/A$1.class", "module-info.class"])
            self.assertEqual([f for f, _ in m.discover_top_level_classes(root)], ["p/A"])

    def test_dollar_prefixed_top_level_classes_are_discovered(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = _tree(td, ["p/$Gson$Types.class", "p/$Gson$Types$Impl.class", "p/$Gson$Types$1.class",
                              "p/$Gson$Pre.class", "p/Plain.class", "p/Plain$In.class"])
            self.assertEqual([f for f, _ in m.discover_top_level_classes(root)],
                             ["p/$Gson$Pre", "p/$Gson$Types", "p/Plain"])

    def test_nested_files_of_a_dollar_prefixed_outer_are_found(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            root = _tree(td, ["p/$G$T.class", "p/$G$T$Impl.class", "p/$G$P.class"])
            self.assertEqual(m.list_nested_class_files(str(root / "p" / "$G$T.class")), ["$G$T$Impl.class"])


if __name__ == "__main__":
    unittest.main()
