#!/usr/bin/env python
"""
Build swing-index.json from decompiled Java sources (Phase 6).

Scans WB (197) and UX (103) modules for UI patterns:
  - Dimensions: setPreferredSize, setMinimumSize, setMaximumSize, setBounds, new Dimension
  - Dialogs: BEdgePane subclasses, BOptionDialog, JDialog, openInDialog, showDialog
  - Colors: new Color(), Color.XXX, setBackground, setForeground
  - Fonts: new Font()
  - Titles: setTitle("...")
  - Icons: BImage.make, new ImageIcon
  - UIManager: UIManager.put()

Input:  indexes/module-inventory.json, indexes/class-index.json
Output: indexes/swing-index.json

Source: /home/cristian/modules/Prototipos/modulos/organized/
Requires: Python 3.x (stdlib only)
"""

import json
import os
import re
import sys
import time


ORGANIZED_DIR = r"/home/cristian/modules/Prototipos/modulos/organized"

# ---------------------------------------------------------------------------
# Regex patterns for UI elements
# ---------------------------------------------------------------------------

# Dimensions — BajaUI style: setPreferredSize(500.0, 380.0) with doubles
RE_SET_PREF_SIZE = re.compile(
    r'setPreferredSize\s*\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)'
)
RE_SET_MIN_SIZE = re.compile(
    r'setMinimumSize\s*\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)'
)
RE_SET_MAX_SIZE = re.compile(
    r'setMaximumSize\s*\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)'
)
RE_SET_BOUNDS = re.compile(
    r'setBounds\s*\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)'
)
# java.awt.Dimension style (rare)
RE_NEW_DIMENSION = re.compile(
    r'new\s+Dimension\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)'
)

# Dialogs
RE_OPEN_IN_DIALOG = re.compile(r'\bopenInDialog\b')
RE_SHOW_DIALOG = re.compile(r'\bshowDialog\b')
RE_JDIALOG = re.compile(r'\bJDialog\b')
RE_BOPTION_DIALOG = re.compile(r'\bBOptionDialog\b')

# Titles
RE_SET_TITLE = re.compile(r'setTitle\s*\(\s*"([^"]*)"')

# Colors
RE_NEW_COLOR_RGB = re.compile(
    r'new\s+Color\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*(\d+))?\s*\)'
)
RE_COLOR_CONSTANT = re.compile(
    r'\bColor\s*\.\s*(BLACK|BLUE|CYAN|DARK_GRAY|GRAY|GREEN|LIGHT_GRAY|MAGENTA|ORANGE|PINK|RED|WHITE|YELLOW|black|blue|cyan|darkGray|gray|green|lightGray|magenta|orange|pink|red|white|yellow)\b'
)
RE_SET_BACKGROUND = re.compile(r'setBackground\s*\(')
RE_SET_FOREGROUND = re.compile(r'setForeground\s*\(')

# Fonts
RE_NEW_FONT = re.compile(
    r'new\s+Font\s*\(\s*"([^"]*)"\s*,\s*(?:Font\.)?(\w+)\s*,\s*(\d+)\s*\)'
)

# UIManager
RE_UIMANAGER_PUT = re.compile(
    r'UIManager\s*\.\s*put\s*\(\s*"([^"]*)"'
)

# Icons
RE_BIMAGE_MAKE = re.compile(r'BImage\s*\.\s*make\s*\(')
RE_NEW_IMAGEICON = re.compile(r'new\s+ImageIcon\s*\(')


# ---------------------------------------------------------------------------
# Classify dialog type
# ---------------------------------------------------------------------------

DIALOG_PARENTS = {
    "BEdgePane", "BDialog", "BOptionPane",
    "JDialog", "JFrame", "JPanel",
    "BAbstractPane", "BPane", "BOptionDialog",
}


def classify_category(class_name, extends, has_dialog_method, has_jdialog,
                      has_boption, has_dimensions, has_colors, has_fonts):
    """Classify a class into a UI category."""
    if extends in DIALOG_PARENTS or has_jdialog or has_boption or has_dialog_method:
        return "dialog"
    if extends and extends.startswith("B") and has_dimensions:
        return "panel"
    if has_colors or has_fonts:
        return "styled"
    return "component"


# ---------------------------------------------------------------------------
# Parse a single file
# ---------------------------------------------------------------------------

