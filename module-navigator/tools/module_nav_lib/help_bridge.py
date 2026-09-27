"""
Help Navigator Bridge for Module Navigator (Phase 9).

Integrates Help Navigator data (bajadoc, public API, devguide) with
Module Navigator data (decompiled code, private classes, UI internals).

Commands:
  full-profile <class>   Combined view from BOTH navigators
  cross-ref <class>      Docs + implementation + who uses it

Help Navigator location is auto-detected or set via --help-dir.
Indexes are loaded on-demand (NOT preloaded with Module Nav indexes).
"""

import json
import os
import re


# ---------------------------------------------------------------------------
# Help Navigator auto-detection
# ---------------------------------------------------------------------------

def detect_help_dir(module_nav_base):
    """Auto-detect Help Navigator directory relative to Module Navigator."""
    # module-navigator/ and niagara-help/ are siblings under the same parent
    parent = os.path.dirname(module_nav_base)
    candidate = os.path.join(parent, "niagara-help")
    if os.path.isdir(candidate) and os.path.isdir(os.path.join(candidate, "indexes")):
        return candidate
    return None


# ---------------------------------------------------------------------------
# Help Navigator index loading (on-demand, cached per call)
# ---------------------------------------------------------------------------

_help_cache = {}


def _load_help_index(help_dir, filename):
    """Load a Help Navigator JSON index. Cached in-process."""
    cache_key = filename
    if cache_key in _help_cache:
        return _help_cache[cache_key]

    path = os.path.join(help_dir, "indexes", filename)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _help_cache[cache_key] = data
        return data
    except Exception:
        return None


