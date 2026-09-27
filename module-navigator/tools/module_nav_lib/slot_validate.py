"""
Slot pre-flight validation for Module Navigator (Batch 4, Gap #4).

Validates a proposed @NiagaraProperty / action / topic slot against the
real corpus before generating code, catching conflicts and naming issues
that would otherwise surface as build failures.

Commands:
  slot-validate <class>
    --add <name>:<type>[:<defaultValue>]
    [--kind property|action|topic]   Slot kind (default: property)
    [--json]                         Structured JSON output

Reuses existing indexes (no new builders):
  class-index.json, annotations-index.json, inheritance.json
  + deprecated scanner from deprecated.py
"""

import json
import os
import re


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached per process)
# ---------------------------------------------------------------------------

_class_index_cache = None
_annotations_cache = None
_inheritance_cache = None


def _load_json(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print("  ERROR loading {}: {}".format(os.path.basename(path), exc))
        return None


def _load_class_index(base_dir):
    global _class_index_cache
    if _class_index_cache is not None:
        return _class_index_cache
    _class_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "class-index.json"))
    return _class_index_cache


def _load_annotations(base_dir):
    global _annotations_cache
    if _annotations_cache is not None:
        return _annotations_cache
    _annotations_cache = _load_json(
        os.path.join(base_dir, "indexes", "annotations-index.json"))
    return _annotations_cache


def _load_inheritance(base_dir):
    global _inheritance_cache
    if _inheritance_cache is not None:
        return _inheritance_cache
    _inheritance_cache = _load_json(
        os.path.join(base_dir, "indexes", "inheritance.json"))
    return _inheritance_cache


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CAMEL_RE = re.compile(r'^[a-z][a-zA-Z0-9]*$')


def _is_camel_case(name):
    """Check if name is strict camelCase (starts lowercase, no underscores)."""
    return bool(_CAMEL_RE.match(name))


def _similarity(a, b):
    """Simple similarity ratio: 2 * common_chars / total_chars (Dice coeff on bigrams)."""
    if not a or not b:
        return 0.0
    a_lower = a.lower()
    b_lower = b.lower()
    if a_lower == b_lower:
        return 1.0
    a_bigrams = set(a_lower[i:i+2] for i in range(len(a_lower) - 1))
    b_bigrams = set(b_lower[i:i+2] for i in range(len(b_lower) - 1))
    if not a_bigrams or not b_bigrams:
        return 0.0
    common = len(a_bigrams & b_bigrams)
    return 2.0 * common / (len(a_bigrams) + len(b_bigrams))


_DEPRECATED_RE = re.compile(r'@Deprecated\b')


def _check_parents_deprecated(base_dir, chain, ci_classes):
    """Quick targeted scan: check only the parent classes' source for @Deprecated.

    Much faster than the full deprecated scanner (scans ~5 files vs 51K).
    Uses the 'path' field from class-index entries for exact file location.
    """
    ci_data = _load_class_index(base_dir)
    source_root = ""
    if ci_data:
        source_root = ci_data.get("_meta", {}).get("source", "")
    if not source_root:
        return []

    dep_parents = []
    for parent in chain:
        entries = ci_classes.get(parent, [])
        if not entries:
            continue
        # Find the top-level entry (not inner class)
        entry = None
        for e in entries:
            if not e.get("outer_class"):
                entry = e
                break
        if not entry:
            entry = entries[0]

        rel_path = entry.get("path", "")
        if not rel_path:
            continue
        src_path = os.path.join(source_root, rel_path)
        if not os.path.isfile(src_path):
            continue

        try:
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                # Read only first 50 lines (class declaration is near the top)
                for lineno, line in enumerate(f, 1):
                    if lineno > 50:
                        break
                    if _DEPRECATED_RE.search(line):
                        dep_parents.append(parent)
                        break
        except Exception:
            continue

    return dep_parents


_KIND_KEYS = {
    "property": "properties",
    "action": "actions",
    "topic": "topics",
}


