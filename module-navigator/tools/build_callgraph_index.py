#!/usr/bin/env python
"""
Build call graph index from decompiled Java sources (Phase 12).

For each method in each class, parses the method body to extract
method invocations. Resolves:
  - ClassName.method()   via import statements
  - this.method()        current class
  - super.method()       parent class (from inheritance index)
  - super()              parent constructor
  - new ClassName()      constructor calls

Does NOT resolve variable.method() (ambiguous without type inference).

Produces indexes/callgraph-index.json with:
  calls: { "Class.method": ["TargetClass.targetMethod", ...] }

The reverse index (called_by) is computed at query time.

Usage:
  python tools/build_callgraph_index.py [--base-dir DIR]
"""

import json
import os
import re
import sys
import time

# Add tools/ dir so we can import build_method_index
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_method_index import parse_methods_from_content


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Receivers to skip (Java stdlib noise)
SKIP_RECEIVERS = frozenset([
    'System', 'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean',
    'Byte', 'Short', 'Character', 'Number', 'Math', 'StrictMath',
    'Arrays', 'Collections', 'Objects', 'Class', 'Thread', 'Runtime',
    'StringBuilder', 'StringBuffer', 'Object', 'Enum', 'Void',
    'Comparable', 'Iterable', 'Iterator', 'Spliterator',
    'Map', 'Set', 'List', 'Queue', 'Deque', 'Collection',
    'HashMap', 'HashSet', 'ArrayList', 'LinkedList', 'TreeMap', 'TreeSet',
    'LinkedHashMap', 'LinkedHashSet', 'ConcurrentHashMap', 'Vector',
    'CopyOnWriteArrayList', 'CopyOnWriteArraySet',
    'Optional', 'Stream', 'Collectors', 'IntStream', 'LongStream',
    'Pattern', 'Matcher',
    'Calendar', 'Date', 'SimpleDateFormat', 'TimeZone', 'Locale',
    'File', 'Path', 'Paths', 'Files',
    'Logger', 'Level', 'LogManager', 'LogRecord',
    'Assert', 'Preconditions',
    'InputStream', 'OutputStream', 'Reader', 'Writer',
    'BufferedReader', 'BufferedWriter', 'InputStreamReader', 'OutputStreamWriter',
    'FileInputStream', 'FileOutputStream', 'ByteArrayInputStream', 'ByteArrayOutputStream',
    'DataInputStream', 'DataOutputStream', 'ObjectInputStream', 'ObjectOutputStream',
    'PrintStream', 'PrintWriter',
    'Socket', 'ServerSocket', 'URL', 'URI', 'HttpURLConnection',
    'Properties', 'ResourceBundle',
    'BigDecimal', 'BigInteger',
    'UUID', 'Random', 'SecureRandom',
    'Throwable', 'Exception', 'RuntimeException', 'Error',
    'IOException', 'IllegalArgumentException', 'IllegalStateException',
    'NullPointerException', 'UnsupportedOperationException',
    'ClassNotFoundException', 'NoSuchMethodException',
    'Field', 'Method', 'Constructor', 'Modifier',
    'Proxy', 'InvocationHandler',
    'Annotation', 'Override', 'Deprecated', 'SuppressWarnings',
])

# Classes to skip for new ClassName() — common Java allocations
SKIP_NEW = frozenset([
    'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Byte', 'Short',
    'Character', 'BigDecimal', 'BigInteger',
    'StringBuilder', 'StringBuffer',
    'ArrayList', 'LinkedList', 'HashMap', 'HashSet', 'TreeMap', 'TreeSet',
    'LinkedHashMap', 'LinkedHashSet', 'ConcurrentHashMap', 'Vector',
    'CopyOnWriteArrayList', 'CopyOnWriteArraySet',
    'Object', 'Exception', 'RuntimeException',
    'IOException', 'IllegalArgumentException', 'IllegalStateException',
    'NullPointerException', 'UnsupportedOperationException',
    'File', 'URL', 'URI',
    'Date', 'Calendar', 'SimpleDateFormat', 'Locale', 'TimeZone',
    'Timer', 'TimerTask',
    'Thread', 'ThreadLocal',
    'Properties', 'Random', 'SecureRandom', 'UUID',
    'ByteArrayInputStream', 'ByteArrayOutputStream',
    'BufferedReader', 'BufferedWriter',
    'InputStreamReader', 'OutputStreamWriter',
    'PrintWriter', 'PrintStream',
    'FileInputStream', 'FileOutputStream',
    'DataInputStream', 'DataOutputStream',
    'ObjectInputStream', 'ObjectOutputStream',
    'StringReader', 'StringWriter',
    'Pattern', 'Matcher',
])

