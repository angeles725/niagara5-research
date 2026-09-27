"""
Complexity Metrics commands for Module Navigator (Phase 40).

LOC + method count + field count + fan-in/fan-out + inheritance depth per class.
Weighted composite score for ranking. Module-level summaries.

Uses class-index.json + method-index.json + field-index.json +
callgraph-index.json + inheritance.json on-demand. No builder.

Commands:
  complexity <class>                 LOC, methods, fields, depth, fan-in/out
  complexity-scan [--module] [-n N]  Ranking of most complex classes
  metrics <module>                   Module-level complexity summary
"""

import json
import os
from collections import defaultdict


# ---------------------------------------------------------------------------
# Index loaders (lazy, cached)
# ---------------------------------------------------------------------------

_class_index_cache = None
_method_index_cache = None
_field_index_cache = None
_callgraph_cache = None
_inheritance_cache = None


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


# ---------------------------------------------------------------------------
# Fan-in / Fan-out computation (cached)
# ---------------------------------------------------------------------------

_fan_cache = None  # (fan_in_dict, fan_out_dict)


def _compute_fan(calls):
    """Build fan-in and fan-out maps from callgraph calls dict.

    fan_out[class] = number of unique external classes this class calls
    fan_in[class]  = number of unique external classes that call this class
    """
    global _fan_cache
    if _fan_cache is not None:
        return _fan_cache

    fan_out = defaultdict(set)
    fan_in = defaultdict(set)

    for caller_key, callees in calls.items():
        dot = caller_key.find(".")
        if dot < 0:
            continue
        caller_class = caller_key[:dot]

        if isinstance(callees, list):
            for callee in callees:
                if isinstance(callee, str):
                    cdot = callee.find(".")
                    callee_class = callee[:cdot] if cdot >= 0 else callee
                    if callee_class != caller_class:
                        fan_out[caller_class].add(callee_class)
                        fan_in[callee_class].add(caller_class)
        elif isinstance(callees, str):
            cdot = callees.find(".")
            callee_class = callees[:cdot] if cdot >= 0 else callees
            if callee_class != caller_class:
                fan_out[caller_class].add(callee_class)
                fan_in[callee_class].add(caller_class)

    # Convert sets to counts
    fan_out_counts = {k: len(v) for k, v in fan_out.items()}
    fan_in_counts = {k: len(v) for k, v in fan_in.items()}

    _fan_cache = (fan_in_counts, fan_out_counts)
    return _fan_cache


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def _compute_score(loc, methods, fields, fan_in, fan_out):
    """Weighted composite: LOC*0.2 + methods*0.3 + fields*0.2 + fan_in*0.15 + fan_out*0.15"""
    return (loc * 0.2
            + methods * 0.3
            + fields * 0.2
            + fan_in * 0.15
            + fan_out * 0.15)


def _score_label(score):
    """Human-readable complexity label."""
    if score < 10:
        return "TRIVIAL"
    elif score < 30:
        return "LOW"
    elif score < 60:
        return "MODERATE"
    elif score < 100:
        return "HIGH"
    elif score < 200:
        return "VERY HIGH"
    else:
        return "EXTREME"


# ---------------------------------------------------------------------------
# cmd_complexity — single class detail
# ---------------------------------------------------------------------------

