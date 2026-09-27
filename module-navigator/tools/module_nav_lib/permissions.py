"""
Permission & Security Model commands for Module Navigator (Phase 37).

Maps the Niagara permission model: checkPermission, getPermissions,
doAuthenticate, checkAccess — and credential handling (password, token,
secret references in string-index.db).

Traces permission verification chains via callgraph-index.

Uses token-index.db + method-index.json + string-index.db +
callgraph-index.json + class-index.json on-demand. No builder.

Commands:
  permissions [--module mod] [-n N]   Classes with permission checks
  permission-flow <class>             Permission verification chain for a class
  credentials [--module mod] [-n N]   Credential handling detection
"""

import json
import os
import sqlite3
from collections import defaultdict


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Tokens that indicate permission checking (searched in token-index.db)
_PERM_TOKENS = [
    "checkPermission", "checkPermissions",
    "getPermissions", "setPermissions",
    "BPermissions", "BPermission",
    "doCheckPermission",
    "ADMIN_WRITE", "ADMIN_READ", "ADMIN_INVOKE",
    "OPERATOR_WRITE", "OPERATOR_READ", "OPERATOR_INVOKE",
    "SUPER_USER",
]

# Methods that indicate authentication (searched in method-index.json)
_AUTH_METHODS = [
    "doAuthenticate", "authenticate", "checkAccess",
    "doLogin", "doLogout", "login", "logout",
    "verifyCredentials", "validateCredentials",
    "checkUserPermission", "getUserPermissions",
    "getCredentials", "setCredentials",
    "doCheckAccess",
]

# String patterns for credential detection (searched in string-index.db)
_CRED_PATTERNS = [
    "password", "credential", "secret", "apiKey", "api_key",
    "authToken", "auth_token", "bearerToken", "bearer_token",
    "sessionToken", "session_token", "accessToken", "access_token",
    "privateKey", "private_key", "passphrase", "passwd",
    "clientSecret", "client_secret",
]

# Classification of permission-related roles
_ROLE_KEYWORDS = {
    "checker": ["checkPermission", "checkAccess", "doCheckPermission",
                "checkUserPermission", "doCheckAccess"],
    "provider": ["getPermissions", "getUserPermissions", "BPermissions",
                 "setPermissions"],
    "authenticator": ["doAuthenticate", "authenticate", "verifyCredentials",
                      "validateCredentials", "doLogin", "login"],
    "guard": ["ADMIN_WRITE", "ADMIN_READ", "OPERATOR_WRITE",
              "OPERATOR_READ", "SUPER_USER", "ADMIN_INVOKE",
              "OPERATOR_INVOKE"],
}


# ---------------------------------------------------------------------------
# Index loaders (lazy, cached)
# ---------------------------------------------------------------------------

_token_db_conn = None
_string_db_conn = None
_method_index_cache = None
_callgraph_cache = None
_class_index_cache = None


def _get_token_db(base_dir):
    """Get or open token-index.db connection (lazy singleton)."""
    global _token_db_conn
    if _token_db_conn is not None:
        return _token_db_conn

    db_path = os.path.join(base_dir, "indexes", "token-index.db")
    if not os.path.isfile(db_path):
        print("ERROR: token-index.db not found.")
        print("Run: python tools/build_token_index.py")
        return None

    _token_db_conn = sqlite3.connect(db_path)
    _token_db_conn.execute("PRAGMA query_only=ON")
    _token_db_conn.execute("PRAGMA cache_size=-16000")
    return _token_db_conn


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


def _load_callgraph(base_dir):
    """Load callgraph-index.json (cached)."""
    global _callgraph_cache
    if _callgraph_cache is not None:
        return _callgraph_cache

    path = os.path.join(base_dir, "indexes", "callgraph-index.json")
    if not os.path.isfile(path):
        print("ERROR: callgraph-index.json not found.")
        return None

    with open(path, "r", encoding="utf-8") as f:
        _callgraph_cache = json.load(f)
    return _callgraph_cache


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


