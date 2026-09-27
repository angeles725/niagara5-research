"""
Extra commands for Module Navigator (Phase 11).

Commands:
  strings          Search for string literals across source code
  resources        List non-Java resources in module JARs
  trace-type       Map Niagara type spec to implementing Java class
  version-diff     Compare two class-index files to find changes
"""

import json
import os
import re
import sys
import zipfile


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_json_path(path):
    """Load a JSON file by full path."""
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_json(base_dir, filename):
    return _load_json_path(os.path.join(base_dir, "indexes", filename))


def _get_source_root(ci_data):
    return ci_data.get("_meta", {}).get("source", "")


def _read_source(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except (IOError, OSError):
        return []


# ---------------------------------------------------------------------------
# strings: search string literals in source code
# ---------------------------------------------------------------------------

# Regex to match Java string literals (handles basic escapes)
_STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def cmd_strings(base_dir, pattern, module_filter=None, class_filter=None, limit=30):
    """Search for string literals matching a pattern across source files."""
    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    source_root = _get_source_root(ci_data)
    if not source_root:
        print("ERROR: source root not found.")
        return

    classes = ci_data.get("classes", {})

    try:
        pat = re.compile(pattern, re.IGNORECASE)
    except re.error:
        pat = re.compile(re.escape(pattern), re.IGNORECASE)

    print("")
    print("  " + "=" * 65)
    print("  STRING SEARCH: \"{}\"".format(pattern))
    if module_filter:
        print("  Module: {}".format(module_filter))
    if class_filter:
        print("  Class: {}".format(class_filter))
    print("  " + "=" * 65)
    print("")

    results = []
    files_scanned = 0

    sys.stdout.write("  Scanning...")
    sys.stdout.flush()

    for class_name, entries in classes.items():
        for entry in entries:
            if entry.get("outer_class") is not None:
                continue
            if entry.get("zkm"):
                continue
            if module_filter and entry["module"] != module_filter:
                continue
            if class_filter and class_name != class_filter:
                continue

            filepath = os.path.join(source_root, entry["path"])
            if not os.path.isfile(filepath):
                continue

            lines = _read_source(filepath)
            files_scanned += 1

            for i, line in enumerate(lines, 1):
                # Skip import/package lines
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("package "):
                    continue

                for m in _STRING_RE.finditer(line):
                    string_val = m.group(1)
                    if pat.search(string_val):
                        results.append((class_name, entry["module"], i, string_val, stripped))
                        if len(results) >= limit * 10:
                            break
                if len(results) >= limit * 10:
                    break
            if len(results) >= limit * 10:
                break
        if len(results) >= limit * 10:
            break

    print(" done ({:,} files, {:,} matches)".format(files_scanned, len(results)))
    print("")

    # Deduplicate by string value, keep first occurrence
    seen = {}
    unique = []
    for cls, mod, line_no, val, full_line in results:
        key = val
        if key not in seen:
            seen[key] = (cls, mod, line_no, full_line)
            unique.append((val, cls, mod, line_no, full_line))

    shown = unique[:limit]
    print("  RESULTS ({:,} unique strings, showing {})".format(len(unique), len(shown)))
    print("  " + "-" * 65)

    for val, cls, mod, line_no, full_line in shown:
        display = val if len(val) <= 80 else val[:77] + "..."
        print("    \"{}\"".format(display))
        print("      {}:{} ({})".format(cls, line_no, mod))

    if len(unique) > limit:
        print("")
        print("  ... and {:,} more unique strings".format(len(unique) - limit))
    print("")


# ---------------------------------------------------------------------------
# resources: list non-Java resources in module JARs
# ---------------------------------------------------------------------------

def cmd_resources(base_dir, module_name, type_filter=None, limit=100):
    """List non-class resources inside a module JAR."""
    # Find JAR path
    niagara_home = os.path.dirname(base_dir)
    jar_name = module_name if module_name.endswith(".jar") else module_name + ".jar"
    jar_path = os.path.join(niagara_home, "modules", jar_name)

    if not os.path.isfile(jar_path):
        print("  JAR not found: {}".format(jar_path))
        print("  Try: modules --has-code")
        return

    print("")
    print("  " + "=" * 65)
    print("  RESOURCES: {}".format(jar_name))
    print("  " + "=" * 65)
    print("")

    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            all_entries = zf.namelist()
    except (zipfile.BadZipFile, IOError) as e:
        print("  ERROR reading JAR: {}".format(e))
        return

    # Separate classes from resources
    class_files = []
    resources = []
    for entry in all_entries:
        if entry.endswith("/"):
            continue  # skip directories
        if entry.endswith(".class"):
            class_files.append(entry)
        else:
            resources.append(entry)

    # Group resources by extension
    by_ext = {}
    for r in resources:
        ext = os.path.splitext(r)[1].lower() if "." in r else "(none)"
        by_ext.setdefault(ext, []).append(r)

    # Apply type filter
    if type_filter:
        tf = type_filter if type_filter.startswith(".") else "." + type_filter
        filtered = by_ext.get(tf.lower(), [])
        print("  Filter: {}".format(tf))
        print("  Matches: {:,}".format(len(filtered)))
        print("")
        for r in filtered[:limit]:
            print("    {}".format(r))
        if len(filtered) > limit:
            print("    ... and {} more".format(len(filtered) - limit))
        print("")
        return

    print("  Total entries:   {:>6,}".format(len(all_entries)))
    print("  Class files:     {:>6,}".format(len(class_files)))
    print("  Resources:       {:>6,}".format(len(resources)))
    print("")

    print("  BY EXTENSION:")
    for ext in sorted(by_ext.keys(), key=lambda x: -len(by_ext[x])):
        items = by_ext[ext]
        print("    {:15s} {:>5,} files".format(ext, len(items)))

    print("")
    print("  ALL RESOURCES ({}, showing {}):".format(len(resources), min(limit, len(resources))))
    print("  " + "-" * 65)

    for r in resources[:limit]:
        print("    {}".format(r))
    if len(resources) > limit:
        print("    ... and {} more".format(len(resources) - limit))

    print("")


# ---------------------------------------------------------------------------
# trace-type: map Niagara type spec to Java class
# ---------------------------------------------------------------------------

def cmd_trace_type(base_dir, type_spec):
    """Map a Niagara type specification to its implementing Java class.

    Type formats:
      - "control:NumericWritable"  → BNumericWritable in control-rt
      - "alarm:AlarmService"       → BAlarmService in alarm-rt
      - "BNumericWritable"         → direct class lookup
    """
    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    classes = ci_data.get("classes", {})
    inv_data = _load_json(base_dir, "module-inventory.json")
    inv = inv_data.get("modules", {}) if inv_data else {}

    print("")
    print("  " + "=" * 65)
    print("  TRACE TYPE: {}".format(type_spec))
    print("  " + "=" * 65)
    print("")

    # Parse type spec
    if ":" in type_spec:
        module_hint, type_name = type_spec.split(":", 1)
    else:
        module_hint = None
        type_name = type_spec

    # Try with and without B prefix (always try both — "BooleanWritable" maps to "BBooleanWritable")
    candidates = [type_name, "B" + type_name]
    if type_name.startswith("B"):
        # Also try without B prefix in case user passed "BAlarmService"
        candidates.append(type_name[1:])

    found = []
    for cand in candidates:
        if cand in classes:
            for entry in classes[cand]:
                if entry.get("outer_class") is not None:
                    continue
                # If module hint given, prefer matching module
                if module_hint:
                    mod = entry["module"]
                    if module_hint in mod or mod.startswith(module_hint):
                        found.insert(0, (cand, entry))
                    else:
                        found.append((cand, entry))
                else:
                    found.append((cand, entry))

    if not found:
        # Try case-insensitive
        for cand in candidates:
            cand_lower = cand.lower()
            for k, entries in classes.items():
                if k.lower() == cand_lower:
                    for entry in entries:
                        if entry.get("outer_class") is None:
                            found.append((k, entry))

    if not found:
        print("  Type '{}' not found.".format(type_spec))
        print("  Tried: {}".format(", ".join(candidates)))
        print("  Try: search '*{}*'".format(type_name))
        return

    print("  RESOLUTION:")
    for class_name, entry in found[:5]:
        print("")
        print("    Class:     {}".format(class_name))
        print("    Package:   {}".format(entry.get("package", "")))
        print("    Module:    {}".format(entry["module"]))
        print("    Kind:      {}".format(entry["kind"]))
        if entry.get("extends"):
            print("    Extends:   {}".format(entry["extends"]))
        if entry.get("implements"):
            print("    Implements: {}".format(", ".join(entry["implements"])))
        print("    Lines:     {:,}".format(entry.get("lines", 0)))
        print("    Path:      {}".format(entry["path"]))

        # Show module info
        mod_key = entry["module"]
        if mod_key in inv:
            mod = inv[mod_key]
            print("    JAR:       {}".format(mod.get("jar", "")))

    # Show annotations if available
    ann_data = _load_json(base_dir, "annotations-index.json")
    if ann_data and found:
        class_name = found[0][0]
        ann_types = ann_data.get("niagara_types", {})
        if class_name in ann_types:
            ann_entry = ann_types[class_name]
            if isinstance(ann_entry, list):
                ann_entry = ann_entry[0]
            props = ann_entry.get("properties", [])
            acts = ann_entry.get("actions", [])
            if props or acts:
                print("")
                print("  NIAGARA SLOTS:")
                for p in props[:10]:
                    name = p.get("name", "?")
                    ptype = p.get("type", "?")
                    print("    property {:30s} {}".format(name, ptype))
                if len(props) > 10:
                    print("    ... and {} more properties".format(len(props) - 10))
                for a in acts[:5]:
                    aname = a.get("name", "?")
                    print("    action   {}".format(aname))

    if len(found) > 1:
        print("")
        print("  NOTE: {} matches found. Showing best match first.".format(len(found)))

    print("")
    print("  Next steps:")
    if found:
        cn = found[0][0]
        print("    profile {}".format(cn))
        print("    source {} --code".format(cn))
        print("    patch-plan {}".format(cn))
    print("")


# ---------------------------------------------------------------------------
# version-diff: compare two class-index files
# ---------------------------------------------------------------------------

def cmd_version_diff(base_dir, other_index_path, limit=50):
    """Compare current class-index with another one to find changes.

    other_index_path: path to another class-index.json (e.g., from a different N4 version)
    """
    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    other_data = _load_json_path(other_index_path)
    if not other_data:
        print("  ERROR: Cannot load '{}'.".format(other_index_path))
        return

    classes_a = ci_data.get("classes", {})
    classes_b = other_data.get("classes", {})

    meta_a = ci_data.get("_meta", {})
    meta_b = other_data.get("_meta", {})

    # Build FQN sets (top-level only)
    def build_fqn_map(classes):
        fqn_map = {}  # fqn -> (name, entry)
        for name, entries in classes.items():
            for entry in entries:
                if entry.get("outer_class") is not None:
                    continue
                pkg = entry.get("package", "")
                fqn = "{}.{}".format(pkg, name) if pkg else name
                fqn_map[fqn] = (name, entry)
        return fqn_map

    fqn_a = build_fqn_map(classes_a)
    fqn_b = build_fqn_map(classes_b)

    set_a = set(fqn_a.keys())
    set_b = set(fqn_b.keys())

    added = set_b - set_a
    removed = set_a - set_b
    common = set_a & set_b

    # Find changed classes (different line count as proxy)
    changed = []
    for fqn in common:
        name_a, entry_a = fqn_a[fqn]
        name_b, entry_b = fqn_b[fqn]
        lines_a = entry_a.get("lines", 0)
        lines_b = entry_b.get("lines", 0)
        if lines_a != lines_b:
            changed.append((fqn, name_a, lines_a, lines_b))

    print("")
    print("  " + "=" * 65)
    print("  VERSION DIFF")
    print("  " + "=" * 65)
    print("")
    print("  Current:  {:,} classes ({})".format(
        len(fqn_a), meta_a.get("source", "?")[:60]))
    print("  Other:    {:,} classes ({})".format(
        len(fqn_b), meta_b.get("source", "?")[:60]))
    print("")
    print("  SUMMARY:")
    print("    Added:     {:>6,}  (in other, not in current)".format(len(added)))
    print("    Removed:   {:>6,}  (in current, not in other)".format(len(removed)))
    print("    Changed:   {:>6,}  (different line count)".format(len(changed)))
    print("    Unchanged: {:>6,}".format(len(common) - len(changed)))

    if added:
        print("")
        print("  ADDED ({}, showing {}):".format(len(added), min(limit, len(added))))
        for fqn in sorted(added)[:limit]:
            name, entry = fqn_b[fqn]
            print("    + {:50s} {:>5}L  {}".format(
                name, entry.get("lines", 0), entry["module"]))

    if removed:
        print("")
        print("  REMOVED ({}, showing {}):".format(len(removed), min(limit, len(removed))))
        for fqn in sorted(removed)[:limit]:
            name, entry = fqn_a[fqn]
            print("    - {:50s} {:>5}L  {}".format(
                name, entry.get("lines", 0), entry["module"]))

    if changed:
        print("")
        print("  CHANGED ({}, showing {}):".format(len(changed), min(limit, len(changed))))
        changed.sort(key=lambda x: abs(x[3] - x[2]), reverse=True)
        for fqn, name, lines_a, lines_b in changed[:limit]:
            delta = lines_b - lines_a
            sign = "+" if delta > 0 else ""
            print("    ~ {:50s} {}L -> {}L ({}{})".format(
                name, lines_a, lines_b, sign, delta))

    print("")
