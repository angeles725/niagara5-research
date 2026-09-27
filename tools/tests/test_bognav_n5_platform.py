"""bog-nav.py against a real N5 artifact: defaults/platform.bog.

Documents the finding from porting bog-nav.py to N5 (tools/README.md has the
full note): platform.bog is the SAME bajaObjectGraph BOG-XML grammar bog-nav.py
already parses for N4 (a bare, non-ZIP file.xml — bog-nav.py already supports
that case). It parses without error. However this particular file's <p>
component nodes carry NO `h=` (handle) attribute — Niagara only assigns
handles when a component is the target of a link, and this is a template
default with no links — while bog-nav.py's Comp indexing requires `h is not
None` to register a node. Net effect: exit 0, zero components indexed, rather
than a crash. This is a real, documented gap (not fixed here — a live N5
station config.bog, once one exists, is expected to carry handles the way N4
station exports do; unverified, since no N5 station has been created yet).

Skipped automatically if the read-only N5 install is not present on this
machine (it lives outside the repo, under /mnt/c).
"""
import os
import subprocess
import sys
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "bog-nav.py")
N5_PLATFORM_BOG = "/mnt/c/Program Files/Niagara/5.0.0.28/defaults/platform.bog"


@unittest.skipUnless(os.path.isfile(N5_PLATFORM_BOG), "N5 install not present on this machine")
class TestBogNavAgainstN5Platform(unittest.TestCase):
    def test_parses_without_crashing(self):
        r = subprocess.run(
            [sys.executable, SCRIPT, N5_PLATFORM_BOG, "types"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_is_bare_xml_not_a_zip(self):
        with open(N5_PLATFORM_BOG, "rb") as fh:
            head = fh.read(16)
        self.assertNotEqual(head[:2], b"PK")  # not a ZIP local-file-header signature
        self.assertTrue(head.startswith(b"<?xml"))

    def test_known_gap_zero_components_without_handle_attrs(self):
        # Pinned as a documented finding, not a silent behavior change: if this
        # ever starts reporting components, the gap note in tools/README.md
        # should be updated (handle-less indexing would have been added).
        r = subprocess.run(
            [sys.executable, SCRIPT, N5_PLATFORM_BOG, "types"],
            capture_output=True, text=True,
        )
        self.assertIn("no components", r.stdout)


if __name__ == "__main__":
    unittest.main()
