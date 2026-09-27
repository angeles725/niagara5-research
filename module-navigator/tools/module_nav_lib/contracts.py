"""
Integration Contract extraction for Module Navigator (Batch 4, Gap #2).

Extracts the real integration contract of a class from the decompiled corpus:
  - Required imports (top companion classes co-appearing in external importers)
  - Typical instantiation pattern (regex-classified from real source snippets)
  - Lifecycle category (station singleton / component / plain)
  - Entry-point methods (>=N external callers via callgraph)
  - Anti-patterns / misuse warnings

Commands:
  integration-contract <class>
    [--min-callers N]   External caller threshold for entry-points (default 5)
    [--json]            Structured JSON output

Reuses existing indexes (no new builders):
  class-index.json, xref-index.json, method-index.json,
  callgraph-index.json, inheritance.json, token-index.db
"""

import json
import os
import re
import sqlite3
from collections import Counter


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached per process)
# ---------------------------------------------------------------------------

_class_index_cache = None
_xref_cache = None
_method_index_cache = None
_inheritance_cache = None
_source_root_cache = None


def _load_json(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print("  ERROR loading {}: {}".format(os.path.basename(path), exc))
        return None


def _load_class_index(base_dir):
    global _class_index_cache, _source_root_cache
    if _class_index_cache is not None:
        return _class_index_cache
    data = _load_json(os.path.join(base_dir, "indexes", "class-index.json"))
    if data:
        _class_index_cache = data
        _source_root_cache = data.get("_meta", {}).get("source", "")
    return _class_index_cache


def _load_xref(base_dir):
    global _xref_cache
    if _xref_cache is not None:
        return _xref_cache
    _xref_cache = _load_json(
        os.path.join(base_dir, "indexes", "xref-index.json"))
    return _xref_cache


def _load_method_index(base_dir):
    global _method_index_cache
    if _method_index_cache is not None:
        return _method_index_cache
    _method_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "method-index.json"))
    return _method_index_cache


def _load_inheritance(base_dir):
    global _inheritance_cache
    if _inheritance_cache is not None:
        return _inheritance_cache
    _inheritance_cache = _load_json(
        os.path.join(base_dir, "indexes", "inheritance.json"))
    return _inheritance_cache


def _open_token_db(base_dir):
    """Open token-index.db read-only. Caller must close it."""
    path = os.path.join(base_dir, "indexes", "token-index.db")
    if not os.path.isfile(path):
        return None
    try:
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA query_only=ON")
        return conn
    except Exception:
        return None


def _get_called_by(base_dir):
    """Load callgraph and return the reverse index (callee -> callers).

    Reuses callgraph.py's module-level caches so subsequent calls are free.
    """
    from module_nav_lib.callgraph import load_callgraph, _build_called_by
    cg = load_callgraph(base_dir)
    if not cg:
        return None
    return _build_called_by(cg)


# ---------------------------------------------------------------------------
# Class resolution helpers
# ---------------------------------------------------------------------------

def _resolve_class(ci_data, class_name):
    """Return (resolved_name, top_entry) or (None, None).

    Prefers top-level entries that are NOT in docSource-doc (which is a
    mirror of the real sources).
    """
    if not ci_data:
        return None, None
    classes = ci_data.get("classes", {})
    entries = classes.get(class_name)
    if not entries:
        name_lower = class_name.lower()
        for k, v in classes.items():
            if k.lower() == name_lower:
                class_name = k
                entries = v
                break
    if not entries:
        return None, None

    for e in entries:
        if e.get("outer_class") is None and e.get("module") != "docSource-doc":
            return class_name, e
    for e in entries:
        if e.get("outer_class") is None:
            return class_name, e
    return class_name, entries[0]


def _get_class_module(ci_classes, class_name):
    """Return preferred module for a class (skipping docSource-doc)."""
    entries = ci_classes.get(class_name)
    if not entries:
        return None
    for e in entries:
        if e.get("outer_class") is None and e.get("module") != "docSource-doc":
            return e.get("module")
    for e in entries:
        if e.get("outer_class") is None:
            return e.get("module")
    return entries[0].get("module") if entries else None


# ---------------------------------------------------------------------------
# Source-file reading (bounded LRU-ish cache)
# ---------------------------------------------------------------------------

_file_cache = {}
_FILE_CACHE_MAX = 80


