"""
ORD Validation for Module Navigator (Batch 5, Gap #9).

Detects ORDs (Object Reference Descriptors) that reference non-existent
paths in the station tree. ORD.resolve() returns null if the path doesn't
exist, causing NPE when code does service.resolve().get() without null-check.

Commands:
  ord-validate <module>
    [--json]              # structured JSON output

Reuses existing indexes (no new builders):
  annotations-index.json, class-index.json, ords.py (ORD extraction)

Classification:
  VALID         - station:|slot:/Path where slot name exists in annotations-index
  RUNTIME-ONLY  - alarm:|uuid:..., history:|uuid:... (not statically validatable)
  DANGLING      - station:|slot:/Path where slot name NOT in annotations-index
"""

import json
import os
import re

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
# Known Niagara ORD schemes
# ---------------------------------------------------------------------------

# Schemes that can be validated statically (station tree paths)
_VALIDATABLE_SCHEMES = {"station", "slot", "service", "baja", "local", "history"}

# Schemes that are runtime-only (UUID-based, not resolvable statically)
_RUNTIME_ONLY_SCHEMES = {"alarm", "uuid", "spy", "view", "fox", "ip", "file", "ord", "module"}


def _classify_scheme(val):
    """Extract the ORD scheme prefix from a string value.

    Returns (scheme, body) or (None, None) if not an ORD.
    """
    # Regex for extracting scheme from an ORD string
    scheme_re = re.compile(r'^([a-zA-Z][a-zA-Z0-9+.-]*):')

    sm = scheme_re.match(val)
    if sm:
        return sm.group(1).lower(), val
    return None, None


def _extract_slot_name(ord_value):
    """Extract the slot name (last path component) from an ORD value.

    For station:|slot:/Services/AlarmService/alarmDbConfig
    Returns: alarmDbConfig

    For station:|slot:/Services/AlarmService
    Returns: AlarmService
    """
    # Remove scheme prefix (e.g., "station:" from "station:|slot:/Path")
    # Handle two formats:
    # 1. station:|slot:/Path -> split on first |, take second part
    # 2. baja:RelTime -> split on first :, take second part
    if "|" in ord_value:
        body = ord_value.split("|", 1)[1]
    elif ":" in ord_value:
        body = ord_value.split(":", 1)[1]
    else:
        body = ord_value

    # Handle station:|slot:/... or slot:/... format
    if body.startswith("slot:/"):
        path = body[6:]  # Remove "slot:/" prefix
    elif body.startswith("/"):
        path = body[1:]  # Remove leading /
    else:
        path = body

    # For malformed paths like "|bql:select..." or empty, return None
    if not path or path.startswith("|") or path.startswith("bql:"):
        return None

    # For paths containing ":" (like "h:", "slot:"), these are malformed
    if ":" in path:
        return None

    # Check if this is a component path (no slot accessor) or a slot reference
    # Component path: station:|slot:/ElectronicSignature -> just a component
    # Slot reference: station:|slot:/Services/AlarmService/alarmDbConfig -> slot on component
    if "/" not in path:
        # No "/" means this is just a component path (e.g., ElectronicSignature)
        # Mark as COMPONENT (not a slot) - these are valid by definition
        return ("COMPONENT", path)

    # Has "/" - this is a slot reference
    # e.g., Services/AlarmService/alarmDbConfig
    # The slot is the LAST component
    components = path.split("/")
    return ("SLOT", components[-1])


# ---------------------------------------------------------------------------
# Build known slots and components indexes
# ---------------------------------------------------------------------------

def _build_known_slots(base_dir):
    """Build a set of all known slot names from annotations-index.

    Returns: set of slot names (property names from @NiagaraProperty)
    """
    ann = _load_annotations(base_dir)
    if not ann:
        return set()

    known_slots = set()
    niagara_types = ann.get("niagara_types", {})

    for class_name, entry in niagara_types.items():
        for prop in entry.get("properties", []):
            name = prop.get("name", "")
            if name:
                known_slots.add(name)

    return known_slots


def _build_known_components(base_dir):
    """Build a set of all known component types from class-index.

    Returns: set of class names that could be station tree components
    """
    ci = _load_class_index(base_dir)
    if not ci:
        return set()

    known_components = set()
    classes = ci.get("classes", {})

    for class_name in classes.keys():
        known_components.add(class_name)

    return known_components


def _build_class_for_slot(base_dir):
    """Build mapping: slot_name -> [(class, module, type), ...]

    Returns: dict slot_name -> list of {class, module, type}
    """
    ann = _load_annotations(base_dir)
    if not ann:
        return {}

    slot_to_classes = {}
    niagara_types = ann.get("niagara_types", {})

    for class_name, entry in niagara_types.items():
        module = entry.get("module", "?")
        for prop in entry.get("properties", []):
            name = prop.get("name", "")
            if not name:
                continue
            if name not in slot_to_classes:
                slot_to_classes[name] = []
            slot_to_classes[name].append({
                "class": class_name,
                "module": module,
                "type": prop.get("type", "?"),
            })

    return slot_to_classes


