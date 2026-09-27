#!/usr/bin/env python
"""
Build exceptions index from decompiled Java sources.

Reads class-index.json as a catalog of all top-level .java files,
parses `throws` declarations from method signatures and `catch` blocks
from method bodies, and produces indexes/exceptions-index.json with:

  thrown:          { "IOException": [{"class":"AlarmDbConnection","module":"alarm-rt","method":"append","line":77}, ...] }
  caught:          { "IOException": [{"class":"BAlarmService","module":"alarm-rt","line":340}, ...] }
  class_throws:    { "BAlarmService": [{"method":"getAlarmDb","line":412,"exceptions":["AlarmException"]}, ...] }
  class_catches:   { "BAlarmService": [{"line":187,"exceptions":["Exception"]}, ...] }

Usage:
  python tools/build_exceptions_index.py [--base-dir DIR]
"""

import json
import os
import re
import sys
import time


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Match throws clause: ) throws ExType1, ExType2 {  or  ) throws ExType;
RE_THROWS = re.compile(
    r'\)\s*throws\s+([\w.]+(?:\s*,\s*[\w.]+)*)\s*[{;]'
)

# Match catch block: catch (ExType1 | ExType2 varName)  or  catch (ExType varName)
RE_CATCH = re.compile(
    r'catch\s*\(\s*([\w.|  ]+?)\s+\w+\s*\)'
)

# Match method declaration (simplified): modifiers returnType methodName(
RE_METHOD_DECL = re.compile(
    r'(?:(?:public|private|protected|static|abstract|final|synchronized|native|strictfp|default)\s+)*'
    r'(?:[\w<>\[\].,? ]+\s+)?'
    r'(\w+)\s*\('
)

# Match class/interface/enum declaration
RE_CLASS_DECL = re.compile(
    r'\b(?:class|interface|enum)\s+(\w+)'
)

NOT_METHOD_NAMES = frozenset([
    'if', 'else', 'while', 'for', 'do', 'switch', 'try', 'catch', 'finally',
    'return', 'throw', 'new', 'super', 'this', 'case', 'import', 'package',
    'class', 'interface', 'enum', 'assert', 'break', 'continue', 'goto',
    'instanceof', 'var', 'record', 'sealed', 'permits', 'yield', 'null',
    'true', 'false', 'void',
])


# ---------------------------------------------------------------------------
# Single-file parser
# ---------------------------------------------------------------------------

