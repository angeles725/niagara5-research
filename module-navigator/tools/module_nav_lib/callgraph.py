"""
Call graph commands for Module Navigator (Phase 12).

Commands:
  callers <class> <method> [-n N]          Who calls this method
  callees <class> [<method>] [-n N]        What methods this class/method calls
  call-chain <class> <method> [--depth N]  Transitive call chain (tree)
  hotspots [-n N] [--module mod]           Most-called methods (hub analysis)

Index loaded on-demand (not preloaded in REPL due to size).
"""

import json
import os


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached after first load)
# ---------------------------------------------------------------------------

_callgraph_cache = None
_called_by_cache = None


def load_callgraph(base_dir):
    """Load callgraph-index.json (on-demand, cached after first load)."""
    global _callgraph_cache
    if _callgraph_cache is not None:
        return _callgraph_cache

    path = os.path.join(base_dir, "indexes", "callgraph-index.json")
    if not os.path.isfile(path):
        print("ERROR: callgraph-index.json not found.")
        print("Run: python tools/build_callgraph_index.py")
        return None

    import sys
    size_mb = os.path.getsize(path) / (1024 * 1024)
    # Progress goes to stderr so stdout stays clean for --json consumers.
    sys.stderr.write("  Loading callgraph-index.json ({:.1f} MB)...".format(size_mb))
    sys.stderr.flush()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sys.stderr.write(" OK\n")
    sys.stderr.flush()

    _callgraph_cache = data
    return data


def _build_called_by(cg):
    """Build reverse index: callee -> list of callers. Cached."""
    global _called_by_cache
    if _called_by_cache is not None:
        return _called_by_cache

    called_by = {}
    calls = cg.get("calls", {})
    for caller, callees in calls.items():
        for callee in callees:
            if callee not in called_by:
                called_by[callee] = []
            called_by[callee].append(caller)

    # Sort each list for deterministic output
    for key in called_by:
        called_by[key].sort()

    _called_by_cache = called_by
    return called_by


def _load_class_index(base_dir):
    """Load class-index for module info lookups."""
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


def _get_module_for_class(class_name, ci_classes):
    """Get module name for a class from class-index."""
    if class_name in ci_classes:
        entries = ci_classes[class_name]
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            return top[0].get("module", "?")
        if entries:
            return entries[0].get("module", "?")
    return "?"


# ---------------------------------------------------------------------------
# callers command
# ---------------------------------------------------------------------------

def cmd_callers(base_dir, class_name, method_name, limit=50):
    """Show who calls a specific method."""
    cg = load_callgraph(base_dir)
    if not cg:
        return

    called_by = _build_called_by(cg)
    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}

    key = "{}.{}".format(class_name, method_name)
    callers = called_by.get(key, [])

    if not callers:
        # Try to find partial matches
        partial = [k for k in called_by if k.endswith("." + method_name)]
        print("")
        print("  No callers found for '{}'.".format(key))
        if partial:
            print("")
            print("  Other classes with callers for '{}':".format(method_name))
            for p in sorted(partial)[:15]:
                print("    {} ({} callers)".format(p, len(called_by[p])))
            if len(partial) > 15:
                print("    ... and {} more".format(len(partial) - 15))
        print("")
        return

    # Get module info for the target
    target_module = _get_module_for_class(class_name, ci_classes)

    print("")
    print("  CALLERS of {}.{}: {} callers".format(class_name, method_name, len(callers)))
    print("  Target module: {}".format(target_module))
    print("")
    print("  {:>40s}  {:25s}  {}".format("CALLER METHOD", "MODULE", "CLASS"))
    print("  " + "-" * 90)

    shown = 0
    for caller in callers:
        if shown >= limit:
            break
        # Parse caller: "ClassName.methodName"
        dot = caller.rfind('.')
        if dot > 0:
            c_cls = caller[:dot]
            c_meth = caller[dot + 1:]
        else:
            c_cls = caller
            c_meth = "?"
        c_module = _get_module_for_class(c_cls, ci_classes)
        print("  {:>40s}  {:25s}  {}".format(caller, c_module, c_cls))
        shown += 1

    if len(callers) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(callers) - limit, len(callers)))
    print("")


# ---------------------------------------------------------------------------
# callees command
# ---------------------------------------------------------------------------