def cmd_complexity(base_dir, class_name):
    """Show complexity metrics for a single class."""
    ci = _load_class_index(base_dir)
    mi = _load_method_index(base_dir)
    fi = _load_field_index(base_dir)
    cg = _load_callgraph(base_dir)
    ih = _load_inheritance(base_dir)

    if not ci or not mi or not fi:
        return

    classes = ci.get("classes", {})
    info_list = classes.get(class_name)
    if not info_list:
        # Try case-insensitive
        for name, entries in classes.items():
            if name.lower() == class_name.lower():
                class_name = name
                info_list = entries
                break

    if not info_list:
        print("  Class '{}' not found in class-index.".format(class_name))
        return

    info = info_list[0]
    module = info.get("module", "unknown")
    loc = info.get("lines", 0)
    kind = info.get("kind", "class")
    package = info.get("package", "")

    class_methods = mi.get("class_methods", {})
    method_list = class_methods.get(class_name, [])
    method_count = len(method_list)

    class_fields = fi.get("class_fields", {})
    field_list = class_fields.get(class_name, [])
    field_count = len(field_list)

    # Inheritance depth
    depth = 0
    if ih:
        chains = ih.get("class_to_chain", {})
        chain = chains.get(class_name, [])
        depth = len(chain)

    # Fan-in / fan-out
    fan_in_val = 0
    fan_out_val = 0
    if cg:
        calls = cg.get("calls", {})
        fan_in_map, fan_out_map = _compute_fan(calls)
        fan_in_val = fan_in_map.get(class_name, 0)
        fan_out_val = fan_out_map.get(class_name, 0)

    score = _compute_score(loc, method_count, field_count, fan_in_val, fan_out_val)
    label = _score_label(score)

    print("")
    print("  COMPLEXITY: {}".format(class_name))
    print("  " + "=" * 55)
    print("")
    print("  Module:            {}".format(module))
    print("  Package:           {}".format(package))
    print("  Kind:              {}".format(kind))
    print("")
    print("  {:20s} {:>8}   {:<10s}".format("METRIC", "VALUE", "WEIGHT"))
    print("  " + "-" * 42)
    print("  {:20s} {:>8,d}   x 0.20  = {:>8.1f}".format(
        "Lines of code", loc, loc * 0.2))
    print("  {:20s} {:>8,d}   x 0.30  = {:>8.1f}".format(
        "Methods", method_count, method_count * 0.3))
    print("  {:20s} {:>8,d}   x 0.20  = {:>8.1f}".format(
        "Fields", field_count, field_count * 0.2))
    print("  {:20s} {:>8,d}   x 0.15  = {:>8.1f}".format(
        "Fan-in (callers)", fan_in_val, fan_in_val * 0.15))
    print("  {:20s} {:>8,d}   x 0.15  = {:>8.1f}".format(
        "Fan-out (callees)", fan_out_val, fan_out_val * 0.15))
    print("  " + "-" * 42)
    print("  {:20s} {:>8.1f}   {}".format("SCORE", score, label))
    print("")

    if depth > 0:
        chain = ih.get("class_to_chain", {}).get(class_name, []) if ih else []
        chain_str = " -> ".join(chain[:8])
        if len(chain) > 8:
            chain_str += " -> ..."
        print("  Inheritance depth: {} ({})".format(depth, chain_str))
        print("")

    # Show methods if not too many
    if method_list and method_count <= 30:
        print("  Methods ({:,d}):".format(method_count))
        for m in sorted(method_list):
            print("    {}".format(m))
        print("")
    elif method_count > 30:
        print("  Methods: {:,d} (use 'methods {}' for full list)".format(
            method_count, class_name))
        print("")

    # Show fields if not too many
    if field_list and field_count <= 20:
        print("  Fields ({:,d}):".format(field_count))
        for fld in field_list:
            if isinstance(fld, dict):
                fname = fld.get("name", str(fld))
                ftype = fld.get("type", "")
                print("    {} {}".format(ftype, fname))
            else:
                print("    {}".format(fld))
        print("")
    elif field_count > 20:
        print("  Fields: {:,d} (use 'fields {}' for full list)".format(
            field_count, class_name))
        print("")


# ---------------------------------------------------------------------------
# cmd_complexity_scan — ranking of most complex classes
# ---------------------------------------------------------------------------

