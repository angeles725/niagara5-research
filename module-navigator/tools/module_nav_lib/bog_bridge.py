"""
BOG-Code Bridge commands for Module Navigator (Phase 16).

Connects BOG Navigator (runtime config) with Module Navigator (decompiled code).
Answers: "this component in the station, what Java code controls it?"

Commands:
  bog-trace <path-or-type>     Trace BOG component to Java class with full profile
    [--bog-index path]         Path to bog_index.json (auto-detected)
  bog-classes [--bog-index P]  List unique Niagara types used in BOG + resolution
  bog-coverage [--bog-index P] What % of code-base classes appear in BOG

No index build required -- reads bog_index.json + Module Nav indexes on-demand.
"""

import json
import os
import sys


# ---------------------------------------------------------------------------
# BOG index loading (auto-detect location)
# ---------------------------------------------------------------------------

_bog_cache = None
_bog_path_used = None

# Well-known locations to search for bog_index.json
_BOG_SEARCH_PATHS = [
    # Sibling of module-navigator (same parent dir)
    lambda base: os.path.join(os.path.dirname(base), "tools", "bog_index.json"),
    # Reflow-Clean project
    r"/home/cristian/modules/Prototipos/Reflow-Clean/tools/bog_index.json",
    # CWD
    lambda base: os.path.join(os.getcwd(), "bog_index.json"),
]


