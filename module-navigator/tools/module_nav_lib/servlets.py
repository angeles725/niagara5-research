"""
Servlet & Web Route Index commands for Module Navigator (Phase 33).

Detects BWebServlet/HttpServlet descendants, parses doGet/doPost/doPut/doDelete,
extracts getServletPath(), maps HTTP routes -> servlet -> method.

Uses inheritance.json + method-index.json + string-index.db on-demand. No builder.

Commands:
  servlets [--module mod] [-n N]    List all servlets with their routes
  routes [--verb GET|POST] [-n N]   Map HTTP routes -> servlet -> method
    [--module mod]
  servlet <class>                   Detail: route, verbs, params, ancestors
"""

import json
import os
import re
import sqlite3


# ---------------------------------------------------------------------------
# Index loaders (lazy, cached)
# ---------------------------------------------------------------------------

_inheritance_cache = None
_method_index_cache = None
_class_index_cache = None
_string_db_conn = None


def _load_inheritance(base_dir):
    """Load inheritance.json (cached)."""
    global _inheritance_cache
    if _inheritance_cache is not None:
        return _inheritance_cache

    path = os.path.join(base_dir, "indexes", "inheritance.json")
    if not os.path.isfile(path):
        print("ERROR: inheritance.json not found.")
        return None

    with open(path, "r", encoding="utf-8") as f:
        _inheritance_cache = json.load(f)
    return _inheritance_cache


def _load_method_index(base_dir):
    """Load method-index.json (cached)."""
    global _method_index_cache
    if _method_index_cache is not None:
        return _method_index_cache

    path = os.path.join(base_dir, "indexes", "method-index.json")
    if not os.path.isfile(path):
        print("ERROR: method-index.json not found.")
        return None

    with open(path, "r", encoding="utf-8") as f:
        _method_index_cache = json.load(f)
    return _method_index_cache


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
        return None

    _string_db_conn = sqlite3.connect(db_path)
    _string_db_conn.execute("PRAGMA query_only=ON")
    _string_db_conn.execute("PRAGMA cache_size=-16000")
    return _string_db_conn


# ---------------------------------------------------------------------------
# Servlet detection helpers
# ---------------------------------------------------------------------------

# Ancestor classes that indicate a servlet
_SERVLET_ANCESTORS = frozenset([
    "BWebServlet", "HttpServlet", "BServletView", "GenericServlet",
])

# HTTP verb methods (Niagara WebOp and standard Servlet patterns)
_VERB_METHODS = frozenset([
    "doGet", "doPost", "doPut", "doDelete", "service",
])


def _find_all_servlets(base_dir):
    """Find all classes that descend from servlet-related base classes.

    Returns dict: class_name -> {module, ancestors, kind}
    where kind is 'BWebServlet', 'HttpServlet', 'BServletView', or 'GenericServlet'.
    """
    inh = _load_inheritance(base_dir)
    if not inh:
        return {}

    ctc = inh.get("class_to_chain", {})
    ci = _load_class_index(base_dir)
    classes_map = ci.get("classes", {}) if ci else {}

    servlets = {}
    for cls, chain in ctc.items():
        for ancestor in _SERVLET_ANCESTORS:
            if ancestor in chain:
                # Determine module from class-index
                module = "unknown"
                entries = classes_map.get(cls, [])
                if entries:
                    module = entries[0].get("module", "unknown")

                servlets[cls] = {
                    "module": module,
                    "ancestors": chain[:5],
                    "kind": ancestor,
                }
                break

    return servlets


def _get_verb_methods(base_dir, class_name):
    """Get HTTP verb methods implemented by a class.

    Returns list of {verb, signature, line, module}.
    """
    mi = _load_method_index(base_dir)
    if not mi:
        return []

    methods_idx = mi.get("methods", {})
    results = []

    for verb_method in _VERB_METHODS:
        entries = methods_idx.get(verb_method, [])
        for entry in entries:
            if entry.get("class") == class_name:
                sig = entry.get("signature", "")
                # Determine HTTP verb from method name + signature
                if verb_method == "service":
                    verb = "SERVICE"
                elif verb_method == "doGet":
                    verb = "GET"
                elif verb_method == "doPost":
                    verb = "POST"
                elif verb_method == "doPut":
                    verb = "PUT"
                elif verb_method == "doDelete":
                    verb = "DELETE"
                else:
                    verb = verb_method.upper()

                # Only count servlet-relevant overrides (WebOp or HttpServletRequest)
                if "WebOp" in sig or "HttpServlet" in sig or "Servlet" in sig:
                    results.append({
                        "verb": verb,
                        "signature": sig,
                        "line": entry.get("line", 0),
                        "module": entry.get("module", "unknown"),
                    })

    return results


