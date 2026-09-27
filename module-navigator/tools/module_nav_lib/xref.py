"""
Cross-reference commands for Module Navigator (Phase 4).

Commands:
  xref <class>                  Who imports this class + what it imports
  xref <class> --importers [-n N]  Only classes that import it
  xref <class> --imports [-n N]    Only imports of that class
  deps <module> [-n N]          Modules this module depends on
  deps <module> --reverse [-n N]   Modules that depend on it
"""

import json
import os


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

_xref_cache = None


def load_xref(base_dir):
    """Load xref-index.json (or use cached version from REPL)."""
    global _xref_cache
    if _xref_cache is not None:
        return _xref_cache

    path = os.path.join(base_dir, "indexes", "xref-index.json")
    if not os.path.isfile(path):
        print("ERROR: xref-index.json not found.")
        print("Run: python tools/build_xref.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def _load_class_index(base_dir):
    """Load class-index.json for module info lookups."""
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


def _get_module_info(class_name, ci_classes):
    """Get (module, package) for a class from class-index, or None."""
    if class_name in ci_classes:
        entries = ci_classes[class_name]
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            return (top[0]["module"], top[0]["package"])
    return None


# ---------------------------------------------------------------------------
# xref command
# ---------------------------------------------------------------------------

def cmd_xref(base_dir, class_name, show_importers=False, show_imports=False, limit=50):
    """Show cross-references for a class."""
    xref = load_xref(base_dir)
    if not xref:
        return

    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}

    imports = xref.get("class_imports", {}).get(class_name, [])
    imported_by = xref.get("class_imported_by", {}).get(class_name, [])

    # Check if class exists at all
    if not imports and not imported_by:
        if ci_classes and class_name in ci_classes:
            print("")
            print("  {} exists but has no cross-references in the xref index.".format(class_name))
            print("  (May have no imports or not be imported by anyone)")
            print("")
        else:
            print("  Class '{}' not found.".format(class_name))
            print("  Try: search '*{}*'".format(class_name))
        return

    # Get module info for the queried class
    info = _get_module_info(class_name, ci_classes)

    if show_importers:
        _show_importers(class_name, imported_by, ci_classes, info, limit)
    elif show_imports:
        _show_imports(class_name, imports, ci_classes, info, limit)
    else:
        _show_full_xref(class_name, imports, imported_by, ci_classes, info, limit)


def _show_full_xref(class_name, imports, imported_by, ci_classes, info, limit):
    """Show both imports and importers for a class."""
    print("")
    print("  XREF: {}".format(class_name))
    if info:
        print("  Module: {}  Package: {}".format(info[0], info[1]))
    print("")

    # Imports (what this class uses)
    print("  IMPORTS ({} classes):".format(len(imports)))
    if imports:
        print("  {:>35s}  {:20s}  {:s}".format("CLASS", "MODULE", "PACKAGE"))
        print("  " + "-" * 80)
        shown = 0
        for cls in imports:
            if shown >= limit:
                break
            cls_info = _get_module_info(cls, ci_classes)
            mod = cls_info[0] if cls_info else "?"
            pkg = cls_info[1] if cls_info else "?"
            print("  {:>35s}  {:20s}  {:s}".format(cls, mod, pkg))
            shown += 1
        if len(imports) > limit:
            print("  ... and {} more (use --imports -n {} to see all)".format(
                len(imports) - limit, len(imports)))
    else:
        print("    (none)")
    print("")

    # Imported by (who uses this class)
    print("  IMPORTED BY ({} classes):".format(len(imported_by)))
    if imported_by:
        print("  {:>35s}  {:20s}  {:s}".format("CLASS", "MODULE", "PACKAGE"))
        print("  " + "-" * 80)
        shown = 0
        for cls in imported_by:
            if shown >= limit:
                break
            cls_info = _get_module_info(cls, ci_classes)
            mod = cls_info[0] if cls_info else "?"
            pkg = cls_info[1] if cls_info else "?"
            print("  {:>35s}  {:20s}  {:s}".format(cls, mod, pkg))
            shown += 1
        if len(imported_by) > limit:
            print("  ... and {} more (use --importers -n {} to see all)".format(
                len(imported_by) - limit, len(imported_by)))
    else:
        print("    (none)")
    print("")


