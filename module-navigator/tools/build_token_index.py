#!/usr/bin/env python
"""
Build full-text token index from decompiled Java sources (Phase 18).

Reads class-index.json as a catalog of all top-level .java files,
tokenizes each file by splitting on non-alphanumeric characters,
and produces indexes/token-index.db (SQLite) with:

  files:    (id, path, module, class_name)
  postings: (token, file_id, line_no)
  meta:     (key, value) — build stats

SQLite is used instead of JSON because the inverted index would be
200-500 MB in JSON format — too large to load into memory.

Usage:
  python tools/build_token_index.py [--base-dir DIR] [--min-len N]
"""

import json
import os
import re
import sqlite3
import sys
import time


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

RE_TOKEN_SPLIT = re.compile(r'[^a-zA-Z0-9_]+')

# Decompiler variable pattern: var1, var2, ..., var99, etc.
RE_DECOMPILER_VAR = re.compile(r'^var\d+$')

# Java keywords, literals, and common noise — not useful for code search
STOP_WORDS = frozenset([
    # Java reserved keywords
    'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
    'char', 'class', 'const', 'continue', 'default', 'do', 'double',
    'else', 'enum', 'extends', 'final', 'finally', 'float', 'for',
    'goto', 'if', 'implements', 'import', 'instanceof', 'int',
    'interface', 'long', 'native', 'new', 'package', 'private',
    'protected', 'public', 'return', 'short', 'static', 'strictfp',
    'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
    'transient', 'try', 'void', 'volatile', 'while',
    # Java literals
    'true', 'false', 'null',
    # Very common package segments (appear in every import)
    'com', 'org', 'javax', 'java',
    # Common annotations
    'Override', 'Deprecated', 'SuppressWarnings',
])


def tokenize_line(line):
    """Split a line into tokens, filtering stop-words and noise."""
    tokens = RE_TOKEN_SPLIT.split(line)
    return [t for t in tokens if len(t) >= 2
            and t not in STOP_WORDS
            and not RE_DECOMPILER_VAR.match(t)]


# ---------------------------------------------------------------------------
# Build index
# ---------------------------------------------------------------------------

def build_index(base_dir, min_token_len=2):
    """Build token index from all decompiled sources."""
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

    print("Scanning {} files for tokens...".format(len(files_to_scan)))

    # Create SQLite database
    db_path = os.path.join(base_dir, "indexes", "token-index.db")
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
        CREATE TABLE postings (
            token TEXT NOT NULL,
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
    total_postings = 0
    unique_tokens = set()
    files_with_tokens = 0
    total_lines = 0
    report_interval = 5000
    batch = []
    batch_size = 50000

    for idx, (filepath, rel_path, class_name, module) in enumerate(files_to_scan):
        if (idx + 1) % report_interval == 0:
            elapsed = time.time() - start_time
            print("  {} / {} files ({:.0f}s, {:,} postings)...".format(
                idx + 1, len(files_to_scan), elapsed, total_postings))

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

        file_has_tokens = False
        total_lines += len(lines)

        for line_no, line in enumerate(lines, 1):
            tokens = tokenize_line(line)
            if not tokens:
                continue

            file_has_tokens = True
            seen_on_line = set()  # deduplicate same token on same line
            for token in tokens:
                if len(token) < min_token_len:
                    continue
                if token in seen_on_line:
                    continue
                seen_on_line.add(token)
                unique_tokens.add(token)
                batch.append((token, file_id, line_no))
                total_postings += 1

            # Flush batch
            if len(batch) >= batch_size:
                cur.executemany(
                    "INSERT INTO postings (token, file_id, line_no) VALUES (?, ?, ?)",
                    batch
                )
                batch = []

        if file_has_tokens:
            files_with_tokens += 1

    # Flush remaining
    if batch:
        cur.executemany(
            "INSERT INTO postings (token, file_id, line_no) VALUES (?, ?, ?)",
            batch
        )

    conn.commit()
    insert_time = time.time() - start_time
    print("")
    print("  Bulk insert done in {:.1f}s. Creating indexes...".format(insert_time))

    # Create indexes (much faster after bulk insert)
    index_start = time.time()
    cur.execute("CREATE INDEX idx_token ON postings(token)")
    cur.execute("CREATE INDEX idx_token_module ON postings(token, file_id)")
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
        ("files_with_tokens", str(files_with_tokens)),
        ("total_lines", str(total_lines)),
        ("total_postings", str(total_postings)),
        ("unique_tokens", str(len(unique_tokens))),
        ("min_token_len", str(min_token_len)),
        ("stop_words_count", str(len(STOP_WORDS))),
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

    # Compute some stats
    # Reopen for stats queries
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Top tokens by frequency
    cur.execute("""
        SELECT token, COUNT(*) as cnt
        FROM postings
        GROUP BY token
        ORDER BY cnt DESC
        LIMIT 20
    """)
    top_tokens = cur.fetchall()

    # Tokens per module
    cur.execute("""
        SELECT f.module, COUNT(*) as cnt
        FROM postings p JOIN files f ON p.file_id = f.id
        GROUP BY f.module
        ORDER BY cnt DESC
        LIMIT 15
    """)
    top_modules = cur.fetchall()

    conn.close()

    print("")
    print("=" * 60)
    print("TOKEN INDEX BUILT")
    print("=" * 60)
    print("")
    print("  Files scanned:          {:>10,}".format(len(files_to_scan)))
    print("  Files with tokens:      {:>10,}".format(files_with_tokens))
    print("  Total lines:            {:>10,}".format(total_lines))
    print("  Total postings:         {:>10,}".format(total_postings))
    print("  Unique tokens:          {:>10,}".format(len(unique_tokens)))
    print("  Min token length:       {:>10}".format(min_token_len))
    print("  Build time:             {:>10.1f}s".format(elapsed))
    print("    Insert phase:         {:>10.1f}s".format(insert_time))
    print("    Index phase:          {:>10.1f}s".format(index_time))
    print("  Index size:             {:>10.1f} MB".format(size_mb))
    print("")

    print("  Top 20 tokens by frequency:")
    for token, cnt in top_tokens:
        print("    {:30s}  {:>8,} occurrences".format(token, cnt))
    print("")

    print("  Top 15 modules by postings:")
    for mod, cnt in top_modules:
        print("    {:35s}  {:>10,} postings".format(mod, cnt))
    print("")

    return db_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Build full-text token index from decompiled Java sources")
    parser.add_argument(
        "--base-dir", "-d",
        help="Base directory (auto-detected if omitted)")
    parser.add_argument(
        "--min-len", type=int, default=2,
        help="Minimum token length (default: 2)")
    args = parser.parse_args()

    base_dir = args.base_dir
    if not base_dir:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)

    if not os.path.isdir(os.path.join(base_dir, "indexes")):
        print("ERROR: indexes/ not found in {}".format(base_dir))
        sys.exit(1)

    build_index(base_dir, min_token_len=args.min_len)


if __name__ == "__main__":
    main()
