"""
Alarm Domain Tracer commands for Module Navigator (Phase 38).

Traces the complete alarm chain: creation -> routing -> ack -> clearing.
Alarms are the heart of Building Automation Systems (BAS).

Uses inheritance.json + callgraph-index.json + method-index.json +
annotations-index.json + class-index.json on-demand. No builder.

Commands:
  alarm-flow [--module mod] [-n N]   Classes in the alarm chain by role
  alarm-types                        Alarm types defined in the corpus
  alarm-trace <class>                Role of a class in the alarm flow
"""

import json
import os
from collections import defaultdict


# ---------------------------------------------------------------------------
# Constants — Alarm domain hierarchy roots and key methods
# ---------------------------------------------------------------------------

# Root classes that define the alarm domain via inheritance
_ALARM_ROOTS = {
    "BAlarmService":     "service",
    "BAlarmRecipient":   "recipient",
    "BAlarmSourceExt":   "source_ext",
    "BAlarmClass":       "source",
    "BAlarmAlgorithm":   "algorithm",
    "BAlarmAcknowledger": "acknowledger",
    "BAlarmDeviceExt":   "device_ext",
    "BAbstractAlarmFilter": "filter",
    "BAlarmRecord":      "data",
}

# Interface that marks alarm source implementations
_ALARM_INTERFACES = [
    "BIAlarmSource",
    "BIAlarmRecordDecorator",
    "BIAlarmServiceView",
]

# Key methods that define alarm flow (searched in method-index + callgraph)
_ALARM_METHODS = {
    # Routing
    "doRouteAlarm":    "routing",
    "doRouteAlarmAck": "routing",
    "routeAlarm":      "routing",
    # Firing / creation
    "fireAlarm":       "creation",
    "fireAlarmAcked":  "creation",
    "postAlarm":       "creation",
    "generateAlarm":   "creation",
    # Acknowledgment
    "ackAlarm":        "acknowledgment",
    "doAckAlarm":      "acknowledgment",
    "acknowledgeAlarm": "acknowledgment",
    "ackAlarmBySource": "acknowledgment",
    "ackAlarmByUuid":  "acknowledgment",
    # Clearing
    "doAlarmClear":    "clearing",
    "clearAlarm":      "clearing",
    # Handling / consuming
    "handleAlarm":     "handling",
    "onAlarm":         "handling",
    "processAlarm":    "handling",
    "toAlarmRecord":   "data",
}

# Role classification based on methods + inheritance
_ROLE_KEYWORDS = {
    "source": ["fireAlarm", "fireAlarmAcked", "postAlarm", "generateAlarm",
               "BAlarmClass", "BAlarmSourceExt", "BIAlarmSource"],
    "router": ["doRouteAlarm", "routeAlarm", "doRouteAlarmAck",
               "BAlarmService", "BAbstractAlarmFilter"],
    "consumer": ["handleAlarm", "onAlarm", "processAlarm",
                 "BAlarmRecipient", "BConsoleRecipient"],
    "acknowledger": ["ackAlarm", "doAckAlarm", "acknowledgeAlarm",
                     "ackAlarmBySource", "BAlarmAcknowledger"],
    "algorithm": ["BAlarmAlgorithm", "BFaultAlgorithm", "BOffnormalAlgorithm"],
    "device": ["BAlarmDeviceExt"],
    "filter": ["BAbstractAlarmFilter", "BAlarmFilter", "BEscalationFilter"],
    "data": ["toAlarmRecord", "BAlarmRecord"],
}


# ---------------------------------------------------------------------------
# Index loaders (lazy, cached)
# ---------------------------------------------------------------------------

_inheritance_cache = None
_callgraph_cache = None
_method_index_cache = None
_annotations_cache = None
_class_index_cache = None