def _read_source(rel_path):
    """Read a source file relative to the class-index source root."""
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
# Block 1 -- Required imports (companion class ranking)
# ---------------------------------------------------------------------------

def _extract_companion_imports(xref, class_name, external_importers, top=10):
    """Rank B-prefixed companion classes co-imported by external importers."""
    class_imports = xref.get("class_imports", {})
    counter = Counter()
    for imp in external_importers:
        for co in class_imports.get(imp, []):
            if co == class_name:
                continue
            if not co.startswith("B"):
                continue
            counter[co] += 1
    return counter.most_common(top)


# ---------------------------------------------------------------------------
# Block 2 -- Instantiation pattern classification
# ---------------------------------------------------------------------------

_PATTERN_LABELS = {
    "ord_resolve": "BOrd.make(...) + resolve().get()",
    "get_service": "getService({}.TYPE)",
    "new_direct":  "new {}(...)",
    "cast_parent": "cast from parent resolve/getter",
    "other":       "other / unclassified",
}


def _classify_pattern(context_lines, class_name):
    """Classify an instantiation snippet into a category (first match wins)."""
    text = " ".join(line.rstrip("\n") for line in context_lines)
    norm = re.sub(r'\s+', ' ', text)

    # new_direct first (used for anti-pattern detection)
    if re.search(r'\bnew\s+' + re.escape(class_name) + r'\s*\(', norm):
        return "new_direct"

    # ord_resolve: BOrd.make(...) + .resolve(...)
    if re.search(r'\bBOrd\s*\.\s*make\s*\(', norm) and \
       re.search(r'\.\s*resolve\s*\(', norm):
        return "ord_resolve"

    # get_service
    if re.search(r'\bgetService\s*\(\s*' + re.escape(class_name) +
                 r'\s*\.\s*TYPE', norm):
        return "get_service"
    if re.search(r'\bgetService\s*\([^)]*' + re.escape(class_name), norm):
        return "get_service"

    # cast to class_name near a resolve/getter call
    if re.search(r'\(\s*' + re.escape(class_name) + r'\s*\)\s*[\w.]+', norm):
        return "cast_parent"

    return "other"


def _extract_context(src_lines, line_no, before=2, after=3):
    idx = line_no - 1
    start = max(0, idx - before)
    end = min(len(src_lines), idx + after + 1)
    return [src_lines[i] for i in range(start, end)], start


def _extract_instantiation_patterns(base_dir, class_name, external_importers,
                                     max_files=60):
    """Scan external-importer source files via token-index and classify."""
    ext_set = set(external_importers)
    if not ext_set:
        return Counter(), {}

    conn = _open_token_db(base_dir)
    if not conn:
        return Counter(), {}

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
    except sqlite3.DatabaseError:
        conn.close()
        return Counter(), {}
    conn.close()

    allowed_files = set()
    counter = Counter()
    samples = {}

    for cls, mod, path, ln in rows:
        if cls == class_name or cls not in ext_set:
            continue
        if path not in allowed_files:
            if len(allowed_files) >= max_files:
                continue
            allowed_files.add(path)

        src = _read_source(path)
        if not src:
            continue
        context, ctx_start = _extract_context(src, ln, before=2, after=3)
        category = _classify_pattern(context, class_name)
        counter[category] += 1
        if category not in samples and category != "other":
            samples[category] = {
                "class": cls,
                "module": mod,
                "path": path,
                "line": ln,
                "start_line": ctx_start + 1,
                "lines": [line.rstrip("\n") for line in context],
            }

    return counter, samples


# ---------------------------------------------------------------------------
# Block 3 -- Lifecycle classification
# ---------------------------------------------------------------------------

def _compute_lifecycle(class_name, top_entry, inheritance_data):
    if not inheritance_data:
        return {
            "category": "unknown",
            "reason": "inheritance.json not available",
            "advice": [],
        }

    chain = inheritance_data.get("class_to_chain", {}).get(class_name, [])
    chain_full = [class_name] + chain
    extends = top_entry.get("extends") or ""

    if "BAbstractService" in chain_full or extends == "BAbstractService":
        return {
            "category": "station_singleton",
            "reason": "extends BAbstractService (station singleton)",
            "advice": [
                "Do NOT instantiate -- resolve via BOrd or getService(TYPE)",
                "No start/stop needed from consumers",
            ],
        }

    if any(c in chain_full for c in ("BComponent", "BComplex")):
        return {
            "category": "component",
            "reason": "extends BComponent/BComplex (Niagara component)",
            "advice": [
                "Instantiate normally or attach as slot",
                "Lifecycle handled by station (started/stopped hooks)",
            ],
        }

    return {
        "category": "plain",
        "reason": "not a Niagara service or component",
        "advice": ["Standard Java instantiation"],
    }


