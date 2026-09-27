"""
Niagara pattern detection for Module Navigator (Phase 17).

Commands:
  patterns <module>              Detect architectural patterns in a module
  pattern services [-n N]        All Service classes across corpus
  pattern drivers [-n N]         Driver stack classes (BDevice, BNetwork, ...)
  pattern points [-n N]          Point and extension classes
  pattern views [-n N]           UI view classes (Workbench editors/views)

No index build required -- uses inheritance.json + class-index.json +
annotations-index.json (on-demand, cached after first load).
"""

import sys


# ---------------------------------------------------------------------------
# Pattern definitions -- known Niagara architectural base classes
# ---------------------------------------------------------------------------

PATTERN_DEFS = [
    {
        "name": "services",
        "label": "Services",
        "description": "Background services (BAbstractService descendants)",
        "base_classes": ["BAbstractService"],
    },
    {
        "name": "drivers",
        "label": "Drivers",
        "description": "Driver stack (BDevice, BDeviceNetwork, BNetwork, BNiagaraNetwork)",
        "base_classes": [
            "BDevice", "BDeviceNetwork", "BNetwork",
            "BNiagaraNetwork", "BDeviceFolder",
        ],
    },
    {
        "name": "points",
        "label": "Points",
        "description": "Control points and extensions (BControlPoint, BProxyExt)",
        "base_classes": [
            "BControlPoint", "BNumericPoint", "BBooleanPoint",
            "BStringPoint", "BEnumPoint", "BProxyExt",
        ],
    },
    {
        "name": "views",
        "label": "UI Views",
        "description": "Workbench/UX views and editors",
        "base_classes": [
            "BWbComponentView", "BWbSheetEditor", "BWbEditor",
            "BWbPlugin", "BWbView",
        ],
    },
    {
        "name": "extensions",
        "label": "Extensions",
        "description": "Component extensions (BExtension descendants)",
        "base_classes": ["BExtension"],
    },
    {
        "name": "enums",
        "label": "Enums",
        "description": "Frozen enums (BFrozenEnum descendants)",
        "base_classes": ["BFrozenEnum"],
    },
    {
        "name": "structs",
        "label": "Structs",
        "description": "Value types / structs (BStruct descendants)",
        "base_classes": ["BStruct"],
    },
]

# Lookup by name
_PATTERN_MAP = {p["name"]: p for p in PATTERN_DEFS}


# ---------------------------------------------------------------------------
# Index loading helpers (reuse existing loaders with caching)
# ---------------------------------------------------------------------------

def _load_inheritance(base_dir):
    from module_nav_lib.hierarchy import load_inheritance
    return load_inheritance(base_dir)


def _load_class_index(base_dir):
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


def _load_annotations(base_dir):
    from module_nav_lib.annotations import load_annotations_index
    return load_annotations_index(base_dir)


# ---------------------------------------------------------------------------
# Core: recursive descendant collection
# ---------------------------------------------------------------------------

def _collect_descendants(base_class, p2c, seen=None):
    """Recursively collect ALL descendants of a base class. Returns set."""
    if seen is None:
        seen = set()
    if base_class in seen:
        return seen
    children = p2c.get(base_class, [])
    for child in children:
        seen.add(child)
        _collect_descendants(child, p2c, seen)
    return seen


def _get_pattern_classes(pattern_name, base_dir):
    """Get all classes matching a pattern. Returns list of (class_name, module, package)."""
    pdef = _PATTERN_MAP.get(pattern_name)
    if not pdef:
        return None, "Unknown pattern: '{}'".format(pattern_name)

    inh = _load_inheritance(base_dir)
    if not inh:
        return None, "inheritance.json not available"

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return None, "class-index.json not available"

    p2c = inh.get("parent_to_children", {})
    ci_classes = ci_data.get("classes", {})

    # Collect descendants from ALL base classes in this pattern
    all_descendants = set()
    matched_bases = []
    for base_cls in pdef["base_classes"]:
        if base_cls in p2c:
            desc = _collect_descendants(base_cls, p2c)
            all_descendants.update(desc)
            matched_bases.append((base_cls, len(desc)))

    # Build results with module info
    results = []
    for cls_name in sorted(all_descendants):
        entries = ci_classes.get(cls_name, [])
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            results.append((cls_name, top[0].get("module", "?"), top[0].get("package", "?")))
        elif entries:
            results.append((cls_name, entries[0].get("module", "?"), entries[0].get("package", "?")))
        else:
            results.append((cls_name, "?", "?"))

    return {
        "pattern": pdef,
        "matched_bases": matched_bases,
        "classes": results,
    }, None


