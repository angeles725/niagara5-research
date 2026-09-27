#!/usr/bin/env python
"""
Build method index from decompiled Java sources.

Reads class-index.json as a catalog of all top-level .java files,
parses method declarations from each file, and produces indexes/method-index.json
with two maps:

  methods:       { "setPreferredSize": [{"class":"BWidget","module":"bajaui-wb",...}] }
  class_methods: { "BLinkPad": ["build","computePreferredSize","getType",...] }

Handles inner classes, constructors (indexed as "<init>"), multi-line signatures,
and skips false positives from control flow, method calls, and field assignments.

Usage:
  python tools/build_method_index.py [--base-dir DIR]
"""

import json
import os
import re
import sys
import time


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODIFIERS = frozenset([
    'public', 'private', 'protected', 'static', 'abstract', 'final',
    'synchronized', 'native', 'strictfp', 'default'
])

NOT_METHOD_NAMES = frozenset([
    'if', 'else', 'while', 'for', 'do', 'switch', 'try', 'catch', 'finally',
    'return', 'throw', 'new', 'super', 'this', 'case', 'import', 'package',
    'class', 'interface', 'enum', 'assert', 'break', 'continue', 'goto',
    'instanceof', 'var', 'record', 'sealed', 'permits', 'yield', 'null',
    'true', 'false', 'void',
])

RE_CLASS_DECL = re.compile(
    r'\b(?:class|interface|enum)\s+(\w+)'
)


# ---------------------------------------------------------------------------
# Brace counting (skips strings, chars, line comments)
# ---------------------------------------------------------------------------

