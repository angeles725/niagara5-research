"""
Example Mining for Module Navigator (Batch 4, Gap #3).

Mines the decompiled corpus for real usage examples of a class. Returns full
method bodies that reference the target class, ranked by a simple similarity
score (class mention density + related B-class density + length penalty).

Commands:
  example-mine <class>
    [--pattern <substring>]  Filter method bodies by substring (case-insensitive)
    [--top N]                Max examples to return (default 3)
    [--exclude-tridium]      Skip com/tridium/* files
    [--include-docsource]    Include docSource-doc (mirror copy; excluded by default)
    [--min-lines N]          Minimum method body lines (default 5)
    [--json]                 Structured JSON output

Reuses existing indexes (no new builders):
  class-index.json, method-index.json, token-index.db

The enclosing-method boundary is derived from method-index line numbers
(robust, no Java parsing required); the method body is extracted via
brace tracking that respects strings and comments.
"""

import json
import os
import re
import sqlite3


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached)
# ---------------------------------------------------------------------------

_class_index_cache = None
_method_index_cache = None
_source_root_cache = None


def _load_class_index(base_dir):
    global _class_index_cache, _source_root_cache
    if _class_index_cache is not None:
        return _class_index_cache
    path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print("  ERROR loading class-index.json: {}".format(exc))
        return None
    _class_index_cache = data
    _source_root_cache = data.get("_meta", {}).get("source", "")
    return data


