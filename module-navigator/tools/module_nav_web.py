#!/usr/bin/env python
"""
Module Navigator - Web Dashboard (Phase 32, FINAL PHASE).

Exposes Module Navigator commands through a local HTTP server with a
browser-based dark-themed UI. Reads the same indexes as the CLI — no data
duplication.

Usage:
  python tools/module_nav_web.py [--port 8042] [--host 127.0.0.1]

Then open: http://localhost:8042

Endpoints:
  GET /                           HTML dashboard (index.html)
  GET /static/<file>              Static assets (CSS/JS)
  GET /api/stats                  Corpus statistics
  GET /api/modules                List modules (query: type, zkm, has_code)
  GET /api/module/<name>          Module detail
  GET /api/autocomplete?q=...     Class name prefix suggestions (max 20)
  GET /api/search?q=...&limit=N   Class search (glob-aware)
  GET /api/class/<name>           Class profile (class + source + UI + module)
  GET /api/unified?q=...&limit=N  Help + Module + BOG unified search
  GET /api/compare/<class>        Side-by-side comparison (text output)
  GET /api/ping                   Health check

Design:
  - Stdlib http.server only — no Flask/deps.
  - Direct data helpers for fast endpoints (search, modules, unified).
  - Stdout capture for rich text endpoints (profile, compare, stats).
  - ES5-compatible frontend (var, no arrows, no template literals).
"""

import argparse
import contextlib
import fnmatch
import io
import json
import os
import re
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Ensure module_nav_lib is on sys.path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from module_nav_lib.inventory import (
    load_inventory,
    cmd_stats,
)
from module_nav_lib.class_search import load_class_index
from module_nav_lib.profile import cmd_profile
from module_nav_lib.unified import (
    cmd_compare,
    _search_help,
    _search_module_nav,
    _search_bog,
    _detect_help_dir,
    _load_bog,
)

# ---------------------------------------------------------------------------
# Globals — set at server start
# ---------------------------------------------------------------------------

BASE_DIR = None
WEB_ROOT = None  # tools/web/

# Caches
_class_names_cache = None  # sorted list of top-level class names
_inventory_cache = None


# ---------------------------------------------------------------------------
# Utility: stdout capture
# ---------------------------------------------------------------------------