# ---------------------------------------------------------------------------
# Block 4 -- Entry-point methods (external callers via callgraph)
# ---------------------------------------------------------------------------

def _extract_entry_points(class_name, method_index, called_by, min_callers=5):
    if called_by is None:
        return []
    class_methods = method_index.get("class_methods", {})
    methods_map = method_index.get("methods", {})

    results = []
    for mname in class_methods.get(class_name, []):
        key = "{}.{}".format(class_name, mname)
        callers = called_by.get(key)
        if not callers:
            continue
        external_classes = set()
        for c in callers:
            dot = c.rfind(".")
            if dot <= 0:
                continue
            caller_cls = c[:dot]
            if caller_cls != class_name:
                external_classes.add(caller_cls)
        if len(external_classes) < min_callers:
            continue

        sig = mname + "(...)"
        modifiers = []
        for entry in methods_map.get(mname, []):
            if entry.get("class") == class_name:
                sig = entry.get("signature", sig)
                modifiers = entry.get("modifiers", [])
                break

        results.append({
            "name": mname,
            "signature": sig,
            "modifiers": modifiers,
            "external_callers": len(external_classes),
        })

    results.sort(key=lambda r: -r["external_callers"])
    return results


def _extract_virtual_entry_points(class_name, method_index, called_by,
                                  inheritance, min_callers=5):
    """Entry-points with virtual dispatch aggregation (--resolve-virtual)."""
    from module_nav_lib.virtual_dispatch import aggregate_method_callers

    class_methods = method_index.get("class_methods", {})
    methods_map = method_index.get("methods", {})
    results = []

    for mname in class_methods.get(class_name, []):
        agg = aggregate_method_callers(
            class_name, mname, inheritance, method_index, called_by)
        total = len(agg["total_unique"])
        if total < min_callers:
            continue

        sig = mname + "(...)"
        modifiers = []
        for entry in methods_map.get(mname, []):
            if entry.get("class") == class_name:
                sig = entry.get("signature", sig)
                modifiers = entry.get("modifiers", [])
                break

        direct_count = len(agg["direct"])
        virtual_count = total - direct_count

        results.append({
            "name": mname,
            "signature": sig,
            "modifiers": modifiers,
            "external_callers": total,
            "direct_callers": direct_count,
            "virtual_callers": virtual_count,
            "overrider_count": len(agg["overriders"]),
        })

    results.sort(key=lambda r: -r["external_callers"])
    return results


# ---------------------------------------------------------------------------
# Block 5 -- Misuse / anti-pattern warnings
# ---------------------------------------------------------------------------

