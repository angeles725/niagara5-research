"""
Deprecated Chain Analysis commands for Module Navigator (Phase 23).

Commands:
  deprecated [--module mod]            List @Deprecated classes and methods
    -n <N>                             Limit results (default 50)
  deprecated-users <class> [method]    Who uses something deprecated
    -n <N>                             Limit results (default 50)
  deprecated-risk [--module mod]       Deprecated usage risk summary
    -n <N>                             Limit results (default 50)

Scans source files for @Deprecated annotations on-demand.
Cross-references with callgraph-index and xref-index.
No builder needed.
"""

import json
import os
import re
from collections import defaultdict


# ---------------------------------------------------------------------------
# Global cache
# ---------------------------------------------------------------------------

_deprecated_cache = None  # {class_name: {"module", "deprecated_class", "deprecated_methods": [...]}}


# ---------------------------------------------------------------------------
# Index loading (reuses existing loaders, on-demand cached)
# ---------------------------------------------------------------------------

def _load_class_index(base_dir):
    """Load class-index.json (on-demand, cached)."""
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


def _load_callgraph(base_dir):
    """Load callgraph-index.json via callgraph module (cached)."""
    from module_nav_lib.callgraph import load_callgraph
    return load_callgraph(base_dir)


def _load_xref(base_dir):
    """Load xref-index.json (on-demand, cached)."""
    from module_nav_lib.xref import load_xref
    return load_xref(base_dir)


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
# @Deprecated scanner (on-demand, cached)
# ---------------------------------------------------------------------------