def count_braces(line):
    """Count { and } in a line, skipping strings, chars, and // comments."""
    opens = 0
    closes = 0
    in_str = False
    in_char = False
    escaped = False
    i = 0
    while i < len(line):
        ch = line[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if ch == '\\' and (in_str or in_char):
            escaped = True
            i += 1
            continue
        if ch == '"' and not in_char:
            in_str = not in_str
            i += 1
            continue
        if ch == "'" and not in_str:
            in_char = not in_char
            i += 1
            continue
        if in_str or in_char:
            i += 1
            continue
        if ch == '/' and i + 1 < len(line) and line[i + 1] == '/':
            break
        if ch == '{':
            opens += 1
        elif ch == '}':
            closes += 1
        i += 1
    return opens, closes


# ---------------------------------------------------------------------------
# Parameter parsing
# ---------------------------------------------------------------------------

def split_params(params_str):
    """Split parameter string by commas, respecting <> nesting."""
    if not params_str.strip():
        return []
    result = []
    current = []
    depth = 0
    for ch in params_str:
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth = max(0, depth - 1)
        elif ch == ',' and depth == 0:
            result.append(''.join(current).strip())
            current = []
            continue
        current.append(ch)
    if current:
        result.append(''.join(current).strip())
    return [p for p in result if p]


def extract_param_type(param):
    """Extract type from 'Type name' or 'final Type name' or '@Ann Type name'."""
    param = param.strip()
    if not param:
        return ''

    # Strip annotations
    while param.startswith('@'):
        paren = param.find('(')
        space = param.find(' ')
        if space < 0:
            return param
        if 0 < paren < space:
            depth = 0
            for k, c in enumerate(param):
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        param = param[k + 1:].strip()
                        break
            else:
                param = param[space + 1:].strip()
        else:
            param = param[space + 1:].strip()

    # Strip 'final'
    if param.startswith('final '):
        param = param[6:].strip()

    # Last token is the param name; everything before is the type
    parts = param.rsplit(None, 1)
    if len(parts) == 2:
        return parts[0]
    return parts[0]


# ---------------------------------------------------------------------------
# Method detection on a single line
# ---------------------------------------------------------------------------

def try_parse_method(stripped, lines, line_idx, n_lines):
    """Try to parse a method/constructor declaration starting at this line.

    Returns (method_dict, extra_lines_consumed) or (None, 0).
    """
    paren_idx = stripped.find('(')
    if paren_idx < 0:
        return None, 0

    before = stripped[:paren_idx].rstrip()

    # Find method name: last identifier before (
    j = len(before) - 1
    while j >= 0 and (before[j].isalnum() or before[j] == '_'):
        j -= 1

    if j >= len(before) - 1:
        return None, 0

    name = before[j + 1:]
    prefix = before[:j + 1].rstrip()

    # Reject Java keywords
    if name in NOT_METHOD_NAMES:
        return None, 0

    if not name or not (name[0].isalpha() or name[0] == '_'):
        return None, 0

    # Reject method calls (prefix ends with .) and assignments (=)
    if prefix.endswith('.') or '=' in prefix:
        return None, 0

    # Parse modifiers and return type from prefix
    if prefix:
        tokens = prefix.split()
        if 'new' in tokens:
            return None, 0

        mods = []
        type_start = 0
        for k, tok in enumerate(tokens):
            if tok.startswith('@'):
                type_start = k + 1
            elif tok in MODIFIERS:
                mods.append(tok)
                type_start = k + 1
            else:
                break

        return_type_parts = tokens[type_start:]
        return_type = ' '.join(return_type_parts)

        # Reject invalid chars in return type
        if return_type and any(c in return_type for c in '=+/%!&|^~;'):
            return None, 0
    else:
        mods = []
        return_type = ''

    # Get parameters
    after = stripped[paren_idx + 1:]
    close_idx = after.find(')')
    extra_lines = 0

    if close_idx >= 0:
        params_str = after[:close_idx].strip()
        rest = after[close_idx + 1:].strip()
    else:
        # Multi-line params: read continuation lines
        parts = [after]
        extra = 0
        while line_idx + extra + 1 < n_lines:
            extra += 1
            next_line = lines[line_idx + extra].strip()
            parts.append(next_line)
            if ')' in next_line:
                break
            if extra > 15:
                return None, 0
        full = ' '.join(parts)
        ci = full.find(')')
        if ci < 0:
            return None, 0
        params_str = full[:ci].strip()
        rest = full[ci + 1:].strip()
        extra_lines = extra

    # Verify: rest should start with { or ; or 'throws'
    if rest:
        if rest[0] not in ('{', ';') and not rest.startswith('throws'):
            return None, 0

    # Parse parameter types
    param_types = []
    if params_str:
        for p in split_params(params_str):
            pt = extract_param_type(p)
            if pt:
                param_types.append(pt)

    # Build signature
    sig_parts = []
    if mods:
        sig_parts.extend(mods)
    if return_type:
        sig_parts.append(return_type)
    sig_parts.append(name + '(' + ', '.join(param_types) + ')')
    signature = ' '.join(sig_parts)

    return {
        'name': name,
        'modifiers': mods,
        'return_type': return_type,
        'params': param_types,
        'signature': signature,
    }, extra_lines


# ---------------------------------------------------------------------------
# Parse all methods from a file
# ---------------------------------------------------------------------------

def parse_methods_from_content(content, file_class_name):
    """Parse all method/constructor declarations from a Java file.

    Uses brace-depth tracking to associate methods with the correct
    enclosing class (supports inner classes).
    """
    lines = content.split('\n')
    n = len(lines)
    methods = []

    brace_depth = 0
    class_stack = []  # [(class_name, body_depth)]
    in_block_comment = False

    i = 0
    while i < n:
        line = lines[i]

        # --- Handle block comments ---
        if in_block_comment:
            end_idx = line.find('*/')
            if end_idx >= 0:
                line = line[end_idx + 2:]
                in_block_comment = False
            else:
                i += 1
                continue

        # Remove inline block comments
        while '/*' in line:
            start = line.find('/*')
            end = line.find('*/', start + 2)
            if end >= 0:
                line = line[:start] + ' ' + line[end + 2:]
            else:
                line = line[:start]
                in_block_comment = True
                break

        stripped = line.strip()

        # --- Brace tracking ---
        opens, closes = count_braces(line)

        # Pop classes whose body has ended
        temp_depth = brace_depth
        for _ in range(closes):
            temp_depth -= 1
        while class_stack and temp_depth <= class_stack[-1][1] - 1:
            class_stack.pop()

        # Detect class/interface/enum declarations
        if stripped and not stripped.startswith('//') and not stripped.startswith('@'):
            cm = RE_CLASS_DECL.search(stripped)
            if cm:
                cname = cm.group(1)
                body_depth = brace_depth + opens
                class_stack.append((cname, body_depth))

        # Update brace depth
        brace_depth += opens - closes

        # --- Method detection ---
        if (stripped
                and not stripped.startswith('//')
                and not stripped.startswith('@')
                and '(' in stripped
                and line[0:1] in (' ', '\t', '')):

            method, extra = try_parse_method(stripped, lines, i, n)
            if method:
                enclosing = class_stack[-1][0] if class_stack else file_class_name

                # Determine if constructor
                if method['name'] == enclosing:
                    indexed_name = '<init>'
                elif not method['return_type'] and not method['modifiers']:
                    # No return type AND no modifiers => likely enum constant,
                    # not a real method. Skip.
                    i += 1
                    continue
                else:
                    indexed_name = method['name']

                method['indexed_name'] = indexed_name
                method['class'] = enclosing
                method['line'] = i + 1  # 1-indexed

                methods.append(method)
                if extra > 0:
                    i += extra

        i += 1

    return methods


# ---------------------------------------------------------------------------
# Builder main
# ---------------------------------------------------------------------------

def detect_base_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(script_dir)
    if os.path.isdir(os.path.join(base, "indexes")):
        return base
    return None


def build_method_index(base_dir):
    ci_path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(ci_path):
        print("ERROR: class-index.json not found at {}".format(ci_path))
        sys.exit(1)

    inv_path = os.path.join(base_dir, "indexes", "module-inventory.json")
    if not os.path.isfile(inv_path):
        print("ERROR: module-inventory.json not found at {}".format(inv_path))
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Load indexes
    # -----------------------------------------------------------------------
    print("Loading class-index.json...")
    t0 = time.time()
    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = json.load(f)
    classes = ci_data.get("classes", {})
    t_load = time.time() - t0
    print("  Loaded in {:.1f}s ({} unique names)".format(t_load, len(classes)))

    print("Loading module-inventory.json...")
    with open(inv_path, "r", encoding="utf-8") as f:
        inv_data = json.load(f)
    source_base = inv_data.get("_meta", {}).get("source", "")
    print("  Source base: {}".format(source_base))

    # -----------------------------------------------------------------------
    # Collect top-level files to process
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # Parse methods from each file
    # -----------------------------------------------------------------------
    print("Parsing methods from {} files...".format(len(top_files)))
    t1 = time.time()

    # Output maps
    methods_map = {}       # method_name -> [entries]
    class_methods_map = {} # class_name -> sorted set of method names

    files_parsed = 0
    files_failed = 0
    total_methods = 0
    total_constructors = 0
    multi_line_sigs = 0
    max_methods_per_class = 0
    max_methods_class = ""
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
            print("  {:>6,} / {:,} files ({:.0f}/s, {:.0f}s elapsed)...".format(
                files_parsed, len(top_files), rate, elapsed))

        methods = parse_methods_from_content(content, file_class)

        for m in methods:
            idx_name = m['indexed_name']
            cls = m['class']

            entry = {
                "class": cls,
                "module": module,
                "signature": m['signature'],
                "line": m['line'],
                "modifiers": m['modifiers'],
                "return_type": m['return_type'],
                "params": m['params'],
            }

            # Add to methods map
            if idx_name not in methods_map:
                methods_map[idx_name] = []
            methods_map[idx_name].append(entry)

            # Add to class_methods map
            if cls not in class_methods_map:
                class_methods_map[cls] = set()
            class_methods_map[cls].add(idx_name)

            total_methods += 1
            if idx_name == '<init>':
                total_constructors += 1

        # Track max methods per class
        for cls, mset in class_methods_map.items():
            if len(mset) > max_methods_per_class:
                max_methods_per_class = len(mset)
                max_methods_class = cls

    t2 = time.time()
    parse_time = t2 - t1
    print("  Parsed {} files in {:.1f}s ({:.0f}/s)".format(
        files_parsed, parse_time,
        files_parsed / parse_time if parse_time > 0 else 0))
    print("  Failed to read: {}".format(files_failed))

    # -----------------------------------------------------------------------
    # Convert class_methods sets to sorted lists
    # -----------------------------------------------------------------------
    class_methods_out = {}
    for cls, mset in class_methods_map.items():
        class_methods_out[cls] = sorted(mset)

    # -----------------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------------
    unique_method_names = len(methods_map)
    total_definitions = sum(len(v) for v in methods_map.values())
    classes_with_methods = len(class_methods_map)

    # Distribution of definitions per method name
    def_counts = [len(v) for v in methods_map.values()]
    max_defs = max(def_counts) if def_counts else 0
    avg_defs = sum(def_counts) / len(def_counts) if def_counts else 0

    # Top overloaded method names (most classes defining them)
    top_methods = sorted(methods_map.items(),
                         key=lambda x: len(x[1]), reverse=True)[:20]

    # Methods per class distribution
    cls_counts = [len(v) for v in class_methods_map.values()]
    avg_methods_per_class = sum(cls_counts) / len(cls_counts) if cls_counts else 0

    print("")
    print("  Total method definitions:    {:>9,}".format(total_definitions))
    print("  Unique method names:         {:>9,}".format(unique_method_names))
    print("  Constructors (<init>):       {:>9,}".format(total_constructors))
    print("  Classes with methods:        {:>9,}".format(classes_with_methods))
    print("  Avg methods per class:       {:>9.1f}".format(avg_methods_per_class))
    print("  Max methods in one class:    {:>9,} ({})".format(
        max_methods_per_class, max_methods_class))
    print("  Max definitions per name:    {:>9,}".format(max_defs))
    print("  Avg definitions per name:    {:>9.1f}".format(avg_defs))
    print("")
    print("  Top 10 most-defined method names:")
    for name, entries in top_methods[:10]:
        print("    {:40s} {:>6,} definitions".format(name, len(entries)))

    # -----------------------------------------------------------------------
    # Build output
    # -----------------------------------------------------------------------
    total_time = time.time() - t0
    meta = {
        "description": "Method index for Niagara N4 decompiled modules",
        "source_index": "class-index.json",
        "files_parsed": files_parsed,
        "files_failed": files_failed,
        "total_method_definitions": total_definitions,
        "unique_method_names": unique_method_names,
        "total_constructors": total_constructors,
        "classes_with_methods": classes_with_methods,
        "avg_methods_per_class": round(avg_methods_per_class, 1),
        "max_methods_per_class": max_methods_per_class,
        "max_methods_class": max_methods_class,
        "max_definitions_per_name": max_defs,
        "avg_definitions_per_name": round(avg_defs, 1),
        "build_time_sec": round(total_time, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    output = {
        "_meta": meta,
        "methods": methods_map,
        "class_methods": class_methods_out,
    }

    # Write
    out_path = os.path.join(base_dir, "indexes", "method-index.json")
    print("")
    print("Writing {}...".format(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"), ensure_ascii=False)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print("  Done: {:.1f} MB in {:.1f}s".format(size_mb, total_time))
    print("")

    # Summary
    print("=" * 65)
    print("METHOD INDEX SUMMARY")
    print("=" * 65)
    print("  Files parsed:                {:>9,}".format(files_parsed))
    print("  Files failed:                {:>9,}".format(files_failed))
    print("  Total method definitions:    {:>9,}".format(total_definitions))
    print("  Unique method names:         {:>9,}".format(unique_method_names))
    print("  Constructors (<init>):       {:>9,}".format(total_constructors))
    print("  Classes with methods:        {:>9,}".format(classes_with_methods))
    print("  Avg methods/class:           {:>9.1f}".format(avg_methods_per_class))
    print("  Max methods/class:           {:>9,} ({})".format(
        max_methods_per_class, max_methods_class))
    print("  Max defs/method name:        {:>9,}".format(max_defs))
    print("  Avg defs/method name:        {:>9.1f}".format(avg_defs))
    print("  Index size:                  {:>8.1f} MB".format(size_mb))
    print("  Build time:                  {:>8.1f}s".format(total_time))
    print("")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build method index")
    parser.add_argument("--base-dir", "-d", help="Base directory")
    args = parser.parse_args()

    base_dir = args.base_dir or detect_base_dir()
    if not base_dir:
        print("ERROR: Cannot detect base directory.")
        sys.exit(1)

    build_method_index(base_dir)
