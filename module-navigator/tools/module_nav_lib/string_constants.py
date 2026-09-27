"""
String constant index commands for Module Navigator (Phase 30).

Uses SQLite index (string-index.db) for fast regex/LIKE searches
across all string literals in 51K+ decompiled Java files.

Much faster than grep for string literal queries (~90s full grep -> <1s indexed).

Commands:
  string-search <pattern> [-n N]           Regex search in string literals
    [--module <mod>]                       Filter by module
  string-constants <class> [-n N]          All string literals in a class
"""

import os
import re
import sqlite3


# ---------------------------------------------------------------------------
# Database connection (lazy, on-demand)
# ---------------------------------------------------------------------------

_db_conn = None


def _get_db(base_dir):
    """Get or open the string-index.db connection (lazy singleton)."""
    global _db_conn
    if _db_conn is not None:
        return _db_conn

    db_path = os.path.join(base_dir, "indexes", "string-index.db")
    if not os.path.isfile(db_path):
        print("ERROR: string-index.db not found.")
        print("Run: python tools/build_string_index.py")
        return None

    _db_conn = sqlite3.connect(db_path)
    _db_conn.execute("PRAGMA query_only=ON")
    _db_conn.execute("PRAGMA cache_size=-16000")  # 16 MB read cache
    return _db_conn


def _get_meta(conn):
    """Read meta table as dict."""
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM meta")
    return dict(cur.fetchall())


# ---------------------------------------------------------------------------
# string-search command — regex search in string literals
# ---------------------------------------------------------------------------

def cmd_string_search(base_dir, pattern, module_filter=None, limit=50):
    """Search for string literals matching a regex pattern."""
    conn = _get_db(base_dir)
    if not conn:
        return

    cur = conn.cursor()

    # First try exact LIKE match for simple patterns (fast path)
    # If pattern contains regex metacharacters, we'll use Python regex post-filter
    is_simple = not any(c in pattern for c in r'.+*?[](){}|^$\\')

    if is_simple:
        # Simple substring match via SQLite LIKE
        like_pattern = '%' + pattern + '%'
        if module_filter:
            cur.execute("""
                SELECT s.string_val, f.class_name, f.module, s.line_no
                FROM strings s
                JOIN files f ON s.file_id = f.id
                WHERE s.string_val LIKE ? AND f.module = ?
                ORDER BY f.module, f.class_name, s.line_no
            """, (like_pattern, module_filter))
        else:
            cur.execute("""
                SELECT s.string_val, f.class_name, f.module, s.line_no
                FROM strings s
                JOIN files f ON s.file_id = f.id
                WHERE s.string_val LIKE ?
                ORDER BY f.module, f.class_name, s.line_no
            """, (like_pattern,))
        rows = cur.fetchall()
    else:
        # Regex search: fetch candidates with LIKE prefix then filter with Python re
        # Extract a fixed prefix for LIKE pre-filter if possible
        like_prefix = _extract_like_prefix(pattern)

        if module_filter:
            if like_prefix:
                cur.execute("""
                    SELECT s.string_val, f.class_name, f.module, s.line_no
                    FROM strings s
                    JOIN files f ON s.file_id = f.id
                    WHERE s.string_val LIKE ? AND f.module = ?
                    ORDER BY f.module, f.class_name, s.line_no
                """, ('%' + like_prefix + '%', module_filter))
            else:
                cur.execute("""
                    SELECT s.string_val, f.class_name, f.module, s.line_no
                    FROM strings s
                    JOIN files f ON s.file_id = f.id
                    WHERE f.module = ?
                    ORDER BY f.module, f.class_name, s.line_no
                """, (module_filter,))
        else:
            if like_prefix:
                cur.execute("""
                    SELECT s.string_val, f.class_name, f.module, s.line_no
                    FROM strings s
                    JOIN files f ON s.file_id = f.id
                    WHERE s.string_val LIKE ?
                    ORDER BY f.module, f.class_name, s.line_no
                """, ('%' + like_prefix + '%',))
            else:
                cur.execute("""
                    SELECT s.string_val, f.class_name, f.module, s.line_no
                    FROM strings s
                    JOIN files f ON s.file_id = f.id
                    ORDER BY f.module, f.class_name, s.line_no
                """)

        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error:
            rx = re.compile(re.escape(pattern), re.IGNORECASE)

        rows = [r for r in cur.fetchall() if rx.search(r[0])]

    if not rows:
        print("")
        print("  No string literals matching '{}' found.".format(pattern))
        if module_filter:
            # Check without module filter
            if is_simple:
                cur.execute(
                    "SELECT COUNT(*) FROM strings WHERE string_val LIKE ?",
                    ('%' + pattern + '%',))
            else:
                cur.execute("SELECT COUNT(*) FROM strings")
            total = cur.fetchone()[0]
            if total > 0 and module_filter:
                print("  Try without --module filter.")
        print("")
        return

    total_hits = len(rows)

    # Group by module
    by_module = {}
    for string_val, class_name, module, line_no in rows:
        if module not in by_module:
            by_module[module] = []
        by_module[module].append((string_val, class_name, line_no))

    unique_classes = len(set((r[1], r[2]) for r in rows))
    unique_vals = len(set(r[0] for r in rows))

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  STRING-SEARCH: '{}'{} ({:,} hits, {:,} unique, {:,} classes, {:,} modules)".format(
        pattern, scope, total_hits, unique_vals, unique_classes, len(by_module)))
    print("")

    # Show results
    print("  {:50s}  {:>5s}  {:20s}  {}".format("STRING", "LINE", "CLASS", "MODULE"))
    print("  " + "-" * 95)

    shown = 0
    for mod in sorted(by_module.keys()):
        entries = by_module[mod]
        for string_val, class_name, line_no in entries:
            if shown >= limit:
                remaining = total_hits - shown
                print("  ... and {:,} more (use -n {:,} to see all)".format(
                    remaining, total_hits))
                print("")
                _show_module_summary(by_module)
                return

            display_str = string_val if len(string_val) <= 50 else string_val[:47] + "..."
            display_cls = class_name if len(class_name) <= 20 else class_name[:17] + "..."
            print("  {:50s}  {:>5d}  {:20s}  {}".format(
                '"' + display_str + '"',
                line_no, display_cls, mod))
            shown += 1

    print("")
    _show_module_summary(by_module)