# ---------------------------------------------------------------------------
# patterns <module> command
# ---------------------------------------------------------------------------

def cmd_patterns(base_dir, module_name, limit=50):
    """Detect all architectural patterns in a module."""
    inh = _load_inheritance(base_dir)
    if not inh:
        return

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return

    p2c = inh.get("parent_to_children", {})
    ci_classes = ci_data.get("classes", {})

    # Build set of classes in this module
    module_classes = set()
    for cls_name, entries in ci_classes.items():
        for e in entries:
            if e.get("module") == module_name and not e.get("outer_class"):
                module_classes.add(cls_name)

    if not module_classes:
        # Try partial match
        all_mods = set()
        for cls_name, entries in ci_classes.items():
            for e in entries:
                m = e.get("module", "")
                if m:
                    all_mods.add(m)
        partial = sorted(m for m in all_mods if module_name.lower() in m.lower())[:10]
        print("")
        print("  Module '{}' not found or has no classes.".format(module_name))
        if partial:
            print("  Did you mean: {}".format(", ".join(partial)))
        print("")
        return

    # Try loading annotations for slot counts
    ann_data = _load_annotations(base_dir)
    ann_types = {}
    if ann_data:
        for cls_name, info in ann_data.get("types", {}).items():
            ann_types[cls_name] = info

    # Check each pattern
    detected = []
    for pdef in PATTERN_DEFS:
        # Collect ALL descendants for each base class
        all_desc = set()
        for base_cls in pdef["base_classes"]:
            if base_cls in p2c:
                all_desc.update(_collect_descendants(base_cls, p2c))

        # Intersect with module classes
        matched = sorted(module_classes & all_desc)
        if matched:
            detected.append((pdef, matched))

    # Also detect classes NOT matched by any pattern
    all_matched = set()
    for _, matched in detected:
        all_matched.update(matched)
    unmatched = sorted(module_classes - all_matched)

    print("")
    print("  " + "=" * 65)
    print("  PATTERNS IN: {} ({} classes)".format(module_name, len(module_classes)))
    print("  " + "=" * 65)
    print("")

    if not detected:
        print("  No known architectural patterns detected.")
        print("  Module has {} classes (may be utilities/helpers).".format(len(module_classes)))
        print("")
        return

    total_detected = 0
    for pdef, matched in detected:
        total_detected += len(matched)
        print("  {} ({} classes):".format(pdef["label"].upper(), len(matched)))
        print("  {}".format(pdef["description"]))
        print("")

        shown = 0
        for cls_name in matched:
            if shown >= limit:
                break
            # Get slot summary
            slot_info = ""
            if cls_name in ann_types:
                t = ann_types[cls_name]
                props = len(t.get("properties", []))
                actions = len(t.get("actions", []))
                topics = len(t.get("topics", []))
                parts = []
                if props:
                    parts.append("{}p".format(props))
                if actions:
                    parts.append("{}a".format(actions))
                if topics:
                    parts.append("{}t".format(topics))
                if parts:
                    slot_info = "  [{}]".format(",".join(parts))

            print("    {}{}".format(cls_name, slot_info))
            shown += 1

        if len(matched) > limit:
            print("    ... and {} more".format(len(matched) - limit))
        print("")

    # Summary
    print("  SUMMARY:")
    for pdef, matched in detected:
        print("    {:15s} {:>4} classes".format(pdef["label"] + ":", len(matched)))
    print("    {:15s} {:>4} classes".format("Unmatched:", len(unmatched)))
    print("    {:15s} {:>4} classes".format("TOTAL:", len(module_classes)))
    print("")

    # Show a few unmatched if any
    if unmatched and len(unmatched) <= 20:
        print("  UNMATCHED CLASSES:")
        for cls_name in unmatched:
            slot_info = ""
            if cls_name in ann_types:
                t = ann_types[cls_name]
                props = len(t.get("properties", []))
                actions = len(t.get("actions", []))
                parts = []
                if props:
                    parts.append("{}p".format(props))
                if actions:
                    parts.append("{}a".format(actions))
                if parts:
                    slot_info = "  [{}]".format(",".join(parts))
            print("    {}{}".format(cls_name, slot_info))
        print("")
    elif unmatched:
        print("  {} unmatched classes (use 'modules {}' for full listing)".format(
            len(unmatched), module_name))
        print("")


