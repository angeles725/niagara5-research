"""
Smoke tests for core navigation commands.

Verifies the everyday commands run against the real indexes, exit 0, and
produce non-empty, plausible output. Not exhaustive — a tripwire that the
CLI and its indexes are wired up and loadable.
"""

import unittest

from _harness import (
    run_nav, FIXTURE_CLASS, FIXTURE_MODULE, FIXTURE_CLASS2,
)


class CoreSmoke(unittest.TestCase):
    def test_stats(self):
        rc, out, err = run_nav("stats")
        self.assertEqual(rc, 0, err[:300])
        self.assertIn("Total", out)

    def test_class_lookup(self):
        rc, out, err = run_nav("class", FIXTURE_CLASS)
        self.assertEqual(rc, 0, err[:300])
        self.assertIn(FIXTURE_CLASS, out)
        # N5 note: N4's javax.baja.alarm package was renamed to niagara.alarm.
        self.assertIn("niagara.alarm", out)

    def test_module_lookup(self):
        rc, out, err = run_nav("module", FIXTURE_MODULE)
        self.assertEqual(rc, 0, err[:300])
        self.assertTrue(out.strip(), "module output should not be empty")

    def test_search_glob(self):
        # Narrow glob so the target isn't truncated by the default result cap.
        rc, out, err = run_nav("search", "BAlarmService*")
        self.assertEqual(rc, 0, err[:300])
        self.assertIn("BAlarmService", out)

    def test_methods(self):
        rc, out, err = run_nav("methods", FIXTURE_CLASS2)
        self.assertEqual(rc, 0, err[:300])
        self.assertTrue(out.strip(), "methods output should not be empty")

    def test_hierarchy(self):
        rc, out, err = run_nav("hierarchy", FIXTURE_CLASS2, "--depth", "1")
        self.assertEqual(rc, 0, err[:300])
        self.assertTrue(out.strip())


if __name__ == "__main__":
    unittest.main()
