"""
Driver Cleanup Audit for Module Navigator (Batch 5, Gap #12).

Detects drivers (BDevice/BDeviceNetwork/BDeviceFolder descendants) whose
doStop() method does not properly clean up hardware resources.

Commands:
  driver-cleanup-audit <module> [--json]

Uses inheritance.json parent_to_children to find ALL BDevice/BDeviceNetwork/
BDeviceFolder descendants, then reads source files to find doStop() method
bodies and classifies cleanup level.

NOTE: method-index.json has very few doStop entries. This tool reads source
files directly instead of relying on the method index.
"""

import json
import os
import re
import sys

# Cleanup keywords that indicate real hardware cleanup
CLEANUP_KEYWORDS = [
    'close', 'disconnect', 'unsubscribe', 'release',
    'shutdown', 'stopComm', 'stopHeartbeat', 'cleanup',
    'destroy', 'stop', 'remove', 'clear'
]

# Pattern: detect doStop method signature (Java source or bytecode-decompiled)
# Handles both "void doStop()" and "doStop ()V" bytecode signature style
DO_STOP_SIGNATURE_RE = re.compile(
    r'^\s*(public\s+)?void\s+doStop\s*\(\s*\)\s*([V\(\)]|$)',
    re.MULTILINE
)
DO_STOP_BYTECODE_RE = re.compile(
    r'^\s*doStop\s+\(\)V',
    re.MULTILINE
)


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached per process)
# ---------------------------------------------------------------------------

_class_index_cache = None
_inheritance_cache = None


def _load_json(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print("  ERROR loading {}: {}".format(os.path.basename(path), exc))
        return None


def _load_class_index(base_dir):
    global _class_index_cache
    if _class_index_cache is not None:
        return _class_index_cache
    _class_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "class-index.json"))
    return _class_index_cache


def _load_inheritance(base_dir):
    global _inheritance_cache
    if _inheritance_cache is not None:
        return _inheritance_cache
    _inheritance_cache = _load_json(
        os.path.join(base_dir, "indexes", "inheritance.json"))
    return _inheritance_cache


def _get_driver_descendants(inh):
    """Return set of all BDevice/BDeviceNetwork/BDeviceFolder descendants."""
    parent_to_children = inh.get("parent_to_children", {})
    drivers = set()

    def collect(root):
        stack = [root]
        while stack:
            c = stack.pop()
            if c in parent_to_children:
                for ch in parent_to_children[c]:
                    drivers.add(ch)
                    stack.append(ch)

    for root in ("BDevice", "BDeviceNetwork", "BDeviceFolder"):
        collect(root)
        drivers.add(root)

    return drivers


def _get_source_root(ci_data):
    return ci_data.get("_meta", {}).get("source", "")