# Regex patterns for call extraction
RE_DOT_CALL = re.compile(r'(\w+)\.(\w+)\s*\(')
RE_THIS_CALL = re.compile(r'\bthis\.(\w+)\s*\(')
RE_SUPER_CALL = re.compile(r'\bsuper\.(\w+)\s*\(')
RE_SUPER_CONSTRUCTOR = re.compile(r'\bsuper\s*\(')
RE_THIS_CONSTRUCTOR = re.compile(r'\bthis\s*\(')
RE_NEW_CALL = re.compile(r'\bnew\s+(\w+)\s*[\(<]')
RE_IMPORT = re.compile(r'^\s*import\s+static\s+([\w.]+)\s*;|^\s*import\s+([\w.]+)\s*;')

# Java keywords that look like method calls
NOT_CALLS = frozenset([
    'if', 'else', 'while', 'for', 'do', 'switch', 'try', 'catch', 'finally',
    'return', 'throw', 'new', 'super', 'this', 'case', 'import', 'package',
    'class', 'interface', 'enum', 'assert', 'break', 'continue', 'goto',
    'instanceof', 'var', 'record', 'sealed', 'permits', 'yield', 'null',
    'true', 'false', 'void', 'synchronized',
])


# ---------------------------------------------------------------------------
# Import parsing
# ---------------------------------------------------------------------------

def parse_imports_from_content(content):
    """Parse import statements. Returns {simple_name: simple_name}."""
    import_map = {}
    for line in content.split('\n'):
        if line.strip().startswith('import '):
            m = RE_IMPORT.match(line)
            if m:
                # Group 1 is static import, group 2 is regular import
                fqn = m.group(1) or m.group(2)
                if fqn and not fqn.endswith('.*'):
                    simple = fqn.rsplit('.', 1)[-1]
                    import_map[simple] = simple
        elif line.strip().startswith('class ') or line.strip().startswith('public '):
            # Past imports section
            break
    return import_map


# ---------------------------------------------------------------------------
# Call extraction from a zone of lines
# ---------------------------------------------------------------------------

def extract_calls_from_zone(lines, current_class, parent_class, import_map):
    """Extract method calls from a list of source lines (a method's zone).

    Returns a set of "ClassName.methodName" strings.
    """
    calls = set()
    in_block_comment = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Handle block comments
        if in_block_comment:
            if '*/' in stripped:
                idx = stripped.find('*/')
                stripped = stripped[idx + 2:]
                in_block_comment = False
            else:
                continue

        # Remove inline block comments
        while '/*' in stripped:
            start = stripped.find('/*')
            end = stripped.find('*/', start + 2)
            if end >= 0:
                stripped = stripped[:start] + ' ' + stripped[end + 2:]
            else:
                stripped = stripped[:start]
                in_block_comment = True
                break

        # Skip line comments
        comment_idx = stripped.find('//')
        if comment_idx >= 0:
            stripped = stripped[:comment_idx]

        if not stripped:
            continue

        # Skip string literals (rough: remove content within quotes)
        # This prevents matching method-like patterns inside strings
        cleaned = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '""', stripped)
        cleaned = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", "''", cleaned)

        # --- this.method( ---
        for m in RE_THIS_CALL.finditer(cleaned):
            method_name = m.group(1)
            if method_name not in NOT_CALLS:
                calls.add("{}.{}".format(current_class, method_name))

        # --- super.method( ---
        for m in RE_SUPER_CALL.finditer(cleaned):
            method_name = m.group(1)
            if method_name not in NOT_CALLS:
                target = parent_class if parent_class else current_class
                calls.add("{}.{}".format(target, method_name))

        # --- super() constructor ---
        if RE_SUPER_CONSTRUCTOR.search(cleaned):
            # Check it's not super.something (already handled above)
            for sm in RE_SUPER_CONSTRUCTOR.finditer(cleaned):
                pos = sm.start()
                before = cleaned[:pos]
                if not before.rstrip().endswith('.'):
                    target = parent_class if parent_class else current_class
                    calls.add("{}.<init>".format(target))

        # --- this() constructor delegation ---
        if RE_THIS_CONSTRUCTOR.search(cleaned):
            for tm in RE_THIS_CONSTRUCTOR.finditer(cleaned):
                pos = tm.start()
                before = cleaned[:pos]
                if not before.rstrip().endswith('.'):
                    calls.add("{}.<init>".format(current_class))

        # --- new ClassName( ---
        for m in RE_NEW_CALL.finditer(cleaned):
            cname = m.group(1)
            if cname[0].isupper() and cname not in SKIP_NEW and cname not in NOT_CALLS:
                calls.add("{}.<init>".format(cname))

        # --- ClassName.method( ---
        for m in RE_DOT_CALL.finditer(cleaned):
            receiver = m.group(1)
            method_name = m.group(2)

            if receiver in ('this', 'super'):
                continue  # Already handled above
            if method_name in NOT_CALLS:
                continue
            if receiver in SKIP_RECEIVERS:
                continue
            if not receiver[0].isupper():
                continue  # Skip variable.method() — lowercase receiver

            calls.add("{}.{}".format(receiver, method_name))

    return calls


