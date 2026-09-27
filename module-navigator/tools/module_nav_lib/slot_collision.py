"""
Slot collision detection for Module Navigator (Batch 5, Gap #8).

Detects when two different modules define slots with the same name in the
station tree. The second overwrites the first silently, causing runtime bugs.

Commands:
  slot-collision
    [--module <mod>]       # optional: only this module vs all others
    [--json]              # structured JSON output

Reuses existing indexes (no new builders):
  annotations-index.json, class-index.json
"""

import json
import os


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached per process)
# ---------------------------------------------------------------------------

_annotations_cache = None
_class_index_cache = None


def _load_json(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print("  ERROR loading {}: {}".format(os.path.basename(path), exc))
        return None


def _load_annotations(base_dir):
    global _annotations_cache
    if _annotations_cache is not None:
        return _annotations_cache
    _annotations_cache = _load_json(
        os.path.join(base_dir, "indexes", "annotations-index.json"))
    return _annotations_cache


def _load_class_index(base_dir):
    global _class_index_cache
    if _class_index_cache is not None:
        return _class_index_cache
    _class_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "class-index.json"))
    return _class_index_cache


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def _build_slot_index(niagara_types):
    """Build index: slot_name -> [{class, module, type}, ...]
    
    Only includes slots from @NiagaraProperty annotations.
    """
    slot_index = {}  # slot_name -> list of {class, module, type}

    for class_name, entry in niagara_types.items():
        module = entry.get("module", "?")
        for prop in entry.get("properties", []):
            name = prop.get("name", "")
            if not name:
                continue
            if name not in slot_index:
                slot_index[name] = []
            slot_index[name].append({
                "class": class_name,
                "module": module,
                "type": prop.get("type", "?"),
            })

    return slot_index


def _find_collisions(slot_index, module_filter=None):
    """Find slots that appear in multiple modules.

    If module_filter is set, only report collisions involving that module.
    A collision is: same slot name, different modules.
    """
    collisions = []

    for slot_name, refs in slot_index.items():
        # Group by module
        module_refs = {}
        for ref in refs:
            mod = ref["module"]
            if mod not in module_refs:
                module_refs[mod] = []
            module_refs[mod].append(ref)

        # Only interested in slots that span multiple modules
        if len(module_refs) < 2:
            continue

        # If filtering by module, skip if this module doesn't participate
        if module_filter and module_filter not in module_refs:
            continue

        # Build collision report
        modules_involved = sorted(module_refs.keys())
        total_refs = len(refs)

        # Check if it's a real collision (same slot, different classes in different modules)
        # Sort by module then class for stable display
        all_refs = []
        for mod, mod_refs in module_refs.items():
            for ref in mod_refs:
                all_refs.append({
                    "module": mod,
                    "class": ref["class"],
                    "type": ref["type"],
                })
        all_refs.sort(key=lambda x: (x["module"], x["class"]))

        collisions.append({
            "slot": slot_name,
            "modules": modules_involved,
            "total_refs": total_refs,
            "refs": all_refs,
        })

    # Sort by slot name
    collisions.sort(key=lambda x: x["slot"])
    return collisions


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_slot_collision(base_dir, module_filter=None, as_json=False):
    """Detect slot name collisions across modules."""
    # Load indexes
    ann = _load_annotations(base_dir)
    ci = _load_class_index(base_dir)

    if not ann:
        print("  ERROR: Could not load annotations-index.json.")
        return

    niagara_types = ann.get("niagara_types", {})
    total_slots = sum(len(e.get("properties", [])) for e in niagara_types.values())

    # Build slot index
    slot_index = _build_slot_index(niagara_types)

    # Find collisions
    collisions = _find_collisions(slot_index, module_filter=module_filter)

    if as_json:
        output = {
            "command": "slot-collision",
            "module_filter": module_filter,
            "total_slots": total_slots,
            "unique_slot_names": len(slot_index),
            "collisions_found": len(collisions),
            "collisions": [],
        }
        for c in collisions:
            output["collisions"].append({
                "slot": c["slot"],
                "modules": c["modules"],
                "refs": [
                    {"module": r["module"], "class": r["class"], "type": r["type"]}
                    for r in c["refs"]
                ],
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Text output
    print("")
    if module_filter:
        print("  SLOT COLLISION REPORT (module filter: {})".format(module_filter))
    else:
        print("  SLOT COLLISION REPORT")
    print("  " + "=" * 68)
    print("")

    print("  Scanning: all modules ({} annotated slots)".format(total_slots))
    print("")

    if not collisions:
        safe_count = sum(
            1 for refs in slot_index.values() if len(refs) == 1
        )
        print("  COLLISIONS FOUND: 0")
        print("")
        print("  SAFE: {} slots without collision".format(safe_count))
        print("")
        return

    print("  COLLISIONS FOUND: {}".format(len(collisions)))
    print("")

    for i, c in enumerate(collisions, 1):
        slot = c["slot"]
        refs = c["refs"]

        print("  {}. Slot \"{}\"".format(i, slot))
        print("       Found in {} module(s):".format(len(c["modules"])))

        # Group by module for cleaner display
        current_module = None
        for ref in refs:
            mod = ref["module"]
            cls = ref["class"]
            typ = ref["type"]

            if mod != current_module:
                print("       {}:".format(mod))
                current_module = mod

            print("         {} ({})".format(cls, typ))

        print("       RISK: potential overwrite in station tree")
        print("")

    safe_count = sum(
        1 for refs in slot_index.values()
        if len(set(r["module"] for r in refs)) == 1
    )
    print("  SAFE: {} slots without cross-module collision".format(safe_count))
    print("")


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cmd_slot_collision(base)