def _get_servlet_path(base_dir, class_name):
    """Extract servlet path for a class from string-index.db and method-index.

    Looks for getServletPath() return values and string literals that look like paths.
    """
    paths = []

    # 1) Check method-index for getServletPath
    mi = _load_method_index(base_dir)
    if mi:
        methods_idx = mi.get("methods", {})
        for mname in ("getServletPath", "getModuleName", "getServletName"):
            entries = methods_idx.get(mname, [])
            for entry in entries:
                if entry.get("class") == class_name:
                    paths.append({"method": mname, "module": entry.get("module", "")})

    # 2) Check string-index.db for path-like strings in the class
    conn = _get_string_db(base_dir)
    if conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.string_val, s.line_no
            FROM strings s JOIN files f ON s.file_id = f.id
            WHERE f.class_name = ?
            AND (
                s.string_val LIKE '/%'
                OR s.string_val LIKE 'servlet%'
                OR s.string_val LIKE '%Servlet%'
            )
            AND length(s.string_val) BETWEEN 2 AND 80
            ORDER BY s.line_no
        """, (class_name,))
        for row in cur.fetchall():
            val = row[0]
            # Filter out common false positives
            if val.startswith("/") or "servlet" in val.lower():
                paths.append({"string": val, "line": row[1]})

    return paths


def _get_parameters(base_dir, class_name):
    """Extract getParameter("...") calls from string-index.db for a class."""
    conn = _get_string_db(base_dir)
    if not conn:
        return []

    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT s.string_val, s.line_no
        FROM strings s JOIN files f ON s.file_id = f.id
        WHERE f.class_name = ?
        AND length(s.string_val) BETWEEN 1 AND 60
        ORDER BY s.line_no
    """, (class_name,))

    # Heuristic: short strings in servlet classes are likely parameter names
    params = []
    for row in cur.fetchall():
        val = row[0]
        # Skip strings that are clearly not parameter names
        if len(val) > 50 or " " in val or val.startswith("/") or val.startswith("javax."):
            continue
        if val.startswith("\"") or val.startswith("'"):
            continue
        # Keep likely parameter names (alphanumeric, dots, dashes, underscores)
        if re.match(r'^[a-zA-Z][a-zA-Z0-9._-]*$', val) and len(val) <= 40:
            params.append({"name": val, "line": row[1]})

    return params


# ---------------------------------------------------------------------------
# cmd_servlets — List all servlets with their routes
# ---------------------------------------------------------------------------

def cmd_servlets(base_dir, module_filter=None, limit=50):
    """List all web servlets detected in the corpus."""
    servlets = _find_all_servlets(base_dir)
    if not servlets:
        print("  No servlets found.")
        return

    # Apply module filter
    if module_filter:
        servlets = {k: v for k, v in servlets.items()
                    if v["module"] == module_filter}
        if not servlets:
            print("  No servlets found in module '{}'.".format(module_filter))
            return

    # Enrich with verb info
    enriched = []
    for cls, info in sorted(servlets.items()):
        verbs = _get_verb_methods(base_dir, cls)
        verb_names = sorted(set(v["verb"] for v in verbs))
        enriched.append({
            "class": cls,
            "module": info["module"],
            "kind": info["kind"],
            "verbs": verb_names,
        })

    # Group by kind for summary
    by_kind = {}
    by_module = {}
    for e in enriched:
        by_kind.setdefault(e["kind"], []).append(e)
        by_module.setdefault(e["module"], []).append(e)

    scope = " in {}".format(module_filter) if module_filter else ""
    print("")
    print("  SERVLETS{} ({:,} classes, {:,} modules)".format(
        scope, len(enriched), len(by_module)))
    print("")

    # Summary by type
    print("  By ancestor type:")
    for kind in sorted(by_kind.keys()):
        items = by_kind[kind]
        with_verbs = sum(1 for e in items if e["verbs"])
        print("    {:20s}  {:>4d} classes  ({:d} with HTTP handlers)".format(
            kind, len(items), with_verbs))
    print("")

    # Table header
    print("  {:40s}  {:25s}  {:20s}  {}".format(
        "CLASS", "MODULE", "TYPE", "VERBS"))
    print("  " + "-" * 105)

    shown = 0
    for e in enriched:
        if shown >= limit:
            remaining = len(enriched) - shown
            print("  ... and {:,} more (use -n {:,} to see all)".format(
                remaining, len(enriched)))
            break

        verbs_str = ", ".join(e["verbs"]) if e["verbs"] else "-"
        cls_display = e["class"] if len(e["class"]) <= 40 else e["class"][:37] + "..."
        mod_display = e["module"] if len(e["module"]) <= 25 else e["module"][:22] + "..."
        print("  {:40s}  {:25s}  {:20s}  {}".format(
            cls_display, mod_display, e["kind"], verbs_str))
        shown += 1

    print("")

    # Module summary
    print("  Top modules by servlet count:")
    top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:10]
    for mod, items in top_mods:
        print("    {:30s}  {:>4d} servlets".format(mod, len(items)))
    print("")