def _get_class_module(base_dir, class_name):
    """Resolve module for a class from class-index."""
    ci = _load_class_index(base_dir)
    if not ci:
        return "unknown"
    entries = ci.get("classes", {}).get(class_name, [])
    if entries:
        return entries[0].get("module", "unknown")
    return "unknown"


# ---------------------------------------------------------------------------
# Permission detection helpers
# ---------------------------------------------------------------------------

def _find_perm_classes_token(base_dir, module_filter=None):
    """Find classes that use permission tokens via token-index.db.

    Returns dict: class_name -> [{token, module, line}]
    """
    conn = _get_token_db(base_dir)
    if not conn:
        return {}

    results = defaultdict(list)
    cur = conn.cursor()

    for token in _PERM_TOKENS:
        if module_filter:
            cur.execute("""
                SELECT f.class_name, f.module, p.line_no
                FROM postings p JOIN files f ON p.file_id = f.id
                WHERE p.token = ? AND f.module = ?
                ORDER BY f.class_name, p.line_no
            """, (token, module_filter))
        else:
            cur.execute("""
                SELECT f.class_name, f.module, p.line_no
                FROM postings p JOIN files f ON p.file_id = f.id
                WHERE p.token = ?
                ORDER BY f.class_name, p.line_no
            """, (token,))

        for row in cur.fetchall():
            cls, mod, line = row
            results[cls].append({
                "token": token,
                "module": mod,
                "line": line,
            })

    return dict(results)


def _find_perm_classes_methods(base_dir, module_filter=None):
    """Find classes that declare auth-related methods via method-index.

    Returns dict: class_name -> [{method, module, line}]
    """
    mi = _load_method_index(base_dir)
    if not mi:
        return {}

    methods_idx = mi.get("methods", {})
    results = defaultdict(list)

    for mname in _AUTH_METHODS:
        entries = methods_idx.get(mname, [])
        for entry in entries:
            cls = entry.get("class", "")
            mod = entry.get("module", "")
            line = entry.get("line", 0)

            if module_filter and mod != module_filter:
                continue

            results[cls].append({
                "method": mname,
                "module": mod,
                "line": line,
            })

    return dict(results)


def _classify_role(tokens_list, methods_list):
    """Classify a class's security role based on its tokens and methods.

    Returns set of roles: checker, provider, authenticator, guard
    """
    roles = set()
    all_names = set()

    for t in tokens_list:
        all_names.add(t.get("token", ""))
    for m in methods_list:
        all_names.add(m.get("method", ""))

    for role, keywords in _ROLE_KEYWORDS.items():
        if any(kw in all_names for kw in keywords):
            roles.add(role)

    return roles if roles else {"related"}


# ---------------------------------------------------------------------------
# cmd_permissions_cli — CLI dispatcher (mirrors `permissions [--declared]`)
# ---------------------------------------------------------------------------

def cmd_permissions_cli(base_dir, declared=False, module_filter=None,
                        type_filter=None, limit=None, summary=False):
    """CLI-level dispatcher for the `permissions` subcommand.

    declared=False → scan bytecode callsites (cmd_permissions).
    declared=True  → scan META-INF/module.xml manifests (cmd_permissions_declared).
    `type_filter` and `summary` only apply when declared=True.
    """
    if declared:
        return cmd_permissions_declared(
            base_dir,
            module_filter=module_filter,
            type_filter=type_filter,
            limit=limit if limit is not None else 500,
            summary=summary,
        )
    return cmd_permissions(
        base_dir,
        module_filter=module_filter,
        limit=limit if limit is not None else 50,
    )


# ---------------------------------------------------------------------------
# cmd_permissions — Classes with permission checks
# ---------------------------------------------------------------------------

