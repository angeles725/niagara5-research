"""Tests for tools/niagara-security-audit.py adapted for the N5 corpus.

Ported from niagara-research (N4 kit tool). Adaptation:
  - Labeled N4/N5 (the checks are Niagara-platform-general, not N4-only).
  - Honest 'not-found' reporting: on a fresh N5 install there is no
    security/ directory yet (no station has been created). The N4 original
    silently OMITTED a row for SEC-02/SEC-06/SEC-15 when their target path
    was missing, and worse, SEC-11 reported a false PASS ("all keys >= 2048")
    when the truststore it never found had exactly zero keys. This test
    locks down that every one of those checks now emits an explicit
    NOTFOUND/MANUAL row instead of a silent gap or a misleading PASS.
"""
import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAVE_KEYTOOL = shutil.which("keytool") is not None


def _load():
    spec = importlib.util.spec_from_file_location(
        "security_audit_n5", os.path.join(TOOLS_DIR, "niagara-security-audit.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSecurityAuditN5(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = os.path.join(self.tmp.name, "n5home")
        os.makedirs(os.path.join(self.home, "defaults"))
        with open(os.path.join(self.home, "defaults", "system.properties"), "w") as fh:
            fh.write("niagara.moduleVerificationMode=full\n")

    def _run(self):
        rep = self.mod.Report()
        self.mod.audit(self.home, None, None, rep)
        return {r["id"]: r for r in rep.rows}

    def test_docstring_labels_n4_and_n5(self):
        with open(os.path.join(TOOLS_DIR, "niagara-security-audit.py"), encoding="utf-8") as fh:
            head = fh.read(1500)
        self.assertIn("N4", head)
        self.assertIn("N5", head)

    def test_sec02_missing_truststore_is_not_silently_dropped(self):
        rows = self._run()
        self.assertIn("SEC-02", rows)
        self.assertIn(rows["SEC-02"]["verdict"], ("MANUAL", "NOTFOUND"))

    def test_sec11_does_not_falsely_pass_when_truststore_absent(self):
        rows = self._run()
        # The N4 bug: 0 keys found -> weak=[] -> reported PASS. Must not PASS
        # when the file that would supply key sizes was never found.
        self.assertNotEqual(rows["SEC-11"]["verdict"], "PASS")

    def test_sec15_missing_modules_dir_is_reported(self):
        rows = self._run()
        self.assertIn("SEC-15", rows)

    def test_sec06_missing_license_dir_is_reported(self):
        rows = self._run()
        self.assertIn("SEC-06", rows)

    @unittest.skipUnless(HAVE_KEYTOOL, "keytool not on PATH")
    def test_sec11_does_not_falsely_pass_on_custom_truststore_password(self):
        # Regression for R3-sec11-false-pass-custom-password: a truststore
        # with a non-default storepass makes `keytool -list` fail with the
        # default "changeit" password, stdout has no "N-bit" tokens, and the
        # empty sizes list must not be reported as a clean PASS.
        secdir = os.path.join(self.home, "security")
        os.makedirs(secdir, exist_ok=True)
        ts = os.path.join(secdir, "truststore.jks")
        subprocess.run(
            [
                "keytool", "-genkeypair", "-alias", "test", "-keyalg", "RSA",
                "-keysize", "2048", "-validity", "1", "-keystore", ts,
                "-storepass", "s3cr3t-not-default", "-dname", "CN=test",
            ],
            capture_output=True, text=True, check=True,
        )
        rows = self._run()
        self.assertEqual(rows["SEC-11"]["verdict"], "MANUAL")

    def test_sec11_does_not_pass_when_keytool_succeeds_but_reports_no_keys(self):
        # Regression for the RDD validator rejection on 370284c: keytool can
        # exit 0 with no "N-bit" tokens (empty truststore, or an older keytool
        # output format). Zero inspected keys is not evidence of strong keys.
        secdir = os.path.join(self.home, "security")
        os.makedirs(secdir, exist_ok=True)
        with open(os.path.join(secdir, "truststore.jks"), "wb") as fh:
            fh.write(b"placeholder")
        self.mod.keytool_keysizes = lambda path, pw="changeit": []
        rows = self._run()
        self.assertEqual(rows["SEC-11"]["verdict"], "MANUAL")

    def test_keytool_keysizes_returns_none_on_missing_file(self):
        mod = _load()
        self.assertIsNone(mod.keytool_keysizes("/nonexistent/truststore.jks"))


if __name__ == "__main__":
    unittest.main()
