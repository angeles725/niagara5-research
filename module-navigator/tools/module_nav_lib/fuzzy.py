"""
Fuzzy/Semantic Search commands for Module Navigator (Phase 22).

Commands:
  find <query>                    Fuzzy search in class names (camelCase-aware)
  find <query> --source           Also search in source tokens (slower)
  find <query> --module <mod>     Filter by module

Builds camelCase token index in-memory from class-index.json.
No builder needed.
"""

import os
import re
import sqlite3
from collections import defaultdict


# ---------------------------------------------------------------------------
# CamelCase splitter
# ---------------------------------------------------------------------------

_CAMEL_RE = re.compile(
    r'[A-Z][a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)|[a-z]+|[A-Z]+|\d+'
)


def _split_camel(name):
    """Split a camelCase/PascalCase name into lowercase tokens.

    Examples:
      BAlarmService     -> ['b', 'alarm', 'service']
      BacnetWritePropertyRequest -> ['bacnet', 'write', 'property', 'request']
      BLinkPad          -> ['b', 'link', 'pad']
      HTTPSConnection   -> ['https', 'connection']
    """
    return [m.lower() for m in _CAMEL_RE.findall(name)]


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached)
# ---------------------------------------------------------------------------

_camel_cache = None  # {class_name: [tokens_lower]}
_class_modules = None  # {class_name: module_name}


def _build_camel_index(base_dir):
    """Build in-memory camelCase index from class-index.json."""
    global _camel_cache, _class_modules
    if _camel_cache is not None:
        return _camel_cache, _class_modules

    from module_nav_lib.class_search import load_class_index
    ci_data = load_class_index(base_dir)
    if not ci_data:
        return {}, {}

    classes = ci_data.get("classes", {})
    camel_idx = {}
    mod_map = {}

    for class_name, entries in classes.items():
        tokens = _split_camel(class_name)
        camel_idx[class_name] = tokens

        # Get module from first top-level entry
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            mod_map[class_name] = top[0].get("module", "?")
        elif entries:
            mod_map[class_name] = entries[0].get("module", "?")
        else:
            mod_map[class_name] = "?"

    _camel_cache = camel_idx
    _class_modules = mod_map
    return camel_idx, mod_map


# ---------------------------------------------------------------------------
# Scoring algorithm
# ---------------------------------------------------------------------------

def _score_class(class_tokens, query_words):
    """Score a class against query words.

    Returns (score, matched_count) where:
      - score > 0 means all query words matched
      - Higher score = better match
      - 0 means not all words matched

    Scoring:
      +10 per exact token match (query word == class token)
      +5  per prefix match (class token starts with query word, len>=3)
      +3  per substring match (query word found within a class token)
      +2  bonus for consecutive token matches
    """
    if not query_words or not class_tokens:
        return 0, 0

    matched = 0
    total_score = 0
    prev_match_idx = -2  # track consecutive matches

    for qw in query_words:
        best = 0
        best_idx = -1

        for idx, ct in enumerate(class_tokens):
            if ct == qw:
                # Exact match
                if 10 > best:
                    best = 10
                    best_idx = idx
            elif ct.startswith(qw) and len(qw) >= 2:
                # Prefix match
                if 5 > best:
                    best = 5
                    best_idx = idx
            elif qw in ct and len(qw) >= 3:
                # Substring match
                if 3 > best:
                    best = 3
                    best_idx = idx

        if best > 0:
            matched += 1
            total_score += best
            # Consecutive bonus
            if best_idx == prev_match_idx + 1:
                total_score += 2
            prev_match_idx = best_idx

    # Only return score if ALL query words matched
    if matched < len(query_words):
        return 0, matched

    # Bonus: penalize long class names (prefer concise matches)
    length_penalty = max(0, len(class_tokens) - len(query_words) - 2) * 0.5
    total_score -= length_penalty

    return total_score, matched


# ---------------------------------------------------------------------------
# Source-level search via token-index.db
# ---------------------------------------------------------------------------

