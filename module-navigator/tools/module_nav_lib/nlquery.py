"""
Natural Language Query for Module Navigator (Phase 31).

Commands:
  ask <question>     Answer a question by searching all indexes heuristically

Tokenizes the question, removes stop-words, searches class names, method names,
token-index, string-index, annotations, and inheritance. Ranks results and
assembles a structured response.

No LLM required — pure heuristic keyword extraction + index lookups.
No builder needed — uses all existing indexes on-demand.
"""

import os
import re
import sqlite3
from collections import defaultdict


# ---------------------------------------------------------------------------
# Stop-words (EN + ES + Java/Niagara noise)
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset([
    # English
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "its",
    "they", "them", "their", "this", "that", "these", "those",
    "what", "which", "who", "whom", "where", "when", "why", "how",
    "if", "then", "else", "so", "but", "and", "or", "not", "no", "nor",
    "of", "in", "on", "at", "to", "for", "with", "by", "from", "about",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "up", "down", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "only", "own",
    "same", "than", "too", "very", "just",
    # Spanish
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "en", "es", "son", "fue", "como", "que", "por", "para",
    "con", "se", "su", "sus", "al", "lo", "le", "les",
    "hay", "tiene", "hace", "puede", "donde", "cuando", "cual",
    # Java/code noise
    "class", "method", "function", "interface", "abstract",
    "public", "private", "protected", "static", "final",
    "void", "return", "new", "null", "true", "false",
    "java", "javax", "import", "package",
])

# Question-type keywords that hint at what kind of answer to produce
_QUESTION_INTENTS = {
    "how": "mechanism",      # how does X work -> show methods + callees
    "what": "definition",    # what is X -> show class + slots + hierarchy
    "who": "usage",          # who uses X -> show importers + callers
    "where": "location",     # where is X -> show module + package
    "why": "rationale",      # why X -> show inheritance + patterns
    "list": "enumeration",   # list X -> show all matches
    "show": "enumeration",
    "find": "enumeration",
    "count": "enumeration",
    "which": "enumeration",
    "como": "mechanism",
    "que": "definition",
    "quien": "usage",
    "donde": "location",
    "cuantos": "enumeration",
    "listar": "enumeration",
}

# Domain synonyms: map common terms to Niagara-specific search tokens
_DOMAIN_SYNONYMS = {
    "alarm": ["alarm", "BAlarm"],
    "alarms": ["alarm", "BAlarm"],
    "alarma": ["alarm", "BAlarm"],
    "alarmas": ["alarm", "BAlarm"],
    "point": ["point", "BControlPoint", "BNumericPoint"],
    "points": ["point", "BControlPoint", "BNumericPoint"],
    "punto": ["point", "BControlPoint"],
    "puntos": ["point", "BControlPoint"],
    "driver": ["driver", "BDevice", "BDeviceNetwork"],
    "drivers": ["driver", "BDevice", "BDeviceNetwork"],
    "service": ["service", "BAbstractService"],
    "services": ["service", "BAbstractService"],
    "servicio": ["service", "BAbstractService"],
    "servicios": ["service", "BAbstractService"],
    "schedule": ["schedule", "BWeeklySchedule"],
    "schedules": ["schedule", "BWeeklySchedule"],
    "history": ["history", "BHistoryService"],
    "historico": ["history", "BHistoryService"],
    "network": ["network", "BDeviceNetwork", "BNiagaraNetwork"],
    "bacnet": ["bacnet", "BBacnet"],
    "modbus": ["modbus", "BModbus"],
    "mqtt": ["mqtt", "BMqtt"],
    "web": ["web", "BWebServlet", "servlet"],
    "servlet": ["servlet", "BWebServlet"],
    "ui": ["ui", "view", "BWbView", "BWbComponentView"],
    "view": ["view", "BWbView", "BWbComponentView"],
    "routing": ["routing", "route", "BAlarmRouting"],
    "enrutamiento": ["routing", "route"],
    "serialization": ["serializable", "serialVersionUID"],
    "serializacion": ["serializable", "serialVersionUID"],
    "thread": ["thread", "synchronized", "volatile", "concurrent"],
    "concurrency": ["thread", "synchronized", "volatile", "concurrent"],
    "lifecycle": ["started", "stopped", "changed", "atSteadyState"],
    "ciclo": ["started", "stopped", "changed", "atSteadyState"],
    "config": ["config", "getConfig", "NiagaraProperty", "BOrd"],
    "configuracion": ["config", "getConfig", "NiagaraProperty"],
    "security": ["security", "password", "auth", "credential", "permission"],
    "seguridad": ["security", "password", "auth", "credential"],
    "exception": ["exception", "throws", "catch", "try"],
    "error": ["exception", "error", "throws", "catch"],
    "slot": ["NiagaraProperty", "NiagaraAction", "NiagaraTopic", "slot"],
    "property": ["NiagaraProperty", "property", "slot"],
    "action": ["NiagaraAction", "action", "doInvoke"],
    "topic": ["NiagaraTopic", "topic", "fire"],
}

