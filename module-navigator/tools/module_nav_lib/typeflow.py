"""
Type flow analysis commands for Module Navigator (Phase 14).

Commands:
  type-consumers <type> [-n N]       Methods that receive this type as parameter
    [--module mod]                   Filter by module
  type-producers <type> [-n N]       Methods that return this type
    [--module mod]                   Filter by module
  type-flow <type> [--depth N]       Producer -> consumer chain via call graph
    [-n N]                           Limit results per section (default 30)

No index build required — builds inverted maps from method-index.json in memory.
Uses callgraph-index.json for transitive type-flow tracing.
"""

import json
import os
import sys


# ---------------------------------------------------------------------------
# Inverted maps (cached after first build)
# ---------------------------------------------------------------------------

_param_type_map = None    # { "BAlarmRecord": [ {class, module, method, signature, line}, ... ] }
_return_type_map = None   # { "BOrd": [ {class, module, method, signature, line}, ... ] }
_method_index_ref = None  # reference to loaded method-index


def _build_type_maps(base_dir):
    """Build inverted param and return type maps from method-index."""
    global _param_type_map, _return_type_map, _method_index_ref

    if _param_type_map is not None:
        return True

    # Load method-index (uses REPL cache if available)
    from module_nav_lib.methods import load_method_index
    mi = load_method_index(base_dir)
    if not mi:
        return False

    _method_index_ref = mi
    methods = mi.get("methods", {})

    sys.stdout.write("  Building type flow maps...")
    sys.stdout.flush()

    param_map = {}   # type -> list of entries
    return_map = {}  # type -> list of entries

    for method_name, entries in methods.items():
        for e in entries:
            # Build compact entry
            entry = {
                "class": e["class"],
                "module": e["module"],
                "method": method_name,
                "signature": e.get("signature", ""),
                "line": e.get("line", 0),
            }

            # Index by return type
            ret = e.get("return_type", "")
            if ret and ret != "void":
                if ret not in return_map:
                    return_map[ret] = []
                return_map[ret].append(entry)

            # Index by param types
            params = e.get("params", [])
            for p in params:
                if p:
                    if p not in param_map:
                        param_map[p] = []
                    param_map[p].append(entry)

    _param_type_map = param_map
    _return_type_map = return_map

    print(" OK ({} param types, {} return types)".format(
        len(param_map), len(return_map)))
    return True


# ---------------------------------------------------------------------------
# type-consumers command
# ---------------------------------------------------------------------------

def cmd_type_consumers(base_dir, type_name, limit=50, module_filter=None):
    """Show methods that receive this type as a parameter."""
    if not _build_type_maps(base_dir):
        return

    entries = _param_type_map.get(type_name, [])

    # Try case-insensitive match if not found
    if not entries:
        lower = type_name.lower()
        for k in _param_type_map:
            if k.lower() == lower:
                type_name = k
                entries = _param_type_map[k]
                break

    if module_filter:
        entries = [e for e in entries if e["module"] == module_filter]

    if not entries:
        if type_name in _param_type_map:
            total = len(_param_type_map[type_name])
            print("  Type '{}' has {} consumers but none in module '{}'.".format(
                type_name, total, module_filter))
        else:
            print("  Type '{}' not found as parameter in any method.".format(type_name))
            _suggest_type(type_name, _param_type_map)
        return

    # Group by class for display
    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  TYPE CONSUMERS: {}{} ({} methods receive this type)".format(
        type_name, scope, len(entries)))
    print("")
    print("  {:35s}  {:30s}  {:25s}  {:>5s}".format(
        "CLASS", "METHOD", "MODULE", "LINE"))
    print("  " + "-" * 100)

    # Sort by class, then method
    sorted_entries = sorted(entries, key=lambda e: (e["class"], e["method"]))

    shown = 0
    for e in sorted_entries:
        if shown >= limit:
            break
        print("  {:35s}  {:30s}  {:25s}  {:>5d}".format(
            _trunc(e["class"], 35),
            _trunc(e["method"], 30),
            _trunc(e["module"], 25),
            e["line"]))
        shown += 1

    if len(entries) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(entries) - limit, len(entries)))

    # Summary: top modules
    mod_counts = {}
    for e in entries:
        mod_counts[e["module"]] = mod_counts.get(e["module"], 0) + 1
    top_mods = sorted(mod_counts.items(), key=lambda x: -x[1])[:10]
    print("")
    print("  Top modules consuming {}:".format(type_name))
    for mod, count in top_mods:
        print("    {:35s}  {:>5d} methods".format(mod, count))
    print("")