def _collect_inherited_slots(class_name, chain, niagara_types, kind_key):
    """Collect all slots of the given kind from the class and its parents.

    Returns dict: slot_name -> {"type": str, "owner": str, "defaultValue": str|None}
    """
    inherited = {}
    for cls in [class_name] + chain:
        entry = niagara_types.get(cls, {})
        slots = entry.get(kind_key, [])
        for slot in slots:
            sname = slot.get("name", "")
            if sname and sname not in inherited:
                inherited[sname] = {
                    "type": slot.get("type", slot.get("parameterType", "?")),
                    "owner": cls,
                    "defaultValue": slot.get("defaultValue"),
                }
    return inherited


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_slot_validate(base_dir, class_name, add_spec, kind="property",
                      as_json=False):
    """Pre-flight validation for a proposed Niagara slot."""
    # --- Parse add_spec ---
    parts = add_spec.split(":")
    if len(parts) < 2:
        print("  ERROR: --add requires format name:type[:defaultValue]")
        print("  Example: --add refreshSeconds:int")
        return
    slot_name = parts[0]
    slot_type = parts[1]
    default_value = parts[2] if len(parts) > 2 else None

    kind_key = _KIND_KEYS.get(kind, "properties")

    # --- Load indexes ---
    ci = _load_class_index(base_dir)
    ann = _load_annotations(base_dir)
    inh = _load_inheritance(base_dir)

    if not ci or not ann or not inh:
        print("  ERROR: Could not load required indexes.")
        return

    classes = ci.get("classes", {})
    niagara_types = ann.get("niagara_types", {})
    property_types = ann.get("property_types", {})
    class_to_chain = inh.get("class_to_chain", {})

    # --- Verify class exists ---
    if class_name not in classes:
        # Try case-insensitive
        found = None
        for k in classes:
            if k.lower() == class_name.lower():
                found = k
                break
        if found:
            class_name = found
        else:
            print("  ERROR: Class '{}' not found in class-index.".format(
                class_name))
            # Fuzzy suggestions
            candidates = [k for k in classes
                          if class_name.lower() in k.lower()]
            if candidates:
                print("  Did you mean: {}".format(
                    ", ".join(sorted(candidates)[:5])))
            return

    # --- Collect inheritance chain ---
    chain = class_to_chain.get(class_name, [])
    all_parents = [class_name] + chain
    inherited_slots = _collect_inherited_slots(
        class_name, chain, niagara_types, kind_key)

    # --- Run checks ---
    checks = []  # list of {"check", "status": "pass"|"warn"|"fail", "detail"}

    # Check 1: camelCase naming
    if _is_camel_case(slot_name):
        checks.append({
            "check": "camelCase naming",
            "status": "pass",
            "detail": "OK",
        })
    else:
        reasons = []
        if slot_name[0].isupper():
            reasons.append("starts with uppercase")
        if "_" in slot_name:
            reasons.append("contains underscore")
        if not re.match(r'^[a-zA-Z]', slot_name):
            reasons.append("does not start with a letter")
        checks.append({
            "check": "camelCase naming",
            "status": "fail",
            "detail": "Name '{}' is not camelCase ({})".format(
                slot_name, "; ".join(reasons) if reasons else "invalid format"),
        })

    # Check 2: type exists in property registry
    if kind == "property":
        if slot_type in property_types:
            usage_count = len(property_types[slot_type])
            checks.append({
                "check": "type exists",
                "status": "pass",
                "detail": "Type '{}' found in property registry "
                          "(used by {} slots)".format(slot_type, usage_count),
            })
        else:
            # Check if it's a primitive or common type that might be aliased
            checks.append({
                "check": "type exists",
                "status": "warn",
                "detail": "Type '{}' not found in property registry "
                          "({} known types)".format(
                              slot_type, len(property_types)),
            })
    else:
        # Actions and topics: parameter types are less constrained
        checks.append({
            "check": "type exists",
            "status": "pass",
            "detail": "{} parameter type '{}' (not validated against "
                      "property registry)".format(kind.title(), slot_type),
        })

    # Check 3: conflict with inherited slots
    if slot_name in inherited_slots:
        conflict = inherited_slots[slot_name]
        detail = "Slot '{}' already exists in {} (type: {})".format(
            slot_name, conflict["owner"], conflict["type"])
        if conflict["defaultValue"]:
            detail += ", default: {}".format(conflict["defaultValue"])
        checks.append({
            "check": "no inherited conflict",
            "status": "fail",
            "detail": detail,
        })
    else:
        checks.append({
            "check": "no inherited conflict",
            "status": "pass",
            "detail": "No conflict (checked {} parents, "
                      "{} total {} slots)".format(
                          len(chain), len(inherited_slots), kind),
        })

    # Check 4: similar slot name suggestion
    similar_hits = []
    for existing_name, info in inherited_slots.items():
        sim = _similarity(slot_name, existing_name)
        if sim >= 0.5 and existing_name != slot_name:
            similar_hits.append((existing_name, info["owner"],
                                 info["type"], sim))
    similar_hits.sort(key=lambda x: -x[3])
    if similar_hits:
        top = similar_hits[0]
        checks.append({
            "check": "similar slot check",
            "status": "warn",
            "detail": "Similar slot '{}' in {} (type: {}, "
                      "similarity: {:.0%})".format(
                          top[0], top[1], top[2], top[3]),
        })

    # Check 5: deprecated parent warning (targeted scan of parent sources only)
    dep_parents = _check_parents_deprecated(base_dir, chain, classes)
    if dep_parents:
        checks.append({
            "check": "deprecated parent",
            "status": "warn",
            "detail": "@Deprecated parent(s): {}".format(
                ", ".join(dep_parents)),
        })

    # --- Determine overall result ---
    has_fail = any(c["status"] == "fail" for c in checks)
    warn_count = sum(1 for c in checks if c["status"] == "warn")

    if has_fail:
        result = "FAIL"
    elif warn_count > 0:
        result = "PASS with {} warning{}".format(
            warn_count, "s" if warn_count != 1 else "")
    else:
        result = "PASS"

    # --- Output ---
    if as_json:
        out = {
            "class": class_name,
            "slot_name": slot_name,
            "slot_type": slot_type,
            "default_value": default_value,
            "kind": kind,
            "parents_checked": len(chain),
            "inherited_slots_count": len(inherited_slots),
            "checks": checks,
            "result": result,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    # Text output
    dv_str = ":{}".format(default_value) if default_value else ""
    print("")
    print("  VALIDATING: {}:{}{} ({}) on {}".format(
        slot_name, slot_type, dv_str, kind, class_name))
    print("  " + "=" * 70)
    print("")

    status_sym = {"pass": "[OK]", "warn": "[!]", "fail": "[X]"}
    for c in checks:
        sym = status_sym.get(c["status"], "?")
        print("  {} {}".format(sym, c["detail"]))
    print("")

    # Inherited slots summary
    if inherited_slots:
        print("  INHERITED {} ({} parents):".format(
            kind.upper() + "S" if kind != "property" else "PROPERTIES",
            len(chain)))
        # Group by owner
        by_owner = {}
        for sname, info in inherited_slots.items():
            owner = info["owner"]
            if owner not in by_owner:
                by_owner[owner] = []
            by_owner[owner].append(sname)
        for cls in all_parents:
            if cls in by_owner:
                names = sorted(by_owner[cls])
                if len(names) > 5:
                    display = ", ".join(names[:5]) + ", ... (+{})".format(
                        len(names) - 5)
                else:
                    display = ", ".join(names)
                print("    {:30s}: {}".format(cls, display))
            else:
                print("    {:30s}: (no annotated {} slots)".format(
                    cls, kind))
    print("")
    print("  RESULT: {}".format(result))
    print("")
