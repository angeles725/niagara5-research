"""
ORD Resolution Graph commands for Module Navigator (Phase 34).

Parses BOrd.make("..."), new BOrd("..."), and ORD scheme literals from
string-index.db. Extracts scheme prefixes (station:, slot:, history:,
local:, fox:, ip:, module:, spy:, view:, alarm:, baja:, file:, service:),
categorizes by type, module, and usage class.

Uses string-index.db + class-index.json on-demand. No builder.

Commands:
  ords [--module mod] [--scheme s] [-n N]   List ORDs grouped by scheme
  ord-usage <scheme>  [--module mod] [-n N]  Classes that use a specific scheme
  ord-flow <class>                           ORDs created/resolved by a class
"""

import json
import os
import re
import sqlite3


# ---------------------------------------------------------------------------
# Known Niagara ORD schemes
# ---------------------------------------------------------------------------

_NIAGARA_SCHEMES = [
    "station:", "slot:", "history:", "local:", "fox:", "ip:",
    "module:", "spy:", "view:", "alarm:", "baja:", "file:",
    "service:", "ord:",
]


# ---------------------------------------------------------------------------
# Index loaders (lazy, cached)
# ---------------------------------------------------------------------------

_class_index_cache = None
_string_db_conn = None


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


def _get_string_db(base_dir):
    """Get or open string-index.db connection (lazy singleton)."""
    global _string_db_conn
    if _string_db_conn is not None:
        return _string_db_conn

    db_path = os.path.join(base_dir, "indexes", "string-index.db")
    if not os.path.isfile(db_path):
        print("ERROR: string-index.db not found.")
        print("Run: python tools/build_string_index.py")
        return None

    _string_db_conn = sqlite3.connect(db_path)
    _string_db_conn.execute("PRAGMA query_only=ON")
    _string_db_conn.execute("PRAGMA cache_size=-16000")
    return _string_db_conn


# ---------------------------------------------------------------------------
# ORD extraction helpers
# ---------------------------------------------------------------------------

# Regex for BOrd.make("...") patterns stored as string literals
_BORD_MAKE_RE = re.compile(r'BOrd\.make\(["\']([^"\']+)["\']')

# Regex for extracting scheme from an ORD string
_SCHEME_RE = re.compile(r'^([a-zA-Z][a-zA-Z0-9+.-]*):')


def _classify_scheme(val):
    """Extract the ORD scheme prefix from a string value.

    Returns (scheme, body) or (None, None) if not an ORD.
    """
    # Check for BOrd.make("...") wrapper
    m = _BORD_MAKE_RE.search(val)
    if m:
        inner = m.group(1)
        sm = _SCHEME_RE.match(inner)
        if sm:
            return sm.group(1).lower(), inner
        # BOrd.make with no scheme — often a relative path
        return "relative", inner

    # Direct scheme literal
    sm = _SCHEME_RE.match(val)
    if sm:
        scheme = sm.group(1).lower()
        # Only count known Niagara schemes to avoid false positives
        if scheme + ":" in _NIAGARA_SCHEMES or scheme in (
            "station", "slot", "history", "local", "fox", "ip",
            "module", "spy", "view", "alarm", "baja", "file",
            "service", "ord",
        ):
            return scheme, val
    return None, None


def _query_all_ords(base_dir, module_filter=None):
    """Query string-index.db for all ORD-like strings.

    Returns list of dicts: {scheme, value, class_name, module, line}.
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
    """.format(where)

    params = []
    if module_filter:
        sql += " AND f.module = ?"
        params.append(module_filter)

    sql += " ORDER BY f.module, f.class_name, s.line_no"

    cur = conn.cursor()
    cur.execute(sql, params)

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
# cmd_ords — List all ORDs grouped by scheme
# ---------------------------------------------------------------------------

