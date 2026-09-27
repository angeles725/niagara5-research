#!/usr/bin/env python
"""
Build string literal index from decompiled Java sources (Phase 30).

Reads class-index.json as a catalog of all top-level .java files,
extracts every string literal ("..."), and produces indexes/string-index.db
(SQLite) with:

  files:    (id, path, module, class_name)
  strings:  (string_val, file_id, line_no)
  meta:     (key, value) -- build stats

SQLite is used for fast regex/LIKE searches across millions of string literals
without loading them all into memory.

Usage:
  python tools/build_string_index.py [--base-dir DIR] [--min-len N]
"""

import json
import os
import re
import sqlite3
import sys
import time


# ---------------------------------------------------------------------------
# String literal extractor
# ---------------------------------------------------------------------------

# Matches "..." including escaped chars, but not empty strings
RE_STRING_LITERAL = re.compile(r'"((?:[^"\\]|\\.)+)"')

# Noise patterns to skip (generated code, package/import paths)
RE_NOISE = re.compile(
    r'^(?:'
    r'com\.[a-z]+\.[a-z]+|'        # package paths: com.tridium.alarm
    r'javax?\.[a-z]+\.[a-z]+|'     # java/javax paths
    r'org\.[a-z]+\.[a-z]+|'        # org paths
    r'[a-z]+/[a-z]+/[a-z]+'        # slash paths: com/tridium/alarm
    r')$'
)


def extract_strings(lines, min_len=2):
    """Extract string literals from Java source lines.

    Returns list of (line_no, string_value) tuples.
    Skips import/package lines, single-char strings, and package-path noise.
    """
    results = []
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip import/package lines
        if stripped.startswith("import ") or stripped.startswith("package "):
            continue
        # Skip single-line comments
        if stripped.startswith("//"):
            continue

        for m in RE_STRING_LITERAL.finditer(line):
            val = m.group(1)
            if len(val) < min_len:
                continue
            # Skip pure package-path noise
            if RE_NOISE.match(val):
                continue
            results.append((line_no, val))

    return results


# ---------------------------------------------------------------------------
# Build index
# ---------------------------------------------------------------------------

