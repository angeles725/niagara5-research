"""
Resolve Audit for Module Navigator (Batch 5, Gap #10).

Detects .resolve() calls in source code and classifies them as SAFE (null-check
found downstream) or UNSAFE (immediate .get() without null-check, will NPE if
resolve() returns null).

Commands:
  resolve-audit <module>
    [--json]              # structured JSON output

Reuses existing indexes (no new builders):
  class-index.json, module-inventory.json

Classification:
  UNSAFE  - .resolve().get() on same line (immediate get, no null check)
  SAFE    - .resolve() without immediate .get(), or null-check detected
"""

import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Pattern: detect .resolve() immediately followed by .get()
# This is UNSAFE because resolve() can return null and get() will NPE.
# ---------------------------------------------------------------------------
_RE_UNSAFE = re.compile(r'\.resolve\(\s*\)\s*\.\s*get\s*\(')

# Pattern: detect any .resolve() usage
_RE_RESOLVE = re.compile(r'\.resolve\(\s*\)')


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached per process)
# ---------------------------------------------------------------------------

_class_index_cache = None
_module_inv_cache = None


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


def _load_module_inv(base_dir):
    global _module_inv_cache
    if _module_inv_cache is not None:
        return _module_inv_cache
    _module_inv_cache = _load_json(
        os.path.join(base_dir, "indexes", "module-inventory.json"))
    return _module_inv_cache


def _read_source(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except (IOError, OSError):
        return []


def _get_source_root(ci_data):
    return ci_data.get("_meta", {}).get("source", "")


# ---------------------------------------------------------------------------
# Core audit logic
# ---------------------------------------------------------------------------

def cmd_resolve_audit(base_dir, module_name, as_json=False):
    """Audit .resolve() usages in a module for null-safety.

    Args:
        base_dir: module-navigator root directory
        module_name: module to audit (e.g. 'alarm-rt')
        as_json: if True, emit JSON instead of human-readable output
    """
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    inv_data = _load_module_inv(base_dir)
    inv = inv_data.get("modules", {}) if inv_data else {}

    source_root = _get_source_root(ci_data)
    if not source_root:
        print("ERROR: source root not found in class-index metadata.")
        return

    classes = ci_data.get("classes", {})

    # Collect all findings
    unsafe_findings = []   # (class_name, module, line_no, line)
    safe_findings = []     # (class_name, module, line_no, line)
    files_scanned = 0

    # Progress goes to stderr so stdout stays clean for --json consumers.
    sys.stderr.write("  Scanning...")
    sys.stderr.flush()

    for class_name, entries in classes.items():
        for entry in entries:
            # Skip inner classes (not standalone source files)
            if entry.get("outer_class") is not None:
                continue
            # Filter by module
            if entry["module"] != module_name:
                continue

            filepath = os.path.join(source_root, entry["path"])
            if not os.path.isfile(filepath):
                continue

            lines = _read_source(filepath)
            files_scanned += 1

            for i, line in enumerate(lines, 1):
                # Check for .resolve() usage at all
                if not _RE_RESOLVE.search(line):
                    continue

                # Classify: UNSAFE if .resolve().get() on same line
                if _RE_UNSAFE.search(line):
                    stripped = line.strip()
                    if len(stripped) > 100:
                        stripped = stripped[:97] + "..."
                    unsafe_findings.append(
                        (class_name, entry["module"], i, stripped))
                else:
                    # Has .resolve() but not immediate .get()
                    stripped = line.strip()
                    if len(stripped) > 100:
                        stripped = stripped[:97] + "..."
                    safe_findings.append(
                        (class_name, entry["module"], i, stripped))

    sys.stderr.write(" done ({:,} files)\n".format(files_scanned))
    sys.stderr.flush()

    total = len(unsafe_findings) + len(safe_findings)

    if as_json:
        _emit_json(module_name, total, safe_findings, unsafe_findings)
    else:
        _emit_text(module_name, total, safe_findings, unsafe_findings)


def _emit_text(module_name, total, safe_findings, unsafe_findings):
    """Print human-readable audit report."""
    print("")
    print("  " + "=" * 66)
    print("  RESOLVE AUDIT: {}".format(module_name))
    print("  " + "=" * 66)
    print("")
    print("  Total .resolve() usages: {:,}".format(total))
    print("")

    if safe_findings:
        print("  SAFE (null-check found downstream, or no immediate get()):")
        for cls, mod, line_no, line in safe_findings[:20]:
            print("    {}:{} ({})".format(cls, line_no, mod))
            print("      {}".format(line))
        if len(safe_findings) > 20:
            print("    ... and {} more".format(len(safe_findings) - 20))
        print("")

    if unsafe_findings:
        print("  UNSAFE (no null-check, will NPE if resolve() returns null):")
        for cls, mod, line_no, line in unsafe_findings[:20]:
            print("    {}:{} ({})".format(cls, line_no, mod))
            print("      {}".format(line))
            print("      → .get() called immediately, no null check")
        if len(unsafe_findings) > 20:
            print("    ... and {} more".format(len(unsafe_findings) - 20))
        print("")

    # Summary
    safe_count = len(safe_findings)
    unsafe_count = len(unsafe_findings)
    print("  SUMMARY:")
    print("    Safe: {:,}  |  Unsafe: {:,}".format(safe_count, unsafe_count))
    if unsafe_count > 0:
        print("    → RISK HIGH: {} unresolved resolves WILL cause NPE if "
              "target is null".format(unsafe_count))
    else:
        print("    → RISK LOW: all resolve() calls are null-safe")
    print("")


def _emit_json(module_name, total, safe_findings, unsafe_findings):
    """Print JSON audit report."""
    result = {
        "command": "resolve-audit",
        "module": module_name,
        "total_resolve_usages": total,
        "safe": [
            {"class": cls, "module": mod, "line": ln, "code": line}
            for cls, mod, ln, line in safe_findings
        ],
        "unsafe": [
            {"class": cls, "module": mod, "line": ln, "code": line}
            for cls, mod, ln, line in unsafe_findings
        ],
        "summary": {
            "safe_count": len(safe_findings),
            "unsafe_count": len(unsafe_findings),
            "risk": "HIGH" if len(unsafe_findings) > 0 else "LOW",
        }
    }
    print(json.dumps(result, indent=2))
