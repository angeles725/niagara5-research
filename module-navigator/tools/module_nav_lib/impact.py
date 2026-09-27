"""
Impact Analysis commands for Module Navigator (Phase 21).

Commands:
  impact <class>                     Transitive impact: callers + importers + modules
  impact <class> <method>            Impact of changing a specific method
  impact <class> --depth N           Depth of transitive analysis (default 3)

Combines callgraph-index, xref-index, and class-index on-demand.
No builder needed.
"""

import json
import os
from collections import defaultdict, deque


# ---------------------------------------------------------------------------
# Index loading (reuses existing loaders, on-demand cached)
# ---------------------------------------------------------------------------

def _load_callgraph(base_dir):
    """Load callgraph-index.json via callgraph module (cached)."""
    from module_nav_lib.callgraph import load_callgraph
    return load_callgraph(base_dir)


def _load_xref(base_dir):
    """Load xref-index.json (on-demand, cached)."""
    from module_nav_lib.xref import load_xref
    return load_xref(base_dir)


def _load_class_index(base_dir):
    """Load class-index.json (on-demand, cached)."""
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


def _get_module_family(module_name):
    """Extract module family (e.g. alarm-rt -> alarm, workbench-wb -> workbench)."""
    for suffix in ("-rt", "-wb", "-ux", "-se", "-doc"):
        if module_name.endswith(suffix):
            return module_name[:-len(suffix)]
    return module_name


# ---------------------------------------------------------------------------
# Risk assessment
# ---------------------------------------------------------------------------

def _assess_risk(affected_modules, total_direct, total_transitive, target_module):
    """Calculate risk level based on impact spread."""
    target_family = _get_module_family(target_module)

    # Count modules outside the target family
    external_modules = set()
    for mod in affected_modules:
        if _get_module_family(mod) != target_family:
            external_modules.add(mod)

    num_affected = len(affected_modules)
    num_external = len(external_modules)

    if num_external == 0 and num_affected <= 1:
        return "LOW", "All impact within same module"
    elif num_external == 0:
        return "LOW", "All impact within {} family ({} modules)".format(
            target_family, num_affected)
    elif num_external <= 3:
        return "MEDIUM", "{} external module(s) affected: {}".format(
            num_external, ", ".join(sorted(external_modules)[:3]))
    elif num_external <= 10:
        return "HIGH", "{} external modules affected across {} families".format(
            num_external, len(set(_get_module_family(m) for m in external_modules)))
    else:
        return "CRITICAL", "{} external modules affected — widely used API".format(
            num_external)


# ---------------------------------------------------------------------------
# impact <class> <method> — method-level impact
# ---------------------------------------------------------------------------

def cmd_impact(base_dir, class_name, method_name=None, depth=3):
    """Transitive impact analysis for a class or method."""
    if method_name:
        _impact_method(base_dir, class_name, method_name, depth)
    else:
        _impact_class(base_dir, class_name, depth)


