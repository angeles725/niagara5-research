"""Acceptance test: the N5 port must contain zero references to the N4
corpus's absolute, machine-specific path.

TDD note: this fails (RED) against the freshly-copied N4 tree (which still
has ORGANIZED_DIR = "/home/cristian/modules/Prototipos/modulos/organized"
and several fallback-path literals in module_nav_lib/*.py), and is expected
to pass (GREEN) once every hardcoded N4 path is replaced by
corpus_config.resolve_organized_dir() / a computed sibling default.
"""

import glob
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN = ("/home/cristian/modules", "Prototipos")


class NoHardcodedN4PathsTests(unittest.TestCase):
    def test_tools_tree_has_no_n4_absolute_paths(self):
        py_files = sorted(
            glob.glob(os.path.join(BASE_DIR, "tools", "**", "*.py"), recursive=True)
        )
        self.assertGreater(len(py_files), 0, "expected to find copied .py files under tools/")

        offenders = []
        for path in py_files:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            for needle in FORBIDDEN:
                if needle in content:
                    offenders.append((os.path.relpath(path, BASE_DIR), needle))

        self.assertEqual(
            offenders, [],
            "Found hardcoded N4 path references (must be zero): {}".format(offenders)
        )

    def test_reindex_sh_has_no_n4_absolute_paths(self):
        reindex_path = os.path.join(BASE_DIR, "reindex.sh")
        with open(reindex_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        for needle in FORBIDDEN:
            self.assertNotIn(needle, content,
                              "reindex.sh must not hardcode N4 corpus path ({})".format(needle))


if __name__ == "__main__":
    unittest.main()
