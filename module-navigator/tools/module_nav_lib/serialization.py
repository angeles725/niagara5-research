"""
Serialization Audit for Module Navigator (Phase 26).

Commands:
  serial <class>                     Serialization info for a class
  serial-audit [--module mod] [-n N] Audit: Serializable without UID, custom read/write
  serial-conflicts [-n N]            Classes with same serialVersionUID (collision)

Checks: serialVersionUID presence, readObject/writeObject/readResolve overrides,
Externalizable implementations. Critical for JAR patching — if you change a field
in a Serializable class without updating the UID, the station won't start.

No builder needed — uses field-index + inheritance + method-index + class-index on-demand.
"""

import os
import re
from collections import defaultdict


# ---------------------------------------------------------------------------
# Index loading (reuse existing loaders, on-demand cached)
# ---------------------------------------------------------------------------

def _load_field_index(base_dir):
    """Load field-index.json via fields module (cached)."""
    from module_nav_lib.fields import load_field_index
    return load_field_index(base_dir)


def _load_inheritance(base_dir):
    """Load inheritance.json via hierarchy module (cached)."""
    from module_nav_lib.hierarchy import load_inheritance
    return load_inheritance(base_dir)


def _load_method_index(base_dir):
    """Load method-index.json via methods module (cached)."""
    from module_nav_lib.methods import load_method_index
    return load_method_index(base_dir)


def _load_class_index(base_dir):
    """Load class-index.json (on-demand, cached)."""
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


# ---------------------------------------------------------------------------
# Serialization data building (cached)
# ---------------------------------------------------------------------------

_serial_cache = {}

# Methods that indicate custom serialization logic
SERIAL_METHODS = {
    "readObject", "writeObject", "readResolve", "writeReplace",
    "readExternal", "writeExternal", "readObjectNoData",
}

# Regex patterns for source-level serialization hints
SERIAL_SOURCE_PATTERNS = {
    "ObjectInputStream": re.compile(r'ObjectInputStream'),
    "ObjectOutputStream": re.compile(r'ObjectOutputStream'),
    "transient field": re.compile(r'\btransient\b'),
    "defaultReadObject": re.compile(r'defaultReadObject\s*\('),
    "defaultWriteObject": re.compile(r'defaultWriteObject\s*\('),
}


def _build_serial_map(base_dir, module_filter=None):
    """Build serialization analysis map.

    Returns dict: class_name -> {
        module, is_serializable, is_externalizable,
        has_uid, uid_value, uid_count (number of UID fields in chain),
        serial_methods: [method names found],
        transient_fields: [field names],
        all_fields_count, source_path
    }
    """
    cache_key = module_filter or "__all__"
    if cache_key in _serial_cache:
        return _serial_cache[cache_key]

    fi = _load_field_index(base_dir)
    inh = _load_inheritance(base_dir)
    mi = _load_method_index(base_dir)
    ci_data = _load_class_index(base_dir)

    if not fi or not inh or not mi or not ci_data:
        return {}

    fields_idx = fi.get("fields", {})
    class_fields = fi.get("class_fields", {})
    c2c = inh.get("class_to_chain", {})
    class_methods = mi.get("class_methods", {})
    ci_classes = ci_data.get("classes", {})
    source_root = ci_data.get("_meta", {}).get("source", "")

    # Build module lookup
    class_module = {}
    class_source = {}
    for cname, entries in ci_classes.items():
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            class_module[cname] = top[0].get("module", "?")
            rel_path = top[0].get("path", "")
            if rel_path and source_root:
                class_source[cname] = os.path.join(source_root, rel_path)
        elif entries:
            class_module[cname] = entries[0].get("module", "?")

    # Find all Serializable/Externalizable classes via inheritance chains
    serial_classes = set()
    external_classes = set()
    for cname, chain in c2c.items():
        for ancestor in chain:
            if ancestor == "Serializable" or ancestor == "java.io.Serializable":
                serial_classes.add(cname)
            if ancestor == "Externalizable" or ancestor == "java.io.Externalizable":
                external_classes.add(cname)
                serial_classes.add(cname)  # Externalizable extends Serializable

    # Get serialVersionUID entries from field-index
    uid_entries = fields_idx.get("serialVersionUID", [])
    uid_by_class = {}
    for entry in uid_entries:
        cname = entry.get("class", "")
        uid_by_class[cname] = entry.get("value", "?")

    # Build serial map
    serial_map = {}
    for cname in serial_classes:
        mod = class_module.get(cname, "?")
        if module_filter and mod != module_filter:
            continue

        # Check for serialVersionUID
        has_uid = cname in uid_by_class
        uid_value = uid_by_class.get(cname, None)

        # Check for custom serialization methods
        methods = set(class_methods.get(cname, []))
        serial_methods = sorted(methods & SERIAL_METHODS)

        # Check for transient fields
        transient_fields = []
        field_names = class_fields.get(cname, [])
        for fname in field_names:
            if fname in fields_idx:
                for entry in fields_idx[fname]:
                    if entry["class"] == cname:
                        if "transient" in entry.get("modifiers", []):
                            transient_fields.append(fname)
                        break

        serial_map[cname] = {
            "module": mod,
            "is_serializable": True,
            "is_externalizable": cname in external_classes,
            "has_uid": has_uid,
            "uid_value": uid_value,
            "serial_methods": serial_methods,
            "transient_fields": transient_fields,
            "all_fields_count": len(field_names),
            "source_path": class_source.get(cname, ""),
        }

    _serial_cache[cache_key] = serial_map
    return serial_map


