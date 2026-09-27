"""
JSON contract tests.

The project's own acceptance criterion says: "--json produce JSON válido en
todos los comandos". This suite enforces it — for every command that declares
--json, stdout must parse as JSON with no progress noise mixed in.

This is exactly the class of bug that shipped undetected before (progress
`Scanning...` / `Loading...` written to stdout ahead of the JSON body).
"""

import json
import unittest

from _harness import run_nav, JSON_COMMANDS, FIXTURE_CLASS


class JsonContract(unittest.TestCase):
    def test_json_stdout_is_pure_json(self):
        for cmd, args in JSON_COMMANDS:
            with self.subTest(command=cmd):
                rc, out, err = run_nav(cmd, *args, "--json")
                self.assertEqual(
                    rc, 0,
                    "{} --json exited {}; stderr:\n{}".format(cmd, rc, err[:500]))
                try:
                    parsed = json.loads(out)
                except json.JSONDecodeError as exc:
                    self.fail(
                        "{} --json produced invalid JSON on stdout "
                        "(progress leaked to stdout?): {}\n"
                        "first 200 chars:\n{}".format(cmd, exc, out[:200]))
                self.assertIsInstance(
                    parsed, (dict, list),
                    "{} --json top-level should be object/array".format(cmd))

    def test_slot_validate_json_contract(self):
        # slot-validate requires --add; verify its --json path is clean too.
        # --add requires "name:type[:default]" format.
        rc, out, err = run_nav(
            "slot-validate", FIXTURE_CLASS, "--add", "refreshSeconds:int",
            "--kind", "property", "--json")
        self.assertEqual(rc, 0, "slot-validate exited {}: {}".format(rc, err[:300]))
        try:
            json.loads(out)
        except json.JSONDecodeError as exc:
            self.fail("slot-validate --json invalid: {}\n{}".format(exc, out[:200]))


if __name__ == "__main__":
    unittest.main()