def _scan_deprecated(base_dir):
    """Scan all source files for @Deprecated annotations. Cached after first call."""
    global _deprecated_cache
    if _deprecated_cache is not None:
        return _deprecated_cache

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return {}

    source_root = ci_data.get("_meta", {}).get("source", "")
    classes = ci_data.get("classes", {})

    cache = {}  # class_name -> {module, deprecated_class, deprecated_methods}

    for cls_name, entries in classes.items():
        for entry in entries:
            if entry.get("outer_class"):
                continue

            path = os.path.join(source_root, entry["path"])
            if not os.path.isfile(path):
                continue

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            if "@Deprecated" not in content:
                continue

            lines = content.split("\n")
            deprecated_class = False
            deprecated_methods = []

            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped.startswith("@Deprecated"):
                    continue

                # Look at next non-annotation, non-empty line
                is_class = False
                target_name = None
                for j in range(i + 1, min(i + 8, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line or next_line.startswith("@"):
                        continue

                    if ("class " in next_line or "interface " in next_line
                            or "enum " in next_line):
                        is_class = True
                    else:
                        # Extract method name
                        m = re.search(
                            r'(?:public|protected|private|static|final|abstract|synchronized|native|'
                            r'default|transient|volatile|\s)+'
                            r'(?:<[^>]+>\s+)?'
                            r'(?:[\w\[\]<>,\s?]+\s+)?'
                            r'(\w+)\s*\(',
                            next_line
                        )
                        if m:
                            target_name = m.group(1)
                        else:
                            # Simpler fallback: find word before (
                            m2 = re.search(r'(\w+)\s*\(', next_line)
                            if m2:
                                target_name = m2.group(1)
                    break

                if is_class:
                    deprecated_class = True
                elif target_name:
                    deprecated_methods.append(target_name)

            if deprecated_class or deprecated_methods:
                key = cls_name
                # Handle duplicate class names across modules
                if key in cache and cache[key]["module"] != entry["module"]:
                    key = "{}@{}".format(cls_name, entry["module"])

                cache[key] = {
                    "module": entry["module"],
                    "class_name": cls_name,
                    "deprecated_class": deprecated_class,
                    "deprecated_methods": deprecated_methods,
                }

    _deprecated_cache = cache
    return cache


# ---------------------------------------------------------------------------
# deprecated [--module mod] [-n N]
# ---------------------------------------------------------------------------

def cmd_deprecated(base_dir, module_filter=None, limit=50):
    """List @Deprecated classes and methods."""
    import sys
    import time

    t0 = time.time()
    sys.stdout.write("\n  Scanning source files for @Deprecated...")
    sys.stdout.flush()

    cache = _scan_deprecated(base_dir)

    elapsed = time.time() - t0
    if elapsed > 0.5:
        print(" {:.1f}s".format(elapsed))
    else:
        print(" OK")

    if not cache:
        print("\n  No @Deprecated annotations found.\n")
        return

    # Apply module filter
    entries = list(cache.values())
    if module_filter:
        entries = [e for e in entries if e["module"] == module_filter]

    if not entries:
        print("\n  No @Deprecated annotations found in module '{}'.\n".format(
            module_filter))
        return

    # Sort by module, then class name
    entries.sort(key=lambda e: (e["module"], e["class_name"]))

    # Statistics
    total_deprecated_classes = sum(1 for e in entries if e["deprecated_class"])
    total_deprecated_methods = sum(len(e["deprecated_methods"]) for e in entries)
    modules = set(e["module"] for e in entries)

    print("")
    print("  DEPRECATED API INVENTORY")
    print("  " + "=" * 55)
    if module_filter:
        print("  Module filter: {}".format(module_filter))
    print("  Files with @Deprecated:     {:>6,}".format(len(entries)))
    print("  Deprecated classes:         {:>6,}".format(total_deprecated_classes))
    print("  Deprecated methods:         {:>6,}".format(total_deprecated_methods))
    print("  Modules with deprecated:    {:>6,}".format(len(modules)))
    print("")

    # Show by module
    by_module = defaultdict(list)
    for e in entries:
        by_module[e["module"]].append(e)

    shown = 0
    for mod in sorted(by_module.keys()):
        if shown >= limit:
            break

        mod_entries = by_module[mod]
        mod_classes = sum(1 for e in mod_entries if e["deprecated_class"])
        mod_methods = sum(len(e["deprecated_methods"]) for e in mod_entries)
        print("  [{}] {} files, {} classes, {} methods".format(
            mod, len(mod_entries), mod_classes, mod_methods))

        for e in mod_entries:
            if shown >= limit:
                break
            shown += 1

            markers = []
            if e["deprecated_class"]:
                markers.append("CLASS")
            if e["deprecated_methods"]:
                markers.append("{} methods".format(len(e["deprecated_methods"])))

            print("    {:40s} {}".format(
                e["class_name"], ", ".join(markers)))

            if e["deprecated_methods"]:
                for m in e["deprecated_methods"][:5]:
                    print("      @Deprecated {}()".format(m))
                if len(e["deprecated_methods"]) > 5:
                    print("      ... and {} more".format(
                        len(e["deprecated_methods"]) - 5))

    remaining = len(entries) - shown
    if remaining > 0:
        print("\n  ... {} more files (use -n {} to see all)".format(
            remaining, len(entries)))
    print("")


# ---------------------------------------------------------------------------
# deprecated-users <class> [method] [-n N]
# ---------------------------------------------------------------------------

def cmd_deprecated_users(base_dir, class_name, method_name=None, limit=50):
    """Find who uses a deprecated class or method."""
    import sys
    import time

    t0 = time.time()
    sys.stdout.write("\n  Scanning for deprecated usage...")
    sys.stdout.flush()

    # First, verify the class/method is actually deprecated
    cache = _scan_deprecated(base_dir)

    # Find the deprecated entry
    dep_entry = None
    for key, entry in cache.items():
        if entry["class_name"] == class_name:
            dep_entry = entry
            break

    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}

    target_module = _get_module_for_class(class_name, ci_classes)

    # Even if not found in deprecated scan, still show who uses it
    is_deprecated_class = dep_entry and dep_entry["deprecated_class"] if dep_entry else False
    is_deprecated_method = (dep_entry and method_name
                            and method_name in dep_entry.get("deprecated_methods", [])) if dep_entry else False

    elapsed = time.time() - t0
    if elapsed > 0.5:
        print(" {:.1f}s".format(elapsed))
    else:
        print(" OK")

    if method_name:
        _deprecated_users_method(base_dir, class_name, method_name,
                                 is_deprecated_method, target_module,
                                 ci_classes, limit)
    else:
        _deprecated_users_class(base_dir, class_name, is_deprecated_class,
                                target_module, ci_classes, limit)


def _deprecated_users_class(base_dir, class_name, is_deprecated, target_module,
                            ci_classes, limit):
    """Show classes that import a deprecated class."""
    xref_data = _load_xref(base_dir)
    cg = _load_callgraph(base_dir)

    # Get importers from xref
    importers = set()
    importer_modules = defaultdict(list)
    if xref_data:
        class_imported_by = xref_data.get("class_imported_by", {})
        imported_by = class_imported_by.get(class_name, [])
        for imp_cls in imported_by:
            importers.add(imp_cls)
            mod = _get_module_for_class(imp_cls, ci_classes)
            importer_modules[mod].append(imp_cls)

    # Get callers from callgraph
    caller_classes = set()
    caller_modules = defaultdict(list)
    if cg:
        calls = cg.get("calls", {})
        from module_nav_lib.callgraph import _build_called_by
        called_by = _build_called_by(cg)

        prefix = class_name + "."
        for callee_key in called_by:
            if callee_key.startswith(prefix):
                for caller in called_by[callee_key]:
                    dot = caller.rfind(".")
                    if dot > 0:
                        caller_cls = caller[:dot]
                        if caller_cls != class_name:
                            caller_classes.add(caller_cls)
                            mod = _get_module_for_class(caller_cls, ci_classes)
                            caller_modules[mod].append(caller_cls)

    # Combine
    all_users = importers | caller_classes
    all_modules = set(importer_modules.keys()) | set(caller_modules.keys())
    all_modules.discard("?")

    # Print
    print("")
    label = "@Deprecated " if is_deprecated else ""
    print("  USERS OF {}{}".format(label, class_name))
    print("  " + "=" * 55)
    print("  Target module:    {}".format(target_module))
    if not is_deprecated:
        print("  WARNING: {} is NOT marked @Deprecated".format(class_name))
    print("")
    print("  Importers (xref):     {:>6,}".format(len(importers)))
    print("  Caller classes:       {:>6,}".format(len(caller_classes)))
    print("  Total user classes:   {:>6,}".format(len(all_users)))
    print("  Affected modules:     {:>6,}".format(len(all_modules)))
    print("")

    if importers:
        print("  IMPORTERS ({} classes):".format(len(importers)))
        shown = 0
        for mod in sorted(importer_modules.keys(), key=lambda m: -len(importer_modules[m])):
            if shown >= limit:
                break
            classes = importer_modules[mod]
            print("    [{}] ({})".format(mod, len(classes)))
            for c in sorted(set(classes))[:8]:
                shown += 1
                print("      {}".format(c))
            if len(set(classes)) > 8:
                print("      ... and {} more".format(len(set(classes)) - 8))
        print("")

    if caller_classes:
        print("  CALLERS ({} classes):".format(len(caller_classes)))
        shown = 0
        for mod in sorted(caller_modules.keys(), key=lambda m: -len(set(caller_modules[m]))):
            if shown >= limit:
                break
            classes = sorted(set(caller_modules[mod]))
            print("    [{}] ({})".format(mod, len(classes)))
            for c in classes[:8]:
                shown += 1
                print("      {}".format(c))
            if len(classes) > 8:
                print("      ... and {} more".format(len(classes) - 8))
        print("")

    if all_modules:
        print("  MODULE SUMMARY ({})".format(len(all_modules)))
        print("  " + "-" * 50)
        mod_counts = defaultdict(int)
        for mod, cls_list in importer_modules.items():
            mod_counts[mod] += len(set(cls_list))
        for mod, cls_list in caller_modules.items():
            mod_counts[mod] += len(set(cls_list))

        for mod in sorted(all_modules, key=lambda m: -mod_counts.get(m, 0)):
            count = mod_counts.get(mod, 0)
            same = mod == target_module
            marker = "" if same else " *"
            print("    {:30s}  {:>5,} user classes{}".format(mod, count, marker))

        external = [m for m in all_modules if m != target_module]
        if external:
            print("")
            print("  * = external module")
        print("")


def _deprecated_users_method(base_dir, class_name, method_name,
                             is_deprecated, target_module, ci_classes, limit):
    """Show callers of a deprecated method."""
    cg = _load_callgraph(base_dir)
    if not cg:
        print("\n  ERROR: callgraph-index.json required.\n")
        return

    from module_nav_lib.callgraph import _build_called_by
    called_by = _build_called_by(cg)

    target_key = "{}.{}".format(class_name, method_name)
    callers = called_by.get(target_key, [])

    # Group by module
    caller_modules = defaultdict(list)
    for caller in callers:
        dot = caller.rfind(".")
        if dot > 0:
            caller_cls = caller[:dot]
            caller_method = caller[dot + 1:]
            mod = _get_module_for_class(caller_cls, ci_classes)
            caller_modules[mod].append("{}.{}".format(caller_cls, caller_method))

    all_modules = set(caller_modules.keys())
    all_modules.discard("?")

    # Print
    print("")
    label = "@Deprecated " if is_deprecated else ""
    print("  CALLERS OF {}{}.{}()".format(label, class_name, method_name))
    print("  " + "=" * 55)
    print("  Target module:    {}".format(target_module))
    if not is_deprecated:
        print("  WARNING: {}.{}() is NOT marked @Deprecated".format(
            class_name, method_name))
    print("")
    print("  Direct callers:       {:>6,}".format(len(callers)))
    print("  Affected modules:     {:>6,}".format(len(all_modules)))
    print("")

    shown = 0
    for mod in sorted(caller_modules.keys(), key=lambda m: -len(caller_modules[m])):
        if shown >= limit:
            break
        methods = caller_modules[mod]
        print("  [{}] ({} callers)".format(mod, len(methods)))
        for m in sorted(methods)[:10]:
            shown += 1
            print("    {}".format(m))
        if len(methods) > 10:
            print("    ... and {} more".format(len(methods) - 10))
    print("")


# ---------------------------------------------------------------------------
# deprecated-risk [--module mod] [-n N]
# ---------------------------------------------------------------------------

def cmd_deprecated_risk(base_dir, module_filter=None, limit=50):
    """Show deprecated usage risk: how many refs to deprecated APIs per module."""
    import sys
    import time

    t0 = time.time()
    sys.stdout.write("\n  Analyzing deprecated risk...")
    sys.stdout.flush()

    cache = _scan_deprecated(base_dir)
    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}
    xref_data = _load_xref(base_dir)
    cg = _load_callgraph(base_dir)

    elapsed = time.time() - t0
    if elapsed > 0.5:
        print(" {:.1f}s".format(elapsed))
    else:
        print(" OK")

    if not cache:
        print("\n  No @Deprecated annotations found.\n")
        return

    # Build reverse callgraph
    called_by = {}
    if cg:
        from module_nav_lib.callgraph import _build_called_by
        called_by = _build_called_by(cg)

    class_imported_by = {}
    if xref_data:
        class_imported_by = xref_data.get("class_imported_by", {})

    # For each module, count:
    #  - deprecated APIs it DEFINES (debt)
    #  - deprecated APIs it USES from OTHER modules (risk)
    module_debt = defaultdict(lambda: {"classes": 0, "methods": 0})
    module_risk = defaultdict(lambda: {"imports": 0, "calls": 0, "unique_deprecated": set()})

    for key, entry in cache.items():
        cls_name = entry["class_name"]
        dep_module = entry["module"]

        # Count debt
        if entry["deprecated_class"]:
            module_debt[dep_module]["classes"] += 1
        module_debt[dep_module]["methods"] += len(entry["deprecated_methods"])

        # Find who uses this deprecated class (from other modules)
        imported_by = class_imported_by.get(cls_name, [])
        for imp_cls in imported_by:
            imp_mod = _get_module_for_class(imp_cls, ci_classes)
            if imp_mod != dep_module and imp_mod != "?":
                module_risk[imp_mod]["imports"] += 1
                module_risk[imp_mod]["unique_deprecated"].add(cls_name)

        # Find who calls deprecated methods (from other modules)
        for method in entry["deprecated_methods"]:
            callee_key = "{}.{}".format(cls_name, method)
            callers = called_by.get(callee_key, [])
            for caller in callers:
                dot = caller.rfind(".")
                if dot > 0:
                    caller_cls = caller[:dot]
                    caller_mod = _get_module_for_class(caller_cls, ci_classes)
                    if caller_mod != dep_module and caller_mod != "?":
                        module_risk[caller_mod]["calls"] += 1
                        module_risk[caller_mod]["unique_deprecated"].add(
                            "{}.{}".format(cls_name, method))

    # Apply module filter
    if module_filter:
        # Show risk for specific module
        _print_module_risk_detail(module_filter, module_debt, module_risk, cache, limit)
        return

    # Summary: rank modules by risk
    total_dep_classes = sum(d["classes"] for d in module_debt.values())
    total_dep_methods = sum(d["methods"] for d in module_debt.values())
    total_risk_modules = len(module_risk)

    print("")
    print("  DEPRECATED USAGE RISK ANALYSIS")
    print("  " + "=" * 55)
    print("  Total deprecated classes:   {:>6,}".format(total_dep_classes))
    print("  Total deprecated methods:   {:>6,}".format(total_dep_methods))
    print("  Modules defining deprecated:{:>6,}".format(len(module_debt)))
    print("  Modules using deprecated:   {:>6,}".format(total_risk_modules))
    print("")

    # Top modules by RISK (using deprecated from others)
    if module_risk:
        print("  TOP MODULES AT RISK (using deprecated APIs):")
        print("  {:30s}  {:>6s}  {:>6s}  {:>6s}  {:>6s}".format(
            "Module", "Impts", "Calls", "Total", "Uniq"))
        print("  " + "-" * 62)

        risk_items = []
        for mod, risk in module_risk.items():
            total = risk["imports"] + risk["calls"]
            risk_items.append((mod, risk["imports"], risk["calls"], total,
                               len(risk["unique_deprecated"])))

        risk_items.sort(key=lambda x: -x[3])

        shown = 0
        for mod, imports, calls, total, uniq in risk_items:
            if shown >= limit:
                break
            shown += 1

            level = "LOW"
            if uniq > 10:
                level = "CRITICAL"
            elif uniq > 5:
                level = "HIGH"
            elif uniq > 2:
                level = "MEDIUM"

            print("  {:30s}  {:>6,}  {:>6,}  {:>6,}  {:>6,}  {}".format(
                mod, imports, calls, total, uniq, level))

        remaining = len(risk_items) - shown
        if remaining > 0:
            print("\n  ... {} more modules (use -n {} to see all)".format(
                remaining, len(risk_items)))
        print("")

    # Top modules by DEBT (defining deprecated)
    if module_debt:
        print("  TOP MODULES WITH DEPRECATED DEBT:")
        print("  {:30s}  {:>6s}  {:>6s}  {:>6s}".format(
            "Module", "Cls", "Meth", "Total"))
        print("  " + "-" * 55)

        debt_items = []
        for mod, debt in module_debt.items():
            total = debt["classes"] + debt["methods"]
            debt_items.append((mod, debt["classes"], debt["methods"], total))

        debt_items.sort(key=lambda x: -x[3])

        shown = 0
        for mod, cls, meth, total in debt_items:
            if shown >= limit:
                break
            shown += 1
            print("  {:30s}  {:>6,}  {:>6,}  {:>6,}".format(
                mod, cls, meth, total))

        remaining = len(debt_items) - shown
        if remaining > 0:
            print("\n  ... {} more modules (use -n {} to see all)".format(
                remaining, len(debt_items)))
        print("")


