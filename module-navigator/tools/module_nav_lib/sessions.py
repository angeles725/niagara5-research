"""
Session Save/Load/Export for Module Navigator (Batch 4, Gap #6).

Wraps bookmarks + history + free-form notes into a named "session" that
persists across Claude sessions. Prevents re-researching from scratch when
a session dies.

Commands:
  session save <name>         Snapshot bookmarks + history + notes
  session load <name>         Restore a saved session as active
  session list                List all saved sessions
  session note <text>         Add a note to the active session
  session export <name>       Export session to stdout
    --as md|json             Format (default: md)
    --out <path>              Write to file instead of stdout
  session delete <name>       Delete a saved session

Storage:
  session/sessions/<name>.json   Saved sessions
  session/active_session.json   Name of currently active session
  session/bookmarks.json         (existing, reused)
  session/history.json           (existing, reused)

Reuses:
  bookmarks._load_bookmarks(), bookmarks._load_history(),
  bookmarks._session_dir()
"""

import json
import os
import time as time_module

# Reuse bookmarks storage helpers
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from module_nav_lib.bookmarks import (
    _load_bookmarks, _save_bookmarks,
    _load_history, _session_dir,
)


# ---------------------------------------------------------------------------
# Active session tracking
# ---------------------------------------------------------------------------

_active_session_cache = None


def _get_active_session_name(base_dir):
    """Return name of active session or None."""
    global _active_session_cache
    if _active_session_cache is not None:
        return _active_session_cache

    sess_dir = os.path.join(_session_dir(base_dir), "sessions")
    active_path = os.path.join(sess_dir, "active_session.json")
    if os.path.isfile(active_path):
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _active_session_cache = data.get("name")
        except Exception:
            _active_session_cache = None
    else:
        _active_session_cache = None
    return _active_session_cache


def _set_active_session(base_dir, name):
    """Set the active session name."""
    global _active_session_cache
    _active_session_cache = name
    sess_dir = os.path.join(_session_dir(base_dir), "sessions")
    os.makedirs(sess_dir, exist_ok=True)
    active_path = os.path.join(sess_dir, "active_session.json")
    try:
        with open(active_path, "w", encoding="utf-8") as f:
            json.dump({"name": name}, f, ensure_ascii=False)
    except Exception as e:
        print("  WARNING: Could not save active session: {}".format(e))


def _clear_active_session(base_dir):
    """Clear the active session."""
    global _active_session_cache
    _active_session_cache = None
    sess_dir = os.path.join(_session_dir(base_dir), "sessions")
    active_path = os.path.join(sess_dir, "active_session.json")
    if os.path.isfile(active_path):
        try:
            os.remove(active_path)
        except Exception:
            pass


def _sessions_dir(base_dir):
    """Return path to session/sessions/ directory."""
    d = os.path.join(_session_dir(base_dir), "sessions")
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Session I/O
# ---------------------------------------------------------------------------

def _load_session(base_dir, name):
    """Load a saved session by name. Returns dict or None."""
    path = os.path.join(_sessions_dir(base_dir), "{}.json".format(name))
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_session(base_dir, name, session_data):
    """Save a session to disk."""
    path = os.path.join(_sessions_dir(base_dir), "{}.json".format(name))
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print("  ERROR: Could not save session: {}".format(e))
        return False


def _session_exists(base_dir, name):
    """Check if a session exists."""
    path = os.path.join(_sessions_dir(base_dir), "{}.json".format(name))
    return os.path.isfile(path)


def _delete_session_file(base_dir, name):
    """Delete a session file."""
    path = os.path.join(_sessions_dir(base_dir), "{}.json".format(name))
    if os.path.isfile(path):
        try:
            os.remove(path)
            return True
        except Exception as e:
            print("  ERROR: Could not delete session: {}".format(e))
            return False
    return True


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_session_save(base_dir, name):
    """Save current bookmarks + history + notes as a named session."""
    if not name:
        print("  Usage: session save <name>")
        return

    # Load current state
    bookmarks = _load_bookmarks(base_dir)
    history = _load_history(base_dir)

    # Load existing session data if it exists (to retain notes)
    existing = _load_session(base_dir, name)
    existing_notes = existing.get("notes", []) if existing else []

    now = time_module.strftime("%Y-%m-%d %H:%M:%S")

    session_data = {
        "name": name,
        "saved_at": now,
        "bookmarks": bookmarks,
        "history": history[-100:],  # Last 100 history entries
        "notes": existing_notes,
        "stats": {
            "bookmark_count": len(bookmarks),
            "history_count": len(history[-100:]),
            "notes_count": len(existing_notes),
        }
    }

    if _save_session(base_dir, name, session_data):
        _set_active_session(base_dir, name)
        print("  Saved session: {} ({} bookmarks, {} history entries, {} notes)".format(
            name, len(bookmarks), len(history[-100:]), len(existing_notes)))
        print("  Active session: {}".format(name))
    print("")


