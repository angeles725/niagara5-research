"""
Subscription & Topic Graph commands for Module Navigator (Phase 35).

Maps the Niagara pub-sub system: @NiagaraTopic declarations, publishers
(fire/changed), and subscribers (subscribe/getTopic/handleTopic).

Uses annotations-index.json + callgraph-index.json + method-index.json
on-demand. No builder.

Commands:
  topics [--module mod] [-n N]      List all @NiagaraTopic declarations
  subscribers <topic|class>         Who subscribes/fires a topic or class topics
  pub-sub <module>                  Publish->subscribe graph for a module
"""

import json
import os
from collections import defaultdict


# ---------------------------------------------------------------------------
# Index loaders (lazy, cached)
# ---------------------------------------------------------------------------

_annotations_cache = None
_callgraph_cache = None
_method_index_cache = None
_class_index_cache = None


def _load_annotations(base_dir):
    """Load annotations-index.json (cached)."""
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


def _load_callgraph(base_dir):
    """Load callgraph-index.json (cached)."""
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
    """Load method-index.json (cached)."""
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


def _load_class_index(base_dir):
    """Load class-index.json (cached)."""
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
    """Resolve module for a class from class-index."""
    ci = _load_class_index(base_dir)
    if not ci:
        return "unknown"
    entries = ci.get("classes", {}).get(class_name, [])
    if entries:
        return entries[0].get("module", "unknown")
    return "unknown"


# ---------------------------------------------------------------------------
# Topic extraction helpers
# ---------------------------------------------------------------------------

def _extract_all_topics(base_dir, module_filter=None):
    """Extract all @NiagaraTopic declarations from annotations-index.

    Returns list of dicts: {class, module, name, eventType, flags}
    """
    ai = _load_annotations(base_dir)
    if not ai:
        return []

    nt = ai.get("niagara_types", {})
    results = []

    for cls, info in nt.items():
        if not isinstance(info, dict):
            continue

        topics = info.get("topics", [])
        if not topics:
            continue

        module = info.get("module", "unknown")
        if module_filter and module != module_filter:
            continue

        for t in topics:
            results.append({
                "class": cls,
                "module": module,
                "name": t.get("name", "?"),
                "eventType": t.get("eventType", None),
                "flags": t.get("flags", None),
            })

    return results


# ---------------------------------------------------------------------------
# Fire/subscribe detection from callgraph + method-index
# ---------------------------------------------------------------------------

# Methods that indicate topic publishing (firing)
_FIRE_METHODS = frozenset([
    "fire", "changed", "fireTopics", "fireNewTopic",
    "fireConfigurationSavedTopic", "doFireConfigurationSavedTopic",
    "fireAlarm", "fireReportTopic",
])

# Method name fragments that indicate firing
_FIRE_FRAGMENTS = frozenset([
    "fire", "changed",
])

# Methods that indicate topic subscription/handling
_SUBSCRIBE_METHODS = frozenset([
    "subscribe", "subscribeTopic", "subscribeTopics",
    "getTopic", "getTopics", "asTopic",
])

# Method name fragments that indicate subscription
_SUBSCRIBE_FRAGMENTS = frozenset([
    "subscribe", "topic",
])


def _find_publishers(base_dir, module_filter=None):
    """Find classes that publish/fire topics via callgraph.

    Returns dict: caller_class -> [{callee, method, module}]
    """
    cg = _load_callgraph(base_dir)
    if not cg:
        return {}

    calls = cg.get("calls", {})
    publishers = defaultdict(list)

    for caller_key, callees in calls.items():
        # caller_key is "ClassName.methodName"
        if "." not in caller_key:
            continue

        caller_class = caller_key.rsplit(".", 1)[0]

        if module_filter:
            mod = _get_class_module(base_dir, caller_class)
            if mod != module_filter:
                continue

        for callee in callees:
            if "." not in callee:
                continue

            callee_method = callee.rsplit(".", 1)[1]

            # Check if it's a fire-related call
            is_fire = False
            if callee_method in _FIRE_METHODS:
                is_fire = True
            elif any(frag in callee_method.lower() for frag in _FIRE_FRAGMENTS):
                # Avoid false positives: must also contain "topic" or be "changed"
                if callee_method == "changed" or "topic" in callee_method.lower() or "fire" in callee_method.lower():
                    is_fire = True

            if is_fire:
                publishers[caller_class].append({
                    "callee": callee,
                    "method": caller_key.rsplit(".", 1)[1],
                })

    return dict(publishers)


