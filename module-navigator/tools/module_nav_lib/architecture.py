"""
Cyclic Dependency & Architecture Quality commands for Module Navigator (Phase 39).

Detects cyclic module dependencies (DFS/Tarjan), identifies god classes
by method+field+importer thresholds, and checks layer violations
(RT modules importing WB/UX modules).

Uses xref-index.json + method-index.json + field-index.json + class-index.json
on-demand. No builder.

Commands:
  cycles [--depth N] [-n N]          Cyclic module dependencies (DFS)
  god-classes [--threshold N] [-n N]  Classes with excessive methods/fields/deps
  layer-check [<module>]             Layer violations: RT must not import WB/UX
"""

import json
import os
from collections import defaultdict


# ---------------------------------------------------------------------------
# Niagara layer definitions
# ---------------------------------------------------------------------------

# Module suffix -> layer rank (lower = more foundational)
_LAYER_SUFFIXES = {
    "-rt": ("RT", 0),
    "-doc": ("DOC", 1),
    "-wb": ("WB", 2),
    "-ux": ("UX", 2),
}

# Violation rules: layer X should NOT import layer Y
# RT -> WB/UX is a violation; WB -> RT is fine; UX -> RT is fine
_LAYER_VIOLATIONS = {
    "RT": {"WB", "UX"},
    # DOC -> anything is fine (documentation modules)
    # WB -> UX would be questionable but not strictly forbidden
}


def _get_layer(module_name):
    """Determine the architectural layer of a module from its suffix."""
    for suffix, (layer, rank) in _LAYER_SUFFIXES.items():
        if module_name.endswith(suffix):
            return layer, rank
    return "OTHER", -1


# ---------------------------------------------------------------------------
# Index loaders (lazy, cached)
# ---------------------------------------------------------------------------

_xref_cache = None
_method_index_cache = None
_field_index_cache = None
_class_index_cache = None


