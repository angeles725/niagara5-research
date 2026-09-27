"""
Cross-Navigator Unified Search for Module Navigator (Phase 42).

Orchestrates Help Navigator + Module Navigator + BOG Navigator
to search across all three simultaneously and compare perspectives.

Commands:
  unified <query>     Search Help + Module + BOG simultaneously
    [--limit N]       Limit results per source (default 10)
  compare <class>     Docs vs implementation vs station usage
    [--help-dir dir]  Path to Help Navigator
    [--bog-index p]   Path to bog_index.json

Sources:
  Help Navigator   — Public API docs, bajadoc, devguide, slots
  Module Navigator — Decompiled source, 51K+ classes, methods, xref
  BOG Navigator    — Runtime station config, live component instances

No builder required — reads existing indexes on-demand.
"""

import json
import os
import re
from collections import defaultdict


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached)
# ---------------------------------------------------------------------------

_class_index_cache = None
_method_index_cache = None


def _load_json(path):
    """Load a JSON file, return None on failure."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_class_index(base_dir):
    """Load Module Nav class-index.json (cached)."""
    global _class_index_cache
    if _class_index_cache is not None:
        return _class_index_cache
    _class_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "class-index.json"))
    return _class_index_cache


def _load_method_index(base_dir):
    """Load Module Nav method-index.json (cached)."""
    global _method_index_cache
    if _method_index_cache is not None:
        return _method_index_cache
    _method_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "method-index.json"))
    return _method_index_cache


# ---------------------------------------------------------------------------
# Help Navigator search helpers
# ---------------------------------------------------------------------------

def _detect_help_dir(base_dir):
    """Auto-detect Help Navigator directory."""
    parent = os.path.dirname(base_dir)
    candidate = os.path.join(parent, "niagara-help")
    if os.path.isdir(candidate) and os.path.isdir(os.path.join(candidate, "indexes")):
        return candidate
    return None


_help_cache = {}


def _load_help_index(help_dir, filename):
    """Load a Help Navigator JSON index (cached)."""
    key = filename
    if key in _help_cache:
        return _help_cache[key]
    path = os.path.join(help_dir, "indexes", filename)
    data = _load_json(path)
    if data is not None:
        _help_cache[key] = data
    return data


def _search_help(help_dir, query, limit=10):
    """Search Help Navigator for query. Returns list of result dicts."""
    results = []
    if not help_dir:
        return results

    query_lower = query.lower()

    # 1. Search class-index
    ci = _load_help_index(help_dir, "class-index.json")
    if ci:
        for cls_name, entry in ci.items():
            if query_lower in cls_name.lower():
                results.append({
                    "type": "class",
                    "name": cls_name,
                    "package": entry.get("package", ""),
                    "kind": entry.get("type", "class"),
                    "source": "Help Nav",
                })

    # 2. Search method-index
    mi = _load_help_index(help_dir, "method-index.json")
    if mi:
        methods = mi.get("methods", mi)
        if isinstance(methods, dict):
            for mname, entries in methods.items():
                if query_lower in mname.lower():
                    if isinstance(entries, list):
                        for e in entries[:2]:
                            cls = e.get("class", e.get("className", "?"))
                            results.append({
                                "type": "method",
                                "name": mname,
                                "class": cls,
                                "source": "Help Nav",
                            })
                    else:
                        results.append({
                            "type": "method",
                            "name": mname,
                            "source": "Help Nav",
                        })

    # 3. Search devguide TOC
    toc = _load_help_index(help_dir, "devguide-toc.json")
    if toc:
        sections = toc.get("sections", [])
        for section in sections:
            for item in section.get("items", []):
                title = item.get("title", "")
                desc = item.get("description", "")
                if query_lower in title.lower() or query_lower in desc.lower():
                    results.append({
                        "type": "guide",
                        "name": title,
                        "file": item.get("file", ""),
                        "source": "Help Nav",
                    })

    # 4. Search guides-index
    gi = _load_help_index(help_dir, "guides-index.json")
    if gi:
        for folder, info in gi.items():
            topics = info.get("topics", [])
            for topic in topics:
                if isinstance(topic, str) and query_lower in topic.lower():
                    results.append({
                        "type": "guide",
                        "name": topic,
                        "folder": folder,
                        "source": "Help Nav",
                    })

    # De-duplicate by (type, name)
    seen = set()
    deduped = []
    for r in results:
        key = (r["type"], r["name"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return deduped[:limit]


# ---------------------------------------------------------------------------
# Module Navigator search helpers
# ---------------------------------------------------------------------------

def _search_module_nav(base_dir, query, limit=10):
    """Search Module Nav indexes for query. Returns list of result dicts."""
    results = []
    query_lower = query.lower()

    # 1. Search class-index
    ci = _load_class_index(base_dir)
    if ci:
        classes = ci.get("classes", {})
        for cls_name, entries in classes.items():
            if query_lower in cls_name.lower():
                for e in entries:
                    if e.get("outer_class") is None:
                        results.append({
                            "type": "class",
                            "name": cls_name,
                            "package": e.get("package", ""),
                            "module": e.get("module", ""),
                            "kind": e.get("kind", "class"),
                            "lines": e.get("lines", 0),
                            "source": "Module Nav",
                        })
                        break

    # 2. Search method-index (sample — limit to avoid overload)
    mi = _load_method_index(base_dir)
    if mi:
        methods_map = mi.get("methods", {})
        method_hits = 0
        for mname, entries in methods_map.items():
            if query_lower in mname.lower():
                for e in entries[:1]:
                    results.append({
                        "type": "method",
                        "name": mname,
                        "class": e.get("class", "?"),
                        "module": e.get("module", ""),
                        "source": "Module Nav",
                    })
                    method_hits += 1
                    if method_hits >= limit:
                        break
            if method_hits >= limit:
                break

    # De-duplicate
    seen = set()
    deduped = []
    for r in results:
        key = (r["type"], r["name"], r.get("class", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return deduped[:limit]


# ---------------------------------------------------------------------------
# BOG Navigator search helpers
# ---------------------------------------------------------------------------

_bog_cache = None
_bog_path_used = None

# N5 port note: see bog_bridge.py -- the N4 "Reflow-Clean" project path is
# dropped rather than replaced; lookup degrades gracefully when not found.
_BOG_SEARCH_PATHS = [
    lambda base: os.path.join(os.path.dirname(base), "tools", "bog_index.json"),
    lambda base: os.path.join(os.getcwd(), "bog_index.json"),
]


def _find_bog_index(base_dir, explicit_path=None):
    """Find bog_index.json.

    Priority: explicit_path > BOG_INDEX_PATH env var > _BOG_SEARCH_PATHS.
    """
    if explicit_path:
        return explicit_path if os.path.isfile(explicit_path) else None
    env_path = os.environ.get("BOG_INDEX_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    for loc in _BOG_SEARCH_PATHS:
        p = loc(base_dir) if callable(loc) else loc
        if os.path.isfile(p):
            return p
    return None


def _load_bog(base_dir, explicit_path=None):
    """Load BOG index (cached)."""
    global _bog_cache, _bog_path_used
    if _bog_cache is not None:
        return _bog_cache, _bog_path_used
    path = _find_bog_index(base_dir, explicit_path)
    if not path:
        return None, None
    data = _load_json(path)
    if data:
        _bog_cache = data
        _bog_path_used = path
    return _bog_cache, _bog_path_used


def _search_bog(base_dir, query, bog_index_path=None, limit=10):
    """Search BOG index for query. Returns list of result dicts."""
    results = []
    bog, bog_path = _load_bog(base_dir, bog_index_path)
    if not bog:
        return results

    query_lower = query.lower()
    components = bog.get("components", [])

    # Search by type name or path
    type_hits = defaultdict(int)
    path_hits = []

    for comp in components:
        ctype = comp.get("type") or ""
        cpath = comp.get("path") or ""
        cname = comp.get("name") or ""

        if not ctype:
            continue

        # Match against type (after colon)
        type_name = ctype.split(":", 1)[1] if ":" in ctype else ctype
        if query_lower in type_name.lower() or query_lower in cname.lower():
            type_hits[ctype] += 1
            if len(path_hits) < limit * 2:
                path_hits.append({
                    "path": cpath,
                    "name": cname,
                    "type": ctype,
                    "value": comp.get("value", ""),
                })

    # Summarize by type
    for type_spec, count in sorted(type_hits.items(), key=lambda x: -x[1]):
        results.append({
            "type": "component",
            "name": type_spec,
            "count": count,
            "source": "BOG Nav",
        })
        if len(results) >= limit:
            break

    # Add a few path examples
    for ph in path_hits[:min(5, limit)]:
        results.append({
            "type": "instance",
            "name": ph["name"],
            "path": ph["path"],
            "bog_type": ph["type"],
            "value": ph["value"],
            "source": "BOG Nav",
        })

    return results[:limit * 2]


# ---------------------------------------------------------------------------
# unified command
# ---------------------------------------------------------------------------

def cmd_unified(base_dir, query, limit=10, help_dir=None, bog_index_path=None):
    """Search Help + Module + BOG simultaneously."""
    if not query or not query.strip():
        print("  Usage: unified <query>")
        return

    query = query.strip()

    # Auto-detect
    if not help_dir:
        help_dir = _detect_help_dir(base_dir)

    print("")
    print("  " + "=" * 70)
    print("  UNIFIED SEARCH: '{}'".format(query))
    print("  " + "=" * 70)

    # Search all three navigators
    help_results = _search_help(help_dir, query, limit) if help_dir else []
    module_results = _search_module_nav(base_dir, query, limit)
    bog_results = _search_bog(base_dir, query, bog_index_path, limit)

    # Navigator availability
    navs = []
    if help_dir:
        navs.append("Help Nav")
    else:
        navs.append("Help Nav (not available)")
    navs.append("Module Nav")
    bog_data, _ = _load_bog(base_dir, bog_index_path)
    if bog_data:
        navs.append("BOG Nav")
    else:
        navs.append("BOG Nav (not available)")
    print("  Sources: {}".format(" | ".join(navs)))

    total = len(help_results) + len(module_results) + len(bog_results)
    print("  Total hits: {} (Help: {}, Module: {}, BOG: {})".format(
        total, len(help_results), len(module_results), len(bog_results)))
    print("")

    # --- Help Navigator results ---
    if help_dir:
        print("  HELP NAVIGATOR  ({} results)".format(len(help_results)))
        print("  " + "-" * 60)
        if help_results:
            for r in help_results:
                if r["type"] == "class":
                    print("    [class]  {:30s}  {}".format(
                        r["name"], r.get("package", "")))
                elif r["type"] == "method":
                    cls = r.get("class", "")
                    print("    [method] {:30s}  in {}".format(r["name"], cls))
                elif r["type"] == "guide":
                    f = r.get("file") or r.get("folder", "")
                    print("    [guide]  {:30s}  {}".format(r["name"][:30], f))
        else:
            print("    (no results)")
        print("")

    # --- Module Navigator results ---
    print("  MODULE NAVIGATOR  ({} results)".format(len(module_results)))
    print("  " + "-" * 60)
    if module_results:
        for r in module_results:
            if r["type"] == "class":
                print("    [class]  {:30s}  {:20s}  {:,} lines".format(
                    r["name"], r.get("module", ""), r.get("lines", 0)))
            elif r["type"] == "method":
                print("    [method] {:30s}  in {:20s}  ({})".format(
                    r["name"], r.get("class", ""), r.get("module", "")))
    else:
        print("    (no results)")
    print("")

    # --- BOG Navigator results ---
    if bog_data:
        print("  BOG NAVIGATOR  ({} results)".format(len(bog_results)))
        print("  " + "-" * 60)
        if bog_results:
            for r in bog_results:
                if r["type"] == "component":
                    print("    [type]     {:30s}  {:,} instances".format(
                        r["name"], r.get("count", 0)))
                elif r["type"] == "instance":
                    val = r.get("value", "")
                    val_str = " = {}".format(val) if val else ""
                    print("    [instance] {}{}".format(
                        r.get("path", ""), val_str))
        else:
            print("    (no results)")
        print("")

    # --- Cross-navigator insights ---
    _print_cross_insights(query, help_results, module_results, bog_results)

    # --- Next steps ---
    print("  NEXT STEPS:")
    if any(r["type"] == "class" for r in help_results + module_results):
        cls_name = next(
            (r["name"] for r in module_results if r["type"] == "class"),
            next((r["name"] for r in help_results if r["type"] == "class"), None))
        if cls_name:
            print("    compare {}             Side-by-side comparison".format(cls_name))
            print("    full-profile {}        Combined profile".format(cls_name))
            print("    class {}               Module Nav details".format(cls_name))
    print("")


def _print_cross_insights(query, help_results, module_results, bog_results):
    """Print cross-navigator insights — things visible in one nav but not others."""
    help_classes = set(r["name"] for r in help_results if r["type"] == "class")
    mod_classes = set(r["name"] for r in module_results if r["type"] == "class")
    bog_types = set()
    for r in bog_results:
        if r["type"] == "component":
            t = r["name"]
            if ":" in t:
                type_name = t.split(":", 1)[1]
                bog_types.add("B" + type_name)
                bog_types.add(type_name)

    if not help_classes and not mod_classes and not bog_types:
        return

    print("  CROSS-NAVIGATOR INSIGHTS:")
    print("  " + "-" * 60)

    # Classes in Module but not in Help (private/internal)
    mod_only = mod_classes - help_classes
    if mod_only:
        print("    Internal (Module only, no public docs):")
        for c in sorted(mod_only)[:5]:
            print("      {}".format(c))

    # Classes in Help but not in Module (external/JDK?)
    help_only = help_classes - mod_classes
    if help_only:
        print("    Documented but not decompiled:")
        for c in sorted(help_only)[:5]:
            print("      {}".format(c))

    # BOG types that match known classes
    bog_in_code = bog_types & mod_classes
    if bog_in_code:
        print("    Active in station (BOG + Module Nav):")
        for c in sorted(bog_in_code)[:5]:
            print("      {}".format(c))

    # BOG types with no code match
    bog_no_code = bog_types - mod_classes - help_classes
    if bog_no_code:
        candidates = [c for c in bog_no_code if not c.startswith("B")]
        if candidates:
            print("    BOG types unresolved in code:")
            for c in sorted(candidates)[:3]:
                print("      {}".format(c))

    print("")


# ---------------------------------------------------------------------------
# compare command
# ---------------------------------------------------------------------------

def cmd_compare(base_dir, class_name, help_dir=None, bog_index_path=None):
    """Compare: public docs vs decompiled implementation vs station usage."""
    if not class_name or not class_name.strip():
        print("  Usage: compare <class>")
        return

    class_name = class_name.strip()

    if not help_dir:
        help_dir = _detect_help_dir(base_dir)

    print("")
    print("  " + "=" * 70)
    print("  COMPARE: {}".format(class_name))
    print("  " + "=" * 70)
    print("  Docs (Help Nav) vs Implementation (Module Nav) vs Station (BOG)")
    print("")

    # ---------- COLUMN 1: Help Navigator (Public API) ----------
    help_found = False
    help_entry = None
    help_methods = set()
    help_slots = {"properties": [], "actions": [], "topics": []}
    bajadoc_desc = ""

    if help_dir:
        ci = _load_help_index(help_dir, "class-index.json")
        if ci:
            help_entry = ci.get(class_name)
            if not help_entry:
                for k, v in ci.items():
                    if k.lower() == class_name.lower():
                        class_name = k
                        help_entry = v
                        break

        if help_entry:
            help_found = True

            # Read bajadoc
            pkg = help_entry.get("package", "")
            pkg_path = pkg.replace(".", os.sep)
            txt_path = os.path.join(help_dir, "bajadoc-clean", pkg_path, class_name + ".txt")
            if os.path.isfile(txt_path):
                try:
                    with open(txt_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    # Extract description
                    in_desc = False
                    desc_lines = []
                    for line in text.splitlines():
                        stripped = line.strip()
                        if stripped == "DESCRIPTION:":
                            in_desc = True
                            continue
                        elif in_desc and stripped.endswith(":") and stripped[:-1].replace(" ", "").isupper():
                            break
                        elif in_desc:
                            desc_lines.append(line)
                    bajadoc_desc = "\n".join(desc_lines).strip()

                    # Extract method names from METHODS section
                    in_methods = False
                    for line in text.splitlines():
                        stripped = line.strip()
                        if stripped == "METHODS:":
                            in_methods = True
                            continue
                        elif in_methods and stripped.endswith(":") and stripped[:-1].replace(" ", "").isupper():
                            break
                        elif in_methods and stripped:
                            # Extract method name from signature
                            m = re.match(r'(?:public\s+)?(?:\w+(?:\[\])?\s+)?(\w+)\s*\(', stripped)
                            if m:
                                help_methods.add(m.group(1))
                except Exception:
                    pass

            # Slots from Help
            sl = _load_help_index(help_dir, "slots-index.json")
            if sl and class_name in sl:
                sdata = sl[class_name]
                help_slots["properties"] = sdata.get("properties", [])
                help_slots["actions"] = sdata.get("actions", [])
                help_slots["topics"] = sdata.get("topics", [])

    # ---------- COLUMN 2: Module Navigator (Decompiled) ----------
    mod_found = False
    mod_entry = None
    mod_methods = set()
    mod_all_methods = []
    mod_private_methods = set()

    ci_data = _load_class_index(base_dir)
    if ci_data:
        classes = ci_data.get("classes", {})
        entries = classes.get(class_name)
        if not entries:
            for k, v in classes.items():
                if k.lower() == class_name.lower():
                    class_name = k
                    entries = v
                    break
        if entries:
            for e in entries:
                if e.get("outer_class") is None:
                    mod_entry = e
                    mod_found = True
                    break
            if not mod_entry and entries:
                mod_entry = entries[0]
                mod_found = True

    if mod_found:
        mi_data = _load_method_index(base_dir)
        if mi_data:
            methods_map = mi_data.get("methods", {})
            for mname, entries in methods_map.items():
                for e in entries:
                    if e.get("class") == class_name:
                        mod_methods.add(mname)
                        mod_all_methods.append(e)
                        if "private" in e.get("modifiers", []):
                            mod_private_methods.add(mname)
                        break

    # ---------- COLUMN 3: BOG Navigator (Station) ----------
    bog_found = False
    bog_instances = []
    bog_type_spec = ""

    bog, bog_path = _load_bog(base_dir, bog_index_path)
    if bog:
        components = bog.get("components", [])
        # Find BOG components that match this class
        # Strip B prefix for type matching
        type_suffix = class_name[1:] if class_name.startswith("B") else class_name
        for comp in components:
            ctype = comp.get("type") or ""
            if not ctype:
                continue
            if ":" in ctype:
                t_name = ctype.split(":", 1)[1]
                if t_name == type_suffix or t_name == class_name:
                    bog_found = True
                    bog_type_spec = ctype
                    bog_instances.append(comp)

    # ========== PRINT COMPARISON ==========

    # --- Section 1: Identity ---
    print("  1. IDENTITY")
    print("  " + "-" * 60)
    labels = ["Help Nav", "Module Nav", "BOG Nav"]
    found = [
        "YES" if help_found else "no",
        "YES" if mod_found else "no",
        "YES ({} instances)".format(len(bog_instances)) if bog_found else "no",
    ]
    for label, f in zip(labels, found):
        print("    {:<15s} {}".format(label + ":", f))

    if mod_entry:
        print("")
        print("    Package:     {}".format(mod_entry.get("package", "")))
        print("    Module:      {}".format(mod_entry.get("module", "")))
        print("    Kind:        {}".format(mod_entry.get("kind", "")))
        if mod_entry.get("extends"):
            print("    Extends:     {}".format(mod_entry["extends"]))
    elif help_entry:
        print("")
        print("    Package:     {}".format(help_entry.get("package", "")))
        print("    Type:        {}".format(help_entry.get("type", "")))

    if bog_found:
        print("    BOG type:    {}".format(bog_type_spec))

    # --- Section 2: Documentation ---
    print("")
    print("  2. DOCUMENTATION (Help Nav)")
    print("  " + "-" * 60)
    if bajadoc_desc:
        desc_lines = bajadoc_desc.splitlines()
        for line in desc_lines[:6]:
            print("    {}".format(line.rstrip()))
        if len(desc_lines) > 6:
            print("    ... ({} more lines)".format(len(desc_lines) - 6))
    elif help_found:
        print("    (class is documented but no description found)")
    elif help_dir:
        print("    (not in public API — internal/private class)")
    else:
        print("    (Help Navigator not available)")

    # --- Section 3: Methods comparison ---
    print("")
    print("  3. METHODS COMPARISON")
    print("  " + "-" * 60)

    if help_methods or mod_methods:
        public_doc = help_methods
        all_impl = mod_methods
        private_impl = mod_private_methods

        # Methods in both (documented + implemented)
        both = public_doc & all_impl
        # Methods only in docs (removed/renamed in impl?)
        doc_only = public_doc - all_impl
        # Methods only in impl (private/undocumented)
        impl_only = all_impl - public_doc

        print("    Documented (Help):  {:>4d} methods".format(len(public_doc)))
        print("    Implemented (Mod):  {:>4d} methods".format(len(all_impl)))
        print("    Private (Mod):      {:>4d} methods".format(len(private_impl)))
        print("")
        print("    Overlap:            {:>4d} (in both Help + Module)".format(len(both)))
        print("    Doc-only:           {:>4d} (in Help, not found in Module)".format(len(doc_only)))
        print("    Undocumented:       {:>4d} (in Module, not in Help)".format(len(impl_only)))

        if doc_only:
            print("")
            print("    Doc-only methods (potential inherited/renamed):")
            for m in sorted(doc_only)[:10]:
                print("      {}".format(m))

        if impl_only and len(impl_only) <= 20:
            print("")
            print("    Undocumented methods (internal API):")
            for m in sorted(impl_only)[:10]:
                priv_mark = " [private]" if m in private_impl else ""
                print("      {}{}".format(m, priv_mark))
            if len(impl_only) > 10:
                print("      ... ({} more)".format(len(impl_only) - 10))
    elif mod_methods:
        print("    Module Nav: {} methods (no Help Nav data to compare)".format(len(mod_methods)))
    elif help_methods:
        print("    Help Nav: {} documented methods (no Module Nav data)".format(len(help_methods)))
    else:
        print("    (no method data available)")

    # --- Section 4: Slots/Properties comparison ---
    print("")
    print("  4. SLOTS & PROPERTIES")
    print("  " + "-" * 60)

    help_prop_names = set(p["name"] for p in help_slots["properties"])
    help_action_names = set(a["name"] for a in help_slots["actions"])
    help_topic_names = set(t["name"] for t in help_slots["topics"])

    # Module Nav slots from annotations
    mod_slots = {"properties": [], "actions": [], "topics": []}
    ann_path = os.path.join(base_dir, "indexes", "annotations-index.json")
    ann_data = _load_json(ann_path)
    if ann_data:
        types_data = ann_data.get("types", {})
        ann_entry = types_data.get(class_name)
        if not ann_entry:
            for k, v in types_data.items():
                if k.lower() == class_name.lower():
                    ann_entry = v
                    break
        if ann_entry:
            mod_slots["properties"] = ann_entry.get("properties", [])
            mod_slots["actions"] = ann_entry.get("actions", [])
            mod_slots["topics"] = ann_entry.get("topics", [])

    mod_prop_names = set(p["name"] for p in mod_slots["properties"])
    mod_action_names = set(a["name"] for a in mod_slots["actions"])
    mod_topic_names = set(t["name"] for t in mod_slots["topics"])

    h_total = len(help_prop_names) + len(help_action_names) + len(help_topic_names)
    m_total = len(mod_prop_names) + len(mod_action_names) + len(mod_topic_names)

    print("    {:20s} {:>8s}  {:>8s}".format("", "Help Nav", "Module Nav"))
    print("    {:20s} {:>8d}  {:>8d}".format("Properties:", len(help_prop_names), len(mod_prop_names)))
    print("    {:20s} {:>8d}  {:>8d}".format("Actions:", len(help_action_names), len(mod_action_names)))
    print("    {:20s} {:>8d}  {:>8d}".format("Topics:", len(help_topic_names), len(mod_topic_names)))
    print("    {:20s} {:>8d}  {:>8d}".format("TOTAL:", h_total, m_total))

    # Property diff
    props_only_help = help_prop_names - mod_prop_names
    props_only_mod = mod_prop_names - help_prop_names
    if props_only_help:
        print("")
        print("    Properties in Help only: {}".format(", ".join(sorted(props_only_help)[:5])))
    if props_only_mod:
        print("    Properties in Module only: {}".format(", ".join(sorted(props_only_mod)[:5])))

    # --- Section 5: Station Usage (BOG) ---
    print("")
    print("  5. STATION USAGE (BOG Nav)")
    print("  " + "-" * 60)

    if bog_found:
        print("    Type:      {}".format(bog_type_spec))
        print("    Instances: {}".format(len(bog_instances)))
        print("")
        print("    Sample instances:")
        for inst in bog_instances[:8]:
            val = inst.get("value", "")
            val_str = " = {}".format(val) if val else ""
            print("      {}{}".format(inst.get("path", ""), val_str))
        if len(bog_instances) > 8:
            print("      ... ({} more)".format(len(bog_instances) - 8))
    elif bog:
        print("    Class '{}' has no instances in the current station config.".format(class_name))
        print("    (This class may be used programmatically, not as a component.)")
    else:
        print("    (BOG Navigator not available)")

    # --- Section 6: Visibility Summary ---
    print("")
    print("  6. VISIBILITY SUMMARY")
    print("  " + "-" * 60)

    visibility = []
    if help_found:
        visibility.append("PUBLIC API (documented in bajadoc)")
    if mod_found and not help_found:
        visibility.append("INTERNAL (decompiled, no public docs)")
    if mod_found and help_found:
        visibility.append("IMPLEMENTED (source available)")
    if bog_found:
        visibility.append("ACTIVE IN STATION ({} instances)".format(len(bog_instances)))
    elif bog and mod_found:
        visibility.append("NOT INSTANTIATED in current station")

    if not visibility:
        visibility.append("NOT FOUND in any navigator")

    for v in visibility:
        print("    - {}".format(v))

    # API surface category
    if help_found and mod_found and bog_found:
        print("")
        print("    Category: FULL STACK — documented, implemented, and deployed")
    elif help_found and mod_found:
        print("")
        print("    Category: LIBRARY — documented and implemented, not deployed as component")
    elif mod_found and bog_found:
        print("")
        print("    Category: UNDOCUMENTED ACTIVE — deployed but no public docs")
    elif mod_found:
        print("")
        print("    Category: INTERNAL — code-only, no docs, no station usage")

    print("")