def parse_exceptions(filepath, class_name, module_name):
    """Parse a single .java file for throws declarations and catch blocks.

    Returns:
      throws_list: [{"method": str, "line": int, "exceptions": [str]}]
      catches_list: [{"line": int, "exceptions": [str]}]
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return [], []

    lines = content.split('\n')
    throws_list = []
    catches_list = []

    # We accumulate multi-line method signatures
    accum = ""
    accum_start_line = 0
    in_accum = False

    # Track current method for context (simple heuristic)
    current_method = None
    brace_depth = 0

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
            if in_accum:
                accum += " " + stripped
            continue

        # Track brace depth for method context
        for ch in stripped:
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1

        # --- Detect throws in method declarations ---
        # Check if line has a method-like pattern with throws
        if 'throws' in stripped:
            # Try single-line match first
            test_line = stripped
            if in_accum:
                test_line = accum + " " + stripped
                in_accum = False

            m = RE_THROWS.search(test_line)
            if m:
                exceptions_str = m.group(1)
                exceptions = [e.strip().split('.')[-1] for e in exceptions_str.split(',')]
                exceptions = [e for e in exceptions if e]

                # Find the method name
                method_name = _find_method_name(test_line)
                if method_name and method_name not in NOT_METHOD_NAMES:
                    throws_list.append({
                        "method": method_name,
                        "line": accum_start_line if accum_start_line else line_num,
                        "exceptions": exceptions,
                    })
                accum = ""
                accum_start_line = 0
                continue

        # Accumulate multi-line signatures (line has '(' but no '{' or ';')
        if '(' in stripped and ')' not in stripped and '{' not in stripped and ';' not in stripped:
            if not stripped.startswith('//') and not stripped.startswith('*'):
                # Could be start of multi-line method signature
                possible_method = _find_method_name(stripped)
                if possible_method and possible_method not in NOT_METHOD_NAMES:
                    accum = stripped
                    accum_start_line = line_num
                    in_accum = True
                    continue

        if in_accum:
            accum += " " + stripped
            # Check if accumulation is complete (has closing paren)
            if ')' in stripped:
                # Check for throws in accumulated line
                m = RE_THROWS.search(accum)
                if m:
                    exceptions_str = m.group(1)
                    exceptions = [e.strip().split('.')[-1] for e in exceptions_str.split(',')]
                    exceptions = [e for e in exceptions if e]

                    method_name = _find_method_name(accum)
                    if method_name and method_name not in NOT_METHOD_NAMES:
                        throws_list.append({
                            "method": method_name,
                            "line": accum_start_line,
                            "exceptions": exceptions,
                        })

                in_accum = False
                accum = ""
                accum_start_line = 0

        # --- Detect catch blocks ---
        if 'catch' in stripped:
            m = RE_CATCH.search(stripped)
            if m:
                catch_content = m.group(1).strip()
                # Handle multi-catch: ExType1 | ExType2
                if '|' in catch_content:
                    exceptions = [e.strip().split('.')[-1] for e in catch_content.split('|')]
                else:
                    exceptions = [catch_content.strip().split('.')[-1]]
                exceptions = [e for e in exceptions if e and e[0].isupper()]

                if exceptions:
                    catches_list.append({
                        "line": line_num,
                        "exceptions": exceptions,
                    })

    return throws_list, catches_list


def _find_method_name(line):
    """Extract method name from a line that looks like a method declaration."""
    # Find the first '(' and look for the identifier before it
    paren_idx = line.find('(')
    if paren_idx < 0:
        return None

    before = line[:paren_idx].rstrip()
    # Walk backwards to find the method name
    j = len(before) - 1
    while j >= 0 and (before[j].isalnum() or before[j] == '_'):
        j -= 1

    if j >= len(before) - 1:
        return None

    name = before[j + 1:]
    if not name or not (name[0].isalpha() or name[0] == '_'):
        return None

    return name


# ---------------------------------------------------------------------------
# Build index
# ---------------------------------------------------------------------------

def build_index(base_dir):
    """Build exceptions index from all decompiled sources."""
    # Load class-index for file catalog
    ci_path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(ci_path):
        print("ERROR: class-index.json not found. Run build_class_index.py first.")
        sys.exit(1)

    print("Loading class-index.json...")
    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = json.load(f)

    classes = ci_data.get("classes", {})
    source_root = ci_data.get("_meta", {}).get("source", "")

    if not source_root or not os.path.isdir(source_root):
        print("ERROR: Source root '{}' not found.".format(source_root))
        print("Check class-index.json _meta.source")
        sys.exit(1)

    # Gather all top-level files
    files_to_scan = []
    for class_name, entries in classes.items():
        for entry in entries:
            if entry.get("inner") or entry.get("outer_class") not in (None, "None", ""):
                continue
            rel_path = entry.get("path", "")
            module = entry.get("module", "")
            if rel_path:
                filepath = os.path.join(source_root, rel_path)
                if os.path.isfile(filepath):
                    files_to_scan.append((filepath, class_name, module))

    print("Scanning {} files for exceptions...".format(len(files_to_scan)))

    # Result maps
    thrown_map = {}        # exception_type -> [{class, module, method, line}]
    caught_map = {}        # exception_type -> [{class, module, line}]
    class_throws_map = {}  # class_name -> [{method, line, exceptions}]
    class_catches_map = {} # class_name -> [{line, exceptions}]

    total_throws = 0
    total_catches = 0
    classes_with_throws = 0
    classes_with_catches = 0

    start_time = time.time()
    report_interval = 5000

    for idx, (filepath, class_name, module) in enumerate(files_to_scan):
        if (idx + 1) % report_interval == 0:
            elapsed = time.time() - start_time
            print("  {} / {} files ({:.0f}s)...".format(
                idx + 1, len(files_to_scan), elapsed))

        throws_list, catches_list = parse_exceptions(filepath, class_name, module)

        if throws_list:
            classes_with_throws += 1
            class_throws_map[class_name] = {
                "module": module,
                "throws": throws_list,
            }

            for t in throws_list:
                total_throws += 1
                for exc in t["exceptions"]:
                    if exc not in thrown_map:
                        thrown_map[exc] = []
                    thrown_map[exc].append({
                        "class": class_name,
                        "module": module,
                        "method": t["method"],
                        "line": t["line"],
                    })

        if catches_list:
            classes_with_catches += 1
            class_catches_map[class_name] = {
                "module": module,
                "catches": catches_list,
            }

            for c in catches_list:
                total_catches += 1
                for exc in c["exceptions"]:
                    if exc not in caught_map:
                        caught_map[exc] = []
                    caught_map[exc].append({
                        "class": class_name,
                        "module": module,
                        "line": c["line"],
                    })

    elapsed = time.time() - start_time

    # Build final index
    index = {
        "_meta": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "build_time_sec": round(elapsed, 1),
            "files_scanned": len(files_to_scan),
            "total_throws_declarations": total_throws,
            "total_catch_blocks": total_catches,
            "unique_thrown_types": len(thrown_map),
            "unique_caught_types": len(caught_map),
            "classes_with_throws": classes_with_throws,
            "classes_with_catches": classes_with_catches,
        },
        "thrown": thrown_map,
        "caught": caught_map,
        "class_throws": class_throws_map,
        "class_catches": class_catches_map,
    }

    # Write index
    out_path = os.path.join(base_dir, "indexes", "exceptions-index.json")
    print("Writing {}...".format(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, separators=(',', ':'))

    size_mb = os.path.getsize(out_path) / (1024 * 1024)

    print("")
    print("=" * 60)
    print("EXCEPTIONS INDEX BUILT")
    print("=" * 60)
    print("")
    print("  Files scanned:          {:>7,}".format(len(files_to_scan)))
    print("  Throws declarations:    {:>7,}".format(total_throws))
    print("  Catch blocks:           {:>7,}".format(total_catches))
    print("  Unique thrown types:    {:>7,}".format(len(thrown_map)))
    print("  Unique caught types:    {:>7,}".format(len(caught_map)))
    print("  Classes with throws:    {:>7,}".format(classes_with_throws))
    print("  Classes with catches:   {:>7,}".format(classes_with_catches))
    print("  Build time:             {:>7.1f}s".format(elapsed))
    print("  Index size:             {:>7.1f} MB".format(size_mb))
    print("")

    # Top thrown exceptions
    top_thrown = sorted(thrown_map.items(), key=lambda x: len(x[1]), reverse=True)[:15]
    print("  Top thrown exceptions:")
    for exc, entries in top_thrown:
        modules = len(set(e["module"] for e in entries))
        print("    {:35s} {:>5,} declarations in {:>3} modules".format(
            exc, len(entries), modules))
    print("")

    # Top caught exceptions
    top_caught = sorted(caught_map.items(), key=lambda x: len(x[1]), reverse=True)[:15]
    print("  Top caught exceptions:")
    for exc, entries in top_caught:
        modules = len(set(e["module"] for e in entries))
        print("    {:35s} {:>5,} catch blocks in {:>3} modules".format(
            exc, len(entries), modules))
    print("")

    return index


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Build exceptions index from decompiled Java sources")
    parser.add_argument(
        "--base-dir", "-d",
        help="Base directory (auto-detected if omitted)")
    args = parser.parse_args()

    base_dir = args.base_dir
    if not base_dir:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)

    if not os.path.isdir(os.path.join(base_dir, "indexes")):
        print("ERROR: indexes/ not found in {}".format(base_dir))
        sys.exit(1)

    build_index(base_dir)


if __name__ == "__main__":
    main()