def cmd_session_load(base_dir, name):
    """Restore a saved session as the active session."""
    if not name:
        print("  Usage: session load <name>")
        return

    session_data = _load_session(base_dir, name)
    if session_data is None:
        print("  Session '{}' not found.".format(name))
        # Suggest similar names
        sessions_dir = _sessions_dir(base_dir)
        if os.path.isdir(sessions_dir):
            available = [f[:-5] for f in os.listdir(sessions_dir)
                         if f.endswith(".json") and f != "active_session.json"]
            if available:
                print("  Available sessions: {}".format(", ".join(sorted(available))))
        print("")
        return

    # Restore bookmarks (merge, don't overwrite)
    current_bookmarks = _load_bookmarks(base_dir)
    saved_bookmarks = session_data.get("bookmarks", {})
    # Merge: saved takes priority for same key, current keys preserved
    merged = dict(current_bookmarks)
    merged.update(saved_bookmarks)
    _save_bookmarks(base_dir, merged)

    # Restore history (append, don't truncate current)
    current_history = _load_history(base_dir)
    saved_history = session_data.get("history", [])
    # Deduplicate by timestamp+command to avoid exact duplicates
    existing_keys = {(h.get("timestamp", ""), h.get("command", ""))
                     for h in current_history}
    new_entries = [h for h in saved_history
                   if (h.get("timestamp", ""), h.get("command", "")) not in existing_keys]
    merged_history = current_history + new_entries
    # Re-save via bookmarks helper (it saves history too via record_history pattern)
    # But bookmarks._save_history is internal; we need to save directly
    history_path = os.path.join(_session_dir(base_dir), "history.json")
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(merged_history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("  WARNING: Could not restore history: {}".format(e))

    _set_active_session(base_dir, name)

    stats = session_data.get("stats", {})
    print("  Loaded session: {}".format(name))
    print("  Saved at: {}".format(session_data.get("saved_at", "?")))
    print("  Bookmarks restored: {} (merged with {} current)".format(
        len(saved_bookmarks), len(current_bookmarks)))
    print("  History entries added: {} ({} total now)".format(
        len(new_entries), len(merged_history)))
    print("  Notes: {} total".format(len(session_data.get("notes", []))))
    print("")


def cmd_session_list(base_dir, limit=50):
    """List all saved sessions."""
    sessions_dir = _sessions_dir(base_dir)
    active = _get_active_session_name(base_dir)

    if not os.path.isdir(sessions_dir):
        sessions = []
    else:
        sessions = [f[:-5] for f in os.listdir(sessions_dir)
                   if f.endswith(".json") and f != "active_session.json"]

    if not sessions:
        print("  (no saved sessions)")
        print("")
        print("  Use: session save <name>   to save current session")
        print("")
        return

    # Load metadata for each (without full bookmarks/history)
    session_infos = []
    for name in sessions:
        data = _load_session(base_dir, name)
        if data:
            stats = data.get("stats", {})
            session_infos.append({
                "name": name,
                "saved_at": data.get("saved_at", "?"),
                "bookmarks": stats.get("bookmark_count", "?"),
                "history": stats.get("history_count", "?"),
                "notes": stats.get("notes_count", 0),
            })

    # Sort by saved_at descending
    session_infos.sort(key=lambda x: x["saved_at"], reverse=True)
    if limit:
        session_infos = session_infos[:limit]

    print("")
    print("  SESSIONS ({} total)".format(len(session_infos)))
    print("  {:<30s}  {:<19s}  {:>8s}  {:>7s}  {:>5s}".format(
        "NAME", "SAVED AT", "BOOKMARKS", "HISTORY", "NOTES"))
    print("  " + "-" * 80)

    for s in session_infos:
        marker = "* " if s["name"] == active else "  "
        print("  {}{:<28s}  {:<19s}  {:>8d}  {:>7d}  {:>5d}".format(
            marker, s["name"], s["saved_at"], s["bookmarks"],
            s["history"], s["notes"]))

    if active and active not in [s["name"] for s in session_infos]:
        print("")
        print("  Active session: {} (session file missing)".format(active))

    print("")


def cmd_session_note(base_dir, text):
    """Add a note to the active session."""
    if not text:
        print("  Usage: session note <text>")
        return

    active = _get_active_session_name(base_dir)
    if not active:
        print("  ERROR: No active session.")
        print("  Use 'session save <name>' first to create and activate a session.")
        print("")
        return

    session_data = _load_session(base_dir, active)
    if session_data is None:
        # Session file missing but active flag set — recreate
        session_data = {
            "name": active,
            "saved_at": time_module.strftime("%Y-%m-%d %H:%M:%S"),
            "bookmarks": {},
            "history": [],
            "notes": [],
            "stats": {"bookmark_count": 0, "history_count": 0, "notes_count": 0},
        }

    notes = session_data.get("notes", [])
    now = time_module.strftime("%Y-%m-%d %H:%M:%S")
    notes.append({
        "text": text,
        "timestamp": now,
    })
    session_data["notes"] = notes
    session_data["stats"]["notes_count"] = len(notes)
    session_data["saved_at"] = now

    if _save_session(base_dir, active, session_data):
        print("  Note added to session '{}' ({} notes)".format(active, len(notes)))
    print("")


def cmd_session_export(base_dir, name, fmt="md", out_path=None):
    """Export a session to Markdown or JSON."""
    if not name:
        print("  Usage: session export <name> [--as md|json] [--out <path>]")
        return

    session_data = _load_session(base_dir, name)
    if session_data is None:
        print("  Session '{}' not found.".format(name))
        print("")
        return

    if fmt == "json":
        output = json.dumps(session_data, indent=2, ensure_ascii=False)
    else:
        # Markdown format
        lines = []
        lines.append("# Session: {}".format(name))
        lines.append("")
        lines.append("**Saved:** {}".format(session_data.get("saved_at", "?")))
        lines.append("")

        # Bookmarks section
        bookmarks = session_data.get("bookmarks", {})
        notes = session_data.get("notes", [])
        history = session_data.get("history", [])
        stats = session_data.get("stats", {})

        lines.append("## Bookmarks ({})".format(len(bookmarks)))
        lines.append("")
        if bookmarks:
            items = sorted(bookmarks.items(),
                          key=lambda x: x[1].get("timestamp", ""),
                          reverse=True)
            for cls, info in items:
                note = info.get("note", "")
                ts = info.get("timestamp", "?")
                marker = " [{}]".format(note) if note else ""
                lines.append("- **{}**{} — saved {}".format(cls, marker, ts))
        else:
            lines.append("_(none)_")
        lines.append("")

        # History section
        lines.append("## History ({} entries)".format(len(history)))
        lines.append("")
        if history:
            lines.append("```")
            for h in reversed(history[-50:]):  # Last 50 in reverse (newest first)
                ts = h.get("timestamp", "?")
                cmd = h.get("command", "?")
                lines.append("{}  {}".format(ts, cmd))
            lines.append("```")
        else:
            lines.append("_(none)_")
        lines.append("")

        # Notes section
        lines.append("## Notes ({})".format(len(notes)))
        lines.append("")
        if notes:
            for i, n in enumerate(notes, 1):
                ts = n.get("timestamp", "?")
                text = n.get("text", "")
                lines.append("{}. **{}**  ".format(i, ts))
                lines.append("   {}".format(text))
                lines.append("")
        else:
            lines.append("_(none)_")
        lines.append("")

        # Stats
        lines.append("## Session Stats")
        lines.append("")
        lines.append("- Bookmarks: {}".format(stats.get("bookmark_count", "?")))
        lines.append("- History entries: {}".format(stats.get("history_count", "?")))
        lines.append("- Notes: {}".format(stats.get("notes_count", 0)))
        lines.append("")

        output = "\n".join(lines)

    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(output)
            print("  Exported session '{}' to {}".format(name, out_path))
        except Exception as e:
            print("  ERROR: Could not write to {}: {}".format(out_path, e))
    else:
        print(output)

    print("")


def cmd_session_delete(base_dir, name):
    """Delete a saved session."""
    if not name:
        print("  Usage: session delete <name>")
        return

    if not _session_exists(base_dir, name):
        print("  Session '{}' not found.".format(name))
        print("")
        return

    # Check if it's the active session
    active = _get_active_session_name(base_dir)
    was_active = (name == active)

    if _delete_session_file(base_dir, name):
        if was_active:
            _clear_active_session(base_dir)
        print("  Deleted session: {}".format(name))

        # Count remaining
        sessions_dir = _sessions_dir(base_dir)
        remaining = [f for f in os.listdir(sessions_dir)
                     if f.endswith(".json") and f != "active_session.json"]
        print("  Remaining sessions: {}".format(len(remaining)))
    print("")