# ---------------------------------------------------------------------------
# ORD extraction from string-index.db
# ---------------------------------------------------------------------------

import sqlite3

_string_db_conn = None


def _get_string_db(base_dir):
    """Get or open string-index.db connection (lazy singleton)."""
    global _string_db_conn
    if _string_db_conn is not None:
        return _string_db_conn

    db_path = os.path.join(base_dir, "indexes", "string-index.db")
    if not os.path.isfile(db_path):
        return None

    _string_db_conn = sqlite3.connect(db_path)
    _string_db_conn.execute("PRAGMA query_only=ON")
    _string_db_conn.execute("PRAGMA cache_size=-16000")
    return _string_db_conn


# Regex for BOrd.make("...") patterns
_BORD_MAKE_RE = re.compile(r'BOrd\.make\(["\']([^"\']+)["\']')

# Known Niagara schemes
_NIAGARA_SCHEMES = [
    "station:", "slot:", "history:", "local:", "fox:", "ip:",
    "module:", "spy:", "view:", "alarm:", "baja:", "file:",
    "service:", "ord:",
]


def _query_module_ords(base_dir, module_filter):
    """Query string-index.db for ORDs in a specific module.

    Returns list of dicts: {scheme, value, class_name, module, line}
    """
    conn = _get_string_db(base_dir)
    if not conn:
        return []

    # Build WHERE clause for ORD-like strings
    conditions = []
    for scheme in _NIAGARA_SCHEMES:
        conditions.append("s.string_val LIKE '{}%'".format(scheme))
    conditions.append("s.string_val LIKE '%BOrd.make%'")
    conditions.append("s.string_val LIKE '%new BOrd%'")

    where = " OR ".join(conditions)

    sql = """
        SELECT s.string_val, f.class_name, f.module, s.line_no
        FROM strings s JOIN files f ON s.file_id = f.id
        WHERE ({})
        AND f.module = ?
    """.format(where)

    cur = conn.cursor()
    cur.execute(sql, (module_filter,))

    results = []
    for row in cur.fetchall():
        val, cls, mod, line = row
        scheme, body = _classify_scheme(val)
        if scheme:
            results.append({
                "scheme": scheme,
                "value": body if body else val,
                "class_name": cls,
                "module": mod,
                "line": line,
            })

    return results


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------

