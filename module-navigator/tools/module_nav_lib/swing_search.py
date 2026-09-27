"""
UI/Swing search commands for Module Navigator (Phase 6).

Commands:
  ui dialogs [-n N]         List all dialog classes (BEdgePane, JDialog, etc.)
  ui sizes [-n N]           List all classes with hardcoded dimensions
  ui colors [-n N]          List all hardcoded colors
  ui fonts [-n N]           List all hardcoded fonts
  ui class <name>           Full UI details for a specific class
  ui customizable           Summary of all patcheable UI elements
"""

import json
import os


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

_swing_index_cache = None


def _load_swing_index(base_dir):
    """Load swing-index.json (cached)."""
    global _swing_index_cache
    if _swing_index_cache is not None:
        return _swing_index_cache
    path = os.path.join(base_dir, "indexes", "swing-index.json")
    if not os.path.isfile(path):
        print("ERROR: swing-index.json not found.")
        print("Run: python tools/build_swing_index.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        _swing_index_cache = json.load(f)
    return _swing_index_cache


def _iter_entries(data):
    """Iterate all (class_name, record) pairs from swing index."""
    classes = data.get("classes", {})
    for cname, val in classes.items():
        if isinstance(val, list):
            for rec in val:
                yield cname, rec
        else:
            yield cname, val


# ---------------------------------------------------------------------------
# ui dialogs
# ---------------------------------------------------------------------------

def cmd_ui_dialogs(base_dir, limit=50):
    """List all dialog classes."""
    data = _load_swing_index(base_dir)
    if not data:
        return

    dialogs = []
    for cname, rec in _iter_entries(data):
        if rec["category"] == "dialog":
            dialogs.append((cname, rec))

    dialogs.sort(key=lambda x: (x[1]["module"], x[0]))

    print("")
    print("  UI DIALOGS — {} classes".format(len(dialogs)))
    print("  {:35s} {:30s} {:15s} {:s}".format("CLASS", "MODULE", "PARENT", "DETAILS"))
    print("  " + "-" * 100)

    shown = 0
    for cname, rec in dialogs:
        if shown >= limit:
            break
        shown += 1

        details = []
        if rec["dimensions"]:
            dims = rec["dimensions"][0]
            details.append("{}x{}".format(dims["w"], dims["h"]))
        if rec["titles"]:
            details.append('title="{}"'.format(rec["titles"][0]))
        if rec["dialog_methods"]:
            details.append(", ".join(rec["dialog_methods"]))

        print("  {:35s} {:30s} {:15s} {:s}".format(
            cname[:35],
            rec["module"][:30],
            (rec["parent"] or "-")[:15],
            "  ".join(details),
        ))

    if len(dialogs) > limit:
        print("")
        print("  ... {} more (use -n to increase)".format(len(dialogs) - limit))
    print("")


# ---------------------------------------------------------------------------
# ui sizes
# ---------------------------------------------------------------------------

def cmd_ui_sizes(base_dir, limit=50):
    """List all classes with hardcoded dimensions."""
    data = _load_swing_index(base_dir)
    if not data:
        return

    sized = []
    for cname, rec in _iter_entries(data):
        if rec["dimensions"]:
            sized.append((cname, rec))

    sized.sort(key=lambda x: (x[1]["module"], x[0]))

    total_dims = sum(len(r["dimensions"]) for _, r in sized)

    print("")
    print("  UI SIZES — {} classes, {} dimension entries".format(len(sized), total_dims))
    print("  {:35s} {:30s} {:12s} {:>6s} {:>6s} {:>5s}".format(
        "CLASS", "MODULE", "METHOD", "W", "H", "LINE"))
    print("  " + "-" * 100)

    shown = 0
    for cname, rec in sized:
        for dim in rec["dimensions"]:
            if shown >= limit:
                break
            shown += 1

            method = dim["method"]
            w = dim.get("w", "?")
            h = dim.get("h", "?")
            line = dim.get("line", "?")

            print("  {:35s} {:30s} {:12s} {:>6s} {:>6s} {:>5s}".format(
                cname[:35],
                rec["module"][:30],
                method[:12],
                str(w),
                str(h),
                str(line),
            ))

        if shown >= limit:
            break

    if total_dims > limit:
        print("")
        print("  ... {} more entries (use -n to increase)".format(total_dims - limit))
    print("")


# ---------------------------------------------------------------------------
# ui colors
# ---------------------------------------------------------------------------

def cmd_ui_colors(base_dir, limit=50):
    """List all hardcoded colors."""
    data = _load_swing_index(base_dir)
    if not data:
        return

    colored = []
    for cname, rec in _iter_entries(data):
        if rec["colors"]:
            colored.append((cname, rec))

    colored.sort(key=lambda x: (x[1]["module"], x[0]))

    total_colors = sum(len(r["colors"]) for _, r in colored)

    print("")
    print("  UI COLORS — {} classes, {} color entries".format(len(colored), total_colors))
    print("  {:35s} {:30s} {:12s} {:25s} {:>5s}".format(
        "CLASS", "MODULE", "TARGET", "VALUE", "LINE"))
    print("  " + "-" * 110)

    shown = 0
    for cname, rec in colored:
        for col in rec["colors"]:
            if shown >= limit:
                break
            shown += 1
            print("  {:35s} {:30s} {:12s} {:25s} {:>5s}".format(
                cname[:35],
                rec["module"][:30],
                col["target"][:12],
                col["value"][:25],
                str(col["line"]),
            ))
        if shown >= limit:
            break

    if total_colors > limit:
        print("")
        print("  ... {} more entries (use -n to increase)".format(total_colors - limit))
    print("")


# ---------------------------------------------------------------------------
# ui fonts
# ---------------------------------------------------------------------------

def cmd_ui_fonts(base_dir, limit=50):
    """List all hardcoded fonts."""
    data = _load_swing_index(base_dir)
    if not data:
        return

    fonted = []
    for cname, rec in _iter_entries(data):
        if rec["fonts"]:
            fonted.append((cname, rec))

    fonted.sort(key=lambda x: (x[1]["module"], x[0]))

    total_fonts = sum(len(r["fonts"]) for _, r in fonted)

    print("")
    print("  UI FONTS — {} classes, {} font entries".format(len(fonted), total_fonts))
    print("  {:35s} {:30s} {:15s} {:10s} {:>5s} {:>5s}".format(
        "CLASS", "MODULE", "FONT NAME", "STYLE", "SIZE", "LINE"))
    print("  " + "-" * 105)

    shown = 0
    for cname, rec in fonted:
        for fnt in rec["fonts"]:
            if shown >= limit:
                break
            shown += 1
            print("  {:35s} {:30s} {:15s} {:10s} {:>5s} {:>5s}".format(
                cname[:35],
                rec["module"][:30],
                fnt["name"][:15],
                fnt["style"][:10],
                str(fnt["size"]),
                str(fnt["line"]),
            ))
        if shown >= limit:
            break

    if total_fonts > limit:
        print("")
        print("  ... {} more entries (use -n to increase)".format(total_fonts - limit))
    print("")


# ---------------------------------------------------------------------------
# ui class <name>
# ---------------------------------------------------------------------------

def cmd_ui_class(base_dir, class_name):
    """Show full UI details for a specific class."""
    data = _load_swing_index(base_dir)
    if not data:
        return

    classes = data.get("classes", {})

    # Exact match
    if class_name in classes:
        val = classes[class_name]
        entries = val if isinstance(val, list) else [val]
        for rec in entries:
            _print_ui_detail(class_name, rec)
        return

    # Case-insensitive fallback
    name_lower = class_name.lower()
    for k, val in classes.items():
        if k.lower() == name_lower:
            entries = val if isinstance(val, list) else [val]
            for rec in entries:
                _print_ui_detail(k, rec)
            return

    # Partial match
    matches = [k for k in classes if class_name.lower() in k.lower()]
    if matches:
        print("")
        print("  '{}' not found. Did you mean:".format(class_name))
        for m in sorted(matches)[:15]:
            val = classes[m]
            entries = val if isinstance(val, list) else [val]
            mod = entries[0]["module"]
            print("    {} ({})".format(m, mod))
        print("")
    else:
        print("  Class '{}' not found in swing index.".format(class_name))
        print("  The class may not have UI patterns or may not be in a WB/UX module.")


def _print_ui_detail(cname, rec):
    """Print full UI details for one class record."""
    print("")
    print("  " + "=" * 60)
    print("  UI DETAILS: {}".format(cname))
    print("  " + "=" * 60)
    print("")
    print("  Module:    {}".format(rec["module"]))
    print("  Package:   {}".format(rec.get("package", "?")))
    print("  Category:  {}".format(rec["category"]))
    print("  Parent:    {}".format(rec["parent"] or "-"))

    if rec["titles"]:
        print("  Titles:    {}".format(", ".join('"{}"'.format(t) for t in rec["titles"])))

    if rec["dialog_methods"]:
        print("  Dialogs:   {}".format(", ".join(rec["dialog_methods"])))

    # Dimensions
    if rec["dimensions"]:
        print("")
        print("  DIMENSIONS ({}):" .format(len(rec["dimensions"])))
        for dim in rec["dimensions"]:
            if dim["method"] == "setBounds":
                print("    Line {:>5}: {}({}, {}, {}, {})".format(
                    dim["line"], dim["method"], dim["x"], dim["y"], dim["w"], dim["h"]))
            else:
                print("    Line {:>5}: {}({}, {})".format(
                    dim["line"], dim["method"], dim["w"], dim["h"]))

    # Colors
    if rec["colors"]:
        print("")
        print("  COLORS ({}):" .format(len(rec["colors"])))
        for col in rec["colors"]:
            print("    Line {:>5}: {} → {}".format(
                col["line"], col["target"], col["value"]))

    # Fonts
    if rec["fonts"]:
        print("")
        print("  FONTS ({}):" .format(len(rec["fonts"])))
        for fnt in rec["fonts"]:
            print("    Line {:>5}: \"{}\" {} {}pt".format(
                fnt["line"], fnt["name"], fnt["style"], fnt["size"]))

    # Icons
    if rec["icons"]:
        print("")
        print("  ICONS ({}):" .format(len(rec["icons"])))
        for ico in rec["icons"]:
            print("    Line {:>5}: {}".format(ico["line"], ico["type"]))

    # UIManager
    if rec["uimanager"]:
        print("")
        print("  UIMANAGER OVERRIDES ({}):" .format(len(rec["uimanager"])))
        for um in rec["uimanager"]:
            print("    Line {:>5}: \"{}\"".format(um["line"], um["key"]))

    print("")


# ---------------------------------------------------------------------------
# ui customizable
# ---------------------------------------------------------------------------

def cmd_ui_customizable(base_dir):
    """Summary of all patcheable UI elements."""
    data = _load_swing_index(base_dir)
    if not data:
        return

    meta = data.get("_meta", {})

    # Collect stats per module
    module_stats = {}
    for cname, rec in _iter_entries(data):
        mod = rec["module"]
        if mod not in module_stats:
            module_stats[mod] = {
                "classes": 0, "dimensions": 0, "colors": 0,
                "fonts": 0, "titles": 0, "icons": 0,
                "uimanager": 0, "dialogs": 0,
            }
        s = module_stats[mod]
        s["classes"] += 1
        s["dimensions"] += len(rec["dimensions"])
        s["colors"] += len(rec["colors"])
        s["fonts"] += len(rec["fonts"])
        s["titles"] += len(rec["titles"])
        s["icons"] += len(rec["icons"])
        s["uimanager"] += len(rec["uimanager"])
        if rec["category"] == "dialog":
            s["dialogs"] += 1

    print("")
    print("  " + "=" * 70)
    print("  UI CUSTOMIZABLE — Everything patcheable in Niagara Workbench")
    print("  " + "=" * 70)
    print("")

    # Global totals
    print("  GLOBAL SUMMARY:")
    print("    Modules scanned:     {:>6,}".format(meta.get("modules_scanned", 0)))
    print("    Files scanned:       {:>6,}".format(meta.get("files_scanned", 0)))
    print("    Classes with UI:     {:>6,}".format(meta.get("classes_with_ui", 0)))
    print("    Dialog classes:      {:>6,}".format(meta.get("total_dialogs", 0)))
    print("    Hardcoded sizes:     {:>6,}".format(meta.get("total_dimensions", 0)))
    print("    Hardcoded colors:    {:>6,}".format(meta.get("total_colors", 0)))
    print("    Hardcoded fonts:     {:>6,}".format(meta.get("total_fonts", 0)))
    print("    Window titles:       {:>6,}".format(meta.get("total_titles", 0)))
    print("    Icons:               {:>6,}".format(meta.get("total_icons", 0)))
    print("    UIManager overrides: {:>6,}".format(meta.get("total_uimanager", 0)))
    print("")

    # Categories
    cats = meta.get("categories", {})
    if cats:
        print("  CATEGORIES:")
        for cat in sorted(cats.keys()):
            print("    {:15s} {:>5,} classes".format(cat, cats[cat]))
        print("")

    # Top modules by patcheable items
    ranked = sorted(
        module_stats.items(),
        key=lambda x: (x[1]["dimensions"] + x[1]["colors"] + x[1]["fonts"] + x[1]["uimanager"]),
        reverse=True,
    )

    print("  TOP MODULES BY PATCHEABLE UI ELEMENTS:")
    print("  {:35s} {:>5s} {:>5s} {:>5s} {:>5s} {:>5s} {:>5s}".format(
        "MODULE", "CLS", "SIZES", "COLOR", "FONT", "UIMGR", "DLG"))
    print("  " + "-" * 70)

    for mod, s in ranked[:25]:
        total_patcheable = s["dimensions"] + s["colors"] + s["fonts"] + s["uimanager"]
        if total_patcheable == 0:
            continue
        print("  {:35s} {:>5,} {:>5,} {:>5,} {:>5,} {:>5,} {:>5,}".format(
            mod[:35], s["classes"], s["dimensions"], s["colors"],
            s["fonts"], s["uimanager"], s["dialogs"],
        ))

    print("")
    print("  Use 'ui class <name>' for full details on any class.")
    print("  Use 'ui dialogs/sizes/colors/fonts' for filtered lists.")
    print("")