def build_index(base_dir, min_string_len=2):
    """Build string literal index from all decompiled sources."""
    # Load class-index for file catalog
    ci_path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(ci_path):
        print("ERROR: class-index.json not found. Run build_class_index.py first.")
        sys.exit(1)

    print("Loading class-index.json...")
    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = json.load(f)

    classes = ci_data.get("classes", {})
    source_root = ci_data.get("_meta", {}).get("source", "")

    if not source_root or not os.path.isdir(source_root):
        print("ERROR: Source root '{}' not found.".format(source_root))
        sys.exit(1)

    # Gather all top-level files
    files_to_scan = []
    for class_name, entries in classes.items():
        for entry in entries:
            if entry.get("inner") or entry.get("outer_class") not in (None, "None", ""):
                continue
            rel_path = entry.get("path", "")
            module = entry.get("module", "")
            if rel_path:
                filepath = os.path.join(source_root, rel_path)
                if os.path.isfile(filepath):
                    files_to_scan.append((filepath, rel_path, class_name, module))

    print("Scanning {} files for string literals...".format(len(files_to_scan)))

    # Create SQLite database
    db_path = os.path.join(base_dir, "indexes", "string-index.db")
    if os.path.isfile(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA cache_size=-64000")  # 64 MB cache
    conn.execute("PRAGMA temp_store=MEMORY")
    cur = conn.cursor()

    # Create tables (indexes created AFTER bulk insert for speed)
    cur.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            module TEXT NOT NULL,
            class_name TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE strings (
            string_val TEXT NOT NULL,
            file_id INTEGER NOT NULL,
            line_no INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    start_time = time.time()
    total_strings = 0
    unique_strings = set()
    files_with_strings = 0
    total_lines = 0
    report_interval = 5000
    batch = []
    batch_size = 50000

    for idx, (filepath, rel_path, class_name, module) in enumerate(files_to_scan):
        if (idx + 1) % report_interval == 0:
            elapsed = time.time() - start_time
            print("  {} / {} files ({:.0f}s, {:,} strings)...".format(
                idx + 1, len(files_to_scan), elapsed, total_strings))

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            continue

        if not lines:
            continue

        # Insert file record
        file_id = idx + 1
        cur.execute(
            "INSERT INTO files (id, path, module, class_name) VALUES (?, ?, ?, ?)",
            (file_id, rel_path, module, class_name)
        )

        extracted = extract_strings(lines, min_string_len)
        total_lines += len(lines)

        if extracted:
            files_with_strings += 1
            for line_no, string_val in extracted:
                unique_strings.add(string_val)
                batch.append((string_val, file_id, line_no))
                total_strings += 1

            # Flush batch
            if len(batch) >= batch_size:
                cur.executemany(
                    "INSERT INTO strings (string_val, file_id, line_no) VALUES (?, ?, ?)",
                    batch
                )
                batch = []

    # Flush remaining
    if batch:
        cur.executemany(
            "INSERT INTO strings (string_val, file_id, line_no) VALUES (?, ?, ?)",
            batch
        )

    conn.commit()
    insert_time = time.time() - start_time
    print("")
    print("  Bulk insert done in {:.1f}s. Creating indexes...".format(insert_time))

    # Create indexes (much faster after bulk insert)
    index_start = time.time()
    cur.execute("CREATE INDEX idx_string_val ON strings(string_val)")
    cur.execute("CREATE INDEX idx_string_file ON strings(file_id)")
    cur.execute("CREATE INDEX idx_file_module ON files(module)")
    conn.commit()
    index_time = time.time() - index_start
    print("  Indexes created in {:.1f}s.".format(index_time))

    elapsed = time.time() - start_time

    # Store meta
    meta_items = [
        ("timestamp", time.strftime("%Y-%m-%d %H:%M:%S")),
        ("build_time_sec", str(round(elapsed, 1))),
        ("files_scanned", str(len(files_to_scan))),
        ("files_with_strings", str(files_with_strings)),
        ("total_lines", str(total_lines)),
        ("total_strings", str(total_strings)),
        ("unique_strings", str(len(unique_strings))),
        ("min_string_len", str(min_string_len)),
        ("source_root", source_root),
    ]
    cur.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", meta_items)
    conn.commit()

    # Analyze for query optimizer
    cur.execute("ANALYZE")
    conn.commit()

    # Compact the database
    print("  Running VACUUM to compact database...")
    vacuum_start = time.time()
    conn.execute("PRAGMA journal_mode=DELETE")  # VACUUM needs non-WAL mode
    cur.execute("VACUUM")
    conn.commit()
    vacuum_time = time.time() - vacuum_start
    print("  VACUUM done in {:.1f}s.".format(vacuum_time))

    conn.close()

    elapsed = time.time() - start_time
    size_mb = os.path.getsize(db_path) / (1024 * 1024)

    # Reopen for stats queries
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Top string values by frequency
    cur.execute("""
        SELECT string_val, COUNT(*) as cnt
        FROM strings
        GROUP BY string_val
        ORDER BY cnt DESC
        LIMIT 20
    """)
    top_strings = cur.fetchall()

    # Strings per module
    cur.execute("""
        SELECT f.module, COUNT(*) as cnt
        FROM strings s JOIN files f ON s.file_id = f.id
        GROUP BY f.module
        ORDER BY cnt DESC
        LIMIT 15
    """)
    top_modules = cur.fetchall()

    # Category counts
    cur.execute("SELECT COUNT(*) FROM strings WHERE string_val LIKE 'http%'")
    url_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM strings WHERE string_val LIKE '%.%' AND string_val LIKE '%/%'")
    path_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM strings WHERE string_val LIKE '%SELECT %' OR string_val LIKE '%INSERT %' OR string_val LIKE '%UPDATE %' OR string_val LIKE '%DELETE %'")
    sql_count = cur.fetchone()[0]

    conn.close()

    print("")
    print("=" * 60)
    print("STRING INDEX BUILD COMPLETE")
    print("=" * 60)
    print("")
    print("  Files scanned:     {:>10,}".format(len(files_to_scan)))
    print("  Files with strings:{:>10,}".format(files_with_strings))
    print("  Total lines:       {:>10,}".format(total_lines))
    print("  Total strings:     {:>10,}".format(total_strings))
    print("  Unique strings:    {:>10,}".format(len(unique_strings)))
    print("  Database size:     {:>10.1f} MB".format(size_mb))
    print("  Build time:        {:>10.1f}s".format(elapsed))
    print("")
    print("  Categories detected:")
    print("    URLs (http...):    {:>8,}".format(url_count))
    print("    Paths (x/y.z):    {:>8,}".format(path_count))
    print("    SQL statements:   {:>8,}".format(sql_count))
    print("")
    print("  Top 20 most common strings:")
    for sv, cnt in top_strings:
        display = sv if len(sv) <= 50 else sv[:47] + "..."
        print("    {:>6,}x  \"{}\"".format(cnt, display))
    print("")
    print("  Top 15 modules by string count:")
    for mod, cnt in top_modules:
        print("    {:35s}  {:>8,}".format(mod, cnt))
    print("")
    print("  Output: {}".format(db_path))
    print("")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Build string literal index (SQLite) from decompiled sources")
    parser.add_argument(
        "--base-dir", default=None,
        help="Module navigator base directory (default: auto-detect)")
    parser.add_argument(
        "--min-len", type=int, default=2,
        help="Minimum string literal length to index (default: 2)")

    args = parser.parse_args()

    if args.base_dir:
        base_dir = args.base_dir
    else:
        # Auto-detect: script is in tools/, base is parent
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if not os.path.isdir(os.path.join(base_dir, "indexes")):
        print("ERROR: indexes/ directory not found in {}".format(base_dir))
        sys.exit(1)

    build_index(base_dir, min_string_len=args.min_len)


if __name__ == "__main__":
    main()
