#!/usr/bin/env python
"""
Build field index from decompiled Java sources.

Reads class-index.json as a catalog of all top-level .java files,
parses field declarations from each file, and produces indexes/field-index.json
with two maps:

  fields:       { "fieldName": [{"class":"BWidget","module":"bajaui-wb",...}] }
  class_fields: { "BLinkPad": ["field1","field2",...] }

Uses brace-depth tracking (same as build_method_index.py) to distinguish
class-level fields from local variables. Only fields at class body depth
(depth == enclosing class brace depth) are captured.

Usage:
  python tools/build_field_index.py [--base-dir DIR]
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
    'synchronized', 'native', 'strictfp', 'default', 'transient', 'volatile',
])

# Keywords that start statements but are NOT field declarations
NOT_FIELD_STARTERS = frozenset([
    'if', 'else', 'while', 'for', 'do', 'switch', 'try', 'catch', 'finally',
    'return', 'throw', 'new', 'super', 'this', 'case', 'import', 'package',
    'class', 'interface', 'enum', 'assert', 'break', 'continue', 'goto',
    'instanceof', 'var', 'record', 'sealed', 'permits', 'yield',
])

RE_CLASS_DECL = re.compile(
    r'\b(?:class|interface|enum)\s+(\w+)'
)

# Pattern: captures a field declaration line
# Matches: [modifiers] Type fieldName [= initializer] ;
# We parse this programmatically rather than with a single regex
# because of generics, arrays, and multi-field declarations.


# ---------------------------------------------------------------------------
# Brace counting (reused from build_method_index.py)
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
# Extract initial value for constants
# ---------------------------------------------------------------------------

def extract_initial_value(rest):
    """Extract a short initial value from '= value;' portion.

    Returns the value string (trimmed) or empty string.
    Only captures simple literals/constants, not complex expressions.
    """
    rest = rest.strip()
    if not rest.startswith('='):
        return ''
    rest = rest[1:].strip()
    # Remove trailing semicolons and braces
    if rest.endswith(';'):
        rest = rest[:-1].strip()

    # Cap length — we only want short constant values
    if len(rest) > 100:
        return rest[:97] + '...'
    return rest


# ---------------------------------------------------------------------------
# Field detection
# ---------------------------------------------------------------------------

def try_parse_field(stripped, lines, line_idx, n_lines):
    """Try to parse a field declaration from a line at class body depth.

    Returns list of field dicts (may be multiple for int a, b, c;)
    or empty list if not a field.
    """
    # Quick rejects
    if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
        return []

    # Must not contain '(' before any ';' — that would be a method
    semi_idx = stripped.find(';')
    paren_idx = stripped.find('(')
    if paren_idx >= 0 and (semi_idx < 0 or paren_idx < semi_idx):
        return []

    # Handle multi-line declarations: if no ';', read continuation
    full_line = stripped
    extra_lines = 0
    if semi_idx < 0:
        parts = [stripped]
        extra = 0
        while line_idx + extra + 1 < n_lines and extra < 10:
            extra += 1
            next_line = lines[line_idx + extra].strip()
            parts.append(next_line)
            if ';' in next_line:
                break
        full_line = ' '.join(parts)
        extra_lines = extra
        semi_idx = full_line.find(';')
        if semi_idx < 0:
            return []

    # Take everything up to the first semicolon (ignore anything after for multi-statement lines)
    decl = full_line[:semi_idx].strip()
    after_semi = full_line[semi_idx + 1:].strip()

    if not decl:
        return []

    # Tokenize the declaration
    tokens = _tokenize_decl(decl)
    if len(tokens) < 2:
        return []

    # Extract modifiers
    mods = []
    type_start = 0
    for k, tok in enumerate(tokens):
        if tok.startswith('@'):
            # Skip annotation — it might have parens in the tokenized form
            type_start = k + 1
        elif tok in MODIFIERS:
            mods.append(tok)
            type_start = k + 1
        else:
            break

    remaining = tokens[type_start:]
    if len(remaining) < 2:
        return []

    # First remaining token(s) are the type, last is the field name
    # But we need to handle generics: "Map<String, List<Integer>>" is one type token
    # and "Type[]" arrays

    # The last token should be the field name (or name = value)
    # We need to find the split between type and name

    # Strategy: work backwards. The last token that is a valid identifier is the name.
    # Everything before it is the type.

    # Handle "Type name = value" — split on '='
    eq_idx = None
    for i, tok in enumerate(remaining):
        if tok == '=':
            eq_idx = i
            break

    if eq_idx is not None:
        # Everything after = is the initial value
        init_parts = remaining[eq_idx + 1:]
        init_value = ' '.join(init_parts).strip()
        remaining = remaining[:eq_idx]
    else:
        init_value = ''

    if len(remaining) < 2:
        return []

    # Last token is field name
    field_name = remaining[-1]
    type_tokens = remaining[:-1]
    field_type = ' '.join(type_tokens)

    # Validate field name: must be a valid Java identifier
    if not field_name or not (field_name[0].isalpha() or field_name[0] == '_'):
        return []
    if field_name in NOT_FIELD_STARTERS:
        return []
    # Reject if field_name looks like a keyword or type
    if field_name in ('class', 'interface', 'enum', 'extends', 'implements',
                      'throws', 'void', 'null', 'true', 'false'):
        return []

    # Reject if the type contains suspicious chars
    if any(c in field_type for c in ('(', ')', '{', '}')):
        return []

    # Handle array brackets on name: "int[] data" or "int data[]"
    if field_name.endswith('[]'):
        field_type += '[]'
        field_name = field_name.rstrip('[]').rstrip()
    if field_name.endswith(']'):
        # Handle complex array: name[][]
        bracket_start = field_name.find('[')
        if bracket_start > 0:
            field_type += field_name[bracket_start:]
            field_name = field_name[:bracket_start]

    if not field_name or not field_name[0].isalpha() and field_name[0] != '_':
        return []

    return [{
        'name': field_name,
        'type': field_type,
        'modifiers': mods,
        'initial_value': init_value,
    }]


def _tokenize_decl(decl):
    """Tokenize a declaration, keeping generics together as one token.

    E.g.: 'private static final Map<String, List<Integer>> cache'
    -> ['private', 'static', 'final', 'Map<String, List<Integer>>', 'cache']
    """
    tokens = []
    current = []
    angle_depth = 0
    i = 0
    while i < len(decl):
        ch = decl[i]
        if ch == '<':
            angle_depth += 1
            current.append(ch)
        elif ch == '>':
            angle_depth = max(0, angle_depth - 1)
            current.append(ch)
        elif ch in (' ', '\t') and angle_depth == 0:
            if current:
                tokens.append(''.join(current))
                current = []
        elif ch == '=' and angle_depth == 0:
            if current:
                tokens.append(''.join(current))
                current = []
            tokens.append('=')
        else:
            current.append(ch)
        i += 1
    if current:
        tokens.append(''.join(current))
    return tokens


# ---------------------------------------------------------------------------
# Parse all fields from a file
# ---------------------------------------------------------------------------

def parse_fields_from_content(content, file_class_name):
    """Parse all field declarations from a Java file.

    Uses brace-depth tracking to only capture fields at class body depth
    (not local variables inside methods).
    """
    lines = content.split('\n')
    n = len(lines)
    fields = []

    brace_depth = 0
    class_stack = []  # [(class_name, body_depth)]
    in_block_comment = False
    in_enum_constants = False  # Track enum constant region

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
            in_enum_constants = False

        # Detect class/interface/enum declarations
        is_class_decl = False
        if stripped and not stripped.startswith('//') and not stripped.startswith('@'):
            cm = RE_CLASS_DECL.search(stripped)
            if cm:
                cname = cm.group(1)
                body_depth = brace_depth + opens
                class_stack.append((cname, body_depth))
                is_class_decl = True
                # Check if this is an enum
                if 'enum ' in stripped:
                    in_enum_constants = True

        # Update brace depth
        brace_depth += opens - closes

        # --- Field detection ---
        # Only parse fields at class body depth (one level inside the class)
        if (not is_class_decl
                and class_stack
                and stripped
                and not stripped.startswith('//')
                and not stripped.startswith('@')
                and not stripped.startswith('*')
                and '(' not in stripped):

            # Current depth should equal the class body depth
            # (meaning we're directly inside the class, not inside a method)
            enclosing_name, body_depth = class_stack[-1]
            # At class body level: depth after opens but before closes
            # should match body_depth
            current_effective = brace_depth
            # We want fields at exactly the class body depth
            if current_effective == body_depth:
                # Skip enum constants region (before first ';' in enum body)
                if in_enum_constants:
                    if ';' in stripped:
                        in_enum_constants = False
                    i += 1
                    continue

                parsed = try_parse_field(stripped, lines, i, n)
                for field in parsed:
                    field['class'] = enclosing_name
                    field['line'] = i + 1  # 1-indexed
                    fields.append(field)

        i += 1

    return fields


# ---------------------------------------------------------------------------
# Builder main
# ---------------------------------------------------------------------------

def detect_base_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(script_dir)
    if os.path.isdir(os.path.join(base, "indexes")):
        return base
    return None


def build_field_index(base_dir):
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
    # Parse fields from each file
    # -----------------------------------------------------------------------
    print("Parsing fields from {} files...".format(len(top_files)))
    t1 = time.time()

    # Output maps
    fields_map = {}       # field_name -> [entries]
    class_fields_map = {} # class_name -> sorted set of field names

    files_parsed = 0
    files_failed = 0
    total_fields = 0
    total_static = 0
    total_final = 0
    total_constants = 0  # static final with initial value
    total_with_init = 0
    max_fields_per_class = 0
    max_fields_class = ""
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

        parsed_fields = parse_fields_from_content(content, file_class)

        for fld in parsed_fields:
            fname = fld['name']
            cls = fld['class']

            entry = {
                "class": cls,
                "module": module,
                "type": fld['type'],
                "modifiers": fld['modifiers'],
                "line": fld['line'],
            }
            if fld['initial_value']:
                entry["init"] = fld['initial_value']

            # Add to fields map
            if fname not in fields_map:
                fields_map[fname] = []
            fields_map[fname].append(entry)

            # Add to class_fields map
            if cls not in class_fields_map:
                class_fields_map[cls] = set()
            class_fields_map[cls].add(fname)

            total_fields += 1
            if 'static' in fld['modifiers']:
                total_static += 1
            if 'final' in fld['modifiers']:
                total_final += 1
            if 'static' in fld['modifiers'] and 'final' in fld['modifiers'] and fld['initial_value']:
                total_constants += 1
            if fld['initial_value']:
                total_with_init += 1

        # Track max fields per class
        for cls, fset in class_fields_map.items():
            if len(fset) > max_fields_per_class:
                max_fields_per_class = len(fset)
                max_fields_class = cls

    t2 = time.time()
    parse_time = t2 - t1
    print("  Parsed {} files in {:.1f}s ({:.0f}/s)".format(
        files_parsed, parse_time,
        files_parsed / parse_time if parse_time > 0 else 0))
    print("  Failed to read: {}".format(files_failed))

    # -----------------------------------------------------------------------
    # Convert class_fields sets to sorted lists
    # -----------------------------------------------------------------------
    class_fields_out = {}
    for cls, fset in class_fields_map.items():
        class_fields_out[cls] = sorted(fset)

    # -----------------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------------
    unique_field_names = len(fields_map)
    total_definitions = sum(len(v) for v in fields_map.values())
    classes_with_fields = len(class_fields_map)

    # Distribution
    def_counts = [len(v) for v in fields_map.values()]
    max_defs = max(def_counts) if def_counts else 0
    avg_defs = sum(def_counts) / len(def_counts) if def_counts else 0

    # Top field names (most classes defining them)
    top_fields = sorted(fields_map.items(),
                        key=lambda x: len(x[1]), reverse=True)[:20]

    # Fields per class distribution
    cls_counts = [len(v) for v in class_fields_map.values()]
    avg_fields_per_class = sum(cls_counts) / len(cls_counts) if cls_counts else 0

    # Top field types
    type_counts = {}
    for fname, entries in fields_map.items():
        for e in entries:
            t = e.get("type", "")
            if t:
                type_counts[t] = type_counts.get(t, 0) + 1
    top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:20]

    print("")
    print("  Total field definitions:     {:>9,}".format(total_definitions))
    print("  Unique field names:          {:>9,}".format(unique_field_names))
    print("  Static fields:               {:>9,}".format(total_static))
    print("  Final fields:                {:>9,}".format(total_final))
    print("  Constants (static final+init):{:>8,}".format(total_constants))
    print("  With initial value:          {:>9,}".format(total_with_init))
    print("  Classes with fields:         {:>9,}".format(classes_with_fields))
    print("  Avg fields per class:        {:>9.1f}".format(avg_fields_per_class))
    print("  Max fields in one class:     {:>9,} ({})".format(
        max_fields_per_class, max_fields_class))
    print("  Max definitions per name:    {:>9,}".format(max_defs))
    print("  Avg definitions per name:    {:>9.1f}".format(avg_defs))
    print("")
    print("  Top 10 most-defined field names:")
    for name, entries in top_fields[:10]:
        print("    {:40s} {:>6,} definitions".format(name, len(entries)))
    print("")
    print("  Top 10 field types:")
    for tname, cnt in top_types[:10]:
        print("    {:40s} {:>6,}".format(tname, cnt))

    # -----------------------------------------------------------------------
    # Build output
    # -----------------------------------------------------------------------
    total_time = time.time() - t0
    meta = {
        "description": "Field index for Niagara N4 decompiled modules",
        "source_index": "class-index.json",
        "files_parsed": files_parsed,
        "files_failed": files_failed,
        "total_field_definitions": total_definitions,
        "unique_field_names": unique_field_names,
        "total_static": total_static,
        "total_final": total_final,
        "total_constants": total_constants,
        "total_with_init": total_with_init,
        "classes_with_fields": classes_with_fields,
        "avg_fields_per_class": round(avg_fields_per_class, 1),
        "max_fields_per_class": max_fields_per_class,
        "max_fields_class": max_fields_class,
        "max_definitions_per_name": max_defs,
        "avg_definitions_per_name": round(avg_defs, 1),
        "build_time_sec": round(total_time, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    output = {
        "_meta": meta,
        "fields": fields_map,
        "class_fields": class_fields_out,
    }

    # Write
    out_path = os.path.join(base_dir, "indexes", "field-index.json")
    print("")
    print("Writing {}...".format(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"), ensure_ascii=False)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print("  Done: {:.1f} MB in {:.1f}s".format(size_mb, total_time))
    print("")

    # Summary
    print("=" * 65)
    print("FIELD INDEX SUMMARY")
    print("=" * 65)
    print("  Files parsed:                {:>9,}".format(files_parsed))
    print("  Files failed:                {:>9,}".format(files_failed))
    print("  Total field definitions:     {:>9,}".format(total_definitions))
    print("  Unique field names:          {:>9,}".format(unique_field_names))
    print("  Static fields:               {:>9,}".format(total_static))
    print("  Final fields:                {:>9,}".format(total_final))
    print("  Constants (static final):    {:>9,}".format(total_constants))
    print("  With initial value:          {:>9,}".format(total_with_init))
    print("  Classes with fields:         {:>9,}".format(classes_with_fields))
    print("  Avg fields/class:            {:>9.1f}".format(avg_fields_per_class))
    print("  Max fields/class:            {:>9,} ({})".format(
        max_fields_per_class, max_fields_class))
    print("  Max defs/field name:         {:>9,}".format(max_defs))
    print("  Avg defs/field name:         {:>9.1f}".format(avg_defs))
    print("  Index size:                  {:>8.1f} MB".format(size_mb))
    print("  Build time:                  {:>8.1f}s".format(total_time))
    print("")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build field index")
    parser.add_argument("--base-dir", "-d", help="Base directory")
    args = parser.parse_args()

    base_dir = args.base_dir or detect_base_dir()
    if not base_dir:
        print("ERROR: Cannot detect base directory.")
        sys.exit(1)

    build_field_index(base_dir)