def cmd_ords(base_dir, module_filter=None, scheme_filter=None, limit=50):
    """List all ORDs found in the corpus, grouped by scheme prefix."""
    ords = _query_all_ords(base_dir, module_filter=module_filter)
    if not ords:
        print("  No ORDs found.")
        return

    if scheme_filter:
        scheme_lower = scheme_filter.lower().rstrip(":")
        ords = [o for o in ords if o["scheme"] == scheme_lower]
        if not ords:
            print("  No ORDs found for scheme '{}'.".format(scheme_filter))
            return

    # Group by scheme
    by_scheme = {}
    by_module = {}
    by_class = {}
    for o in ords:
        by_scheme.setdefault(o["scheme"], []).append(o)
        by_module.setdefault(o["module"], []).append(o)
        by_class.setdefault(o["class_name"], []).append(o)

    scope = ""
    if module_filter:
        scope += " in {}".format(module_filter)
    if scheme_filter:
        scope += " [{}:]".format(scheme_filter.lower().rstrip(":"))

    print("")
    print("  ORD RESOLUTION GRAPH{} ({:,} ORDs, {:,} classes, {:,} modules)".format(
        scope, len(ords), len(by_class), len(by_module)))
    print("")

    # Summary by scheme
    print("  By scheme:")
    for scheme in sorted(by_scheme.keys(), key=lambda s: -len(by_scheme[s])):
        items = by_scheme[scheme]
        classes = len(set(o["class_name"] for o in items))
        modules = len(set(o["module"] for o in items))
        print("    {:12s}  {:>5,d} refs  {:>5,d} classes  {:>4,d} modules".format(
            scheme + ":", len(items), classes, modules))
    print("")

    # Top modules by ORD count
    print("  Top modules by ORD usage:")
    top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:10]
    for mod, items in top_mods:
        schemes_used = sorted(set(o["scheme"] for o in items))
        print("    {:35s}  {:>4,d} ORDs  [{}]".format(
            mod, len(items), ", ".join(schemes_used)))
    print("")

    # Top classes by ORD count
    print("  Top classes by ORD usage:")
    top_cls = sorted(by_class.items(), key=lambda x: -len(x[1]))[:10]
    for cls, items in top_cls:
        mod = items[0]["module"]
        schemes_used = sorted(set(o["scheme"] for o in items))
        print("    {:35s}  {:>4,d} ORDs  {:25s}  [{}]".format(
            cls if len(cls) <= 35 else cls[:32] + "...",
            len(items), mod, ", ".join(schemes_used)))
    print("")

    # Detailed listing (with limit)
    if scheme_filter:
        print("  {:50s}  {:30s}  {:25s}  {:>5s}".format(
            "ORD VALUE", "CLASS", "MODULE", "LINE"))
        print("  " + "-" * 120)

        shown = 0
        for o in ords:
            if shown >= limit:
                remaining = len(ords) - shown
                print("  ... and {:,} more (use -n {:,} to see all)".format(
                    remaining, len(ords)))
                break

            val_display = o["value"] if len(o["value"]) <= 50 else o["value"][:47] + "..."
            cls_display = o["class_name"] if len(o["class_name"]) <= 30 else o["class_name"][:27] + "..."
            mod_display = o["module"] if len(o["module"]) <= 25 else o["module"][:22] + "..."
            print("  {:50s}  {:30s}  {:25s}  {:>5d}".format(
                val_display, cls_display, mod_display, o["line"]))
            shown += 1
        print("")


# ---------------------------------------------------------------------------
# cmd_ord_usage — Classes that use a specific scheme
# ---------------------------------------------------------------------------

def cmd_ord_usage(base_dir, scheme, module_filter=None, limit=50):
    """Show classes that use a specific ORD scheme."""
    scheme_lower = scheme.lower().rstrip(":")

    ords = _query_all_ords(base_dir, module_filter=module_filter)
    if not ords:
        print("  No ORDs found.")
        return

    # Filter by scheme
    filtered = [o for o in ords if o["scheme"] == scheme_lower]
    if not filtered:
        # Show available schemes
        available = sorted(set(o["scheme"] for o in ords))
        print("  No ORDs found for scheme '{}'.".format(scheme))
        print("  Available schemes: {}".format(", ".join(available)))
        return

    # Group by class
    by_class = {}
    for o in filtered:
        by_class.setdefault(o["class_name"], []).append(o)

    by_module = {}
    for o in filtered:
        by_module.setdefault(o["module"], []).append(o)

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  ORD USAGE: {}:{} ({:,} refs, {:,} classes, {:,} modules)".format(
        scheme_lower, scope, len(filtered), len(by_class), len(by_module)))
    print("")

    # Module breakdown
    print("  By module:")
    top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:15]
    for mod, items in top_mods:
        classes = len(set(o["class_name"] for o in items))
        print("    {:35s}  {:>4,d} refs  {:>3,d} classes".format(
            mod, len(items), classes))
    if len(by_module) > 15:
        print("    ... and {:,} more modules".format(len(by_module) - 15))
    print("")

    # Class table
    print("  {:35s}  {:30s}  {:>5s}  {}".format(
        "CLASS", "MODULE", "REFS", "SAMPLE ORD"))
    print("  " + "-" * 110)

    shown = 0
    for cls, items in sorted(by_class.items(), key=lambda x: -len(x[1])):
        if shown >= limit:
            remaining = len(by_class) - shown
            print("  ... and {:,} more classes (use -n {:,} to see all)".format(
                remaining, len(by_class)))
            break

        mod = items[0]["module"]
        sample = items[0]["value"]
        sample_display = sample if len(sample) <= 40 else sample[:37] + "..."
        cls_display = cls if len(cls) <= 35 else cls[:32] + "..."
        mod_display = mod if len(mod) <= 30 else mod[:27] + "..."

        print("  {:35s}  {:30s}  {:>5,d}  {}".format(
            cls_display, mod_display, len(items), sample_display))
        shown += 1

    print("")


