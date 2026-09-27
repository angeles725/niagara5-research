"""
Virtual Dispatch Caller Aggregation for Module Navigator (Batch 4, Gap #7).

Aggregates callers across the inheritance chain to resolve virtual dispatch.
The callgraph-index only records static/direct calls to the exact declaring
type; when code calls BaseClass.method() and the runtime dispatches to
SubClass.method(), the callgraph shows callers of SubClass.method but NOT
of BaseClass.method.  This command unifies both.

Commands:
  virtual-callers <class> <method>
    [--depth N]       Max subclass depth (0=unlimited, default 0)
    [--no-self]       Exclude direct callers of class.method
    [--json]          Structured JSON output

Reuses existing indexes (no new builders):
  class-index.json, inheritance.json, method-index.json, callgraph-index.json
"""

import json
import os
from collections import Counter


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached per process)
# ---------------------------------------------------------------------------

_class_index_cache = None
_inheritance_cache = None
_method_index_cache = None


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


def _load_inheritance(base_dir):
    global _inheritance_cache
    if _inheritance_cache is not None:
        return _inheritance_cache
    _inheritance_cache = _load_json(
        os.path.join(base_dir, "indexes", "inheritance.json"))
    return _inheritance_cache


def _load_method_index(base_dir):
    global _method_index_cache
    if _method_index_cache is not None:
        return _method_index_cache
    _method_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "method-index.json"))
    return _method_index_cache


def _get_called_by(base_dir):
    """Load callgraph and return reverse index (callee -> callers)."""
    from module_nav_lib.callgraph import load_callgraph, _build_called_by
    cg = load_callgraph(base_dir)
    if not cg:
        return None
    return _build_called_by(cg)


# ---------------------------------------------------------------------------
# Class resolution helpers
# ---------------------------------------------------------------------------

def _resolve_class(ci_data, class_name):
    """Return canonical class name (case-corrected) or None."""
    if not ci_data:
        return None
    classes = ci_data.get("classes", {})
    if class_name in classes:
        return class_name
    name_lower = class_name.lower()
    for k in classes:
        if k.lower() == name_lower:
            return k
    return None


def _get_class_module(ci_classes, class_name):
    """Return preferred module for a class (skipping docSource-doc)."""
    entries = ci_classes.get(class_name)
    if not entries:
        return None
    for e in entries:
        if e.get("outer_class") is None and e.get("module") != "docSource-doc":
            return e.get("module")
    for e in entries:
        if e.get("outer_class") is None:
            return e.get("module")
    return entries[0].get("module") if entries else None


# ---------------------------------------------------------------------------
# BFS descendant walk
# ---------------------------------------------------------------------------

def _bfs_descendants(inheritance, root_class, max_depth=0):
    """BFS through parent_to_children.  Returns list of (class, depth).

    max_depth=0 means unlimited.  root_class itself is NOT included.
    """
    children_map = inheritance.get("parent_to_children", {})
    result = []
    queue = [(root_class, 0)]
    visited = {root_class}

    while queue:
        cls, d = queue.pop(0)
        if cls != root_class:
            result.append((cls, d))

        if max_depth > 0 and d >= max_depth:
            continue

        for child in children_map.get(cls, []):
            if child not in visited:
                visited.add(child)
                queue.append((child, d + 1))

    return result


# ---------------------------------------------------------------------------
# External-caller extraction
# ---------------------------------------------------------------------------

def _get_external_callers(called_by, class_name, method_name):
    """Return set of external caller class names for class.method."""
    key = "{}.{}".format(class_name, method_name)
    callers = called_by.get(key, [])
    external = set()
    for c in callers:
        dot = c.rfind(".")
        if dot <= 0:
            continue
        caller_cls = c[:dot]
        if caller_cls != class_name:
            external.add(caller_cls)
    return external


# ---------------------------------------------------------------------------
# Core aggregation (public — reused by contracts.py --resolve-virtual)
# ---------------------------------------------------------------------------

