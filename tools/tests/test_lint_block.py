"""Tests for tools/lint-block.py (mechanical decompiler-fidelity / method-blind-spot rules R0-R8).

Fixtures live under tools/tests/fixtures/lint_block/niagara5-block9NNN.md — small synthetic blocks,
each built from the real corpus positives/negatives named in odd/tasks/decompiler-fidelity-audit.md
T8 (B84 R1, B98 R2, B107 R5, B106 R6, B96/B105 R7, B13 R8).
"""
import os
import subprocess
import sys
import unittest

TOOL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lint-block.py")
FIXDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "lint_block")


def run(*args):
    return subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True)


def fx(name):
    return os.path.join(FIXDIR, name)


def lines_for(stdout, rule):
    return [l for l in stdout.splitlines() if l.startswith(rule + " ")]


class TestCleanFixture(unittest.TestCase):
    def test_clean_block_has_no_findings_in_audit(self):
        r = run("--audit", fx("niagara5-block9000.md"))
        self.assertEqual(r.returncode, 0)
        for rule in ("R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"):
            self.assertEqual(lines_for(r.stdout, rule), [], f"{rule} fired on the clean fixture")

    def test_clean_block_passes_enforced(self):
        r = run(fx("niagara5-block9000.md"))
        self.assertEqual(r.returncode, 0)