def parse_java_file(filepath, lineno_offset=1):
    """Parse a Java file and extract all UI patterns.

    Returns a dict with dimensions, colors, fonts, titles, icons, uimanager,
    dialog_methods, or None if no UI patterns found.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (IOError, OSError):
        return None

    dimensions = []
    colors = []
    fonts = []
    titles = []
    icons = []
    uimanager = []
    dialog_methods = []
    has_jdialog = False
    has_boption = False

    for i, line in enumerate(lines):
        lineno = i + lineno_offset

        # --- Dimensions ---
        for m in RE_SET_PREF_SIZE.finditer(line):
            dimensions.append({
                "method": "setPreferredSize",
                "w": _parse_num(m.group(1)),
                "h": _parse_num(m.group(2)),
                "line": lineno,
            })
        for m in RE_SET_MIN_SIZE.finditer(line):
            dimensions.append({
                "method": "setMinimumSize",
                "w": _parse_num(m.group(1)),
                "h": _parse_num(m.group(2)),
                "line": lineno,
            })
        for m in RE_SET_MAX_SIZE.finditer(line):
            dimensions.append({
                "method": "setMaximumSize",
                "w": _parse_num(m.group(1)),
                "h": _parse_num(m.group(2)),
                "line": lineno,
            })
        for m in RE_SET_BOUNDS.finditer(line):
            dimensions.append({
                "method": "setBounds",
                "x": _parse_num(m.group(1)),
                "y": _parse_num(m.group(2)),
                "w": _parse_num(m.group(3)),
                "h": _parse_num(m.group(4)),
                "line": lineno,
            })
        for m in RE_NEW_DIMENSION.finditer(line):
            dimensions.append({
                "method": "new Dimension",
                "w": int(m.group(1)),
                "h": int(m.group(2)),
                "line": lineno,
            })

        # --- Colors ---
        for m in RE_NEW_COLOR_RGB.finditer(line):
            r, g, b = m.group(1), m.group(2), m.group(3)
            a = m.group(4)
            val = "Color({},{},{})".format(r, g, b)
            if a:
                val = "Color({},{},{},{})".format(r, g, b, a)
            # Determine target
            target = "unknown"
            if RE_SET_BACKGROUND.search(line):
                target = "background"
            elif RE_SET_FOREGROUND.search(line):
                target = "foreground"
            colors.append({"target": target, "value": val, "line": lineno})

        for m in RE_COLOR_CONSTANT.finditer(line):
            target = "unknown"
            if RE_SET_BACKGROUND.search(line):
                target = "background"
            elif RE_SET_FOREGROUND.search(line):
                target = "foreground"
            colors.append({
                "target": target,
                "value": "Color.{}".format(m.group(1)),
                "line": lineno,
            })

        # --- Fonts ---
        for m in RE_NEW_FONT.finditer(line):
            fonts.append({
                "name": m.group(1),
                "style": m.group(2),
                "size": int(m.group(3)),
                "line": lineno,
            })

        # --- Titles ---
        for m in RE_SET_TITLE.finditer(line):
            titles.append(m.group(1))

        # --- Icons ---
        if RE_BIMAGE_MAKE.search(line):
            icons.append({"type": "BImage.make", "line": lineno})
        if RE_NEW_IMAGEICON.search(line):
            icons.append({"type": "new ImageIcon", "line": lineno})

        # --- UIManager ---
        for m in RE_UIMANAGER_PUT.finditer(line):
            uimanager.append({"key": m.group(1), "line": lineno})

        # --- Dialog methods ---
        if RE_OPEN_IN_DIALOG.search(line):
            if "openInDialog" not in dialog_methods:
                dialog_methods.append("openInDialog")
        if RE_SHOW_DIALOG.search(line):
            if "showDialog" not in dialog_methods:
                dialog_methods.append("showDialog")

        # --- JDialog / BOptionDialog ---
        if RE_JDIALOG.search(line):
            has_jdialog = True
        if RE_BOPTION_DIALOG.search(line):
            has_boption = True

    # Only return if we found something
    if not any([dimensions, colors, fonts, titles, icons, uimanager,
                dialog_methods, has_jdialog, has_boption]):
        return None

    return {
        "dimensions": dimensions,
        "colors": colors,
        "fonts": fonts,
        "titles": list(set(titles)),  # dedupe
        "icons": icons,
        "uimanager": uimanager,
        "dialog_methods": dialog_methods,
        "has_jdialog": has_jdialog,
        "has_boption": has_boption,
    }


def _parse_num(s):
    """Parse a number string to int or float."""
    try:
        f = float(s)
        if f == int(f):
            return int(f)
        return f
    except ValueError:
        return s


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_swing_index(base_dir):
    """Build swing-index.json by scanning WB and UX modules."""
    t0 = time.time()

    # Load indexes
    inv_path = os.path.join(base_dir, "indexes", "module-inventory.json")
    cls_path = os.path.join(base_dir, "indexes", "class-index.json")

    if not os.path.isfile(inv_path):
        print("ERROR: module-inventory.json not found. Run build_module_inventory.py first.")
        sys.exit(1)
    if not os.path.isfile(cls_path):
        print("ERROR: class-index.json not found. Run build_class_index.py first.")
        sys.exit(1)

    print("Loading module-inventory.json ...")
    with open(inv_path, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    print("Loading class-index.json ...")
    with open(cls_path, "r", encoding="utf-8") as f:
        class_index = json.load(f)

    source_root = class_index.get("_meta", {}).get("source", ORGANIZED_DIR)
    modules = inventory.get("modules", {})
    classes = class_index.get("classes", {})

    # Filter WB + UX modules
    wb_ux_modules = set()
    for mod_name, mod_info in modules.items():
        if mod_info.get("type") in ("wb", "ux"):
            wb_ux_modules.add(mod_name)

    print("WB+UX modules: {} ({} WB, {} UX)".format(
        len(wb_ux_modules),
        sum(1 for m in wb_ux_modules if modules[m]["type"] == "wb"),
        sum(1 for m in wb_ux_modules if modules[m]["type"] == "ux"),
    ))

    # Collect top-level classes from WB/UX modules
    files_to_scan = []
    for cname, entries in classes.items():
        for entry in entries:
            if entry["outer_class"] is not None:
                continue
            if entry["module"] not in wb_ux_modules:
                continue
            files_to_scan.append((cname, entry))

    print("Classes to scan: {:,}".format(len(files_to_scan)))

    # Scan each file
    swing_index = {}
    files_scanned = 0
    classes_with_ui = 0

    for cname, entry in files_to_scan:
        filepath = os.path.join(source_root, entry["path"])
        if not os.path.isfile(filepath):
            continue

        files_scanned += 1
        result = parse_java_file(filepath)
        if result is None:
            continue

        classes_with_ui += 1
        extends = entry.get("extends", None)

        category = classify_category(
            cname, extends,
            has_dialog_method=bool(result["dialog_methods"]),
            has_jdialog=result["has_jdialog"],
            has_boption=result["has_boption"],
            has_dimensions=bool(result["dimensions"]),
            has_colors=bool(result["colors"]),
            has_fonts=bool(result["fonts"]),
        )

        rec = {
            "module": entry["module"],
            "package": entry.get("package", ""),
            "category": category,
            "parent": extends,
            "dimensions": result["dimensions"],
            "colors": result["colors"],
            "fonts": result["fonts"],
            "titles": result["titles"],
            "icons": result["icons"],
            "uimanager": result["uimanager"],
            "dialog_methods": result["dialog_methods"],
        }

        # Store: if class name already exists (from different module), use list
        if cname in swing_index:
            if isinstance(swing_index[cname], list):
                swing_index[cname].append(rec)
            else:
                swing_index[cname] = [swing_index[cname], rec]
        else:
            swing_index[cname] = rec

    elapsed = time.time() - t0

    # Compute stats
    total_dims = 0
    total_colors = 0
    total_fonts = 0
    total_titles = 0
    total_icons = 0
    total_uimgr = 0
    total_dialogs = 0
    category_counts = {}

    for cname, data in swing_index.items():
        entries = data if isinstance(data, list) else [data]
        for rec in entries:
            total_dims += len(rec["dimensions"])
            total_colors += len(rec["colors"])
            total_fonts += len(rec["fonts"])
            total_titles += len(rec["titles"])
            total_icons += len(rec["icons"])
            total_uimgr += len(rec["uimanager"])
            cat = rec["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
            if cat == "dialog":
                total_dialogs += 1

    # Build output
    output = {
        "_meta": {
            "description": "UI/Swing pattern index for Niagara N4 WB+UX modules",
            "source": source_root,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "build_time_sec": round(elapsed, 1),
            "modules_scanned": len(wb_ux_modules),
            "files_scanned": files_scanned,
            "classes_with_ui": classes_with_ui,
            "total_dimensions": total_dims,
            "total_colors": total_colors,
            "total_fonts": total_fonts,
            "total_titles": total_titles,
            "total_icons": total_icons,
            "total_uimanager": total_uimgr,
            "total_dialogs": total_dialogs,
            "categories": category_counts,
        },
        "classes": swing_index,
    }

    # Write
    out_path = os.path.join(base_dir, "indexes", "swing-index.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)

    print("")
    print("=" * 60)
    print("SWING INDEX BUILD COMPLETE")
    print("=" * 60)
    print("")
    print("  Files scanned:       {:>6,}".format(files_scanned))
    print("  Classes with UI:     {:>6,}".format(classes_with_ui))
    print("  Total dimensions:    {:>6,}".format(total_dims))
    print("  Total colors:        {:>6,}".format(total_colors))
    print("  Total fonts:         {:>6,}".format(total_fonts))
    print("  Total titles:        {:>6,}".format(total_titles))
    print("  Total icons:         {:>6,}".format(total_icons))
    print("  Total UIManager:     {:>6,}".format(total_uimgr))
    print("  Total dialogs:       {:>6,}".format(total_dialogs))
    print("")
    print("  Categories:")
    for cat in sorted(category_counts.keys()):
        print("    {:15s} {:>5,}".format(cat, category_counts[cat]))
    print("")
    print("  Output: {} ({:.1f} MB)".format(out_path, size_mb))
    print("  Build time: {:.1f}s".format(elapsed))
    print("")


def main():
    # Base dir = parent of tools/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    if not os.path.isdir(os.path.join(base_dir, "indexes")):
        print("ERROR: indexes/ not found. Run from module-navigator/tools/")
        sys.exit(1)

    build_swing_index(base_dir)


if __name__ == "__main__":
    main()
