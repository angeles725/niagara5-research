"""
Niagara Lifecycle Analysis for Module Navigator (Phase 29).

Commands:
  lifecycle <class>                    Lifecycle methods implemented by a class
  lifecycle-scan [--module mod] [-n N] Classes with lifecycle overrides
  lifecycle --pattern <name>           Classes implementing a specific lifecycle

Traces how BComponents implement started/stopped/changed/added/removed/
atSteadyState/serviceStarted/serviceStopped.  Critical for understanding
runtime behaviour of services, drivers, and points.

No builder needed -- uses method-index + inheritance on-demand.
"""

from collections import defaultdict


# ---------------------------------------------------------------------------
# Lifecycle method definitions
# ---------------------------------------------------------------------------

# Core BComponent lifecycle methods (order = typical call order)
LIFECYCLE_METHODS = [
    "started",
    "stopped",
    "changed",
    "added",
    "removed",
    "atSteadyState",
    "serviceStarted",
    "serviceStopped",
]

# Descriptions for help output
LIFECYCLE_DESC = {
    "started":         "Called when component enters RUNNING state",
    "stopped":         "Called when component leaves RUNNING state",
    "changed":         "Called when a slot value changes",
    "added":           "Called when a child is added",
    "removed":         "Called when a child is removed",
    "atSteadyState":   "Called once after entire station reaches steady state",
    "serviceStarted":  "Called when the owning service starts",
    "serviceStopped":  "Called when the owning service stops",
}

LIFECYCLE_SET = frozenset(LIFECYCLE_METHODS)


# ---------------------------------------------------------------------------
# Index loading (reuse existing loaders, on-demand cached)
# ---------------------------------------------------------------------------

def _load_method_index(base_dir):
    from module_nav_lib.methods import load_method_index
    return load_method_index(base_dir)


def _load_class_index(base_dir):
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


def _load_inheritance(base_dir):
    from module_nav_lib.hierarchy import load_inheritance
    return load_inheritance(base_dir)


# ---------------------------------------------------------------------------
# Build lifecycle map (cached)
# ---------------------------------------------------------------------------

_lifecycle_cache = {}


def _build_lifecycle_map(base_dir, module_filter=None):
    """Build map of class -> list of lifecycle methods it overrides.

    Returns dict: class_name -> {
        module, methods: [method_name, ...], count, is_service, is_driver
    }
    """
    cache_key = module_filter or "__all__"
    if cache_key in _lifecycle_cache:
        return _lifecycle_cache[cache_key]

    mi = _load_method_index(base_dir)
    ci_data = _load_class_index(base_dir)
    inh = _load_inheritance(base_dir)

    if not mi or not ci_data:
        return {}

    methods_idx = mi.get("methods", {})
    ci_classes = ci_data.get("classes", {})

    # Build module lookup
    class_module = {}
    for cname, entries in ci_classes.items():
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            class_module[cname] = top[0].get("module", "?")
        elif entries:
            class_module[cname] = entries[0].get("module", "?")

    # Service / Driver ancestry (for categorisation)
    # NOTE: inheritance.json uses "parent_to_children" (NOT "children")
    service_descendants = set()
    driver_descendants = set()
    if inh:
        parent_to_children = inh.get("parent_to_children", {})

        def _collect(root, dest):
            stack = [root]
            while stack:
                c = stack.pop()
                if c in parent_to_children:
                    for ch in parent_to_children[c]:
                        dest.add(ch)
                        stack.append(ch)

        _collect("BAbstractService", service_descendants)
        service_descendants.add("BAbstractService")
        for drv_root in ("BDevice", "BDeviceNetwork", "BDeviceFolder"):
            _collect(drv_root, driver_descendants)
            driver_descendants.add(drv_root)

    # Scan lifecycle methods
    result = {}
    for lc_method in LIFECYCLE_METHODS:
        entries = methods_idx.get(lc_method, [])
        for e in entries:
            cname = e.get("class", "")
            mod = e.get("module", class_module.get(cname, "?"))

            if module_filter and mod != module_filter:
                continue

            if cname not in result:
                result[cname] = {
                    "module": mod,
                    "methods": [],
                    "count": 0,
                    "is_service": cname in service_descendants,
                    "is_driver": cname in driver_descendants,
                }
            if lc_method not in result[cname]["methods"]:
                result[cname]["methods"].append(lc_method)
                result[cname]["count"] = len(result[cname]["methods"])

    _lifecycle_cache[cache_key] = result
    return result


# ---------------------------------------------------------------------------
# lifecycle <class>
# ---------------------------------------------------------------------------