# ---------------------------------------------------------------------------
# cmd_routes — Map HTTP routes -> servlet -> method
# ---------------------------------------------------------------------------

def cmd_routes(base_dir, verb_filter=None, module_filter=None, limit=50):
    """Map HTTP verbs to servlet classes and their handler methods."""
    servlets = _find_all_servlets(base_dir)
    if not servlets:
        print("  No servlets found.")
        return

    if module_filter:
        servlets = {k: v for k, v in servlets.items()
                    if v["module"] == module_filter}

    # Collect all verb implementations
    routes = []
    for cls, info in sorted(servlets.items()):
        verbs = _get_verb_methods(base_dir, cls)
        for v in verbs:
            routes.append({
                "class": cls,
                "module": info["module"],
                "kind": info["kind"],
                "verb": v["verb"],
                "signature": v["signature"],
                "line": v["line"],
            })

    if verb_filter:
        verb_upper = verb_filter.upper()
        routes = [r for r in routes if r["verb"] == verb_upper]

    if not routes:
        msg = "  No routes found"
        if verb_filter:
            msg += " for verb '{}'".format(verb_filter.upper())
        if module_filter:
            msg += " in module '{}'".format(module_filter)
        print(msg + ".")
        return

    # Group by verb
    by_verb = {}
    by_module = {}
    for r in routes:
        by_verb.setdefault(r["verb"], []).append(r)
        by_module.setdefault(r["module"], []).append(r)

    scope_parts = []
    if verb_filter:
        scope_parts.append(verb_filter.upper())
    if module_filter:
        scope_parts.append(module_filter)
    scope = " [{}]".format(", ".join(scope_parts)) if scope_parts else ""

    print("")
    print("  ROUTES{} ({:,} handlers, {:,} classes, {:,} modules)".format(
        scope, len(routes), len(set(r["class"] for r in routes)), len(by_module)))
    print("")

    # Summary by verb
    print("  By HTTP verb:")
    for verb in sorted(by_verb.keys()):
        print("    {:10s}  {:>4d} handlers".format(verb, len(by_verb[verb])))
    print("")

    # Table
    print("  {:8s}  {:35s}  {:25s}  {:>5s}  {}".format(
        "VERB", "CLASS", "MODULE", "LINE", "SIGNATURE"))
    print("  " + "-" * 115)

    shown = 0
    for r in sorted(routes, key=lambda x: (x["verb"], x["class"])):
        if shown >= limit:
            remaining = len(routes) - shown
            print("  ... and {:,} more (use -n {:,} to see all)".format(
                remaining, len(routes)))
            break

        cls_display = r["class"] if len(r["class"]) <= 35 else r["class"][:32] + "..."
        mod_display = r["module"] if len(r["module"]) <= 25 else r["module"][:22] + "..."
        sig_display = r["signature"] if len(r["signature"]) <= 60 else r["signature"][:57] + "..."
        print("  {:8s}  {:35s}  {:25s}  {:>5d}  {}".format(
            r["verb"], cls_display, mod_display, r["line"], sig_display))
        shown += 1

    print("")

    # Module breakdown
    if len(by_module) > 1:
        print("  Top modules:")
        top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:10]
        for mod, items in top_mods:
            verb_set = sorted(set(r["verb"] for r in items))
            print("    {:30s}  {:>3d} handlers  [{}]".format(
                mod, len(items), ", ".join(verb_set)))
        print("")


# ---------------------------------------------------------------------------
# cmd_servlet — Detailed view for a single servlet class
# ---------------------------------------------------------------------------

