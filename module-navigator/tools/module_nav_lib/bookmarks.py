"""
Bookmarks & Session commands for Module Navigator (Phase 41).

Commands:
  bookmark <class> [note]    Save a class bookmark with optional note
  bookmarks                  List all bookmarks
    --sort time|name|access  Sort order (default: time)
    -n N                     Limit results
  unbookmark <class>         Remove a bookmark
  history                    Show command history
    -n N                     Limit results (default 50)
    --all                    Show all (up to 500)
    --grep <pattern>         Filter history by pattern

Storage:
  session/bookmarks.json     {class: {note, timestamp, last_accessed, access_count}}
  session/history.json       [{command, timestamp}] (last 500)
"""

import json
import os
import time


# ---------------------------------------------------------------------------
# Session directory
# ---------------------------------------------------------------------------

def _session_dir(base_dir):
    """Return path to session/ directory, creating if needed."""
    d = os.path.join(base_dir, "session")
    if not os.path.isdir(d):
        os.makedirs(d)
    return d


# ---------------------------------------------------------------------------
# Bookmarks storage
# ---------------------------------------------------------------------------

_bookmarks_cache = None


def _load_bookmarks(base_dir):
    """Load bookmarks from session/bookmarks.json."""
    global _bookmarks_cache
    if _bookmarks_cache is not None:
        return _bookmarks_cache

    path = os.path.join(_session_dir(base_dir), "bookmarks.json")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                _bookmarks_cache = json.load(f)
        except Exception:
            _bookmarks_cache = {}
    else:
        _bookmarks_cache = {}
    return _bookmarks_cache


