"""
Field index commands for Module Navigator (Phase 13).

Commands:
  fields <class> [-n N]            List all fields of a class
  fields <class> --static          Only static fields/constants
  fields <class> --public          Only public fields
  field <name> [-n N]              Classes that define a field with this name
  field <name> --module <mod>      Filter by module
"""

import json
import os
import re


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

_field_index_cache = None


def load_field_index(base_dir):
    """Load field-index.json (or use cached version from REPL)."""
    global _field_index_cache
    if _field_index_cache is not None:
        return _field_index_cache

    path = os.path.join(base_dir, "indexes", "field-index.json")
    if not os.path.isfile(path):
        print("ERROR: field-index.json not found.")
        print("Run: python tools/build_field_index.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# ---------------------------------------------------------------------------
# field command — search by field name across all classes
# ---------------------------------------------------------------------------

def cmd_field(base_dir, name, module_filter=None, limit=50):
    """Show classes that define a field with the given name."""
    fi = load_field_index(base_dir)
    if not fi:
        return

    fields = fi.get("fields", {})

    entries = fields.get(name, [])

    if module_filter:
        entries = [e for e in entries if e["module"] == module_filter]

    if not entries:
        if name in fields:
            print("  Field '{}' exists but not in module '{}'.".format(
                name, module_filter))
            print("  Total definitions: {}".format(len(fields[name])))
        else:
            print("  Field '{}' not found in index.".format(name))
            # Suggest partial matches
            partial = [f for f in fields if name.lower() in f.lower()]
            if partial:
                shown = sorted(partial)[:10]
                print("  Partial matches: {}".format(", ".join(shown)))
                if len(partial) > 10:
                    print("  ... and {} more".format(len(partial) - 10))
        return

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  FIELD: {}{} ({} definitions)".format(name, scope, len(entries)))
    print("")
    print("  {:35s}  {:25s}  {:>5s}  {:4s}  {}".format(
        "CLASS", "MODULE", "LINE", "MOD", "TYPE"))
    print("  " + "-" * 110)

    shown = 0
    for e in entries:
        if shown >= limit:
            break

        # Short modifier indicator
        mod_flags = _mod_flags(e.get("modifiers", []))

        print("  {:35s}  {:25s}  {:>5d}  {:4s}  {}".format(
            e["class"], e["module"], e["line"], mod_flags,
            e.get("type", "")))
        shown += 1

    if len(entries) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(entries) - limit, len(entries)))
    print("")


# ---------------------------------------------------------------------------
# fields command — list fields of a specific class
# ---------------------------------------------------------------------------

def cmd_fields(base_dir, class_name, static_only=False, public_only=False,
               grep_pattern=None, limit=50):
    """List all fields of a class."""
    fi = load_field_index(base_dir)
    if not fi:
        return

    class_fields = fi.get("class_fields", {})
    fields = fi.get("fields", {})

    if class_name not in class_fields:
        # Try case-insensitive match
        found = None
        lower = class_name.lower()
        for k in class_fields:
            if k.lower() == lower:
                found = k
                break
        if found:
            class_name = found
        else:
            print("  Class '{}' not found in field index.".format(class_name))
            partial = [c for c in class_fields if class_name.lower() in c.lower()]
            if partial:
                shown = sorted(partial)[:10]
                print("  Partial matches: {}".format(", ".join(shown)))
                if len(partial) > 10:
                    print("  ... and {} more".format(len(partial) - 10))
            return

    field_names = class_fields[class_name]

    # Collect full entries for this class
    results = []
    for fname in field_names:
        if fname in fields:
            for e in fields[fname]:
                if e["class"] == class_name:
                    results.append((fname, e))

    # Apply filters
    if static_only:
        results = [(f, e) for f, e in results if "static" in e.get("modifiers", [])]

    if public_only:
        results = [(f, e) for f, e in results if "public" in e.get("modifiers", [])]

    if grep_pattern:
        try:
            pat = re.compile(grep_pattern, re.IGNORECASE)
        except re.error as err:
            print("  ERROR: Invalid regex: {}".format(err))
            return
        results = [(f, e) for f, e in results
                    if pat.search(f) or pat.search(e.get("type", ""))]

    # Sort by line number
    results.sort(key=lambda x: x[1]["line"])

    # Display
    filters = []
    if static_only:
        filters.append("static only")
    if public_only:
        filters.append("public only")
    if grep_pattern:
        filters.append("grep /{}/".format(grep_pattern))
    filter_str = " ({})".format(", ".join(filters)) if filters else ""

    print("")
    print("  FIELDS of {}{}: {} fields".format(
        class_name, filter_str, len(results)))
    print("")

    if not results:
        print("    (no matching fields)")
        print("")
        return

    print("  {:>5s}  {:4s}  {:30s}  {:30s}  {}".format(
        "LINE", "MOD", "TYPE", "NAME", "INIT"))
    print("  " + "-" * 100)

    shown = 0
    for fname, e in results:
        if shown >= limit:
            break

        mod_flags = _mod_flags(e.get("modifiers", []))
        init_val = e.get("init", "")
        if len(init_val) > 40:
            init_val = init_val[:37] + "..."

        print("  {:>5d}  {:4s}  {:30s}  {:30s}  {}".format(
            e["line"], mod_flags,
            _truncate(e.get("type", ""), 30),
            _truncate(fname, 30),
            init_val))
        shown += 1

    if len(results) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(results) - limit, len(results)))
    print("")
    print("  Modifiers: +=public  #=protected  -=private  ~=package  S=static  F=final  V=volatile  T=transient")
    print("")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mod_flags(modifiers):
    """Build short modifier flags string."""
    flags = ""
    if "public" in modifiers:
        flags += "+"
    elif "protected" in modifiers:
        flags += "#"
    elif "private" in modifiers:
        flags += "-"
    else:
        flags += "~"
    if "static" in modifiers:
        flags += "S"
    if "final" in modifiers:
        flags += "F"
    if "volatile" in modifiers:
        flags += "V"
    if "transient" in modifiers:
        flags += "T"
    return flags


def _truncate(s, max_len):
    """Truncate string to max_len with ellipsis."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."
