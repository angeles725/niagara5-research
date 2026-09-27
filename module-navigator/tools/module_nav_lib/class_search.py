"""
Class search commands for Module Navigator.

Commands:
  class <name>           Look up a class by exact name
  search <pattern>       Search classes by glob pattern (e.g. "*Dialog*", "BLink*")
  package <name>         List classes in a package
  package --all          List all packages with class counts
"""

import fnmatch
import json
import os


def load_class_index(base_dir):
    """Load class-index.json."""
    path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(path):
        print("ERROR: class-index.json not found.")
        print("Run: python tools/build_class_index.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# --- Display helpers ---

def _print_class_detail(name, entry):
    """Print detailed info for one class entry."""
    print("")
    print("  Class:       {}".format(name))
    print("  Package:     {}".format(entry['package']))
    print("  Module:      {}".format(entry['module']))
    print("  Kind:        {}".format(entry['kind']))
    print("  Modifiers:   {}".format(' '.join(entry['modifiers']) if entry['modifiers'] else '-'))
    if entry['extends']:
        print("  Extends:     {}".format(entry['extends']))
    if entry['implements']:
        print("  Implements:  {}".format(', '.join(entry['implements'])))
    print("  Lines:       {:,}".format(entry['lines']))
    print("  Path:        {}".format(entry['path']))
    print("  ZKM:         {}".format("YES" if entry['zkm'] else "no"))
    if entry.get('outer_class'):
        print("  Outer class: {}".format(entry['outer_class']))
    if entry.get('inner_classes'):
        print("  Inner classes ({}):" .format(len(entry['inner_classes'])))
        for ic in entry['inner_classes']:
            print("    {}".format(ic))
    print("")


def _format_class_row(name, entry, name_width=35):
    """Format a one-line summary for a class."""
    extra = ""
    if entry.get('outer_class'):
        extra = "in:" + entry['outer_class']
    elif entry['zkm']:
        extra = "ZKM"

    return "  {:>{nw}s}  {:9s} {:>6}  {:20s} {:s}".format(
        name[:name_width],
        entry['kind'],
        "{:,}".format(entry['lines']) if entry['lines'] > 0 else "-",
        entry['module'][:20],
        entry['package'] + ("  " + extra if extra else ""),
        nw=name_width,
    )


# --- Commands ---

def cmd_class(base_dir, name):
    """Look up a class by exact name."""
    data = load_class_index(base_dir)
    if not data:
        return

    classes = data["classes"]

    # Exact match
    if name in classes:
        entries = classes[name]
        if len(entries) == 1:
            _print_class_detail(name, entries[0])
        else:
            print("")
            print("  {} entries for '{}':" .format(len(entries), name))
            print("")
            for i, e in enumerate(entries):
                fqn = "{}.{}".format(e['package'], name) if e['package'] else name
                print("  [{}] {}".format(i + 1, fqn))
                print("      Module: {}  Kind: {}  Lines: {:,}".format(
                    e['module'], e['kind'], e['lines']))
                if e['extends']:
                    print("      Extends: {}".format(e['extends']))
                if e['outer_class']:
                    print("      Inner class of: {}".format(e['outer_class']))
            print("")
        return

    # Case-insensitive fallback
    name_lower = name.lower()
    ci_matches = [(k, classes[k]) for k in classes if k.lower() == name_lower]

    if ci_matches:
        print("")
        print("  No exact match for '{}'. Case-insensitive matches:".format(name))
        print("")
        for cname, entries in ci_matches:
            for e in entries:
                print("    {} ({}, {})".format(cname, e['package'], e['module']))
        print("")
        return

    # Suggest search
    print("  Class '{}' not found.".format(name))
    print("  Try: search '*{}*'".format(name))


def cmd_search(base_dir, pattern, limit=50):
    """Search classes by glob pattern (case-insensitive)."""
    data = load_class_index(base_dir)
    if not data:
        return

    classes = data["classes"]
    pattern_lower = pattern.lower()

    # Match class names (top-level and inner that are indexed)
    matches = []
    for cname, entries in classes.items():
        if fnmatch.fnmatch(cname.lower(), pattern_lower):
            for e in entries:
                matches.append((cname, e))

    if not matches:
        print("  No results for '{}'.".format(pattern))
        return

    # Sort by name, then by module
    matches.sort(key=lambda x: (x[0].lower(), x[1]['module']))

    # Count by kind
    kinds = {}
    for _, e in matches:
        k = e['kind']
        kinds[k] = kinds.get(k, 0) + 1

    print("")
    print("  Search '{}': {} results".format(pattern, len(matches)))
    kind_parts = ["{}={}".format(k, v) for k, v in sorted(kinds.items())]
    if kind_parts:
        print("  ({})".format(", ".join(kind_parts)))
    print("")
    print("  {:>35s}  {:9s} {:>6s}  {:20s} {:s}".format(
        "CLASS", "KIND", "LINES", "MODULE", "PACKAGE"))
    print("  " + "-" * 100)

    shown = 0
    for cname, e in matches:
        if shown >= limit:
            break
        print(_format_class_row(cname, e))
        shown += 1

    if len(matches) > limit:
        print("")
        print("  ... and {} more (use -n to show more)".format(len(matches) - limit))

    print("")


def cmd_package(base_dir, name=None, show_all=False, limit=50):
    """List classes in a package, or list all packages."""
    data = load_class_index(base_dir)
    if not data:
        return

    classes = data["classes"]

    if show_all:
        # Collect all packages (top-level classes only)
        packages = {}
        for cname, entries in classes.items():
            for e in entries:
                if e['outer_class']:
                    continue
                pkg = e['package']
                if pkg not in packages:
                    packages[pkg] = 0
                packages[pkg] += 1

        print("")
        print("  All packages: {} unique".format(len(packages)))
        print("")
        print("  {:55s} {:>6s}".format("PACKAGE", "COUNT"))
        print("  " + "-" * 63)

        for pkg in sorted(packages.keys()):
            print("  {:55s} {:>6,}".format(pkg, packages[pkg]))

        print("")
        print("  Total: {} packages, {:,} top-level classes".format(
            len(packages),
            sum(packages.values())))
        print("")
        return

    if not name:
        print("  Usage: package <name> or package --all")
        return

    # Find classes in this exact package (top-level only)
    matches = []
    for cname, entries in classes.items():
        for e in entries:
            if e['package'] == name and not e['outer_class']:
                matches.append((cname, e))

    if not matches:
        # Try partial match (subpackages)
        partial = set()
        for cname, entries in classes.items():
            for e in entries:
                if e['package'] and e['package'].startswith(name) and not e['outer_class']:
                    partial.add(e['package'])

        if partial:
            print("")
            print("  No exact match for '{}'. Sub-packages:".format(name))
            for p in sorted(partial)[:30]:
                print("    {}".format(p))
            if len(partial) > 30:
                print("    ... and {} more".format(len(partial) - 30))
            print("")
        else:
            print("  Package '{}' not found.".format(name))
        return

    matches.sort(key=lambda x: x[0])

    print("")
    print("  Package {}: {} classes".format(name, len(matches)))
    print("")
    print("  {:>35s}  {:9s} {:>6s}  {:20s} {:s}".format(
        "CLASS", "KIND", "LINES", "MODULE", "INNER"))
    print("  " + "-" * 80)

    shown = 0
    for cname, e in matches:
        if shown >= limit:
            break
        inner_count = len(e.get('inner_classes', []))
        inner_str = str(inner_count) if inner_count > 0 else ""
        print("  {:>35s}  {:9s} {:>6,}  {:20s} {:s}".format(
            cname,
            e['kind'],
            e['lines'],
            e['module'],
            inner_str,
        ))
        shown += 1

    if len(matches) > limit:
        print("")
        print("  ... and {} more (use -n to show more)".format(len(matches) - limit))

    print("")