# ---------------------------------------------------------------------------
# type-producers command
# ---------------------------------------------------------------------------

def cmd_type_producers(base_dir, type_name, limit=50, module_filter=None):
    """Show methods that return this type."""
    if not _build_type_maps(base_dir):
        return

    entries = _return_type_map.get(type_name, [])

    # Try case-insensitive match if not found
    if not entries:
        lower = type_name.lower()
        for k in _return_type_map:
            if k.lower() == lower:
                type_name = k
                entries = _return_type_map[k]
                break

    if module_filter:
        entries = [e for e in entries if e["module"] == module_filter]

    if not entries:
        if type_name in _return_type_map:
            total = len(_return_type_map[type_name])
            print("  Type '{}' has {} producers but none in module '{}'.".format(
                type_name, total, module_filter))
        else:
            print("  Type '{}' not found as return type in any method.".format(type_name))
            _suggest_type(type_name, _return_type_map)
        return

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  TYPE PRODUCERS: {}{} ({} methods return this type)".format(
        type_name, scope, len(entries)))
    print("")
    print("  {:35s}  {:30s}  {:25s}  {:>5s}".format(
        "CLASS", "METHOD", "MODULE", "LINE"))
    print("  " + "-" * 100)

    sorted_entries = sorted(entries, key=lambda e: (e["class"], e["method"]))

    shown = 0
    for e in sorted_entries:
        if shown >= limit:
            break
        print("  {:35s}  {:30s}  {:25s}  {:>5d}".format(
            _trunc(e["class"], 35),
            _trunc(e["method"], 30),
            _trunc(e["module"], 25),
            e["line"]))
        shown += 1

    if len(entries) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(entries) - limit, len(entries)))

    # Summary: top modules
    mod_counts = {}
    for e in entries:
        mod_counts[e["module"]] = mod_counts.get(e["module"], 0) + 1
    top_mods = sorted(mod_counts.items(), key=lambda x: -x[1])[:10]
    print("")
    print("  Top modules producing {}:".format(type_name))
    for mod, count in top_mods:
        print("    {:35s}  {:>5d} methods".format(mod, count))
    print("")


# ---------------------------------------------------------------------------
# type-flow command
# ---------------------------------------------------------------------------