def _load_inheritance(base_dir):
    global _inheritance_cache
    if _inheritance_cache is not None:
        return _inheritance_cache
    path = os.path.join(base_dir, "indexes", "inheritance.json")
    if not os.path.isfile(path):
        print("ERROR: inheritance.json not found.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _inheritance_cache = json.load(f)
    return _inheritance_cache


def _load_callgraph(base_dir):
    global _callgraph_cache
    if _callgraph_cache is not None:
        return _callgraph_cache
    path = os.path.join(base_dir, "indexes", "callgraph-index.json")
    if not os.path.isfile(path):
        print("ERROR: callgraph-index.json not found.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _callgraph_cache = json.load(f)
    return _callgraph_cache


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


def _load_annotations(base_dir):
    global _annotations_cache
    if _annotations_cache is not None:
        return _annotations_cache
    path = os.path.join(base_dir, "indexes", "annotations-index.json")
    if not os.path.isfile(path):
        print("ERROR: annotations-index.json not found.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _annotations_cache = json.load(f)
    return _annotations_cache


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


def _get_class_module(base_dir, class_name):
    ci = _load_class_index(base_dir)
    if not ci:
        return "unknown"
    entries = ci.get("classes", {}).get(class_name, [])
    if entries:
        return entries[0].get("module", "unknown")
    return "unknown"


# ---------------------------------------------------------------------------
# Alarm domain detection helpers
# ---------------------------------------------------------------------------

def _get_all_descendants(inh, root_class):
    """Get all descendants of a root class from inheritance index."""
    children_map = inh.get("parent_to_children", {})
    result = set()
    queue = [root_class]
    while queue:
        current = queue.pop(0)
        kids = children_map.get(current, [])
        for kid in kids:
            name = kid if isinstance(kid, str) else kid.get("class", kid.get("name", ""))
            if name and name not in result:
                result.add(name)
                queue.append(name)
    return result


def _get_interface_implementors(inh, interface_name):
    """Get all implementors of an interface from inheritance index."""
    impls = inh.get("interface_to_implementors", {}).get(interface_name, [])
    result = set()
    for imp in impls:
        name = imp if isinstance(imp, str) else imp.get("class", imp.get("name", ""))
        if name:
            result.add(name)
    return result


def _find_alarm_classes_by_inheritance(base_dir):
    """Find all alarm-related classes via inheritance hierarchy.

    Returns dict: class_name -> {module, roles, ancestors}
    """
    inh = _load_inheritance(base_dir)
    if not inh:
        return {}

    results = {}

    # 1) Descendants of alarm root classes
    for root, role in _ALARM_ROOTS.items():
        descendants = _get_all_descendants(inh, root)
        # Include the root itself
        for cls in descendants | {root}:
            if cls not in results:
                results[cls] = {
                    "module": _get_class_module(base_dir, cls),
                    "roles": set(),
                    "ancestors": set(),
                    "methods": [],
                }
            results[cls]["roles"].add(role)
            if cls != root:
                results[cls]["ancestors"].add(root)

    # 2) Interface implementors
    for iface in _ALARM_INTERFACES:
        impls = _get_interface_implementors(inh, iface)
        for cls in impls:
            if cls not in results:
                results[cls] = {
                    "module": _get_class_module(base_dir, cls),
                    "roles": set(),
                    "ancestors": set(),
                    "methods": [],
                }
            results[cls]["roles"].add("source")
            results[cls]["ancestors"].add(iface)

    return results


def _find_alarm_classes_by_methods(base_dir, module_filter=None):
    """Find classes that declare alarm-related methods via method-index.

    Returns dict: class_name -> [{method, phase, module, line}]
    """
    mi = _load_method_index(base_dir)
    if not mi:
        return {}

    methods_idx = mi.get("methods", {})
    results = defaultdict(list)

    for mname, phase in _ALARM_METHODS.items():
        entries = methods_idx.get(mname, [])
        for entry in entries:
            cls = entry.get("class", "")
            mod = entry.get("module", "")
            line = entry.get("line", 0)

            if module_filter and mod != module_filter:
                continue

            results[cls].append({
                "method": mname,
                "phase": phase,
                "module": mod,
                "line": line,
            })

    return dict(results)


def _classify_alarm_role(class_name, inheritance_roles, method_phases):
    """Classify a class's role in the alarm flow based on inheritance + methods.

    Returns set of roles: source, router, consumer, acknowledger, algorithm, device, filter, data
    """
    roles = set()
    all_names = set()

    # From inheritance
    all_names.update(inheritance_roles)

    # From method phases
    for m in method_phases:
        phase = m.get("phase", "")
        if phase == "routing":
            all_names.add("router")
        elif phase == "creation":
            all_names.add("source")
        elif phase == "acknowledgment":
            all_names.add("acknowledger")
        elif phase == "clearing":
            all_names.add("router")
        elif phase == "handling":
            all_names.add("consumer")
        elif phase == "data":
            all_names.add("data")

    # Map to final roles
    for r in all_names:
        if r in ("source", "source_ext"):
            roles.add("source")
        elif r in ("router", "service"):
            roles.add("router")
        elif r in ("consumer", "recipient"):
            roles.add("consumer")
        elif r == "acknowledger":
            roles.add("acknowledger")
        elif r == "algorithm":
            roles.add("algorithm")
        elif r == "device_ext":
            roles.add("device")
        elif r == "filter":
            roles.add("filter")
        elif r == "data":
            roles.add("data")

    return roles if roles else {"related"}


# ---------------------------------------------------------------------------
# cmd_alarm_flow — Classes in the alarm chain
# ---------------------------------------------------------------------------

def cmd_alarm_flow(base_dir, module_filter=None, limit=50):
    """List classes in the alarm chain, classified by role."""
    inh_classes = _find_alarm_classes_by_inheritance(base_dir)
    method_classes = _find_alarm_classes_by_methods(base_dir, module_filter)

    # Merge
    all_classes = set(inh_classes.keys()) | set(method_classes.keys())

    if module_filter:
        # Filter inheritance results by module too
        filtered = set()
        for cls in all_classes:
            inh_info = inh_classes.get(cls, {})
            mod = inh_info.get("module", _get_class_module(base_dir, cls))
            if mod == module_filter:
                filtered.add(cls)
            elif cls in method_classes:
                filtered.add(cls)
        all_classes = filtered

    if not all_classes:
        msg = "  No alarm-related classes found"
        if module_filter:
            msg += " in module '{}'".format(module_filter)
        print(msg + ".")
        return

    # Build entries
    entries = []
    by_module = defaultdict(list)
    by_role = defaultdict(list)

    for cls in sorted(all_classes):
        inh_info = inh_classes.get(cls, {})
        inh_roles = inh_info.get("roles", set())
        methods = method_classes.get(cls, [])
        module = inh_info.get("module", "")
        if not module and methods:
            module = methods[0].get("module", "unknown")
        if not module:
            module = _get_class_module(base_dir, cls)

        roles = _classify_alarm_role(cls, inh_roles, methods)

        # Count distinct method phases
        method_phases = set(m["phase"] for m in methods)

        entry = {
            "class": cls,
            "module": module,
            "roles": roles,
            "methods": methods,
            "method_count": len(methods),
            "phases": method_phases,
            "ancestors": inh_info.get("ancestors", set()),
        }
        entries.append(entry)
        by_module[module].append(entry)
        for r in roles:
            by_role[r].append(entry)

    entries.sort(key=lambda e: (-len(e["roles"]), -e["method_count"]))

    scope = " in {}".format(module_filter) if module_filter else ""
    print("")
    print("  ALARM DOMAIN FLOW{} ({:,} classes, {:,} modules)".format(
        scope, len(entries), len(by_module)))
    print("")

    # Role breakdown
    print("  By alarm role:")
    role_order = ["source", "router", "consumer", "acknowledger",
                  "algorithm", "device", "filter", "data", "related"]
    for role in role_order:
        items = by_role.get(role, [])
        if items:
            modules = len(set(e["module"] for e in items))
            print("    {:15s}  {:>5,d} classes  {:>4,d} modules".format(
                role, len(items), modules))
    print("")

    # Flow summary (the alarm lifecycle)
    print("  Alarm lifecycle flow:")
    flow_steps = [
        ("source", "CREATION",     "fireAlarm, postAlarm"),
        ("router", "ROUTING",      "doRouteAlarm, routeAlarm"),
        ("filter", "FILTERING",    "doRouteAlarm (filtered)"),
        ("consumer", "HANDLING",   "handleAlarm, onAlarm"),
        ("acknowledger", "ACK",    "ackAlarm, doAckAlarm"),
    ]
    for role, label, methods_desc in flow_steps:
        items = by_role.get(role, [])
        count = len(items)
        arrow = "-->" if count > 0 else "   "
        print("    {} {:12s}  {:>4d} classes  ({})".format(
            arrow, label, count, methods_desc))
    print("")

    # Top modules
    print("  Top modules:")
    top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:15]
    for mod, items in top_mods:
        roles_set = set()
        for e in items:
            roles_set.update(e["roles"])
        print("    {:35s}  {:>4,d} classes  [{}]".format(
            mod, len(items), ", ".join(sorted(roles_set))))
    if len(by_module) > 15:
        print("    ... and {:,} more modules".format(len(by_module) - 15))
    print("")

    # Detailed listing
    print("  {:35s}  {:25s}  {:>4s}  {}".format(
        "CLASS", "MODULE", "MTHS", "ROLES"))
    print("  " + "-" * 100)

    shown = 0
    for e in entries:
        if shown >= limit:
            remaining = len(entries) - shown
            print("  ... and {:,} more (use -n {:,} to see all)".format(
                remaining, len(entries)))
            break

        cls_d = e["class"] if len(e["class"]) <= 35 else e["class"][:32] + "..."
        mod_d = e["module"] if len(e["module"]) <= 25 else e["module"][:22] + "..."
        roles_str = ", ".join(sorted(e["roles"]))
        print("  {:35s}  {:25s}  {:>4d}  {}".format(
            cls_d, mod_d, e["method_count"], roles_str))
        shown += 1

    print("")

    # Summary
    total_methods = sum(e["method_count"] for e in entries)
    all_phases = set()
    for e in entries:
        all_phases.update(e["phases"])

    print("  Summary:")
    print("    Total classes:       {:>6,d}".format(len(entries)))
    print("    Total modules:       {:>6,d}".format(len(by_module)))
    print("    Alarm methods found: {:>6,d}".format(total_methods))
    print("    Flow phases covered: {}".format(
        ", ".join(sorted(all_phases)) if all_phases else "none"))
    print("")


# ---------------------------------------------------------------------------
# cmd_alarm_types — Alarm types defined in the corpus
# ---------------------------------------------------------------------------

def cmd_alarm_types(base_dir):
    """List all alarm types organized by category."""
    inh = _load_inheritance(base_dir)
    if not inh:
        return

    print("")
    print("  ALARM TYPES IN CORPUS")
    print("  " + "=" * 40)
    print("")

    total_classes = 0
    total_modules = set()

    categories = [
        ("Alarm Services", "BAlarmService",
         "Central orchestrators that route and manage alarms"),
        ("Alarm Recipients", "BAlarmRecipient",
         "Endpoints that receive and handle routed alarms"),
        ("Alarm Sources (Ext)", "BAlarmSourceExt",
         "Extensions that generate alarms on components"),
        ("Alarm Classes", "BAlarmClass",
         "Alarm function blocks for creating alarm logic"),
        ("Alarm Algorithms", "BAlarmAlgorithm",
         "Algorithms that evaluate conditions and trigger alarms"),
        ("Alarm Acknowledgers", "BAlarmAcknowledger",
         "Handlers for alarm acknowledgment responses"),
        ("Alarm Device Extensions", "BAlarmDeviceExt",
         "Protocol-specific device alarm extensions"),
        ("Alarm Filters", "BAbstractAlarmFilter",
         "Filters that control alarm routing"),
    ]

    for cat_name, root_class, description in categories:
        descendants = _get_all_descendants(inh, root_class)

        if not descendants and root_class not in (inh.get("children", {})):
            continue

        # Group by module
        by_module = defaultdict(list)
        for cls in sorted(descendants):
            mod = _get_class_module(base_dir, cls)
            by_module[mod].append(cls)
            total_modules.add(mod)

        total_classes += len(descendants)
        root_mod = _get_class_module(base_dir, root_class)

        print("  {} ({:d} types, root: {} [{}])".format(
            cat_name, len(descendants), root_class, root_mod))
        print("  {}".format(description))
        print("")

        if not descendants:
            print("    (no descendants found)")
            print("")
            continue

        for mod in sorted(by_module.keys()):
            classes = by_module[mod]
            cls_str = ", ".join(classes[:5])
            if len(classes) > 5:
                cls_str += " ... +{:d}".format(len(classes) - 5)
            print("    {:30s}  {:>3d}  {}".format(mod, len(classes), cls_str))

        print("")

    # Interface implementors
    for iface in _ALARM_INTERFACES:
        impls = _get_interface_implementors(inh, iface)
        if impls:
            by_module = defaultdict(list)
            for cls in sorted(impls):
                mod = _get_class_module(base_dir, cls)
                by_module[mod].append(cls)
                total_modules.add(mod)

            total_classes += len(impls)

            print("  {} implementors ({:d} classes)".format(iface, len(impls)))
            print("")
            for mod in sorted(by_module.keys()):
                classes = by_module[mod]
                cls_str = ", ".join(classes[:5])
                if len(classes) > 5:
                    cls_str += " ... +{:d}".format(len(classes) - 5)
                print("    {:30s}  {:>3d}  {}".format(mod, len(classes), cls_str))
            print("")

    # Summary
    print("  " + "-" * 60)
    print("  Summary:")
    print("    Alarm type categories: {:>5d}".format(len(categories)))
    print("    Total alarm classes:   {:>5,d}".format(total_classes))
    print("    Modules with alarms:   {:>5,d}".format(len(total_modules)))
    print("")


# ---------------------------------------------------------------------------
# cmd_alarm_trace — Role of a class in the alarm flow
# ---------------------------------------------------------------------------

def cmd_alarm_trace(base_dir, class_name):
    """Trace a specific class's role in the alarm flow."""
    ci = _load_class_index(base_dir)
    classes_map = ci.get("classes", {}) if ci else {}

    # Resolve class name
    target = None
    if class_name in classes_map:
        target = class_name
    else:
        matches = [k for k in classes_map if class_name.lower() in k.lower()]
        if len(matches) == 1:
            target = matches[0]
        elif len(matches) > 1:
            # Filter to alarm-related matches
            alarm_matches = [m for m in matches if "alarm" in m.lower() or "Alarm" in m]
            if len(alarm_matches) == 1:
                target = alarm_matches[0]
            else:
                print("")
                print("  Multiple matches for '{}':".format(class_name))
                show = alarm_matches if alarm_matches else matches
                for m in sorted(show)[:20]:
                    entries = classes_map.get(m, [])
                    mod = entries[0].get("module", "?") if entries else "?"
                    print("    {}  ({})".format(m, mod))
                if len(show) > 20:
                    print("    ... and {} more".format(len(show) - 20))
                print("")
                return
        else:
            print("  Class '{}' not found.".format(class_name))
            return

    entries = classes_map.get(target, [])
    class_info = entries[0] if entries else {}
    module = class_info.get("module", "unknown")

    print("")
    print("  ALARM TRACE: {}".format(target))
    print("  " + "=" * (14 + len(target)))
    print("")
    print("  Module:   {}".format(module))
    print("  Package:  {}".format(class_info.get("package", "?")))
    print("")

    # 1) Inheritance analysis — where does this class sit in alarm hierarchy?
    inh = _load_inheritance(base_dir)
    alarm_ancestors = []
    inh_roles = set()

    if inh:
        # Check chain to root using class_to_chain
        chain = inh.get("class_to_chain", {}).get(target, [])

        # If the target IS an alarm root, mark it
        if target in _ALARM_ROOTS:
            alarm_ancestors.append(target + " (IS ROOT)")
            inh_roles.add(_ALARM_ROOTS[target])

        # Check which alarm roots are in the chain
        for cls in chain:
            if cls in _ALARM_ROOTS:
                alarm_ancestors.append(cls)
                inh_roles.add(_ALARM_ROOTS[cls])

        # Check interfaces (reverse lookup)
        interfaces = inh.get("interface_to_implementors", {})
        for iface in _ALARM_INTERFACES:
            impls = interfaces.get(iface, [])
            if target in impls:
                alarm_ancestors.append(iface)
                inh_roles.add("source")

        if alarm_ancestors:
            print("  ALARM ANCESTRY:")
            for anc in alarm_ancestors:
                role = _ALARM_ROOTS.get(anc, "interface")
                print("    extends {:30s}  -> role: {}".format(anc, role))
            if chain:
                chain_str = " -> ".join([target] + chain[:8])
                if len(chain) > 8:
                    chain_str += " -> ..."
                print("    Full chain: {}".format(chain_str))
            print("")
        else:
            print("  ALARM ANCESTRY: none (not in alarm hierarchy)")
            print("")

    # 2) Alarm methods declared by this class
    mi = _load_method_index(base_dir)
    alarm_methods_declared = []

    if mi:
        methods_idx = mi.get("methods", {})
        for mname, phase in _ALARM_METHODS.items():
            for entry in methods_idx.get(mname, []):
                if entry.get("class") == target:
                    alarm_methods_declared.append({
                        "method": mname,
                        "phase": phase,
                        "line": entry.get("line", 0),
                        "visibility": entry.get("visibility", "?"),
                        "params": entry.get("params", ""),
                        "return_type": entry.get("return_type", "void"),
                    })

    if alarm_methods_declared:
        # Group by phase
        by_phase = defaultdict(list)
        for m in alarm_methods_declared:
            by_phase[m["phase"]].append(m)

        print("  ALARM METHODS DECLARED ({:d}):".format(
            len(alarm_methods_declared)))
        phase_order = ["creation", "routing", "handling",
                       "acknowledgment", "clearing", "data"]
        for phase in phase_order:
            items = by_phase.get(phase, [])
            if items:
                print("    [{:^14s}]".format(phase.upper()))
                for m in sorted(items, key=lambda x: x["line"]):
                    print("      {:30s}  {:10s}  line {:>5d}  {}({})".format(
                        m["method"], m["visibility"], m["line"],
                        m["return_type"], m["params"]))
        print("")
    else:
        print("  ALARM METHODS DECLARED: none")
        print("")

    # 3) Callgraph: alarm-related calls made and received
    cg = _load_callgraph(base_dir)
    calls_out = []
    calls_in = []

    if cg:
        calls = cg.get("calls", {})
        alarm_method_names = set(_ALARM_METHODS.keys())

        # Add broader patterns
        alarm_patterns = ["Alarm", "alarm", "Route", "Ack", "Fire"]

        # Outgoing: this class calling alarm methods
        for caller_key, callees in calls.items():
            if "." not in caller_key:
                continue
            caller_class = caller_key.rsplit(".", 1)[0]
            if caller_class != target:
                continue
            caller_method = caller_key.rsplit(".", 1)[1]

            for callee in callees:
                if "." not in callee:
                    continue
                callee_class = callee.rsplit(".", 1)[0]
                callee_method = callee.rsplit(".", 1)[1]

                if callee_method in alarm_method_names or any(
                    p in callee_method for p in alarm_patterns
                ):
                    calls_out.append({
                        "from_method": caller_method,
                        "to_class": callee_class,
                        "to_method": callee_method,
                        "phase": _ALARM_METHODS.get(callee_method, "related"),
                    })

        # Incoming: other classes calling this class's alarm methods
        for caller_key, callees in calls.items():
            if "." not in caller_key:
                continue
            caller_class = caller_key.rsplit(".", 1)[0]
            if caller_class == target:
                continue
            caller_method = caller_key.rsplit(".", 1)[1]

            for callee in callees:
                if "." not in callee:
                    continue
                callee_class = callee.rsplit(".", 1)[0]
                callee_method = callee.rsplit(".", 1)[1]

                if callee_class == target and (
                    callee_method in alarm_method_names or any(
                        p in callee_method for p in alarm_patterns
                    )
                ):
                    calls_in.append({
                        "caller_class": caller_class,
                        "caller_method": caller_method,
                        "target_method": callee_method,
                    })

    # Output callgraph
    if calls_out:
        by_target = defaultdict(list)
        for c in calls_out:
            by_target[c["to_class"]].append(c)

        print("  OUTGOING ALARM CALLS ({:d} calls to {:d} classes):".format(
            len(calls_out), len(by_target)))
        for tcls in sorted(by_target.keys()):
            items = by_target[tcls]
            tmod = _get_class_module(base_dir, tcls)
            methods_called = sorted(set(c["to_method"] for c in items))
            from_methods = sorted(set(c["from_method"] for c in items))
            print("    -> {:30s}  ({})".format(tcls, tmod))
            print("       calls: {}".format(", ".join(methods_called[:5])))
            if len(methods_called) > 5:
                print("       ... +{:d} more methods".format(len(methods_called) - 5))
            print("       from:  {}".format(", ".join(from_methods[:5])))
        print("")
    else:
        print("  OUTGOING ALARM CALLS: none")
        print("")

    if calls_in:
        by_caller = defaultdict(list)
        for c in calls_in:
            by_caller[c["caller_class"]].append(c)

        print("  INCOMING ALARM CALLERS ({:d} calls from {:d} classes):".format(
            len(calls_in), len(by_caller)))
        for ccls in sorted(by_caller.keys()):
            items = by_caller[ccls]
            cmod = _get_class_module(base_dir, ccls)
            target_methods = sorted(set(c["target_method"] for c in items))
            from_methods = sorted(set(c["caller_method"] for c in items))
            print("    <- {:30s}  ({})".format(ccls, cmod))
            print("       targets: {}".format(", ".join(target_methods[:5])))
            print("       via:     {}".format(", ".join(from_methods[:5])))
        print("")
    else:
        print("  INCOMING ALARM CALLERS: none")
        print("")

    # 4) Descendants (if this is an alarm root or has alarm subtypes)
    if inh:
        descendants = _get_all_descendants(inh, target)
        alarm_descendants = []
        for d in sorted(descendants):
            d_mod = _get_class_module(base_dir, d)
            # Check if descendant is alarm-related
            if "alarm" in d.lower() or "Alarm" in d or d in _ALARM_ROOTS:
                alarm_descendants.append((d, d_mod))

        if descendants:
            print("  DESCENDANTS ({:d} total, {:d} alarm-related):".format(
                len(descendants), len(alarm_descendants)))
            show_list = alarm_descendants if alarm_descendants else [
                (d, _get_class_module(base_dir, d)) for d in sorted(descendants)[:20]
            ]
            for d, d_mod in show_list[:20]:
                print("    {:35s}  ({})".format(d, d_mod))
            if len(show_list) > 20:
                print("    ... and {:d} more".format(len(show_list) - 20))
            print("")

    # 5) Related classes in same module
    all_alarm_inh = _find_alarm_classes_by_inheritance(base_dir)
    related = set()
    for cls, info in all_alarm_inh.items():
        if info.get("module") == module and cls != target:
            related.add(cls)

    if related:
        print("  OTHER ALARM CLASSES IN {} ({:d}):".format(
            module, len(related)))
        for r in sorted(related)[:20]:
            r_info = all_alarm_inh.get(r, {})
            r_roles = r_info.get("roles", set())
            roles_str = ", ".join(sorted(r_roles))
            print("    {:35s}  [{}]".format(r, roles_str))
        if len(related) > 20:
            print("    ... and {:,d} more".format(len(related) - 20))
        print("")

    # 6) Classify final role
    method_phases = alarm_methods_declared if alarm_methods_declared else []
    roles = _classify_alarm_role(target, inh_roles, method_phases)

    print("  ALARM ROLE: {}".format(", ".join(sorted(roles))))
    print("")

    # Summary
    print("  Summary:")
    print("    Alarm ancestry:      {:>5d}  ({})".format(
        len(alarm_ancestors),
        ", ".join(alarm_ancestors) if alarm_ancestors else "none"))
    print("    Methods declared:    {:>5d}".format(len(alarm_methods_declared)))
    print("    Outgoing calls:      {:>5d}".format(len(calls_out)))
    print("    Incoming callers:    {:>5d}".format(len(calls_in)))
    print("    Alarm role:          {}".format(", ".join(sorted(roles))))
    print("")
