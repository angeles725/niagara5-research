"""
Method index commands for Module Navigator (Phase 5).

Commands:
  method <name> [-n N]              All classes that define this method
  method <name> --module <mod>      Filter by module
  method <name> --class <cls>       Show full signature in that class
  methods <class> [-n N]            List all methods of a class
  methods <class> --public          Only public methods
  methods <class> --grep <pat>      Filter methods by regex pattern
"""

import json
import os
import re


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

_method_index_cache = None


def load_method_index(base_dir):
    """Load method-index.json (or use cached version from REPL)."""
    global _method_index_cache
    if _method_index_cache is not None:
        return _method_index_cache

    path = os.path.join(base_dir, "indexes", "method-index.json")
    if not os.path.isfile(path):
        print("ERROR: method-index.json not found.")
        print("Run: python tools/build_method_index.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# ---------------------------------------------------------------------------
# method command
# ---------------------------------------------------------------------------

def cmd_method(base_dir, name, module_filter=None, class_filter=None, limit=50):
    """Show classes that define a given method."""
    mi = load_method_index(base_dir)
    if not mi:
        return

    methods = mi.get("methods", {})

    if class_filter:
        _show_method_in_class(name, class_filter, methods)
        return

    entries = methods.get(name, [])

    if module_filter:
        entries = [e for e in entries if e["module"] == module_filter]

    if not entries:
        if name in methods:
            print("  Method '{}' exists but not in module '{}'.".format(
                name, module_filter))
            print("  Total definitions: {}".format(len(methods[name])))
        else:
            print("  Method '{}' not found in index.".format(name))
            # Suggest partial matches
            partial = [m for m in methods if name.lower() in m.lower()]
            if partial:
                shown = partial[:10]
                print("  Partial matches: {}".format(", ".join(shown)))
                if len(partial) > 10:
                    print("  ... and {} more".format(len(partial) - 10))
        return

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  METHOD: {}{} ({} definitions)".format(name, scope, len(entries)))
    print("")
    print("  {:35s}  {:25s}  {:>5s}  {}".format(
        "CLASS", "MODULE", "LINE", "SIGNATURE"))
    print("  " + "-" * 110)

    shown = 0
    for e in entries:
        if shown >= limit:
            break
        print("  {:35s}  {:25s}  {:>5d}  {}".format(
            e["class"], e["module"], e["line"], e["signature"]))
        shown += 1

    if len(entries) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(entries) - limit, len(entries)))
    print("")


def _show_method_in_class(name, class_filter, methods):
    """Show detailed method signature in a specific class."""
    entries = methods.get(name, [])
    matches = [e for e in entries if e["class"] == class_filter]

    if not matches:
        print("  Method '{}' not found in class '{}'.".format(name, class_filter))
        return

    print("")
    for e in matches:
        print("  {}.{}".format(e["class"], name))
        print("    Module:      {}".format(e["module"]))
        print("    Signature:   {}".format(e["signature"]))
        print("    Line:        {}".format(e["line"]))
        print("    Modifiers:   {}".format(", ".join(e["modifiers"]) if e["modifiers"] else "(package-private)"))
        print("    Return type: {}".format(e["return_type"] if e["return_type"] else "(constructor)"))
        print("    Params:      {}".format(", ".join(e["params"]) if e["params"] else "(none)"))
        print("")


# ---------------------------------------------------------------------------
# methods command
# ---------------------------------------------------------------------------

def cmd_methods(base_dir, class_name, public_only=False, grep_pattern=None, limit=50):
    """List all methods of a class."""
    mi = load_method_index(base_dir)
    if not mi:
        return

    class_methods = mi.get("class_methods", {})
    methods = mi.get("methods", {})

    if class_name not in class_methods:
        # Try case-insensitive match
        found = None
        lower = class_name.lower()
        for k in class_methods:
            if k.lower() == lower:
                found = k
                break
        if found:
            class_name = found
        else:
            print("  Class '{}' not found in method index.".format(class_name))
            partial = [c for c in class_methods if class_name.lower() in c.lower()]
            if partial:
                shown = sorted(partial)[:10]
                print("  Partial matches: {}".format(", ".join(shown)))
                if len(partial) > 10:
                    print("  ... and {} more".format(len(partial) - 10))
            return

    method_names = class_methods[class_name]

    # Collect full entries for this class
    results = []
    for mname in method_names:
        if mname in methods:
            for e in methods[mname]:
                if e["class"] == class_name:
                    results.append((mname, e))

    # Apply filters
    if public_only:
        results = [(m, e) for m, e in results if "public" in e["modifiers"]]

    if grep_pattern:
        try:
            pat = re.compile(grep_pattern, re.IGNORECASE)
        except re.error as err:
            print("  ERROR: Invalid regex: {}".format(err))
            return
        results = [(m, e) for m, e in results
                    if pat.search(m) or pat.search(e["signature"])]

    # Sort by line number
    results.sort(key=lambda x: x[1]["line"])

    # Display
    filters = []
    if public_only:
        filters.append("public only")
    if grep_pattern:
        filters.append("grep /{}/ ".format(grep_pattern))
    filter_str = " ({})".format(", ".join(filters)) if filters else ""

    print("")
    print("  METHODS of {}{}: {} methods".format(
        class_name, filter_str, len(results)))
    print("")

    if not results:
        print("    (no matching methods)")
        print("")
        return

    print("  {:>5s}  {:4s}  {}".format("LINE", "MOD", "SIGNATURE"))
    print("  " + "-" * 90)

    shown = 0
    for mname, e in results:
        if shown >= limit:
            break

        # Short modifier indicator
        mod_flags = ""
        if "public" in e["modifiers"]:
            mod_flags += "+"
        elif "protected" in e["modifiers"]:
            mod_flags += "#"
        elif "private" in e["modifiers"]:
            mod_flags += "-"
        else:
            mod_flags += "~"
        if "static" in e["modifiers"]:
            mod_flags += "S"
        if "abstract" in e["modifiers"]:
            mod_flags += "A"
        if "final" in e["modifiers"]:
            mod_flags += "F"

        print("  {:>5d}  {:4s}  {}".format(e["line"], mod_flags, e["signature"]))
        shown += 1

    if len(results) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(results) - limit, len(results)))
    print("")
    print("  Modifiers: +=public  #=protected  -=private  ~=package  S=static  A=abstract  F=final")
    print("")