def _find_subscribers(base_dir, module_filter=None):
    """Find classes that subscribe to topics via method-index + callgraph.

    Returns dict: class_name -> [{method_name, kind}]
    where kind is 'declares' (has subscribe-like method) or 'calls' (calls subscribe).
    """
    subscribers = defaultdict(list)

    # 1) Check method-index for classes that DECLARE topic-related methods
    mi = _load_method_index(base_dir)
    if mi:
        methods_idx = mi.get("methods", {})
        for mname in sorted(methods_idx.keys()):
            mname_lower = mname.lower()
            is_sub = False

            if mname in _SUBSCRIBE_METHODS:
                is_sub = True
            elif "topic" in mname_lower and ("get" in mname_lower or "handle" in mname_lower or "subscribe" in mname_lower):
                is_sub = True

            if is_sub:
                for entry in methods_idx[mname]:
                    cls = entry.get("class", "")
                    mod = entry.get("module", "")
                    if module_filter and mod != module_filter:
                        continue
                    subscribers[cls].append({
                        "method_name": mname,
                        "kind": "declares",
                        "module": mod,
                    })

    # 2) Check callgraph for classes that CALL subscribe-like methods
    cg = _load_callgraph(base_dir)
    if cg:
        calls = cg.get("calls", {})
        for caller_key, callees in calls.items():
            if "." not in caller_key:
                continue

            caller_class = caller_key.rsplit(".", 1)[0]

            if module_filter:
                mod = _get_class_module(base_dir, caller_class)
                if mod != module_filter:
                    continue

            for callee in callees:
                if "." not in callee:
                    continue

                callee_method = callee.rsplit(".", 1)[1]

                is_sub = False
                if callee_method in _SUBSCRIBE_METHODS:
                    is_sub = True
                elif "subscribe" in callee_method.lower() and "unsubscribe" not in callee_method.lower():
                    is_sub = True

                if is_sub:
                    subscribers[caller_class].append({
                        "method_name": callee_method,
                        "kind": "calls",
                        "callee": callee,
                    })

    return dict(subscribers)


# ---------------------------------------------------------------------------
# cmd_topics — List all @NiagaraTopic declarations
# ---------------------------------------------------------------------------

