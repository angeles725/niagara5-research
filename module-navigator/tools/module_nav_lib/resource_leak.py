"""
Resource Leak Audit for Module Navigator (Batch 5, Gap #11).

Detects resource allocations (file/socket/stream/JDBC handles) that are not
paired with a close() in the same method scope, which leak file handles or
connection-pool slots over the long life of a Niagara station.

Commands:
  resource-leak <module> [--json]

Reuses existing indexes (no new builders):
  class-index.json (source root + per-module class list)

Method-scope heuristic (NOT full inter-method dataflow):
  For each method that acquires a real resource, classify by what the same
  method body contains:
    SAFE    - try-with-resources ("try (") OR a close() guarded by a finally
    PARTIAL - a close() exists but not inside a finally (leaks on exception path)
    LEAKED  - resource acquired, no close()/try-with-resources anywhere in method

  This mirrors the source-scanning heuristics used by resolve-audit and
  driver-cleanup-audit. It favors low false-positives: methods whose signature
  the extractor cannot parse are simply not audited rather than guessed at.

  In-memory streams (ByteArrayInputStream, StringReader, ...) are intentionally
  excluded: their close() is a no-op and cannot leak an OS handle.
"""

import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Resource acquisition patterns (real OS/pool handles only)
# ---------------------------------------------------------------------------

# `new FileInputStream(...)`, `new Socket(...)`, wrapping streams, etc.
# In-memory types (ByteArray*/String*/CharArray*) are deliberately absent.
_RE_ALLOC = re.compile(
    r'\bnew\s+\w*(?:'
    r'FileInputStream|FileOutputStream|FileReader|FileWriter|RandomAccessFile|'
    r'BufferedReader|BufferedWriter|BufferedInputStream|BufferedOutputStream|'
    r'InputStreamReader|OutputStreamWriter|DataInputStream|DataOutputStream|'
    r'PrintWriter|PrintStream|Socket|ServerSocket|DatagramSocket|'
    r'ZipFile|JarFile|ZipInputStream|ZipOutputStream|GZIPInputStream|'
    r'GZIPOutputStream|ObjectInputStream|ObjectOutputStream'
    r')\s*\('
)

# Factory acquisitions: `.getConnection()`, `.getInputStream()`, `.openStream()`
_RE_ACQUIRE = re.compile(
    r'\.(?:getConnection|getInputStream|getOutputStream|openStream|'
    r'openConnection|createStatement|prepareStatement|newInputStream|'
    r'newOutputStream|newByteChannel)\s*\('
)

_RE_CLOSE = re.compile(r'\.close\s*\(')
_RE_TRY_WITH_RESOURCES = re.compile(r'\btry\s*\(')
_RE_FINALLY = re.compile(r'\bfinally\b')

# Method signature: TYPE name(...) {  — excludes control-flow keywords so that
# `return foo(...)` / `if (...)` are not mistaken for method declarations.
_RE_METHOD = re.compile(
    r'^[ \t]*'
    r'(?!\s*(?:if|for|while|switch|catch|return|else|do|throw|synchronized)\b)'
    r'(?:(?:public|protected|private|static|final|abstract|synchronized|'
    r'native|default|strictfp)\s+)*'
    r'[\w$<>\[\],.\s]+?\s+(\w+)\s*\([^;={]*\)\s*(?:throws[\w,.\s]+?)?\s*\{',
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached per process)
# ---------------------------------------------------------------------------

_class_index_cache = None


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


def _get_source_root(ci_data):
    return ci_data.get("_meta", {}).get("source", "")


