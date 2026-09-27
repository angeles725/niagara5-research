"""
Robustness tests: bad input must fail gracefully.

Contract: a missing class/module is a user error, not a program error. The CLI
must report it in plain language and must NOT leak a Python traceback — an
unhandled exception is a bug regardless of exit code.
"""

import unittest

from _harness import run_nav, MISSING_CLASS, MISSING_MODULE


def _assert_no_traceback(testcase, cmd, rc, out, err):
    combined = out + "\n" + err
    testcase.assertNotIn(
        "Traceback (most recent call last)", combined,
        "{} leaked a Python traceback on bad input:\n{}".format(
            cmd, combined[-600:]))
    # A graceful failure returns a controlled code, never a crash signal.
    testcase.assertIn(
        rc, (0, 1, 2),
        "{} returned uncontrolled exit code {}".format(cmd, rc))


class MissingClass(unittest.TestCase):
    def test_missing_class_no_traceback(self):
        for cmd in ["class", "methods", "hierarchy", "callers",
                    "integration-contract"]:
            with self.subTest(command=cmd):
                rc, out, err = run_nav(cmd, MISSING_CLASS)
                _assert_no_traceback(self, cmd, rc, out, err)


class MissingModule(unittest.TestCase):
    def test_missing_module_no_traceback(self):
        for cmd in ["module", "ord-validate", "resolve-audit",
                    "resource-leak", "dependency-audit", "module-health"]:
            with self.subTest(command=cmd):
                rc, out, err = run_nav(cmd, MISSING_MODULE)
                _assert_no_traceback(self, cmd, rc, out, err)


class MissingModuleJson(unittest.TestCase):
    """Bad input under --json should still yield parseable JSON or a clean
    error — never a traceback."""

    def test_missing_module_json_no_traceback(self):
        for cmd in ["resolve-audit", "resource-leak", "dependency-audit"]:
            with self.subTest(command=cmd):
                rc, out, err = run_nav(cmd, MISSING_MODULE, "--json")
                _assert_no_traceback(self, cmd, rc, out, err)


if __name__ == "__main__":
    unittest.main()