def _print_module_risk_detail(module_name, module_debt, module_risk, cache, limit):
    """Detailed deprecated risk for a specific module."""
    debt = module_debt.get(module_name, {"classes": 0, "methods": 0})
    risk = module_risk.get(module_name, {"imports": 0, "calls": 0, "unique_deprecated": set()})

    print("")
    print("  DEPRECATED RISK: {}".format(module_name))
    print("  " + "=" * 55)
    print("")
    print("  DEBT (deprecated APIs defined here):")
    print("    Deprecated classes:  {:>6,}".format(debt["classes"]))
    print("    Deprecated methods:  {:>6,}".format(debt["methods"]))
    print("")

    # List deprecated items in this module
    module_deprecated = [e for e in cache.values() if e["module"] == module_name]
    if module_deprecated:
        print("  Deprecated items in {}:".format(module_name))
        shown = 0
        for e in sorted(module_deprecated, key=lambda x: x["class_name"]):
            if shown >= limit:
                break
            shown += 1
            if e["deprecated_class"]:
                print("    @Deprecated class {}".format(e["class_name"]))
            for m in e["deprecated_methods"]:
                print("    @Deprecated {}.{}()".format(e["class_name"], m))
        print("")

    print("  RISK (deprecated APIs used from OTHER modules):")
    print("    Imports of deprecated:  {:>6,}".format(risk["imports"]))
    print("    Calls to deprecated:    {:>6,}".format(risk["calls"]))
    print("    Unique deprecated used: {:>6,}".format(len(risk["unique_deprecated"])))
    print("")

    if risk["unique_deprecated"]:
        print("  Deprecated APIs used:")
        for dep in sorted(risk["unique_deprecated"]):
            print("    {}".format(dep))
        print("")

    total_risk = risk["imports"] + risk["calls"]
    uniq = len(risk["unique_deprecated"])
    if uniq > 10:
        level = "CRITICAL"
    elif uniq > 5:
        level = "HIGH"
    elif uniq > 2:
        level = "MEDIUM"
    elif uniq > 0:
        level = "LOW"
    else:
        level = "NONE"

    print("  Overall risk level: {}".format(level))
    print("")