# ---------------------------------------------------------------------------
# serial <class> — serialization info for a class
# ---------------------------------------------------------------------------

def cmd_serial(base_dir, class_name):
    """Show serialization details for a specific class."""
    serial_map = _build_serial_map(base_dir)
    if not serial_map:
        print("  ERROR: Could not build serialization map (indexes missing).")
        return

    # Case-insensitive lookup
    if class_name not in serial_map:
        found = None
        lower = class_name.lower()
        for k in serial_map:
            if k.lower() == lower:
                found = k
                break
        if found:
            class_name = found
        else:
            # Check if class exists but is not Serializable
            ci_data = _load_class_index(base_dir)
            if ci_data:
                ci_classes = ci_data.get("classes", {})
                exists = class_name in ci_classes
                if not exists:
                    for k in ci_classes:
                        if k.lower() == lower:
                            exists = True
                            class_name = k
                            break
                if exists:
                    print("")
                    print("  Class '{}' exists but does NOT implement Serializable.".format(
                        class_name))
                    # Show inheritance chain
                    inh = _load_inheritance(base_dir)
                    if inh:
                        chain = inh.get("class_to_chain", {}).get(class_name, [])
                        if chain:
                            print("  Inheritance: {} -> {}".format(
                                class_name, " -> ".join(chain[:5])))
                    print("")
                    return

            print("")
            print("  Class '{}' not found.".format(class_name))
            partial = [c for c in serial_map if class_name.lower() in c.lower()]
            if partial:
                shown = sorted(partial)[:10]
                print("  Serializable partial matches: {}".format(", ".join(shown)))
            print("")
            return

    info = serial_map[class_name]

    print("")
    print("  SERIALIZATION: {}".format(class_name))
    print("  " + "=" * 65)
    print("  Module:          {}".format(info["module"]))
    print("  Serializable:    Yes")
    print("  Externalizable:  {}".format("Yes" if info["is_externalizable"] else "No"))
    print("")

    # serialVersionUID
    if info["has_uid"]:
        print("  serialVersionUID: {}".format(info["uid_value"]))
    else:
        print("  serialVersionUID: *** MISSING ***")
        print("    WARNING: JVM will auto-compute UID based on class structure.")
        print("    Any field/method change may break deserialization!")
    print("")

    # Custom serialization methods
    if info["serial_methods"]:
        print("  CUSTOM SERIALIZATION METHODS ({}):" .format(len(info["serial_methods"])))
        for m in info["serial_methods"]:
            desc = _method_description(m)
            print("    {} — {}".format(m, desc))
    else:
        print("  Custom serialization methods: none (uses default)")
    print("")

    # Transient fields
    if info["transient_fields"]:
        print("  TRANSIENT FIELDS ({} of {} total):".format(
            len(info["transient_fields"]), info["all_fields_count"]))
        for f in info["transient_fields"]:
            print("    {}".format(f))
    else:
        print("  Transient fields: none ({} total fields)".format(
            info["all_fields_count"]))
    print("")

    # Inheritance chain for serialization context
    inh = _load_inheritance(base_dir)
    if inh:
        chain = inh.get("class_to_chain", {}).get(class_name, [])
        if chain:
            serial_ancestors = []
            for ancestor in chain:
                if ancestor in serial_map:
                    ancestor_info = serial_map[ancestor]
                    uid_str = "UID={}".format(ancestor_info["uid_value"]) if ancestor_info["has_uid"] else "NO UID"
                    serial_ancestors.append("{} ({})".format(ancestor, uid_str))
            if serial_ancestors:
                print("  SERIALIZABLE ANCESTORS:")
                for sa in serial_ancestors:
                    print("    {}".format(sa))
                print("")

    # Source-level analysis
    src_path = info.get("source_path", "")
    if src_path and os.path.isfile(src_path):
        source_hits = _scan_source_serial(src_path)
        if source_hits:
            print("  SOURCE PATTERNS:")
            for pattern_name, count in sorted(source_hits.items()):
                print("    {:25s}  {:>3} occurrences".format(pattern_name, count))
            print("")

    # Risk assessment
    risk = _assess_serial_risk(info)
    print("  PATCH RISK: {}".format(risk))
    if risk == "HIGH":
        print("    Modifying fields in this class requires updating serialVersionUID!")
    elif risk == "MEDIUM":
        print("    Has custom serialization — changes need careful review.")
    else:
        print("    Standard serialization — field changes still need UID check.")
    print("")


