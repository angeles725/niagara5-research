"""
Source grep commands for Module Navigator (Phase 2).

Commands:
  grep <regex> [-n N] [--module mod] [--type rt|wb|ux]
      Full-text regex search across all decompiled sources.

  source <class> [--code] [--grep pattern]
      Show info or source code for a class.

  snippet <class> <method>
      Extract a specific method's source code.
"""

import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

_class_index_cache = None
_inventory_cache = None


def _load_class_index(base_dir):
    """Load class-index.json (cached)."""
    global _class_index_cache
    if _class_index_cache is not None:
        return _class_index_cache
    path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(path):
        print("ERROR: class-index.json not found.")
        print("Run: python tools/build_class_index.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _class_index_cache = json.load(f)
    return _class_index_cache


def _load_inventory(base_dir):
    """Load module-inventory.json (cached)."""
    global _inventory_cache
    if _inventory_cache is not None:
        return _inventory_cache
    path = os.path.join(base_dir, "indexes", "module-inventory.json")
    if not os.path.isfile(path):
        print("ERROR: module-inventory.json not found.")
        print("Run: python tools/build_module_inventory.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _inventory_cache = json.load(f)
    return _inventory_cache


def _resolve_source_root(meta_source):
    """Resolve the corpus source root via env var + fallback chain.

    Semantics:
      - If NAV_CORPUS_BASE is SET, it is the only path tried. A set-but-invalid
        env var does NOT fall through — it is treated as a hard error so the
        user notices the mistake instead of silently getting the default.
      - If NAV_CORPUS_BASE is UNSET, the fallback chain is:
          1. meta_source (from class-index.json _meta.source)
          2. /home/cristian/modules/Prototipos/modulos/organized (WSL native)
          3. /mnt/c/modules/Prototipos/modulos/organized (WSL over Windows mount)

    Returns (resolved_path, None) on success or (None, tried_paths) on failure.
    """
    tried = []

    env_override = os.environ.get("NAV_CORPUS_BASE")
    if env_override:
        tried.append(env_override)
        if os.path.isdir(env_override):
            return env_override, None
        # Explicitly set but invalid — don't silently fall through.
        return None, tried

    for candidate in [
        meta_source,
        "/home/cristian/modules/Prototipos/modulos/organized",
        "/mnt/c/modules/Prototipos/modulos/organized",
    ]:
        if not candidate:
            continue
        tried.append(candidate)
        if os.path.isdir(candidate):
            return candidate, None
    return None, tried


def _print_source_root_error(tried):
    """Print an actionable error listing every path attempted."""
    print("")
    print("ERROR: Corpus source root not found.")
    print("  Tried the following paths (first valid wins):")
    for p in tried:
        print("    {}".format(p))
    print("")
    print("  Override with the NAV_CORPUS_BASE environment variable, e.g.:")
    print("    export NAV_CORPUS_BASE=/home/user/modules/organized")
    print("")


def _get_source_root(data):
    """Get the resolved corpus root.

    Returns the resolved path on success, or None after printing an actionable
    error that lists every path attempted and the NAV_CORPUS_BASE override.
    """
    meta_source = data.get("_meta", {}).get("source", "")
    resolved, tried = _resolve_source_root(meta_source)
    if resolved:
        return resolved
    _print_source_root_error(tried)
    return None


def _build_type_set(base_dir, type_filter):
    """Build a set of module names (e.g. 'workbench-wb') matching a type filter."""
    inv = _load_inventory(base_dir)
    if not inv:
        return None
    modules = inv.get("modules", {})
    return set(k for k, v in modules.items() if v.get("type") == type_filter)


# ---------------------------------------------------------------------------
# grep command
# ---------------------------------------------------------------------------

def cmd_grep(base_dir, pattern, limit=30, module_filter=None, type_filter=None):
    """Regex search across all decompiled Java sources.

    Uses class-index.json to iterate files (only top-level classes to
    avoid scanning the same file twice for inner classes).
    """
    data = _load_class_index(base_dir)
    if not data:
        return

    source_root = _get_source_root(data)
    if not source_root:
        return  # _get_source_root already printed an actionable error

    # Compile regex
    try:
        regex = re.compile(pattern)
    except re.error as e:
        print("ERROR: Invalid regex '{}': {}".format(pattern, e))
        return

    # Build type filter set if needed
    type_set = None
    if type_filter:
        type_set = _build_type_set(base_dir, type_filter)
        if type_set is None:
            return
        if not type_set:
            print("No modules found with type '{}'.".format(type_filter))
            return

    classes = data["classes"]

    # Collect unique files to scan (skip inner classes to avoid duplicates)
    files_to_scan = []
    for cname, entries in classes.items():
        for entry in entries:
            if entry["outer_class"] is not None:
                continue
            if module_filter and entry["module"] != module_filter:
                continue
            if type_set and entry["module"] not in type_set:
                continue
            files_to_scan.append((cname, entry))

    # Sort by module then class for consistent output
    files_to_scan.sort(key=lambda x: (x[1]["module"], x[0]))

    results = []
    files_searched = 0
    files_with_matches = 0

    for cname, entry in files_to_scan:
        filepath = os.path.join(source_root, entry["path"])
        if not os.path.isfile(filepath):
            continue

        files_searched += 1
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except (IOError, OSError):
            continue

        file_had_match = False
        for lineno, line in enumerate(lines, 1):
            if regex.search(line):
                if not file_had_match:
                    file_had_match = True
                    files_with_matches += 1
                results.append((cname, entry["module"], entry["path"], lineno, line.rstrip()))
                if len(results) >= limit:
                    break

        if len(results) >= limit:
            break

    # Output
    if not results:
        scope = ""
        if module_filter:
            scope = " in module '{}'".format(module_filter)
        elif type_filter:
            scope = " in type '{}'".format(type_filter)
        print("  No matches for /{}/{} ({:,} files searched).".format(
            pattern, scope, files_searched))
        return

    print("")
    print("  grep /{}/ — {} matches in {} files ({:,} files searched)".format(
        pattern,
        len(results) if len(results) < limit else "{}+".format(limit),
        files_with_matches,
        files_searched,
    ))
    print("")

    last_module = None
    for cname, module, path, lineno, line in results:
        if module != last_module:
            if last_module is not None:
                print("")
            print("  [{}]".format(module))
            last_module = module
        # Truncate long lines
        display_line = line if len(line) <= 120 else line[:117] + "..."
        print("    {}:{} {}".format(cname, lineno, display_line))

    if len(results) >= limit:
        print("")
        print("  ... limit reached ({}) — use -n to increase".format(limit))
    print("")


# ---------------------------------------------------------------------------
# source command
# ---------------------------------------------------------------------------

def _resolve_class(data, class_name):
    """Resolve a class name to (resolved_name, entry) or (None, None).

    Accepts:
      - Simple names (e.g. 'BLinkPad')
      - Fully-qualified names (e.g. 'com.tridium.workbench.util.BLinkPad')

    If multiple entries exist for a simple name, picks the first top-level
    one. For an FQN, filters by exact package match (preferring top-level).
    """
    classes = data["classes"]

    # FQN path: split on the last dot and filter by package
    if "." in class_name:
        pkg, simple = class_name.rsplit(".", 1)
        if simple in classes:
            # Prefer top-level matches in the requested package
            for e in classes[simple]:
                if e["package"] == pkg and e["outer_class"] is None:
                    return simple, e
            # Fall back to any match in the package (inner classes indexed separately)
            for e in classes[simple]:
                if e["package"] == pkg:
                    return simple, e
        return None, None

    # Simple-name path (unchanged behavior)
    if class_name in classes:
        entries = classes[class_name]
        # Prefer top-level
        for e in entries:
            if e["outer_class"] is None:
                return class_name, e
        return class_name, entries[0]

    # Case-insensitive fallback
    name_lower = class_name.lower()
    for k, entries in classes.items():
        if k.lower() == name_lower:
            for e in entries:
                if e["outer_class"] is None:
                    return k, e
            return k, entries[0]

    return None, None


def cmd_source(base_dir, class_name, show_code=False, grep_pattern=None):
    """Show info or source code for a class."""
    data = _load_class_index(base_dir)
    if not data:
        return

    resolved, entry = _resolve_class(data, class_name)
    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        print("  Try: search '*{}*'".format(class_name))
        return

    source_root = _get_source_root(data)
    # Info mode still works even without a valid source root (prints metadata only).
    # Code / grep modes require filesystem access and return early on failure.
    if source_root is None and (show_code or grep_pattern):
        return  # error already printed by _get_source_root
    filepath = os.path.join(source_root, entry["path"]) if source_root else None

    if not show_code and not grep_pattern:
        # Info mode
        print("")
        print("  Class:    {}".format(resolved))
        print("  Package:  {}".format(entry["package"]))
        print("  Module:   {}".format(entry["module"]))
        print("  Kind:     {}".format(entry["kind"]))
        print("  Lines:    {:,}".format(entry["lines"]))
        print("  Path:     {}".format(entry["path"]))
        if filepath and not os.path.isfile(filepath):
            print("  WARNING:  Source file not found on disk!")
        print("")
        return

    # Read source file
    if not filepath or not os.path.isfile(filepath):
        print("  ERROR: Source file not found: {}".format(filepath))
        return

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (IOError, OSError) as e:
        print("  ERROR: Cannot read source: {}".format(e))
        return

    if grep_pattern:
        # Grep within file
        try:
            regex = re.compile(grep_pattern)
        except re.error as e:
            print("  ERROR: Invalid regex: {}".format(e))
            return

        print("")
        print("  source {} --grep /{}/ ({})".format(resolved, grep_pattern, entry["module"]))
        print("")
        matches = 0
        for lineno, line in enumerate(lines, 1):
            if regex.search(line):
                matches += 1
                print("  {:4d} | {}".format(lineno, line.rstrip()))
        if matches == 0:
            print("  No matches for /{}/ in {} ({} lines).".format(
                grep_pattern, resolved, len(lines)))
        else:
            print("")
            print("  {} matches in {} lines".format(matches, len(lines)))
        print("")
        return

    if show_code:
        # Full source with line numbers
        print("")
        print("  SOURCE: {} ({}, {} lines)".format(resolved, entry["module"], len(lines)))
        print("  PATH:   {}".format(entry["path"]))
        print("")
        for lineno, line in enumerate(lines, 1):
            print("{:4d} | {}".format(lineno, line.rstrip()))
        print("")


# ---------------------------------------------------------------------------
# source --batch — read multiple classes in one call (Batch 7, FEATURE-7)
# ---------------------------------------------------------------------------

def cmd_source_batch(base_dir, class_names_csv, show_code=False, grep_pattern=None):
    """Invoke cmd_source for each class in the CSV with separators.

    Mantains existing cmd_source semantics per class: "not found" messages do
    not abort the loop; the batch continues to the next class. When --code is
    combined with more than one class, emits a stderr warning since combined
    source output can be very large.
    """
    import sys as _sys

    # Split and trim; drop empty entries (tolerant of trailing commas / spaces)
    names = [n.strip() for n in class_names_csv.split(",") if n.strip()]
    if not names:
        print("  Usage: source --batch A,B,C [--code] [--grep pattern]")
        return

    if show_code and len(names) > 1:
        _sys.stderr.write(
            "  WARN: --batch with --code can emit large output; "
            "redirect to a file (e.g. `> out.txt`) if needed.\n")

    for name in names:
        print("")
        print("=== {} ===".format(name))
        cmd_source(base_dir, name, show_code=show_code, grep_pattern=grep_pattern)


# ---------------------------------------------------------------------------
# snippet command
# ---------------------------------------------------------------------------

def cmd_snippet(base_dir, class_name, method_name, context=2):
    """Extract a specific method's source code from a class.

    Finds the method declaration and tracks brace depth to find the end.
    Shows the complete method body with line numbers.
    """
    data = _load_class_index(base_dir)
    if not data:
        return

    resolved, entry = _resolve_class(data, class_name)
    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        print("  Try: search '*{}*'".format(class_name))
        return

    source_root = _get_source_root(data)
    if not source_root:
        return  # error already printed
    filepath = os.path.join(source_root, entry["path"])

    if not os.path.isfile(filepath):
        print("  ERROR: Source file not found: {}".format(filepath))
        return

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (IOError, OSError) as e:
        print("  ERROR: Cannot read source: {}".format(e))
        return

    # Pattern to find method declaration
    method_pat = re.compile(
        r'\b' + re.escape(method_name) + r'\s*\('
    )

    # Pattern to verify it's a declaration (has a type or modifier before it)
    decl_pat = re.compile(
        r'(?:public|protected|private|static|final|abstract|synchronized|native|void|'
        r'int|long|boolean|double|float|byte|short|char|'
        r'[A-Z]\w*(?:<[^>]*>)?(?:\[\])*)\s+'
        + re.escape(method_name) + r'\s*\('
    )

    snippets = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if method_pat.search(line) and decl_pat.search(line):
            # Found a method declaration
            start = max(0, i - context)

            # Track brace depth to find method end
            brace_depth = 0
            found_open = False
            j = i
            while j < len(lines):
                for ch in lines[j]:
                    if ch == '{':
                        brace_depth += 1
                        found_open = True
                    elif ch == '}':
                        brace_depth -= 1
                if found_open and brace_depth == 0:
                    end = min(len(lines), j + 1 + context)
                    snippets.append((start, end))
                    i = j + 1
                    break
                j += 1
            else:
                # No closing brace found
                end = min(len(lines), i + 30)
                snippets.append((start, end))
                i = end
            continue
        i += 1

    if not snippets:
        print("  Method '{}' not found in {} ({} lines).".format(
            method_name, resolved, len(lines)))
        # Suggest similar methods
        partial_pat = re.compile(
            r'(?:public|protected|private)\s+\S+\s+(\w*'
            + re.escape(method_name) + r'\w*)\s*\(', re.IGNORECASE
        )
        suggestions = []
        for line in lines:
            m = partial_pat.search(line)
            if m and m.group(1) not in suggestions:
                suggestions.append(m.group(1))
        if suggestions:
            print("  Similar methods: {}".format(", ".join(suggestions[:10])))
        return

    print("")
    print("  SNIPPET: {}.{} ({})".format(resolved, method_name, entry["module"]))
    print("  PATH:    {}".format(entry["path"]))
    print("")

    for si, (start, end) in enumerate(snippets):
        if si > 0:
            print("")
            print("  --- overload {} ---".format(si + 1))
            print("")
        for k in range(start, end):
            print("{:4d} | {}".format(k + 1, lines[k].rstrip()))

    if len(snippets) > 1:
        print("")
        print("  ({} overloads found)".format(len(snippets)))
    print("")