# ---------------------------------------------------------------------------
# Parse calls from a single file
# ---------------------------------------------------------------------------

def parse_calls_from_file(content, file_class_name, parent_map):
    """Parse method calls from a Java file using zone-based method attribution.

    Uses parse_methods_from_content to find method declarations and their line
    numbers, then extracts calls from each method's zone.

    Returns dict: {"ClassName.method": set("TargetClass.targetMethod", ...)}
    """
    lines = content.split('\n')

    # Parse imports
    import_map = parse_imports_from_content(content)

    # Parse method declarations
    methods = parse_methods_from_content(content, file_class_name)
    if not methods:
        return {}

    # Sort by line number
    methods.sort(key=lambda m: m['line'])

    calls = {}

    for idx, m in enumerate(methods):
        indexed_name = m.get('indexed_name')
        if not indexed_name:
            continue

        start = m['line'] - 1  # 0-indexed
        if idx + 1 < len(methods):
            end = methods[idx + 1]['line'] - 1
        else:
            end = len(lines)

        zone = lines[start:end]
        caller_class = m['class']

        # Get parent class for super resolution
        parent_class = parent_map.get(caller_class)

        callees = extract_calls_from_zone(zone, caller_class, parent_class, import_map)

        # Remove self-referencing call (method calling itself is valid but
        # remove exact same key to avoid noise from the declaration line)
        key = "{}.{}".format(caller_class, indexed_name)

        if callees:
            if key in calls:
                calls[key].update(callees)
            else:
                calls[key] = callees

    return calls


# ---------------------------------------------------------------------------
# Builder main
# ---------------------------------------------------------------------------

def detect_base_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(script_dir)
    if os.path.isdir(os.path.join(base, "indexes")):
        return base
    return None