def cmd_lifecycle(base_dir, class_name):
    """Show lifecycle methods implemented by a specific class."""
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: class-index.json not found.")
        return

    ci_classes = ci_data.get("classes", {})

    # Case-insensitive lookup
    actual_name = class_name
    if class_name not in ci_classes:
        lower = class_name.lower()
        for k in ci_classes:
            if k.lower() == lower:
                actual_name = k
                break
        else:
            print("  Class '{}' not found.".format(class_name))
            return

    entries = ci_classes[actual_name]
    top = [e for e in entries if not e.get("outer_class")]
    if top:
        module = top[0].get("module", "?")
    elif entries:
        module = entries[0].get("module", "?")
    else:
        module = "?"

    # Get inheritance chain
    inh = _load_inheritance(base_dir)
    chain = []
    if inh:
        # NOTE: inheritance.json uses "class_to_chain" (NOT "parents")
        class_to_chain = inh.get("class_to_chain", {})
        chain = class_to_chain.get(actual_name, [])

    # Check which lifecycle methods this class implements
    mi = _load_method_index(base_dir)
    if not mi:
        print("  ERROR: method-index.json not found.")
        return

    methods_idx = mi.get("methods", {})

    implemented = []
    for lc in LIFECYCLE_METHODS:
        mlist = methods_idx.get(lc, [])
        for e in mlist:
            if e.get("class") == actual_name:
                implemented.append({
                    "name": lc,
                    "signature": e.get("signature", ""),
                    "line": e.get("line", 0),
                })
                break

    # Check what ancestors implement
    ancestor_lifecycle = {}
    if chain:
        for ancestor in chain[1:]:  # skip self
            for lc in LIFECYCLE_METHODS:
                mlist = methods_idx.get(lc, [])
                for e in mlist:
                    if e.get("class") == ancestor:
                        if lc not in ancestor_lifecycle:
                            ancestor_lifecycle[lc] = ancestor
                        break

    # Categorize
    lc_map = _build_lifecycle_map(base_dir)
    info = lc_map.get(actual_name, {})
    is_service = info.get("is_service", False)
    is_driver = info.get("is_driver", False)

    # Output
    print("")
    print("  LIFECYCLE: {}".format(actual_name))
    print("  " + "=" * 55)
    print("  Module: {}".format(module))

    role = "BComponent"
    if is_service:
        role = "Service"
    elif is_driver:
        role = "Driver"
    print("  Role: {}".format(role))

    if chain:
        print("  Chain: {}".format(" -> ".join(chain[:6])))
        if len(chain) > 6:
            print("         ... ({} total ancestors)".format(len(chain)))
    print("")

    if not implemented:
        print("  No lifecycle overrides found.")
        if ancestor_lifecycle:
            print("")
            print("  INHERITED LIFECYCLE (from ancestors):")
            for lc in LIFECYCLE_METHODS:
                if lc in ancestor_lifecycle:
                    print("    {:20s}  (from {})".format(lc, ancestor_lifecycle[lc]))
        print("")
        return

    print("  IMPLEMENTED ({}/{}):" .format(len(implemented), len(LIFECYCLE_METHODS)))
    for m in implemented:
        desc = LIFECYCLE_DESC.get(m["name"], "")
        line_info = "  line {}".format(m["line"]) if m["line"] else ""
        print("    {:20s} {}{}".format(m["name"], desc, line_info))
    print("")

    # Not implemented
    not_impl = [lc for lc in LIFECYCLE_METHODS if lc not in
                [m["name"] for m in implemented]]
    if not_impl:
        print("  NOT IMPLEMENTED:")
        for lc in not_impl:
            inherited = ancestor_lifecycle.get(lc)
            suffix = "  (inherited from {})".format(inherited) if inherited else ""
            print("    {:20s}{}".format(lc, suffix))
        print("")

    # Relevant ancestors
    if ancestor_lifecycle:
        print("  ANCESTOR OVERRIDES:")
        shown = set()
        for lc in LIFECYCLE_METHODS:
            if lc in ancestor_lifecycle and lc not in shown:
                print("    {:20s}  in {}".format(lc, ancestor_lifecycle[lc]))
                shown.add(lc)
        print("")


# ---------------------------------------------------------------------------
# lifecycle-scan [--module mod] [-n N]
# ---------------------------------------------------------------------------

