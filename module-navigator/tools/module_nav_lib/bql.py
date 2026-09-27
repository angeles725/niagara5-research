"""
BQL Query Analyzer commands for Module Navigator (Phase 36).

Extracts and categorizes BQL (Baja Query Language) queries from
string-index.db. Detects both pure BQL (scheme:|bql:select ...)
and embedded SQL queries used by RDB modules.

Categorizes by:
  - Type: BQL (Niagara native) vs SQL (RDBMS via rdb modules)
  - ORD scheme prefix: alarm:, station:, history:, slot:, service:
  - Query type: SELECT, INSERT, UPDATE, DELETE, CREATE, COUNT
  - Table/source: openAlarms, schedule, control, history, etc.

Uses string-index.db + class-index.json on-demand. No builder.

Commands:
  bql [--module mod] [--type bql|sql] [-n N]  List BQL/SQL queries found
  bql-tables [--module mod] [-n N]            Tables/sources most queried
  bql-class <class>                           Queries used by a specific class
"""

import json
import os
import re
import sqlite3


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# ORD schemes that appear before |bql: in Niagara query ORDs
_BQL_ORD_SCHEMES = [
    "station:", "slot:", "history:", "alarm:", "service:",
    "local:", "module:", "file:",
]

# Modules known to be RDBMS-related (SQL, not BQL)
_RDB_MODULE_PREFIXES = (
    "rdb", "sql", "oracle", "hsql", "mysql", "postgres",
    "alarmOrion", "historyOrion",
)