def cmd_servlet(base_dir, class_name):
    """Show detailed information for a specific servlet class."""
    # Find the class in servlet detection
    servlets = _find_all_servlets(base_dir)

    # Support partial/fuzzy match
    target = None
    if class_name in servlets:
        target = class_name
    else:
        # Case-insensitive partial match
        matches = [k for k in servlets if class_name.lower() in k.lower()]
        if len(matches) == 1:
            target = matches[0]
        elif len(matches) > 1:
            print("")
            print("  Multiple matches for '{}'".format(class_name))
            for m in sorted(matches)[:20]:
                print("    {}  ({})".format(m, servlets[m]["module"]))
            if len(matches) > 20:
                print("    ... and {} more".format(len(matches) - 20))
            print("")
            return
        else:
            # Maybe it's a valid class but not detected as servlet — check class-index
            ci = _load_class_index(base_dir)
            classes_map = ci.get("classes", {}) if ci else {}
            if class_name in classes_map:
                print("")
                print("  '{}' exists but is NOT a servlet descendant.".format(class_name))
                entries = classes_map[class_name]
                if entries:
                    chain_info = ""
                    inh = _load_inheritance(base_dir)
                    if inh:
                        ctc = inh.get("class_to_chain", {})
                        if class_name in ctc:
                            chain_info = " -> ".join(ctc[class_name][:5])
                    print("  Module: {}".format(entries[0].get("module", "?")))
                    if chain_info:
                        print("  Extends: {}".format(chain_info))
                print("")
            else:
                print("  Class '{}' not found.".format(class_name))
            return

    info = servlets[target]

    # Get detailed data
    verbs = _get_verb_methods(base_dir, target)
    paths = _get_servlet_path(base_dir, target)
    params = _get_parameters(base_dir, target)

    # Ancestors
    inh = _load_inheritance(base_dir)
    chain = []
    if inh:
        ctc = inh.get("class_to_chain", {})
        chain = ctc.get(target, [])

    # Class info
    ci = _load_class_index(base_dir)
    classes_map = ci.get("classes", {}) if ci else {}
    class_entries = classes_map.get(target, [])
    class_info = class_entries[0] if class_entries else {}

    print("")
    print("  SERVLET: {}".format(target))
    print("  " + "=" * (len(target) + 10))
    print("")

    # Basic info
    print("  Module:     {}".format(info["module"]))
    print("  Package:    {}".format(class_info.get("package", "?")))
    print("  Kind:       {} (extends {})".format(
        class_info.get("kind", "class"), info["kind"]))
    print("  Lines:      {}".format(class_info.get("lines", "?")))
    print("")

    # Inheritance chain
    if chain:
        print("  Inheritance:")
        print("    {} -> {}".format(target, " -> ".join(chain[:6])))
        print("")

    # HTTP Verbs
    if verbs:
        print("  HTTP Handlers ({:d}):".format(len(verbs)))
        for v in sorted(verbs, key=lambda x: x["verb"]):
            print("    {:8s}  line {:>5d}  {}".format(
                v["verb"], v["line"], v["signature"]))
    else:
        print("  HTTP Handlers: none (may use service() or inherit handlers)")
    print("")

    # Servlet paths / route hints
    if paths:
        print("  Route Hints ({:d}):".format(len(paths)))
        for p in paths:
            if "method" in p:
                print("    [method]  {}() implemented  (module: {})".format(
                    p["method"], p["module"]))
            elif "string" in p:
                val = p["string"] if len(p["string"]) <= 60 else p["string"][:57] + "..."
                print("    [string]  \"{}\"  (line {:d})".format(val, p["line"]))
    else:
        print("  Route Hints: none found (path may be configured externally)")
    print("")

    # Parameters
    if params:
        shown_params = params[:30]
        print("  Likely Parameters ({:d}):".format(len(params)))
        for p in shown_params:
            print("    {:30s}  (line {:d})".format(p["name"], p["line"]))
        if len(params) > 30:
            print("    ... and {:d} more".format(len(params) - 30))
    else:
        print("  Parameters: none detected")
    print("")

    # All methods in this class from method-index
    mi = _load_method_index(base_dir)
    if mi:
        class_methods = mi.get("class_methods", {})
        cls_method_names = class_methods.get(target, [])
        if cls_method_names:
            # class_methods is a list of method name strings
            # Look up details from methods index
            methods_idx = mi.get("methods", {})
            detailed = []
            for mname in cls_method_names:
                entries = methods_idx.get(mname, [])
                for e in entries:
                    if e.get("class") == target:
                        detailed.append(e)

            public_methods = [m for m in detailed
                              if "public" in m.get("modifiers", [])]
            print("  All Methods: {:d} total, {:d} public".format(
                len(cls_method_names), len(public_methods)))
            for m in sorted(public_methods, key=lambda x: x.get("line", 0))[:10]:
                print("    line {:>5d}  {}".format(
                    m.get("line", 0), m.get("signature", "?")))
            if len(public_methods) > 10:
                print("    ... and {:d} more public methods".format(
                    len(public_methods) - 10))
            print("")
