"""
Annotation commands for Module Navigator (Phase 7).

Commands:
  slots <class>                  List properties, actions, and topics
    --properties                 Only properties
    --actions                    Only actions
    --topics                     Only topics
  slots --by-type <type> [-n N]  Classes with properties of that type
    --module <mod>               Filter by module
  annotations <annotation> [-n N]  Classes with that annotation
    --module <mod>               Filter by module
"""

import json
import os


# Cache for REPL pre-loading
_annotations_cache = None


def load_annotations_index(base_dir):
    """Load annotations-index.json."""
    global _annotations_cache
    if _annotations_cache is not None:
        return _annotations_cache

    path = os.path.join(base_dir, "indexes", "annotations-index.json")
    if not os.path.isfile(path):
        print("ERROR: annotations-index.json not found.")
        print("Run: python tools/build_annotations_index.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# ---------------------------------------------------------------------------
# slots command
# ---------------------------------------------------------------------------

def cmd_slots(base_dir, class_name=None, show_properties=False,
              show_actions=False, show_topics=False,
              by_type=None, module_filter=None, limit=50):
    """Show Niagara slots (properties, actions, topics) for a class,
    or find classes by property type."""
    data = load_annotations_index(base_dir)
    if not data:
        return

    niagara_types = data.get("niagara_types", {})
    property_types = data.get("property_types", {})

    # Mode: --by-type
    if by_type:
        _slots_by_type(niagara_types, property_types, by_type,
                       module_filter=module_filter, limit=limit)
        return

    # Mode: show slots for a class
    if not class_name:
        print("  Usage: slots <class> [--properties] [--actions] [--topics]")
        print("         slots --by-type <type> [-n N] [--module mod]")
        return

    if class_name not in niagara_types:
        # Try case-insensitive
        matches = [k for k in niagara_types if k.lower() == class_name.lower()]
        if matches:
            class_name = matches[0]
        else:
            print("  '{}' is not a registered Niagara type.".format(class_name))
            # Try partial match
            partials = [k for k in niagara_types if class_name.lower() in k.lower()]
            if partials:
                print("  Did you mean: {}".format(", ".join(sorted(partials)[:10])))
            return

    entry = niagara_types[class_name]
    module = entry.get("module", "?")
    props = entry.get("properties", [])
    actions = entry.get("actions", [])
    topics = entry.get("topics", [])

    # Determine what to show
    show_all = not (show_properties or show_actions or show_topics)

    print("")
    print("  {} ({})".format(class_name, module))
    print("  " + "-" * 60)

    if show_all or show_properties:
        if props:
            print("")
            print("  PROPERTIES ({}):" .format(len(props)))
            for p in props:
                flags_str = ""
                if "flags" in p:
                    flags_str = " [flags={}]".format(p["flags"])
                override_str = " OVERRIDE" if p.get("override") else ""
                facets_str = ""
                if p.get("facets"):
                    facets_str = " facets={}".format(p["facets"])

                print("    {:30s} {:20s} = {}{}{}{}".format(
                    p.get("name", "?"),
                    p.get("type", "?"),
                    p.get("defaultValue", "?"),
                    flags_str,
                    override_str,
                    facets_str,
                ))
        elif show_properties:
            print("  (no properties)")

    if show_all or show_actions:
        if actions:
            print("")
            print("  ACTIONS ({}):" .format(len(actions)))
            for a in actions:
                parts = [a.get("name", "?")]
                if a.get("parameterType"):
                    parts.append("param={}".format(a["parameterType"]))
                if a.get("returnType"):
                    parts.append("returns={}".format(a["returnType"]))
                if "flags" in a:
                    parts.append("[flags={}]".format(a["flags"]))
                print("    {}".format("  ".join(parts)))
        elif show_actions:
            print("  (no actions)")

    if show_all or show_topics:
        if topics:
            print("")
            print("  TOPICS ({}):" .format(len(topics)))
            for t in topics:
                parts = [t.get("name", "?")]
                if t.get("eventType"):
                    parts.append("event={}".format(t["eventType"]))
                if "flags" in t:
                    parts.append("[flags={}]".format(t["flags"]))
                print("    {}".format("  ".join(parts)))
        elif show_topics:
            print("  (no topics)")

    total = len(props) + len(actions) + len(topics)
    print("")
    print("  Total slots: {} ({} properties, {} actions, {} topics)".format(
        total, len(props), len(actions), len(topics)))
    print("")


def _slots_by_type(niagara_types, property_types, type_name,
                   module_filter=None, limit=50):
    """Find classes that have properties of a given type."""
    # Try exact match in property_types index first
    refs = property_types.get(type_name, [])
    if not refs:
        # Try case-insensitive
        for k, v in property_types.items():
            if k.lower() == type_name.lower():
                refs = v
                type_name = k
                break

    if not refs:
        print("  No properties found with type '{}'.".format(type_name))
        # Suggest similar types
        similar = [k for k in property_types if type_name.lower() in k.lower()]
        if similar:
            print("  Similar types: {}".format(", ".join(sorted(similar)[:10])))
        return

    # Apply module filter
    if module_filter:
        filtered = []
        for ref in refs:
            class_name = ref.split(".")[0] if "." in ref else ref
            entry = niagara_types.get(class_name, {})
            if entry.get("module", "") == module_filter:
                filtered.append(ref)
        refs = filtered

    print("")
    print("  Properties of type '{}': {:,} usages".format(type_name, len(refs)))
    if module_filter:
        print("  (filtered by module: {})".format(module_filter))
    print("  " + "-" * 60)
    print("")

    shown = 0
    for ref in refs:
        if shown >= limit:
            remaining = len(refs) - shown
            if remaining > 0:
                print("  ... and {:,} more (use -n to show more)".format(remaining))
            break
        # ref is "ClassName.propName"
        if "." in ref:
            cls, prop = ref.split(".", 1)
            mod = niagara_types.get(cls, {}).get("module", "?")
            print("    {:30s} {:20s} ({})".format(cls, prop, mod))
        else:
            print("    {}".format(ref))
        shown += 1

    print("")


# ---------------------------------------------------------------------------
# annotations command
# ---------------------------------------------------------------------------

def cmd_annotations(base_dir, annotation_name, module_filter=None, limit=50):
    """List all classes with a specific Niagara annotation."""
    data = load_annotations_index(base_dir)
    if not data:
        return

    niagara_types = data.get("niagara_types", {})

    # Normalize annotation name
    ann = annotation_name
    if ann.startswith("@"):
        ann = ann[1:]
    # Accept short forms
    if not ann.startswith("Niagara"):
        ann = "Niagara" + ann

    # Filter classes by annotation type
    results = []
    for class_name, entry in niagara_types.items():
        module = entry.get("module", "?")

        if module_filter and module != module_filter:
            continue

        has_annotation = False
        if ann == "NiagaraType":
            has_annotation = True  # all entries have @NiagaraType
        elif ann == "NiagaraProperty" or ann == "NiagaraProperties":
            has_annotation = bool(entry.get("properties"))
        elif ann == "NiagaraAction" or ann == "NiagaraActions":
            has_annotation = bool(entry.get("actions"))
        elif ann == "NiagaraTopic":
            has_annotation = bool(entry.get("topics"))
        else:
            print("  Unknown annotation: @{}".format(ann))
            print("  Available: NiagaraType, NiagaraProperty, NiagaraAction, NiagaraTopic")
            return

        if has_annotation:
            count = 0
            if ann in ("NiagaraProperty", "NiagaraProperties"):
                count = len(entry.get("properties", []))
            elif ann in ("NiagaraAction", "NiagaraActions"):
                count = len(entry.get("actions", []))
            elif ann == "NiagaraTopic":
                count = len(entry.get("topics", []))

            results.append((class_name, module, count))

    # Sort by count descending (for properties/actions/topics), then by name
    if ann != "NiagaraType":
        results.sort(key=lambda x: (-x[2], x[0]))
    else:
        results.sort(key=lambda x: x[0])

    print("")
    print("  @{}: {:,} classes".format(ann, len(results)))
    if module_filter:
        print("  (filtered by module: {})".format(module_filter))
    print("  " + "-" * 60)
    print("")

    shown = 0
    for class_name, module, count in results:
        if shown >= limit:
            remaining = len(results) - shown
            if remaining > 0:
                print("  ... and {:,} more (use -n to show more)".format(remaining))
            break

        if ann == "NiagaraType":
            n_props = len(niagara_types[class_name].get("properties", []))
            n_acts = len(niagara_types[class_name].get("actions", []))
            n_tops = len(niagara_types[class_name].get("topics", []))
            detail = "props={} acts={} topics={}".format(n_props, n_acts, n_tops)
            print("    {:35s} {:25s} {}".format(class_name, module, detail))
        else:
            print("    {:35s} {:25s} {:>3} slots".format(class_name, module, count))

        shown += 1

    print("")
