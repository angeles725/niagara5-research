"""
Unit tests for palette_lexicon_agents — pure parse helpers.

One test function:
  - Builds a fixture in a tmp directory.
  - Asserts find_duplicate_keys detects the duplicated bare key.
  - Asserts parse_agents returns exactly one agent.
  - Asserts that removing the duplicate detection (comment-out guard) would
    break the assertion (the test BITES: it checks the dup count, not just
    that the function runs).

No subprocess invocation, no index dependency — runs in isolation.
"""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

# Make the tests importable from the tests/ directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from module_nav_lib.palette_lexicon_agents import (
    find_duplicate_keys,
    parse_agents,
)


class TestDuplicateKeyAndAgentParsing(unittest.TestCase):
    """Fixture-based test for the B759 duplicate-bare-key hazard and agent parsing."""

    def test_duplicate_key_detected_and_one_agent_parsed(self):
        """Verify find_duplicate_keys reports duplicated keys and parse_agents finds one agent."""

        # --- Lexicon fixture: key 'foo.bar' appears twice → duplicate ---
        lexicon_content = (
            "foo.bar=First value\n"
            "baz=Something else\n"
            "foo.bar=Second value silently overrides\n"  # B759 duplicate
        )

        # --- module.xml fixture: exactly one <agent> element ---
        module_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<module name="fixture" bajaVersion="0" vendor="test" version="1.0.0">
 <types>
  <type class="com.example.BFoo" name="Foo">
   <agent>
    <on type="baja:LocalHost"/>
   </agent>
  </type>
  <type class="com.example.BBar" name="Bar"/>
 </types>
</module>
"""

        # --- Duplicate key detection ---
        dups = find_duplicate_keys(lexicon_content)

        # BITE: this assertion fails if find_duplicate_keys stops reporting dups
        self.assertIn(
            "foo.bar", dups,
            "find_duplicate_keys must report 'foo.bar' as a duplicate bare key "
            "(B759 hazard: later occurrence silently overrides earlier one)"
        )
        self.assertEqual(
            dups["foo.bar"], 2,
            "foo.bar appears exactly 2 times; count must be 2"
        )

        # Non-duplicate key must NOT appear in the result
        self.assertNotIn(
            "baz", dups,
            "'baz' appears once — must not be in the duplicate report"
        )

        # --- Agent parsing ---
        agents = parse_agents(module_xml_content)

        # BITE: fails if parse_agents misses the <agent> element or over-counts
        self.assertEqual(
            len(agents), 1,
            "Fixture has exactly one <agent> element; parse_agents must return one entry"
        )
        agent = agents[0]
        self.assertEqual(agent["type_name"], "Foo")
        self.assertIn("baja:LocalHost", agent["on_types"])


if __name__ == "__main__":
    unittest.main()