def _read_source(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (IOError, OSError):
        return None


def _extract_dostop_body(content, class_name):
    """Extract doStop method body from source content.

    Returns (method_body_str, is_bytecoded) where:
      - method_body_str: the text inside the method (between braces), or
        bytecode comment block if decompiled, or empty string if not found
      - is_bytecoded: True if the body is all bytecode comments (decompiled)
    """
    if not content:
        return "", False

    # Try Java-style signature: "void doStop()"
    m = DO_STOP_SIGNATURE_RE.search(content)
    if m:
        brace_start = content.find('{', m.start())
        if brace_start == -1:
            return "", False
        depth = 0
        body_end = brace_start
        for i in range(brace_start, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    body_end = i
                    break
        body = content[brace_start + 1:body_end]
        return body, False

    # Try bytecode-style: "doStop ()V" (decompiled bytecode signature)
    m = DO_STOP_BYTECODE_RE.search(content)
    if m:
        # Collect the bytecode block after this line
        # Find the end of the bytecode block (next method or class end)
        lines = content.split('\n')
        body_lines = []
        in_block = False
        brace_depth = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if m.start() <= content.find(line):
                in_block = True
            if in_block:
                body_lines.append(line)
                # Track brace depth in the actual code
                for ch in stripped:
                    if ch == '{':
                        brace_depth += 1
                    elif ch == '}':
                        brace_depth -= 1
                # End when we close the method block and hit next method/class
                if brace_depth == 0 and len(body_lines) > 5:
                    break
        body = '\n'.join(body_lines)
        return body, True

    return "", False


def _classify_cleanup(method_body, is_bytecoded=False):
    """Classify doStop cleanup level based on method body content.

    Args:
        method_body: The text inside the doStop method (or bytecode block)
        is_bytecoded: True if the body is decompiled bytecode (not source)

    Returns:
        ("FULL"|"PARTIAL"|"NONE", keyword_count)
    """
    if not method_body or not method_body.strip():
        return "NONE", 0

    body_lower = method_body.lower()

    # Count cleanup keyword occurrences
    count = sum(1 for kw in CLEANUP_KEYWORDS if kw in body_lower)

    if count == 0:
        return "NONE", 0
    elif count <= 2:
        return "PARTIAL", count
    else:
        return "FULL", count


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_driver_cleanup_audit(base_dir, module_name, as_json=False):
    """Audit driver doStop() cleanup in a module.

    Args:
        base_dir: module-navigator root directory
        module_name: module to audit (e.g. 'bacnet-rt')
        as_json: if True, emit JSON instead of human-readable output
    """
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    inh = _load_inheritance(base_dir)
    if not inh:
        print("ERROR: inheritance.json not found.")
        return

    source_root = _get_source_root(ci_data)
    if not source_root:
        print("ERROR: source root not found in class-index metadata.")
        return

    # Get all driver class names
    driver_classes = _get_driver_descendants(inh)

    classes = ci_data.get("classes", {})

    # Collect findings per driver class
    full_cleanup = []    # (class_name, module, body_snippet)
    partial_cleanup = [] # (class_name, module, body_snippet)
    none_cleanup = []    # (class_name, module, body_snippet)
    no_override = []     # (class_name, module) - no doStop found
    skipped = []         # (class_name, module, reason)

    # Progress goes to stderr so stdout stays clean for --json consumers.
    sys.stderr.write("  Scanning...")
    sys.stderr.flush()

    scanned = 0

    for class_name in driver_classes:
        if class_name not in classes:
            continue

        # Find the entry for this module (outer_class=None, non-inner)
        entry = None
        for e in classes[class_name]:
            if e.get("module") == module_name and not e.get("outer_class"):
                entry = e
                break

        if entry is None:
            continue

        filepath = os.path.join(source_root, entry["path"])
        content = _read_source(filepath)
        if content is None:
            skipped.append((class_name, module_name, "source file not found"))
            continue

        scanned += 1

        # Check if the source actually has doStop
        if 'doStop' not in content:
            no_override.append((class_name, module_name))
            continue

        # Extract doStop method body
        body, is_bytecoded = _extract_dostop_body(content, class_name)

        if not body:
            no_override.append((class_name, module_name))
            continue

        # Classify
        level, kw_count = _classify_cleanup(body, is_bytecoded)

        # Truncate body for storage
        snippet = body.strip()[:200]

        if level == "FULL":
            full_cleanup.append((class_name, module_name, snippet, kw_count))
        elif level == "PARTIAL":
            partial_cleanup.append((class_name, module_name, snippet, kw_count))
        else:
            none_cleanup.append((class_name, module_name, snippet, kw_count))

    sys.stderr.write(" done ({} driver source files scanned)\n".format(scanned))
    sys.stderr.flush()

    if as_json:
        _emit_json(module_name, scanned, full_cleanup, partial_cleanup,
                   none_cleanup, no_override, skipped)
    else:
        _emit_text(module_name, scanned, full_cleanup, partial_cleanup,
                   none_cleanup, no_override, skipped)


def _emit_text(module_name, scanned, full_cleanup, partial_cleanup,
               none_cleanup, no_override, skipped):
    """Print human-readable audit report."""
    print("")
    print("  " + "=" * 66)
    print("  DRIVER CLEANUP AUDIT: {}".format(module_name))
    print("  " + "=" * 66)
    print("")
    print("  Total driver classes found: {:>6,}".format(
        scanned + len(no_override)))
    print("  Source files scanned:       {:>6,}".format(scanned))
    print("")

    # WITH FULL CLEANUP
    if full_cleanup:
        print("  WITH FULL CLEANUP (3+ cleanup keywords):")
        for cls, mod, snippet, kw_count in sorted(full_cleanup):
            label = _cleanup_label(snippet)
            print("    {}.doStop()  → {}".format(cls, label))
        print("")

    # WITH PARTIAL CLEANUP
    if partial_cleanup:
        print("  PARTIAL CLEANUP (1-2 cleanup keywords):")
        for cls, mod, snippet, kw_count in sorted(partial_cleanup):
            label = _cleanup_label(snippet)
            print("    {}.doStop()  → {} ({})".format(cls, label, kw_count))
        print("")

    # WITHOUT CLEANUP (no-op doStop)
    if none_cleanup:
        print("  WITHOUT CLEANUP (doStop is no-op):")
        for cls, mod, snippet, kw_count in sorted(none_cleanup):
            print("    {}.doStop()  → no cleanup, device left inconsistent".format(cls))
        if len(none_cleanup) > 20:
            print("    ... and {} more".format(len(none_cleanup) - 20))
        print("")

    # NO DOSTOP OVERRIDE
    if no_override:
        print("  NO DOSTOP OVERRIDE (inherits no-op from parent):")
        for cls, mod in sorted(no_override)[:20]:
            print("    {}  → no doStop override".format(cls))
        if len(no_override) > 20:
            print("    ... and {} more".format(len(no_override) - 20))
        print("")

    # SKIPPED
    if skipped:
        print("  SKIPPED (source not accessible):")
        for cls, mod, reason in sorted(skipped)[:5]:
            print("    {}  → {}".format(cls, reason))
        if len(skipped) > 5:
            print("    ... and {} more".format(len(skipped) - 5))
        print("")

    # Summary
    print("  SUMMARY:")
    total = len(full_cleanup) + len(partial_cleanup) + len(none_cleanup)
    print("    Full cleanup:  {:>3}  |  Partial: {:>3}  |  No cleanup: {:>3}".format(
        len(full_cleanup), len(partial_cleanup), len(none_cleanup)))
    print("    No doStop override: {:>3}".format(len(no_override)))
    if len(none_cleanup) > 0:
        print("    → RISK: {} drivers will leave hardware in inconsistent state "
              "on station restart".format(len(none_cleanup)))
    elif len(no_override) > 0:
        print("    → RISK: {} drivers inherit no-op doStop from parent "
              "(no explicit cleanup)".format(len(no_override)))
    else:
        print("    → RISK LOW: all drivers with doStop override have cleanup")
    print("")


def _cleanup_label(snippet):
    """Generate a short human-readable label for what cleanup is done."""
    snippet_lower = snippet.lower()
    actions = []
    for kw in ['close', 'disconnect', 'unsubscribe', 'release', 'shutdown',
               'stopComm', 'stopHeartbeat', 'cleanup', 'destroy', 'remove']:
        if kw in snippet_lower:
            actions.append(kw)
    if len(actions) >= 3:
        return "proper cleanup: " + ", ".join(actions[:3]) + "..."
    elif actions:
        return "partial cleanup: " + ", ".join(actions)
    return "minimal cleanup"


def _emit_json(module_name, scanned, full_cleanup, partial_cleanup,
               none_cleanup, no_override, skipped):
    """Print JSON audit report."""
    result = {
        "command": "driver-cleanup-audit",
        "module": module_name,
        "scanned": scanned,
        "total_driver_classes": scanned + len(no_override),
        "full_cleanup": [
            {"class": cls, "module": mod,
             "snippet": snippet[:200], "kw_count": kw_count}
            for cls, mod, snippet, kw_count in full_cleanup
        ],
        "partial_cleanup": [
            {"class": cls, "module": mod,
             "snippet": snippet[:200], "kw_count": kw_count}
            for cls, mod, snippet, kw_count in partial_cleanup
        ],
        "no_cleanup": [
            {"class": cls, "module": mod,
             "snippet": snippet[:200]}
            for cls, mod, snippet, kw_count in none_cleanup
        ],
        "no_override": [
            {"class": cls, "module": mod}
            for cls, mod in no_override
        ],
        "skipped": [
            {"class": cls, "module": mod, "reason": reason}
            for cls, mod, reason in skipped
        ],
        "summary": {
            "full_cleanup_count": len(full_cleanup),
            "partial_cleanup_count": len(partial_cleanup),
            "no_cleanup_count": len(none_cleanup),
            "no_override_count": len(no_override),
            "skipped_count": len(skipped),
            "risk": (
                "HIGH" if len(none_cleanup) > 0
                else "MEDIUM" if len(no_override) > 0
                else "LOW"
            ),
        }
    }
    print(json.dumps(result, indent=2))