def cmd_permissions(base_dir, module_filter=None, limit=50):
    """List classes with permission checks and auth-related methods."""
    token_results = _find_perm_classes_token(base_dir, module_filter)
    method_results = _find_perm_classes_methods(base_dir, module_filter)

    # Merge results
    all_classes = set(token_results.keys()) | set(method_results.keys())

    if not all_classes:
        msg = "  No permission-related classes found"
        if module_filter:
            msg += " in module '{}'".format(module_filter)
        print(msg + ".")
        return

    # Build merged entries
    entries = []
    by_module = defaultdict(list)
    by_role = defaultdict(list)
    for cls in sorted(all_classes):
        tokens = token_results.get(cls, [])
        methods = method_results.get(cls, [])
        module = tokens[0]["module"] if tokens else (
            methods[0]["module"] if methods else "unknown")
        roles = _classify_role(tokens, methods)

        entry = {
            "class": cls,
            "module": module,
            "tokens": tokens,
            "methods": methods,
            "roles": roles,
            "total_refs": len(tokens) + len(methods),
        }
        entries.append(entry)
        by_module[module].append(entry)
        for r in roles:
            by_role[r].append(entry)

    # Sort by total references descending
    entries.sort(key=lambda e: -e["total_refs"])

    scope = " in {}".format(module_filter) if module_filter else ""
    print("")
    print("  PERMISSION & SECURITY MODEL{} ({:,} classes, {:,} modules)".format(
        scope, len(entries), len(by_module)))
    print("")

    # Role breakdown
    print("  By security role:")
    for role in ["checker", "guard", "authenticator", "provider", "related"]:
        items = by_role.get(role, [])
        if items:
            modules = len(set(e["module"] for e in items))
            print("    {:15s}  {:>5,d} classes  {:>4,d} modules".format(
                role, len(items), modules))
    print("")

    # Top modules
    print("  Top modules:")
    top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:15]
    for mod, items in top_mods:
        roles_set = set()
        for e in items:
            roles_set.update(e["roles"])
        print("    {:35s}  {:>4,d} classes  [{}]".format(
            mod, len(items), ", ".join(sorted(roles_set))))
    if len(by_module) > 15:
        print("    ... and {:,} more modules".format(len(by_module) - 15))
    print("")

    # Detailed listing
    print("  {:35s}  {:25s}  {:>4s}  {:>4s}  {}".format(
        "CLASS", "MODULE", "TOKS", "MTHS", "ROLES"))
    print("  " + "-" * 100)

    shown = 0
    for e in entries:
        if shown >= limit:
            remaining = len(entries) - shown
            print("  ... and {:,} more (use -n {:,} to see all)".format(
                remaining, len(entries)))
            break

        cls_d = e["class"] if len(e["class"]) <= 35 else e["class"][:32] + "..."
        mod_d = e["module"] if len(e["module"]) <= 25 else e["module"][:22] + "..."
        roles_str = ", ".join(sorted(e["roles"]))
        print("  {:35s}  {:25s}  {:>4d}  {:>4d}  {}".format(
            cls_d, mod_d, len(e["tokens"]), len(e["methods"]), roles_str))
        shown += 1

    print("")

    # Summary
    total_tokens = sum(len(e["tokens"]) for e in entries)
    total_methods = sum(len(e["methods"]) for e in entries)
    unique_tokens = set()
    unique_methods = set()
    for e in entries:
        for t in e["tokens"]:
            unique_tokens.add(t["token"])
        for m in e["methods"]:
            unique_methods.add(m["method"])

    print("  Summary:")
    print("    Total classes:       {:>6,d}".format(len(entries)))
    print("    Total modules:       {:>6,d}".format(len(by_module)))
    print("    Token references:    {:>6,d}  ({})".format(
        total_tokens, ", ".join(sorted(unique_tokens))))
    print("    Auth methods found:  {:>6,d}  ({})".format(
        total_methods, ", ".join(sorted(unique_methods))))
    print("")


# ---------------------------------------------------------------------------
# cmd_permission_flow — Permission verification chain for a class
# ---------------------------------------------------------------------------