def _load_xref(base_dir):
    global _xref_cache
    if _xref_cache is not None:
        return _xref_cache
    path = os.path.join(base_dir, "indexes", "xref-index.json")
    if not os.path.isfile(path):
        print("ERROR: xref-index.json not found.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _xref_cache = json.load(f)
    return _xref_cache


def _load_method_index(base_dir):
    global _method_index_cache
    if _method_index_cache is not None:
        return _method_index_cache
    path = os.path.join(base_dir, "indexes", "method-index.json")
    if not os.path.isfile(path):
        print("ERROR: method-index.json not found.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _method_index_cache = json.load(f)
    return _method_index_cache


def _load_field_index(base_dir):
    global _field_index_cache
    if _field_index_cache is not None:
        return _field_index_cache
    path = os.path.join(base_dir, "indexes", "field-index.json")
    if not os.path.isfile(path):
        print("ERROR: field-index.json not found.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _field_index_cache = json.load(f)
    return _field_index_cache


def _load_class_index(base_dir):
    global _class_index_cache
    if _class_index_cache is not None:
        return _class_index_cache
    path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(path):
        print("ERROR: class-index.json not found.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _class_index_cache = json.load(f)
    return _class_index_cache


# ---------------------------------------------------------------------------
# Cycle detection — Tarjan's SCC on module dependency graph
# ---------------------------------------------------------------------------

def _find_cycles_tarjan(adj):
    """Find all strongly connected components with >1 node using Tarjan's algorithm.

    adj: dict mapping module -> list of modules it depends on.
    Returns: list of SCCs (each is a list of module names), sorted by size desc.
    """
    index_counter = [0]
    stack = []
    on_stack = set()
    indices = {}
    lowlinks = {}
    sccs = []

    def strongconnect(v):
        indices[v] = index_counter[0]
        lowlinks[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)

        for w in adj.get(v, []):
            if w not in indices:
                strongconnect(w)
                lowlinks[v] = min(lowlinks[v], lowlinks[w])
            elif w in on_stack:
                lowlinks[v] = min(lowlinks[v], indices[w])

        if lowlinks[v] == indices[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                scc.append(w)
                if w == v:
                    break
            if len(scc) > 1:
                sccs.append(sorted(scc))

    for node in sorted(adj.keys()):
        if node not in indices:
            strongconnect(node)

    sccs.sort(key=lambda x: -len(x))
    return sccs


def _find_simple_cycles_dfs(adj, max_depth=6, max_cycles=500):
    """Find simple cycles up to max_depth using DFS.

    Returns list of cycles, each is a list of modules forming the cycle.
    More granular than Tarjan — shows individual dependency paths.
    Caps at max_cycles to avoid explosion in dense SCCs.
    """
    cycles = []
    seen_cycles = set()
    hit_limit = [False]

    def dfs(start, path, visited):
        if hit_limit[0]:
            return
        current = path[-1]
        if len(path) > max_depth + 1:
            return
        for neighbor in adj.get(current, []):
            if hit_limit[0]:
                return
            if neighbor == start and len(path) >= 2:
                cycle = path[:]
                # Normalize: start from the smallest element
                min_idx = cycle.index(min(cycle))
                canonical = tuple(cycle[min_idx:] + cycle[:min_idx])
                if canonical not in seen_cycles:
                    seen_cycles.add(canonical)
                    cycles.append(list(canonical))
                    if len(cycles) >= max_cycles:
                        hit_limit[0] = True
                        return
            elif neighbor not in visited and len(path) < max_depth + 1:
                visited.add(neighbor)
                path.append(neighbor)
                dfs(start, path, visited)
                path.pop()
                visited.discard(neighbor)

    for node in sorted(adj.keys()):
        if hit_limit[0]:
            break
        dfs(node, [node], {node})

    cycles.sort(key=lambda x: (len(x), x))
    return cycles


# ---------------------------------------------------------------------------
# cmd_cycles — Cyclic module dependencies
# ---------------------------------------------------------------------------

def cmd_cycles(base_dir, max_depth=6, limit=50):
    """Detect cyclic dependencies between modules using DFS/Tarjan."""
    xref = _load_xref(base_dir)
    if not xref:
        return

    module_deps = xref.get("module_deps", {})
    if not module_deps:
        print("  No module dependency data found in xref-index.")
        return

    print("")
    print("  CYCLIC MODULE DEPENDENCIES")
    print("  " + "=" * 50)
    print("")

    # --- Tarjan SCCs (strongly connected components) ---
    sccs = _find_cycles_tarjan(module_deps)

    print("  Strongly Connected Components (mutual dependency clusters):")
    print("")

    if not sccs:
        print("    No cyclic dependencies found!")
        print("")
    else:
        total_modules_in_cycles = sum(len(s) for s in sccs)
        print("    Found {:,d} SCC{} involving {:,d} modules".format(
            len(sccs), "s" if len(sccs) != 1 else "",
            total_modules_in_cycles))
        print("")

        shown = 0
        for i, scc in enumerate(sccs):
            if shown >= limit:
                print("    ... and {:,d} more SCCs (use -n {:,d} to see all)".format(
                    len(sccs) - shown, len(sccs)))
                break

            # Classify layers in SCC
            layers = defaultdict(list)
            for mod in scc:
                layer, _ = _get_layer(mod)
                layers[layer].append(mod)

            layer_summary = ", ".join(
                "{}x{}".format(len(mods), layer)
                for layer, mods in sorted(layers.items())
            )

            print("    SCC #{}: {:,d} modules [{}]".format(
                i + 1, len(scc), layer_summary))

            # Show edges within SCC
            scc_set = set(scc)
            edges = []
            for mod in scc:
                for dep in module_deps.get(mod, []):
                    if dep in scc_set:
                        edges.append((mod, dep))

            for src, dst in sorted(edges)[:20]:
                src_layer, _ = _get_layer(src)
                dst_layer, _ = _get_layer(dst)
                violation = ""
                if src_layer in _LAYER_VIOLATIONS and dst_layer in _LAYER_VIOLATIONS.get(src_layer, set()):
                    violation = "  [LAYER VIOLATION]"
                print("      {} -> {}{}".format(src, dst, violation))

            if len(edges) > 20:
                print("      ... and {:,d} more edges".format(len(edges) - 20))
            print("")
            shown += 1

    # --- Simple cycles (short paths) ---
    print("  Simple cycles (depth <= {:d}):".format(max_depth))
    print("")

    simple_cycles = _find_simple_cycles_dfs(module_deps, max_depth=max_depth)

    if not simple_cycles:
        print("    No simple cycles found at depth <= {:d}.".format(max_depth))
        print("")
    else:
        # Group by length
        by_length = defaultdict(list)
        for cycle in simple_cycles:
            by_length[len(cycle)].append(cycle)

        for length in sorted(by_length.keys()):
            group = by_length[length]
            print("    {:,d}-module cycles: {:,d} found".format(length, len(group)))
            shown_in_group = 0
            for cycle in group:
                if shown_in_group >= 10:
                    print("      ... and {:,d} more".format(len(group) - shown_in_group))
                    break
                chain = " -> ".join(cycle) + " -> " + cycle[0]
                print("      {}".format(chain))
                shown_in_group += 1
            print("")

    # Summary
    total_modules = len(module_deps)
    modules_in_sccs = set()
    for scc in sccs:
        modules_in_sccs.update(scc)

    print("  Summary:")
    print("    Total modules in graph:    {:>6,d}".format(total_modules))
    print("    SCCs found:                {:>6,d}".format(len(sccs)))
    print("    Modules in cycles:         {:>6,d}  ({:.1f}%)".format(
        len(modules_in_sccs),
        100.0 * len(modules_in_sccs) / total_modules if total_modules else 0))
    print("    Simple cycles (depth<={}):  {:>6,d}".format(
        max_depth, len(simple_cycles)))
    print("")


# ---------------------------------------------------------------------------
# cmd_god_classes — Classes with excessive complexity
# ---------------------------------------------------------------------------

def cmd_god_classes(base_dir, threshold=100, limit=50):
    """Find god classes by combined method + field + importer count."""
    mi = _load_method_index(base_dir)
    fi = _load_field_index(base_dir)
    ci = _load_class_index(base_dir)
    xref = _load_xref(base_dir)

    if not mi or not fi or not ci:
        return

    class_methods = mi.get("class_methods", {})
    class_fields = fi.get("class_fields", {})
    class_info = ci.get("classes", {})
    imported_by = xref.get("class_imported_by", {}) if xref else {}

    print("")
    print("  GOD CLASSES (threshold >= {:,d})".format(threshold))
    print("  " + "=" * 50)
    print("")

    # Build score for each class
    entries = []
    for class_name, info_list in class_info.items():
        if not info_list:
            continue

        info = info_list[0]
        module = info.get("module", "unknown")

        method_count = len(class_methods.get(class_name, []))
        field_count = len(class_fields.get(class_name, []))
        importer_count = len(imported_by.get(class_name, []))
        lines = info.get("lines", 0)

        # Composite score: methods + fields + importers
        score = method_count + field_count + importer_count

        if score >= threshold:
            entries.append({
                "class": class_name,
                "module": module,
                "methods": method_count,
                "fields": field_count,
                "importers": importer_count,
                "lines": lines,
                "score": score,
            })

    entries.sort(key=lambda e: -e["score"])

    if not entries:
        print("  No classes found with score >= {:,d}.".format(threshold))
        print("  Try a lower threshold (e.g. --threshold 50).")
        print("")
        return

    # By module stats
    by_module = defaultdict(list)
    for e in entries:
        by_module[e["module"]].append(e)

    # Breakdown by component
    print("  Score = methods + fields + importers (classes that import this one)")
    print("")
    print("  {:35s}  {:25s}  {:>5s}  {:>5s}  {:>5s}  {:>5s}  {:>6s}".format(
        "CLASS", "MODULE", "MTHDS", "FLDS", "IMPRS", "LINES", "SCORE"))
    print("  " + "-" * 95)

    shown = 0
    for e in entries:
        if shown >= limit:
            remaining = len(entries) - shown
            print("  ... and {:,d} more (use -n {:,d} to see all)".format(
                remaining, len(entries)))
            break

        cls_d = e["class"] if len(e["class"]) <= 35 else e["class"][:32] + "..."
        mod_d = e["module"] if len(e["module"]) <= 25 else e["module"][:22] + "..."
        print("  {:35s}  {:25s}  {:>5,d}  {:>5,d}  {:>5,d}  {:>5,d}  {:>6,d}".format(
            cls_d, mod_d,
            e["methods"], e["fields"], e["importers"], e["lines"],
            e["score"]))
        shown += 1

    print("")

    # Top modules with most god classes
    print("  Top modules with god classes:")
    top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:15]
    for mod, mod_entries in top_mods:
        avg_score = sum(e["score"] for e in mod_entries) / len(mod_entries)
        max_score = max(e["score"] for e in mod_entries)
        print("    {:35s}  {:>4,d} classes  avg={:>6,.0f}  max={:>6,d}".format(
            mod, len(mod_entries), avg_score, max_score))
    if len(by_module) > 15:
        print("    ... and {:,d} more modules".format(len(by_module) - 15))
    print("")

    # Summary
    total_classes = len(class_info)
    print("  Summary:")
    print("    Total classes analyzed:     {:>8,d}".format(total_classes))
    print("    God classes (score>={}):  {:>8,d}  ({:.1f}%)".format(
        threshold, len(entries),
        100.0 * len(entries) / total_classes if total_classes else 0))
    print("    Modules with god classes:   {:>8,d}".format(len(by_module)))
    if entries:
        print("    Highest score:              {:>8,d}  ({})".format(
            entries[0]["score"], entries[0]["class"]))
        avg_all = sum(e["score"] for e in entries) / len(entries)
        print("    Average score (god only):   {:>8,.1f}".format(avg_all))
    print("")


# ---------------------------------------------------------------------------
# cmd_layer_check — Layer violation detection
# ---------------------------------------------------------------------------

def cmd_layer_check(base_dir, module_filter=None):
    """Check for layer violations: RT modules should not import WB/UX modules."""
    xref = _load_xref(base_dir)
    if not xref:
        return

    module_deps = xref.get("module_deps", {})
    if not module_deps:
        print("  No module dependency data found in xref-index.")
        return

    print("")
    print("  LAYER CHECK — Architectural Violations")
    print("  " + "=" * 50)
    print("")
    print("  Rules: RT must NOT import WB/UX (lower layer must not depend on higher)")
    print("")

    violations = []

    modules_to_check = [module_filter] if module_filter else sorted(module_deps.keys())

    for mod in modules_to_check:
        if module_filter and mod not in module_deps:
            print("  Module '{}' not found in dependency graph.".format(mod))
            print("")
            return

        src_layer, src_rank = _get_layer(mod)
        if src_layer not in _LAYER_VIOLATIONS:
            continue

        forbidden_layers = _LAYER_VIOLATIONS[src_layer]
        deps = module_deps.get(mod, [])

        for dep in deps:
            dep_layer, dep_rank = _get_layer(dep)
            if dep_layer in forbidden_layers:
                violations.append({
                    "source": mod,
                    "source_layer": src_layer,
                    "target": dep,
                    "target_layer": dep_layer,
                })

    if module_filter:
        # Detailed report for a single module
        mod_deps = module_deps.get(module_filter, [])
        src_layer, _ = _get_layer(module_filter)

        # Group deps by layer
        deps_by_layer = defaultdict(list)
        for dep in sorted(mod_deps):
            dep_layer, _ = _get_layer(dep)
            deps_by_layer[dep_layer].append(dep)

        print("  Module: {} (layer: {})".format(module_filter, src_layer))
        print("  Dependencies: {:,d} total".format(len(mod_deps)))
        print("")

        forbidden = _LAYER_VIOLATIONS.get(src_layer, set())

        for layer in ["RT", "WB", "UX", "DOC", "OTHER"]:
            deps_in_layer = deps_by_layer.get(layer, [])
            if not deps_in_layer:
                continue

            is_violation = layer in forbidden
            marker = "  [VIOLATION]" if is_violation else ""
            print("  {} dependencies ({:d}):{}".format(layer, len(deps_in_layer), marker))
            for dep in deps_in_layer:
                flag = " *** VIOLATION ***" if is_violation else ""
                print("    {}{}".format(dep, flag))
            print("")

        mod_violations = [v for v in violations if v["source"] == module_filter]
        if mod_violations:
            print("  VIOLATIONS FOUND: {:,d}".format(len(mod_violations)))
            print("  {} ({}) imports from higher layers:".format(
                module_filter, src_layer))
            for v in mod_violations:
                print("    -> {} ({})".format(v["target"], v["target_layer"]))
        else:
            print("  No layer violations found for '{}'.".format(module_filter))
        print("")
        return

    # Full scan report
    if not violations:
        print("  No layer violations found across all modules!")
        print("")
        return

    # Group by source module
    by_source = defaultdict(list)
    for v in violations:
        by_source[v["source"]].append(v)

    # Group by violation type (RT->WB, RT->UX)
    by_type = defaultdict(list)
    for v in violations:
        key = "{} -> {}".format(v["source_layer"], v["target_layer"])
        by_type[key].append(v)

    print("  Violation types:")
    for vtype, items in sorted(by_type.items()):
        sources = set(v["source"] for v in items)
        targets = set(v["target"] for v in items)
        print("    {:10s}  {:>4,d} violations  {:>4,d} source modules  {:>4,d} target modules".format(
            vtype, len(items), len(sources), len(targets)))
    print("")

    print("  {:35s}  {:5s}  {:35s}  {:5s}".format(
        "SOURCE MODULE", "LAYER", "TARGET MODULE", "LAYER"))
    print("  " + "-" * 85)

    # Sort by number of violations per source
    sorted_sources = sorted(by_source.items(), key=lambda x: -len(x[1]))

    shown = 0
    for src_mod, src_violations in sorted_sources:
        for v in sorted(src_violations, key=lambda x: x["target"]):
            if shown >= 200:
                remaining = len(violations) - shown
                print("  ... and {:,d} more violations".format(remaining))
                break

            src_d = v["source"] if len(v["source"]) <= 35 else v["source"][:32] + "..."
            tgt_d = v["target"] if len(v["target"]) <= 35 else v["target"][:32] + "..."
            print("  {:35s}  {:5s}  {:35s}  {:5s}".format(
                src_d, v["source_layer"], tgt_d, v["target_layer"]))
            shown += 1
        else:
            continue
        break

    print("")

    # Top violators
    print("  Top violating modules (by violation count):")
    for src_mod, src_violations in sorted_sources[:15]:
        targets = set(v["target"] for v in src_violations)
        target_layers = set(v["target_layer"] for v in src_violations)
        print("    {:35s}  {:>3,d} violations  -> [{}]".format(
            src_mod, len(src_violations), ", ".join(sorted(target_layers))))
    if len(sorted_sources) > 15:
        print("    ... and {:,d} more modules".format(len(sorted_sources) - 15))
    print("")

    # Summary
    total_rt = sum(1 for m in module_deps if _get_layer(m)[0] == "RT")
    violating_rt = len(by_source)

    print("  Summary:")
    print("    Total RT modules:           {:>6,d}".format(total_rt))
    print("    RT modules with violations: {:>6,d}  ({:.1f}%)".format(
        violating_rt,
        100.0 * violating_rt / total_rt if total_rt else 0))
    print("    Total violations:           {:>6,d}".format(len(violations)))
    print("    Unique targets (WB/UX):     {:>6,d}".format(
        len(set(v["target"] for v in violations))))
    print("")