def _validate_ord(ord_entry, known_slots, known_components, slot_to_classes):
    """Classify a single ORD as VALID, RUNTIME-ONLY, or DANGLING.

    Args:
        ord_entry: dict with scheme, value, class_name, module, line
        known_slots: set of all known slot names
        known_components: set of all known component types
        slot_to_classes: dict slot_name -> list of {class, module, type}

    Returns:
        dict with validated entry plus: status, slot_name, resolved_type, ref_type
    """
    scheme = ord_entry["scheme"]
    value = ord_entry["value"]

    # RUNTIME-ONLY schemes cannot be validated statically
    if scheme in _RUNTIME_ONLY_SCHEMES:
        return {
            **ord_entry,
            "status": "RUNTIME-ONLY",
            "slot_name": None,
            "resolved_type": None,
            "ref_type": None,
        }

    # For validatable schemes, check if slot name exists
    ref_info = _extract_slot_name(value)

    # Handle malformed ORDs (ref_info is None or ("SLOT", None))
    if ref_info is None or ref_info[1] is None:
        return {
            **ord_entry,
            "status": "DANGLING",
            "slot_name": None,
            "resolved_type": None,
            "ref_type": "MALFORMED",
        }

    ref_type, extracted_name = ref_info

    # Only station:|slot:/... ORDs can be VALID (checked against known slots/components)
    # All other validatable schemes (baja:, local:, service:, etc.) are RUNTIME-ONLY
    if scheme != "station":
        return {
            **ord_entry,
            "status": "RUNTIME-ONLY",
            "slot_name": extracted_name,
            "resolved_type": None,
            "ref_type": ref_type,
        }

    # scheme == "station"
    if ref_type == "SLOT":
        # Slot reference: check if slot exists in known_slots
        slot_name = extracted_name
        if slot_name in known_slots:
            # Find the type for this slot (prefer same module)
            resolved_type = None
            refs = slot_to_classes.get(slot_name, [])
            for ref in refs:
                if ref["module"] == ord_entry["module"]:
                    resolved_type = ref["type"]
                    break
            if not resolved_type and refs:
                resolved_type = refs[0]["type"]

            return {
                **ord_entry,
                "status": "VALID",
                "slot_name": slot_name,
                "resolved_type": resolved_type,
                "ref_type": "SLOT",
            }
        else:
            return {
                **ord_entry,
                "status": "DANGLING",
                "slot_name": slot_name,
                "resolved_type": None,
                "ref_type": "SLOT",
            }
    else:
        # ref_type == "COMPONENT" - component path reference
        # Check if it's a known component type
        if extracted_name in known_components:
            return {
                **ord_entry,
                "status": "VALID",
                "slot_name": extracted_name,
                "resolved_type": extracted_name,
                "ref_type": "COMPONENT",
            }
        else:
            return {
                **ord_entry,
                "status": "DANGLING",
                "slot_name": extracted_name,
                "resolved_type": None,
                "ref_type": "COMPONENT",
            }


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_ord_validate(base_dir, module_name, as_json=False):
    """Validate ORDs for a specific module."""
    # Load indexes
    ann = _load_annotations(base_dir)
    if not ann:
        print("  ERROR: Could not load annotations-index.json.")
        return

    # Build known slots and components indexes
    known_slots = _build_known_slots(base_dir)
    known_components = _build_known_components(base_dir)
    slot_to_classes = _build_class_for_slot(base_dir)

    # Get ORDs for the module
    ords = _query_module_ords(base_dir, module_name)

    if not ords:
        print("")
        print("  ORD VALIDATION: {}".format(module_name))
        print("  " + "=" * 68)
        print("")
        print("  No ORDs found for module '{}'.".format(module_name))
        print("")
        return

    # Validate each ORD
    validated = [_validate_ord(o, known_slots, known_components, slot_to_classes) for o in ords]

    # Group by status
    valid = [v for v in validated if v["status"] == "VALID"]
    runtime_only = [v for v in validated if v["status"] == "RUNTIME-ONLY"]
    dangling = [v for v in validated if v["status"] == "DANGLING"]

    if as_json:
        output = {
            "command": "ord-validate",
            "module": module_name,
            "total_ords": len(ords),
            "valid": len(valid),
            "runtime_only": len(runtime_only),
            "dangling": len(dangling),
            "classifications": {
                "VALID": [
                    {
                        "ord": v["value"],
                        "class": v["class_name"],
                        "slot": v["slot_name"],
                        "type": v["resolved_type"],
                    }
                    for v in valid
                ],
                "RUNTIME-ONLY": [
                    {
                        "ord": v["value"],
                        "class": v["class_name"],
                        "scheme": v["scheme"],
                    }
                    for v in runtime_only
                ],
                "DANGLING": [
                    {
                        "ord": v["value"],
                        "class": v["class_name"],
                        "slot": v["slot_name"],
                    }
                    for v in dangling
                ],
            },
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Text output
    print("")
    print("  ORD VALIDATION: {}".format(module_name))
    print("  " + "=" * 68)
    print("")
    print("  Total ORDs found: {}".format(len(ords)))
    print("")

    # VALID section
    print("  VALID (static analysis):")
    if valid:
        for v in valid[:15]:
            resolved = "({})".format(v["resolved_type"]) if v["resolved_type"] else ""
            print("    {} → {} {}".format(v["value"], v["class_name"], resolved))
        if len(valid) > 15:
            print("    ... and {} more".format(len(valid) - 15))
    else:
        print("    (none)")
    print("")

    # RUNTIME-ONLY section
    print("  RUNTIME-ONLY (cannot validate statically):")
    if runtime_only:
        for v in runtime_only[:10]:
            print("    {} → {}".format(v["value"], v["scheme"]))
        if len(runtime_only) > 10:
            print("    ... and {} more".format(len(runtime_only) - 10))
    else:
        print("    (none)")
    print("")

    # DANGLING section
    print("  DANGLING (slot name not found in annotations-index):")
    if dangling:
        for v in dangling[:15]:
            print("    {} → {} [MISSING]".format(v["value"], v["slot_name"]))
        if len(dangling) > 15:
            print("    ... and {} more".format(len(dangling) - 15))
    else:
        print("    (none)")
    print("")

    # Summary
    print("  SUMMARY:")
    print("    Valid: {:>5}  |  Runtime-only: {:>5}  |  Dangling: {:>5}".format(
        len(valid), len(runtime_only), len(dangling)))
    if dangling:
        print("    → RISK: {} dangling references CAN cause NPE if accessed".format(
            len(dangling)))
    print("")


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ord_validate.py <module> [--json]")
        sys.exit(1)

    module = sys.argv[1]
    as_json = "--json" in sys.argv

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cmd_ord_validate(base, module, as_json=as_json)