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
        joined = "\n".join(hits)
        # row 1 (plain /tmp path, no line number) fires
        self.assertIn(":7:", joined, hits)
        # rows 2/3 (organized/, evidence/ paths) are durable -> suppressed
        self.assertNotIn(":8:", joined, hits)
        self.assertNotIn(":9:", joined, hits)
        self.assertEqual(len(hits), 3, hits)

    def test_tmp_path_with_trailing_line_number_still_fires(self):
        # Regression for the R3_DURABLE_RE bug — old regex, removed in aaa369d: a /tmp (or /tmp/.../scratchpad/...) path that
        # happens to carry a trailing ":<line>" must never be mistaken for a durable
        # "path:line" citation like "organized/foo/Bar.java:42".
        r = run("--audit", fx("niagara5-block9003.md"))
        hits = lines_for(r.stdout, "R3")
        joined = "\n".join(hits)
        self.assertIn(":11:", joined, hits)  # /tmp/.../F.java:12, no "scratchpad" in the path
        self.assertIn(":12:", joined, hits)  # /tmp/.../scratchpad/F.java:12


class TestR4ChildGapHygiene(unittest.TestCase):
    def test_missing_coverage_check_and_missing_measured_by(self):
        r = run("--audit", fx("niagara5-block9004.md"))
        hits = lines_for(r.stdout, "R4")
        self.assertEqual(len(hits), 2, hits)


class TestR5Dispatch(unittest.TestCase):
    def test_fail_open_without_dispatch_fires(self):
        r = run("--audit", fx("niagara5-block9005.md"))
        hits = lines_for(r.stdout, "R5")
        self.assertIn(":5:", "\n".join(hits), hits)

    def test_fail_open_with_dispatch_suppressed(self):
        # 9005.2 (line 10) is the SAME "fails open"/getPermissions(null) claim as 9005.1, plus a
        # dispatch: clause -- it must not appear among the R5 hits by its real line number.
        r = run("--audit", fx("niagara5-block9005.md"))
        self.assertNotIn(":10:", "\n".join(lines_for(r.stdout, "R5")))

    def test_bypass_without_permission_context_does_not_fire(self):
        # "bypasses" is common in ordinary build/CI prose; only a permission/security-shaped
        # consequence is R5's target. Paired against 9005.4 (line 21), which uses the SAME
        # "bypasses" verb in a genuine permission-consequence shape and DOES fire -- proving
        # 9005.3 not firing is because it lacks permission context, not because "bypasses" is
        # dead wiring in the rule.
        r = run("--audit", fx("niagara5-block9005.md"))
        joined = "\n".join(lines_for(r.stdout, "R5"))
        self.assertIn(":21:", joined)   # 9005.4 -- bypasses + permission context, no dispatch
        self.assertNotIn(":16:", joined)  # 9005.3 -- bypasses, unrelated Gradle wording
        self.assertNotIn(":17:", joined)


class TestR6ProseVsRaw(unittest.TestCase):
    def test_no_raw_path_fires(self):
        r = run("--audit", fx("niagara5-block9006.md"))
        hits = lines_for(r.stdout, "R6")
        self.assertEqual(len(hits), 1, hits)

    def test_raw_path_cited_suppresses(self):
        # 9006.2 (line 10) is the SAME "does not mention" / [Block N] claim as 9006.1, plus a
        # raw `organized/...` path citation -- checked by its real line number, not a heading
        # label that never appears in a finding's quoted excerpt.
        r = run("--audit", fx("niagara5-block9006.md"))
        self.assertNotIn(":10:", "\n".join(lines_for(r.stdout, "R6")))


class TestR7ConstantInlining(unittest.TestCase):
    def test_shadow_literal_claim_without_evidence_fires(self):
        r = run("--audit", fx("niagara5-block9007.md"))
        hits = lines_for(r.stdout, "R7")
        self.assertEqual(len(hits), 1, hits)
        self.assertIn(":5:", hits[0])

    def test_inline_word_alone_is_not_mistaken_for_evidence(self):
        # 9007.1 (line 5) is a paragraph whose ONLY candidate evidence-looking word is "inline"
        # (as in "an inline literal duplicate", the real B96 positive's own phrasing) -- that
        # must NOT be read as the technical "inlin(e/ing/ed)" evidence token, so R7 must still
        # fire on exactly this line.
        r = run("--audit", fx("niagara5-block9007.md"))
        hits = lines_for(r.stdout, "R7")
        self.assertIn(":5:", "\n".join(hits), hits)

    def test_compile_time_constant_evidence_suppresses(self):
        # 9007.2 (line 10) is the SAME shadow-literal claim as 9007.1, plus real bytecode
        # evidence (ldc / JLS 4.12.4) -- checked by its real line number.
        r = run("--audit", fx("niagara5-block9007.md"))
        self.assertNotIn(":10:", "\n".join(lines_for(r.stdout, "R7")))


class TestR8BaselineAttribution(unittest.TestCase):
    def test_n5_only_without_415_fires(self):
        r = run("--audit", fx("niagara5-block9008.md"))
        hits = lines_for(r.stdout, "R8")
        self.assertEqual(len(hits), 1, hits)

    def test_with_415_baseline_check_suppresses(self):
        # 9008.2 (line 9) is the SAME N5-only/module claim shape as 9008.1, plus a real
        # PowerB/4.15 baseline check -- checked by its real line number, not a heading label
        # that never appears in a finding's quoted excerpt.
        r = run("--audit", fx("niagara5-block9008.md"))
        self.assertNotIn(":9:", "\n".join(lines_for(r.stdout, "R8")))


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

    def test_enforced_summary_reports_scanned_enforced_and_findings_separately(self):
        # block9001 (9001) is below --min-block 9002, so it is scanned but NOT enforced (no
        # findings reported for it, even though it has R1 findings in --audit mode); block9002
        # (9002) is enforced and contributes its 1 R2 finding. The old "checked=N" line conflated
        # "files scanned" with "files whose findings actually gate the exit code".
        r = run("--min-block", "9002", fx("niagara5-block9001.md"), fx("niagara5-block9002.md"))
        self.assertEqual(r.returncode, 1)
        summary = r.stdout.splitlines()[-1]
        self.assertEqual(summary, "scanned=2 enforced=1 findings=1")

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