def cmd_callees(base_dir, class_name, method_name=None, limit=50):
    """Show what methods a class or method calls."""
    cg = load_callgraph(base_dir)
    if not cg:
        return

    calls = cg.get("calls", {})
    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}

    if method_name:
        # Single method callees
        key = "{}.{}".format(class_name, method_name)
        callees = calls.get(key, [])

        if not callees:
            print("")
            print("  No callees found for '{}'.".format(key))
            # Check if the caller exists at all
            prefix = class_name + "."
            class_methods = [k for k in calls if k.startswith(prefix)]
            if class_methods:
                print("  {} has {} methods with calls. Try:".format(
                    class_name, len(class_methods)))
                for cm in sorted(class_methods)[:10]:
                    print("    callees {} {}".format(class_name, cm.split('.', 1)[1]))
            print("")
            return

        print("")
        print("  CALLEES of {}: {} calls".format(key, len(callees)))
        print("")
        print("  {:>40s}  {:25s}".format("CALLED METHOD", "MODULE"))
        print("  " + "-" * 65)

        shown = 0
        for callee in callees:
            if shown >= limit:
                break
            dot = callee.rfind('.')
            c_cls = callee[:dot] if dot > 0 else callee
            c_module = _get_module_for_class(c_cls, ci_classes)
            print("  {:>40s}  {:25s}".format(callee, c_module))
            shown += 1

        if len(callees) > limit:
            print("")
            print("  ... and {} more (use -n {} to see all)".format(
                len(callees) - limit, len(callees)))
        print("")

    else:
        # All methods of the class
        prefix = class_name + "."
        class_entries = {k: v for k, v in calls.items() if k.startswith(prefix)}

        if not class_entries:
            print("")
            print("  No call data found for class '{}'.".format(class_name))
            # Suggest partial matches
            partial = [k.split('.')[0] for k in calls if class_name.lower() in k.split('.')[0].lower()]
            unique = sorted(set(partial))[:10]
            if unique:
                print("  Did you mean: {}".format(", ".join(unique)))
            print("")
            return

        total_callees = sum(len(v) for v in class_entries.values())
        target_module = _get_module_for_class(class_name, ci_classes)

        print("")
        print("  CALLEES of {} (all methods): {} methods, {} total calls".format(
            class_name, len(class_entries), total_callees))
        print("  Module: {}".format(target_module))
        print("")

        shown = 0
        for key in sorted(class_entries.keys()):
            if shown >= limit:
                break
            method = key.split('.', 1)[1] if '.' in key else key
            callees = class_entries[key]
            print("  {} ({} calls):".format(method, len(callees)))
            for callee in callees[:10]:
                dot = callee.rfind('.')
                c_cls = callee[:dot] if dot > 0 else callee
                c_mod = _get_module_for_class(c_cls, ci_classes)
                print("    -> {:40s}  [{}]".format(callee, c_mod))
            if len(callees) > 10:
                print("    ... and {} more".format(len(callees) - 10))
            print("")
            shown += 1

        if len(class_entries) > limit:
            print("  ... and {} more methods (use -n {} to see all)".format(
                len(class_entries) - limit, len(class_entries)))
            print("")


# ---------------------------------------------------------------------------
# call-chain command
# ---------------------------------------------------------------------------

def cmd_call_chain(base_dir, class_name, method_name, depth=2):
    """Show transitive call chain as a tree."""
    cg = load_callgraph(base_dir)
    if not cg:
        return

    calls = cg.get("calls", {})
    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}

    root = "{}.{}".format(class_name, method_name)

    if root not in calls:
        print("")
        print("  '{}' not found in call graph.".format(root))
        prefix = class_name + "."
        class_methods = [k for k in calls if k.startswith(prefix)]
        if class_methods:
            print("  Available methods for {}:".format(class_name))
            for cm in sorted(class_methods)[:15]:
                print("    {}".format(cm))
        print("")
        return

    root_module = _get_module_for_class(class_name, ci_classes)

    print("")
    print("  CALL CHAIN from {} (depth {})".format(root, depth))
    print("  Module: {}".format(root_module))
    print("")

    visited = set()
    _print_tree(root, calls, ci_classes, depth, 0, visited, is_last=[])


def _print_tree(node, calls, ci_classes, max_depth, current_depth, visited, is_last):
    """Recursively print call tree."""
    # Build prefix
    prefix = "  "
    for i, last in enumerate(is_last):
        if i < len(is_last) - 1:
            prefix += "    " if last else "|   "
        else:
            prefix += "`-- " if last else "|-- "

    if current_depth == 0:
        prefix = "  "

    # Get module
    dot = node.rfind('.')
    cls = node[:dot] if dot > 0 else node
    mod = _get_module_for_class(cls, ci_classes)

    # Check circular
    circular = node in visited
    suffix = ""
    if circular:
        suffix = " (circular)"

    callees = calls.get(node, [])
    count_str = " [{} calls]".format(len(callees)) if callees and not circular else ""

    print("{}{} [{}]{}{}".format(prefix, node, mod, count_str, suffix))

    if circular or current_depth >= max_depth:
        if callees and not circular:
            leaf_prefix = "  "
            for last in is_last:
                leaf_prefix += "    " if last else "|   "
            print("{}    ... ({} callees, depth limit)".format(leaf_prefix, len(callees)))
        return

    visited.add(node)

    for i, callee in enumerate(callees):
        is_last_child = (i == len(callees) - 1)
        _print_tree(callee, calls, ci_classes, max_depth,
                    current_depth + 1, visited, is_last + [is_last_child])

    visited.discard(node)


# ---------------------------------------------------------------------------
# hotspots command
# ---------------------------------------------------------------------------

def cmd_hotspots(base_dir, limit=20, module_filter=None):
    """Show most-called methods (hub analysis)."""
    cg = load_callgraph(base_dir)
    if not cg:
        return

    called_by = _build_called_by(cg)
    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}

    # Count callers per callee
    entries = []
    for callee, callers in called_by.items():
        dot = callee.rfind('.')
        cls = callee[:dot] if dot > 0 else callee
        mod = _get_module_for_class(cls, ci_classes)

        if module_filter and mod != module_filter:
            continue

        entries.append((callee, len(callers), mod))

    entries.sort(key=lambda x: -x[1])

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  HOTSPOTS{}: top {} most-called methods".format(scope, min(limit, len(entries))))
    print("")
    print("  {:>5s}  {:>45s}  {:25s}".format("CALLS", "METHOD", "MODULE"))
    print("  " + "-" * 80)

    shown = 0
    for callee, count, mod in entries:
        if shown >= limit:
            break
        print("  {:>5,}  {:>45s}  {:25s}".format(count, callee, mod))
        shown += 1

    if len(entries) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(entries) - limit, len(entries)))

    meta = cg.get("_meta", {})
    print("")
    print("  Index: {:,} callers, {:,} callees, {:,} edges".format(
        meta.get("total_caller_methods", 0),
        meta.get("total_unique_callees", 0),
        meta.get("total_edges", 0)))
    print("")