def _method_description(method_name):
    """Human-readable description of serialization method."""
    descs = {
        "readObject": "Custom deserialization logic",
        "writeObject": "Custom serialization logic",
        "readResolve": "Substitutes object after deserialization (singleton pattern)",
        "writeReplace": "Substitutes object before serialization",
        "readExternal": "Externalizable: custom deserialization",
        "writeExternal": "Externalizable: custom serialization",
        "readObjectNoData": "Called when superclass not in serialized stream",
    }
    return descs.get(method_name, "")


def _scan_source_serial(src_path):
    """Scan source file for serialization-related patterns."""
    hits = {}
    try:
        with open(src_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except Exception:
        return hits

    for pname, pat in SERIAL_SOURCE_PATTERNS.items():
        count = len(pat.findall(source))
        if count > 0:
            hits[pname] = count

    return hits


def _assess_serial_risk(info):
    """Assess risk of modifying a serializable class.

    HIGH: No UID + has fields (any change can break)
    MEDIUM: Has UID + custom methods (changes need review)
    LOW: Has UID + default serialization (safer to patch)
    """
    if not info["has_uid"] and info["all_fields_count"] > 0:
        return "HIGH"
    if info["serial_methods"]:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# serial-audit [--module mod] — audit serializable classes
# ---------------------------------------------------------------------------

def cmd_serial_audit(base_dir, module_filter=None, limit=50):
    """Audit Serializable classes: missing UIDs, custom read/write, risks."""
    print("")
    print("  Building serialization map...")

    serial_map = _build_serial_map(base_dir, module_filter=module_filter)
    if not serial_map:
        if module_filter:
            print("  No Serializable classes found in module '{}'.".format(module_filter))
        else:
            print("  ERROR: Could not build serialization map (indexes missing).")
        return

    scope = module_filter if module_filter else "ALL MODULES"

    # Statistics
    total = len(serial_map)
    missing_uid = [c for c, info in serial_map.items() if not info["has_uid"]]
    has_custom = [c for c, info in serial_map.items() if info["serial_methods"]]
    externalizable = [c for c, info in serial_map.items() if info["is_externalizable"]]
    has_transient = [c for c, info in serial_map.items() if info["transient_fields"]]

    risk_high = [c for c, info in serial_map.items()
                 if _assess_serial_risk(info) == "HIGH"]
    risk_medium = [c for c, info in serial_map.items()
                   if _assess_serial_risk(info) == "MEDIUM"]
    risk_low = [c for c, info in serial_map.items()
                if _assess_serial_risk(info) == "LOW"]

    print("")
    print("  SERIALIZATION AUDIT: {}".format(scope))
    print("  " + "=" * 70)
    print("  Serializable classes: {:>7,}".format(total))
    print("  With serialVersionUID: {:>6,}  ({:.1%})".format(
        total - len(missing_uid), (total - len(missing_uid)) / total if total else 0))
    print("  Missing UID:          {:>6,}  ({:.1%})".format(
        len(missing_uid), len(missing_uid) / total if total else 0))
    print("  Custom read/write:    {:>6,}".format(len(has_custom)))
    print("  Externalizable:       {:>6,}".format(len(externalizable)))
    print("  With transient fields:{:>6,}".format(len(has_transient)))
    print("")
    print("  RISK DISTRIBUTION:")
    print("    HIGH   (no UID + fields):  {:>6,}".format(len(risk_high)))
    print("    MEDIUM (custom methods):   {:>6,}".format(len(risk_medium)))
    print("    LOW    (UID + default):    {:>6,}".format(len(risk_low)))
    print("")

    # Missing UID classes (most important for patching)
    if missing_uid:
        # Sort by field count descending (more fields = more risk)
        missing_ranked = sorted(
            missing_uid,
            key=lambda c: serial_map[c]["all_fields_count"],
            reverse=True
        )[:limit]

        print("  CLASSES MISSING serialVersionUID ({:,} total, top {}):".format(
            len(missing_uid), min(limit, len(missing_uid))))
        print("  {:35s}  {:25s}  {:>5s}  {:>5s}  {:s}".format(
            "CLASS", "MODULE", "FLDS", "TRANS", "METHODS"))
        print("  " + "-" * 90)

        for cname in missing_ranked:
            info = serial_map[cname]
            methods_str = ", ".join(info["serial_methods"]) if info["serial_methods"] else "-"
            print("  {:35s}  {:25s}  {:>5d}  {:>5d}  {}".format(
                cname[:35],
                info["module"][:25],
                info["all_fields_count"],
                len(info["transient_fields"]),
                methods_str,
            ))

        if len(missing_uid) > limit:
            print("")
            print("  ... and {:,} more (use -n {} to see all)".format(
                len(missing_uid) - limit, len(missing_uid)))
        print("")

    # Classes with custom serialization methods
    if has_custom:
        custom_ranked = sorted(
            has_custom,
            key=lambda c: len(serial_map[c]["serial_methods"]),
            reverse=True
        )[:limit]

        print("  CLASSES WITH CUSTOM SERIALIZATION ({:,}):".format(len(has_custom)))
        print("  {:35s}  {:25s}  {:>5s}  {:s}".format(
            "CLASS", "MODULE", "UID?", "METHODS"))
        print("  " + "-" * 85)

        shown = 0
        for cname in custom_ranked:
            if shown >= limit:
                break
            info = serial_map[cname]
            uid_str = "Yes" if info["has_uid"] else "NO"
            methods_str = ", ".join(info["serial_methods"])
            print("  {:35s}  {:25s}  {:>5s}  {}".format(
                cname[:35],
                info["module"][:25],
                uid_str,
                methods_str,
            ))
            shown += 1

        if len(has_custom) > limit:
            print("")
            print("  ... and {:,} more".format(len(has_custom) - limit))
        print("")

    # Module summary
    if not module_filter:
        mod_stats = defaultdict(lambda: {"total": 0, "missing": 0, "custom": 0})
        for cname, info in serial_map.items():
            mod = info["module"]
            mod_stats[mod]["total"] += 1
            if not info["has_uid"]:
                mod_stats[mod]["missing"] += 1
            if info["serial_methods"]:
                mod_stats[mod]["custom"] += 1

        # Sort by missing UID count
        ranked_mods = sorted(mod_stats.items(), key=lambda x: -x[1]["missing"])[:20]

        print("  TOP MODULES BY MISSING UID:")
        print("  {:30s}  {:>6s}  {:>8s}  {:>6s}".format(
            "MODULE", "TOTAL", "NO UID", "CUSTOM"))
        print("  " + "-" * 55)
        for mod, stats in ranked_mods:
            if stats["missing"] > 0:
                print("  {:30s}  {:>6,}  {:>8,}  {:>6,}".format(
                    mod[:30], stats["total"], stats["missing"], stats["custom"]))
        print("")

    print("")


# ---------------------------------------------------------------------------
# serial-conflicts — classes with same serialVersionUID value
# ---------------------------------------------------------------------------

def cmd_serial_conflicts(base_dir, limit=30):
    """Find classes that share the same serialVersionUID value (collisions)."""
    print("")
    print("  Building serialization map...")

    serial_map = _build_serial_map(base_dir)
    if not serial_map:
        print("  ERROR: Could not build serialization map (indexes missing).")
        return

    # Group classes by UID value
    uid_groups = defaultdict(list)
    for cname, info in serial_map.items():
        if info["has_uid"] and info["uid_value"] is not None:
            uid_val = str(info["uid_value"]).strip()
            # Skip trivial UIDs
            if uid_val in ("?", ""):
                continue
            uid_groups[uid_val].append(cname)

    # Find conflicts (more than 1 class with same UID)
    conflicts = {uid: classes for uid, classes in uid_groups.items()
                 if len(classes) > 1}

    # Sort by group size descending
    sorted_conflicts = sorted(conflicts.items(), key=lambda x: -len(x[1]))

    # Statistics
    total_with_uid = sum(1 for info in serial_map.values() if info["has_uid"])
    unique_uids = len(uid_groups)

    print("")
    print("  SERIALVERSIONUID CONFLICTS")
    print("  " + "=" * 70)
    print("  Serializable classes:    {:>7,}".format(len(serial_map)))
    print("  With explicit UID:       {:>7,}".format(total_with_uid))
    print("  Unique UID values:       {:>7,}".format(unique_uids))
    print("  UIDs shared by 2+ classes: {:>5,}".format(len(conflicts)))
    print("  Classes in conflict:     {:>7,}".format(
        sum(len(c) for c in conflicts.values())))
    print("")

    if not sorted_conflicts:
        print("  No UID conflicts found — all serialVersionUID values are unique.")
        print("")
        return

    # Common/trivial UIDs
    TRIVIAL_UIDS = {"1L", "1", "0L", "0", "-1L", "-1", "2L", "2"}

    shown = 0
    trivial_count = 0

    for uid_val, classes in sorted_conflicts:
        if shown >= limit:
            break

        is_trivial = uid_val in TRIVIAL_UIDS
        if is_trivial:
            trivial_count += 1

        tag = " [TRIVIAL]" if is_trivial else ""
        print("  UID = {}{} ({} classes):".format(uid_val, tag, len(classes)))

        # Show classes, grouped by module
        by_module = defaultdict(list)
        for cname in classes:
            mod = serial_map[cname]["module"]
            by_module[mod].append(cname)

        for mod in sorted(by_module.keys()):
            for cname in sorted(by_module[mod]):
                print("    {:35s}  {}".format(cname[:35], mod))

        print("")
        shown += 1

    if len(sorted_conflicts) > limit:
        print("  ... and {:,} more conflict groups (use -n {} to see all)".format(
            len(sorted_conflicts) - limit, len(sorted_conflicts)))
        print("")

    if trivial_count > 0:
        print("  NOTE: {} groups use trivial UIDs (0, 1, -1, 2).".format(trivial_count))
        print("  These are common defaults — not necessarily real conflicts,")
        print("  but they indicate classes where UID was not carefully assigned.")
        print("")

    print("")