def cmd_permission_flow(base_dir, class_name):
    """Trace the permission verification chain for a specific class."""
    ci = _load_class_index(base_dir)
    classes_map = ci.get("classes", {}) if ci else {}

    # Resolve class name (support partial match)
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

    entries = classes_map.get(target, [])
    class_info = entries[0] if entries else {}
    module = class_info.get("module", "unknown")

    print("")
    print("  PERMISSION FLOW: {}".format(target))
    print("  " + "=" * (18 + len(target)))
    print("")
    print("  Module:   {}".format(module))
    print("  Package:  {}".format(class_info.get("package", "?")))
    print("")

    # 1) Find permission tokens used BY this class
    conn_tok = _get_token_db(base_dir)
    perm_tokens_in_class = []
    if conn_tok:
        cur = conn_tok.cursor()
        for token in _PERM_TOKENS:
            cur.execute("""
                SELECT p.line_no
                FROM postings p JOIN files f ON p.file_id = f.id
                WHERE p.token = ? AND f.class_name = ?
                ORDER BY p.line_no
            """, (token, target))
            for row in cur.fetchall():
                perm_tokens_in_class.append({
                    "token": token,
                    "line": row[0],
                })

    # 2) Find auth methods DECLARED by this class
    mi = _load_method_index(base_dir)
    auth_methods_in_class = []
    if mi:
        methods_idx = mi.get("methods", {})
        for mname in _AUTH_METHODS:
            for entry in methods_idx.get(mname, []):
                if entry.get("class") == target:
                    auth_methods_in_class.append({
                        "method": mname,
                        "line": entry.get("line", 0),
                        "visibility": entry.get("visibility", "?"),
                        "params": entry.get("params", ""),
                        "return_type": entry.get("return_type", "void"),
                    })

    # 3) Callgraph: who calls this class's permission methods
    #    and what permission methods does this class call
    cg = _load_callgraph(base_dir)
    calls_out = []   # permission calls this class makes
    calls_in = []    # who calls this class's permission methods

    if cg:
        calls = cg.get("calls", {})

        # Outgoing: methods in this class that call permission-related methods
        perm_method_names = set(_PERM_TOKENS) | set(_AUTH_METHODS)
        for caller_key, callees in calls.items():
            if "." not in caller_key:
                continue
            caller_class = caller_key.rsplit(".", 1)[0]
            if caller_class != target:
                continue
            caller_method = caller_key.rsplit(".", 1)[1]

            for callee in callees:
                if "." not in callee:
                    continue
                callee_class = callee.rsplit(".", 1)[0]
                callee_method = callee.rsplit(".", 1)[1]

                if callee_method in perm_method_names or any(
                    pm in callee_method for pm in [
                        "Permission", "permission", "Authenticate",
                        "authenticate", "checkAccess", "Credential",
                        "credential",
                    ]
                ):
                    calls_out.append({
                        "from_method": caller_method,
                        "to": callee,
                        "to_class": callee_class,
                        "to_method": callee_method,
                    })

        # Incoming: other classes calling this class's methods
        for caller_key, callees in calls.items():
            if "." not in caller_key:
                continue
            caller_class = caller_key.rsplit(".", 1)[0]
            if caller_class == target:
                continue
            caller_method = caller_key.rsplit(".", 1)[1]

            for callee in callees:
                if "." not in callee:
                    continue
                callee_class = callee.rsplit(".", 1)[0]
                callee_method = callee.rsplit(".", 1)[1]

                if callee_class == target and (
                    callee_method in perm_method_names or any(
                        pm in callee_method for pm in [
                            "Permission", "permission", "Authenticate",
                            "authenticate", "checkAccess", "Credential",
                            "credential",
                        ]
                    )
                ):
                    calls_in.append({
                        "caller_class": caller_class,
                        "caller_method": caller_method,
                        "target_method": callee_method,
                    })

    # --- Output ---

    # Section 1: Permission tokens found
    if perm_tokens_in_class:
        # Group by token
        by_token = defaultdict(list)
        for t in perm_tokens_in_class:
            by_token[t["token"]].append(t["line"])

        print("  PERMISSION TOKENS ({:d} references):".format(
            len(perm_tokens_in_class)))
        for token in sorted(by_token.keys()):
            lines = by_token[token]
            lines_str = ", ".join(str(l) for l in sorted(lines)[:10])
            if len(lines) > 10:
                lines_str += " ..."
            print("    {:30s}  {:>3d} refs  lines: {}".format(
                token, len(lines), lines_str))
        print("")
    else:
        print("  PERMISSION TOKENS: none found")
        print("")

    # Section 2: Auth methods declared
    if auth_methods_in_class:
        print("  AUTH METHODS DECLARED ({:d}):".format(
            len(auth_methods_in_class)))
        for m in sorted(auth_methods_in_class, key=lambda x: x["line"]):
            print("    {:30s}  {:10s}  line {:>5d}  {}({})".format(
                m["method"], m["visibility"], m["line"],
                m["return_type"], m["params"]))
        print("")
    else:
        print("  AUTH METHODS DECLARED: none")
        print("")

    # Section 3: Outgoing permission calls
    if calls_out:
        by_target = defaultdict(list)
        for c in calls_out:
            by_target[c["to_class"]].append(c)

        print("  OUTGOING PERMISSION CALLS ({:d} calls to {:d} classes):".format(
            len(calls_out), len(by_target)))
        for tcls in sorted(by_target.keys()):
            items = by_target[tcls]
            tmod = _get_class_module(base_dir, tcls)
            methods_called = sorted(set(c["to_method"] for c in items))
            from_methods = sorted(set(c["from_method"] for c in items))
            print("    -> {:30s}  ({})".format(tcls, tmod))
            print("       calls: {}".format(", ".join(methods_called)))
            print("       from:  {}".format(", ".join(from_methods[:5])))
        print("")
    else:
        print("  OUTGOING PERMISSION CALLS: none")
        print("")

    # Section 4: Incoming callers
    if calls_in:
        by_caller = defaultdict(list)
        for c in calls_in:
            by_caller[c["caller_class"]].append(c)

        print("  INCOMING CALLERS ({:d} calls from {:d} classes):".format(
            len(calls_in), len(by_caller)))
        for ccls in sorted(by_caller.keys()):
            items = by_caller[ccls]
            cmod = _get_class_module(base_dir, ccls)
            target_methods = sorted(set(c["target_method"] for c in items))
            from_methods = sorted(set(c["caller_method"] for c in items))
            print("    <- {:30s}  ({})".format(ccls, cmod))
            print("       targets: {}".format(", ".join(target_methods)))
            print("       via:     {}".format(", ".join(from_methods[:5])))
        print("")
    else:
        print("  INCOMING CALLERS: none")
        print("")

    # Section 5: Classify role
    roles = _classify_role(
        [{"token": t["token"]} for t in perm_tokens_in_class],
        [{"method": m["method"]} for m in auth_methods_in_class],
    )
    print("  SECURITY ROLE: {}".format(", ".join(sorted(roles))))
    print("")

    # Section 6: Related classes in same module
    all_perm_classes = _find_perm_classes_token(base_dir, module_filter=module)
    all_auth_classes = _find_perm_classes_methods(base_dir, module_filter=module)
    related = (set(all_perm_classes.keys()) | set(all_auth_classes.keys())) - {target}
    if related:
        print("  OTHER SECURITY CLASSES IN {} ({:d}):".format(
            module, len(related)))
        for r in sorted(related)[:20]:
            r_tok = len(all_perm_classes.get(r, []))
            r_mth = len(all_auth_classes.get(r, []))
            print("    {:35s}  {:>3d} tokens  {:>3d} methods".format(r, r_tok, r_mth))
        if len(related) > 20:
            print("    ... and {:,} more".format(len(related) - 20))
        print("")

    # Summary
    print("  Summary:")
    print("    Permission tokens:    {:>5d}".format(len(perm_tokens_in_class)))
    print("    Auth methods:         {:>5d}".format(len(auth_methods_in_class)))
    print("    Outgoing perm calls:  {:>5d}".format(len(calls_out)))
    print("    Incoming callers:     {:>5d}".format(len(calls_in)))
    print("    Security role:        {}".format(", ".join(sorted(roles))))
    print("")