def cmd_lifecycle_scan(base_dir, module_filter=None, limit=50):
    """Scan for lifecycle overrides across classes (index-only, fast)."""
    lc_map = _build_lifecycle_map(base_dir, module_filter=module_filter)

    if not lc_map:
        if module_filter:
            print("  No lifecycle overrides found in module '{}'.".format(module_filter))
        else:
            print("  No lifecycle overrides found.")
        return

    total = len(lc_map)
    by_module = defaultdict(int)
    by_method = defaultdict(int)
    by_count = defaultdict(int)  # how many lifecycle methods per class
    services_with_lc = 0
    drivers_with_lc = 0

    for cname, info in lc_map.items():
        by_module[info["module"]] += 1
        by_count[info["count"]] += 1
        for m in info["methods"]:
            by_method[m] += 1
        if info["is_service"]:
            services_with_lc += 1
        if info["is_driver"]:
            drivers_with_lc += 1

    scope = module_filter if module_filter else "ALL modules"
    print("")
    print("  LIFECYCLE SCAN: {}".format(scope))
    print("  " + "=" * 55)
    print("")
    print("  Classes with lifecycle overrides: {:>6,}".format(total))
    print("  Modules with lifecycle overrides: {:>6,}".format(len(by_module)))
    print("  Services with lifecycle:          {:>6,}".format(services_with_lc))
    print("  Drivers with lifecycle:           {:>6,}".format(drivers_with_lc))
    print("")

    # Per-method counts
    print("  LIFECYCLE METHOD USAGE:")
    for lc in LIFECYCLE_METHODS:
        count = by_method.get(lc, 0)
        bar = "#" * min(count // 20, 40)
        print("    {:20s} {:>5,}  {}".format(lc, count, bar))
    print("")

    # Overrides per class distribution
    print("  OVERRIDES PER CLASS:")
    for n in sorted(by_count.keys()):
        print("    {} lifecycle methods: {:>5,} classes".format(n, by_count[n]))
    print("")

    # Top modules
    top_modules = sorted(by_module.items(), key=lambda x: x[1], reverse=True)
    print("  TOP MODULES ({} with lifecycle):".format(len(top_modules)))
    for mod, count in top_modules[:15]:
        print("    {:40s} {:>4,} classes".format(mod, count))
    if len(top_modules) > 15:
        print("    ... and {} more modules".format(len(top_modules) - 15))
    print("")

    # Top classes by lifecycle count
    top_classes = sorted(lc_map.items(),
                         key=lambda x: x[1]["count"], reverse=True)
    show = top_classes[:limit]
    print("  TOP CLASSES ({} total, showing {}):".format(total, len(show)))
    for cname, info in show:
        role = ""
        if info["is_service"]:
            role = " [Service]"
        elif info["is_driver"]:
            role = " [Driver]"
        methods_str = ", ".join(info["methods"])
        print("    {:35s} {:20s} {}/{}{}  ({})".format(
            cname, info["module"],
            info["count"], len(LIFECYCLE_METHODS),
            role, methods_str))
    print("")


# ---------------------------------------------------------------------------
# lifecycle --pattern <name>
# ---------------------------------------------------------------------------

def cmd_lifecycle_pattern(base_dir, pattern_name, module_filter=None, limit=50):
    """Show classes that implement a specific lifecycle method."""
    if pattern_name not in LIFECYCLE_SET:
        print("  Unknown lifecycle pattern: '{}'".format(pattern_name))
        print("  Available: {}".format(", ".join(LIFECYCLE_METHODS)))
        return

    mi = _load_method_index(base_dir)
    if not mi:
        print("  ERROR: method-index.json not found.")
        return

    ci_data = _load_class_index(base_dir)
    inh = _load_inheritance(base_dir)

    methods_idx = mi.get("methods", {})
    entries = methods_idx.get(pattern_name, [])

    if module_filter:
        entries = [e for e in entries if e.get("module") == module_filter]

    # Service / Driver check
    service_descendants = set()
    driver_descendants = set()
    if inh:
        parent_to_children = inh.get("parent_to_children", {})

        def _collect(root, dest):
            stack = [root]
            while stack:
                c = stack.pop()
                if c in parent_to_children:
                    for ch in parent_to_children[c]:
                        dest.add(ch)
                        stack.append(ch)

        _collect("BAbstractService", service_descendants)
        service_descendants.add("BAbstractService")
        for drv_root in ("BDevice", "BDeviceNetwork", "BDeviceFolder"):
            _collect(drv_root, driver_descendants)
            driver_descendants.add(drv_root)

    total = len(entries)
    by_module = defaultdict(int)
    for e in entries:
        by_module[e.get("module", "?")] += 1

    scope = module_filter if module_filter else "ALL modules"
    print("")
    print("  LIFECYCLE PATTERN: {} ({})".format(pattern_name, scope))
    print("  " + "=" * 55)
    print("  {}".format(LIFECYCLE_DESC.get(pattern_name, "")))
    print("")
    print("  Classes implementing: {:>6,}".format(total))
    print("  Modules:              {:>6,}".format(len(by_module)))
    print("")

    show = entries[:limit]
    print("  CLASSES (showing {}):".format(len(show)))
    for e in show:
        cname = e.get("class", "?")
        mod = e.get("module", "?")
        line = e.get("line", 0)
        role = ""
        if cname in service_descendants:
            role = " [Service]"
        elif cname in driver_descendants:
            role = " [Driver]"
        line_info = "  line {}".format(line) if line else ""
        print("    {:35s} {:25s}{}{}".format(cname, mod, role, line_info))

    if total > limit:
        print("    ... and {} more (use -n to show more)".format(total - limit))
    print("")

    # Top modules
    top_mods = sorted(by_module.items(), key=lambda x: x[1], reverse=True)
    print("  TOP MODULES:")
    for mod, count in top_mods[:10]:
        print("    {:40s} {:>4,} classes".format(mod, count))
    if len(top_mods) > 10:
        print("    ... and {} more".format(len(top_mods) - 10))
    print("")