def _read_source(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (IOError, OSError):
        return None


# ---------------------------------------------------------------------------
# Method extraction (brace-matching, same technique as driver_cleanup)
# ---------------------------------------------------------------------------

def _iter_methods(content):
    """Yield (method_name, start_line_no, body_text) for each method.

    Uses a signature regex to find method openings, then brace-matches to
    capture the body. Methods whose signature is not matched are skipped
    (conservative: no guess = no false positive).
    """
    for m in _RE_METHOD.finditer(content):
        name = m.group(1)
        brace_open = content.rfind('{', m.start(), m.end())
        if brace_open == -1:
            continue
        depth = 0
        end = brace_open
        for i in range(brace_open, len(content)):
            c = content[i]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        body = content[brace_open + 1:end]
        start_line = content.count('\n', 0, brace_open) + 1
        yield name, start_line, body


def _first_alloc_line(body, start_line):
    """Return (relative_line_no, stripped_code) of the first acquisition."""
    for offset, line in enumerate(body.split('\n')):
        if _RE_ALLOC.search(line) or _RE_ACQUIRE.search(line):
            stripped = line.strip()
            if len(stripped) > 100:
                stripped = stripped[:97] + "..."
            return start_line + offset, stripped
    return start_line, ""


def _classify_method(body):
    """Classify a method body's resource handling.

    Returns one of "SAFE", "PARTIAL", "LEAKED", or None if the method acquires
    no real resource.
    """
    if not (_RE_ALLOC.search(body) or _RE_ACQUIRE.search(body)):
        return None

    if _RE_TRY_WITH_RESOURCES.search(body):
        return "SAFE"

    has_close = _RE_CLOSE.search(body) is not None
    if not has_close:
        return "LEAKED"

    if _RE_FINALLY.search(body):
        return "SAFE"
    return "PARTIAL"


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_resource_leak(base_dir, module_name, as_json=False):
    """Audit resource acquisitions in a module for missing close().

    Args:
        base_dir: module-navigator root directory
        module_name: module to audit (e.g. 'fox-rt')
        as_json: if True, emit JSON instead of human-readable output
    """
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    source_root = _get_source_root(ci_data)
    if not source_root:
        print("ERROR: source root not found in class-index metadata.")
        return

    classes = ci_data.get("classes", {})

    safe = []      # (class, method, line, code)
    partial = []   # (class, method, line, code)
    leaked = []    # (class, method, line, code)
    files_scanned = 0

    # Progress goes to stderr so stdout stays clean for --json consumers.
    sys.stderr.write("  Scanning...")
    sys.stderr.flush()

    for class_name, entries in classes.items():
        for entry in entries:
            # Skip inner classes (not standalone source files)
            if entry.get("outer_class") is not None:
                continue
            if entry.get("module") != module_name:
                continue

            filepath = os.path.join(source_root, entry["path"])
            content = _read_source(filepath)
            if content is None:
                continue

            files_scanned += 1

            # Cheap pre-filter: skip files with no acquisition at all
            if not (_RE_ALLOC.search(content) or _RE_ACQUIRE.search(content)):
                continue

            for method_name, start_line, body in _iter_methods(content):
                verdict = _classify_method(body)
                if verdict is None:
                    continue
                line_no, code = _first_alloc_line(body, start_line)
                rec = (class_name, method_name, line_no, code)
                if verdict == "SAFE":
                    safe.append(rec)
                elif verdict == "PARTIAL":
                    partial.append(rec)
                else:
                    leaked.append(rec)

    sys.stderr.write(" done ({:,} files)\n".format(files_scanned))
    sys.stderr.flush()

    if as_json:
        _emit_json(module_name, files_scanned, safe, partial, leaked)
    else:
        _emit_text(module_name, files_scanned, safe, partial, leaked)


def _emit_text(module_name, files_scanned, safe, partial, leaked):
    """Print human-readable audit report."""
    total = len(safe) + len(partial) + len(leaked)

    print("")
    print("  " + "=" * 66)
    print("  RESOURCE LEAK AUDIT: {}".format(module_name))
    print("  " + "=" * 66)
    print("")
    print("  Source files scanned:        {:>6,}".format(files_scanned))
    print("  Methods acquiring resources: {:>6,}".format(total))
    print("")

    if safe:
        print("  SAFE (try-with-resources or close() in finally):")
        for cls, meth, ln, code in safe[:15]:
            print("    {}.{}():{}".format(cls, meth, ln))
        if len(safe) > 15:
            print("    ... and {} more".format(len(safe) - 15))
        print("")

    if partial:
        print("  PARTIAL (close() present but not in finally — leaks on "
              "exception path):")
        for cls, meth, ln, code in partial[:20]:
            print("    {}.{}():{}".format(cls, meth, ln))
            print("      {}".format(code))
        if len(partial) > 20:
            print("    ... and {} more".format(len(partial) - 20))
        print("")

    if leaked:
        print("  LEAKED (resource acquired, no close() in method):")
        for cls, meth, ln, code in leaked[:20]:
            print("    {}.{}():{}".format(cls, meth, ln))
            print("      {}".format(code))
            print("      → no close() / try-with-resources in this method")
        if len(leaked) > 20:
            print("    ... and {} more".format(len(leaked) - 20))
        print("")

    print("  SUMMARY:")
    print("    Safe: {:,}  |  Partial: {:,}  |  Leaked: {:,}".format(
        len(safe), len(partial), len(leaked)))
    if leaked:
        print("    → RISK HIGH: {} acquisitions have no close() — file handles "
              "/ pool slots held until station restart".format(len(leaked)))
    elif partial:
        print("    → RISK MEDIUM: {} acquisitions leak only on the exception "
              "path".format(len(partial)))
    else:
        print("    → RISK LOW: all resource acquisitions are closed safely")
    print("")
    print("  NOTE: method-scope heuristic; resources closed in a different "
          "method (e.g. lifecycle doStop) may show as LEAKED.")
    print("")


def _emit_json(module_name, files_scanned, safe, partial, leaked):
    """Print JSON audit report."""
    def rows(items):
        return [
            {"class": cls, "method": meth, "line": ln, "code": code}
            for cls, meth, ln, code in items
        ]

    result = {
        "command": "resource-leak",
        "module": module_name,
        "files_scanned": files_scanned,
        "methods_acquiring_resources": len(safe) + len(partial) + len(leaked),
        "safe": rows(safe),
        "partial": rows(partial),
        "leaked": rows(leaked),
        "summary": {
            "safe_count": len(safe),
            "partial_count": len(partial),
            "leaked_count": len(leaked),
            "risk": (
                "HIGH" if leaked
                else "MEDIUM" if partial
                else "LOW"
            ),
        },
        "note": ("method-scope heuristic; resources closed in a different "
                 "method may show as LEAKED"),
    }
    print(json.dumps(result, indent=2))