def cmd_complexity_scan(base_dir, module_filter=None, limit=50):
    """Rank classes by complexity score, optionally filtered by module."""
    ci = _load_class_index(base_dir)
    mi = _load_method_index(base_dir)
    fi = _load_field_index(base_dir)
    cg = _load_callgraph(base_dir)
    ih = _load_inheritance(base_dir)

    if not ci or not mi or not fi:
        return

    classes = ci.get("classes", {})
    class_methods = mi.get("class_methods", {})
    class_fields = fi.get("class_fields", {})

    # Build fan-in/out
    fan_in_map = {}
    fan_out_map = {}
    if cg:
        calls = cg.get("calls", {})
        fan_in_map, fan_out_map = _compute_fan(calls)

    chains = {}
    if ih:
        chains = ih.get("class_to_chain", {})

    print("")
    if module_filter:
        print("  COMPLEXITY SCAN — module: {}".format(module_filter))
    else:
        print("  COMPLEXITY SCAN — all modules")
    print("  " + "=" * 55)
    print("")
    print("  Score = LOC*0.2 + methods*0.3 + fields*0.2 + fan_in*0.15 + fan_out*0.15")
    print("")

    entries = []
    for class_name, info_list in classes.items():
        if not info_list:
            continue
        info = info_list[0]
        module = info.get("module", "unknown")

        if module_filter and module != module_filter:
            continue

        loc = info.get("lines", 0)
        mc = len(class_methods.get(class_name, []))
        fc = len(class_fields.get(class_name, []))
        fi_val = fan_in_map.get(class_name, 0)
        fo_val = fan_out_map.get(class_name, 0)
        depth = len(chains.get(class_name, []))

        score = _compute_score(loc, mc, fc, fi_val, fo_val)
        entries.append({
            "class": class_name,
            "module": module,
            "loc": loc,
            "methods": mc,
            "fields": fc,
            "fan_in": fi_val,
            "fan_out": fo_val,
            "depth": depth,
            "score": score,
        })

    entries.sort(key=lambda e: -e["score"])

    if not entries:
        print("  No classes found{}.".format(
            " in module '{}'".format(module_filter) if module_filter else ""))
        print("")
        return

    # Table header
    print("  {:35s}  {:25s}  {:>5s}  {:>5s}  {:>5s}  {:>5s}  {:>5s}  {:>3s}  {:>7s}  {:s}".format(
        "CLASS", "MODULE", "LOC", "MTHDS", "FLDS", "FAN_I", "FAN_O", "DEP", "SCORE", "LEVEL"))
    print("  " + "-" * 115)

    shown = 0
    for e in entries:
        if shown >= limit:
            remaining = len(entries) - shown
            print("  ... and {:,d} more (use -n {:,d} to see all)".format(
                remaining, len(entries)))
            break

        cls_d = e["class"] if len(e["class"]) <= 35 else e["class"][:32] + "..."
        mod_d = e["module"] if len(e["module"]) <= 25 else e["module"][:22] + "..."
        label = _score_label(e["score"])
        print("  {:35s}  {:25s}  {:>5,d}  {:>5,d}  {:>5,d}  {:>5,d}  {:>5,d}  {:>3d}  {:>7.1f}  {:s}".format(
            cls_d, mod_d,
            e["loc"], e["methods"], e["fields"],
            e["fan_in"], e["fan_out"], e["depth"],
            e["score"], label))
        shown += 1

    print("")

    # Distribution by level
    level_counts = defaultdict(int)
    for e in entries:
        level_counts[_score_label(e["score"])] += 1

    print("  Distribution:")
    for lvl in ["EXTREME", "VERY HIGH", "HIGH", "MODERATE", "LOW", "TRIVIAL"]:
        cnt = level_counts.get(lvl, 0)
        if cnt > 0:
            pct = 100.0 * cnt / len(entries)
            bar = "#" * int(pct / 2)
            print("    {:10s}  {:>7,d}  ({:>5.1f}%)  {}".format(lvl, cnt, pct, bar))
    print("")

    # Top modules by average score
    if not module_filter:
        by_module = defaultdict(list)
        for e in entries:
            by_module[e["module"]].append(e["score"])

        mod_avgs = []
        for mod, scores in by_module.items():
            mod_avgs.append((mod, sum(scores) / len(scores), max(scores), len(scores)))
        mod_avgs.sort(key=lambda x: -x[1])

        print("  Top modules by avg complexity:")
        for mod, avg, mx, cnt in mod_avgs[:15]:
            print("    {:35s}  avg={:>7.1f}  max={:>7.1f}  classes={:>5,d}".format(
                mod, avg, mx, cnt))
        if len(mod_avgs) > 15:
            print("    ... and {:,d} more modules".format(len(mod_avgs) - 15))
        print("")

    # Summary
    total_analyzed = len(entries)
    avg_score = sum(e["score"] for e in entries) / total_analyzed if total_analyzed else 0
    print("  Summary:")
    print("    Classes analyzed:     {:>8,d}".format(total_analyzed))
    print("    Average score:        {:>8.1f}".format(avg_score))
    if entries:
        print("    Highest score:        {:>8.1f}  ({})".format(
            entries[0]["score"], entries[0]["class"]))
        print("    Median score:         {:>8.1f}".format(
            entries[total_analyzed // 2]["score"]))
    extreme = level_counts.get("EXTREME", 0)
    very_high = level_counts.get("VERY HIGH", 0)
    print("    EXTREME + VERY HIGH:  {:>8,d}  ({:.1f}%)".format(
        extreme + very_high,
        100.0 * (extreme + very_high) / total_analyzed if total_analyzed else 0))
    print("")


# ---------------------------------------------------------------------------
# cmd_metrics — module-level summary
# ---------------------------------------------------------------------------

def cmd_metrics(base_dir, module_name):
    """Show aggregated complexity metrics for a module."""
    ci = _load_class_index(base_dir)
    mi = _load_method_index(base_dir)
    fi = _load_field_index(base_dir)
    cg = _load_callgraph(base_dir)
    ih = _load_inheritance(base_dir)

    if not ci or not mi or not fi:
        return

    classes = ci.get("classes", {})
    class_methods = mi.get("class_methods", {})
    class_fields = fi.get("class_fields", {})

    fan_in_map = {}
    fan_out_map = {}
    if cg:
        calls = cg.get("calls", {})
        fan_in_map, fan_out_map = _compute_fan(calls)

    chains = {}
    if ih:
        chains = ih.get("class_to_chain", {})

    # Gather classes for this module
    entries = []
    for class_name, info_list in classes.items():
        if not info_list:
            continue
        info = info_list[0]
        if info.get("module", "") != module_name:
            continue

        loc = info.get("lines", 0)
        mc = len(class_methods.get(class_name, []))
        fc = len(class_fields.get(class_name, []))
        fi_val = fan_in_map.get(class_name, 0)
        fo_val = fan_out_map.get(class_name, 0)
        depth = len(chains.get(class_name, []))
        score = _compute_score(loc, mc, fc, fi_val, fo_val)

        entries.append({
            "class": class_name,
            "loc": loc,
            "methods": mc,
            "fields": fc,
            "fan_in": fi_val,
            "fan_out": fo_val,
            "depth": depth,
            "score": score,
        })

    if not entries:
        print("  No classes found for module '{}'.".format(module_name))
        return

    entries.sort(key=lambda e: -e["score"])

    total_loc = sum(e["loc"] for e in entries)
    total_methods = sum(e["methods"] for e in entries)
    total_fields = sum(e["fields"] for e in entries)
    avg_loc = total_loc / len(entries)
    avg_methods = total_methods / len(entries)
    avg_fields = total_fields / len(entries)
    avg_depth = sum(e["depth"] for e in entries) / len(entries)
    avg_score = sum(e["score"] for e in entries) / len(entries)
    max_score = entries[0]["score"]
    max_depth = max(e["depth"] for e in entries)

    # Distribution
    level_counts = defaultdict(int)
    for e in entries:
        level_counts[_score_label(e["score"])] += 1

    print("")
    print("  MODULE METRICS: {}".format(module_name))
    print("  " + "=" * 55)
    print("")

    print("  Aggregate:")
    print("    Classes:              {:>8,d}".format(len(entries)))
    print("    Total LOC:            {:>8,d}".format(total_loc))
    print("    Total methods:        {:>8,d}".format(total_methods))
    print("    Total fields:         {:>8,d}".format(total_fields))
    print("")

    print("  Averages:")
    print("    Avg LOC/class:        {:>8.1f}".format(avg_loc))
    print("    Avg methods/class:    {:>8.1f}".format(avg_methods))
    print("    Avg fields/class:     {:>8.1f}".format(avg_fields))
    print("    Avg depth:            {:>8.1f}".format(avg_depth))
    print("    Avg complexity score: {:>8.1f}".format(avg_score))
    print("")

    print("  Peaks:")
    print("    Max complexity:       {:>8.1f}  ({})".format(
        max_score, entries[0]["class"]))
    print("    Max LOC:              {:>8,d}  ({})".format(
        max(e["loc"] for e in entries),
        max(entries, key=lambda e: e["loc"])["class"]))
    print("    Max methods:          {:>8,d}  ({})".format(
        max(e["methods"] for e in entries),
        max(entries, key=lambda e: e["methods"])["class"]))
    print("    Max fields:           {:>8,d}  ({})".format(
        max(e["fields"] for e in entries),
        max(entries, key=lambda e: e["fields"])["class"]))
    print("    Max depth:            {:>8,d}  ({})".format(
        max_depth,
        max(entries, key=lambda e: e["depth"])["class"]))
    print("")

    print("  Complexity distribution:")
    for lvl in ["EXTREME", "VERY HIGH", "HIGH", "MODERATE", "LOW", "TRIVIAL"]:
        cnt = level_counts.get(lvl, 0)
        if cnt > 0:
            pct = 100.0 * cnt / len(entries)
            bar = "#" * int(pct / 2)
            print("    {:10s}  {:>5,d}  ({:>5.1f}%)  {}".format(lvl, cnt, pct, bar))
    print("")

    # Top 10 most complex classes in module
    top_n = min(10, len(entries))
    print("  Top {} most complex classes:".format(top_n))
    print("  {:35s}  {:>5s}  {:>5s}  {:>5s}  {:>5s}  {:>5s}  {:>3s}  {:>7s}".format(
        "CLASS", "LOC", "MTHDS", "FLDS", "FAN_I", "FAN_O", "DEP", "SCORE"))
    print("  " + "-" * 80)
    for e in entries[:top_n]:
        cls_d = e["class"] if len(e["class"]) <= 35 else e["class"][:32] + "..."
        print("  {:35s}  {:>5,d}  {:>5,d}  {:>5,d}  {:>5,d}  {:>5,d}  {:>3d}  {:>7.1f}".format(
            cls_d, e["loc"], e["methods"], e["fields"],
            e["fan_in"], e["fan_out"], e["depth"], e["score"]))
    print("")