def _capture(func, *args, **kwargs):
    """Run a cmd_* function that prints to stdout, return the captured text."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            func(*args, **kwargs)
        except Exception as exc:
            return "ERROR: {}\n".format(exc)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Data helpers (direct — no stdout capture)
# ---------------------------------------------------------------------------

def _get_inventory():
    global _inventory_cache
    if _inventory_cache is None:
        _inventory_cache = load_inventory(BASE_DIR)
    return _inventory_cache


def _get_class_names():
    """Return cached sorted list of top-level class names."""
    global _class_names_cache
    if _class_names_cache is not None:
        return _class_names_cache
    ci = load_class_index(BASE_DIR)
    if not ci:
        _class_names_cache = []
        return _class_names_cache
    names = []
    for cname, entries in ci.get("classes", {}).items():
        # Only top-level (not inner)
        for e in entries:
            if e.get("outer_class") is None:
                names.append(cname)
                break
    names.sort(key=lambda n: n.lower())
    _class_names_cache = names
    return names


def data_stats():
    """Return corpus stats dict (captured via cmd_stats --json)."""
    text = _capture(cmd_stats, BASE_DIR, as_json=True)
    try:
        return json.loads(text)
    except Exception:
        return {"error": "could not parse stats", "raw": text[:500]}


def data_modules(type_filter=None, zkm_only=False, has_code=None, limit=None):
    """Return list of modules with filters."""
    data = _get_inventory()
    if not data:
        return {"error": "inventory not available", "modules": []}
    inv = data["modules"]
    results = []
    for name, v in inv.items():
        if type_filter:
            mt = v["type"] if v["type"] else "standalone"
            if mt != type_filter:
                continue
        if zkm_only and not v["zkm"]:
            continue
        if has_code is True and not v["has_code"]:
            continue
        if has_code is False and v["has_code"]:
            continue
        results.append({
            "name": name,
            "type": v["type"] or "standalone",
            "module": v["module"],
            "has_code": v["has_code"],
            "java_files": v["java_files"],
            "class_count": v["class_count"],
            "zkm": v["zkm"],
            "bytecode": v["bytecode"] or 0,
            "jar": v["jar"],
        })
    results.sort(key=lambda x: x["name"])
    if limit:
        results = results[:limit]
    return {
        "total": len(results),
        "modules": results,
    }


def data_module(name):
    """Return detailed info for a specific module (exact or partial)."""
    data = _get_inventory()
    if not data:
        return {"error": "inventory not available"}
    inv = data["modules"]
    if name in inv:
        v = inv[name]
        return {
            "name": name,
            "parent": v["module"],
            "type": v["type"] or "standalone",
            "jar": v["jar"],
            "has_code": v["has_code"],
            "class_count": v["class_count"],
            "java_files": v["java_files"],
            "zkm": v["zkm"],
            "bytecode": v["bytecode"] or 0,
            "has_vineflower": v.get("has_vineflower", False),
            "packages": v.get("packages", []),
            "third_party": v.get("third_party", []),
        }
    # Partial match
    lower = name.lower()
    matches = [k for k in inv if lower in k.lower()]
    if not matches:
        return {"error": "module '{}' not found".format(name)}
    if len(matches) == 1:
        return data_module(matches[0])
    return {
        "matches": [
            {
                "name": m,
                "type": inv[m]["type"] or "-",
                "java_files": inv[m]["java_files"],
                "zkm": inv[m]["zkm"],
            }
            for m in sorted(matches)[:50]
        ],
        "match_count": len(matches),
    }


def data_autocomplete(q, limit=20):
    """Prefix + substring match for class names."""
    if not q:
        return []
    names = _get_class_names()
    q_lower = q.lower()
    prefix = []
    substring = []
    for n in names:
        nl = n.lower()
        if nl.startswith(q_lower):
            prefix.append(n)
            if len(prefix) >= limit:
                break
        elif q_lower in nl and len(substring) < limit:
            substring.append(n)
    out = prefix[:limit]
    if len(out) < limit:
        out.extend(substring[: limit - len(out)])
    return out


def data_search(pattern, limit=50):
    """Glob-style class search."""
    ci = load_class_index(BASE_DIR)
    if not ci:
        return {"error": "class-index not available", "matches": []}
    classes = ci.get("classes", {})
    # If pattern has no glob chars, do a substring search
    if "*" not in pattern and "?" not in pattern:
        pat_lower = pattern.lower()
        def match(n):
            return pat_lower in n.lower()
    else:
        pat_lower = pattern.lower()
        def match(n):
            return fnmatch.fnmatch(n.lower(), pat_lower)

    matches = []
    for cname, entries in classes.items():
        if not match(cname):
            continue
        for e in entries:
            matches.append({
                "name": cname,
                "package": e.get("package", ""),
                "module": e.get("module", ""),
                "kind": e.get("kind", ""),
                "lines": e.get("lines", 0),
                "zkm": e.get("zkm", False),
                "outer_class": e.get("outer_class"),
            })
    matches.sort(key=lambda x: (x["name"].lower(), x["module"]))
    kinds = {}
    for m in matches:
        kinds[m["kind"]] = kinds.get(m["kind"], 0) + 1
    return {
        "pattern": pattern,
        "total": len(matches),
        "shown": min(limit, len(matches)),
        "kinds": kinds,
        "matches": matches[:limit],
    }


def data_class_profile(class_name):
    """Return rich profile — combines class-index, inheritance, module."""
    ci = load_class_index(BASE_DIR)
    if not ci:
        return {"error": "class-index not available"}
    classes = ci.get("classes", {})
    entries = classes.get(class_name)
    resolved = class_name
    if not entries:
        # Case-insensitive
        for k, v in classes.items():
            if k.lower() == class_name.lower():
                resolved = k
                entries = v
                break
    if not entries:
        return {"error": "class '{}' not found".format(class_name)}

    # Prefer top-level
    entry = None
    for e in entries:
        if e.get("outer_class") is None:
            entry = e
            break
    if entry is None:
        entry = entries[0]

    # Module context
    inv_data = _get_inventory()
    mod_ctx = None
    if inv_data:
        mod = inv_data["modules"].get(entry["module"])
        if mod:
            mod_ctx = {
                "name": entry["module"],
                "type": mod["type"] or "standalone",
                "jar": mod["jar"],
                "java_files": mod["java_files"],
                "class_count": mod["class_count"],
                "zkm": mod["zkm"],
                "third_party": mod.get("third_party", []),
            }

    # Source snippet (first 60 lines) if available
    source_root = ci.get("_meta", {}).get("source", "")
    source_preview = None
    source_lines = 0
    if source_root:
        full_path = os.path.join(source_root, entry["path"])
        if os.path.isfile(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                source_lines = len(lines)
                source_preview = "".join(lines[:80])
            except Exception:
                pass

    # UI (swing-index)
    ui_rec = None
    si_path = os.path.join(BASE_DIR, "indexes", "swing-index.json")
    if os.path.isfile(si_path):
        try:
            with open(si_path, "r", encoding="utf-8") as f:
                si_data = json.load(f)
            si_classes = si_data.get("classes", {})
            if resolved in si_classes:
                val = si_classes[resolved]
                ui_rec = val[0] if isinstance(val, list) else val
        except Exception:
            pass

    # Full-profile text (captured)
    profile_text = _capture(cmd_profile, BASE_DIR, resolved)

    return {
        "name": resolved,
        "package": entry["package"],
        "module": entry["module"],
        "kind": entry["kind"],
        "modifiers": entry["modifiers"],
        "extends": entry.get("extends"),
        "implements": entry.get("implements", []),
        "lines": entry["lines"],
        "zkm": entry["zkm"],
        "path": entry["path"],
        "inner_classes": entry.get("inner_classes", []),
        "outer_class": entry.get("outer_class"),
        "all_entries": len(entries),
        "module_context": mod_ctx,
        "source_total_lines": source_lines,
        "source_preview": source_preview,
        "ui": ui_rec,
        "profile_text": profile_text,
    }


def data_unified(query, limit=10):
    """Help + Module + BOG unified search."""
    help_dir = _detect_help_dir(BASE_DIR)
    help_results = _search_help(help_dir, query, limit) if help_dir else []
    module_results = _search_module_nav(BASE_DIR, query, limit)
    bog_results = _search_bog(BASE_DIR, query, None, limit)
    bog_data, bog_path = _load_bog(BASE_DIR, None)

    return {
        "query": query,
        "sources": {
            "help": help_dir is not None,
            "module": True,
            "bog": bog_data is not None,
        },
        "help_dir": help_dir,
        "bog_path": bog_path,
        "totals": {
            "help": len(help_results),
            "module": len(module_results),
            "bog": len(bog_results),
            "total": len(help_results) + len(module_results) + len(bog_results),
        },
        "help": help_results,
        "module": module_results,
        "bog": bog_results,
    }


def data_compare(class_name):
    """Text output of compare (captured)."""
    text = _capture(cmd_compare, BASE_DIR, class_name)
    return {"class": class_name, "text": text}


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    # Silence default access logs (too chatty for a local tool)
    def log_message(self, format, *args):  # noqa: A002 — stdlib signature
        sys.stderr.write("[web] {} - {}\n".format(self.address_string(), format % args))

    # -------- helpers --------
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, relpath):
        # Guard traversal
        safe = os.path.normpath(relpath).lstrip(os.sep).replace("\\", "/")
        if ".." in safe.split("/"):
            self.send_error(403, "forbidden")
            return
        full = os.path.join(WEB_ROOT, safe)
        if not os.path.isfile(full):
            self.send_error(404, "not found: {}".format(relpath))
            return
        ext = os.path.splitext(full)[1].lower()
        mime = _MIME.get(ext, "application/octet-stream")
        try:
            with open(full, "rb") as f:
                body = f.read()
        except Exception as exc:
            self.send_error(500, "read error: {}".format(exc))
            return
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _query(self):
        """Parse query string into flat dict."""
        pr = urllib.parse.urlparse(self.path)
        return urllib.parse.parse_qs(pr.query), pr.path

    # -------- routing --------
    def do_GET(self):  # noqa: N802 — stdlib signature
        try:
            qs, path = self._query()
        except Exception:
            self.send_error(400, "bad request")
            return

        # Static / index
        if path == "/" or path == "/index.html":
            self._send_static("index.html")
            return

        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            self._send_static(rel)
            return

        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if path == "/api/ping":
            self._send_json({
                "ok": True,
                "base_dir": BASE_DIR,
                "has_indexes": os.path.isdir(os.path.join(BASE_DIR, "indexes")),
            })
            return

        # ---- API routes ----
        try:
            if path == "/api/stats":
                self._send_json(data_stats())
                return

            if path == "/api/modules":
                tf = (qs.get("type") or [None])[0]
                zkm = (qs.get("zkm") or ["0"])[0] in ("1", "true", "yes")
                hc_raw = (qs.get("has_code") or [None])[0]
                has_code = None
                if hc_raw is not None:
                    has_code = hc_raw in ("1", "true", "yes")
                limit_raw = (qs.get("limit") or [None])[0]
                limit = int(limit_raw) if limit_raw else None
                self._send_json(data_modules(tf, zkm, has_code, limit))
                return

            m = re.match(r"^/api/module/(.+)$", path)
            if m:
                name = urllib.parse.unquote(m.group(1))
                self._send_json(data_module(name))
                return

            if path == "/api/autocomplete":
                q = (qs.get("q") or [""])[0]
                limit = int((qs.get("limit") or ["20"])[0])
                self._send_json({"q": q, "results": data_autocomplete(q, limit)})
                return

            if path == "/api/search":
                q = (qs.get("q") or [""])[0]
                limit = int((qs.get("limit") or ["50"])[0])
                if not q:
                    self._send_json({"error": "missing q", "matches": []})
                    return
                self._send_json(data_search(q, limit))
                return

            m = re.match(r"^/api/class/(.+)$", path)
            if m:
                name = urllib.parse.unquote(m.group(1))
                self._send_json(data_class_profile(name))
                return

            if path == "/api/unified":
                q = (qs.get("q") or [""])[0]
                limit = int((qs.get("limit") or ["10"])[0])
                if not q:
                    self._send_json({"error": "missing q"})
                    return
                self._send_json(data_unified(q, limit))
                return

            m = re.match(r"^/api/compare/(.+)$", path)
            if m:
                name = urllib.parse.unquote(m.group(1))
                self._send_json(data_compare(name))
                return

            self.send_error(404, "unknown path: {}".format(path))
        except Exception as exc:
            import traceback
            tb = traceback.format_exc()
            self._send_json({"error": str(exc), "trace": tb}, status=500)


def _banner(host, port):
    bar = "=" * 64
    print(bar)
    print("  MODULE NAVIGATOR — WEB DASHBOARD (F32)")
    print(bar)
    print("  Base dir:  {}".format(BASE_DIR))
    print("  Web root:  {}".format(WEB_ROOT))
    print("  URL:       http://{}:{}".format(host, port))
    print("  Ctrl+C to stop")
    print(bar)


def _detect_base_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.dirname(script_dir)  # tools/ -> module-navigator/
    if os.path.isdir(os.path.join(candidate, "indexes")):
        return candidate
    return None


def main():
    global BASE_DIR, WEB_ROOT

    parser = argparse.ArgumentParser(
        prog="module_nav_web",
        description="Module Navigator Web Dashboard (F32)",
    )
    parser.add_argument("--port", "-p", type=int, default=8042,
                        help="HTTP port (default 8042)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bind host (default 127.0.0.1)")
    parser.add_argument("--base-dir", "-d",
                        help="Base dir (auto-detected if omitted)")
    parser.add_argument("--web-root",
                        help="Frontend dir (default: tools/web)")
    args = parser.parse_args()

    BASE_DIR = args.base_dir or _detect_base_dir()
    if not BASE_DIR:
        sys.stderr.write("ERROR: could not detect module-navigator base dir\n")
        sys.exit(1)

    WEB_ROOT = args.web_root or os.path.join(_THIS_DIR, "web")
    if not os.path.isdir(WEB_ROOT):
        sys.stderr.write("ERROR: web root not found: {}\n".format(WEB_ROOT))
        sys.exit(1)

    _banner(args.host, args.port)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("Stopping server...")
        server.server_close()


if __name__ == "__main__":
    main()