def _detect_warnings(class_name, ci_classes, method_index, called_by,
                     lifecycle, pattern_counter):
    warnings = []

    # 1. Direct `new` on a station singleton
    if lifecycle["category"] == "station_singleton":
        new_count = pattern_counter.get("new_direct", 0)
        if new_count > 0:
            warnings.append(
                "{} external usage(s) detected of `new {}(...)` -- this class "
                "is a station singleton; use BOrd.make(\"station:|slot:/Services"
                "/...\") or getService({}.TYPE) instead".format(
                    new_count, class_name, class_name))

    # 2. Subclasses of a station singleton
    if lifecycle["category"] == "station_singleton":
        subclasses = []
        for cname, entries in ci_classes.items():
            if cname == class_name:
                continue
            for e in entries:
                if e.get("outer_class") is not None:
                    continue
                if e.get("extends") == class_name:
                    subclasses.append(cname)
                    break
        if subclasses:
            sample = ", ".join(sorted(subclasses)[:5])
            more = " (+{} more)".format(len(subclasses) - 5) if len(subclasses) > 5 else ""
            warnings.append(
                "{} subclass(es) extend {}: {}{} -- subclassing a service "
                "singleton is rarely correct".format(
                    len(subclasses), class_name, sample, more))

    # 3. Private methods with external callers (visibility / reflection smell)
    if called_by is not None:
        methods_map = method_index.get("methods", {})
        class_methods = method_index.get("class_methods", {}).get(class_name, [])
        private_external = []
        for mname in class_methods:
            entry = None
            for e in methods_map.get(mname, []):
                if e.get("class") == class_name:
                    entry = e
                    break
            if not entry or "private" not in entry.get("modifiers", []):
                continue
            key = "{}.{}".format(class_name, mname)
            ext_count = 0
            for c in called_by.get(key, []):
                dot = c.rfind(".")
                if dot > 0 and c[:dot] != class_name:
                    ext_count += 1
            if ext_count > 0:
                private_external.append((mname, ext_count))
        if private_external:
            private_external.sort(key=lambda x: -x[1])
            desc = ", ".join("{} ({}x)".format(m, n)
                             for m, n in private_external[:3])
            warnings.append(
                "Private method(s) called externally: {} -- possible "
                "reflection, inner-class access, or visibility bug".format(desc))

    return warnings


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _fmt_modifiers(modifiers):
    if not modifiers:
        return ""
    tags = []
    for m in modifiers:
        if m in ("public", "protected", "private", "static", "abstract", "final"):
            tags.append(m)
    return " ".join(tags)