# ---------------------------------------------------------------------------
# cmd_ord_flow — ORDs created/resolved by a specific class
# ---------------------------------------------------------------------------

def cmd_ord_flow(base_dir, class_name):
    """Show all ORDs used by a specific class, with context."""
    # Validate class exists
    ci = _load_class_index(base_dir)
    classes_map = ci.get("classes", {}) if ci else {}

    # Support partial/fuzzy match
    target = None
    if class_name in classes_map:
        target = class_name
    else:
        matches = [k for k in classes_map if class_name.lower() in k.lower()]
        if len(matches) == 1:
            target = matches[0]
        elif len(matches) > 1:
            print("")
            print("  Multiple matches for '{}':".format(class_name))
            for m in sorted(matches)[:20]:
                entries = classes_map.get(m, [])
                mod = entries[0].get("module", "?") if entries else "?"
                print("    {}  ({})".format(m, mod))
            if len(matches) > 20:
                print("    ... and {} more".format(len(matches) - 20))
            print("")
            return
        else:
            print("  Class '{}' not found.".format(class_name))
            return

    # Get class info
    entries = classes_map.get(target, [])
    class_info = entries[0] if entries else {}
    module = class_info.get("module", "unknown")

    # Query ORDs for this class
    conn = _get_string_db(base_dir)
    if not conn:
        return

    conditions = []
    for scheme in _NIAGARA_SCHEMES:
        conditions.append("s.string_val LIKE '{}%'".format(scheme))
    conditions.append("s.string_val LIKE '%BOrd.make%'")
    conditions.append("s.string_val LIKE '%new BOrd%'")

    where = " OR ".join(conditions)

    cur = conn.cursor()
    cur.execute("""
        SELECT s.string_val, s.line_no
        FROM strings s JOIN files f ON s.file_id = f.id
        WHERE f.class_name = ?
        AND ({})
        ORDER BY s.line_no
    """.format(where), (target,))

    ords = []
    for row in cur.fetchall():
        val, line = row
        scheme, body = _classify_scheme(val)
        if scheme:
            ords.append({
                "scheme": scheme,
                "value": body if body else val,
                "line": line,
            })

    print("")
    print("  ORD FLOW: {}".format(target))
    print("  " + "=" * (len(target) + 11))
    print("")
    print("  Module:   {}".format(module))
    print("  Package:  {}".format(class_info.get("package", "?")))
    print("  ORDs:     {:,} references".format(len(ords)))
    print("")

    if not ords:
        print("  No ORD references found in this class.")
        print("")
        return

    # Group by scheme
    by_scheme = {}
    for o in ords:
        by_scheme.setdefault(o["scheme"], []).append(o)

    print("  By scheme:")
    for scheme in sorted(by_scheme.keys(), key=lambda s: -len(by_scheme[s])):
        items = by_scheme[scheme]
        print("    {:12s}  {:>3d} refs".format(scheme + ":", len(items)))
    print("")

    # Detailed listing
    print("  {:>5s}  {:12s}  {}".format("LINE", "SCHEME", "ORD VALUE"))
    print("  " + "-" * 90)

    for o in ords:
        val_display = o["value"] if len(o["value"]) <= 70 else o["value"][:67] + "..."
        print("  {:>5d}  {:12s}  {}".format(
            o["line"], o["scheme"] + ":", val_display))
    print("")

    # Cross-reference: other classes in same module using same schemes
    if len(by_scheme) > 0:
        print("  Related classes in {} using same schemes:".format(module))
        cur.execute("""
            SELECT DISTINCT f.class_name
            FROM strings s JOIN files f ON s.file_id = f.id
            WHERE f.module = ? AND f.class_name != ?
            AND ({})
            LIMIT 20
        """.format(where), (module, target))

        related = [row[0] for row in cur.fetchall()]
        if related:
            for r in sorted(related):
                print("    {}".format(r))
            if len(related) == 20:
                print("    ... (showing first 20)")
        else:
            print("    (none)")
        print("")