def _load_method_index(base_dir):
    global _method_index_cache
    if _method_index_cache is not None:
        return _method_index_cache
    path = os.path.join(base_dir, "indexes", "method-index.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            _method_index_cache = json.load(f)
    except Exception as exc:
        print("  ERROR loading method-index.json: {}".format(exc))
        return None
    return _method_index_cache


def _open_token_db(base_dir):
    path = os.path.join(base_dir, "indexes", "token-index.db")
    if not os.path.isfile(path):
        return None
    try:
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA query_only=ON")
        return conn
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Class resolution
# ---------------------------------------------------------------------------

def _resolve_class(ci_data, class_name):
    """Return the canonical class name (case-corrected) or None."""
    classes = ci_data.get("classes", {})
    if class_name in classes:
        return class_name
    name_lower = class_name.lower()
    for k in classes:
        if k.lower() == name_lower:
            return k
    return None


# ---------------------------------------------------------------------------
# Enclosing-method lookup via method-index line numbers
# ---------------------------------------------------------------------------

_class_method_lines_cache = {}


def _get_class_method_lines(method_index, class_name, module):
    """Return sorted [(decl_line, method_name), ...] for a class in a module.

    Scoped by (class_name, module) because short class names like "Helper"
    or "Utils" appear in many modules — mixing their line numbers would
    produce bogus method boundaries when extracting bodies.
    """
    cache_key = (class_name, module)
    if cache_key in _class_method_lines_cache:
        return _class_method_lines_cache[cache_key]

    class_methods = method_index.get("class_methods", {}).get(class_name)
    if not class_methods:
        _class_method_lines_cache[cache_key] = None
        return None

    methods_map = method_index.get("methods", {})
    pairs = []
    for mname in class_methods:
        for entry in methods_map.get(mname, []):
            if entry.get("class") != class_name:
                continue
            if entry.get("module") != module:
                continue
            line = entry.get("line", 0)
            if line > 0:
                pairs.append((line, mname))
            break
    pairs.sort()
    _class_method_lines_cache[cache_key] = pairs if pairs else None
    return _class_method_lines_cache[cache_key]


def _find_enclosing_method(method_lines, hit_line):
    """Return (decl_line, method_name) for the method containing hit_line."""
    enclosing = None
    for decl_line, mname in method_lines:
        if decl_line <= hit_line:
            enclosing = (decl_line, mname)
        else:
            break
    return enclosing


# ---------------------------------------------------------------------------
# Method body extraction via brace tracking (comment/string-aware)
# ---------------------------------------------------------------------------

def _extract_method_body(src_lines, start_line):
    """Return (start_idx, end_idx) of the method starting at start_line.

    start_line is 1-based; the returned indices are 0-based and end_idx is
    exclusive (like Python slicing).
    """
    if start_line < 1 or start_line > len(src_lines):
        return None

    start_idx = start_line - 1
    depth = 0
    found_open = False
    in_string = False
    in_char = False
    in_block_comment = False

    for j in range(start_idx, len(src_lines)):
        line = src_lines[j]
        k = 0
        L = len(line)
        in_line_comment = False

        while k < L:
            ch = line[k]
            nx = line[k + 1] if k + 1 < L else ""

            if in_line_comment:
                break
            if in_block_comment:
                if ch == '*' and nx == '/':
                    in_block_comment = False
                    k += 2
                    continue
                k += 1
                continue
            if in_string:
                if ch == '\\':
                    k += 2
                    continue
                if ch == '"':
                    in_string = False
                k += 1
                continue
            if in_char:
                if ch == '\\':
                    k += 2
                    continue
                if ch == "'":
                    in_char = False
                k += 1
                continue

            if ch == '/' and nx == '/':
                in_line_comment = True
                break
            if ch == '/' and nx == '*':
                in_block_comment = True
                k += 2
                continue
            if ch == '"':
                in_string = True
                k += 1
                continue
            if ch == "'":
                in_char = True
                k += 1
                continue
            if ch == '{':
                depth += 1
                found_open = True
            elif ch == '}':
                depth -= 1
                if found_open and depth == 0:
                    return (start_idx, j + 1)
            k += 1

    return None


# ---------------------------------------------------------------------------
# Source reading (bounded cache)
# ---------------------------------------------------------------------------

_file_cache = {}
_FILE_CACHE_MAX = 60


def _read_source(rel_path):
    if rel_path in _file_cache:
        return _file_cache[rel_path]
    if len(_file_cache) >= _FILE_CACHE_MAX:
        _file_cache.pop(next(iter(_file_cache)))
    if not _source_root_cache:
        return None
    full = os.path.join(_source_root_cache, rel_path)
    if not os.path.isfile(full):
        _file_cache[rel_path] = None
        return None
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            _file_cache[rel_path] = f.readlines()
    except Exception:
        _file_cache[rel_path] = None
    return _file_cache[rel_path]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

_BCLASS_RE = re.compile(r'\bB[A-Z]\w+')


def _score_snippet(body_text, class_name):
    """Score a method body as a candidate example.

    Higher is better. Components:
      + 2.0 per direct class_name mention
      + 0.15 per other B-prefixed class mention (domain density)
      x length penalty (shorter, denser methods rank higher)
    """
    class_mentions = body_text.count(class_name)
    bcls_mentions = len(_BCLASS_RE.findall(body_text))
    line_count = body_text.count('\n') + 1
    length_penalty = 1.0 if line_count <= 60 else max(0.25, 60.0 / line_count)
    score = (class_mentions * 2.0) + (bcls_mentions * 0.15)
    score *= length_penalty
    return round(score, 2)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _print_examples(class_name, examples, total, files_scanned, pattern):
    print("")
    print("  " + "=" * 68)
    print("  EXAMPLE MINE: {}".format(class_name))
    print("  " + "=" * 68)
    scope = " (pattern='{}')".format(pattern) if pattern else ""
    print("  {} matching method(s), {} files scanned{}".format(
        total, files_scanned, scope))

    for i, ex in enumerate(examples, 1):
        print("")
        print("  EXAMPLE {}  --  {} / {}  (score {})".format(
            i, ex["module"], ex["class"] + ".java", ex["score"]))
        print("  Method:  {}".format(ex["method"]))
        print("  Path:    {}".format(ex["path"]))
        print("  Lines:   {}-{}".format(ex["start_line"], ex["end_line"]))
        print("  " + "-" * 68)
        for k, line in enumerate(ex["body"]):
            lineno = ex["start_line"] + k
            display = line if len(line) <= 120 else line[:117] + "..."
            print("  {:>5d} | {}".format(lineno, display))
    print("")


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_example_mine(base_dir, class_name, pattern=None, top=3,
                     exclude_tridium=False, min_lines=5, as_json=False,
                     include_docsource=False):
    """Mine the corpus for real usage examples of a class.

    By default, hits from the `docSource-doc` module are skipped because that
    module is a mirror copy of the real runtime sources (alarm-rt, control-rt,
    etc.) and produces duplicate snippets. Pass include_docsource=True to opt
    in to those hits.
    """
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: class-index.json not found.")
        return

    resolved = _resolve_class(ci_data, class_name)
    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        return
    class_name = resolved

    method_index = _load_method_index(base_dir)
    if not method_index:
        print("  ERROR: method-index.json not found.")
        return

    conn = _open_token_db(base_dir)
    if not conn:
        print("  ERROR: token-index.db not found.")
        return

    # Query token-index for all file hits of this class name
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT f.class_name, f.module, f.path, p.line_no
            FROM postings p
            JOIN files f ON p.file_id = f.id
            WHERE p.token = ?
            ORDER BY f.path, p.line_no
        """, (class_name,))
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        print("  No token-index hits for '{}'.".format(class_name))
        return

    # Group hits by (caller_class, module, path); skip self-file and filters
    hits_by_file = {}
    for cls, mod, path, ln in rows:
        if cls == class_name:
            continue
        if not include_docsource and mod == "docSource-doc":
            continue
        if exclude_tridium and "/com/tridium/" in path.replace("\\", "/"):
            continue
        key = (cls, mod, path)
        hits_by_file.setdefault(key, []).append(ln)

    if not hits_by_file:
        msg = "  No external examples found for '{}'".format(class_name)
        if exclude_tridium:
            msg += " (retry without --exclude-tridium?)"
        print(msg + ".")
        return

    pattern_lc = pattern.lower() if pattern else None
    examples = []
    seen_methods = set()
    files_scanned = 0
    MAX_FILES_SCAN = 250  # safety cap to avoid scanning 51K files

    for (cls, mod, path), line_nos in hits_by_file.items():
        if files_scanned >= MAX_FILES_SCAN:
            break
        files_scanned += 1

        method_lines = _get_class_method_lines(method_index, cls, mod)
        if not method_lines:
            continue

        src = _read_source(path)
        if not src:
            continue

        for hit_line in line_nos:
            enclosing = _find_enclosing_method(method_lines, hit_line)
            if not enclosing:
                continue
            decl_line, method_name = enclosing

            key = (path, decl_line)
            if key in seen_methods:
                continue
            seen_methods.add(key)

            body = _extract_method_body(src, decl_line)
            if not body:
                continue
            start_idx, end_idx = body

            # Verify the hit actually lies inside the method
            if not (start_idx < hit_line <= end_idx):
                continue

            body_lines = src[start_idx:end_idx]
            if len(body_lines) < min_lines:
                continue

            body_text = "".join(body_lines)
            if pattern_lc and pattern_lc not in body_text.lower():
                continue

            score = _score_snippet(body_text, class_name)
            examples.append({
                "class": cls,
                "module": mod,
                "path": path,
                "method": method_name,
                "start_line": start_idx + 1,
                "end_line": end_idx,
                "body": [line.rstrip("\n") for line in body_lines],
                "score": score,
            })

    if not examples:
        msg = "  No method bodies matched for '{}'".format(class_name)
        if pattern:
            msg += " (pattern='{}')".format(pattern)
        print(msg + ".")
        return

    examples.sort(key=lambda e: -e["score"])
    selected = examples[:top]

    if as_json:
        print(json.dumps({
            "class": class_name,
            "total_candidates": len(examples),
            "files_scanned": files_scanned,
            "examples": selected,
        }, indent=2, ensure_ascii=False))
        return

    _print_examples(class_name, selected, len(examples), files_scanned, pattern)