def build_callgraph_index(base_dir):
    ci_path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(ci_path):
        print("ERROR: class-index.json not found at {}".format(ci_path))
        sys.exit(1)

    inv_path = os.path.join(base_dir, "indexes", "module-inventory.json")
    if not os.path.isfile(inv_path):
        print("ERROR: module-inventory.json not found at {}".format(inv_path))
        sys.exit(1)

    inh_path = os.path.join(base_dir, "indexes", "inheritance.json")

    # -------------------------------------------------------------------
    # Load indexes
    # -------------------------------------------------------------------
    t0 = time.time()

    print("Loading class-index.json...")
    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = json.load(f)
    classes = ci_data.get("classes", {})
    source_base = ci_data.get("_meta", {}).get("source", "")
    print("  {} unique class names, source: {}".format(len(classes), source_base))

    # Load inheritance for parent resolution (super.method)
    parent_map = {}  # simple_name -> simple_parent_name
    if os.path.isfile(inh_path):
        print("Loading inheritance.json...")
        with open(inh_path, "r", encoding="utf-8") as f:
            inh_data = json.load(f)
        # class_to_chain: {"BLinkPad": ["BEdgePane", "BWidget", ...]}
        # chain[0] is immediate parent
        for cls, chain in inh_data.get("class_to_chain", {}).items():
            if chain:
                parent_map[cls] = chain[0]
        print("  {} classes with parent mapping".format(len(parent_map)))
    else:
        print("WARNING: inheritance.json not found. super.method() resolution disabled.")

    # -------------------------------------------------------------------
    # Collect top-level files
    # -------------------------------------------------------------------
    print("Collecting top-level files...")
    top_files = []  # (class_name, module, rel_path)
    seen_paths = set()

    for class_name, entries in classes.items():
        for e in entries:
            if e.get("outer_class"):
                continue
            rel_path = e.get("path", "")
            if not rel_path or rel_path in seen_paths:
                continue
            seen_paths.add(rel_path)
            top_files.append((class_name, e.get("module", ""), rel_path))

    print("  {} top-level files to parse".format(len(top_files)))

    # -------------------------------------------------------------------
    # Parse calls from each file
    # -------------------------------------------------------------------
    print("Parsing call graph from {} files...".format(len(top_files)))
    t1 = time.time()

    all_calls = {}  # "Class.method" -> set("Target.method", ...)
    files_parsed = 0
    files_failed = 0
    total_edges = 0
    progress_interval = 5000

    for file_class, module, rel_path in top_files:
        full_path = os.path.join(source_base, rel_path)
        if not os.path.isfile(full_path):
            files_failed += 1
            continue

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            files_failed += 1
            continue

        files_parsed += 1
        if files_parsed % progress_interval == 0:
            elapsed = time.time() - t1
            rate = files_parsed / elapsed if elapsed > 0 else 0
            print("  {:>6,} / {:,} files ({:.0f}/s, {:.0f}s elapsed, {:,} edges so far)...".format(
                files_parsed, len(top_files), rate, elapsed, total_edges))

        file_calls = parse_calls_from_file(content, file_class, parent_map)

        for key, callees in file_calls.items():
            if key in all_calls:
                all_calls[key].update(callees)
            else:
                all_calls[key] = callees
            total_edges += len(callees)

    t2 = time.time()
    parse_time = t2 - t1
    print("  Parsed {} files in {:.1f}s ({:.0f}/s)".format(
        files_parsed, parse_time,
        files_parsed / parse_time if parse_time > 0 else 0))
    print("  Failed to read: {}".format(files_failed))

    # -------------------------------------------------------------------
    # Convert sets to sorted lists
    # -------------------------------------------------------------------
    calls_out = {}
    for key in sorted(all_calls.keys()):
        callees = sorted(all_calls[key])
        if callees:
            calls_out[key] = callees

    # Recount after dedup
    total_callers = len(calls_out)
    total_edges_dedup = sum(len(v) for v in calls_out.values())

    # Compute callee stats (for hotspots preview)
    callee_counts = {}
    for callees in calls_out.values():
        for c in callees:
            callee_counts[c] = callee_counts.get(c, 0) + 1

    total_callees = len(callee_counts)
    top_callees = sorted(callee_counts.items(), key=lambda x: -x[1])[:20]

    # -------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------
    print("")
    print("  Total caller methods:        {:>9,}".format(total_callers))
    print("  Total unique callees:        {:>9,}".format(total_callees))
    print("  Total edges (raw):           {:>9,}".format(total_edges))
    print("  Total edges (dedup):         {:>9,}".format(total_edges_dedup))
    print("  Avg callees per caller:      {:>9.1f}".format(
        total_edges_dedup / max(total_callers, 1)))
    print("")
    print("  Top 20 most-called methods (hotspots):")
    for name, count in top_callees:
        print("    {:50s} {:>6,} callers".format(name, count))

    # -------------------------------------------------------------------
    # Build output
    # -------------------------------------------------------------------
    total_time = time.time() - t0
    meta = {
        "description": "Call graph index for Niagara N4 decompiled modules",
        "source_indexes": ["class-index.json", "inheritance.json"],
        "files_parsed": files_parsed,
        "files_failed": files_failed,
        "total_caller_methods": total_callers,
        "total_unique_callees": total_callees,
        "total_edges": total_edges_dedup,
        "avg_callees_per_caller": round(total_edges_dedup / max(total_callers, 1), 1),
        "build_time_sec": round(total_time, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    output = {
        "_meta": meta,
        "calls": calls_out,
    }

    # Write
    out_path = os.path.join(base_dir, "indexes", "callgraph-index.json")
    print("")
    print("Writing {}...".format(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"), ensure_ascii=False)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print("  Done: {:.1f} MB in {:.1f}s".format(size_mb, total_time))
    print("")

    # Summary
    print("=" * 65)
    print("CALL GRAPH INDEX SUMMARY")
    print("=" * 65)
    print("  Files parsed:                {:>9,}".format(files_parsed))
    print("  Files failed:                {:>9,}".format(files_failed))
    print("  Caller methods:              {:>9,}".format(total_callers))
    print("  Unique callees:              {:>9,}".format(total_callees))
    print("  Total edges:                 {:>9,}".format(total_edges_dedup))
    print("  Avg callees/caller:          {:>9.1f}".format(
        total_edges_dedup / max(total_callers, 1)))
    print("  Index size:                  {:>8.1f} MB".format(size_mb))
    print("  Build time:                  {:>8.1f}s".format(total_time))
    print("")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build call graph index")
    parser.add_argument("--base-dir", "-d", help="Base directory")
    args = parser.parse_args()

    base_dir = args.base_dir or detect_base_dir()
    if not base_dir:
        print("ERROR: Cannot detect base directory.")
        sys.exit(1)

    build_callgraph_index(base_dir)