def _read_bajadoc_clean(help_dir, package, class_name):
    """Read the bajadoc-clean text for a class."""
    pkg_path = package.replace(".", os.sep)
    txt_path = os.path.join(help_dir, "bajadoc-clean", pkg_path, class_name + ".txt")
    if os.path.isfile(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    return None


def _parse_bajadoc_sections(text):
    """Parse bajadoc-clean text into sections dict."""
    sections = {}
    current_section = None
    current_lines = []

    for line in text.splitlines():
        stripped = line.strip()
        # Section headers are ALL CAPS followed by colon
        if stripped.endswith(":") and stripped[:-1].replace(" ", "").isupper() and len(stripped) > 2:
            if current_section is not None:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = stripped[:-1].strip()
            current_lines = []
        # Also handle header-like lines at start (CLASS:, PACKAGE:, etc.)
        elif ":" in stripped and not stripped.startswith(" ") and current_section is None:
            key, _, val = stripped.partition(":")
            key = key.strip()
            if key in ("CLASS", "INTERFACE", "PACKAGE", "SINCE", "EXTENDS",
                        "IMPLEMENTS", "SUBCLASSES", "DEPRECATED"):
                sections[key] = val.strip()
            else:
                if current_section is not None:
                    current_lines.append(line)
        else:
            if current_section is not None:
                current_lines.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(current_lines).strip()

    return sections


def _find_class_in_help(help_dir, class_name):
    """Find a class in Help Navigator indexes. Returns (name, class_entry, source_entry, slots_entry) or Nones."""
    ci = _load_help_index(help_dir, "class-index.json")
    if not ci:
        return None, None, None, None

    # Exact match
    entry = ci.get(class_name)
    if not entry:
        # Case-insensitive fallback
        name_lower = class_name.lower()
        for k, v in ci.items():
            if k.lower() == name_lower:
                class_name = k
                entry = v
                break

    if not entry:
        return None, None, None, None

    # Source info
    si = _load_help_index(help_dir, "source-index.json")
    source_entry = si.get(class_name) if si else None

    # Slots info
    sl = _load_help_index(help_dir, "slots-index.json")
    slots_entry = sl.get(class_name) if sl else None

    return class_name, entry, source_entry, slots_entry


def _find_class_in_module_nav(base_dir, class_name):
    """Find a class in Module Navigator class-index. Returns (name, entry) or Nones."""
    ci_path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(ci_path):
        return None, None

    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = json.load(f)

    classes = ci_data.get("classes", {})

    if class_name in classes:
        entries = classes[class_name]
        for e in entries:
            if e["outer_class"] is None:
                return class_name, e
        return class_name, entries[0]

    name_lower = class_name.lower()
    for k, entries in classes.items():
        if k.lower() == name_lower:
            for e in entries:
                if e["outer_class"] is None:
                    return k, e
            return k, entries[0]

    return None, None


# Cache reference to avoid reloading 32MB class-index
_mn_class_index_cache = None


def _find_class_in_module_nav_cached(base_dir, class_name):
    """Find class using cached Module Nav class-index (for REPL)."""
    global _mn_class_index_cache

    if _mn_class_index_cache is not None:
        classes = _mn_class_index_cache.get("classes", {})
    else:
        ci_path = os.path.join(base_dir, "indexes", "class-index.json")
        if not os.path.isfile(ci_path):
            return None, None
        with open(ci_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _mn_class_index_cache = data
        classes = data.get("classes", {})

    if class_name in classes:
        entries = classes[class_name]
        for e in entries:
            if e["outer_class"] is None:
                return class_name, e
        return class_name, entries[0]

    name_lower = class_name.lower()
    for k, entries in classes.items():
        if k.lower() == name_lower:
            for e in entries:
                if e["outer_class"] is None:
                    return k, e
            return k, entries[0]

    return None, None


# ---------------------------------------------------------------------------
# full-profile command
# ---------------------------------------------------------------------------

def cmd_full_profile(base_dir, class_name, help_dir=None):
    """Combined profile from BOTH navigators."""
    # Auto-detect help dir
    if not help_dir:
        help_dir = detect_help_dir(base_dir)

    # Find class in both navigators
    mn_name, mn_entry = _find_class_in_module_nav_cached(base_dir, class_name)

    help_name = None
    help_entry = None
    help_source = None
    help_slots = None
    bajadoc_text = None
    bajadoc_sections = {}

    if help_dir:
        help_name, help_entry, help_source, help_slots = _find_class_in_help(help_dir, class_name)
        if help_name and help_entry:
            bajadoc_text = _read_bajadoc_clean(help_dir, help_entry["package"], help_name)
            if bajadoc_text:
                bajadoc_sections = _parse_bajadoc_sections(bajadoc_text)

    if not mn_name and not help_name:
        print("  Class '{}' not found in either navigator.".format(class_name))
        return

    resolved = mn_name or help_name

    # Header
    print("")
    print("  " + "=" * 70)
    print("  FULL PROFILE: {}".format(resolved))
    print("  " + "=" * 70)

    # Sources available
    sources = []
    if mn_name:
        sources.append("Module Nav (decompiled)")
    if help_name:
        sources.append("Help Nav (public API)")
    print("  Sources: {}".format(" + ".join(sources)))
    print("")

    # --- Section 1: CLASS INFO (Module Nav preferred, Help Nav fallback) ---
    print("  CLASS INFO:")
    if mn_entry:
        print("    Name:        {}".format(mn_name))
        print("    Package:     {}".format(mn_entry["package"]))
        print("    Module:      {}".format(mn_entry["module"]))
        print("    Kind:        {}".format(mn_entry["kind"]))
        print("    Modifiers:   {}".format(" ".join(mn_entry["modifiers"]) if mn_entry["modifiers"] else "-"))
        if mn_entry["extends"]:
            print("    Extends:     {}".format(mn_entry["extends"]))
        if mn_entry["implements"]:
            print("    Implements:  {}".format(", ".join(mn_entry["implements"])))
        print("    Lines:       {:,}".format(mn_entry["lines"]))
        if mn_entry["zkm"]:
            print("    ZKM:         YES (obfuscated)")
    elif help_entry:
        print("    Name:        {}".format(help_name))
        print("    Package:     {}".format(help_entry["package"]))
        print("    Type:        {}".format(help_entry["type"]))
        if help_source:
            print("    Module:      {}".format(help_source["module"]))
            print("    Lines:       {:,}".format(help_source["lines"]))

    # Since version (from bajadoc)
    if bajadoc_sections.get("SINCE"):
        print("    Since:       {}".format(bajadoc_sections["SINCE"]))

    # Deprecated?
    if bajadoc_sections.get("DEPRECATED"):
        print("    DEPRECATED:  {}".format(bajadoc_sections["DEPRECATED"]))

    # --- Section 2: DOCUMENTATION (Help Nav only) ---
    if bajadoc_sections.get("DESCRIPTION"):
        print("")
        print("  DOCUMENTATION:  [Help Nav - bajadoc]")
        desc = bajadoc_sections["DESCRIPTION"]
        # Truncate to ~8 lines for readability
        desc_lines = desc.strip().splitlines()
        for line in desc_lines[:8]:
            print("    {}".format(line.rstrip()))
        if len(desc_lines) > 8:
            print("    ... ({} more lines)".format(len(desc_lines) - 8))
    elif not help_dir:
        print("")
        print("  DOCUMENTATION:  (Help Navigator not available)")
    elif not help_name:
        print("")
        print("  DOCUMENTATION:  (class not in public API - private/internal)")

    # --- Section 3: NIAGARA SLOTS (Help Nav preferred, Module Nav fallback) ---
    _print_slots_section(help_slots, base_dir, resolved)

    # --- Section 4: PUBLIC API METHODS (Help Nav) ---
    if bajadoc_sections.get("METHODS"):
        print("")
        print("  PUBLIC API METHODS:  [Help Nav - bajadoc]")
        method_lines = bajadoc_sections["METHODS"].strip().splitlines()
        shown = 0
        for line in method_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("Methods inherited"):
                print("    {}".format(stripped))
                shown += 1
                if shown >= 20:
                    remaining = len([l for l in method_lines[method_lines.index(line)+1:]
                                    if l.strip() and not l.strip().startswith("Methods inherited")])
                    if remaining > 0:
                        print("    ... ({} more methods)".format(remaining))
                    break

    # --- Section 5: INTERNAL METHODS (Module Nav) ---
    if mn_entry:
        _print_internal_methods(base_dir, resolved, mn_entry)

    # --- Section 6: HIERARCHY (Module Nav) ---
    if mn_entry:
        _print_hierarchy_section(base_dir, resolved)

    # --- Section 7: CROSS-REFERENCES (Module Nav) ---
    if mn_entry:
        _print_xref_section(base_dir, resolved)

    # --- Section 8: UI DETAILS (Module Nav) ---
    if mn_entry:
        _print_ui_section(base_dir, resolved)

    # --- Section 9: MODULE CONTEXT ---
    if mn_entry:
        _print_module_context(base_dir, mn_entry)

    print("")


def _print_slots_section(help_slots, base_dir, class_name):
    """Print slots from Help Nav or Module Nav annotations."""
    # Try Help Nav first (has cleaner data)
    if help_slots:
        props = help_slots.get("properties", [])
        actions = help_slots.get("actions", [])
        topics = help_slots.get("topics", [])
        total = len(props) + len(actions) + len(topics)
        if total > 0:
            print("")
            print("  NIAGARA SLOTS:  [Help Nav]  ({} properties, {} actions, {} topics)".format(
                len(props), len(actions), len(topics)))
            if props:
                for p in props[:10]:
                    flags_str = "  [{}]".format(p["flags"]) if p.get("flags") else ""
                    print("    P  {:30s} : {}{}".format(p["name"], p["type"], flags_str))
                if len(props) > 10:
                    print("    ... ({} more properties)".format(len(props) - 10))
            if actions:
                for a in actions[:10]:
                    param = a.get("parameterType", "")
                    print("    A  {:30s}   param: {}".format(a["name"], param or "-"))
                if len(actions) > 10:
                    print("    ... ({} more actions)".format(len(actions) - 10))
            if topics:
                for t in topics:
                    print("    T  {:30s}   event: {}".format(t["name"], t.get("eventType", "-")))
            return

    # Fallback to Module Nav annotations
    ann_path = os.path.join(base_dir, "indexes", "annotations-index.json")
    if not os.path.isfile(ann_path):
        return

    try:
        with open(ann_path, "r", encoding="utf-8") as f:
            ann_data = json.load(f)
    except Exception:
        return

    types_data = ann_data.get("types", {})
    ann_entry = types_data.get(class_name)
    if not ann_entry:
        # Case-insensitive
        for k, v in types_data.items():
            if k.lower() == class_name.lower():
                ann_entry = v
                break

    if ann_entry:
        props = ann_entry.get("properties", [])
        actions = ann_entry.get("actions", [])
        topics = ann_entry.get("topics", [])
        total = len(props) + len(actions) + len(topics)
        if total > 0:
            print("")
            print("  NIAGARA SLOTS:  [Module Nav]  ({} properties, {} actions, {} topics)".format(
                len(props), len(actions), len(topics)))
            if props:
                for p in props[:10]:
                    print("    P  {:30s} : {}".format(p["name"], p["type"]))
                if len(props) > 10:
                    print("    ... ({} more properties)".format(len(props) - 10))
            if actions:
                for a in actions[:10]:
                    print("    A  {}".format(a["name"]))
                if len(actions) > 10:
                    print("    ... ({} more actions)".format(len(actions) - 10))
            if topics:
                for t in topics:
                    print("    T  {}".format(t["name"]))


def _print_internal_methods(base_dir, class_name, mn_entry):
    """Print internal methods from Module Nav method-index."""
    mi_path = os.path.join(base_dir, "indexes", "method-index.json")
    if not os.path.isfile(mi_path):
        return

    try:
        with open(mi_path, "r", encoding="utf-8") as f:
            mi_data = json.load(f)
    except Exception:
        return

    methods_map = mi_data.get("methods", {})
    class_methods = []
    seen_sigs = set()
    for mname, entries in methods_map.items():
        for e in entries:
            if e.get("class") == class_name:
                sig = e.get("signature", "")
                if sig not in seen_sigs:
                    seen_sigs.add(sig)
                    class_methods.append(e)

    if class_methods:
        # Separate by visibility
        private_methods = [m for m in class_methods if "private" in m.get("modifiers", [])]
        protected_methods = [m for m in class_methods if "protected" in m.get("modifiers", [])]
        total = len(class_methods)

        print("")
        print("  INTERNAL METHODS:  [Module Nav]  ({} total, {} private, {} protected)".format(
            total, len(private_methods), len(protected_methods)))

        # Show private ones first (they're the ones Help Nav DOESN'T have)
        if private_methods:
            print("    Private:")
            for m in private_methods[:10]:
                sig = m.get("signature", "?")
                print("      {}".format(sig))
            if len(private_methods) > 10:
                print("      ... ({} more)".format(len(private_methods) - 10))

        if protected_methods:
            print("    Protected:")
            for m in protected_methods[:10]:
                sig = m.get("signature", "?")
                print("      {}".format(sig))
            if len(protected_methods) > 10:
                print("      ... ({} more)".format(len(protected_methods) - 10))


def _print_hierarchy_section(base_dir, class_name):
    """Print inheritance info from Module Nav."""
    ih_path = os.path.join(base_dir, "indexes", "inheritance.json")
    if not os.path.isfile(ih_path):
        return

    try:
        with open(ih_path, "r", encoding="utf-8") as f:
            ih_data = json.load(f)
    except Exception:
        return

    chains = ih_data.get("class_to_chain", {})
    children_map = ih_data.get("parent_to_children", {})

    chain = chains.get(class_name, [])
    children = children_map.get(class_name, [])

    if chain or children:
        print("")
        print("  HIERARCHY:  [Module Nav]")
        if chain:
            print("    Chain:    {} -> {}".format(class_name, " -> ".join(chain)))
        if children:
            print("    Children: {} direct subclasses".format(len(children)))
            for c in children[:10]:
                print("      {}".format(c))
            if len(children) > 10:
                print("      ... ({} more)".format(len(children) - 10))


def _print_xref_section(base_dir, class_name):
    """Print cross-references from Module Nav."""
    xr_path = os.path.join(base_dir, "indexes", "xref-index.json")
    if not os.path.isfile(xr_path):
        return

    try:
        with open(xr_path, "r", encoding="utf-8") as f:
            xr_data = json.load(f)
    except Exception:
        return

    class_imports = xr_data.get("class_imports", {})
    class_imported_by = xr_data.get("class_imported_by", {})

    imports = class_imports.get(class_name, [])
    importers = class_imported_by.get(class_name, [])

    if imports or importers:
        print("")
        print("  CROSS-REFERENCES:  [Module Nav]")
        print("    Imports:   {} classes".format(len(imports)))
        if imports:
            for imp in imports[:10]:
                print("      {}".format(imp))
            if len(imports) > 10:
                print("      ... ({} more)".format(len(imports) - 10))
        print("    Importers: {} classes".format(len(importers)))
        if importers:
            for imp in importers[:10]:
                print("      {}".format(imp))
            if len(importers) > 10:
                print("      ... ({} more)".format(len(importers) - 10))


def _print_ui_section(base_dir, class_name):
    """Print UI details from Module Nav swing-index."""
    si_path = os.path.join(base_dir, "indexes", "swing-index.json")
    if not os.path.isfile(si_path):
        return

    try:
        with open(si_path, "r", encoding="utf-8") as f:
            si_data = json.load(f)
    except Exception:
        return

    si_classes = si_data.get("classes", {})
    ui_rec = None
    if class_name in si_classes:
        val = si_classes[class_name]
        ui_rec = val[0] if isinstance(val, list) else val
    else:
        for k, val in si_classes.items():
            if k.lower() == class_name.lower():
                ui_rec = val[0] if isinstance(val, list) else val
                break

    if ui_rec:
        print("")
        print("  UI DETAILS:  [Module Nav]")
        print("    Category:    {}".format(ui_rec.get("category", "-")))
        if ui_rec.get("dimensions"):
            print("    Dimensions:")
            for dim in ui_rec["dimensions"][:5]:
                if dim.get("method") == "setBounds":
                    print("      Line {:>5}: {}({}, {}, {}, {})".format(
                        dim["line"], dim["method"], dim["x"], dim["y"], dim["w"], dim["h"]))
                else:
                    print("      Line {:>5}: {}({}, {})".format(
                        dim["line"], dim["method"], dim.get("w", "?"), dim.get("h", "?")))


def _print_module_context(base_dir, mn_entry):
    """Print module context from Module Nav inventory."""
    inv_path = os.path.join(base_dir, "indexes", "module-inventory.json")
    if not os.path.isfile(inv_path):
        return

    try:
        with open(inv_path, "r", encoding="utf-8") as f:
            inv_data = json.load(f)
    except Exception:
        return

    inv = inv_data.get("modules", {})
    mod_key = mn_entry["module"]
    if mod_key in inv:
        mod = inv[mod_key]
        print("")
        print("  MODULE CONTEXT:  [Module Nav]")
        print("    Module:      {} ({})".format(mod_key, mod.get("type") or "standalone"))
        print("    JAR:         {}".format(mod.get("jar", "-")))
        print("    Java files:  {:,}".format(mod.get("java_files", 0)))
        print("    Class count: {:,}".format(mod.get("class_count", 0)))
        if mod.get("zkm"):
            print("    ZKM:         YES (obfuscated)")


# ---------------------------------------------------------------------------
# cross-ref command
# ---------------------------------------------------------------------------

def cmd_cross_ref(base_dir, class_name, help_dir=None):
    """Show class in context: docs + implementation + who uses it."""
    if not help_dir:
        help_dir = detect_help_dir(base_dir)

    # Find in both
    mn_name, mn_entry = _find_class_in_module_nav_cached(base_dir, class_name)

    help_name = None
    help_entry = None
    help_source = None
    help_slots = None
    bajadoc_text = None
    bajadoc_sections = {}

    if help_dir:
        help_name, help_entry, help_source, help_slots = _find_class_in_help(help_dir, class_name)
        if help_name and help_entry:
            bajadoc_text = _read_bajadoc_clean(help_dir, help_entry["package"], help_name)
            if bajadoc_text:
                bajadoc_sections = _parse_bajadoc_sections(bajadoc_text)

    if not mn_name and not help_name:
        print("  Class '{}' not found in either navigator.".format(class_name))
        return

    resolved = mn_name or help_name

    # Header
    print("")
    print("  " + "=" * 70)
    print("  CROSS-REFERENCE: {}".format(resolved))
    print("  " + "=" * 70)
    print("")

    # --- Section 1: IDENTITY ---
    print("  IDENTITY:")
    if mn_entry:
        print("    Package:     {}".format(mn_entry["package"]))
        print("    Module:      {}".format(mn_entry["module"]))
        print("    Kind:        {}".format(mn_entry["kind"]))
        if mn_entry["extends"]:
            print("    Extends:     {}".format(mn_entry["extends"]))
    elif help_entry:
        print("    Package:     {}".format(help_entry["package"]))
        print("    Type:        {}".format(help_entry["type"]))
        if help_source:
            print("    Module:      {}".format(help_source["module"]))

    in_help = "YES" if help_name else "no"
    in_mod = "YES" if mn_name else "no"
    print("    Help Nav:    {}".format(in_help))
    print("    Module Nav:  {}".format(in_mod))

    # --- Section 2: WHAT DOES IT DO? (bajadoc description) ---
    if bajadoc_sections.get("DESCRIPTION"):
        print("")
        print("  WHAT DOES IT DO?  [Help Nav - bajadoc]")
        desc_lines = bajadoc_sections["DESCRIPTION"].strip().splitlines()
        for line in desc_lines[:6]:
            print("    {}".format(line.rstrip()))
        if len(desc_lines) > 6:
            print("    ... ({} more lines)".format(len(desc_lines) - 6))
    elif not help_name and mn_entry:
        print("")
        print("  WHAT DOES IT DO?  (no public docs — private/internal class)")

    # --- Section 3: PUBLIC CONTRACT (Help Nav methods) ---
    if bajadoc_sections.get("METHODS"):
        print("")
        print("  PUBLIC CONTRACT:  [Help Nav]")
        method_lines = bajadoc_sections["METHODS"].strip().splitlines()
        shown = 0
        for line in method_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("Methods inherited"):
                print("    {}".format(stripped))
                shown += 1
                if shown >= 15:
                    remaining = sum(1 for l in method_lines
                                   if l.strip() and not l.strip().startswith("Methods inherited"))
                    if remaining > shown:
                        print("    ... ({} more)".format(remaining - shown))
                    break

    # --- Section 4: INTERNAL IMPLEMENTATION (Module Nav) ---
    if mn_entry:
        source_root = ""
        ci_path = os.path.join(base_dir, "indexes", "class-index.json")
        if _mn_class_index_cache:
            source_root = _mn_class_index_cache.get("_meta", {}).get("source", "")
        elif os.path.isfile(ci_path):
            try:
                with open(ci_path, "r", encoding="utf-8") as f:
                    ci_data = json.load(f)
                source_root = ci_data.get("_meta", {}).get("source", "")
            except Exception:
                pass

        print("")
        print("  IMPLEMENTATION:  [Module Nav]")
        print("    Source:      {}".format(mn_entry["path"]))
        print("    Lines:       {:,}".format(mn_entry["lines"]))

        filepath = os.path.join(source_root, mn_entry["path"]) if source_root else ""
        if filepath and os.path.isfile(filepath):
            # Count methods by visibility
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    src_lines = f.readlines()
            except Exception:
                src_lines = []

            if src_lines:
                pub = 0
                priv = 0
                prot = 0
                for line in src_lines:
                    stripped = line.strip()
                    if re.match(r'public\s+', stripped):
                        pub += 1
                    elif re.match(r'private\s+', stripped):
                        priv += 1
                    elif re.match(r'protected\s+', stripped):
                        prot += 1
                print("    Visibility:  public={}, protected={}, private={}".format(pub, prot, priv))

    # --- Section 5: WHO USES IT (Module Nav xref importers) ---
    if mn_entry:
        _print_xref_importers_only(base_dir, resolved)

    # --- Section 6: RELATED GUIDES (Help Nav) ---
    if help_dir:
        _print_related_guides(help_dir, resolved)

    print("")


def _print_xref_importers_only(base_dir, class_name):
    """Print just the importers for cross-ref."""
    xr_path = os.path.join(base_dir, "indexes", "xref-index.json")
    if not os.path.isfile(xr_path):
        return

    try:
        with open(xr_path, "r", encoding="utf-8") as f:
            xr_data = json.load(f)
    except Exception:
        return

    class_imported_by = xr_data.get("class_imported_by", {})
    importers = class_imported_by.get(class_name, [])

    if importers:
        print("")
        print("  WHO USES IT:  [Module Nav]  ({} importers)".format(len(importers)))
        for imp in importers[:15]:
            print("    {}".format(imp))
        if len(importers) > 15:
            print("    ... ({} more)".format(len(importers) - 15))


def _print_related_guides(help_dir, class_name):
    """Search Help Nav guides for mentions of this class."""
    guides_index = _load_help_index(help_dir, "guides-index.json")
    devguide_toc = _load_help_index(help_dir, "devguide-toc.json")

    related = []

    # Search devguide TOC for class mentions
    if devguide_toc:
        sections = devguide_toc.get("sections", [])
        for section in sections:
            for item in section.get("items", []):
                title = item.get("title", "")
                desc = item.get("description", "")
                if class_name.lower() in title.lower() or class_name.lower() in desc.lower():
                    related.append({
                        "source": "DevGuide",
                        "title": title,
                        "file": item.get("file", ""),
                    })

    # Search guides index for class mentions in topic names
    if guides_index:
        for folder, info in guides_index.items():
            topics = info.get("topics", [])
            for topic in topics:
                if isinstance(topic, str) and class_name.lower() in topic.lower():
                    related.append({
                        "source": "Guide: {}".format(folder),
                        "title": topic,
                    })

    if related:
        print("")
        print("  RELATED GUIDES:  [Help Nav]")
        for r in related[:10]:
            source = r["source"]
            title = r["title"]
            if r.get("file"):
                print("    [{}] {} ({})".format(source, title, r["file"]))
            else:
                print("    [{}] {}".format(source, title))
        if len(related) > 10:
            print("    ... ({} more)".format(len(related) - 10))


# ---------------------------------------------------------------------------
# Stats helper
# ---------------------------------------------------------------------------

def get_help_nav_status(base_dir, help_dir=None):
    """Return Help Navigator status dict for stats display."""
    if not help_dir:
        help_dir = detect_help_dir(base_dir)

    if not help_dir:
        return {"available": False, "path": None}

    ci = _load_help_index(help_dir, "class-index.json")
    si = _load_help_index(help_dir, "source-index.json")
    sl = _load_help_index(help_dir, "slots-index.json")

    return {
        "available": True,
        "path": help_dir,
        "classes": len(ci) if ci else 0,
        "source_files": len(si) if si else 0,
        "classes_with_slots": len(sl) if sl else 0,
        "indexes": len([f for f in os.listdir(os.path.join(help_dir, "indexes"))
                       if f.endswith(".json")]) if os.path.isdir(os.path.join(help_dir, "indexes")) else 0,
    }