def _print_contract(class_name, target_module, target_package, all_importers,
                    external, top_companions, pattern_counter, pattern_samples,
                    lifecycle, entry_points, warnings):
    print("")
    print("  " + "=" * 68)
    print("  INTEGRATION CONTRACT: {}".format(class_name))
    print("  " + "=" * 68)
    print("  Package:           {}".format(target_package))
    print("  Module:            {}".format(target_module))
    print("  Importers (total): {}".format(len(all_importers)))
    print("  External (other modules): {}".format(len(external)))
    print("")

    # --- Required imports ---
    print("  REQUIRED IMPORTS  (top companions from {} external importers)".format(
        len(external)))
    print("  " + "-" * 68)
    if top_companions:
        for cls, count in top_companions:
            print("    {:<35s}  {:>4d} importers".format(cls, count))
    else:
        print("    (no external importers to learn from)")
    print("")

    # --- Instantiation patterns ---
    total_classified = sum(pattern_counter.values())
    print("  TYPICAL INSTANTIATION PATTERN  ({} usages classified)".format(
        total_classified))
    print("  " + "-" * 68)
    if not pattern_counter:
        print("    (no classified usages found)")
    else:
        ranked = pattern_counter.most_common()
        top_cat, top_count = ranked[0]
        label = _PATTERN_LABELS.get(top_cat, top_cat).format(class_name)
        print("    TOP: {}  ({}/{} external usages)".format(
            label, top_count, total_classified))
        sample = pattern_samples.get(top_cat)
        if sample:
            print("")
            print("    From: {}.java ({})".format(sample["class"], sample["module"]))
            print("")
            for idx, line in enumerate(sample["lines"]):
                lineno = sample["start_line"] + idx
                display = line if len(line) <= 110 else line[:107] + "..."
                print("      {:>5d} | {}".format(lineno, display))
        if len(ranked) > 1:
            print("")
            print("    ALTERNATIVE PATTERNS:")
            for cat, cnt in ranked[1:]:
                label = _PATTERN_LABELS.get(cat, cat).format(class_name)
                print("      {:<40s}  {:>4d} usages".format(label, cnt))
    print("")

    # --- Lifecycle ---
    print("  LIFECYCLE")
    print("  " + "-" * 68)
    print("    Category: {}".format(lifecycle["category"]))
    print("    Reason:   {}".format(lifecycle["reason"]))
    for a in lifecycle.get("advice", []):
        print("    - {}".format(a))
    print("")

    # --- Entry-point methods ---
    has_virtual = any("virtual_callers" in ep for ep in entry_points)
    header = "ENTRY-POINT METHODS"
    if has_virtual:
        header += "  (--resolve-virtual)"
    print("  {}  ({} method(s) with external callers)".format(
        header, len(entry_points)))
    print("  " + "-" * 68)
    if not entry_points:
        print("    (no methods meet the external-callers threshold)")
    else:
        for ep in entry_points[:15]:
            mods = _fmt_modifiers(ep["modifiers"])
            mods_str = " [{}]".format(mods) if mods else ""
            sig = ep["signature"]
            if len(sig) > 50:
                sig = sig[:47] + "..."
            virt_note = ""
            if ep.get("virtual_callers", 0) > 0:
                virt_note = " ({} direct + {} virtual)".format(
                    ep["direct_callers"], ep["virtual_callers"])
            print("    {:<52s}  {:>4d} callers{}{}".format(
                sig, ep["external_callers"], mods_str, virt_note))
        if len(entry_points) > 15:
            print("    ... ({} more)".format(len(entry_points) - 15))
    print("")

    # --- Warnings ---
    print("  WARNINGS (common misuse)")
    print("  " + "-" * 68)
    if warnings:
        for w in warnings:
            # Wrap long warnings at ~64 chars
            words = w.split(" ")
            line = "    !! "
            first = True
            for word in words:
                if len(line) + len(word) + 1 > 72 and not first:
                    print(line)
                    line = "       " + word
                else:
                    line = (line + " " + word) if not first else (line + word)
                    first = False
            if line.strip():
                print(line)
    else:
        print("    (no anti-patterns detected)")
    print("")

    # --- Next steps ---
    print("  NEXT STEPS")
    print("  " + "-" * 68)
    print("    example-mine {} --top 3       Full usage method bodies".format(
        class_name))
    print("    methods {}                   All class methods".format(class_name))
    print("    compare {}                   Docs vs impl vs station".format(
        class_name))
    print("")


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_integration_contract(base_dir, class_name, min_callers=5,
                             as_json=False, resolve_virtual=False):
    """Extract integration contract for a class from the decompiled corpus."""
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: class-index.json not found.")
        return
    ci_classes = ci_data.get("classes", {})

    resolved, top_entry = _resolve_class(ci_data, class_name)
    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        suggestions = [c for c in ci_classes
                       if class_name.lower() in c.lower()][:10]
        if suggestions:
            print("  Did you mean: {}".format(", ".join(suggestions)))
        return
    class_name = resolved

    xref = _load_xref(base_dir)
    if not xref:
        print("  ERROR: xref-index.json not found.")
        return

    method_index = _load_method_index(base_dir)
    if not method_index:
        print("  ERROR: method-index.json not found.")
        return

    inheritance = _load_inheritance(base_dir)

    target_module = top_entry.get("module", "")
    target_package = top_entry.get("package", "")

    # Split importers: external vs same-module
    all_importers = xref.get("class_imported_by", {}).get(class_name, [])
    external = []
    for imp in all_importers:
        imp_mod = _get_class_module(ci_classes, imp)
        if imp_mod and imp_mod != target_module and imp_mod != "docSource-doc":
            external.append(imp)

    # Block 1: companion imports
    top_companions = _extract_companion_imports(xref, class_name, external, top=10)

    # Block 2: instantiation patterns
    pattern_counter, pattern_samples = _extract_instantiation_patterns(
        base_dir, class_name, external)

    # Block 3: lifecycle
    lifecycle = _compute_lifecycle(class_name, top_entry, inheritance)

    # Block 4: callgraph-based entry points (loads callgraph on demand)
    called_by = _get_called_by(base_dir)
    if resolve_virtual and inheritance:
        entry_points = _extract_virtual_entry_points(
            class_name, method_index, called_by, inheritance,
            min_callers=min_callers)
    else:
        entry_points = _extract_entry_points(
            class_name, method_index, called_by,
            min_callers=min_callers)

    # Block 5: warnings (reuses the loaded called_by)
    warnings = _detect_warnings(class_name, ci_classes, method_index,
                                called_by, lifecycle, pattern_counter)

    if as_json:
        result = {
            "class": class_name,
            "package": target_package,
            "module": target_module,
            "importers": {
                "total": len(all_importers),
                "external": len(external),
                "internal": len(all_importers) - len(external),
            },
            "required_imports": [{"class": c, "count": n}
                                 for c, n in top_companions],
            "instantiation_patterns": dict(pattern_counter),
            "instantiation_samples": pattern_samples,
            "lifecycle": lifecycle,
            "entry_points": entry_points,
            "warnings": warnings,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    _print_contract(class_name, target_module, target_package, all_importers,
                    external, top_companions, pattern_counter, pattern_samples,
                    lifecycle, entry_points, warnings)