def _find_bog_index(base_dir, explicit_path=None):
    """Find bog_index.json. Returns path or None.

    Priority:
      1. Explicit path (CLI --bog-index flag)
      2. BOG_INDEX_PATH environment variable
      3. Well-known _BOG_SEARCH_PATHS locations
    """
    if explicit_path:
        if os.path.isfile(explicit_path):
            return explicit_path
        return None

    env_path = os.environ.get("BOG_INDEX_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    for loc in _BOG_SEARCH_PATHS:
        if callable(loc):
            p = loc(base_dir)
        else:
            p = loc
        if os.path.isfile(p):
            return p

    return None


def _load_bog(base_dir, explicit_path=None):
    """Load BOG index. Cached after first load."""
    global _bog_cache, _bog_path_used

    if _bog_cache is not None:
        return _bog_cache, _bog_path_used

    path = _find_bog_index(base_dir, explicit_path)
    if not path:
        return None, None

    with open(path, "r", encoding="utf-8") as f:
        _bog_cache = json.load(f)
    _bog_path_used = path
    return _bog_cache, path


def _load_class_index(base_dir):
    """Load class-index.json."""
    ci_path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(ci_path):
        return None
    with open(ci_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_annotations(base_dir):
    """Load annotations-index.json."""
    ai_path = os.path.join(base_dir, "indexes", "annotations-index.json")
    if not os.path.isfile(ai_path):
        return None
    with open(ai_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_inheritance(base_dir):
    """Load inheritance.json."""
    ih_path = os.path.join(base_dir, "indexes", "inheritance.json")
    if not os.path.isfile(ih_path):
        return None
    with open(ih_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Niagara module prefix -> module name mapping
# ---------------------------------------------------------------------------

# Common Niagara module short prefixes used in BOG types
_MODULE_PREFIX_MAP = {
    "a": "alarm",
    "b": "baja",
    "bac": "bacnet",
    "box": "box",
    "c": "control",
    "conv": "conv",
    "d": "driver",
    "h": "history",
    "hbdm": "honBacnetDm",
    "jstk": "jstack",
    "kitControl": "kitControl",
    "n": "net",
    "nd": "ndio",
    "nss": "niagaraStation",
    "p": "program",
    "sch": "schedule",
    "td": "timeDashboard",
    "w": "web",
    "amd": "amd",
    "TW": "twBacnetDevice",
    "EDM": "edm",
}


def _resolve_bog_type(type_spec, ci_classes):
    """Resolve a BOG type spec (e.g. 'c:NumericWritable') to Java class entries.

    Returns list of (class_name, entry) tuples.
    """
    if not type_spec or ":" not in type_spec:
        return []

    prefix, type_name = type_spec.split(":", 1)

    # Try with and without B prefix
    candidates = ["B" + type_name, type_name]
    if type_name.startswith("B"):
        candidates.append(type_name[1:])

    # Get module hint from prefix map
    module_hint = _MODULE_PREFIX_MAP.get(prefix, prefix)

    found = []
    for cand in candidates:
        if cand in ci_classes:
            for entry in ci_classes[cand]:
                if entry.get("outer_class") is not None:
                    continue
                mod = entry.get("module", "")
                # Prefer entries whose module matches the prefix hint
                if module_hint and (module_hint in mod or mod.startswith(module_hint)):
                    found.insert(0, (cand, entry))
                else:
                    found.append((cand, entry))

    # If no results, try case-insensitive
    if not found:
        for cand in candidates:
            cand_lower = cand.lower()
            for k, entries in ci_classes.items():
                if k.lower() == cand_lower:
                    for entry in entries:
                        if entry.get("outer_class") is None:
                            found.append((k, entry))

    return found


# ---------------------------------------------------------------------------
# bog-trace: BOG component -> Java class full profile
# ---------------------------------------------------------------------------

def cmd_bog_trace(base_dir, query, bog_index_path=None):
    """Trace a BOG component (by path or type) to its Java class."""
    bog, bog_path = _load_bog(base_dir, bog_index_path)
    if not bog:
        print("")
        print("  ERROR: bog_index.json not found.")
        print("  Searched: well-known locations")
        if bog_index_path:
            print("  Explicit: {}".format(bog_index_path))
        print("  Run: python bog_navigator.py extract <config.bog>")
        return

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: class-index.json not found.")
        return

    ci_classes = ci_data.get("classes", {})
    components = bog.get("components", [])

    print("")
    print("  " + "=" * 65)
    print("  BOG TRACE: {}".format(query))
    print("  " + "=" * 65)
    print("  BOG index: {}".format(bog_path))
    print("")

    # Determine if query is a path or a type spec
    target_type = None
    target_comp = None

    if "/" in query:
        # It's a path — find component by path match
        query_clean = query.strip("/")
        matches = []
        for comp in components:
            comp_path = comp.get("path", "").strip("/")
            if comp_path == query_clean or comp_path.endswith("/" + query_clean):
                matches.append(comp)
            elif query_clean in comp_path:
                matches.append(comp)

        if not matches:
            print("  No BOG component found for path: {}".format(query))
            print("  Try: bog-classes to see available types")
            return

        # Use the best match (exact > partial)
        target_comp = matches[0]
        target_type = target_comp.get("type", "")

        # Print BOG component info
        print("  BOG COMPONENT:")
        print("    Path:    {}".format(target_comp.get("path", "")))
        print("    Name:    {}".format(target_comp.get("name", "")))
        print("    Type:    {}".format(target_type))
        if target_comp.get("handle"):
            print("    Handle:  {}".format(target_comp["handle"]))
        if target_comp.get("value"):
            print("    Value:   {}".format(target_comp["value"]))
        print("    Line:    {}".format(target_comp.get("line", "")))

        if len(matches) > 1:
            print("")
            print("  Other matches ({} total):".format(len(matches)))
            for m in matches[1:5]:
                print("    {} [{}]".format(m.get("path", ""), m.get("type", "")))

    elif ":" in query:
        # It's a type spec directly
        target_type = query
        # Find example components with this type
        examples = [c for c in components if c.get("type") == target_type]
        print("  BOG TYPE: {}".format(target_type))
        print("  Instances in BOG: {}".format(len(examples)))
        if examples:
            print("")
            print("  Sample instances:")
            for ex in examples[:5]:
                val = " = {}".format(ex["value"]) if ex.get("value") else ""
                print("    {}{}".format(ex.get("path", ""), val))
    else:
        # Try as partial type name
        target_type = query
        # Search for types containing the query
        matching_types = set()
        for comp in components:
            t = comp.get("type", "")
            if query.lower() in t.lower():
                matching_types.add(t)
        if matching_types:
            print("  Matching BOG types:")
            for t in sorted(matching_types)[:10]:
                count = sum(1 for c in components if c.get("type") == t)
                print("    {} ({} instances)".format(t, count))
            target_type = sorted(matching_types)[0]
            print("")
            print("  Using first match: {}".format(target_type))
        else:
            print("  No BOG type matching '{}' found.".format(query))
            return

    if not target_type or ":" not in target_type:
        print("")
        print("  Cannot resolve type without module:TypeName format.")
        return

    # Resolve to Java class
    print("")
    print("  " + "-" * 55)
    print("  JAVA CLASS RESOLUTION")
    print("  " + "-" * 55)
    print("")

    results = _resolve_bog_type(target_type, ci_classes)

    if not results:
        prefix, type_name = target_type.split(":", 1)
        print("  Type '{}' not found in class-index.".format(target_type))
        print("  Tried: B{}, {}".format(type_name, type_name))
        hint = _MODULE_PREFIX_MAP.get(prefix, prefix)
        print("  Module hint: {} (prefix '{}')".format(hint, prefix))
        print("")
        print("  Suggestions:")
        print("    search '*{}*'".format(type_name))
        print("    modules --has-code | grep {}".format(hint))
        return

    # Show top result with enriched info
    top_class, top_entry = results[0]

    print("    Class:     {}".format(top_class))
    print("    Package:   {}".format(top_entry.get("package", "")))
    print("    Module:    {}".format(top_entry.get("module", "")))
    print("    Kind:      {}".format(top_entry.get("kind", "")))
    if top_entry.get("extends"):
        print("    Extends:   {}".format(top_entry["extends"]))
    if top_entry.get("implements"):
        print("    Implements: {}".format(", ".join(top_entry["implements"])))
    print("    Lines:     {:,}".format(top_entry.get("lines", 0)))
    print("    Path:      {}".format(top_entry.get("path", "")))

    if len(results) > 1:
        print("")
        print("    Other definitions:")
        for cn, e in results[1:3]:
            print("      {} in {} ({})".format(cn, e.get("module", ""), e.get("package", "")))

    # Enrich with annotations if available
    ann_data = _load_annotations(base_dir)
    if ann_data:
        types_data = ann_data.get("niagara_types", {})
        if top_class in types_data:
            tinfo = types_data[top_class]
            props = tinfo.get("properties", [])
            actions = tinfo.get("actions", [])
            topics = tinfo.get("topics", [])

            if props or actions or topics:
                print("")
                print("  " + "-" * 55)
                print("  NIAGARA SLOTS")
                print("  " + "-" * 55)
                print("")
                if props:
                    print("    Properties ({})".format(len(props)))
                    for p in props[:15]:
                        flags = " [{}]".format(p["flags"]) if p.get("flags") else ""
                        print("      {} : {}{}".format(p["name"], p["type"], flags))
                    if len(props) > 15:
                        print("      ... and {} more".format(len(props) - 15))

                if actions:
                    print("")
                    print("    Actions ({})".format(len(actions)))
                    for a in actions[:10]:
                        print("      {}".format(a["name"]))
                    if len(actions) > 10:
                        print("      ... and {} more".format(len(actions) - 10))

                if topics:
                    print("")
                    print("    Topics ({})".format(len(topics)))
                    for t in topics[:5]:
                        print("      {}".format(t["name"]))

    # Enrich with inheritance
    inh_data = _load_inheritance(base_dir)
    if inh_data:
        children_data = inh_data.get("children", {})
        chains = inh_data.get("chains", {})

        if top_class in chains:
            chain = chains[top_class]
            print("")
            print("  " + "-" * 55)
            print("  INHERITANCE CHAIN")
            print("  " + "-" * 55)
            print("")
            print("    " + " -> ".join(chain))

        if top_class in children_data:
            kids = children_data[top_class]
            if kids:
                print("")
                print("    Direct subclasses: {} ({})".format(
                    len(kids), ", ".join(kids[:5])))
                if len(kids) > 5:
                    print("    ... and {} more".format(len(kids) - 5))

    # Summary
    print("")
    print("  " + "-" * 55)
    print("  NEXT STEPS")
    print("  " + "-" * 55)
    print("")
    print("    source {} --code          Full source code".format(top_class))
    print("    methods {}                All methods".format(top_class))
    print("    slots {}                  Niagara properties/actions".format(top_class))
    print("    xref {}                   Who uses this class".format(top_class))
    print("    hierarchy {}              Subclass tree".format(top_class))
    print("")


# ---------------------------------------------------------------------------
# bog-classes: unique types used in BOG with Java resolution
# ---------------------------------------------------------------------------

def cmd_bog_classes(base_dir, bog_index_path=None):
    """List unique Niagara types used in BOG and resolve each to Java class."""
    bog, bog_path = _load_bog(base_dir, bog_index_path)
    if not bog:
        print("")
        print("  ERROR: bog_index.json not found.")
        return

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: class-index.json not found.")
        return

    ci_classes = ci_data.get("classes", {})
    components = bog.get("components", [])

    # Collect unique types with counts
    from collections import Counter
    type_counts = Counter(c.get("type", "") for c in components if c.get("type"))

    print("")
    print("  " + "=" * 65)
    print("  BOG CLASSES — Niagara Types in Station Config")
    print("  " + "=" * 65)
    print("  BOG index: {}".format(bog_path))
    print("  Total components: {:,}".format(len(components)))
    print("  Unique types: {}".format(len(type_counts)))
    print("")

    # Group by prefix (module)
    from collections import defaultdict
    by_prefix = defaultdict(list)
    for type_spec, count in type_counts.most_common():
        if ":" in type_spec:
            prefix = type_spec.split(":")[0]
        else:
            prefix = "?"
        by_prefix[prefix].append((type_spec, count))

    resolved_count = 0
    unresolved_count = 0
    unresolved_types = []

    print("  {:<35} {:>6}  {}".format("BOG Type", "Count", "Java Class"))
    print("  " + "-" * 65)

    for prefix in sorted(by_prefix.keys()):
        items = by_prefix[prefix]
        module_hint = _MODULE_PREFIX_MAP.get(prefix, prefix)
        total_in_prefix = sum(c for _, c in items)
        print("")
        print("  [{} -> {}] ({} types, {:,} instances)".format(
            prefix, module_hint, len(items), total_in_prefix))

        for type_spec, count in sorted(items, key=lambda x: -x[1]):
            results = _resolve_bog_type(type_spec, ci_classes)
            if results:
                resolved_count += 1
                cls_name = results[0][0]
                mod = results[0][1].get("module", "?")
                print("    {:<33} {:>5}  {} ({})".format(
                    type_spec, count, cls_name, mod))
            else:
                unresolved_count += 1
                unresolved_types.append((type_spec, count))
                print("    {:<33} {:>5}  ???".format(type_spec, count))

    print("")
    print("  " + "=" * 65)
    print("  RESOLUTION SUMMARY")
    print("  " + "=" * 65)
    print("")
    print("    Resolved:   {}/{} types ({:.1f}%)".format(
        resolved_count, resolved_count + unresolved_count,
        100.0 * resolved_count / max(resolved_count + unresolved_count, 1)))
    print("    Unresolved: {}".format(unresolved_count))

    if unresolved_types:
        print("")
        print("    Top unresolved:")
        for ts, cnt in sorted(unresolved_types, key=lambda x: -x[1])[:10]:
            print("      {} ({} instances)".format(ts, cnt))

    print("")


# ---------------------------------------------------------------------------
# bog-coverage: how much of the code-base is used in BOG
# ---------------------------------------------------------------------------

def cmd_bog_coverage(base_dir, bog_index_path=None):
    """Show what % of code-base classes appear in BOG."""
    bog, bog_path = _load_bog(base_dir, bog_index_path)
    if not bog:
        print("")
        print("  ERROR: bog_index.json not found.")
        return

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: class-index.json not found.")
        return

    ci_classes = ci_data.get("classes", {})
    components = bog.get("components", [])

    # Unique BOG types
    bog_types = set(c.get("type", "") for c in components if c.get("type"))

    print("")
    print("  " + "=" * 65)
    print("  BOG COVERAGE — Code vs Runtime")
    print("  " + "=" * 65)
    print("  BOG index: {}".format(bog_path))
    print("")

    # Resolve each BOG type to a Java class
    resolved_classes = set()   # Java class names found in BOG
    resolved_modules = set()   # modules referenced by BOG

    for type_spec in bog_types:
        results = _resolve_bog_type(type_spec, ci_classes)
        if results:
            for cls_name, entry in results[:1]:  # only top match
                resolved_classes.add(cls_name)
                resolved_modules.add(entry.get("module", "?"))

    # Count total top-level classes (no inner classes)
    total_classes = 0
    classes_by_module = {}
    for class_name, entries in ci_classes.items():
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            total_classes += 1
            mod = top[0].get("module", "?")
            if mod not in classes_by_module:
                classes_by_module[mod] = set()
            classes_by_module[mod].add(class_name)

    total_modules = len(classes_by_module)

    # Per-module coverage
    module_coverage = {}
    for mod in resolved_modules:
        if mod in classes_by_module:
            mod_classes = classes_by_module[mod]
            used = mod_classes & resolved_classes
            module_coverage[mod] = {
                "total": len(mod_classes),
                "used": len(used),
                "pct": 100.0 * len(used) / max(len(mod_classes), 1),
            }

    print("  OVERALL:")
    print("    BOG types:          {:,}".format(len(bog_types)))
    print("    Resolved classes:   {:,}".format(len(resolved_classes)))
    print("    Total classes:      {:,}".format(total_classes))
    print("    Class coverage:     {:.2f}%".format(
        100.0 * len(resolved_classes) / max(total_classes, 1)))
    print("    BOG modules:        {}".format(len(resolved_modules)))
    print("    Total modules:      {}".format(total_modules))
    print("    Module coverage:    {:.1f}%".format(
        100.0 * len(resolved_modules) / max(total_modules, 1)))

    print("")
    print("  PER-MODULE COVERAGE (used in BOG):")
    print("  {:<25} {:>6} {:>6} {:>7}".format("Module", "Used", "Total", "Pct"))
    print("  " + "-" * 50)

    for mod, info in sorted(module_coverage.items(), key=lambda x: -x[1]["used"]):
        print("  {:<25} {:>5} {:>6}   {:>5.1f}%".format(
            mod, info["used"], info["total"], info["pct"]))

    print("")
    print("  MODULES NOT USED IN BOG ({} total, showing top 10 by class count):".format(
        total_modules - len(resolved_modules)))
    unused = [(m, len(c)) for m, c in classes_by_module.items()
              if m not in resolved_modules]
    for mod, cnt in sorted(unused, key=lambda x: -x[1])[:10]:
        print("    {:<25} ({} classes)".format(mod, cnt))

    print("")