# SQL DDL/DML keywords that indicate pure SQL rather than BQL
_SQL_KEYWORDS = [
    "INSERT INTO", "CREATE TABLE", "DROP TABLE", "ALTER TABLE",
    "DELETE FROM", "UPDATE ", "INFORMATION_SCHEMA", "SYSTEM_LOBS",
    "TRUNCATE ", "CREATE INDEX", "CREATE VIEW",
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
# Query extraction helpers
# ---------------------------------------------------------------------------

# Regex to extract FROM target
_FROM_RE = re.compile(r'\bFROM\s+(\w+)', re.IGNORECASE)

# Regex to extract SELECT fields hint
_SELECT_RE = re.compile(r'\bSELECT\s+(.+?)\s+FROM\b', re.IGNORECASE)

# Regex to detect WHERE clause
_WHERE_RE = re.compile(r'\bWHERE\s+', re.IGNORECASE)


def _classify_query(val, module):
    """Classify a string as BQL, SQL, or None.

    Returns dict with keys: kind, query_type, scheme, table, where, value
    or None if not a query.
    """
    val_stripped = val.strip()
    val_upper = val_stripped.upper()

    # --- Detect BQL: explicit bql: prefix ---
    is_bql_prefix = "bql:" in val_stripped.lower()

    # --- Detect SQL keywords ---
    is_sql_kw = any(kw in val_upper for kw in _SQL_KEYWORDS)

    # --- Detect SELECT...FROM ---
    has_select_from = "SELECT" in val_upper and "FROM" in val_upper

    # --- Must be either bql: prefix or SELECT/SQL pattern ---
    if not is_bql_prefix and not has_select_from and not is_sql_kw:
        return None

    # Determine kind: BQL vs SQL
    is_rdb_module = any(module.lower().startswith(p.lower()) for p in _RDB_MODULE_PREFIXES)
    is_niagara_scheme = any(s in val_stripped.lower() for s in _BQL_ORD_SCHEMES)

    if is_bql_prefix or is_niagara_scheme:
        kind = "BQL"
    elif is_sql_kw or is_rdb_module:
        kind = "SQL"
    elif has_select_from:
        # Heuristic: if it has Niagara-style unquoted table names, likely BQL
        kind = "BQL" if not any(c in val_stripped for c in ("()", ";", "@@")) else "SQL"
    else:
        kind = "BQL"

    # Extract ORD scheme prefix (for BQL queries like "alarm:|bql:select ...")
    scheme = None
    if "|bql:" in val_stripped.lower() or "|" in val_stripped:
        parts = val_stripped.split("|")
        for p in parts:
            if ":" in p and not p.lower().startswith("bql"):
                s = p.split(":")[0].lower()
                if s + ":" in _BQL_ORD_SCHEMES or s in (
                    "station", "slot", "history", "alarm", "service",
                    "local", "module", "file",
                ):
                    scheme = s
                    break
    elif val_stripped.lower().startswith("bql:"):
        scheme = "direct"

    # Extract query type
    query_type = "SELECT"
    for kw in ["INSERT", "CREATE", "DROP", "ALTER", "DELETE", "UPDATE", "TRUNCATE"]:
        if kw in val_upper:
            query_type = kw
            break
    # COUNT detection
    if "COUNT" in val_upper and "SELECT" in val_upper:
        query_type = "SELECT/COUNT"

    # Extract table/source
    table = None
    m = _FROM_RE.search(val_stripped)
    if m:
        table = m.group(1)
    elif "INSERT INTO" in val_upper:
        m2 = re.search(r'INSERT\s+INTO\s+(\w+)', val_stripped, re.IGNORECASE)
        if m2:
            table = m2.group(1)
    elif "UPDATE " in val_upper:
        m2 = re.search(r'UPDATE\s+(\w+)', val_stripped, re.IGNORECASE)
        if m2:
            table = m2.group(1)
    elif "CREATE TABLE" in val_upper:
        m2 = re.search(r'CREATE\s+TABLE\s+(\w+)', val_stripped, re.IGNORECASE)
        if m2:
            table = m2.group(1)

    # Has WHERE clause?
    has_where = bool(_WHERE_RE.search(val_stripped))

    return {
        "kind": kind,
        "query_type": query_type,
        "scheme": scheme,
        "table": table,
        "where": has_where,
        "value": val_stripped,
    }


def _query_all_bql(base_dir, module_filter=None):
    """Query string-index.db for all BQL/SQL-like strings.

    Returns list of dicts with keys:
      kind, query_type, scheme, table, where, value, class_name, module, line
    """
    conn = _get_string_db(base_dir)
    if not conn:
        return []

    # Build WHERE clause to find BQL/SQL candidates
    conditions = [
        "s.string_val LIKE '%bql:%'",
        "(UPPER(s.string_val) LIKE '%SELECT %' AND UPPER(s.string_val) LIKE '%FROM %')",
        "UPPER(s.string_val) LIKE '%INSERT INTO%'",
        "UPPER(s.string_val) LIKE '%CREATE TABLE%'",
        "UPPER(s.string_val) LIKE '%DELETE FROM%'",
        "(UPPER(s.string_val) LIKE '%UPDATE %' AND UPPER(s.string_val) LIKE '%SET %')",
    ]

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
    seen = set()  # deduplicate identical (value, class, line) triples
    for row in cur.fetchall():
        val, cls, mod, line = row
        dedup_key = (val.strip(), cls, line)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        info = _classify_query(val, mod)
        if info:
            info["class_name"] = cls
            info["module"] = mod
            info["line"] = line
            results.append(info)

    return results


# ---------------------------------------------------------------------------
# cmd_bql — List all BQL/SQL queries found
# ---------------------------------------------------------------------------

def cmd_bql(base_dir, module_filter=None, type_filter=None, limit=50):
    """List all BQL/SQL queries found in the corpus."""
    queries = _query_all_bql(base_dir, module_filter=module_filter)
    if not queries:
        print("  No BQL/SQL queries found.")
        return

    if type_filter:
        tf = type_filter.upper()
        queries = [q for q in queries if q["kind"] == tf]
        if not queries:
            print("  No {} queries found.".format(type_filter.upper()))
            return

    # Aggregate stats
    by_kind = {}
    by_type = {}
    by_scheme = {}
    by_module = {}
    by_class = {}
    for q in queries:
        by_kind.setdefault(q["kind"], []).append(q)
        by_type.setdefault(q["query_type"], []).append(q)
        if q["scheme"]:
            by_scheme.setdefault(q["scheme"], []).append(q)
        by_module.setdefault(q["module"], []).append(q)
        by_class.setdefault(q["class_name"], []).append(q)

    scope = ""
    if module_filter:
        scope += " in {}".format(module_filter)
    if type_filter:
        scope += " [{}]".format(type_filter.upper())

    print("")
    print("  BQL QUERY ANALYZER{} ({:,} queries, {:,} classes, {:,} modules)".format(
        scope, len(queries), len(by_class), len(by_module)))
    print("")

    # By kind (BQL vs SQL)
    print("  By kind:")
    for kind in sorted(by_kind.keys()):
        items = by_kind[kind]
        cls_count = len(set(q["class_name"] for q in items))
        mod_count = len(set(q["module"] for q in items))
        print("    {:8s}  {:>5,d} queries  {:>5,d} classes  {:>4,d} modules".format(
            kind, len(items), cls_count, mod_count))
    print("")

    # By query type
    print("  By query type:")
    for qt in sorted(by_type.keys(), key=lambda t: -len(by_type[t])):
        items = by_type[qt]
        print("    {:15s}  {:>5,d} queries".format(qt, len(items)))
    print("")

    # By ORD scheme (BQL only)
    if by_scheme:
        print("  By ORD scheme (BQL):")
        for scheme in sorted(by_scheme.keys(), key=lambda s: -len(by_scheme[s])):
            items = by_scheme[scheme]
            print("    {:12s}  {:>5,d} queries".format(
                scheme + ":", len(items)))
        print("")

    # Top modules
    print("  Top modules by query count:")
    top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:15]
    for mod, items in top_mods:
        bql_n = sum(1 for q in items if q["kind"] == "BQL")
        sql_n = sum(1 for q in items if q["kind"] == "SQL")
        parts = []
        if bql_n:
            parts.append("{} BQL".format(bql_n))
        if sql_n:
            parts.append("{} SQL".format(sql_n))
        print("    {:35s}  {:>4,d} queries  [{}]".format(
            mod, len(items), ", ".join(parts)))
    if len(by_module) > 15:
        print("    ... and {:,} more modules".format(len(by_module) - 15))
    print("")

    # Top classes
    print("  Top classes by query count:")
    top_cls = sorted(by_class.items(), key=lambda x: -len(x[1]))[:10]
    for cls, items in top_cls:
        mod = items[0]["module"]
        kinds = sorted(set(q["kind"] for q in items))
        cls_display = cls if len(cls) <= 35 else cls[:32] + "..."
        print("    {:35s}  {:>4,d} queries  {:25s}  [{}]".format(
            cls_display, len(items), mod, "/".join(kinds)))
    print("")

    # Detailed listing
    print("  {:6s}  {:15s}  {:50s}  {:25s}  {}".format(
        "KIND", "QUERY TYPE", "QUERY (truncated)", "CLASS", "MODULE"))
    print("  " + "-" * 130)

    shown = 0
    for q in queries:
        if shown >= limit:
            remaining = len(queries) - shown
            print("  ... and {:,} more (use -n {:,} to see all)".format(
                remaining, len(queries)))
            break

        val_display = q["value"] if len(q["value"]) <= 50 else q["value"][:47] + "..."
        cls_display = q["class_name"] if len(q["class_name"]) <= 25 else q["class_name"][:22] + "..."
        print("  {:6s}  {:15s}  {:50s}  {:25s}  {}".format(
            q["kind"], q["query_type"], val_display, cls_display, q["module"]))
        shown += 1

    print("")


