#!/usr/bin/env python
"""
Build Niagara Annotations Index (Phase 7).

Parses @NiagaraType, @NiagaraProperty, @NiagaraProperties,
@NiagaraAction, @NiagaraActions, @NiagaraTopic from ALL top-level
.java files and generates indexes/annotations-index.json.

Only indexes classes that have @NiagaraType annotation.

Input:  indexes/class-index.json (catalog of 50K+ top-level classes)
        Source files in organized/{module}/{module}-{type}/vineflower/
Output: indexes/annotations-index.json

Usage:
  python tools/build_annotations_index.py
  python tools/build_annotations_index.py --base-dir /path/to/module-navigator
"""

import json
import os
import re
import sys
import time


# ---------------------------------------------------------------------------
# Annotation parsing
# ---------------------------------------------------------------------------

def read_header(filepath, max_lines=200):
    """Read the first N lines of a file (annotations + class decl zone)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            return "".join(lines)
    except Exception:
        return None


def extract_annotation_block(text):
    """Extract the annotation zone: from first @ to the class/interface/enum declaration."""
    # Find annotations that start at beginning of line (possibly with whitespace)
    # and the class declaration
    lines = text.split("\n")
    annot_start = None
    class_line_idx = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Detect annotation start
        if annot_start is None and stripped.startswith("@Niagara"):
            annot_start = i
        # Detect class declaration
        if re.match(r'^(public\s+)?(abstract\s+)?(final\s+)?(strictfp\s+)?(class|interface|enum)\s+', stripped):
            class_line_idx = i
            break

    if annot_start is None or class_line_idx is None:
        return None

    return "\n".join(lines[annot_start:class_line_idx])


def find_balanced_parens(text, start):
    """Find the matching closing paren for the opening paren at position start.
    Handles nested parens, strings (with escaped quotes), and braces."""
    depth = 0
    in_string = False
    escape_next = False
    i = start

    while i < len(text):
        ch = text[i]

        if escape_next:
            escape_next = False
            i += 1
            continue

        if ch == '\\' and in_string:
            escape_next = True
            i += 1
            continue

        if ch == '"' and not escape_next:
            in_string = not in_string
            i += 1
            continue

        if in_string:
            i += 1
            continue

        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return i

        i += 1

    return -1  # unbalanced


def split_top_level_annotations(text):
    """Split annotation block into individual top-level annotations.
    Returns list of (annotation_name, full_text) tuples."""
    annotations = []
    i = 0
    while i < len(text):
        # Find next @
        at_pos = text.find("@Niagara", i)
        if at_pos == -1:
            break

        # Find the opening paren
        paren_pos = text.find("(", at_pos)
        newline_pos = text.find("\n", at_pos)

        # Extract annotation name
        if paren_pos == -1 or (newline_pos != -1 and newline_pos < paren_pos):
            # No parens — simple annotation like @NiagaraType
            name_match = re.match(r'@(\w+)', text[at_pos:])
            if name_match:
                annotations.append((name_match.group(1), ""))
            i = newline_pos + 1 if newline_pos != -1 else len(text)
            continue

        name_match = re.match(r'@(\w+)', text[at_pos:])
        if not name_match:
            i = at_pos + 1
            continue

        ann_name = name_match.group(1)

        # Find balanced closing paren
        close_pos = find_balanced_parens(text, paren_pos)
        if close_pos == -1:
            i = at_pos + 1
            continue

        body = text[paren_pos + 1:close_pos]
        annotations.append((ann_name, body))
        i = close_pos + 1

    return annotations


def parse_key_value_fields(text):
    """Parse key=value fields from annotation body.
    Returns dict of field_name -> value_string."""
    fields = {}
    # Remove leading/trailing whitespace
    text = text.strip()
    if not text:
        return fields

    i = 0
    while i < len(text):
        # Skip whitespace
        while i < len(text) and text[i] in ' \t\n\r':
            i += 1
        if i >= len(text):
            break

        # Find key
        key_match = re.match(r'(\w+)\s*=\s*', text[i:])
        if not key_match:
            # Skip to next comma
            comma = text.find(",", i)
            if comma == -1:
                break
            i = comma + 1
            continue

        key = key_match.group(1)
        i += key_match.end()

        # Parse value — could be string, int, boolean, array {...}, or complex expression
        if i >= len(text):
            break

        value, end_pos = _parse_value(text, i)
        fields[key] = value
        i = end_pos

        # Skip comma
        while i < len(text) and text[i] in ' \t\n\r':
            i += 1
        if i < len(text) and text[i] == ',':
            i += 1

    return fields


def _parse_value(text, start):
    """Parse a single value starting at position start.
    Returns (value_string, end_position)."""
    i = start
    while i < len(text) and text[i] in ' \t\n\r':
        i += 1

    if i >= len(text):
        return ("", i)

    ch = text[i]

    # String literal
    if ch == '"':
        end = i + 1
        while end < len(text):
            if text[end] == '\\':
                end += 2
                continue
            if text[end] == '"':
                end += 1
                break
            end += 1
        return (text[i + 1:end - 1], end)

    # Array: {...}
    if ch == '{':
        depth = 0
        end = i
        in_str = False
        while end < len(text):
            c = text[end]
            if c == '"' and (end == 0 or text[end - 1] != '\\'):
                in_str = not in_str
            if not in_str:
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        end += 1
                        break
            end += 1
        return (text[i:end], end)

    # Nested annotation: @Something(...)
    if ch == '@':
        paren_pos = text.find("(", i)
        if paren_pos != -1:
            close = find_balanced_parens(text, paren_pos)
            if close != -1:
                return (text[i:close + 1], close + 1)
        # No parens
        end = i
        while end < len(text) and text[end] not in ',\n\r}':
            end += 1
        return (text[i:end].strip(), end)

    # Number, boolean, or identifier (e.g. "true", "false", "42", "BStatus.ok")
    end = i
    paren_depth = 0
    in_str = False
    while end < len(text):
        c = text[end]
        if c == '"' and (end == 0 or text[end - 1] != '\\'):
            in_str = not in_str
        if not in_str:
            if c == '(':
                paren_depth += 1
            elif c == ')':
                if paren_depth == 0:
                    break
                paren_depth -= 1
            elif c == ',' and paren_depth == 0:
                break
            elif c == '}' and paren_depth == 0:
                break
        end += 1

    return (text[i:end].strip(), end)


def parse_inner_annotations(body, ann_type):
    """Parse inner annotations from a wrapper like @NiagaraProperties({...}).
    ann_type is 'NiagaraProperty', 'NiagaraAction', etc."""
    results = []
    # The body is the content inside the outer parens
    # For @NiagaraProperties({@NiagaraProperty(...), @NiagaraProperty(...)})
    # body = "{@NiagaraProperty(...), @NiagaraProperty(...)}"

    # Find all @ann_type occurrences
    pattern = "@" + ann_type
    i = 0
    while i < len(body):
        pos = body.find(pattern, i)
        if pos == -1:
            break

        # Find the opening paren
        paren_start = body.find("(", pos)
        if paren_start == -1:
            i = pos + len(pattern)
            continue

        # Find balanced close
        close = find_balanced_parens(body, paren_start)
        if close == -1:
            i = pos + len(pattern)
            continue

        inner_body = body[paren_start + 1:close]
        fields = parse_key_value_fields(inner_body)
        results.append(fields)
        i = close + 1

    return results


def parse_facets(facets_str):
    """Parse facets from a string like '{@Facet("..."), @Facet(name="...", value="...")}'.
    Returns list of facet strings."""
    if not facets_str or not facets_str.strip():
        return []

    facets = []
    i = 0
    while i < len(facets_str):
        pos = facets_str.find("@Facet", i)
        if pos == -1:
            break

        paren_start = facets_str.find("(", pos)
        if paren_start == -1:
            break

        close = find_balanced_parens(facets_str, paren_start)
        if close == -1:
            break

        facet_body = facets_str[paren_start + 1:close].strip()
        # Facet can be either @Facet("expr") or @Facet(name="x", value="y")
        if facet_body.startswith('"'):
            # Simple form: @Facet("BFacets.make(...)")
            # Remove surrounding quotes and unescape inner quotes
            val = facet_body.strip('"').replace('\\"', '"')
            facets.append(val)
        else:
            # Named form: @Facet(name="x", value="y")
            fields = parse_key_value_fields(facet_body)
            if "name" in fields and "value" in fields:
                facets.append("{}={}".format(fields["name"], fields["value"]))
            elif "name" in fields:
                facets.append(fields["name"])
            else:
                facets.append(facet_body)

        i = close + 1

    return facets


def build_property_entry(fields):
    """Build a property dict from parsed fields."""
    entry = {"name": fields.get("name", "")}

    if "type" in fields:
        entry["type"] = fields["type"]
    if "defaultValue" in fields:
        entry["defaultValue"] = fields["defaultValue"]
    if "flags" in fields:
        try:
            entry["flags"] = int(fields["flags"])
        except (ValueError, TypeError):
            entry["flags"] = fields["flags"]
    if "override" in fields:
        entry["override"] = fields["override"].lower() == "true"
    if "facets" in fields:
        entry["facets"] = parse_facets(fields["facets"])

    return entry


def build_action_entry(fields):
    """Build an action dict from parsed fields."""
    entry = {"name": fields.get("name", "")}

    if "parameterType" in fields:
        entry["parameterType"] = fields["parameterType"]
    if "defaultValue" in fields:
        entry["defaultValue"] = fields["defaultValue"]
    if "returnType" in fields:
        entry["returnType"] = fields["returnType"]
    if "flags" in fields:
        try:
            entry["flags"] = int(fields["flags"])
        except (ValueError, TypeError):
            entry["flags"] = fields["flags"]

    return entry


def build_topic_entry(fields):
    """Build a topic dict from parsed fields."""
    entry = {"name": fields.get("name", "")}

    if "eventType" in fields:
        entry["eventType"] = fields["eventType"]
    if "flags" in fields:
        try:
            entry["flags"] = int(fields["flags"])
        except (ValueError, TypeError):
            entry["flags"] = fields["flags"]

    return entry


def parse_file_annotations(filepath):
    """Parse all Niagara annotations from a Java file.
    Returns None if the file does not have @NiagaraType.
    Returns dict with properties, actions, topics if it does."""
    header = read_header(filepath)
    if header is None:
        return None

    # Quick check: must have @NiagaraType
    if "@NiagaraType" not in header:
        return None

    block = extract_annotation_block(header)
    if block is None:
        return None

    top_anns = split_top_level_annotations(block)

    has_niagara_type = False
    properties = []
    actions = []
    topics = []

    for ann_name, ann_body in top_anns:
        if ann_name == "NiagaraType":
            has_niagara_type = True

        elif ann_name == "NiagaraProperty":
            fields = parse_key_value_fields(ann_body)
            if fields.get("name"):
                properties.append(build_property_entry(fields))

        elif ann_name == "NiagaraProperties":
            inner = parse_inner_annotations(ann_body, "NiagaraProperty")
            for fields in inner:
                if fields.get("name"):
                    properties.append(build_property_entry(fields))

        elif ann_name == "NiagaraAction":
            fields = parse_key_value_fields(ann_body)
            if fields.get("name"):
                actions.append(build_action_entry(fields))

        elif ann_name == "NiagaraActions":
            inner = parse_inner_annotations(ann_body, "NiagaraAction")
            for fields in inner:
                if fields.get("name"):
                    actions.append(build_action_entry(fields))

        elif ann_name == "NiagaraTopic":
            fields = parse_key_value_fields(ann_body)
            if fields.get("name"):
                topics.append(build_topic_entry(fields))

    if not has_niagara_type:
        return None

    result = {}
    if properties:
        result["properties"] = properties
    if actions:
        result["actions"] = actions
    if topics:
        result["topics"] = topics

    return result


# ---------------------------------------------------------------------------
# Index builder
# ---------------------------------------------------------------------------

def build_annotations_index(base_dir):
    """Build the annotations index from all top-level classes."""
    index_dir = os.path.join(base_dir, "indexes")

    # Load class-index for catalog of top-level classes
    ci_path = os.path.join(index_dir, "class-index.json")
    if not os.path.isfile(ci_path):
        print("ERROR: class-index.json not found. Run build_class_index.py first.")
        sys.exit(1)

    print("Loading class-index.json...")
    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = json.load(f)

    classes = ci_data.get("classes", {})

    # Load module-inventory for source base path
    inv_path = os.path.join(index_dir, "module-inventory.json")
    if not os.path.isfile(inv_path):
        print("ERROR: module-inventory.json not found.")
        sys.exit(1)

    with open(inv_path, "r", encoding="utf-8") as f:
        inv_data = json.load(f)

    source_base = inv_data.get("_meta", {}).get("source", "")
    if not source_base or not os.path.isdir(source_base):
        print("ERROR: Source base '{}' not found.".format(source_base))
        sys.exit(1)

    print("Source base: {}".format(source_base))

    # Collect all top-level class entries with paths
    entries = []
    for class_name, class_list in classes.items():
        for entry in class_list:
            if entry.get("outer_class") is not None:
                continue  # skip inner classes
            path = entry.get("path", "")
            module = entry.get("module", "")
            if path:
                entries.append((class_name, module, path))

    print("Top-level classes to scan: {:,}".format(len(entries)))

    # Process each file
    start_time = time.time()
    niagara_types = {}  # class_name -> {module, properties, actions, topics}
    property_types = {}  # type -> [class.propName, ...]
    action_names = {}  # action_name -> [{class, module}, ...]

    processed = 0
    skipped = 0
    errors = 0
    with_props = 0
    with_actions = 0
    with_topics = 0
    total_props = 0
    total_actions = 0
    total_topics = 0

    for class_name, module, rel_path in entries:
        full_path = os.path.join(source_base, rel_path)
        if not os.path.isfile(full_path):
            skipped += 1
            continue

        try:
            result = parse_file_annotations(full_path)
        except Exception as e:
            errors += 1
            continue

        if result is None:
            processed += 1
            continue

        processed += 1

        # Build niagara_types entry
        nt_entry = {"module": module}
        if "properties" in result:
            nt_entry["properties"] = result["properties"]
            with_props += 1
            total_props += len(result["properties"])

            # Build property_types index
            for prop in result["properties"]:
                ptype = prop.get("type", "")
                if ptype:
                    key = ptype
                    ref = "{}.{}".format(class_name, prop["name"])
                    if key not in property_types:
                        property_types[key] = []
                    property_types[key].append(ref)

        if "actions" in result:
            nt_entry["actions"] = result["actions"]
            with_actions += 1
            total_actions += len(result["actions"])

            # Build action_names index
            for act in result["actions"]:
                aname = act.get("name", "")
                if aname:
                    aref = {"class": class_name, "module": module}
                    if aname not in action_names:
                        action_names[aname] = []
                    action_names[aname].append(aref)

        if "topics" in result:
            nt_entry["topics"] = result["topics"]
            with_topics += 1
            total_topics += len(result["topics"])

        niagara_types[class_name] = nt_entry

        # Progress
        if processed % 5000 == 0:
            elapsed = time.time() - start_time
            print("  {:,} processed, {:,} Niagara types found ({:.1f}s)...".format(
                processed, len(niagara_types), elapsed))

    elapsed = time.time() - start_time

    # Sort property_types by count descending
    property_types_sorted = {}
    for ptype in sorted(property_types.keys(), key=lambda k: len(property_types[k]), reverse=True):
        property_types_sorted[ptype] = property_types[ptype]

    # Sort action_names by count descending
    action_names_sorted = {}
    for aname in sorted(action_names.keys(), key=lambda k: len(action_names[k]), reverse=True):
        action_names_sorted[aname] = action_names[aname]

    # Build output
    index = {
        "_meta": {
            "description": "Niagara annotations index (@NiagaraType, @NiagaraProperty, @NiagaraAction, @NiagaraTopic)",
            "total_niagara_types": len(niagara_types),
            "with_properties": with_props,
            "with_actions": with_actions,
            "with_topics": with_topics,
            "total_properties": total_props,
            "total_actions": total_actions,
            "total_topics": total_topics,
            "unique_property_types": len(property_types_sorted),
            "unique_action_names": len(action_names_sorted),
            "files_processed": processed,
            "files_skipped": skipped,
            "files_errored": errors,
            "build_time_sec": round(elapsed, 1),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "niagara_types": niagara_types,
        "property_types": property_types_sorted,
        "action_names": action_names_sorted,
    }

    # Write output
    out_path = os.path.join(index_dir, "annotations-index.json")
    print("\nWriting {}...".format(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, separators=(",", ":"), ensure_ascii=False)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)

    print("\n" + "=" * 60)
    print("ANNOTATIONS INDEX — BUILD COMPLETE")
    print("=" * 60)
    print("")
    print("  Files processed:         {:>7,}".format(processed))
    print("  Files skipped:           {:>7,}".format(skipped))
    print("  Files errored:           {:>7,}".format(errors))
    print("")
    print("  Niagara types:           {:>7,}".format(len(niagara_types)))
    print("  With properties:         {:>7,}".format(with_props))
    print("  With actions:            {:>7,}".format(with_actions))
    print("  With topics:             {:>7,}".format(with_topics))
    print("")
    print("  Total properties:        {:>7,}".format(total_props))
    print("  Total actions:           {:>7,}".format(total_actions))
    print("  Total topics:            {:>7,}".format(total_topics))
    print("  Unique property types:   {:>7,}".format(len(property_types_sorted)))
    print("  Unique action names:     {:>7,}".format(len(action_names_sorted)))
    print("")
    print("  Index size:              {:>7.1f} MB".format(size_mb))
    print("  Build time:              {:>7.1f}s".format(elapsed))
    print("")

    # Top 10 property types
    top_pt = list(property_types_sorted.items())[:10]
    if top_pt:
        print("  Top 10 property types:")
        for ptype, refs in top_pt:
            print("    {:30s} {:>5,} usages".format(ptype, len(refs)))
        print("")

    # Top 10 action names
    top_an = list(action_names_sorted.items())[:10]
    if top_an:
        print("  Top 10 action names:")
        for aname, refs in top_an:
            print("    {:30s} {:>5,} classes".format(aname, len(refs)))
        print("")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Niagara annotations index (Phase 7)")
    parser.add_argument(
        "--base-dir", "-d",
        help="Base directory (auto-detected if omitted)")

    args = parser.parse_args()

    if args.base_dir:
        base_dir = args.base_dir
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)

    if not os.path.isdir(os.path.join(base_dir, "indexes")):
        print("ERROR: indexes/ directory not found in {}".format(base_dir))
        sys.exit(1)

    build_annotations_index(base_dir)


if __name__ == "__main__":
    main()
