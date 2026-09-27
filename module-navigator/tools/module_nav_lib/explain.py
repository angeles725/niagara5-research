"""
Cross-reference a concept across niagara-help (devguide, guides, bajadoc) and
the decompiled code indexes (class and method names).

Command:
  explain <concept> [--help-root PATH] [--no-content] [-n N]

Strategy:
  1. Filename match across the three doc trees (fast — path-relative grep).
  2. Optional content grep via shell-out to system `grep` (cheap under Linux;
     skipped if --no-content). Reports top N file hits.
  3. Cross-reference with class-index and method-index (substring match).

Prefers `niagara-help/` sibling of this tool's project. Fallback to
$NIAGARA_HOME/niagara-help.
"""

import json
import os
import re
import shutil
import subprocess

from module_nav_lib.license_inspect import resolve_niagara_home


_DOC_TREES = [
    ("devguide", "devguide-clean"),
    ("guides", "guides-clean"),
    ("bajadoc", "bajadoc-clean"),
]


def _resolve_help_root(explicit=None):
    if explicit and os.path.isdir(explicit):
        return explicit
    home, _ = resolve_niagara_home()
    if home:
        cand = os.path.join(home, "niagara-help")
        if os.path.isdir(cand):
            return cand
    return None


def _first_nonempty_line(path, limit_bytes=2048):
    """Return first non-empty line (<= limit_bytes) or '' on failure."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            buf = fh.read(limit_bytes)
    except (IOError, OSError):
        return ""
    for ln in buf.splitlines():
        ln = ln.strip()
        if ln:
            return ln
    return ""


def _filename_matches(root, concept, limit=40):
    """Walk the tree looking for files whose basename contains concept."""
    q = concept.lower()
    hits = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if q in fn.lower():
                hits.append(os.path.join(dirpath, fn))
                if len(hits) >= limit:
                    return hits
    return hits


def _content_matches(root, concept, limit=20):
    """Shell out to system grep to find files whose *content* matches concept."""
    grep = shutil.which("grep")
    if not grep:
        return []
    try:
        proc = subprocess.run(
            [grep, "-rli", "--include=*.txt", concept, root],
            capture_output=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError, subprocess.SubprocessError):
        return []
    out = proc.stdout.decode("utf-8", errors="replace")
    files = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return files[:limit]


def _index_matches(base_dir, concept, limit=10):
    """Return (classes, methods) with concept as substring (case-insensitive)."""
    q = concept.lower()
    classes = []
    methods = []
    class_idx_path = os.path.join(base_dir, "indexes", "class-index.json")
    method_idx_path = os.path.join(base_dir, "indexes", "method-index.json")
    try:
        with open(class_idx_path, "r", encoding="utf-8") as fh:
            c_idx = json.load(fh)
        for cname in c_idx.get("classes", {}):
            if q in cname.lower() and len(cname) > 2:
                classes.append(cname)
    except (IOError, OSError, ValueError):
        pass
    try:
        with open(method_idx_path, "r", encoding="utf-8") as fh:
            m_idx = json.load(fh)
        for mname in m_idx.get("methods", {}):
            if q in mname.lower() and len(mname) > 3:
                methods.append(mname)
    except (IOError, OSError, ValueError):
        pass
    return sorted(classes)[:limit], sorted(methods)[:limit]


def _print_doc_hits(label, root, paths, help_root, show_snippet=True):
    print("  {} ({})".format(label.upper(), len(paths)))
    if not paths:
        print("    (no matches)")
        print("")
        return
    rel_root = help_root + os.sep
    for p in paths:
        rel = p[len(rel_root):] if p.startswith(rel_root) else p
        snippet = _first_nonempty_line(p) if show_snippet else ""
        if snippet:
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            print("    {}".format(rel))
            print("      └── {}".format(snippet))
        else:
            print("    {}".format(rel))
    print("")


def cmd_explain(base_dir, concept, help_root=None, no_content=False,
                limit=15):
    help_root = _resolve_help_root(help_root)
    if not help_root:
        print("")
        print("  ERROR: niagara-help/ not found. "
              "Pass --help-root or set $NIAGARA_HOME.")
        print("")
        return

    print("")
    print("=" * 72)
    print("  EXPLAIN: '{}'".format(concept))
    print("=" * 72)
    print("  niagara-help: {}".format(help_root))
    print("")

    for label, sub in _DOC_TREES:
        tree = os.path.join(help_root, sub)
        if not os.path.isdir(tree):
            continue

        fn_hits = _filename_matches(tree, concept, limit=limit)
        if not no_content and len(fn_hits) < limit:
            # Augment with content hits (dedup).
            remaining = limit - len(fn_hits)
            seen = set(fn_hits)
            content_hits = []
            for p in _content_matches(tree, concept, limit=remaining * 3):
                if p in seen:
                    continue
                content_hits.append(p)
                seen.add(p)
                if len(content_hits) >= remaining:
                    break
            combined = fn_hits + content_hits
        else:
            combined = fn_hits

        # Prefer filename matches first (they stay at the top).
        _print_doc_hits(label, tree, combined[:limit], help_root)

    # Code cross-reference.
    classes, methods = _index_matches(base_dir, concept, limit=12)
    print("  CODE — matching classes ({})".format(len(classes)))
    if classes:
        for c in classes:
            print("    {}".format(c))
    else:
        print("    (none)")
    print("")
    print("  CODE — matching methods ({})".format(len(methods)))
    if methods:
        for m in methods:
            print("    {}()".format(m))
    else:
        print("    (none)")
    print("")

    # Next actions.
    print("  Next commands:")
    if classes:
        print("    source {}".format(classes[0]))
    if methods:
        print("    method {}".format(methods[0]))
    print("    grep '{}'".format(concept))
    print("")
