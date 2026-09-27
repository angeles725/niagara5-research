"""
License feature gating commands for Module Navigator (Batch 7, FEATURE-4).

Extracts the feature names passed to
`Sys.getLicenseManager().checkFeature("tridium", "<feature>")` by reading a
small source window around each token-index hit of `checkFeature`.

Use cases:
  - Auditing which features gate a class (`license-feature <name>`)
  - Discovering all feature names referenced across the corpus
    (`license-features`)

Commands:
  license-feature <name> [-n N]    Callsites for a specific feature name
  license-features [-n N]          Aggregate top feature names with counts

Pattern matched (multi-line tolerant):
    checkFeature(
        "tridium",
        "historyImport"
    )

Unresolved cases (non-literal feature name arg such as `FEATURE_X` constants
or ZKM-obfuscated identifiers) are counted separately as "(unresolved)" — the
callsite is still shown but not aggregated under a real feature name.
"""

import json
import os
import re
import sqlite3

import corpus_config


# The feature name MUST be the SECOND string literal passed to checkFeature.
# We allow arbitrary whitespace (including newlines) between the tokens so
# the pattern matches both one-liners and multi-line calls.
_CHECK_FEATURE_RE = re.compile(
    r'checkFeature\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"',
    re.DOTALL,
)

# When the second argument is a constant / identifier (not a string literal),
# this pattern still matches so we can flag the callsite as unresolved.
_CHECK_FEATURE_ANY_RE = re.compile(
    r'checkFeature\s*\(',
)

# Window size around the token hit line (±N lines) when scanning the source.
_WINDOW = 5


# ---------------------------------------------------------------------------
# Shared helpers (kept in sync with tokens.py / grep_search.py — the third
# reader pattern; extraction to a shared module is deferred per Batch 6/7
# proposal decisions).
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
    _db_conn.execute("PRAGMA cache_size=-16000")
    return _db_conn


def _resolve_source_root(meta_source):
    """Env-var + fallback chain resolver (see tokens.py for semantics)."""
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
    print("")
    print("ERROR: Corpus source root not found.")
    print("  Tried the following paths (first valid wins):")
    for p in tried:
        print("    {}".format(p))
    print("")
    print("  Override with the NAV_CORPUS_BASE environment variable, e.g.:")
    print("    export NAV_CORPUS_BASE=/home/user/modules/organized")
    print("")


def _meta_source_root(conn):
    """Read class-index source_root equivalent from token-index meta."""
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM meta WHERE key = 'source_root'")
    row = cur.fetchone()
    if not row:
        return None
    resolved, tried = _resolve_source_root(row[1])
    if resolved:
        return resolved
    _print_source_root_error(tried)
    return None


def _collect_callsites(conn):
    """Return [(class_name, module, path, line_no)] for every `checkFeature` hit."""
    cur = conn.cursor()
    cur.execute("""
        SELECT f.class_name, f.module, f.path, p.line_no
        FROM postings p
        JOIN files f ON p.file_id = f.id
        WHERE p.token = 'checkFeature'
        ORDER BY f.module, f.class_name, p.line_no
    """)
    return cur.fetchall()


def _extract_feature_name(lines, hit_line):
    """Look for `checkFeature("tridium", "<name>")` in a window around hit_line.

    Returns (category, feature_name) on success, or (None, None) if the second
    argument was not a string literal (ZKM constant, variable, etc.)."""
    start = max(0, hit_line - 1 - _WINDOW)
    end = min(len(lines), hit_line + _WINDOW)
    window = "".join(lines[start:end])
    m = _CHECK_FEATURE_RE.search(window)
    if m:
        return m.group(1), m.group(2)
    # The hit exists but the second arg is not a literal — mark unresolved.
    if _CHECK_FEATURE_ANY_RE.search(window):
        return None, None
    return None, None


# ---------------------------------------------------------------------------
# license-feature <name>
# ---------------------------------------------------------------------------

def cmd_license_feature(base_dir, feature_name, limit=100):
    """List callsites of checkFeature("tridium", feature_name)."""
    conn = _get_db(base_dir)
    if not conn:
        return
    root = _meta_source_root(conn)
    if not root:
        return

    hits = _collect_callsites(conn)
    matched = []       # [(class, module, path, line, category)]
    unresolved = 0
    missing_files = 0

    for cls, module, path, line_no in hits:
        filepath = os.path.join(root, path)
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                source_lines = f.readlines()
        except (IOError, OSError):
            missing_files += 1
            continue
        category, feature = _extract_feature_name(source_lines, line_no)
        if feature is None:
            unresolved += 1
            continue
        if feature != feature_name:
            continue
        matched.append((cls, module, path, line_no, category))

    print("")
    print("  LICENSE FEATURE: '{}'".format(feature_name))
    print("  Hits for token 'checkFeature': {}  (unresolved args: {})".format(
        len(hits), unresolved))
    if missing_files:
        print("  Source files missing on disk: {}".format(missing_files))
    print("")

    if not matched:
        print("  No callsites found for feature '{}'.".format(feature_name))
        _print_fallback_hints(base_dir, conn, feature_name, hits)
        print("")
        return

    print("  {} callsite(s):".format(len(matched)))
    print("")
    print("  {:40s} {:>6s}  {:20s} {}".format("CLASS", "LINE", "CATEGORY", "MODULE"))
    print("  " + "-" * 100)
    shown = 0
    for cls, module, _path, line_no, category in matched:
        if shown >= limit:
            print("    ... limit reached ({}) — use -n to increase".format(limit))
            break
        print("  {:40s} {:>6d}  {:20s} {}".format(
            cls[:40], line_no, (category or "")[:20], module))
        shown += 1
    print("")