def _show_importers(class_name, imported_by, ci_classes, info, limit):
    """Show only classes that import the given class."""
    print("")
    print("  IMPORTERS of {}: {} classes".format(class_name, len(imported_by)))
    if info:
        print("  Module: {}  Package: {}".format(info[0], info[1]))
    print("")

    if not imported_by:
        print("    (no classes import {})".format(class_name))
        print("")
        return

    print("  {:>35s}  {:20s}  {:s}".format("CLASS", "MODULE", "PACKAGE"))
    print("  " + "-" * 80)

    shown = 0
    for cls in imported_by:
        if shown >= limit:
            break
        cls_info = _get_module_info(cls, ci_classes)
        mod = cls_info[0] if cls_info else "?"
        pkg = cls_info[1] if cls_info else "?"
        print("  {:>35s}  {:20s}  {:s}".format(cls, mod, pkg))
        shown += 1

    if len(imported_by) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(imported_by) - limit, len(imported_by)))
    print("")


def _show_imports(class_name, imports, ci_classes, info, limit):
    """Show only what the given class imports."""
    print("")
    print("  IMPORTS of {}: {} classes".format(class_name, len(imports)))
    if info:
        print("  Module: {}  Package: {}".format(info[0], info[1]))
    print("")

    if not imports:
        print("    (no imports found for {})".format(class_name))
        print("")
        return

    print("  {:>35s}  {:20s}  {:s}".format("CLASS", "MODULE", "PACKAGE"))
    print("  " + "-" * 80)

    shown = 0
    for cls in imports:
        if shown >= limit:
            break
        cls_info = _get_module_info(cls, ci_classes)
        mod = cls_info[0] if cls_info else "?"
        pkg = cls_info[1] if cls_info else "?"
        print("  {:>35s}  {:20s}  {:s}".format(cls, mod, pkg))
        shown += 1

    if len(imports) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(imports) - limit, len(imports)))
    print("")


# ---------------------------------------------------------------------------
# deps command
# ---------------------------------------------------------------------------

def cmd_deps(base_dir, module_name, reverse=False, limit=50):
    """Show module-level dependencies."""
    xref = load_xref(base_dir)
    if not xref:
        return

    if reverse:
        _show_deps_reverse(module_name, xref, limit)
    else:
        _show_deps_forward(module_name, xref, limit)


def _show_deps_forward(module_name, xref, limit):
    """Show modules that this module depends on."""
    deps_map = xref.get("module_deps", {})

    if module_name not in deps_map:
        # Check if module exists at all in any map
        all_modules = set(deps_map.keys())
        all_modules.update(xref.get("module_depended_by", {}).keys())
        if module_name in all_modules:
            print("")
            print("  {} has no outgoing dependencies.".format(module_name))
            print("")
        else:
            # Try partial match
            matches = [m for m in all_modules if module_name.lower() in m.lower()]
            if matches:
                print("  Module '{}' not found. Did you mean:".format(module_name))
                for m in sorted(matches)[:10]:
                    print("    {}".format(m))
            else:
                print("  Module '{}' not found in xref index.".format(module_name))
        return

    deps = deps_map[module_name]

    print("")
    print("  DEPENDENCIES of {}: {} modules".format(module_name, len(deps)))
    print("")
    print("  {:>40s}".format("MODULE"))
    print("  " + "-" * 40)

    shown = 0
    for mod in deps:
        if shown >= limit:
            break
        print("  {:>40s}".format(mod))
        shown += 1

    if len(deps) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(deps) - limit, len(deps)))
    print("")


def _show_deps_reverse(module_name, xref, limit):
    """Show modules that depend on this module."""
    depby_map = xref.get("module_depended_by", {})

    if module_name not in depby_map:
        # Check if module exists at all
        all_modules = set(depby_map.keys())
        all_modules.update(xref.get("module_deps", {}).keys())
        if module_name in all_modules:
            print("")
            print("  No modules depend on {}.".format(module_name))
            print("")
        else:
            matches = [m for m in all_modules if module_name.lower() in m.lower()]
            if matches:
                print("  Module '{}' not found. Did you mean:".format(module_name))
                for m in sorted(matches)[:10]:
                    print("    {}".format(m))
            else:
                print("  Module '{}' not found in xref index.".format(module_name))
        return

    dependents = depby_map[module_name]

    print("")
    print("  DEPENDED ON BY (reverse deps of {}): {} modules".format(
        module_name, len(dependents)))
    print("")
    print("  {:>40s}".format("MODULE"))
    print("  " + "-" * 40)

    shown = 0
    for mod in dependents:
        if shown >= limit:
            break
        print("  {:>40s}".format(mod))
        shown += 1

    if len(dependents) > limit:
        print("")
        print("  ... and {} more (use -n {} to see all)".format(
            len(dependents) - limit, len(dependents)))
    print("")