# ---------------------------------------------------------------------------
# pattern <category> command
# ---------------------------------------------------------------------------

def cmd_pattern(base_dir, pattern_name, limit=50, module_filter=None):
    """List all classes matching a specific pattern across corpus."""
    result, err = _get_pattern_classes(pattern_name, base_dir)
    if err:
        print("")
        print("  ERROR: {}".format(err))
        if pattern_name not in _PATTERN_MAP:
            print("  Available patterns: {}".format(
                ", ".join(p["name"] for p in PATTERN_DEFS)))
        print("")
        return

    pdef = result["pattern"]
    classes = result["classes"]
    matched_bases = result["matched_bases"]

    # Apply module filter
    if module_filter:
        classes = [(c, m, p) for c, m, p in classes if m == module_filter]

    print("")
    print("  " + "=" * 65)
    print("  PATTERN: {} — {} classes{}".format(
        pdef["label"].upper(),
        len(classes),
        " in {}".format(module_filter) if module_filter else "",
    ))
    print("  {}".format(pdef["description"]))
    print("  " + "=" * 65)
    print("")

    # Show matched base classes and their descendant counts
    if matched_bases:
        print("  BASE CLASSES:")
        for base_cls, count in sorted(matched_bases, key=lambda x: -x[1]):
            print("    {:35s} {:>5,} descendants".format(base_cls, count))
        print("")

    if not classes:
        if module_filter:
            print("  No {} found in module '{}'.".format(pdef["label"].lower(), module_filter))
        else:
            print("  No {} found in corpus.".format(pdef["label"].lower()))
        print("")
        return

    # Group by module for summary
    module_counts = {}
    for _, mod, _ in classes:
        module_counts[mod] = module_counts.get(mod, 0) + 1

    sorted_mods = sorted(module_counts.items(), key=lambda x: -x[1])

    # Show module breakdown (top 20)
    print("  BY MODULE ({} modules):".format(len(sorted_mods)))
    print("  {:>5s}  {}".format("COUNT", "MODULE"))
    print("  " + "-" * 50)
    shown_mods = 0
    for mod, count in sorted_mods:
        if shown_mods >= 20:
            break
        print("  {:>5,}  {}".format(count, mod))
        shown_mods += 1
    if len(sorted_mods) > 20:
        print("  ... and {} more modules".format(len(sorted_mods) - 20))
    print("")

    # Show classes (detailed listing)
    print("  CLASSES:")
    print("  {:>35s}  {:30s}  {:s}".format("CLASS", "MODULE", "PACKAGE"))
    print("  " + "-" * 90)

    shown = 0
    for cls_name, mod, pkg in classes:
        if shown >= limit:
            break
        print("  {:>35s}  {:30s}  {:s}".format(
            _trunc(cls_name, 35), _trunc(mod, 30), pkg))
        shown += 1

    if len(classes) > limit:
        print("")
        print("  ... and {} more (use -n {} to show all)".format(
            len(classes) - limit, len(classes)))
    print("")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _trunc(s, max_len):
    """Truncate string with ellipsis."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."