# ---------------------------------------------------------------------------
# string-constants command — all strings in a class
# ---------------------------------------------------------------------------

def cmd_string_constants(base_dir, class_name, limit=50):
    """Show all string literals defined in a specific class."""
    conn = _get_db(base_dir)
    if not conn:
        return

    cur = conn.cursor()

    # Find the class
    cur.execute("""
        SELECT id, module, path FROM files
        WHERE class_name = ?
    """, (class_name,))
    files = cur.fetchall()

    if not files:
        # Try case-insensitive
        cur.execute("""
            SELECT id, module, path, class_name FROM files
            WHERE class_name LIKE ? COLLATE NOCASE
            LIMIT 10
        """, (class_name,))
        suggestions = cur.fetchall()

        print("")
        print("  Class '{}' not found in string index.".format(class_name))
        if suggestions:
            print("  Did you mean:")
            for _, mod, _, cn in suggestions:
                print("    {} ({})".format(cn, mod))
        print("")
        return

    # Collect strings from all files matching this class
    all_strings = []
    modules_seen = set()

    for file_id, module, path in files:
        modules_seen.add(module)
        cur.execute("""
            SELECT string_val, line_no FROM strings
            WHERE file_id = ?
            ORDER BY line_no
        """, (file_id,))
        for string_val, line_no in cur.fetchall():
            all_strings.append((string_val, line_no, module))

    if not all_strings:
        print("")
        print("  {} ({}) — no string literals found.".format(
            class_name, ", ".join(sorted(modules_seen))))
        print("")
        return

    unique_vals = len(set(s[0] for s in all_strings))

    print("")
    print("  STRING-CONSTANTS: {} ({})".format(
        class_name, ", ".join(sorted(modules_seen))))
    print("  {:,} total, {:,} unique string literals".format(
        len(all_strings), unique_vals))
    print("")

    # Categorize
    categories = {
        "URLs": [],
        "SQL": [],
        "Paths": [],
        "Messages": [],
        "Other": [],
    }

    for string_val, line_no, module in all_strings:
        if string_val.startswith("http://") or string_val.startswith("https://"):
            categories["URLs"].append((string_val, line_no))
        elif any(kw in string_val.upper() for kw in
                 ["SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE TABLE",
                  "DROP TABLE", "ALTER TABLE"]):
            categories["SQL"].append((string_val, line_no))
        elif "/" in string_val and "." in string_val:
            categories["Paths"].append((string_val, line_no))
        elif len(string_val) > 20:
            categories["Messages"].append((string_val, line_no))
        else:
            categories["Other"].append((string_val, line_no))

    # Show by category
    shown = 0
    for cat_name, cat_items in categories.items():
        if not cat_items:
            continue
        print("  {} ({:,}):".format(cat_name, len(cat_items)))
        for string_val, line_no in cat_items:
            if shown >= limit:
                remaining = len(all_strings) - shown
                print("")
                print("  ... and {:,} more (use -n {:,} to see all)".format(
                    remaining, len(all_strings)))
                _show_category_summary(categories)
                return

            display = string_val if len(string_val) <= 70 else string_val[:67] + "..."
            print("    L{:>5d}: \"{}\"".format(line_no, display))
            shown += 1
        print("")

    _show_category_summary(categories)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_like_prefix(pattern):
    """Extract a fixed-string prefix from a regex for LIKE pre-filtering."""
    # Take characters before the first metacharacter
    prefix = []
    for ch in pattern:
        if ch in r'.+*?[](){}|^$\\':
            break
        prefix.append(ch)
    result = ''.join(prefix)
    return result if len(result) >= 2 else ''


def _show_module_summary(by_module):
    """Show top modules summary."""
    top_mods = sorted(by_module.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print("  Top modules:")
    for mod, entries in top_mods:
        classes = len(set(e[1] for e in entries))
        print("    {:35s}  {:>5} hits, {:>4} classes".format(
            mod, len(entries), classes))
    if len(by_module) > 10:
        print("    ... and {} more modules".format(len(by_module) - 10))
    print("")


def _show_category_summary(categories):
    """Show category breakdown."""
    print("  Category summary:")
    for cat_name, cat_items in categories.items():
        if cat_items:
            print("    {:12s} {:>6,} strings".format(cat_name + ":", len(cat_items)))
    print("")