def cmd_type_flow(base_dir, type_name, depth=1, limit=30):
    """Show producer -> consumer flow for a type, using call graph for tracing."""
    if not _build_type_maps(base_dir):
        return

    producers = _return_type_map.get(type_name, [])
    consumers = _param_type_map.get(type_name, [])

    # Try case-insensitive match
    if not producers and not consumers:
        lower = type_name.lower()
        for k in _return_type_map:
            if k.lower() == lower:
                type_name = k
                producers = _return_type_map.get(k, [])
                consumers = _param_type_map.get(k, [])
                break

    if not producers and not consumers:
        print("  Type '{}' not found as parameter or return type.".format(type_name))
        # Combine both maps for suggestions
        all_types = set(_param_type_map.keys()) | set(_return_type_map.keys())
        partial = [t for t in all_types if type_name.lower() in t.lower()]
        if partial:
            shown = sorted(partial)[:10]
            print("  Partial matches: {}".format(", ".join(shown)))
            if len(partial) > 10:
                print("  ... and {} more".format(len(partial) - 10))
        return

    print("")
    print("  " + "=" * 70)
    print("  TYPE FLOW: {}".format(type_name))
    print("  " + "=" * 70)

    # --- Section 1: Producers ---
    print("")
    print("  PRODUCERS ({} methods return {}):".format(len(producers), type_name))
    if producers:
        print("")
        print("  {:35s}  {:30s}  {:25s}".format("CLASS", "METHOD", "MODULE"))
        print("  " + "-" * 95)

        sorted_p = sorted(producers, key=lambda e: (e["class"], e["method"]))
        shown = 0
        for e in sorted_p:
            if shown >= limit:
                break
            print("  {:35s}  {:30s}  {:25s}".format(
                _trunc(e["class"], 35),
                _trunc(e["method"], 30),
                _trunc(e["module"], 25)))
            shown += 1

        if len(producers) > limit:
            print("  ... and {} more".format(len(producers) - limit))
    else:
        print("    (none)")

    # --- Section 2: Consumers ---
    print("")
    print("  CONSUMERS ({} methods take {} as parameter):".format(
        len(consumers), type_name))
    if consumers:
        print("")
        print("  {:35s}  {:30s}  {:25s}".format("CLASS", "METHOD", "MODULE"))
        print("  " + "-" * 95)

        sorted_c = sorted(consumers, key=lambda e: (e["class"], e["method"]))
        shown = 0
        for e in sorted_c:
            if shown >= limit:
                break
            print("  {:35s}  {:30s}  {:25s}".format(
                _trunc(e["class"], 35),
                _trunc(e["method"], 30),
                _trunc(e["module"], 25)))
            shown += 1

        if len(consumers) > limit:
            print("  ... and {} more".format(len(consumers) - limit))
    else:
        print("    (none)")

    # --- Section 3: Connected flow (producers whose callees are consumers) ---
    if depth >= 1 and producers and consumers:
        _trace_flow(base_dir, type_name, producers, consumers, depth, limit)

    # --- Section 4: Summary ---
    print("")
    print("  SUMMARY:")
    print("    Producers:  {:>6,} methods return {}".format(len(producers), type_name))
    print("    Consumers:  {:>6,} methods take {} as param".format(len(consumers), type_name))

    # Unique modules
    prod_mods = set(e["module"] for e in producers)
    cons_mods = set(e["module"] for e in consumers)
    bridge_mods = prod_mods & cons_mods
    print("    Producer modules:  {:>4}".format(len(prod_mods)))
    print("    Consumer modules:  {:>4}".format(len(cons_mods)))
    print("    Bridge modules:    {:>4} (both produce and consume)".format(len(bridge_mods)))
    if bridge_mods:
        for m in sorted(bridge_mods)[:10]:
            print("      {}".format(m))
        if len(bridge_mods) > 10:
            print("      ... and {} more".format(len(bridge_mods) - 10))
    print("")


def _trace_flow(base_dir, type_name, producers, consumers, depth, limit):
    """Trace connected producer->consumer pairs via call graph."""
    from module_nav_lib.callgraph import load_callgraph

    cg = load_callgraph(base_dir)
    if not cg:
        print("")
        print("  CONNECTED FLOW: (callgraph-index.json not available)")
        return

    calls = cg.get("calls", {})

    # Build consumer lookup: "ClassName.methodName" -> entry
    consumer_keys = set()
    for e in consumers:
        consumer_keys.add("{}.{}".format(e["class"], e["method"]))

    # For each producer, check if any of its callees are consumers
    connections = []
    seen = set()

    for p in producers:
        caller_key = "{}.{}".format(p["class"], p["method"])
        callees = calls.get(caller_key, [])

        for callee in callees:
            if callee in consumer_keys and (caller_key, callee) not in seen:
                seen.add((caller_key, callee))
                connections.append({
                    "producer": caller_key,
                    "consumer": callee,
                    "producer_module": p["module"],
                })

    print("")
    print("  CONNECTED FLOW ({} direct producer->consumer edges via call graph):".format(
        len(connections)))

    if connections:
        print("")
        print("  {:40s}  -->  {:40s}".format("PRODUCER", "CONSUMER"))
        print("  " + "-" * 85)

        shown = 0
        for conn in sorted(connections, key=lambda c: c["producer"]):
            if shown >= limit:
                break
            print("  {:40s}  -->  {:40s}".format(
                _trunc(conn["producer"], 40),
                _trunc(conn["consumer"], 40)))
            shown += 1

        if len(connections) > limit:
            print("  ... and {} more".format(len(connections) - limit))
    else:
        print("    (no direct producer->consumer edges found in call graph)")
        print("    This is common — the type may flow through intermediate variables")
        print("    that the static call graph does not capture.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _suggest_type(type_name, type_map):
    """Suggest partial matches for a type name."""
    partial = [t for t in type_map if type_name.lower() in t.lower()]
    if partial:
        shown = sorted(partial)[:10]
        print("  Partial matches: {}".format(", ".join(shown)))
        if len(partial) > 10:
            print("  ... and {} more".format(len(partial) - 10))


def _trunc(s, max_len):
    """Truncate string with ellipsis."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."