def aggregate_method_callers(class_name, method_name, inheritance,
                             method_index, called_by, max_depth=0):
    """Aggregate callers of class.method including virtual dispatch.

    Returns dict:
      direct:               set of external caller class names
      breakdown:            {subclass: set of external caller class names}
      overriders:           sorted list of subclasses that override method
      total_unique:         set of ALL unique external caller class names
      descendants_explored: total descendants checked
    """
    class_methods = method_index.get("class_methods", {})

    # Direct callers of the base class method
    direct = _get_external_callers(called_by, class_name, method_name)

    # BFS descendants
    desc_list = _bfs_descendants(inheritance, class_name, max_depth)

    # Filter to subclasses that override the method
    overriders = []
    for desc, _depth in desc_list:
        if method_name in class_methods.get(desc, []):
            overriders.append(desc)

    # Collect callers per overrider
    breakdown = {}
    for sub in sorted(overriders):
        ext = _get_external_callers(called_by, sub, method_name)
        if ext:
            breakdown[sub] = ext

    # Union all
    total_unique = set(direct)
    for ext in breakdown.values():
        total_unique |= ext

    return {
        "direct": direct,
        "breakdown": breakdown,
        "overriders": sorted(overriders),
        "total_unique": total_unique,
        "descendants_explored": len(desc_list),
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _print_virtual_callers(class_name, method_name, result, ci_classes,
                           include_self, max_depth):
    depth_str = "unlimited" if max_depth == 0 else str(max_depth)

    print("")
    print("  " + "=" * 68)
    print("  VIRTUAL-CALLERS: {}.{}  (depth {})".format(
        class_name, method_name, depth_str))
    print("  " + "=" * 68)

    direct = result["direct"]
    breakdown = result["breakdown"]
    overriders = result["overriders"]
    total_unique = result["total_unique"]
    desc_explored = result["descendants_explored"]

    # Direct callers
    print("")
    if include_self:
        print("  DIRECT CALLERS of {}.{}:  {}".format(
            class_name, method_name, len(direct)))
    else:
        print("  DIRECT CALLERS of {}.{}:  {} (excluded by --no-self)".format(
            class_name, method_name, len(direct)))

    # Virtual callers breakdown
    print("")
    overriders_with = [o for o in overriders if o in breakdown]
    overriders_without = [o for o in overriders if o not in breakdown]

    print("  VIRTUAL CALLERS (via {} overriding subclass(es)):".format(
        len(overriders)))
    print("  " + "-" * 68)

    if not overriders:
        print("    (no subclasses override {})".format(method_name))
    else:
        for sub in overriders_with:
            ext = breakdown[sub]
            label = "{}.{}".format(sub, method_name)
            if len(label) > 44:
                label = label[:41] + "..."
            print("    {:<45s}  -> {:>5d} external caller classes".format(
                label, len(ext)))

        if overriders_without:
            sample = ", ".join(overriders_without[:5])
            more = " ..." if len(overriders_without) > 5 else ""
            print("")
            print("    ({} override(s) with 0 external callers: {}{})".format(
                len(overriders_without), sample, more))

    print("")
    print("  Subclasses explored: {} total, {} override {}".format(
        desc_explored, len(overriders), method_name))

    # Totals
    if include_self:
        effective = total_unique
    else:
        effective = total_unique - direct

    print("")
    print("  TOTAL DISTINCT EXTERNAL CALLER CLASSES: {}".format(len(effective)))

    # Module breakdown
    module_counter = Counter()
    for cls in effective:
        mod = _get_class_module(ci_classes, cls)
        if mod:
            module_counter[mod] += 1

    print("  TOTAL DISTINCT CALLER MODULES:          {}".format(
        len(module_counter)))

    if module_counter:
        print("")
        print("  TOP CALLER MODULES:")
        for mod, count in module_counter.most_common(10):
            print("    {:<35s}  {:>5d} caller classes".format(mod, count))

    # Next steps
    print("")
    print("  NEXT STEPS:")
    print("    integration-contract {} --resolve-virtual"
          "   Full contract with virtual entry-points".format(class_name))
    print("    example-mine {} --top 3"
          "                      Real usage snippets".format(class_name))
    print("")


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_virtual_callers(base_dir, class_name, method_name, max_depth=0,
                        include_self=True, as_json=False):
    """Aggregate callers via virtual dispatch across the inheritance chain."""
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: class-index.json not found.")
        return
    ci_classes = ci_data.get("classes", {})

    resolved = _resolve_class(ci_data, class_name)
    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        suggestions = [c for c in ci_classes
                       if class_name.lower() in c.lower()][:10]
        if suggestions:
            print("  Did you mean: {}".format(", ".join(suggestions)))
        return
    class_name = resolved

    inh = _load_inheritance(base_dir)
    if not inh:
        print("  ERROR: inheritance.json not found.")
        return

    mi = _load_method_index(base_dir)
    if not mi:
        print("  ERROR: method-index.json not found.")
        return

    # Verify method exists on the class
    class_methods = mi.get("class_methods", {})
    if method_name not in class_methods.get(class_name, []):
        print("  Method '{}' not found on class '{}'.".format(
            method_name, class_name))
        available = class_methods.get(class_name, [])
        if available:
            matches = [m for m in available
                       if method_name.lower() in m.lower()]
            if matches:
                print("  Did you mean: {}".format(
                    ", ".join(sorted(matches)[:10])))
            else:
                print("  Available methods ({} total): {}".format(
                    len(available),
                    ", ".join(sorted(available)[:15])))
        return

    called_by = _get_called_by(base_dir)
    if called_by is None:
        print("  ERROR: callgraph-index.json not found or failed to load.")
        return

    result = aggregate_method_callers(
        class_name, method_name, inh, mi, called_by, max_depth=max_depth)

    if as_json:
        caller_set = result["total_unique"] if include_self \
            else (result["total_unique"] - result["direct"])
        mod_counter = Counter()
        for cls in caller_set:
            mod = _get_class_module(ci_classes, cls)
            if mod:
                mod_counter[mod] += 1

        json_result = {
            "class": class_name,
            "method": method_name,
            "max_depth": max_depth if max_depth > 0 else "unlimited",
            "include_self": include_self,
            "direct_callers": len(result["direct"]),
            "overriders": result["overriders"],
            "descendants_explored": result["descendants_explored"],
            "breakdown": {sub: sorted(ext)
                          for sub, ext in result["breakdown"].items()},
            "total_unique_external": len(caller_set),
            "caller_modules": dict(mod_counter.most_common()),
        }
        print(json.dumps(json_result, indent=2, ensure_ascii=False))
        return

    _print_virtual_callers(class_name, method_name, result, ci_classes,
                           include_self, max_depth)