# CamelCase splitter
_CAMEL_RE = re.compile(
    r'[A-Z][a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)|[a-z]+|[A-Z]+|\d+'
)


def _split_camel(name):
    """Split CamelCase name into lowercase tokens."""
    return [m.lower() for m in _CAMEL_RE.findall(name)]


# ---------------------------------------------------------------------------
# Question parsing
# ---------------------------------------------------------------------------

def _parse_question(question):
    """Parse question into (intent, keywords, expanded_tokens).

    Returns:
      intent: str - what kind of answer (mechanism, definition, usage, etc.)
      keywords: list - cleaned keywords from the question
      expanded: list - keywords + domain synonym expansions
    """
    # Normalize
    q = question.strip().strip('"').strip("'").strip("?").strip(".").lower()

    # Tokenize
    words = re.findall(r'[a-zA-Z0-9_]+', q)

    # Detect intent from first word
    intent = "general"
    if words:
        first = words[0].lower()
        if first in _QUESTION_INTENTS:
            intent = _QUESTION_INTENTS[first]

    # Remove stop-words
    keywords = [w for w in words if w.lower() not in _STOP_WORDS and len(w) >= 2]

    # Expand with domain synonyms
    expanded = list(keywords)
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in _DOMAIN_SYNONYMS:
            for syn in _DOMAIN_SYNONYMS[kw_lower]:
                if syn.lower() not in [e.lower() for e in expanded]:
                    expanded.append(syn)

    return intent, keywords, expanded


# ---------------------------------------------------------------------------
# Index loaders (on-demand, cached via existing modules)
# ---------------------------------------------------------------------------

def _load_class_index(base_dir):
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


def _load_method_index(base_dir):
    from module_nav_lib.methods import load_method_index
    return load_method_index(base_dir)


def _load_inheritance(base_dir):
    from module_nav_lib.hierarchy import load_inheritance
    return load_inheritance(base_dir)


def _load_annotations(base_dir):
    from module_nav_lib.annotations import load_annotations_index
    return load_annotations_index(base_dir)


def _load_xref(base_dir):
    from module_nav_lib.xref import load_xref
    return load_xref(base_dir)


def _load_callgraph(base_dir):
    from module_nav_lib.callgraph import load_callgraph
    return load_callgraph(base_dir)


# ---------------------------------------------------------------------------
# Search channels
# ---------------------------------------------------------------------------