class TestR1SyntaxAdoption(unittest.TestCase):
    def test_audit_fires_on_positive_paragraph_and_row_only(self):
        r = run("--audit", fx("niagara5-block9001.md"))
        self.assertEqual(r.returncode, 0)
        hits = lines_for(r.stdout, "R1")
        self.assertEqual(len(hits), 2, hits)
        self.assertTrue(any(":6:" in h or ":5:" in h for h in hits), hits)

    def test_enforced_fails_above_threshold(self):
        r = run(fx("niagara5-block9001.md"))
        self.assertEqual(r.returncode, 1)
        self.assertTrue(lines_for(r.stdout, "R1"))

    def test_enforced_skips_below_threshold(self):
        r = run("--min-block", "9999", fx("niagara5-block9001.md"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(lines_for(r.stdout, "R1"), [])


class TestR2AbsenceCensus(unittest.TestCase):
    def test_single_jar_unzip_still_fires(self):
        r = run("--audit", fx("niagara5-block9002.md"))
        hits = lines_for(r.stdout, "R2")
        self.assertEqual(len(hits), 1, hits)

    def test_all_247_census_suppresses(self):
        r = run("--audit", fx("niagara5-block9002.md"))
        self.assertFalse(any("9002.2" in h or ":10:" in h for h in lines_for(r.stdout, "R2")))

    def test_config_key_absence_is_not_a_jar_class_census_claim(self):
        # "absent" describing one config property's value is a different claim shape than "this
        # jar/class doesn't exist in the install" -- must not fire R2.
        r = run("--audit", fx("niagara5-block9002.md"))
        self.assertEqual(len(lines_for(r.stdout, "R2")), 1)


class TestR3EphemeralEvidence(unittest.TestCase):
    def test_only_tmp_path_fires_others_dont(self):
        r = run("--audit", fx("niagara5-block9003.md"))
        hits = lines_for(r.stdout, "R3")
        self.assertEqual(len(hits), 1, hits)
        self.assertIn(":7:", hits[0])


class TestR4ChildGapHygiene(unittest.TestCase):
    def test_missing_coverage_check_and_missing_measured_by(self):
        r = run("--audit", fx("niagara5-block9004.md"))
        hits = lines_for(r.stdout, "R4")
        self.assertEqual(len(hits), 2, hits)


class TestR5Dispatch(unittest.TestCase):
    def test_fail_open_without_dispatch_fires(self):
        r = run("--audit", fx("niagara5-block9005.md"))
        hits = lines_for(r.stdout, "R5")
        self.assertEqual(len(hits), 1, hits)

    def test_fail_open_with_dispatch_suppressed(self):
        r = run("--audit", fx("niagara5-block9005.md"))
        self.assertFalse(any("9005.2" in h for h in lines_for(r.stdout, "R5")))

    def test_bypass_without_permission_context_does_not_fire(self):
        # "bypasses" is common in ordinary build/CI prose; only a permission/security-shaped
        # consequence is R5's target.
        r = run("--audit", fx("niagara5-block9005.md"))
        self.assertEqual(len(lines_for(r.stdout, "R5")), 1)


class TestR6ProseVsRaw(unittest.TestCase):
    def test_no_raw_path_fires(self):
        r = run("--audit", fx("niagara5-block9006.md"))
        hits = lines_for(r.stdout, "R6")
        self.assertEqual(len(hits), 1, hits)

    def test_raw_path_cited_suppresses(self):
        r = run("--audit", fx("niagara5-block9006.md"))
        self.assertFalse(any("9006.2" in h for h in lines_for(r.stdout, "R6")))


class TestR7ConstantInlining(unittest.TestCase):
    def test_shadow_literal_claim_without_evidence_fires(self):
        r = run("--audit", fx("niagara5-block9007.md"))
        hits = lines_for(r.stdout, "R7")
        self.assertEqual(len(hits), 1, hits)

    def test_inline_word_alone_is_not_mistaken_for_evidence(self):
        # the positive paragraph itself says "an inline literal duplicate" -- that must NOT
        # be read as the "inlin" evidence token, or the real B96 positive would go dark.
        r = run("--audit", fx("niagara5-block9007.md"))
        hits = lines_for(r.stdout, "R7")
        self.assertTrue(any("9007" in h for h in hits))

    def test_compile_time_constant_evidence_suppresses(self):
        r = run("--audit", fx("niagara5-block9007.md"))
        self.assertFalse(any(":11:" in h for h in lines_for(r.stdout, "R7")))


class TestR8BaselineAttribution(unittest.TestCase):
    def test_n5_only_without_415_fires(self):
        r = run("--audit", fx("niagara5-block9008.md"))
        hits = lines_for(r.stdout, "R8")
        self.assertEqual(len(hits), 1, hits)

    def test_with_415_baseline_check_suppresses(self):
        r = run("--audit", fx("niagara5-block9008.md"))
        self.assertFalse(any("9008.2" in h for h in lines_for(r.stdout, "R8")))


class TestWaivers(unittest.TestCase):
    def test_nonempty_reason_suppresses_and_raises_no_r0(self):
        r = run("--audit", fx("niagara5-block9009.md"))
        self.assertEqual(lines_for(r.stdout, "R1"), [])
        self.assertEqual(lines_for(r.stdout, "R0"), [])

    def test_empty_reason_is_itself_an_r0_finding_and_still_suppresses_r1(self):
        r = run("--audit", fx("niagara5-block9010.md"))
        self.assertEqual(lines_for(r.stdout, "R1"), [])
        self.assertEqual(len(lines_for(r.stdout, "R0")), 1)


class TestCli(unittest.TestCase):
    def test_audit_prints_per_rule_summary(self):
        r = run("--audit", fx("niagara5-block9001.md"), fx("niagara5-block9002.md"))
        self.assertEqual(r.returncode, 0)
        summary = r.stdout.splitlines()[-1]
        self.assertIn("R1=", summary)
        self.assertIn("R2=", summary)

    def test_enforced_min_block_boundary(self):
        # block9001 has number 9001; with --min-block 9001 it IS enforced (>=).
        r = run("--min-block", "9001", fx("niagara5-block9001.md"))
        self.assertEqual(r.returncode, 1)
        # with --min-block 9002 it is NOT enforced (9001 < 9002).
        r2 = run("--min-block", "9002", fx("niagara5-block9001.md"))
        self.assertEqual(r2.returncode, 0)

    def test_usage_error_on_missing_file(self):
        r = run(fx("niagara5-block0000-does-not-exist.md"))
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