# ---------------------------------------------------------------------------
# cmd_credentials — Credential handling detection
# ---------------------------------------------------------------------------

def cmd_credentials(base_dir, module_filter=None, limit=50):
    """Detect classes that handle credentials (password, token, secret, etc.)."""
    conn = _get_string_db(base_dir)
    if not conn:
        return

    # Build query: search for credential-related string literals
    like_clauses = []
    params = []
    for pattern in _CRED_PATTERNS:
        like_clauses.append("LOWER(s.string_val) LIKE ?")
        params.append("%{}%".format(pattern.lower()))

    where = " OR ".join(like_clauses)

    sql = """
        SELECT s.string_val, f.class_name, f.module, s.line_no
        FROM strings s JOIN files f ON s.file_id = f.id
        WHERE ({})
    """.format(where)

    if module_filter:
        sql += " AND f.module = ?"
        params.append(module_filter)

    sql += " ORDER BY f.module, f.class_name, s.line_no"

    cur = conn.cursor()
    cur.execute(sql, params)

    # Group results by class
    by_class = defaultdict(list)
    seen = set()
    for row in cur.fetchall():
        val, cls, mod, line = row
        val_stripped = val.strip()

        # Skip very short or very long strings (noise)
        if len(val_stripped) < 4 or len(val_stripped) > 200:
            continue

        # Skip common false positives
        val_lower = val_stripped.lower()
        if val_lower in ("password", "token", "secret"):
            # These single-word strings are likely field names, still interesting
            pass

        dedup_key = (val_stripped, cls, line)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Categorize the credential reference
        category = _categorize_credential(val_stripped)

        by_class[cls].append({
            "value": val_stripped,
            "module": mod,
            "line": line,
            "category": category,
        })

    if not by_class:
        msg = "  No credential references found"
        if module_filter:
            msg += " in module '{}'".format(module_filter)
        print(msg + ".")
        return

    # Build entries
    entries = []
    by_module = defaultdict(list)
    by_category = defaultdict(list)
    total_refs = 0

    for cls in sorted(by_class.keys()):
        items = by_class[cls]
        module = items[0]["module"]
        categories = set(i["category"] for i in items)

        entry = {
            "class": cls,
            "module": module,
            "refs": items,
            "categories": categories,
            "count": len(items),
        }
        entries.append(entry)
        by_module[module].append(entry)
        total_refs += len(items)
        for cat in categories:
            by_category[cat].append(entry)

    entries.sort(key=lambda e: -e["count"])

    scope = " in {}".format(module_filter) if module_filter else ""
    print("")
    print("  CREDENTIAL HANDLING{} ({:,} classes, {:,} refs, {:,} modules)".format(
        scope, len(entries), total_refs, len(by_module)))
    print("")

    # By category
    print("  By category:")
    for cat in sorted(by_category.keys(), key=lambda c: -len(by_category[c])):
        items = by_category[cat]
        refs = sum(e["count"] for e in items)
        mods = len(set(e["module"] for e in items))
        print("    {:20s}  {:>5,d} classes  {:>6,d} refs  {:>4,d} modules".format(
            cat, len(items), refs, mods))
    print("")

    # Top modules
    print("  Top modules:")
    top_mods = sorted(by_module.items(), key=lambda x: -len(x[1]))[:15]
    for mod, items in top_mods:
        refs = sum(e["count"] for e in items)
        cats = set()
        for e in items:
            cats.update(e["categories"])
        print("    {:35s}  {:>4,d} classes  {:>5,d} refs  [{}]".format(
            mod, len(items), refs, ", ".join(sorted(cats))))
    if len(by_module) > 15:
        print("    ... and {:,} more modules".format(len(by_module) - 15))
    print("")

    # Detailed listing
    print("  {:35s}  {:25s}  {:>4s}  {:15s}  {}".format(
        "CLASS", "MODULE", "REFS", "CATEGORIES", "SAMPLE"))
    print("  " + "-" * 120)

    shown = 0
    for e in entries:
        if shown >= limit:
            remaining = len(entries) - shown
            print("  ... and {:,} more (use -n {:,} to see all)".format(
                remaining, len(entries)))
            break

        cls_d = e["class"] if len(e["class"]) <= 35 else e["class"][:32] + "..."
        mod_d = e["module"] if len(e["module"]) <= 25 else e["module"][:22] + "..."
        cats_str = ", ".join(sorted(e["categories"]))
        if len(cats_str) > 15:
            cats_str = cats_str[:12] + "..."

        # Show a sample string
        sample = e["refs"][0]["value"]
        if len(sample) > 40:
            sample = sample[:37] + "..."

        print("  {:35s}  {:25s}  {:>4d}  {:15s}  {}".format(
            cls_d, mod_d, e["count"], cats_str, sample))
        shown += 1

    print("")


