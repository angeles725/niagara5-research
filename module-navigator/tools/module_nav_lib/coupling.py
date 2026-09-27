"""
Cross-module method usage commands for Module Navigator (Phase 15).

Commands:
  module-calls <from> <to> [-n N]     Methods of `to` called from `from`
  module-api-usage <mod> [-n N]       Top external methods used by a module
  coupling <mod1> <mod2>              Coupling metrics between two modules

No index build required -- filters callgraph-index + class-index.
Callgraph loaded on-demand (cached after first load).
"""

import sys


# ---------------------------------------------------------------------------
# Module-level edge map (cached after first build)
# ---------------------------------------------------------------------------

_module_edge_cache = None   # { (from_mod, to_mod): [ (caller_key, callee_key), ... ] }
_class_to_module = None     # { "ClassName": "module-name" }


def _build_module_edges(base_dir):
    """Build per-module edge map from callgraph + class-index. Cached."""
    global _module_edge_cache, _class_to_module

    if _module_edge_cache is not None:
        return True

    from module_nav_lib.callgraph import load_callgraph, _load_class_index

    cg = load_callgraph(base_dir)
    if not cg:
        return False

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: class-index.json not available.")
        return False

    ci_classes = ci_data.get("classes", {})
    calls = cg.get("calls", {})

    sys.stdout.write("  Building module edge map...")
    sys.stdout.flush()

    # Pre-build class -> module lookup
    c2m = {}
    for class_name, entries in ci_classes.items():
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            c2m[class_name] = top[0].get("module", "?")
        elif entries:
            c2m[class_name] = entries[0].get("module", "?")

    _class_to_module = c2m

    # Build edge map grouped by (from_module, to_module)
    edge_map = {}
    for caller_key, callees in calls.items():
        dot = caller_key.rfind('.')
        caller_cls = caller_key[:dot] if dot > 0 else caller_key
        caller_mod = c2m.get(caller_cls, "?")

        for callee_key in callees:
            dot2 = callee_key.rfind('.')
            callee_cls = callee_key[:dot2] if dot2 > 0 else callee_key
            callee_mod = c2m.get(callee_cls, "?")

            # Skip intra-module calls
            if caller_mod == callee_mod:
                continue
            # Skip unresolved
            if caller_mod == "?" or callee_mod == "?":
                continue

            pair = (caller_mod, callee_mod)
            if pair not in edge_map:
                edge_map[pair] = []
            edge_map[pair].append((caller_key, callee_key))

    _module_edge_cache = edge_map
    total_pairs = len(edge_map)
    total_edges = sum(len(v) for v in edge_map.values())
    print(" OK ({:,} module pairs, {:,} cross-module edges)".format(
        total_pairs, total_edges))
    return True


# ---------------------------------------------------------------------------
# module-calls command
# ---------------------------------------------------------------------------

def cmd_module_calls(base_dir, from_mod, to_mod, limit=50):
    """Show methods of `to_mod` called from `from_mod`."""
    if not _build_module_edges(base_dir):
        return

    pair = (from_mod, to_mod)
    edges = _module_edge_cache.get(pair, [])

    if not edges:
        # Try partial match
        partial_from = [k for k in _module_edge_cache if from_mod in k[0]]
        partial_to = [k for k in _module_edge_cache if to_mod in k[1]]
        print("")
        print("  No calls found from '{}' to '{}'.".format(from_mod, to_mod))
        if partial_from:
            mods = sorted(set(k[1] for k in partial_from))[:10]
            print("  '{}' calls into: {}".format(from_mod, ", ".join(mods)))
        if partial_to:
            mods = sorted(set(k[0] for k in partial_to))[:10]
            print("  '{}' is called from: {}".format(to_mod, ", ".join(mods)))
        print("")
        return

    # Group by callee method and count
    callee_counts = {}
    callee_callers = {}
    for caller_key, callee_key in edges:
        callee_counts[callee_key] = callee_counts.get(callee_key, 0) + 1
        if callee_key not in callee_callers:
            callee_callers[callee_key] = set()
        callee_callers[callee_key].add(caller_key)

    # Sort by call count descending
    sorted_callees = sorted(callee_counts.items(), key=lambda x: -x[1])

    unique_callers = set()
    unique_callees = set()
    for caller_key, callee_key in edges:
        unique_callers.add(caller_key)
        unique_callees.add(callee_key)

    print("")
    print("  MODULE CALLS: {} -> {}".format(from_mod, to_mod))
    print("  {:,} total edges, {:,} unique callees, {:,} unique callers".format(
        len(edges), len(unique_callees), len(unique_callers)))
    print("")
    print("  {:>5s}  {:>5s}  {:45s}".format("CALLS", "FROM", "METHOD IN {}".format(to_mod)))
    print("  " + "-" * 60)

    shown = 0
    for callee_key, count in sorted_callees:
        if shown >= limit:
            break
        n_callers = len(callee_callers[callee_key])
        print("  {:>5,}  {:>5,}  {}".format(count, n_callers, callee_key))
        shown += 1

    if len(sorted_callees) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(sorted_callees) - limit, len(sorted_callees)))
    print("")