# ---------------------------------------------------------------------------
# cmd_bql_tables — Tables/sources most queried
# ---------------------------------------------------------------------------

def cmd_bql_tables(base_dir, module_filter=None, limit=50):
    """Show the most queried tables/sources in BQL and SQL."""
    queries = _query_all_bql(base_dir, module_filter=module_filter)
    if not queries:
        print("  No BQL/SQL queries found.")
        return

    # Group by table
    by_table = {}
    no_table = 0
    for q in queries:
        table = q["table"]
        if table:
            by_table.setdefault(table, []).append(q)
        else:
            no_table += 1

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  BQL TABLES{} ({:,} tables from {:,} queries, {:,} without table)".format(
        scope, len(by_table), len(queries), no_table))
    print("")

    # Summary by kind
    bql_tables = set()
    sql_tables = set()
    for table, items in by_table.items():
        for q in items:
            if q["kind"] == "BQL":
                bql_tables.add(table)
            else:
                sql_tables.add(table)

    print("  BQL tables (Niagara): {:,}".format(len(bql_tables)))
    print("  SQL tables (RDBMS):   {:,}".format(len(sql_tables)))
    print("")

    # Table ranking
    print("  {:30s}  {:>5s}  {:>5s}  {:>5s}  {:6s}  {}".format(
        "TABLE/SOURCE", "TOTAL", "BQL", "SQL", "TYPE", "TOP MODULES"))
    print("  " + "-" * 110)

    shown = 0
    for table, items in sorted(by_table.items(), key=lambda x: -len(x[1])):
        if shown >= limit:
            remaining = len(by_table) - shown
            print("  ... and {:,} more (use -n {:,} to see all)".format(
                remaining, len(by_table)))
            break

        bql_n = sum(1 for q in items if q["kind"] == "BQL")
        sql_n = sum(1 for q in items if q["kind"] == "SQL")
        dominant = "BQL" if bql_n >= sql_n else "SQL"

        # Top modules for this table
        mod_counts = {}
        for q in items:
            mod_counts.setdefault(q["module"], 0)
            mod_counts[q["module"]] += 1
        top_mods = sorted(mod_counts.items(), key=lambda x: -x[1])[:3]
        mods_str = ", ".join("{}({})".format(m, c) for m, c in top_mods)

        tbl_display = table if len(table) <= 30 else table[:27] + "..."
        print("  {:30s}  {:>5,d}  {:>5,d}  {:>5,d}  {:6s}  {}".format(
            tbl_display, len(items), bql_n, sql_n, dominant, mods_str))
        shown += 1

    print("")

    # Query type breakdown per table (top 10)
    print("  Top tables with query type breakdown:")
    top10 = sorted(by_table.items(), key=lambda x: -len(x[1]))[:10]
    for table, items in top10:
        qt_counts = {}
        for q in items:
            qt_counts.setdefault(q["query_type"], 0)
            qt_counts[q["query_type"]] += 1
        qt_str = ", ".join("{}:{}".format(t, c) for t, c
                           in sorted(qt_counts.items(), key=lambda x: -x[1]))
        print("    {:25s}  {}".format(table, qt_str))
    print("")


