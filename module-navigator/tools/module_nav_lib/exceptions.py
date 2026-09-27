"""
Exception flow commands for Module Navigator (Phase 19).

Commands:
  throws <class> [-n N]             Methods that declare throws in a class
  throws <class> --module <mod>     Filter by module (for duplicate class names)
  catches <exception> [-n N]        Classes/methods that catch this exception
  catches <exception> --module <mod> Filter by module
"""

import json
import os


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

_exceptions_index_cache = None


def load_exceptions_index(base_dir):
    """Load exceptions-index.json (or use cached version from REPL)."""
    global _exceptions_index_cache
    if _exceptions_index_cache is not None:
        return _exceptions_index_cache

    path = os.path.join(base_dir, "indexes", "exceptions-index.json")
    if not os.path.isfile(path):
        print("ERROR: exceptions-index.json not found.")
        print("Run: python tools/build_exceptions_index.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# ---------------------------------------------------------------------------
# throws command — show what a class's methods throw
# ---------------------------------------------------------------------------

def cmd_throws(base_dir, class_name, module_filter=None, limit=50):
    """Show methods of a class that declare throws."""
    ei = load_exceptions_index(base_dir)
    if not ei:
        return

    class_throws = ei.get("class_throws", {})
    thrown_map = ei.get("thrown", {})

    # Look up class
    entry = class_throws.get(class_name)

    if entry and module_filter and entry.get("module") != module_filter:
        entry = None

    if not entry:
        # If class_name is an exception type, show who throws it
        if class_name in thrown_map:
            _show_thrown_exception(class_name, thrown_map[class_name],
                                  module_filter, limit)
            return

        # Try partial match on class names
        partial = [k for k in class_throws if class_name.lower() in k.lower()]
        if partial:
            print("")
            print("  Class '{}' not found. Partial matches:".format(class_name))
            for p in sorted(partial)[:10]:
                e = class_throws[p]
                print("    {} ({}) — {} throws".format(
                    p, e["module"], len(e["throws"])))
            if len(partial) > 10:
                print("    ... and {} more".format(len(partial) - 10))
        else:
            # Maybe it's an exception type — check thrown map
            partial_ex = [k for k in thrown_map if class_name.lower() in k.lower()]
            if partial_ex:
                print("")
                print("  No class '{}' with throws. Did you mean an exception type?".format(
                    class_name))
                for p in sorted(partial_ex)[:10]:
                    print("    catches {} — use: catches {}".format(p, p))
            else:
                print("  Class '{}' has no throws declarations.".format(class_name))
        return

    module = entry["module"]
    throws = entry["throws"]

    print("")
    print("  THROWS: {} ({})".format(class_name, module))
    print("  {} methods with throws declarations".format(len(throws)))
    print("")

    # Collect unique exception types
    all_exceptions = set()
    for t in throws:
        all_exceptions.update(t["exceptions"])

    print("  {:30s}  {:>5s}  {}".format("METHOD", "LINE", "EXCEPTIONS"))
    print("  " + "-" * 75)

    shown = 0
    for t in sorted(throws, key=lambda x: x["line"]):
        if shown >= limit:
            remaining = len(throws) - shown
            print("  ... and {} more (use -n {} to see all)".format(
                remaining, len(throws)))
            break

        exc_str = ", ".join(t["exceptions"])
        print("  {:30s}  {:>5d}  {}".format(
            t["method"], t["line"], exc_str))
        shown += 1

    print("")
    print("  Unique exception types: {} ({})".format(
        len(all_exceptions), ", ".join(sorted(all_exceptions))))
    print("")

    # Show catch blocks for same class if available
    class_catches = ei.get("class_catches", {})
    if class_name in class_catches:
        catches = class_catches[class_name]["catches"]
        caught_types = set()
        for c in catches:
            caught_types.update(c["exceptions"])
        print("  Also catches: {} types in {} blocks ({})".format(
            len(caught_types), len(catches),
            ", ".join(sorted(caught_types))))
        print("")


def _show_thrown_exception(exc_name, entries, module_filter, limit):
    """Show who throws a specific exception type."""
    if module_filter:
        entries = [e for e in entries if e["module"] == module_filter]

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  THROWN: {}{} ({} declarations)".format(exc_name, scope, len(entries)))
    print("")
    print("  {:30s}  {:25s}  {:>5s}  {}".format(
        "CLASS", "METHOD", "LINE", "MODULE"))
    print("  " + "-" * 75)

    # Group by module for nice display
    by_module = {}
    for e in entries:
        mod = e["module"]
        if mod not in by_module:
            by_module[mod] = []
        by_module[mod].append(e)

    shown = 0
    for mod in sorted(by_module.keys()):
        mod_entries = sorted(by_module[mod], key=lambda x: (x["class"], x["line"]))
        for e in mod_entries:
            if shown >= limit:
                remaining = len(entries) - shown
                print("  ... and {} more (use -n {} to see all)".format(
                    remaining, len(entries)))
                print("")
                print("  Modules: {}".format(len(by_module)))
                return

            print("  {:30s}  {:25s}  {:>5d}  {}".format(
                e["class"], e["method"], e["line"], e["module"]))
            shown += 1

    print("")
    print("  {} modules: {}".format(
        len(by_module), ", ".join(sorted(by_module.keys()))))
    print("")


# ---------------------------------------------------------------------------
# catches command — show who catches an exception type
# ---------------------------------------------------------------------------

def cmd_catches(base_dir, exception_name, module_filter=None, limit=50):
    """Show classes that catch a specific exception type."""
    ei = load_exceptions_index(base_dir)
    if not ei:
        return

    caught_map = ei.get("caught", {})

    entries = caught_map.get(exception_name, [])

    if module_filter:
        entries = [e for e in entries if e["module"] == module_filter]

    if not entries:
        if exception_name in caught_map:
            print("  Exception '{}' is caught, but not in module '{}'.".format(
                exception_name, module_filter))
            print("  Total catch blocks: {}".format(len(caught_map[exception_name])))
        else:
            # Try partial match
            partial = [k for k in caught_map if exception_name.lower() in k.lower()]
            if partial:
                print("")
                print("  Exception '{}' not found exactly. Partial matches:".format(
                    exception_name))
                for p in sorted(partial)[:15]:
                    print("    {:35s}  {:>5,} catch blocks".format(
                        p, len(caught_map[p])))
                if len(partial) > 15:
                    print("    ... and {} more".format(len(partial) - 15))
            else:
                print("  Exception '{}' not caught anywhere in the corpus.".format(
                    exception_name))

            # Also check thrown map
            thrown_map = ei.get("thrown", {})
            if exception_name in thrown_map:
                print("  (But it IS thrown by {} methods — use: throws {})".format(
                    len(thrown_map[exception_name]), exception_name))
        return

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    # Group by module
    by_module = {}
    for e in entries:
        mod = e["module"]
        if mod not in by_module:
            by_module[mod] = []
        by_module[mod].append(e)

    print("")
    print("  CATCHES: {}{} ({} catch blocks in {} modules)".format(
        exception_name, scope, len(entries), len(by_module)))
    print("")
    print("  {:35s}  {:>5s}  {}".format("CLASS", "LINE", "MODULE"))
    print("  " + "-" * 65)

    shown = 0
    for mod in sorted(by_module.keys()):
        mod_entries = sorted(by_module[mod], key=lambda x: (x["class"], x["line"]))
        for e in mod_entries:
            if shown >= limit:
                remaining = len(entries) - shown
                print("  ... and {} more (use -n {} to see all)".format(
                    remaining, len(entries)))
                break
            print("  {:35s}  {:>5d}  {}".format(
                e["class"], e["line"], e["module"]))
            shown += 1
        if shown >= limit:
            break

    print("")

    # Top modules
    top_mods = sorted(by_module.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print("  Top modules:")
    for mod, mod_entries in top_mods:
        classes = len(set(e["class"] for e in mod_entries))
        print("    {:35s}  {:>4} blocks, {:>3} classes".format(
            mod, len(mod_entries), classes))
    print("")

    # Also show if this exception is thrown
    thrown_map = ei.get("thrown", {})
    if exception_name in thrown_map:
        thrown_entries = thrown_map[exception_name]
        thrown_mods = len(set(e["module"] for e in thrown_entries))
        print("  Also thrown: {} declarations in {} modules".format(
            len(thrown_entries), thrown_mods))
        print("  (use: throws {} to see declarations)".format(exception_name))
        print("")