# ---------------------------------------------------------------------------
# module-api-usage command
# ---------------------------------------------------------------------------

def cmd_module_api_usage(base_dir, module_name, limit=50):
    """Show top external methods used by a module."""
    if not _build_module_edges(base_dir):
        return

    # Collect all outgoing edges from this module
    outgoing = []
    for (from_mod, to_mod), edges in _module_edge_cache.items():
        if from_mod == module_name:
            outgoing.extend(edges)

    if not outgoing:
        print("")
        print("  No outgoing cross-module calls found for '{}'.".format(module_name))
        # Suggest partial matches
        all_from = sorted(set(k[0] for k in _module_edge_cache))
        partial = [m for m in all_from if module_name in m]
        if partial:
            print("  Partial matches: {}".format(", ".join(partial[:10])))
        print("")
        return

    # Group by callee method
    callee_counts = {}
    for caller_key, callee_key in outgoing:
        callee_counts[callee_key] = callee_counts.get(callee_key, 0) + 1

    sorted_callees = sorted(callee_counts.items(), key=lambda x: -x[1])

    # Also group by target module
    target_mod_counts = {}
    for (from_mod, to_mod), edges in _module_edge_cache.items():
        if from_mod == module_name:
            target_mod_counts[to_mod] = target_mod_counts.get(to_mod, 0) + len(edges)

    sorted_targets = sorted(target_mod_counts.items(), key=lambda x: -x[1])

    print("")
    print("  MODULE API USAGE: {} ({:,} external calls to {:,} unique methods)".format(
        module_name, len(outgoing), len(callee_counts)))
    print("")

    # Top external methods
    print("  TOP EXTERNAL METHODS CALLED:")
    print("  {:>5s}  {:45s}  {:25s}".format("CALLS", "METHOD", "MODULE"))
    print("  " + "-" * 80)

    shown = 0
    for callee_key, count in sorted_callees:
        if shown >= limit:
            break
        dot = callee_key.rfind('.')
        callee_cls = callee_key[:dot] if dot > 0 else callee_key
        callee_mod = _class_to_module.get(callee_cls, "?")
        print("  {:>5,}  {:45s}  {:25s}".format(count, _trunc(callee_key, 45), callee_mod))
        shown += 1

    if len(sorted_callees) > limit:
        print("")
        print("  ... and {} more methods (use -n {} to see all)".format(
            len(sorted_callees) - limit, len(sorted_callees)))

    # Target module summary
    print("")
    print("  TARGET MODULES ({} modules called):".format(len(sorted_targets)))
    print("  {:>5s}  {}".format("EDGES", "MODULE"))
    print("  " + "-" * 40)
    for mod, count in sorted_targets[:20]:
        print("  {:>5,}  {}".format(count, mod))
    if len(sorted_targets) > 20:
        print("  ... and {} more".format(len(sorted_targets) - 20))
    print("")


# ---------------------------------------------------------------------------
# coupling command
# ---------------------------------------------------------------------------