def _search_classes(base_dir, keywords, limit=20):
    """Search class names using fuzzy matching on keywords."""
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return []

    classes = ci_data.get("classes", {})
    results = []

    kw_lower = [k.lower() for k in keywords]

    for class_name, entries in classes.items():
        tokens = _split_camel(class_name)
        class_lower = class_name.lower()
        score = 0
        matched = 0

        for kw in kw_lower:
            best = 0
            # Check against full class name (case-insensitive)
            if class_lower == kw:
                best = max(best, 15)
            elif kw in class_lower and len(kw) >= 3:
                best = max(best, 4)
            # Check against camelCase tokens
            for ct in tokens:
                if ct == kw:
                    best = max(best, 10)
                elif ct.startswith(kw) and len(kw) >= 2:
                    best = max(best, 5)
                elif kw in ct and len(kw) >= 3:
                    best = max(best, 3)
            if best > 0:
                matched += 1
                score += best

        if matched >= max(1, len(kw_lower) // 2):
            # Get module
            top = [e for e in entries if not e.get("outer_class")]
            mod = top[0].get("module", "?") if top else (
                entries[0].get("module", "?") if entries else "?")
            # Bonus for matching more keywords
            score += matched * 2
            results.append((score, class_name, mod))

    results.sort(key=lambda x: (-x[0], len(x[1])))
    return results[:limit]


def _search_methods(base_dir, keywords, limit=20):
    """Search method names matching keywords."""
    mi_data = _load_method_index(base_dir)
    if not mi_data:
        return []

    methods = mi_data.get("methods", {})
    results = []

    kw_lower = [k.lower() for k in keywords]

    for method_name, defs in methods.items():
        tokens = _split_camel(method_name)
        score = 0
        matched = 0

        for kw in kw_lower:
            for ct in tokens:
                if ct == kw:
                    score += 8
                    matched += 1
                    break
                elif ct.startswith(kw) and len(kw) >= 2:
                    score += 4
                    matched += 1
                    break
                elif kw in ct and len(kw) >= 3:
                    score += 2
                    matched += 1
                    break

        if matched >= 1 and score >= 4:
            n_defs = len(defs)
            # Sample up to 5 modules
            modules = set()
            for d in defs[:50]:
                mod = d.get("module", "?")
                modules.add(mod)

            results.append((score, method_name, n_defs, sorted(modules)[:5]))

    results.sort(key=lambda x: (-x[0], -x[2]))
    return results[:limit]


def _search_tokens_db(base_dir, keywords, limit=10):
    """Search token-index.db for keyword occurrences."""
    db_path = os.path.join(base_dir, "indexes", "token-index.db")
    if not os.path.isfile(db_path):
        return []

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA query_only = ON")
    cur = conn.cursor()

    results = []
    for kw in keywords[:5]:
        if len(kw) < 3:
            continue
        cur.execute("""
            SELECT COUNT(DISTINCT file_id) as cnt
            FROM postings
            WHERE token = ?
        """, (kw,))
        row = cur.fetchone()
        if row and row[0] > 0:
            results.append((kw, row[0]))

        # Also try as prefix
        if len(kw) >= 4:
            cur.execute("""
                SELECT COUNT(DISTINCT file_id) as cnt
                FROM postings
                WHERE token LIKE ? || '%' AND token != ?
                LIMIT 5000
            """, (kw, kw))
            row = cur.fetchone()
            if row and row[0] > 0:
                results.append((kw + "*", row[0]))

    conn.close()
    return results


def _search_strings_db(base_dir, keywords, limit=10):
    """Search string-index.db for keyword occurrences."""
    db_path = os.path.join(base_dir, "indexes", "string-index.db")
    if not os.path.isfile(db_path):
        return []

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA query_only = ON")
    cur = conn.cursor()

    results = []
    for kw in keywords[:5]:
        if len(kw) < 3:
            continue
        try:
            cur.execute("""
                SELECT COUNT(*) as cnt, COUNT(DISTINCT class_name) as cls
                FROM strings
                WHERE value LIKE '%' || ? || '%'
                LIMIT 10000
            """, (kw,))
            row = cur.fetchone()
            if row and row[0] > 0:
                results.append((kw, row[0], row[1]))
        except Exception:
            pass

    conn.close()
    return results


def _search_annotations(base_dir, keywords):
    """Search annotations index for Niagara types matching keywords."""
    ann_data = _load_annotations(base_dir)
    if not ann_data:
        return []

    # annotations-index uses "niagara_types" key (not "types")
    types = ann_data.get("niagara_types", ann_data.get("types", {}))
    results = []

    kw_lower = [k.lower() for k in keywords]

    for class_name, info in types.items():
        module = info.get("module", "")
        tokens = _split_camel(class_name) + [module.lower()]

        matched = 0
        for kw in kw_lower:
            for ct in tokens:
                if kw in ct:
                    matched += 1
                    break

        if matched >= 1:
            props = info.get("properties", [])
            actions = info.get("actions", [])
            topics = info.get("topics", [])
            ntype = "{}:{}".format(module, class_name) if module else class_name
            results.append((matched, class_name, ntype,
                            len(props), len(actions), len(topics)))

    results.sort(key=lambda x: (-x[0], x[1]))
    return results[:10]


def _detect_exact_classes(base_dir, keywords):
    """Detect if any keyword is an exact class name (case-insensitive).
    Returns list of (class_name, module)."""
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return []

    classes = ci_data.get("classes", {})
    results = []

    # Build lowercase lookup if not cached
    lower_map = {}
    for cname in classes:
        lower_map[cname.lower()] = cname

    for kw in keywords:
        # Try exact match first
        if kw in classes:
            matched_name = kw
        elif kw.lower() in lower_map:
            matched_name = lower_map[kw.lower()]
        else:
            continue

        entries = classes[matched_name]
        top = [e for e in entries if not e.get("outer_class")]
        mod = top[0].get("module", "?") if top else (
            entries[0].get("module", "?") if entries else "?")
        results.append((matched_name, mod))

    return results


def _get_class_usage(base_dir, class_name):
    """Get importers and callers for a known class."""
    usage = {"importers": [], "callers": [], "modules": set()}

    # Importers from xref
    xref_data = _load_xref(base_dir)
    if xref_data:
        ci_data = _load_class_index(base_dir)
        ci_classes = ci_data.get("classes", {}) if ci_data else {}

        imported_by = xref_data.get("class_imported_by", {}).get(class_name, [])
        for imp_cls in imported_by[:20]:
            mod = "?"
            if imp_cls in ci_classes:
                entries = ci_classes[imp_cls]
                top = [e for e in entries if not e.get("outer_class")]
                mod = top[0].get("module", "?") if top else (
                    entries[0].get("module", "?") if entries else "?")
            usage["importers"].append((imp_cls, mod))
            usage["modules"].add(mod)

    # Callers from callgraph
    cg_data = _load_callgraph(base_dir)
    if cg_data:
        from module_nav_lib.callgraph import _build_called_by
        called_by = _build_called_by(cg_data)
        prefix = class_name + "."
        caller_set = set()
        for key in called_by:
            if key.startswith(prefix):
                for caller in called_by[key][:10]:
                    caller_set.add(caller)
        usage["callers"] = sorted(caller_set)[:20]

    return usage


def _search_inheritance(base_dir, keywords):
    """Find relevant base classes / interfaces matching keywords."""
    inh_data = _load_inheritance(base_dir)
    if not inh_data:
        return []

    chains = inh_data.get("chains", {})
    results = []

    kw_lower = [k.lower() for k in keywords]

    # Check parent classes that match keywords
    parent_counts = defaultdict(int)
    for class_name, info in chains.items():
        extends = info.get("extends", "")
        if extends:
            for kw in kw_lower:
                if kw in extends.lower():
                    parent_counts[extends] += 1

        impls = info.get("implements", [])
        for iface in impls:
            for kw in kw_lower:
                if kw in iface.lower():
                    parent_counts[iface] += 1

    results = [(count, name) for name, count in parent_counts.items()]
    results.sort(key=lambda x: -x[0])
    return results[:10]


# ---------------------------------------------------------------------------
# Response assembly
# ---------------------------------------------------------------------------

def _assemble_response(intent, keywords, expanded, classes, methods,
                       token_hits, string_hits, ann_hits, inh_hits,
                       exact_classes=None, class_usage=None):
    """Assemble a structured response from multi-channel results."""
    if exact_classes is None:
        exact_classes = []
    if class_usage is None:
        class_usage = {}

    print("")
    print("  NATURAL LANGUAGE QUERY")
    print("  " + "=" * 60)
    print("  Keywords: {}".format(", ".join(keywords)))
    if len(expanded) > len(keywords):
        extra = [e for e in expanded if e not in keywords]
        print("  Expanded: + {}".format(", ".join(extra[:10])))
    print("  Intent:   {}".format(intent))
    print("")

    has_results = False

    # --- Exact class match + usage ---
    if exact_classes:
        has_results = True
        for cname, cmod in exact_classes:
            print("  EXACT CLASS MATCH: {} [{}]".format(cname, cmod))
            print("  " + "-" * 55)
            usage = class_usage.get(cname, {})
            importers = usage.get("importers", [])
            callers = usage.get("callers", [])
            modules = usage.get("modules", set())

            if importers:
                print("    Imported by {} classes in {} modules:".format(
                    len(importers), len(modules)))
                for imp_cls, imp_mod in importers[:10]:
                    print("      {:35s}  [{}]".format(imp_cls[:35], imp_mod))
                if len(importers) > 10:
                    print("      ... and {} more".format(len(importers) - 10))

            if callers:
                print("    Called by {} methods:".format(len(callers)))
                for caller in callers[:10]:
                    print("      {}".format(caller))
                if len(callers) > 10:
                    print("      ... and {} more".format(len(callers) - 10))

            if not importers and not callers:
                print("    (no importers or callers found)")
            print("")

    # --- Relevant classes ---
    if classes:
        has_results = True
        print("  RELEVANT CLASSES ({} found):".format(len(classes)))
        print("  {:>5s}  {:40s}  {}".format("Score", "Class", "Module"))
        print("  " + "-" * 70)
        for score, cname, mod in classes[:15]:
            print("  {:>5.0f}  {:40s}  {}".format(score, cname[:40], mod))
        if len(classes) > 15:
            print("  ... and {} more".format(len(classes) - 15))
        print("")

    # --- Relevant methods ---
    if methods:
        has_results = True
        print("  KEY METHODS ({} found):".format(len(methods)))
        print("  {:>5s}  {:30s}  {:>6s}  {}".format(
            "Score", "Method", "Defs", "Modules"))
        print("  " + "-" * 80)
        for score, mname, ndefs, mods in methods[:15]:
            mod_str = ", ".join(mods[:3])
            if len(mods) > 3:
                mod_str += " +{}".format(len(mods) - 3)
            print("  {:>5.0f}  {:30s}  {:>6,}  {}".format(
                score, mname[:30], ndefs, mod_str))
        if len(methods) > 15:
            print("  ... and {} more".format(len(methods) - 15))
        print("")

    # --- Niagara components (annotations) ---
    if ann_hits:
        has_results = True
        print("  NIAGARA COMPONENTS ({} matches):".format(len(ann_hits)))
        print("  {:30s}  {:25s}  {:>4s}  {:>4s}  {:>4s}".format(
            "Class", "Type", "Prop", "Act", "Top"))
        print("  " + "-" * 75)
        for matched, cname, ntype, np, na, nt in ann_hits[:10]:
            print("  {:30s}  {:25s}  {:>4d}  {:>4d}  {:>4d}".format(
                cname[:30], ntype[:25], np, na, nt))
        print("")

    # --- Inheritance / base classes ---
    if inh_hits:
        has_results = True
        print("  RELATED BASE CLASSES / INTERFACES:")
        for count, name in inh_hits[:8]:
            print("    {:40s}  ({} subclasses match)".format(name, count))
        print("")

    # --- Token index hits ---
    if token_hits:
        has_results = True
        print("  TOKEN INDEX COVERAGE:")
        for entry in token_hits:
            kw = entry[0]
            count = entry[1]
            print("    {:25s}  {:>6,} files contain this token".format(kw, count))
        print("")

    # --- String constant hits ---
    if string_hits:
        has_results = True
        print("  STRING CONSTANT COVERAGE:")
        for kw, total, cls_count in string_hits:
            print("    {:25s}  {:>6,} strings in {:>5,} classes".format(
                kw, total, cls_count))
        print("")

    # --- Suggestions ---
    if has_results and classes:
        print("  SUGGESTED NEXT STEPS:")
        top_class = classes[0][1]
        top_mod = classes[0][2]
        print("    1. profile {}        — full class overview".format(top_class))
        print("    2. source {} --code  — read the source".format(top_class))
        if methods:
            top_method = methods[0][1]
            print("    3. method {}        — who defines this method".format(top_method))
        print("    4. impact {}         — change impact analysis".format(top_class))
        if ann_hits:
            ann_class = ann_hits[0][1]
            print("    5. slots {}          — Niagara properties/actions".format(ann_class))
        print("    6. find {} --source   — deeper fuzzy search".format(
            " ".join(keywords[:3])))
        print("")

    if not has_results:
        print("  No results found for these keywords.")
        print("")
        print("  Tips:")
        print("    - Use more specific terms (class names, method names)")
        print("    - Try: find {} --source".format(" ".join(keywords[:3])))
        print("    - Try: token {}".format(keywords[0] if keywords else "<word>"))
        print("    - Try: grep {}".format(keywords[0] if keywords else "<pattern>"))
        print("")

    # Summary line
    total = len(classes) + len(methods) + len(ann_hits)
    channels = sum([
        1 if classes else 0,
        1 if methods else 0,
        1 if token_hits else 0,
        1 if string_hits else 0,
        1 if ann_hits else 0,
        1 if inh_hits else 0,
    ])
    print("  Summary: {} entities found across {} search channels".format(
        total, channels))
    print("")


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_ask(base_dir, question):
    """Answer a natural language question by searching all indexes."""
    if not question or not question.strip():
        print("")
        print("  Usage: ask <question>")
        print("")
        print("  Examples:")
        print('    ask "how does alarm routing work"')
        print('    ask "what classes handle BACnet communication"')
        print('    ask "who uses BAlarmService"')
        print('    ask "where is the schedule engine"')
        print('    ask "list all point types"')
        print('    ask "como funciona el motor de alarmas"')
        print("")
        return

    # 1. Parse question
    intent, keywords, expanded = _parse_question(question)

    if not keywords:
        print("")
        print("  Could not extract meaningful keywords from the question.")
        print("  Try using more specific terms.")
        print("")
        return

    # 2. Detect exact class names in keywords
    exact_classes = _detect_exact_classes(base_dir, keywords)
    # Filter out short/common words that happen to be class names when multi-keyword
    if len(keywords) > 1:
        exact_classes = [(c, m) for c, m in exact_classes
                         if (len(c) >= 8 or c.startswith('B'))
                         and c[0].isupper()]
    class_usage = {}
    for cname, cmod in exact_classes:
        if intent in ("usage", "definition", "mechanism", "general"):
            class_usage[cname] = _get_class_usage(base_dir, cname)

    # 3. Search across all channels
    # Class/method names use original keywords (short names, don't over-expand)
    # Token/string/annotations use expanded for broader recall
    classes = _search_classes(base_dir, keywords, limit=20)
    methods = _search_methods(base_dir, keywords, limit=20)
    token_hits = _search_tokens_db(base_dir, keywords, limit=10)
    string_hits = _search_strings_db(base_dir, keywords, limit=10)
    ann_hits = _search_annotations(base_dir, expanded)
    inh_hits = _search_inheritance(base_dir, expanded)

    # 4. Assemble and print response
    _assemble_response(intent, keywords, expanded,
                       classes, methods, token_hits, string_hits,
                       ann_hits, inh_hits,
                       exact_classes=exact_classes,
                       class_usage=class_usage)