# ---------------------------------------------------------------------------
# license-features (aggregate listing)
# ---------------------------------------------------------------------------

def _print_fallback_hints(base_dir, conn, feature_name, hits):
    """When the requested feature name has no callsites, hint at related
    feature names, methods, and classes so the user has a next step."""
    import json as _json

    q = feature_name.lower()
    print("")
    print("  Fallback hints for '{}':".format(feature_name))

    # (1) Known feature names with substring overlap.
    known = set()
    for cls, _mod, path, line_no in hits:
        try:
            root = _meta_source_root(conn)
            if not root:
                break
            with open(os.path.join(root, path), "r",
                      encoding="utf-8", errors="replace") as f:
                source_lines = f.readlines()
        except (IOError, OSError):
            continue
        _cat, feat = _extract_feature_name(source_lines, line_no)
        if feat:
            known.add(feat)

    related_features = sorted(
        f for f in known
        if q != f.lower() and (q in f.lower() or f.lower() in q)
    )[:10]
    print("    Related feature names ({}):".format(len(related_features)))
    if related_features:
        for f in related_features:
            print("      - {}".format(f))
    else:
        print("      (none — try 'license-features' for the full list)")

    # (2) Methods in the method-index whose name contains the query.
    method_idx_path = os.path.join(base_dir, "indexes", "method-index.json")
    method_hits = []
    if os.path.isfile(method_idx_path):
        try:
            with open(method_idx_path, "r", encoding="utf-8") as f:
                m_idx = _json.load(f)
            methods = m_idx.get("methods", {})
            for mname in methods:
                ml = mname.lower()
                if q in ml and len(mname) > 3:
                    method_hits.append(mname)
        except (IOError, OSError, ValueError):
            pass
    method_hits = sorted(method_hits)[:8]
    print("    Related method names ({}):".format(len(method_hits)))
    for m in method_hits:
        print("      - {}()".format(m))
    if not method_hits:
        print("      (none)")

    # (3) Classes whose name contains the query.
    class_idx_path = os.path.join(base_dir, "indexes", "class-index.json")
    class_hits = []
    if os.path.isfile(class_idx_path):
        try:
            with open(class_idx_path, "r", encoding="utf-8") as f:
                c_idx = _json.load(f)
            classes = c_idx.get("classes", {})
            for cname in classes:
                cl = cname.lower()
                if q in cl and len(cname) > 3:
                    class_hits.append(cname)
        except (IOError, OSError, ValueError):
            pass
    class_hits = sorted(class_hits)[:8]
    print("    Related class names ({}):".format(len(class_hits)))
    for c in class_hits:
        print("      - {}".format(c))
    if not class_hits:
        print("      (none)")

    # (4) Always-useful canonical entry points for license exploration.
    print("    Next commands to try:")
    if related_features:
        print("      license-feature {}".format(related_features[0]))
    print("      license-features                     # full aggregate of feature names")
    if method_hits:
        print("      method {}".format(method_hits[0]))
    if class_hits:
        print("      source {}".format(class_hits[0]))
    print("      grep '{}'".format(feature_name))


def cmd_license_features(base_dir, limit=50):
    """Aggregate all feature names referenced by checkFeature with counts."""
    conn = _get_db(base_dir)
    if not conn:
        return
    root = _meta_source_root(conn)
    if not root:
        return

    hits = _collect_callsites(conn)
    # feature_name -> dict with counters
    agg = {}
    unresolved = 0
    missing_files = 0

    for cls, module, path, line_no in hits:
        filepath = os.path.join(root, path)
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                source_lines = f.readlines()
        except (IOError, OSError):
            missing_files += 1
            continue
        category, feature = _extract_feature_name(source_lines, line_no)
        if feature is None:
            unresolved += 1
            continue
        bucket = agg.setdefault(feature, {
            "category": category, "hits": 0,
            "classes": set(), "modules": set(),
        })
        bucket["hits"] += 1
        bucket["classes"].add(cls)
        bucket["modules"].add(module)

    total_resolved = sum(b["hits"] for b in agg.values())

    print("")
    print("  LICENSE FEATURES — aggregate")
    print("  Total checkFeature hits: {}  resolved: {}  unresolved: {}".format(
        len(hits), total_resolved, unresolved))
    if missing_files:
        print("  Source files missing on disk: {}".format(missing_files))
    print("")

    if not agg:
        print("  No resolvable feature names found.")
        print("")
        return

    ranked = sorted(agg.items(), key=lambda kv: kv[1]["hits"], reverse=True)

    print("  {:30s} {:12s} {:>5s}  {:>5s}  {:>5s}".format(
        "FEATURE", "CATEGORY", "HITS", "CLS", "MOD"))
    print("  " + "-" * 70)
    shown = 0
    for feature, b in ranked:
        if shown >= limit:
            print("    ... limit reached ({}) — use -n to increase".format(limit))
            break
        print("  {:30s} {:12s} {:>5d}  {:>5d}  {:>5d}".format(
            feature[:30], (b["category"] or "")[:12],
            b["hits"], len(b["classes"]), len(b["modules"])))
        shown += 1
    print("")
