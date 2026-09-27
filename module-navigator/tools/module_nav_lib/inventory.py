"""
Inventory commands for Module Navigator.

Commands:
  inventory            Summary of all indexed modules
  module <name>        Detailed info for a specific submodule
  modules              List modules with optional filters
    --type <type>      Filter by type (rt, wb, ux, doc, se, standalone)
    --zkm              Show only ZKM-obfuscated modules
    --no-code          Show only modules without Java code
    --has-code         Show only modules with Java code
    --bytecode <ver>   Filter by bytecode version (e.g. 52)
    --top <N>          Show top N by java_files count
  stats                Corpus summary (modules, classes, indexes, sizes)
    --json             JSON output
"""

import json
import os


def load_inventory(base_dir):
    """Load module-inventory.json."""
    path = os.path.join(base_dir, "indexes", "module-inventory.json")
    if not os.path.isfile(path):
        print("ERROR: module-inventory.json not found.")
        print("Run: python tools/build_module_inventory.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def cmd_inventory(base_dir):
    """Print inventory summary."""
    data = load_inventory(base_dir)
    if not data:
        return

    inv = data["modules"]
    meta = data.get("_meta", {})

    total = len(inv)
    with_code = sum(1 for v in inv.values() if v["has_code"])
    without_code = total - with_code
    total_java = sum(v["java_files"] for v in inv.values())
    total_classes = sum(v["class_count"] for v in inv.values())
    zkm_count = sum(1 for v in inv.values() if v["zkm"])
    with_vf = sum(1 for v in inv.values() if v["has_vineflower"])

    # Types
    types = {}
    for v in inv.values():
        t = v["type"] if v["type"] else "standalone"
        types[t] = types.get(t, 0) + 1

    # Bytecode
    bytecodes = {}
    for v in inv.values():
        bc = v["bytecode"] or 0
        if bc > 0:
            bytecodes[bc] = bytecodes.get(bc, 0) + 1

    # Unique modules
    modules = set(v["module"] for v in inv.values())

    # Third-party libs
    all_3p = set()
    for v in inv.values():
        all_3p.update(v.get("third_party", []))

    print("=" * 60)
    print("MODULE INVENTORY")
    print("=" * 60)
    print("")
    print("  Total submodules (JARs):   {:>6,}".format(total))
    print("  Unique modules:            {:>6,}".format(len(modules)))
    print("  With Java code:            {:>6,}".format(with_code))
    print("  Without code (docs/res):   {:>6,}".format(without_code))
    print("  With vineflower/:          {:>6,}".format(with_vf))
    print("  ZKM obfuscated:            {:>6,}".format(zkm_count))
    print("  Total .java files:         {:>6,}".format(total_java))
    print("  Total .class files:        {:>6,}".format(total_classes))
    print("  Unique 3rd-party libs:     {:>6,}".format(len(all_3p)))
    print("")
    print("  Type breakdown:")
    for t in sorted(types.keys()):
        print("    {:12s} {:>5,}".format(t, types[t]))
    print("")
    print("  Bytecode versions:")
    for bc in sorted(bytecodes.keys()):
        label = "Java {}".format(bc - 44) if bc >= 45 else str(bc)
        print("    v{} ({:8s}): {:>5,}".format(bc, label, bytecodes[bc]))
    print("")

    if meta:
        print("  Index built: {}".format(meta.get("timestamp", "unknown")))
        print("  Build time:  {:.1f}s".format(meta.get("build_time_sec", 0)))
    print("")

    # Top 10 by java_files
    top10 = sorted(inv.items(), key=lambda x: x[1]["java_files"], reverse=True)[:10]
    print("  Top 10 by .java files:")
    for name, v in top10:
        print("    {:40s} {:>5,} files  {:>5,} classes".format(
            name, v["java_files"], v["class_count"]))
    print("")


def cmd_module(base_dir, name, show_permissions=False, show_deps=False,
               show_sma=False):
    """Show detailed info for a specific submodule.

    If any show_* flag is set, print only that focused view from the module's
    META-INF/module.xml (and, for --sma, cross-ref with installed licenses).
    """
    data = load_inventory(base_dir)
    if not data:
        return

    inv = data["modules"]

    if name in inv:
        resolved = name
    else:
        matches = [k for k in inv if name.lower() in k.lower()]
        if not matches:
            print("Module '{}' not found.".format(name))
            print("Use 'modules' to list all modules.")
            return
        if len(matches) == 1:
            resolved = matches[0]
        else:
            print("Multiple matches for '{}':".format(name))
            for m in sorted(matches)[:20]:
                v = inv[m]
                print("  {:40s} {:>4s}  {:>5,} java  {}".format(
                    m, v["type"] or "-", v["java_files"],
                    "ZKM" if v["zkm"] else ""))
            if len(matches) > 20:
                print("  ... and {} more".format(len(matches) - 20))
            return

    if show_permissions or show_deps or show_sma:
        _print_module_xml_view(
            base_dir, resolved, inv[resolved],
            show_permissions=show_permissions,
            show_deps=show_deps,
            show_sma=show_sma,
        )
        return

    _print_module_detail(resolved, inv[resolved])


def _find_module_xml(base_dir, submodule_name, parent_module):
    """Return the path to the META-INF/module.xml for a submodule, or None."""
    import glob
    from module_nav_lib.grep_search import (
        _load_class_index, _resolve_source_root,
    )
    data = _load_class_index(base_dir)
    if not data:
        return None
    meta_source = data.get("_meta", {}).get("source_root", "")
    root, _tried = _resolve_source_root(meta_source)
    if not root:
        return None
    candidates = [
        os.path.join(root, parent_module or "*", submodule_name,
                     "extracted", "META-INF", "module.xml"),
        os.path.join(root, "*", submodule_name,
                     "extracted", "META-INF", "module.xml"),
    ]
    for pat in candidates:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    return None


def _parse_module_xml(path):
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(path)
        return tree.getroot(), None
    except (ET.ParseError, IOError, OSError) as e:
        return None, str(e)


def _print_module_xml_view(base_dir, name, meta, show_permissions=False,
                           show_deps=False, show_sma=False):
    xml_path = _find_module_xml(base_dir, name, meta.get("module"))
    if not xml_path:
        print("")
        print("  module.xml not found for '{}' (parent='{}')".format(
            name, meta.get("module")))
        print("")
        return
    root, err = _parse_module_xml(xml_path)
    if err:
        print("")
        print("  module.xml parse failed: {}".format(err))
        print("")
        return

    print("")
    print("  Module:      {}".format(name))
    print("  module.xml:  {}".format(xml_path))
    print("")

    if show_deps:
        deps_el = root.find("dependencies")
        if deps_el is None:
            print("  No <dependencies> block in module.xml.")
        else:
            entries = list(deps_el)
            print("  DEPENDENCIES ({})".format(len(entries)))
            print("  {:30s} {:12s} {}".format("NAME", "VENDOR", "VERSION"))
            print("  " + "-" * 64)
            for d in entries:
                print("  {:30s} {:12s} {}".format(
                    d.get("name", "")[:30],
                    d.get("vendor", "")[:12],
                    d.get("vendorVersion", "")))
        print("")

    if show_permissions:
        perms_el = root.find("permissions")
        if perms_el is None:
            print("  No <permissions> block in module.xml.")
        else:
            total = 0
            print("  DECLARED PERMISSIONS")
            for jps in perms_el.findall("java-permissions"):
                ptype = jps.get("type", "")
                entries = list(jps.findall("java-permission"))
                total += len(entries)
                print("    type={}  ({} entries)".format(ptype, len(entries)))
                for jp in entries:
                    print("      {:45s} {:25s} {}".format(
                        jp.get("class", "")[:45],
                        jp.get("name", "")[:25],
                        jp.get("action", "")))
            print("")
            print("  Total java-permission entries: {}".format(total))
        print("")

    if show_sma:
        from module_nav_lib.license_inspect import load_all_licenses
        licenses, lic_dir, _src = load_all_licenses()
        print("  SMA / LICENSE FEATURE CROSS-REFERENCE")
        print("  Licenses dir: {}".format(lic_dir or "(not resolved)"))

        candidates = set()
        pref = root.get("preferredSymbol") or ""
        mod_name = root.get("moduleName") or ""
        if pref:
            candidates.add(pref)
        if mod_name:
            candidates.add(mod_name)
        if "-" in name:
            candidates.add(name.rsplit("-", 1)[0])
        candidates = {c for c in candidates if c}

        print("  Candidate feature names: {}".format(
            ", ".join(sorted(candidates)) or "(none)"))
        print("")

        hits = []
        for lic in licenses or []:
            for feat in lic["features"]:
                if feat["name"] in candidates:
                    hits.append((lic["vendor"], lic["file"], feat))

        if not hits:
            print("  No matching license feature found. "
                  "The module may be license-free or use a non-standard name.")
        else:
            print("  {:18s} {:28s} {:20s} {:12s} {}".format(
                "VENDOR", "LICENSE FILE", "FEATURE", "SMA-EXEMPT", "EXPIRATION"))
            print("  " + "-" * 96)
            for vendor, fname, feat in hits:
                attrs = feat["attrs"]
                sma = attrs.get("sma.exempt", "no")
                exp = attrs.get("expiration", "(inherits)")
                print("  {:18s} {:28s} {:20s} {:12s} {}".format(
                    vendor[:18], fname[:28], feat["name"][:20],
                    str(sma)[:12], exp))
                extra = [
                    "{}={}".format(k, v) for k, v in sorted(attrs.items())
                    if k not in ("sma.exempt", "expiration")
                ]
                if extra:
                    print("      attrs: {}".format(" ".join(extra)[:100]))
        print("")


def _print_module_detail(name, v):
    """Print detailed info for one module."""
    print("")
    print("  Module:      {}".format(name))
    print("  Parent:      {}".format(v["module"]))
    print("  Type:        {}".format(v["type"] if v["type"] else "standalone"))
    print("  JAR:         {}".format(v["jar"]))
    print("  Has code:    {}".format("yes" if v["has_code"] else "no"))
    print("  Class count: {:,}".format(v["class_count"]))
    print("  Java files:  {:,}".format(v["java_files"]))
    print("  ZKM:         {}".format("YES" if v["zkm"] else "no"))
    print("  Bytecode:    v{} (Java {})".format(
        v["bytecode"], v["bytecode"] - 44 if v["bytecode"] >= 45 else "?"))
    print("  Vineflower:  {}".format("yes" if v["has_vineflower"] else "no"))
    print("  CFR:         {}".format("yes" if v["has_cfr"] else "no"))
    print("")

    if v["packages"]:
        print("  Packages ({}):" .format(len(v["packages"])))
        for p in v["packages"]:
            print("    {}".format(p))
        print("")

    if v["third_party"]:
        print("  Third-party libs ({}):" .format(len(v["third_party"])))
        for p in v["third_party"]:
            print("    {}".format(p))
        print("")


def cmd_modules(base_dir, type_filter=None, zkm_only=False,
                no_code=False, has_code=False, bytecode=None, top_n=None):
    """List modules with filters."""
    data = load_inventory(base_dir)
    if not data:
        return

    inv = data["modules"]
    results = []

    for name, v in inv.items():
        # Apply filters
        if type_filter:
            mod_type = v["type"] if v["type"] else "standalone"
            if mod_type != type_filter:
                continue
        if zkm_only and not v["zkm"]:
            continue
        if no_code and v["has_code"]:
            continue
        if has_code and not v["has_code"]:
            continue
        if bytecode is not None and v["bytecode"] != bytecode:
            continue

        results.append((name, v))

    # Sort
    if top_n:
        results.sort(key=lambda x: x[1]["java_files"], reverse=True)
        results = results[:top_n]
    else:
        results.sort(key=lambda x: x[0])

    # Print
    label_parts = []
    if type_filter:
        label_parts.append("type={}".format(type_filter))
    if zkm_only:
        label_parts.append("ZKM")
    if no_code:
        label_parts.append("no-code")
    if has_code:
        label_parts.append("has-code")
    if bytecode is not None:
        label_parts.append("bytecode=v{}".format(bytecode))
    label = " ({})".format(", ".join(label_parts)) if label_parts else ""

    print("")
    print("  Modules{}: {} results".format(label, len(results)))
    print("  {:40s} {:>4s}  {:>6s}  {:>6s}  {:>3s}  {:>3s}".format(
        "NAME", "TYPE", "JAVA", "CLASS", "ZKM", "BC"))
    print("  " + "-" * 70)

    for name, v in results:
        print("  {:40s} {:>4s}  {:>6,}  {:>6,}  {:>3s}  v{}".format(
            name,
            v["type"] if v["type"] else "-",
            v["java_files"],
            v["class_count"],
            "YES" if v["zkm"] else "",
            v["bytecode"] if (v["bytecode"] or 0) > 0 else "?",
        ))

    print("")
    print("  Total: {} modules, {:,} java files, {:,} classes".format(
        len(results),
        sum(v["java_files"] for _, v in results),
        sum(v["class_count"] for _, v in results),
    ))
    print("")


# ---------------------------------------------------------------------------
# stats command
# ---------------------------------------------------------------------------

def cmd_stats(base_dir, as_json=False):
    """Print corpus summary: modules, classes, indexes, sizes."""
    index_dir = os.path.join(base_dir, "indexes")

    # Gather index file info
    index_files = []
    if os.path.isdir(index_dir):
        for fname in sorted(os.listdir(index_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(index_dir, fname)
                size_bytes = os.path.getsize(fpath)
                index_files.append({
                    "name": fname,
                    "size_bytes": size_bytes,
                    "size_mb": round(size_bytes / (1024 * 1024), 1),
                })

    total_index_bytes = sum(f["size_bytes"] for f in index_files)

    # Load inventory
    inv_data = load_inventory(base_dir)
    inv = inv_data["modules"] if inv_data else {}
    inv_meta = inv_data.get("_meta", {}) if inv_data else {}

    total_submodules = len(inv)
    unique_modules = len(set(v["module"] for v in inv.values())) if inv else 0
    with_code = sum(1 for v in inv.values() if v["has_code"])
    without_code = total_submodules - with_code
    total_java = sum(v["java_files"] for v in inv.values())
    total_classes = sum(v["class_count"] for v in inv.values())
    zkm_count = sum(1 for v in inv.values() if v["zkm"])

    # Types
    types = {}
    for v in inv.values():
        t = v["type"] if v["type"] else "standalone"
        types[t] = types.get(t, 0) + 1

    # Load class-index meta if available
    ci_path = os.path.join(index_dir, "class-index.json")
    ci_meta = {}
    if os.path.isfile(ci_path):
        try:
            with open(ci_path, "r", encoding="utf-8") as f:
                # Only read _meta to avoid loading 32MB
                raw = f.read(2000)
                # Fast parse: find _meta near start
            with open(ci_path, "r", encoding="utf-8") as f:
                ci_data = json.load(f)
                ci_meta = ci_data.get("_meta", {})
                ci_classes = ci_data.get("classes", {})
                ci_total_entries = sum(len(v) for v in ci_classes.values())
                ci_unique_names = len(ci_classes)
        except Exception:
            ci_total_entries = 0
            ci_unique_names = 0
    else:
        ci_total_entries = 0
        ci_unique_names = 0

    # Load swing-index meta if available
    si_path = os.path.join(index_dir, "swing-index.json")
    si_meta = {}
    if os.path.isfile(si_path):
        try:
            with open(si_path, "r", encoding="utf-8") as f:
                si_data = json.load(f)
                si_meta = si_data.get("_meta", {})
        except Exception:
            pass

    # Load inheritance meta if available
    ih_path = os.path.join(index_dir, "inheritance.json")
    ih_meta = {}
    if os.path.isfile(ih_path):
        try:
            with open(ih_path, "r", encoding="utf-8") as f:
                ih_data = json.load(f)
                ih_meta = ih_data.get("_meta", {})
        except Exception:
            pass

    # Load xref meta if available
    xr_path = os.path.join(index_dir, "xref-index.json")
    xr_meta = {}
    if os.path.isfile(xr_path):
        try:
            with open(xr_path, "r", encoding="utf-8") as f:
                xr_data = json.load(f)
                xr_meta = xr_data.get("_meta", {})
        except Exception:
            pass

    # Load method-index meta if available
    mi_path = os.path.join(index_dir, "method-index.json")
    mi_meta = {}
    if os.path.isfile(mi_path):
        try:
            with open(mi_path, "r", encoding="utf-8") as f:
                mi_data = json.load(f)
                mi_meta = mi_data.get("_meta", {})
        except Exception:
            pass

    # Load annotations-index meta if available
    ai_path = os.path.join(index_dir, "annotations-index.json")
    ai_meta = {}
    if os.path.isfile(ai_path):
        try:
            with open(ai_path, "r", encoding="utf-8") as f:
                ai_data = json.load(f)
                ai_meta = ai_data.get("_meta", {})
        except Exception:
            pass

    # Load callgraph-index meta if available
    cg_path = os.path.join(index_dir, "callgraph-index.json")
    cg_meta = {}
    if os.path.isfile(cg_path):
        try:
            with open(cg_path, "r", encoding="utf-8") as f:
                cg_data = json.load(f)
                cg_meta = cg_data.get("_meta", {})
        except Exception:
            pass

    # Load field-index meta if available
    fi_path = os.path.join(index_dir, "field-index.json")
    fi_meta = {}
    if os.path.isfile(fi_path):
        try:
            with open(fi_path, "r", encoding="utf-8") as f:
                fi_data = json.load(f)
                fi_meta = fi_data.get("_meta", {})
        except Exception:
            pass

    # Load exceptions-index meta if available
    ex_path = os.path.join(index_dir, "exceptions-index.json")
    ex_meta = {}
    if os.path.isfile(ex_path):
        try:
            with open(ex_path, "r", encoding="utf-8") as f:
                ex_data = json.load(f)
                ex_meta = ex_data.get("_meta", {})
        except Exception:
            pass

    # Load token-index meta if available (SQLite)
    import sqlite3
    tk_path = os.path.join(index_dir, "token-index.db")
    tk_meta = {}
    if os.path.isfile(tk_path):
        try:
            tk_conn = sqlite3.connect(tk_path)
            tk_cur = tk_conn.cursor()
            tk_cur.execute("SELECT key, value FROM meta")
            tk_meta = dict(tk_cur.fetchall())
            tk_conn.close()
            # Also include token-index.db in the index file list
            tk_size_bytes = os.path.getsize(tk_path)
            index_files.append({
                "name": "token-index.db",
                "size_bytes": tk_size_bytes,
                "size_mb": round(tk_size_bytes / (1024 * 1024), 1),
            })
            total_index_bytes += tk_size_bytes
        except Exception:
            pass

    # Load string-index meta if available (SQLite)
    si_db_path = os.path.join(index_dir, "string-index.db")
    str_meta = {}
    if os.path.isfile(si_db_path):
        try:
            si_conn = sqlite3.connect(si_db_path)
            si_cur = si_conn.cursor()
            si_cur.execute("SELECT key, value FROM meta")
            str_meta = dict(si_cur.fetchall())
            si_conn.close()
            # Also include string-index.db in the index file list
            si_size_bytes = os.path.getsize(si_db_path)
            index_files.append({
                "name": "string-index.db",
                "size_bytes": si_size_bytes,
                "size_mb": round(si_size_bytes / (1024 * 1024), 1),
            })
            total_index_bytes += si_size_bytes
        except Exception:
            pass

    # Build stats dict
    stats = {
        "corpus": {
            "submodules": total_submodules,
            "unique_modules": unique_modules,
            "with_code": with_code,
            "without_code": without_code,
            "java_files": total_java,
            "class_files": total_classes,
            "zkm_obfuscated": zkm_count,
            "types": types,
        },
        "class_index": {
            "total_entries": ci_total_entries,
            "unique_names": ci_unique_names,
            "top_level": ci_meta.get("top_level_classes", 0),
            "inner_classes": ci_meta.get("inner_classes", 0),
            "interfaces": ci_meta.get("interfaces", 0),
            "enums": ci_meta.get("enums", 0),
            "abstract_classes": ci_meta.get("abstract_classes", 0),
            "packages": ci_meta.get("unique_packages", 0),
        },
        "swing_index": {
            "classes_with_ui": si_meta.get("classes_with_ui", 0),
            "dialogs": si_meta.get("total_dialogs", 0),
            "dimensions": si_meta.get("total_dimensions", 0),
            "colors": si_meta.get("total_colors", 0),
            "fonts": si_meta.get("total_fonts", 0),
            "icons": si_meta.get("total_icons", 0),
        },
        "inheritance_index": {
            "unique_parents": ih_meta.get("unique_parents", 0),
            "unique_interfaces": ih_meta.get("unique_interfaces_implemented", 0),
            "classes_with_chains": ih_meta.get("classes_with_chains", 0),
            "max_chain_depth": ih_meta.get("max_chain_depth", 0),
            "avg_chain_depth": ih_meta.get("avg_chain_depth", 0),
            "with_extends": ih_meta.get("with_extends", 0),
            "with_implements": ih_meta.get("with_implements", 0),
        },
        "xref_index": {
            "classes_with_imports": xr_meta.get("classes_with_imports", 0),
            "classes_imported_by_others": xr_meta.get("classes_imported_by_others", 0),
            "total_import_statements": xr_meta.get("total_import_statements", 0),
            "resolved_imports": xr_meta.get("resolved_imports", 0),
            "wildcard_imports": xr_meta.get("wildcard_imports", 0),
            "modules_with_deps": xr_meta.get("modules_with_deps", 0),
            "modules_depended_on": xr_meta.get("modules_depended_on", 0),
            "total_class_import_edges": xr_meta.get("total_class_import_edges", 0),
            "total_module_dep_edges": xr_meta.get("total_module_dep_edges", 0),
        },
        "method_index": {
            "total_definitions": mi_meta.get("total_method_definitions", 0),
            "unique_names": mi_meta.get("unique_method_names", 0),
            "constructors": mi_meta.get("total_constructors", 0),
            "classes_with_methods": mi_meta.get("classes_with_methods", 0),
            "avg_methods_per_class": mi_meta.get("avg_methods_per_class", 0),
            "max_methods_per_class": mi_meta.get("max_methods_per_class", 0),
            "max_methods_class": mi_meta.get("max_methods_class", ""),
        },
        "annotations_index": {
            "niagara_types": ai_meta.get("total_niagara_types", 0),
            "with_properties": ai_meta.get("with_properties", 0),
            "with_actions": ai_meta.get("with_actions", 0),
            "with_topics": ai_meta.get("with_topics", 0),
            "total_properties": ai_meta.get("total_properties", 0),
            "total_actions": ai_meta.get("total_actions", 0),
            "total_topics": ai_meta.get("total_topics", 0),
            "unique_property_types": ai_meta.get("unique_property_types", 0),
            "unique_action_names": ai_meta.get("unique_action_names", 0),
        },
        "callgraph_index": {
            "caller_methods": cg_meta.get("total_caller_methods", 0),
            "unique_callees": cg_meta.get("total_unique_callees", 0),
            "total_edges": cg_meta.get("total_edges", 0),
            "avg_callees_per_caller": cg_meta.get("avg_callees_per_caller", 0),
        } if cg_meta else {},
        "field_index": {
            "total_definitions": fi_meta.get("total_field_definitions", 0),
            "unique_names": fi_meta.get("unique_field_names", 0),
            "static_fields": fi_meta.get("total_static", 0),
            "final_fields": fi_meta.get("total_final", 0),
            "constants": fi_meta.get("total_constants", 0),
            "with_init": fi_meta.get("total_with_init", 0),
            "classes_with_fields": fi_meta.get("classes_with_fields", 0),
            "avg_fields_per_class": fi_meta.get("avg_fields_per_class", 0),
            "max_fields_per_class": fi_meta.get("max_fields_per_class", 0),
            "max_fields_class": fi_meta.get("max_fields_class", ""),
        } if fi_meta else {},
        "exceptions_index": {
            "throws_declarations": ex_meta.get("total_throws_declarations", 0),
            "catch_blocks": ex_meta.get("total_catch_blocks", 0),
            "unique_thrown_types": ex_meta.get("unique_thrown_types", 0),
            "unique_caught_types": ex_meta.get("unique_caught_types", 0),
            "classes_with_throws": ex_meta.get("classes_with_throws", 0),
            "classes_with_catches": ex_meta.get("classes_with_catches", 0),
        } if ex_meta else {},
        "token_index": {
            "total_postings": int(tk_meta.get("total_postings", 0)),
            "unique_tokens": int(tk_meta.get("unique_tokens", 0)),
            "files_with_tokens": int(tk_meta.get("files_with_tokens", 0)),
            "total_lines": int(tk_meta.get("total_lines", 0)),
        } if tk_meta else {},
        "string_index": {
            "total_strings": int(str_meta.get("total_strings", 0)),
            "unique_strings": int(str_meta.get("unique_strings", 0)),
            "files_with_strings": int(str_meta.get("files_with_strings", 0)),
        } if str_meta else {},
        "indexes": index_files,
        "total_index_size_mb": round(total_index_bytes / (1024 * 1024), 1),
    }

    if as_json:
        print(json.dumps(stats, indent=2))
        return

    # Pretty print
    print("")
    print("=" * 65)
    print("  MODULE NAVIGATOR — CORPUS STATS")
    print("=" * 65)
    print("")
    print("  CORPUS:")
    print("    Submodules (JARs):      {:>7,}".format(total_submodules))
    print("    Unique modules:         {:>7,}".format(unique_modules))
    print("    With Java code:         {:>7,}".format(with_code))
    print("    Without code:           {:>7,}".format(without_code))
    print("    Java files:             {:>7,}".format(total_java))
    print("    Class files:            {:>7,}".format(total_classes))
    print("    ZKM obfuscated:         {:>7,}".format(zkm_count))
    print("")
    print("    Types: {}".format(
        ", ".join("{}={}".format(k, v) for k, v in sorted(types.items()))))
    print("")

    if ci_total_entries > 0:
        print("  CLASS INDEX:")
        print("    Total entries:          {:>7,}".format(ci_total_entries))
        print("    Unique class names:     {:>7,}".format(ci_unique_names))
        c = stats["class_index"]
        if c["top_level"]:
            print("    Top-level classes:      {:>7,}".format(c["top_level"]))
        if c["inner_classes"]:
            print("    Inner classes:          {:>7,}".format(c["inner_classes"]))
        if c["interfaces"]:
            print("    Interfaces:             {:>7,}".format(c["interfaces"]))
        if c["enums"]:
            print("    Enums:                  {:>7,}".format(c["enums"]))
        if c["abstract_classes"]:
            print("    Abstract classes:       {:>7,}".format(c["abstract_classes"]))
        if c["packages"]:
            print("    Unique packages:        {:>7,}".format(c["packages"]))
        print("")

    if si_meta:
        print("  SWING INDEX:")
        s = stats["swing_index"]
        print("    Classes with UI:        {:>7,}".format(s["classes_with_ui"]))
        print("    Dialogs:                {:>7,}".format(s["dialogs"]))
        print("    Hardcoded sizes:        {:>7,}".format(s["dimensions"]))
        print("    Hardcoded colors:       {:>7,}".format(s["colors"]))
        print("    Hardcoded fonts:        {:>7,}".format(s["fonts"]))
        print("    Icons:                  {:>7,}".format(s["icons"]))
        print("")

    if ih_meta:
        print("  INHERITANCE INDEX:")
        h = stats["inheritance_index"]
        print("    With extends:           {:>7,}".format(h["with_extends"]))
        print("    With implements:        {:>7,}".format(h["with_implements"]))
        print("    Unique parents:         {:>7,}".format(h["unique_parents"]))
        print("    Unique interfaces:      {:>7,}".format(h["unique_interfaces"]))
        print("    Classes with chains:    {:>7,}".format(h["classes_with_chains"]))
        print("    Max chain depth:        {:>7}".format(h["max_chain_depth"]))
        print("    Avg chain depth:        {:>7.1f}".format(h["avg_chain_depth"]))
        print("")

    if xr_meta:
        print("  XREF INDEX:")
        x = stats["xref_index"]
        print("    Classes with imports:    {:>7,}".format(x["classes_with_imports"]))
        print("    Classes imported by:     {:>7,}".format(x["classes_imported_by_others"]))
        print("    Import statements:       {:>7,}".format(x["total_import_statements"]))
        print("    Resolved imports:        {:>7,}".format(x["resolved_imports"]))
        print("    Wildcard imports:        {:>7,}".format(x["wildcard_imports"]))
        print("    Class import edges:      {:>7,}".format(x["total_class_import_edges"]))
        print("    Modules with deps:       {:>7,}".format(x["modules_with_deps"]))
        print("    Modules depended on:     {:>7,}".format(x["modules_depended_on"]))
        print("    Module dep edges:        {:>7,}".format(x["total_module_dep_edges"]))
        print("")

    if mi_meta:
        print("  METHOD INDEX:")
        m = stats["method_index"]
        print("    Total definitions:       {:>7,}".format(m["total_definitions"]))
        print("    Unique method names:     {:>7,}".format(m["unique_names"]))
        print("    Constructors (<init>):   {:>7,}".format(m["constructors"]))
        print("    Classes with methods:    {:>7,}".format(m["classes_with_methods"]))
        print("    Avg methods/class:       {:>7.1f}".format(m["avg_methods_per_class"]))
        print("    Max methods/class:       {:>7,} ({})".format(
            m["max_methods_per_class"], m["max_methods_class"]))
        print("")

    if ai_meta:
        print("  ANNOTATIONS INDEX:")
        a = stats["annotations_index"]
        print("    Niagara types:           {:>7,}".format(a["niagara_types"]))
        print("    With properties:         {:>7,}".format(a["with_properties"]))
        print("    With actions:            {:>7,}".format(a["with_actions"]))
        print("    With topics:             {:>7,}".format(a["with_topics"]))
        print("    Total properties:        {:>7,}".format(a["total_properties"]))
        print("    Total actions:           {:>7,}".format(a["total_actions"]))
        print("    Total topics:            {:>7,}".format(a["total_topics"]))
        print("    Unique property types:   {:>7,}".format(a["unique_property_types"]))
        print("    Unique action names:     {:>7,}".format(a["unique_action_names"]))
        print("")

    if cg_meta:
        print("  CALL GRAPH INDEX:")
        print("    Caller methods:          {:>7,}".format(cg_meta.get("total_caller_methods", 0)))
        print("    Unique callees:          {:>7,}".format(cg_meta.get("total_unique_callees", 0)))
        print("    Total edges:             {:>7,}".format(cg_meta.get("total_edges", 0)))
        print("    Avg callees/caller:      {:>7.1f}".format(cg_meta.get("avg_callees_per_caller", 0)))
        print("")

    if fi_meta:
        print("  FIELD INDEX:")
        f = stats["field_index"]
        print("    Total definitions:       {:>7,}".format(f["total_definitions"]))
        print("    Unique field names:      {:>7,}".format(f["unique_names"]))
        print("    Static fields:           {:>7,}".format(f["static_fields"]))
        print("    Final fields:            {:>7,}".format(f["final_fields"]))
        print("    Constants (static final):{:>7,}".format(f["constants"]))
        print("    With initial value:      {:>7,}".format(f["with_init"]))
        print("    Classes with fields:     {:>7,}".format(f["classes_with_fields"]))
        print("    Avg fields/class:        {:>7.1f}".format(f["avg_fields_per_class"]))
        print("    Max fields/class:        {:>7,} ({})".format(
            f["max_fields_per_class"], f["max_fields_class"]))
        print("")

    if ex_meta:
        print("  EXCEPTIONS INDEX:")
        ex = stats["exceptions_index"]
        print("    Throws declarations:     {:>7,}".format(ex["throws_declarations"]))
        print("    Catch blocks:            {:>7,}".format(ex["catch_blocks"]))
        print("    Unique thrown types:      {:>7,}".format(ex["unique_thrown_types"]))
        print("    Unique caught types:      {:>7,}".format(ex["unique_caught_types"]))
        print("    Classes with throws:     {:>7,}".format(ex["classes_with_throws"]))
        print("    Classes with catches:    {:>7,}".format(ex["classes_with_catches"]))
        print("")

    if tk_meta:
        print("  TOKEN INDEX (SQLite):")
        tk = stats["token_index"]
        print("    Total postings:      {:>11,}".format(tk["total_postings"]))
        print("    Unique tokens:       {:>11,}".format(tk["unique_tokens"]))
        print("    Files with tokens:   {:>11,}".format(tk["files_with_tokens"]))
        print("    Total lines scanned: {:>11,}".format(tk["total_lines"]))
        print("")

    if str_meta:
        print("  STRING INDEX (SQLite):")
        st = stats["string_index"]
        print("    Total strings:       {:>11,}".format(st["total_strings"]))
        print("    Unique strings:      {:>11,}".format(st["unique_strings"]))
        print("    Files with strings:  {:>11,}".format(st["files_with_strings"]))
        print("")

    print("  INDEXES:")
    for f in index_files:
        print("    {:30s} {:>6.1f} MB".format(f["name"], f["size_mb"]))
    print("    {:30s} {:>6.1f} MB".format("TOTAL", stats["total_index_size_mb"]))
    print("")

    # Help Navigator integration status
    from module_nav_lib.help_bridge import get_help_nav_status
    help_status = get_help_nav_status(base_dir)
    print("  HELP NAVIGATOR INTEGRATION:")
    if help_status["available"]:
        print("    Status:      CONNECTED")
        print("    Path:        {}".format(help_status["path"]))
        print("    Classes:     {:>7,}".format(help_status["classes"]))
        print("    Source files: {:>6,}".format(help_status["source_files"]))
        print("    With slots:  {:>7,}".format(help_status["classes_with_slots"]))
        print("    Indexes:     {:>7}".format(help_status["indexes"]))
    else:
        print("    Status:      NOT AVAILABLE")
        print("    (niagara-help/ not found as sibling of module-navigator/)")
    print("")

    # Commands count
    commands = [
        "inventory", "module", "modules", "class", "search", "package",
        "grep", "source", "source --batch", "snippet", "imports", "imports --external-only",
        "license-feature", "license-features",
        "hierarchy", "implementors",
        "xref", "xref --importers", "xref --imports", "deps", "deps --reverse",
        "method", "method --module", "method --class",
        "methods", "methods --public", "methods --grep",
        "ui dialogs", "ui sizes", "ui colors",
        "ui fonts", "ui class", "ui customizable",
        "slots", "slots --properties", "slots --actions",
        "slots --topics", "slots --by-type", "slots --by-type --module",
        "annotations", "annotations --module",
        "stats", "profile", "repl",
        "full-profile", "cross-ref",
        "patch-target", "patch-plan", "extract",
        "orphans", "deps-graph", "api-surface", "security-audit",
        "strings", "resources", "trace-type", "version-diff",
        "callers", "callees", "call-chain", "hotspots",
        "fields", "fields --static", "fields --public", "fields --grep",
        "field", "field --module",
        "type-consumers", "type-consumers --module",
        "type-producers", "type-producers --module",
        "type-flow",
        "module-calls", "module-api-usage", "coupling",
        "patterns",
        "pattern services", "pattern drivers", "pattern points",
        "pattern views", "pattern extensions", "pattern enums", "pattern structs",
        "pattern --module",
        "bog-trace", "bog-classes", "bog-coverage",
        "throws", "throws --module",
        "catches", "catches --module",
        "export --html", "export --mermaid", "export --dot",
        "token", "token --context",
        "impact", "impact <method>", "impact --depth",
        "find", "find --source", "find --module",
        "deprecated", "deprecated --module",
        "deprecated-users", "deprecated-users <method>",
        "deprecated-risk", "deprecated-risk --module",
        "similar", "clones", "clones --module",
        "config-usage", "config-usage --module", "config-keys",
        "resources-usage",
        "serial", "serial-audit", "serial-audit --module", "serial-conflicts",
        "thread-safety", "thread-scan", "thread-scan --module",
        "lifecycle", "lifecycle --pattern", "lifecycle --pattern --module",
        "lifecycle-scan", "lifecycle-scan --module",
        "string-search", "string-search --module",
        "string-constants",
        "ask",
        "servlets", "servlets --module",
        "routes", "routes --verb",
        "servlet",
        "ords", "ords --scheme", "ords --module",
        "ord-usage", "ord-usage --module",
        "ord-flow",
        "topics", "topics --module",
        "subscribers",
        "pub-sub",
        "bql", "bql --module", "bql --type",
        "bql-tables", "bql-tables --module",
        "bql-class",
        "permissions", "permissions --module", "permissions --declared",
        "permission-flow",
        "credentials", "credentials --module",
        "alarm-flow", "alarm-flow --module",
        "alarm-types",
        "alarm-trace",
        "cycles", "cycles --depth",
        "god-classes", "god-classes --threshold",
        "layer-check",
        "complexity",
        "complexity-scan", "complexity-scan --module",
        "metrics",
        "bookmark", "bookmarks", "bookmarks --sort",
        "unbookmark",
        "history", "history --all", "history --grep",
        "unified", "unified --limit",
        "compare",
        "integration-contract", "integration-contract --min-callers",
        "integration-contract --json", "integration-contract --resolve-virtual",
        "example-mine", "example-mine --pattern", "example-mine --top",
        "example-mine --exclude-tridium", "example-mine --include-docsource",
        "example-mine --min-lines", "example-mine --json",
        "virtual-callers", "virtual-callers --depth",
        "virtual-callers --no-self", "virtual-callers --json",
        "feature-brief", "feature-brief --depth quick",
        "feature-brief --depth full", "feature-brief --out",
        "feature-brief --json",
        "slot-validate", "slot-validate --kind action",
        "slot-validate --kind topic", "slot-validate --json",
        "session save", "session load", "session list",
        "session note", "session export", "session export --as json",
        "session export --out", "session delete",
        "full-stack-trace",
    ]
    print("  COMMANDS: {} available".format(len(commands)))
    print("    {}".format(", ".join(commands)))
    print("")
