"""
Profile command for Module Navigator (Phase 8).

Combines class info + source info + UI info into a single view.

Commands:
  profile <class>    Combined view of class metadata, source, and UI details
"""

import json
import os
import re


def _load_json(base_dir, filename):
    """Load a JSON index file."""
    path = os.path.join(base_dir, "indexes", filename)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_class(classes, class_name):
    """Resolve class name to (name, entry) or (None, None)."""
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


def cmd_profile(base_dir, class_name):
    """Combined profile: class metadata + source info + UI details."""
    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    classes = ci_data.get("classes", {})
    resolved, entry = _resolve_class(classes, class_name)

    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        print("  Try: search '*{}*'".format(class_name))
        return

    source_root = ci_data.get("_meta", {}).get("source", "")

    # --- Section 1: Class metadata ---
    print("")
    print("  " + "=" * 65)
    print("  PROFILE: {}".format(resolved))
    print("  " + "=" * 65)
    print("")
    print("  CLASS INFO:")
    print("    Name:        {}".format(resolved))
    print("    Package:     {}".format(entry["package"]))
    print("    Module:      {}".format(entry["module"]))
    print("    Kind:        {}".format(entry["kind"]))
    print("    Modifiers:   {}".format(" ".join(entry["modifiers"]) if entry["modifiers"] else "-"))
    if entry["extends"]:
        print("    Extends:     {}".format(entry["extends"]))
    if entry["implements"]:
        print("    Implements:  {}".format(", ".join(entry["implements"])))
    print("    Lines:       {:,}".format(entry["lines"]))
    print("    ZKM:         {}".format("YES" if entry["zkm"] else "no"))
    if entry.get("inner_classes"):
        print("    Inner ({:>2}):  {}".format(
            len(entry["inner_classes"]),
            ", ".join(entry["inner_classes"][:10])))
        if len(entry["inner_classes"]) > 10:
            print("                 ... and {} more".format(len(entry["inner_classes"]) - 10))

    # --- Section 2: Source file info ---
    print("")
    print("  SOURCE:")
    print("    Path:        {}".format(entry["path"]))
    filepath = os.path.join(source_root, entry["path"]) if source_root else ""
    if filepath and os.path.isfile(filepath):
        size_bytes = os.path.getsize(filepath)
        print("    Size:        {:,} bytes".format(size_bytes))

        # Extract method signatures
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                source_lines = f.readlines()
        except (IOError, OSError):
            source_lines = []

        if source_lines:
            method_pat = re.compile(
                r'^\s+(?:public|protected|private)\s+'
                r'(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?'
                r'(?:abstract\s+)?'
                r'(\S+)\s+(\w+)\s*\('
            )
            constructor_pat = re.compile(
                r'^\s+(?:public|protected|private)\s+'
                + re.escape(resolved) + r'\s*\('
            )
            methods = []
            constructors = 0
            for line in source_lines:
                m = method_pat.match(line)
                if m:
                    methods.append(m.group(2))
                elif constructor_pat.match(line):
                    constructors += 1

            if constructors > 0 or methods:
                print("    Constructors: {}".format(constructors))
                print("    Methods:     {} ({})".format(
                    len(methods),
                    ", ".join(methods[:15])))
                if len(methods) > 15:
                    print("                 ... and {} more".format(len(methods) - 15))
    else:
        print("    (source file not found on disk)")

    # --- Section 3: UI info (from swing-index) ---
    si_data = _load_json(base_dir, "swing-index.json")
    if si_data:
        si_classes = si_data.get("classes", {})
        ui_rec = None

        if resolved in si_classes:
            val = si_classes[resolved]
            ui_rec = val[0] if isinstance(val, list) else val
        else:
            for k, val in si_classes.items():
                if k.lower() == resolved.lower():
                    ui_rec = val[0] if isinstance(val, list) else val
                    break

        if ui_rec:
            print("")
            print("  UI DETAILS:")
            print("    Category:    {}".format(ui_rec["category"]))
            print("    Parent:      {}".format(ui_rec["parent"] or "-"))

            if ui_rec["titles"]:
                print("    Titles:      {}".format(
                    ", ".join('"{}"'.format(t) for t in ui_rec["titles"])))
            if ui_rec["dialog_methods"]:
                print("    Dialog:      {}".format(", ".join(ui_rec["dialog_methods"])))

            if ui_rec["dimensions"]:
                print("    Dimensions:")
                for dim in ui_rec["dimensions"]:
                    if dim["method"] == "setBounds":
                        print("      Line {:>5}: {}({}, {}, {}, {})".format(
                            dim["line"], dim["method"], dim["x"], dim["y"], dim["w"], dim["h"]))
                    else:
                        print("      Line {:>5}: {}({}, {})".format(
                            dim["line"], dim["method"], dim["w"], dim["h"]))

            if ui_rec["colors"]:
                print("    Colors ({}):" .format(len(ui_rec["colors"])))
                for col in ui_rec["colors"][:5]:
                    print("      Line {:>5}: {} -> {}".format(
                        col["line"], col["target"], col["value"]))
                if len(ui_rec["colors"]) > 5:
                    print("      ... and {} more".format(len(ui_rec["colors"]) - 5))

            if ui_rec["fonts"]:
                print("    Fonts:")
                for fnt in ui_rec["fonts"]:
                    print("      Line {:>5}: \"{}\" {} {}pt".format(
                        fnt["line"], fnt["name"], fnt["style"], fnt["size"]))

            if ui_rec["icons"]:
                print("    Icons:       {} total".format(len(ui_rec["icons"])))
        else:
            print("")
            print("  UI DETAILS:  (not in swing-index — no UI patterns found)")

    # --- Section 4: Module context ---
    inv_data = _load_json(base_dir, "module-inventory.json")
    if inv_data:
        inv = inv_data.get("modules", {})
        mod_key = entry["module"]
        if mod_key in inv:
            mod = inv[mod_key]
            print("")
            print("  MODULE CONTEXT:")
            print("    Module:      {} ({})".format(mod_key, mod["type"] or "standalone"))
            print("    JAR:         {}".format(mod["jar"]))
            print("    Java files:  {:,}".format(mod["java_files"]))
            print("    Class count: {:,}".format(mod["class_count"]))
            if mod["zkm"]:
                print("    ZKM:         YES (obfuscated)")
            if mod["third_party"]:
                print("    3rd-party:   {}".format(", ".join(mod["third_party"][:5])))

    print("")