def _save_bookmarks(base_dir, bookmarks):
    """Persist bookmarks to session/bookmarks.json."""
    global _bookmarks_cache
    _bookmarks_cache = bookmarks
    path = os.path.join(_session_dir(base_dir), "bookmarks.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(bookmarks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("  WARNING: Could not save bookmarks: {}".format(e))


# ---------------------------------------------------------------------------
# History storage
# ---------------------------------------------------------------------------

_history_cache = None
MAX_HISTORY = 500


def _load_history(base_dir):
    """Load history from session/history.json."""
    global _history_cache
    if _history_cache is not None:
        return _history_cache

    path = os.path.join(_session_dir(base_dir), "history.json")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                _history_cache = json.load(f)
        except Exception:
            _history_cache = []
    else:
        _history_cache = []
    return _history_cache


def _save_history(base_dir, history):
    """Persist history to session/history.json."""
    global _history_cache
    _history_cache = history
    path = os.path.join(_session_dir(base_dir), "history.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def record_history(base_dir, command):
    """Append a command to the persistent history. Called from REPL loop."""
    history = _load_history(base_dir)
    entry = {
        "command": command,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    history.append(entry)
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    _save_history(base_dir, history)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_bookmark(base_dir, class_name, note=None):
    """Save a class bookmark with optional note."""
    if not class_name:
        print("  Usage: bookmark <class> [note]")
        return

    bookmarks = _load_bookmarks(base_dir)
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    if class_name in bookmarks:
        # Update existing
        bookmarks[class_name]["last_accessed"] = now
        bookmarks[class_name]["access_count"] = bookmarks[class_name].get("access_count", 0) + 1
        if note:
            bookmarks[class_name]["note"] = note
        print("  Updated bookmark: {} (accessed {} times)".format(
            class_name, bookmarks[class_name]["access_count"]))
    else:
        # New bookmark
        bookmarks[class_name] = {
            "note": note or "",
            "timestamp": now,
            "last_accessed": now,
            "access_count": 1,
        }
        print("  Bookmarked: {}".format(class_name))
        if note:
            print("  Note: {}".format(note))

    _save_bookmarks(base_dir, bookmarks)
    print("  Total bookmarks: {}".format(len(bookmarks)))
    print("")


def cmd_bookmarks(base_dir, sort_by="time", limit=None):
    """List all bookmarks."""
    bookmarks = _load_bookmarks(base_dir)

    if not bookmarks:
        print("  (no bookmarks)")
        print("")
        print("  Use: bookmark <class> [note]")
        print("")
        return

    # Sort
    items = list(bookmarks.items())
    if sort_by == "name":
        items.sort(key=lambda x: x[0])
    elif sort_by == "access":
        items.sort(key=lambda x: x[1].get("access_count", 0), reverse=True)
    else:  # time (default) — most recent first
        items.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)

    if limit:
        items = items[:limit]

    print("")
    print("  BOOKMARKS ({} total, sorted by {})".format(len(bookmarks), sort_by))
    print("  {:30s}  {:5s}  {:19s}  {}".format("CLASS", "HITS", "CREATED", "NOTE"))
    print("  " + "-" * 80)

    for cls, info in items:
        note = info.get("note", "") or ""
        ts = info.get("timestamp", "?")
        hits = info.get("access_count", 0)
        # Truncate note if too long
        if len(note) > 30:
            note = note[:27] + "..."
        print("  {:30s}  {:>5d}  {:19s}  {}".format(cls, hits, ts, note))

    print("")


def cmd_unbookmark(base_dir, class_name):
    """Remove a bookmark."""
    if not class_name:
        print("  Usage: unbookmark <class>")
        return

    bookmarks = _load_bookmarks(base_dir)

    if class_name in bookmarks:
        note = bookmarks[class_name].get("note", "")
        del bookmarks[class_name]
        _save_bookmarks(base_dir, bookmarks)
        print("  Removed bookmark: {}".format(class_name))
        if note:
            print("  (was: {})".format(note))
        print("  Remaining bookmarks: {}".format(len(bookmarks)))
    else:
        print("  Bookmark '{}' not found.".format(class_name))
        if bookmarks:
            # Fuzzy match
            matches = [k for k in bookmarks if class_name.lower() in k.lower()]
            if matches:
                print("  Did you mean: {}".format(", ".join(matches)))
    print("")


def cmd_history(base_dir, limit=50, show_all=False, grep_pattern=None):
    """Show command history."""
    history = _load_history(base_dir)

    if not history:
        print("  (no history)")
        print("")
        return

    items = history[:]

    # Filter by pattern
    if grep_pattern:
        items = [h for h in items if grep_pattern.lower() in h["command"].lower()]
        if not items:
            print("  No history matching '{}'.".format(grep_pattern))
            print("")
            return

    # Limit
    if show_all:
        display = items
    else:
        display = items[-limit:]

    start_idx = len(items) - len(display)

    print("")
    print("  COMMAND HISTORY ({} of {} entries{})".format(
        len(display), len(items),
        ", filter='{}'".format(grep_pattern) if grep_pattern else ""))
    print("  {:>5s}  {:19s}  {}".format("#", "TIMESTAMP", "COMMAND"))
    print("  " + "-" * 70)

    for i, entry in enumerate(display):
        idx = start_idx + i + 1
        ts = entry.get("timestamp", "?")
        cmd = entry.get("command", "?")
        print("  {:>5d}  {:19s}  {}".format(idx, ts, cmd))

    print("")


# ---------------------------------------------------------------------------
# Bookmark resolution (for REPL @reference expansion)
# ---------------------------------------------------------------------------

def resolve_bookmark_refs(base_dir, line):
    """Replace @bookmarkName references in a command line.

    Returns (resolved_line, was_resolved).
    """
    bookmarks = _load_bookmarks(base_dir)
    if not bookmarks:
        return line, False

    resolved = False
    for cls in bookmarks:
        ref = "@" + cls
        if ref in line:
            line = line.replace(ref, cls)
            # Update last_accessed
            bookmarks[cls]["last_accessed"] = time.strftime("%Y-%m-%d %H:%M:%S")
            bookmarks[cls]["access_count"] = bookmarks[cls].get("access_count", 0) + 1
            resolved = True

    if resolved:
        _save_bookmarks(base_dir, bookmarks)

    return line, resolved


# ---------------------------------------------------------------------------
# Migration: convert old bookmarks.json (name->class) to new format
# ---------------------------------------------------------------------------

def migrate_old_bookmarks(base_dir):
    """Migrate old-style bookmarks.json (in base_dir root) to session/ format."""
    old_path = os.path.join(base_dir, "bookmarks.json")
    if not os.path.isfile(old_path):
        return 0

    try:
        with open(old_path, "r", encoding="utf-8") as f:
            old_data = json.load(f)
    except Exception:
        return 0

    if not old_data or not isinstance(old_data, dict):
        return 0

    # Check if it's old format (values are plain strings, not dicts)
    first_val = next(iter(old_data.values()))
    if isinstance(first_val, dict):
        return 0  # Already new format

    bookmarks = _load_bookmarks(base_dir)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    migrated = 0

    for name, class_val in old_data.items():
        # Old format: bookmark name -> class name
        # New format: class name -> {note, timestamp, ...}
        if class_val not in bookmarks:
            bookmarks[class_val] = {
                "note": "migrated from '{}'".format(name),
                "timestamp": now,
                "last_accessed": now,
                "access_count": 1,
            }
            migrated += 1

    if migrated > 0:
        _save_bookmarks(base_dir, bookmarks)
        # Rename old file
        try:
            os.rename(old_path, old_path + ".bak")
        except Exception:
            pass

    return migrated