def cmd_coupling(base_dir, mod1, mod2):
    """Show coupling metrics between two modules."""
    if not _build_module_edges(base_dir):
        return

    edges_1to2 = _module_edge_cache.get((mod1, mod2), [])
    edges_2to1 = _module_edge_cache.get((mod2, mod1), [])

    if not edges_1to2 and not edges_2to1:
        print("")
        print("  No coupling found between '{}' and '{}'.".format(mod1, mod2))
        # Check if modules exist
        all_mods = set()
        for (f, t) in _module_edge_cache:
            all_mods.add(f)
            all_mods.add(t)
        if mod1 not in all_mods:
            partial = sorted(m for m in all_mods if mod1 in m)[:5]
            if partial:
                print("  '{}' not found. Did you mean: {}".format(mod1, ", ".join(partial)))
        if mod2 not in all_mods:
            partial = sorted(m for m in all_mods if mod2 in m)[:5]
            if partial:
                print("  '{}' not found. Did you mean: {}".format(mod2, ", ".join(partial)))
        print("")
        return

    # Compute metrics for each direction
    def _metrics(edges):
        callers = set()
        callees = set()
        caller_classes = set()
        callee_classes = set()
        for ck, ce in edges:
            callers.add(ck)
            callees.add(ce)
            dot1 = ck.rfind('.')
            dot2 = ce.rfind('.')
            if dot1 > 0:
                caller_classes.add(ck[:dot1])
            if dot2 > 0:
                callee_classes.add(ce[:dot2])
        return {
            "edges": len(edges),
            "unique_callers": len(callers),
            "unique_callees": len(callees),
            "caller_classes": len(caller_classes),
            "callee_classes": len(callee_classes),
        }

    m_1to2 = _metrics(edges_1to2)
    m_2to1 = _metrics(edges_2to1)
    total_edges = m_1to2["edges"] + m_2to1["edges"]

    print("")
    print("  " + "=" * 65)
    print("  COUPLING: {} <-> {}".format(mod1, mod2))
    print("  " + "=" * 65)
    print("")

    # Direction 1 -> 2
    print("  {} -> {}:".format(mod1, mod2))
    if m_1to2["edges"]:
        print("    Call edges:       {:>6,}".format(m_1to2["edges"]))
        print("    Unique callers:   {:>6,} methods in {:,} classes".format(
            m_1to2["unique_callers"], m_1to2["caller_classes"]))
        print("    Unique callees:   {:>6,} methods in {:,} classes".format(
            m_1to2["unique_callees"], m_1to2["callee_classes"]))
    else:
        print("    (no calls)")
    print("")

    # Direction 2 -> 1
    print("  {} -> {}:".format(mod2, mod1))
    if m_2to1["edges"]:
        print("    Call edges:       {:>6,}".format(m_2to1["edges"]))
        print("    Unique callers:   {:>6,} methods in {:,} classes".format(
            m_2to1["unique_callers"], m_2to1["caller_classes"]))
        print("    Unique callees:   {:>6,} methods in {:,} classes".format(
            m_2to1["unique_callees"], m_2to1["callee_classes"]))
    else:
        print("    (no calls)")
    print("")

    # Combined metrics
    print("  COMBINED:")
    print("    Total edges:      {:>6,}".format(total_edges))
    if m_1to2["edges"] and m_2to1["edges"]:
        ratio = m_1to2["edges"] / m_2to1["edges"]
        if ratio >= 1:
            print("    Direction ratio:  {:.1f}:1 ({} -> {})".format(
                ratio, mod1, mod2))
        else:
            print("    Direction ratio:  {:.1f}:1 ({} -> {})".format(
                1.0 / ratio, mod2, mod1))
        print("    Bidirectional:    YES (tight coupling)")
    elif m_1to2["edges"]:
        print("    Direction:        unidirectional ({} -> {})".format(mod1, mod2))
    elif m_2to1["edges"]:
        print("    Direction:        unidirectional ({} -> {})".format(mod2, mod1))

    # Top called methods in each direction
    if edges_1to2:
        callee_counts = {}
        for _, ce in edges_1to2:
            callee_counts[ce] = callee_counts.get(ce, 0) + 1
        top = sorted(callee_counts.items(), key=lambda x: -x[1])[:10]
        print("")
        print("  TOP {} methods called by {}:".format(mod2, mod1))
        for meth, count in top:
            print("    {:>4,}x  {}".format(count, meth))

    if edges_2to1:
        callee_counts = {}
        for _, ce in edges_2to1:
            callee_counts[ce] = callee_counts.get(ce, 0) + 1
        top = sorted(callee_counts.items(), key=lambda x: -x[1])[:10]
        print("")
        print("  TOP {} methods called by {}:".format(mod1, mod2))
        for meth, count in top:
            print("    {:>4,}x  {}".format(count, meth))

    print("")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _trunc(s, max_len):
    """Truncate string with ellipsis."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."