def _categorize_credential(value):
    """Categorize a credential-related string."""
    val_lower = value.lower()

    if any(kw in val_lower for kw in ["password", "passwd", "passphrase"]):
        return "password"
    elif any(kw in val_lower for kw in ["token", "bearer"]):
        return "token"
    elif any(kw in val_lower for kw in ["secret", "client_secret", "clientsecret"]):
        return "secret"
    elif any(kw in val_lower for kw in ["api_key", "apikey"]):
        return "api-key"
    elif any(kw in val_lower for kw in ["credential"]):
        return "credential"
    elif any(kw in val_lower for kw in ["private_key", "privatekey"]):
        return "private-key"
    elif any(kw in val_lower for kw in ["session"]):
        return "session"
    elif any(kw in val_lower for kw in ["access"]):
        return "access"
    else:
        return "other"


# ---------------------------------------------------------------------------
# cmd_permissions_declared — Batch 7, FEATURE-5
#
# Scans META-INF/module.xml <permissions> blocks across the decompiled corpus
# and lists declared java-permission entries grouped by module and type.
# ---------------------------------------------------------------------------

def _resolve_corpus_root():
    """Read class-index.json._meta.source and apply env-var + fallback chain."""
    # Imported here to avoid circular dependencies at module load time.
    from module_nav_lib.grep_search import (
        _load_class_index, _resolve_source_root, _print_source_root_error,
    )
    # The class index lives at indexes/class-index.json — the base_dir plumb
    # is module_nav.py territory. We replicate the same logic using the meta
    # that _load_class_index returns. To avoid passing base_dir here we pull
    # it from the indexes/ directory relative to this file.
    import os as _os
    lib_dir = _os.path.dirname(_os.path.abspath(__file__))
    tools_dir = _os.path.dirname(lib_dir)
    project_root = _os.path.dirname(tools_dir)
    data = _load_class_index(project_root)
    if not data:
        return None
    meta_source = data.get("_meta", {}).get("source_root", "")
    resolved, tried = _resolve_source_root(meta_source)
    if resolved:
        return resolved
    _print_source_root_error(tried)
    return None


