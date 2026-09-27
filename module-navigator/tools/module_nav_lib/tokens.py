"""
Full-text token search commands for Module Navigator (Phase 18).

Uses SQLite inverted index (token-index.db) for O(1) exact-token lookups
across all 51K+ decompiled Java files. Much faster than grep for single
token queries (~90s full grep → <1s token lookup).

Commands:
  token <word> [-n N]              Exact token search (instant)
  token <word> --context           With surrounding source lines
  token <word> --module <mod>      Filter by module
"""

import os
import sqlite3

import corpus_config


# ---------------------------------------------------------------------------
# Database connection (lazy, on-demand)
# ---------------------------------------------------------------------------

_db_conn = None


def _get_db(base_dir):
    """Get or open the token-index.db connection (lazy singleton)."""
    global _db_conn
    if _db_conn is not None:
        return _db_conn

    db_path = os.path.join(base_dir, "indexes", "token-index.db")
    if not os.path.isfile(db_path):
        print("ERROR: token-index.db not found.")
        print("Run: python tools/build_token_index.py")
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


def _resolve_source_root(meta_source):
    """Resolve the corpus source root via env var + fallback chain.

    Kept in sync with grep_search._resolve_source_root. See that function for
    the full semantics — if NAV_CORPUS_BASE is set, it is the only path tried;
    a set-but-invalid env var is a hard error, not a silent fallback.

    Returns (resolved_path, None) on success or (None, tried_paths) on failure.
    """
    tried = []

    env_override = os.environ.get("NAV_CORPUS_BASE")
    if env_override:
        tried.append(env_override)
        if os.path.isdir(env_override):
            return env_override, None
        return None, tried

    for candidate in [
        meta_source,
        os.environ.get("NAV_ORGANIZED_DIR"),
        corpus_config.default_organized_dir_from_lib_file(__file__),
    ]:
        if not candidate:
            continue
        tried.append(candidate)
        if os.path.isdir(candidate):
            return candidate, None
    return None, tried


def _print_source_root_error(tried):
    """Print an actionable error listing every path attempted."""
    print("")
    print("ERROR: Corpus source root not found.")
    print("  Tried the following paths (first valid wins):")
    for p in tried:
        print("    {}".format(p))
    print("")
    print("  Override with the NAV_CORPUS_BASE environment variable, e.g.:")
    print("    export NAV_CORPUS_BASE=/home/user/modules/organized")
    print("")


def _get_source_root(conn):
    """Get the resolved corpus root.

    Returns the resolved path on success, or None after printing an actionable
    error. Used only when --context is requested (i.e. when we need to read
    the source file). Silent when the caller never dereferences the path.
    """
    meta = _get_meta(conn)
    meta_source = meta.get("source_root", "")
    resolved, tried = _resolve_source_root(meta_source)
    if resolved:
        return resolved
    _print_source_root_error(tried)
    return None


# ---------------------------------------------------------------------------
# token command — exact token search
# ---------------------------------------------------------------------------

def cmd_token(base_dir, word, module_filter=None, show_context=False,
              context_lines=2, limit=50):
    """Search for an exact token across all decompiled sources."""
    conn = _get_db(base_dir)
    if not conn:
        return

    cur = conn.cursor()

    # Query postings with file info
    if module_filter:
        cur.execute("""
            SELECT p.token, f.class_name, f.module, f.path, p.line_no
            FROM postings p
            JOIN files f ON p.file_id = f.id
            WHERE p.token = ? AND f.module = ?
            ORDER BY f.module, f.class_name, p.line_no
        """, (word, module_filter))
    else:
        cur.execute("""
            SELECT p.token, f.class_name, f.module, f.path, p.line_no
            FROM postings p
            JOIN files f ON p.file_id = f.id
            WHERE p.token = ?
            ORDER BY f.module, f.class_name, p.line_no
        """, (word,))

    rows = cur.fetchall()

    if not rows:
        # Try case-insensitive partial match for suggestions
        cur.execute("""
            SELECT DISTINCT token FROM postings
            WHERE token LIKE ? COLLATE NOCASE
            LIMIT 10
        """, ('%' + word + '%',))
        suggestions = [r[0] for r in cur.fetchall()]

        print("")
        print("  Token '{}' not found in index.".format(word))
        if module_filter:
            # Check without module filter
            cur.execute(
                "SELECT COUNT(*) FROM postings WHERE token = ?", (word,))
            total = cur.fetchone()[0]
            if total > 0:
                print("  Found {} occurrences without module filter.".format(total))
                print("  Try: token {}".format(word))
        elif suggestions:
            print("  Similar tokens: {}".format(", ".join(suggestions)))
        print("")
        return

    total_hits = len(rows)

    # Group by module
    by_module = {}
    for _, class_name, module, path, line_no in rows:
        if module not in by_module:
            by_module[module] = []
        by_module[module].append((class_name, path, line_no))

    unique_classes = len(set((r[1], r[2]) for r in rows))  # (class, module) pairs

    scope = ""
    if module_filter:
        scope = " in {}".format(module_filter)

    print("")
    print("  TOKEN: '{}'{} ({:,} occurrences in {:,} classes, {:,} modules)".format(
        word, scope, total_hits, unique_classes, len(by_module)))
    print("")

    if show_context:
        _show_with_context(base_dir, conn, rows, limit, context_lines)
    else:
        _show_compact(by_module, limit, total_hits)