def _impact_method(base_dir, class_name, method_name, depth):
    """BFS impact analysis for a specific method."""
    cg = _load_callgraph(base_dir)
    if not cg:
        return

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return
    ci_classes = ci_data.get("classes", {})

    # Build reverse callgraph (callee -> callers)
    from module_nav_lib.callgraph import _build_called_by
    called_by = _build_called_by(cg)

    target_key = "{}.{}".format(class_name, method_name)
    target_module = _get_module_for_class(class_name, ci_classes)

    if target_module == "?":
        # Try to find the class
        print("")
        print("  Class '{}' not found in class-index.".format(class_name))
        print("")
        return

    # BFS: expand callers transitively
    # Each entry in queue: (method_key, depth_level)
    visited = set()
    visited.add(target_key)
    queue = deque()

    # Seed with direct callers
    direct_callers = called_by.get(target_key, [])
    for caller in direct_callers:
        if caller not in visited:
            queue.append((caller, 1))
            visited.add(caller)

    # Track by depth level
    by_depth = defaultdict(list)  # depth -> [(method_key, module)]
    affected_modules = set()
    affected_classes = set()

    for caller in direct_callers:
        dot = caller.rfind('.')
        cls = caller[:dot] if dot > 0 else caller
        mod = _get_module_for_class(cls, ci_classes)
        by_depth[1].append((caller, mod))
        affected_modules.add(mod)
        affected_classes.add(cls)

    # BFS expansion
    while queue:
        current, current_depth = queue.popleft()
        if current_depth >= depth:
            continue

        callers = called_by.get(current, [])
        for caller in callers:
            if caller not in visited:
                visited.add(caller)
                next_depth = current_depth + 1
                dot = caller.rfind('.')
                cls = caller[:dot] if dot > 0 else caller
                mod = _get_module_for_class(cls, ci_classes)
                by_depth[next_depth].append((caller, mod))
                affected_modules.add(mod)
                affected_classes.add(cls)
                queue.append((caller, next_depth))

    # Calculate totals
    total_direct = len(by_depth.get(1, []))
    total_transitive = sum(len(v) for d, v in by_depth.items() if d > 1)
    total_all = total_direct + total_transitive

    # Remove "?" from affected modules
    affected_modules.discard("?")

    risk_level, risk_reason = _assess_risk(
        affected_modules, total_direct, total_transitive, target_module)

    # Print results
    print("")
    print("  IMPACT ANALYSIS: {}.{}".format(class_name, method_name))
    print("  " + "=" * 60)
    print("  Target module:  {}".format(target_module))
    print("  Analysis depth: {}".format(depth))
    print("")
    print("  SUMMARY:")
    print("    Direct callers:     {:>6,}".format(total_direct))
    print("    Transitive callers: {:>6,}".format(total_transitive))
    print("    Total affected:     {:>6,}".format(total_all))
    print("    Affected classes:   {:>6,}".format(len(affected_classes)))
    print("    Affected modules:   {:>6,}".format(len(affected_modules)))
    print("    Risk: {} — {}".format(risk_level, risk_reason))
    print("")

    # Print by depth level
    for d in sorted(by_depth.keys()):
        entries = by_depth[d]
        label = "DIRECT" if d == 1 else "DEPTH {}".format(d)
        print("  {} ({} callers):".format(label, len(entries)))

        # Group by module for readability
        by_mod = defaultdict(list)
        for method_key, mod in entries:
            by_mod[mod].append(method_key)

        for mod in sorted(by_mod.keys()):
            methods = by_mod[mod]
            print("    [{}] ({})".format(mod, len(methods)))
            for m in sorted(methods)[:10]:
                print("      {}".format(m))
            if len(methods) > 10:
                print("      ... and {} more".format(len(methods) - 10))
        print("")

    # Module summary
    if affected_modules:
        print("  AFFECTED MODULES ({})".format(len(affected_modules)))
        print("  " + "-" * 50)

        mod_counts = defaultdict(int)
        for d in by_depth:
            for _, mod in by_depth[d]:
                mod_counts[mod] += 1

        for mod, count in sorted(mod_counts.items(), key=lambda x: -x[1]):
            same_family = _get_module_family(mod) == _get_module_family(target_module)
            marker = "" if same_family else " *"
            print("    {:30s}  {:>5,} callers{}".format(mod, count, marker))

        external = [m for m in affected_modules
                    if _get_module_family(m) != _get_module_family(target_module)]
        if external:
            print("")
            print("  * = external module (different family from {})".format(target_module))
        print("")


# ---------------------------------------------------------------------------
# impact <class> — class-level impact
# ---------------------------------------------------------------------------