def cmd_topics(base_dir, module_filter=None, limit=50):
    """List all @NiagaraTopic declarations from annotations-index."""
    topics = _extract_all_topics(base_dir, module_filter=module_filter)
    if not topics:
        msg = "  No @NiagaraTopic declarations found"
        if module_filter:
            msg += " in module '{}'".format(module_filter)
        print(msg + ".")
        return

    # Group by module
    by_module = defaultdict(list)
    by_name = defaultdict(list)
    by_class = defaultdict(list)
    for t in topics:
        by_module[t["module"]].append(t)
        by_name[t["name"]].append(t)
        by_class[t["class"]].append(t)

    scope = " in {}".format(module_filter) if module_filter else ""
    print("")
    print("  SUBSCRIPTION & TOPIC GRAPH{} ({:,} topics, {:,} classes, {:,} modules)".format(
        scope, len(topics), len(by_class), len(by_module)))
    print("")

    # Summary: topic names sorted by frequency
    print("  Top topic names (by frequency):")
    top_names = sorted(by_name.items(), key=lambda x: -len(x[1]))[:15]
    for name, entries in top_names:
        classes = sorted(set(e["class"] for e in entries))
        classes_str = ", ".join(classes[:3])
        if len(classes) > 3:
            classes_str += " +{}".format(len(classes) - 3)
        evt = entries[0].get("eventType", "")
        evt_str = "  [{}]".format(evt) if evt else ""
        print("    {:30s}  {:>3d} classes  ({}){}".format(
            name, len(entries), classes_str, evt_str))
    print("")

    # By module breakdown
    print("  By module:")
    top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:15]
    for mod, entries in top_mods:
        classes = len(set(e["class"] for e in entries))
        names = sorted(set(e["name"] for e in entries))[:5]
        names_str = ", ".join(names)
        if len(set(e["name"] for e in entries)) > 5:
            names_str += " ..."
        print("    {:30s}  {:>3d} topics  {:>3d} classes  [{}]".format(
            mod, len(entries), classes, names_str))
    if len(by_module) > 15:
        print("    ... and {:,} more modules".format(len(by_module) - 15))
    print("")

    # Detailed table
    print("  {:35s}  {:25s}  {:25s}  {:>5s}  {}".format(
        "CLASS", "MODULE", "TOPIC NAME", "FLAGS", "EVENT TYPE"))
    print("  " + "-" * 125)

    shown = 0
    for t in sorted(topics, key=lambda x: (x["module"], x["class"], x["name"])):
        if shown >= limit:
            remaining = len(topics) - shown
            print("  ... and {:,} more (use -n {:,} to see all)".format(
                remaining, len(topics)))
            break

        cls_d = t["class"] if len(t["class"]) <= 35 else t["class"][:32] + "..."
        mod_d = t["module"] if len(t["module"]) <= 25 else t["module"][:22] + "..."
        name_d = t["name"] if len(t["name"]) <= 25 else t["name"][:22] + "..."
        flags_d = str(t["flags"]) if t["flags"] is not None else "-"
        evt_d = t["eventType"] if t["eventType"] else "-"

        print("  {:35s}  {:25s}  {:25s}  {:>5s}  {}".format(
            cls_d, mod_d, name_d, flags_d, evt_d))
        shown += 1

    print("")

    # Event type distribution
    event_types = defaultdict(int)
    for t in topics:
        et = t["eventType"] if t["eventType"] else "(none)"
        event_types[et] += 1

    if event_types:
        print("  Event type distribution:")
        for et, count in sorted(event_types.items(), key=lambda x: -x[1]):
            print("    {:25s}  {:>4d} topics".format(et, count))
        print("")


# ---------------------------------------------------------------------------
# cmd_subscribers — Who subscribes/fires a topic or class topics
# ---------------------------------------------------------------------------