# ---------------------------------------------------------------------------
# cmd_bql_class — Queries used by a specific class
# ---------------------------------------------------------------------------

def cmd_bql_class(base_dir, class_name):
    """Show all BQL/SQL queries used by a specific class."""
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

    # Query all BQL strings for this class
    conn = _get_string_db(base_dir)
    if not conn:
        return

    conditions = [
        "s.string_val LIKE '%bql:%'",
        "(UPPER(s.string_val) LIKE '%SELECT %' AND UPPER(s.string_val) LIKE '%FROM %')",
        "UPPER(s.string_val) LIKE '%INSERT INTO%'",
        "UPPER(s.string_val) LIKE '%CREATE TABLE%'",
        "UPPER(s.string_val) LIKE '%DELETE FROM%'",
        "(UPPER(s.string_val) LIKE '%UPDATE %' AND UPPER(s.string_val) LIKE '%SET %')",
    ]

    where = " OR ".join(conditions)

    cur = conn.cursor()
    cur.execute("""
        SELECT s.string_val, s.line_no
        FROM strings s JOIN files f ON s.file_id = f.id
        WHERE f.class_name = ?
        AND ({})
        ORDER BY s.line_no
    """.format(where), (target,))

    queries = []
    seen = set()
    for row in cur.fetchall():
        val, line = row
        dedup_key = (val.strip(), line)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        info = _classify_query(val, module)
        if info:
            info["line"] = line
            queries.append(info)

    print("")
    print("  BQL ANALYSIS: {}".format(target))
    print("  " + "=" * (len(target) + 15))
    print("")
    print("  Module:   {}".format(module))
    print("  Package:  {}".format(class_info.get("package", "?")))
    print("  Queries:  {:,} found".format(len(queries)))
    print("")

    if not queries:
        print("  No BQL/SQL queries found in this class.")
        print("")
        return

    # Stats
    by_kind = {}
    by_type = {}
    by_table = {}
    for q in queries:
        by_kind.setdefault(q["kind"], []).append(q)
        by_type.setdefault(q["query_type"], []).append(q)
        if q["table"]:
            by_table.setdefault(q["table"], []).append(q)

    print("  Kind:       {}".format(
        ", ".join("{} {}".format(len(v), k) for k, v in sorted(by_kind.items()))))
    print("  Types:      {}".format(
        ", ".join("{} {}".format(len(v), k) for k, v
                  in sorted(by_type.items(), key=lambda x: -len(x[1])))))
    if by_table:
        print("  Tables:     {}".format(
            ", ".join("{} ({})".format(t, len(v)) for t, v
                      in sorted(by_table.items(), key=lambda x: -len(x[1])))))
    with_where = sum(1 for q in queries if q["where"])
    print("  With WHERE: {:,} ({:.0f}%)".format(
        with_where, 100.0 * with_where / len(queries) if queries else 0))
    print("")

    # Detailed listing
    print("  {:>5s}  {:6s}  {:15s}  {:15s}  {}".format(
        "LINE", "KIND", "TYPE", "TABLE", "QUERY"))
    print("  " + "-" * 100)

    for q in queries:
        val_display = q["value"] if len(q["value"]) <= 60 else q["value"][:57] + "..."
        table_display = q["table"] if q["table"] else "-"
        print("  {:>5d}  {:6s}  {:15s}  {:15s}  {}".format(
            q["line"], q["kind"], q["query_type"],
            table_display, val_display))
    print("")

    # Cross-reference: other classes in same module with queries
    cur.execute("""
        SELECT DISTINCT f.class_name
        FROM strings s JOIN files f ON s.file_id = f.id
        WHERE f.module = ? AND f.class_name != ?
        AND ({})
        LIMIT 20
    """.format(where), (module, target))

    related = [row[0] for row in cur.fetchall()]
    if related:
        print("  Other classes in {} with queries:".format(module))
        for r in sorted(related):
            print("    {}".format(r))
        if len(related) == 20:
            print("    ... (showing first 20)")
        print("")