def _impact_class(base_dir, class_name, depth):
    """Impact analysis for an entire class (importers + callers of all methods)."""
    cg = _load_callgraph(base_dir)
    if not cg:
        return

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return
    ci_classes = ci_data.get("classes", {})

    xref_data = _load_xref(base_dir)

    target_module = _get_module_for_class(class_name, ci_classes)
    if target_module == "?":
        print("")
        print("  Class '{}' not found in class-index.".format(class_name))
        print("")
        return

    # 1. Find all importers of this class (from xref-index)
    importers = set()
    importer_modules = set()
    if xref_data:
        class_imported_by = xref_data.get("class_imported_by", {})
        imported_by = class_imported_by.get(class_name, [])
        for imp_cls in imported_by:
            importers.add(imp_cls)
            mod = _get_module_for_class(imp_cls, ci_classes)
            importer_modules.add(mod)

    # 2. Find all methods of this class in callgraph
    calls = cg.get("calls", {})
    prefix = class_name + "."
    class_methods = [k for k in calls if k.startswith(prefix)]

    # 3. Find all callers of all methods (BFS transitive)
    from module_nav_lib.callgraph import _build_called_by
    called_by = _build_called_by(cg)

    # Also find callers of methods that have class_name as callee
    method_callers = defaultdict(set)  # method -> set of direct callers
    all_caller_keys = set()

    for mkey in class_methods:
        callers = called_by.get(mkey, [])
        for c in callers:
            method_callers[mkey].add(c)
            all_caller_keys.add(c)

    # Also check called_by for keys matching ClassName.* pattern
    for callee_key in called_by:
        if callee_key.startswith(prefix):
            for c in called_by[callee_key]:
                method_callers[callee_key].add(c)
                all_caller_keys.add(c)

    # BFS transitive expansion from all direct callers
    visited = set()
    for mkey in class_methods:
        visited.add(mkey)

    affected_modules = set()
    affected_classes = set()
    by_depth = defaultdict(list)

    # Depth 1: direct callers
    for caller in all_caller_keys:
        visited.add(caller)
        dot = caller.rfind('.')
        cls = caller[:dot] if dot > 0 else caller
        mod = _get_module_for_class(cls, ci_classes)
        by_depth[1].append((caller, mod))
        affected_modules.add(mod)
        affected_classes.add(cls)

    # BFS deeper levels
    queue = deque()
    for caller in all_caller_keys:
        queue.append((caller, 1))

    while queue:
        current, current_depth = queue.popleft()
        if current_depth >= depth:
            continue

        callers = called_by.get(current, [])
        for caller in callers:
            if caller not in visited:
                visited.add(caller)
                next_depth = current_depth + 1
                dot = caller.rfind('.')
                cls = caller[:dot] if dot > 0 else caller
                mod = _get_module_for_class(cls, ci_classes)
                by_depth[next_depth].append((caller, mod))
                affected_modules.add(mod)
                affected_classes.add(cls)
                queue.append((caller, next_depth))

    # Add importer modules
    affected_modules.update(importer_modules)
    affected_modules.discard("?")

    total_direct = len(by_depth.get(1, []))
    total_transitive = sum(len(v) for d, v in by_depth.items() if d > 1)

    risk_level, risk_reason = _assess_risk(
        affected_modules, total_direct, total_transitive, target_module)

    # Print results
    print("")
    print("  IMPACT ANALYSIS: {}".format(class_name))
    print("  " + "=" * 60)
    print("  Target module:  {}".format(target_module))
    print("  Analysis depth: {}".format(depth))
    print("")
    print("  SUMMARY:")
    print("    Importers (xref):   {:>6,}".format(len(importers)))
    print("    Direct callers:     {:>6,}".format(total_direct))
    print("    Transitive callers: {:>6,}".format(total_transitive))
    print("    Affected classes:   {:>6,}".format(len(affected_classes | importers)))
    print("    Affected modules:   {:>6,}".format(len(affected_modules)))
    print("    Methods in class:   {:>6,}".format(len(class_methods)))
    print("    Risk: {} — {}".format(risk_level, risk_reason))
    print("")

    # Top imported-by classes
    if importers:
        print("  IMPORTERS ({} classes):".format(len(importers)))
        imp_by_mod = defaultdict(list)
        for imp_cls in importers:
            mod = _get_module_for_class(imp_cls, ci_classes)
            imp_by_mod[mod].append(imp_cls)

        for mod in sorted(imp_by_mod.keys(), key=lambda m: -len(imp_by_mod[m])):
            classes = imp_by_mod[mod]
            print("    [{}] ({})".format(mod, len(classes)))
            for c in sorted(classes)[:5]:
                print("      {}".format(c))
            if len(classes) > 5:
                print("      ... and {} more".format(len(classes) - 5))
        print("")

    # Callers by depth
    for d in sorted(by_depth.keys()):
        entries = by_depth[d]
        if not entries:
            continue
        label = "DIRECT CALLERS" if d == 1 else "DEPTH {} CALLERS".format(d)
        print("  {} ({}):".format(label, len(entries)))

        by_mod = defaultdict(list)
        for method_key, mod in entries:
            by_mod[mod].append(method_key)

        for mod in sorted(by_mod.keys(), key=lambda m: -len(by_mod[m])):
            methods = by_mod[mod]
            print("    [{}] ({})".format(mod, len(methods)))
            for m in sorted(methods)[:8]:
                print("      {}".format(m))
            if len(methods) > 8:
                print("      ... and {} more".format(len(methods) - 8))
        print("")

    # Module summary
    if affected_modules:
        print("  AFFECTED MODULES ({})".format(len(affected_modules)))
        print("  " + "-" * 50)

        mod_counts = defaultdict(int)
        for d in by_depth:
            for _, mod in by_depth[d]:
                mod_counts[mod] += 1
        # Add importer counts
        for imp_cls in importers:
            mod = _get_module_for_class(imp_cls, ci_classes)
            if mod != "?":
                mod_counts[mod] = mod_counts.get(mod, 0)  # ensure key exists

        for mod in sorted(affected_modules, key=lambda m: -mod_counts.get(m, 0)):
            count = mod_counts.get(mod, 0)
            same_family = _get_module_family(mod) == _get_module_family(target_module)
            marker = "" if same_family else " *"
            if count > 0:
                print("    {:30s}  {:>5,} refs{}".format(mod, count, marker))
            else:
                print("    {:30s}  (importer only){}".format(mod, marker))

        external = [m for m in affected_modules
                    if _get_module_family(m) != _get_module_family(target_module)]
        if external:
            print("")
            print("  * = external module (different family from {})".format(target_module))
        print("")