def _search_source_tokens(base_dir, query_words, module_filter=None, limit=50):
    """Search in token-index.db for classes containing all query words."""
    db_path = os.path.join(base_dir, "indexes", "token-index.db")
    if not os.path.isfile(db_path):
        print("  token-index.db not found — --source mode unavailable.")
        print("  Run: python tools/build_token_index.py")
        return []

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA query_only = ON")
    cur = conn.cursor()

    # For each query word, get the set of (file_id, class_name) that contain it
    sets_per_word = []
    for qw in query_words:
        # Use LIKE for prefix matching on tokens
        cur.execute("""
            SELECT DISTINCT p.file_id, f.class_name
            FROM postings p
            JOIN files f ON p.file_id = f.id
            WHERE p.token LIKE ? || '%'
            LIMIT 10000
        """, (qw,))
        rows = cur.fetchall()
        file_set = set()
        for fid, cname in rows:
            file_set.add((fid, cname))
        sets_per_word.append(file_set)

    conn.close()

    if not sets_per_word:
        return []

    # Intersect: only classes that contain ALL query words
    result_set = sets_per_word[0]
    for s in sets_per_word[1:]:
        result_set = result_set & s

    # Build results with module info
    camel_idx, mod_map = _build_camel_index(base_dir)

    results = []
    for fid, cname in result_set:
        mod = mod_map.get(cname, "?")
        if module_filter and mod != module_filter:
            continue
        results.append((cname, mod))

    # Sort by class name, deduplicate by class name
    seen = set()
    unique_results = []
    for cname, mod in sorted(results, key=lambda x: x[0]):
        if cname not in seen:
            seen.add(cname)
            unique_results.append((cname, mod))

    return unique_results[:limit]


# ---------------------------------------------------------------------------
# cmd_find — main command
# ---------------------------------------------------------------------------

def cmd_find(base_dir, query, source_mode=False, module_filter=None, limit=50):
    """Fuzzy search in class names (and optionally source tokens)."""
    if not query or not query.strip():
        print("")
        print("  Usage: find <query> [--source] [--module <mod>] [-n N]")
        print("")
        print("  Examples:")
        print("    find alarm service")
        print("    find link dialog --source")
        print("    find bacnet write --module bacnet-rt")
        print("")
        return

    # Parse query into words
    query_words = [w.lower() for w in query.strip().split() if w]
    if not query_words:
        return

    # --- Phase 1: Class name fuzzy search ---
    camel_idx, mod_map = _build_camel_index(base_dir)
    if not camel_idx:
        return

    # Score all classes
    scored = []
    for class_name, tokens in camel_idx.items():
        if module_filter and mod_map.get(class_name, "?") != module_filter:
            continue

        score, matched = _score_class(tokens, query_words)
        if score > 0:
            mod = mod_map.get(class_name, "?")
            scored.append((score, class_name, mod, tokens))

    # Sort by score descending, then by class name length (shorter = more relevant)
    scored.sort(key=lambda x: (-x[0], len(x[1])))

    # --- Phase 2: Source token search (if --source) ---
    source_results = []
    source_only = []
    if source_mode:
        source_results = _search_source_tokens(
            base_dir, query_words, module_filter, limit=limit * 2)
        # Find classes in source but NOT in name results
        name_set = set(s[1] for s in scored)
        source_only = [(c, m) for c, m in source_results if c not in name_set]

    # --- Print results ---
    name_count = min(len(scored), limit)
    source_count = min(len(source_only), limit)
    total = name_count + source_count

    print("")
    print("  FUZZY SEARCH: \"{}\"".format(" ".join(query_words)))
    print("  " + "=" * 60)

    if module_filter:
        print("  Module filter: {}".format(module_filter))

    if not scored and not source_only:
        print("")
        print("  No matches found.")
        if not source_mode:
            print("  Try: find {} --source  (searches source code too)".format(
                " ".join(query_words)))
        print("")
        return

    # Name matches
    if scored:
        print("")
        print("  CLASS NAME MATCHES ({} of {}):".format(name_count, len(scored)))
        print("  {:>5s}  {:40s}  {:25s}  {}".format(
            "Score", "Class", "Module", "Tokens"))
        print("  " + "-" * 90)

        for i, (score, class_name, mod, tokens) in enumerate(scored[:limit]):
            # Highlight matched tokens
            highlighted = []
            for t in tokens:
                is_match = False
                for qw in query_words:
                    if t == qw or t.startswith(qw) or (len(qw) >= 3 and qw in t):
                        is_match = True
                        break
                if is_match:
                    highlighted.append("[{}]".format(t.upper()))
                else:
                    highlighted.append(t)
            token_str = " ".join(highlighted)

            print("  {:>5.1f}  {:40s}  {:25s}  {}".format(
                score, class_name[:40], mod[:25], token_str))

        if len(scored) > limit:
            print("  ... and {} more (use -n to show more)".format(
                len(scored) - limit))

    # Source matches (only classes not already in name results)
    if source_only:
        print("")
        print("  SOURCE TOKEN MATCHES ({} additional):".format(
            min(len(source_only), limit)))
        print("  {:40s}  {}".format("Class", "Module"))
        print("  " + "-" * 70)

        for cname, mod in source_only[:limit]:
            print("  {:40s}  {}".format(cname[:40], mod))

        if len(source_only) > limit:
            print("  ... and {} more".format(len(source_only) - limit))

    print("")
    print("  Total: {} matches ({} by name{})".format(
        name_count + source_count,
        name_count,
        ", {} by source".format(source_count) if source_mode else ""))
    print("")