def cmd_permissions_declared(base_dir, module_filter=None, type_filter=None,
                             limit=500, summary=False):
    """Scan META-INF/module.xml permissions blocks across the corpus.

    - Iterates `<corpus>/*/*/extracted/META-INF/module.xml` (extracted is the
      canonical source from the JAR; `vineflower/` would be a decompiled copy
      and duplicates the same XML — intentionally skipped).
    - Parses with stdlib `xml.etree.ElementTree`.
    - For each <java-permissions type="station|all|workbench">, reads each
      <java-permission class=... name=... action=...> element.
    - `module_filter` matches by submodule dir name (e.g. `bql-rt`).
    - `type_filter` restricts to one of station/all/workbench.
    - `summary=True` prints aggregate counts (per module, per type, per class)
      instead of the full row dump.
    """
    import glob
    import xml.etree.ElementTree as ET

    # Resolve corpus root from class-index meta (same chain as tokens/grep).
    from module_nav_lib.grep_search import (
        _load_class_index, _resolve_source_root, _print_source_root_error,
    )
    data = _load_class_index(base_dir)
    if not data:
        return
    meta_source = data.get("_meta", {}).get("source_root", "")
    root, tried = _resolve_source_root(meta_source)
    if not root:
        _print_source_root_error(tried)
        return

    # organized/<module>/<submodule-rt|wb|ux|doc>/extracted/META-INF/module.xml
    pattern = os.path.join(root, "*", "*", "extracted", "META-INF", "module.xml")
    xml_files = sorted(glob.glob(pattern))

    if not xml_files:
        print("")
        print("  No module.xml files found under {}".format(pattern))
        print("")
        return

    rows = []          # (submodule_dir_name, perm_type, cls, name, action)
    modules_scanned = 0
    modules_with_perms = 0
    parse_failures = 0

    for xml_path in xml_files:
        # submodule dir is two parents up from META-INF/module.xml
        submodule_dir = os.path.basename(
            os.path.dirname(os.path.dirname(os.path.dirname(xml_path))))
        modules_scanned += 1

        if module_filter and submodule_dir != module_filter:
            continue

        try:
            tree = ET.parse(xml_path)
        except (ET.ParseError, IOError, OSError) as e:
            parse_failures += 1
            import sys as _sys
            _sys.stderr.write(
                "  WARN: skipped malformed module.xml ({}): {}\n".format(
                    submodule_dir, e))
            continue

        module_root = tree.getroot()
        perms_block = module_root.find("permissions")
        if perms_block is None:
            continue

        local_count = 0
        for jps in perms_block.findall("java-permissions"):
            perm_type = jps.get("type", "") or ""
            if type_filter and perm_type != type_filter:
                continue
            for jp in jps.findall("java-permission"):
                cls = jp.get("class", "") or ""
                name = jp.get("name", "") or ""
                action = jp.get("action", "") or ""
                rows.append((submodule_dir, perm_type, cls, name, action))
                local_count += 1
        if local_count > 0:
            modules_with_perms += 1

    # Sort for stable output
    rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))

    # Labels for header
    filter_parts = []
    if module_filter:
        filter_parts.append("module={}".format(module_filter))
    if type_filter:
        filter_parts.append("type={}".format(type_filter))
    filter_label = " ({})".format(", ".join(filter_parts)) if filter_parts else ""

    print("")
    print("  DECLARED PERMISSIONS{}".format(filter_label))
    print("  module.xml files scanned: {}  with <permissions>: {}  parse failures: {}".format(
        modules_scanned, modules_with_perms, parse_failures))
    print("  java-permission entries: {}".format(len(rows)))

    if not rows:
        print("")
        if module_filter:
            print("  No declared permissions for module '{}'.".format(module_filter))
        else:
            print("  No declared permissions match the given filter.")
        print("")
        return

    if summary:
        from collections import Counter
        by_type = Counter(r[1] for r in rows)
        by_module = Counter(r[0] for r in rows)
        by_class = Counter(r[2] for r in rows)

        print("")
        print("  By type:   " + "   ".join(
            "{}={}".format(t or "(none)", c) for t, c in sorted(by_type.items())))

        print("")
        print("  Top modules by entry count:")
        for mod_name, cnt in by_module.most_common(10):
            print("    {:30s} {:>6d}".format(mod_name[:30], cnt))

        print("")
        print("  Top permission classes:")
        for cls, cnt in by_class.most_common(10):
            print("    {:50s} {:>6d}".format(cls[:50], cnt))
        print("")
        return

    print("")
    print("  {:30s} {:10s} {:45s} {:25s} {}".format(
        "MODULE", "TYPE", "CLASS", "NAME", "ACTION"))
    print("  " + "-" * 120)
    shown = 0
    for mod_name, perm_type, cls, name, action in rows:
        if shown >= limit:
            print("    ... limit reached ({}) — use -n to increase".format(limit))
            break
        print("  {:30s} {:10s} {:45s} {:25s} {}".format(
            mod_name[:30], perm_type[:10],
            cls[:45], name[:25], action))
        shown += 1
    print("")