def cmd_subscribers(base_dir, query):
    """Show who subscribes to or fires a specific topic name or class's topics.

    The query can be:
    - A topic name (e.g. "alarm", "actionPerformed")
    - A class name (e.g. "BAlarmService")
    """
    # First, check if it matches a topic name
    all_topics = _extract_all_topics(base_dir)
    topic_matches = [t for t in all_topics if t["name"].lower() == query.lower()]

    # Also check if it matches a class name
    class_topics = [t for t in all_topics if t["class"].lower() == query.lower()
                    or t["class"] == query]

    if not topic_matches and not class_topics:
        # Fuzzy match on topic names
        partial = [t for t in all_topics if query.lower() in t["name"].lower()]
        if partial:
            unique_names = sorted(set(t["name"] for t in partial))
            print("")
            print("  No exact match for '{}'. Partial matches:".format(query))
            for n in unique_names[:20]:
                count = sum(1 for t in partial if t["name"] == n)
                print("    {:30s}  {:>3d} classes".format(n, count))
            print("")
            return

        # Check if it's a known class
        ci = _load_class_index(base_dir)
        if ci:
            classes_map = ci.get("classes", {})
            cls_matches = [k for k in classes_map if query.lower() in k.lower()]
            if cls_matches:
                print("")
                print("  '{}' has no @NiagaraTopic declarations.".format(query))
                print("  Did you mean one of these classes?")
                for m in sorted(cls_matches)[:10]:
                    print("    {}".format(m))
                print("")
                return

        print("  No topics or classes matching '{}'.".format(query))
        return

    # Determine the scope
    target_classes = set()
    target_topic_names = set()

    if topic_matches:
        # Query is a topic name
        target_topic_names.add(query.lower())
        for t in topic_matches:
            target_classes.add(t["class"])
        mode = "topic"
        display_name = query
    else:
        # Query is a class name
        for t in class_topics:
            target_classes.add(t["class"])
            target_topic_names.add(t["name"].lower())
        mode = "class"
        display_name = class_topics[0]["class"]

    print("")
    if mode == "topic":
        print("  SUBSCRIBERS FOR TOPIC: '{}'".format(display_name))
        print("  " + "=" * (25 + len(display_name)))
        print("")
        print("  Declared in {:,} classes:".format(len(topic_matches)))
        for t in sorted(topic_matches, key=lambda x: x["class"]):
            evt = " [{}]".format(t["eventType"]) if t["eventType"] else ""
            print("    {:35s}  {:25s}{}".format(t["class"], t["module"], evt))
    else:
        print("  SUBSCRIBERS FOR CLASS: {}".format(display_name))
        print("  " + "=" * (24 + len(display_name)))
        print("")
        print("  Topics declared ({:d}):".format(len(class_topics)))
        for t in sorted(class_topics, key=lambda x: x["name"]):
            evt = " [{}]".format(t["eventType"]) if t["eventType"] else ""
            print("    {:30s}{}".format(t["name"], evt))
    print("")

    # Find publishers (classes that call fire/changed on target classes)
    cg = _load_callgraph(base_dir)
    publishers = []
    if cg:
        calls = cg.get("calls", {})
        for caller_key, callees in calls.items():
            if "." not in caller_key:
                continue
            caller_class = caller_key.rsplit(".", 1)[0]
            caller_method = caller_key.rsplit(".", 1)[1]

            for callee in callees:
                if "." not in callee:
                    continue
                callee_class = callee.rsplit(".", 1)[0]
                callee_method = callee.rsplit(".", 1)[1]

                # Check if callee is a fire/changed call on one of our target classes
                if callee_class in target_classes:
                    if callee_method in _FIRE_METHODS or "fire" in callee_method.lower():
                        publishers.append({
                            "caller_class": caller_class,
                            "caller_method": caller_method,
                            "target": callee,
                        })

    # Find subscribers (classes that call subscribe on target classes or
    # reference topics by name)
    subscribers_list = []
    if cg:
        calls = cg.get("calls", {})
        for caller_key, callees in calls.items():
            if "." not in caller_key:
                continue
            caller_class = caller_key.rsplit(".", 1)[0]
            caller_method = caller_key.rsplit(".", 1)[1]

            for callee in callees:
                if "." not in callee:
                    continue
                callee_class = callee.rsplit(".", 1)[0]
                callee_method = callee.rsplit(".", 1)[1]

                # Check if callee is a subscribe call on one of our target classes
                if callee_class in target_classes:
                    if "subscribe" in callee_method.lower() and "unsubscribe" not in callee_method.lower():
                        subscribers_list.append({
                            "caller_class": caller_class,
                            "caller_method": caller_method,
                            "target": callee,
                            "kind": "subscribes",
                        })
                    elif callee_method in ("getTopic", "getTopics", "asTopic"):
                        subscribers_list.append({
                            "caller_class": caller_class,
                            "caller_method": caller_method,
                            "target": callee,
                            "kind": "reads-topic",
                        })

    # Also find classes that override changed() and reference target classes
    mi = _load_method_index(base_dir)
    changed_overrides = []
    if mi:
        methods_idx = mi.get("methods", {})
        changed_entries = methods_idx.get("changed", [])
        for entry in changed_entries:
            cls = entry.get("class", "")
            if cls in target_classes:
                changed_overrides.append({
                    "class": cls,
                    "module": entry.get("module", ""),
                    "line": entry.get("line", 0),
                })

    # Print publishers
    if publishers:
        unique_pub = {}
        for p in publishers:
            key = p["caller_class"]
            if key not in unique_pub:
                unique_pub[key] = []
            unique_pub[key].append(p)

        print("  PUBLISHERS ({:,} classes fire/change topics):".format(len(unique_pub)))
        for cls in sorted(unique_pub.keys()):
            entries = unique_pub[cls]
            mod = _get_class_module(base_dir, cls)
            methods = sorted(set(e["caller_method"] for e in entries))
            targets = sorted(set(e["target"] for e in entries))
            print("    {:35s}  {:20s}  via {}".format(
                cls if len(cls) <= 35 else cls[:32] + "...",
                mod,
                ", ".join(methods[:3]) + (" ..." if len(methods) > 3 else "")))
            for t in targets[:2]:
                print("      -> {}".format(t))
        print("")
    else:
        print("  PUBLISHERS: none found (no fire/changed calls on target classes)")
        print("")

    # Print subscribers
    if subscribers_list:
        unique_sub = {}
        for s in subscribers_list:
            key = s["caller_class"]
            if key not in unique_sub:
                unique_sub[key] = []
            unique_sub[key].append(s)

        print("  SUBSCRIBERS ({:,} classes subscribe/read topics):".format(len(unique_sub)))
        for cls in sorted(unique_sub.keys()):
            entries = unique_sub[cls]
            mod = _get_class_module(base_dir, cls)
            kinds = sorted(set(e["kind"] for e in entries))
            targets = sorted(set(e["target"] for e in entries))
            print("    {:35s}  {:20s}  [{}]".format(
                cls if len(cls) <= 35 else cls[:32] + "...",
                mod,
                ", ".join(kinds)))
            for t in targets[:2]:
                print("      -> {}".format(t))
        print("")
    else:
        print("  SUBSCRIBERS: none found (no subscribe calls on target classes)")
        print("")

    # Print changed() overrides in target classes
    if changed_overrides:
        print("  changed() OVERRIDES in target classes ({:d}):".format(len(changed_overrides)))
        for co in sorted(changed_overrides, key=lambda x: x["class"]):
            print("    {:35s}  {:20s}  line {:>5d}".format(
                co["class"], co["module"], co["line"]))
        print("")

    # Summary
    print("  Summary:")
    print("    Topic declarations:   {:>5d}".format(
        len(topic_matches) if mode == "topic" else len(class_topics)))
    print("    Publisher classes:     {:>5d}".format(
        len(set(p["caller_class"] for p in publishers)) if publishers else 0))
    print("    Subscriber classes:   {:>5d}".format(
        len(set(s["caller_class"] for s in subscribers_list)) if subscribers_list else 0))
    print("    changed() overrides:  {:>5d}".format(len(changed_overrides)))
    print("")