def _show_compact(by_module, limit, total_hits):
    """Show compact token results (class + line + module)."""
    print("  {:35s}  {:>5s}  {}".format("CLASS", "LINE", "MODULE"))
    print("  " + "-" * 65)

    shown = 0
    for mod in sorted(by_module.keys()):
        entries = by_module[mod]
        for class_name, path, line_no in entries:
            if shown >= limit:
                remaining = total_hits - shown
                print("  ... and {:,} more (use -n {:,} to see all)".format(
                    remaining, total_hits))
                print("")
                _show_module_summary(by_module)
                return

            print("  {:35s}  {:>5d}  {}".format(
                _truncate(class_name, 35), line_no, mod))
            shown += 1

    print("")
    _show_module_summary(by_module)


def _show_with_context(base_dir, conn, rows, limit, context_lines):
    """Show token results with surrounding source lines."""
    source_root = _get_source_root(conn)
    if not source_root:
        print("  ERROR: Source root not available. Falling back to compact view.")
        by_module = {}
        for _, class_name, module, path, line_no in rows:
            if module not in by_module:
                by_module[module] = []
            by_module[module].append((class_name, path, line_no))
        _show_compact(by_module, limit, len(rows))
        return

    shown = 0
    prev_path = None
    file_lines = None

    for _, class_name, module, rel_path, line_no in rows:
        if shown >= limit:
            remaining = len(rows) - shown
            print("  ... and {:,} more (use -n {:,} to see all)".format(
                remaining, len(rows)))
            break

        # Load file if different from previous
        if rel_path != prev_path:
            filepath = os.path.join(source_root, rel_path)
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    file_lines = f.readlines()
            except Exception:
                file_lines = None
            prev_path = rel_path

            # Print file header
            if shown > 0:
                print("")
            print("  --- {} ({}) ---".format(class_name, module))

        if file_lines is None:
            print("    {:>5d}: (source not available)".format(line_no))
            shown += 1
            continue

        # Show context lines
        start = max(0, line_no - 1 - context_lines)
        end = min(len(file_lines), line_no + context_lines)

        for i in range(start, end):
            ln = i + 1
            line_text = file_lines[i].rstrip()
            if len(line_text) > 100:
                line_text = line_text[:97] + "..."
            marker = " >> " if ln == line_no else "    "
            print("  {}{:>5d}: {}".format(marker, ln, line_text))

        if shown < limit - 1:
            # Small separator between context blocks within same file
            next_idx = shown + 1
            if next_idx < len(rows):
                next_path = rows[next_idx][3]
                next_line = rows[next_idx][4]
                if next_path == rel_path and next_line - line_no <= context_lines * 2 + 1:
                    pass  # Lines overlap, no separator needed
                else:
                    print("")

        shown += 1

    print("")


def _show_module_summary(by_module):
    """Show top modules summary."""
    top_mods = sorted(by_module.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print("  Top modules:")
    for mod, entries in top_mods:
        classes = len(set(e[0] for e in entries))
        print("    {:35s}  {:>5} hits, {:>4} classes".format(
            mod, len(entries), classes))
    if len(by_module) > 10:
        print("    ... and {} more modules".format(len(by_module) - 10))
    print("")


def _truncate(s, max_len):
    """Truncate string with ellipsis."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."