# ---------------------------------------------------------------------------
# cmd_pub_sub — Publish->subscribe graph for a module
# ---------------------------------------------------------------------------

def cmd_pub_sub(base_dir, module_name):
    """Show the publish-subscribe graph for a module.

    Combines topics declared in the module, who fires them, and who listens.
    """
    # Get topics declared in this module
    topics = _extract_all_topics(base_dir, module_filter=module_name)

    # Get publishers and subscribers in this module
    publishers = _find_publishers(base_dir, module_filter=module_name)
    subscribers = _find_subscribers(base_dir, module_filter=module_name)

    if not topics and not publishers and not subscribers:
        print("  No pub-sub activity found in module '{}'.".format(module_name))
        # Check if module exists
        ci = _load_class_index(base_dir)
        if ci:
            classes_map = ci.get("classes", {})
            mod_classes = [k for k, v in classes_map.items()
                          if v and v[0].get("module") == module_name]
            if not mod_classes:
                print("  Module '{}' not found in class-index.".format(module_name))
            else:
                print("  Module exists ({:,} classes) but no topic activity.".format(
                    len(mod_classes)))
        print("")
        return

    # Collect all topic-declaring classes in this module
    topic_classes = defaultdict(list)
    for t in topics:
        topic_classes[t["class"]].append(t["name"])

    # Build the graph
    print("")
    print("  PUB-SUB GRAPH: {}".format(module_name))
    print("  " + "=" * (16 + len(module_name)))
    print("")

    # Section 1: Topics declared in this module
    if topics:
        print("  TOPICS DECLARED ({:d} topics in {:d} classes):".format(
            len(topics), len(topic_classes)))
        for cls in sorted(topic_classes.keys()):
            names = topic_classes[cls]
            topic_detail = []
            for t in topics:
                if t["class"] == cls:
                    evt = " [{}]".format(t["eventType"]) if t["eventType"] else ""
                    topic_detail.append("{}{}".format(t["name"], evt))
            print("    {:35s}  {}".format(cls, ", ".join(topic_detail)))
        print("")
    else:
        print("  TOPICS DECLARED: none")
        print("")

    # Section 2: Publishers in this module (classes that fire/change)
    if publishers:
        total_calls = sum(len(v) for v in publishers.values())
        print("  PUBLISHERS ({:d} classes, {:d} fire/changed calls):".format(
            len(publishers), total_calls))

        for cls in sorted(publishers.keys()):
            calls = publishers[cls]
            # Group by callee target
            targets = defaultdict(list)
            for c in calls:
                targets[c["callee"]].append(c["method"])

            print("    {}:".format(cls))
            for target, methods in sorted(targets.items()):
                unique_methods = sorted(set(methods))[:4]
                print("      -> {:40s}  via {}".format(
                    target,
                    ", ".join(unique_methods) + (" ..." if len(set(methods)) > 4 else "")))
        print("")
    else:
        print("  PUBLISHERS: none (no fire/changed calls in this module)")
        print("")

    # Section 3: Subscribers in this module
    if subscribers:
        total_subs = sum(len(v) for v in subscribers.values())
        print("  SUBSCRIBERS ({:d} classes, {:d} subscribe/topic methods):".format(
            len(subscribers), total_subs))

        for cls in sorted(subscribers.keys()):
            subs = subscribers[cls]
            by_kind = defaultdict(list)
            for s in subs:
                by_kind[s["kind"]].append(s["method_name"])

            parts = []
            for kind in sorted(by_kind.keys()):
                methods = sorted(set(by_kind[kind]))[:4]
                methods_str = ", ".join(methods)
                if len(set(by_kind[kind])) > 4:
                    methods_str += " ..."
                parts.append("[{}] {}".format(kind, methods_str))

            print("    {:35s}  {}".format(
                cls if len(cls) <= 35 else cls[:32] + "...",
                "  ".join(parts)))
        print("")
    else:
        print("  SUBSCRIBERS: none (no subscribe/topic methods in this module)")
        print("")

    # Section 4: Cross-module connections
    # Find OTHER modules that interact with this module's topics
    if topics:
        other_publishers = _find_publishers(base_dir)
        other_subscribers = _find_subscribers(base_dir)

        # Classes declared in this module
        ci = _load_class_index(base_dir)
        classes_map = ci.get("classes", {}) if ci else {}
        mod_classes = set(k for k, v in classes_map.items()
                         if v and v[0].get("module") == module_name)

        # External classes that fire/call methods on this module's classes
        ext_publishers = defaultdict(list)
        for cls, calls in other_publishers.items():
            if cls in mod_classes:
                continue  # Skip internal
            for c in calls:
                target_cls = c["callee"].rsplit(".", 1)[0] if "." in c["callee"] else ""
                if target_cls in mod_classes:
                    ext_mod = _get_class_module(base_dir, cls)
                    ext_publishers[ext_mod].append({
                        "class": cls,
                        "target": c["callee"],
                    })

        if ext_publishers:
            print("  EXTERNAL PUBLISHERS (other modules -> this module's classes):")
            for ext_mod in sorted(ext_publishers.keys()):
                entries = ext_publishers[ext_mod]
                unique_cls = sorted(set(e["class"] for e in entries))
                print("    {:25s}  {:>3d} classes  ({})".format(
                    ext_mod, len(unique_cls),
                    ", ".join(unique_cls[:3]) + (" ..." if len(unique_cls) > 3 else "")))
            print("")

    # Summary
    print("  Summary:")
    print("    Topics declared:       {:>5d}".format(len(topics)))
    print("    Publisher classes:      {:>5d}".format(len(publishers)))
    print("    Subscriber classes:     {:>5d}".format(len(subscribers)))
    total_fire = sum(len(v) for v in publishers.values())
    total_sub = sum(len(v) for v in subscribers.values())
    print("    Fire/changed calls:    {:>5d}".format(total_fire))
    print("    Subscribe/topic refs:  {:>5d}".format(total_sub))
    print("")
