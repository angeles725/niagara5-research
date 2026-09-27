#!/usr/bin/env python
"""
Build class-index.json from decompiled Java sources.

Scans all vineflower/ directories listed in module-inventory.json
and parses each .java file to extract:
  - Class/interface/enum name and kind
  - Package declaration
  - extends / implements
  - Modifiers (public, abstract, final, etc.)
  - Line count
  - Inner classes
  - Relative path from organized/

Source: /home/cristian/modules/Prototipos/modulos/organized/
Input:  indexes/module-inventory.json
Output: indexes/class-index.json

Requires: Python 3.x (stdlib only)
"""

import json
import os
import re
import sys
import time


ORGANIZED_DIR = r"/home/cristian/modules/Prototipos/modulos/organized"

# --- Regex patterns ---

PACKAGE_RE = re.compile(r'^package\s+([\w.]+)\s*;')

# Match: [indent][modifiers] class|interface|enum Name
DECL_RE = re.compile(
    r'^(\s*)'                                                        # grp 1: indent
    r'((?:(?:public|protected|private|static|abstract|final|strictfp)\s+)*)'  # grp 2: mods
    r'(class|interface|enum)\s+'                                     # grp 3: kind
    r'(\w+)'                                                         # grp 4: name
)


# --- Helpers ---

def split_type_list(s):
    """Split comma-separated types respecting <> nesting."""
    parts = []
    buf = []
    depth = 0
    for c in s:
        if c == '<':
            depth += 1
        elif c == '>':
            depth -= 1
        elif c == ',' and depth == 0:
            t = ''.join(buf).strip()
            if t:
                parts.append(t)
            buf = []
            continue
        buf.append(c)
    t = ''.join(buf).strip()
    if t:
        parts.append(t)
    return parts


def parse_extends_implements(text):
    """Extract extends and implements from text after class name (before {)."""
    brace = text.find('{')
    if brace >= 0:
        text = text[:brace]
    text = text.strip()

    # Skip leading type parameters <T, U extends ...>
    if text.startswith('<'):
        depth = 0
        for i, c in enumerate(text):
            if c == '<':
                depth += 1
            elif c == '>':
                depth -= 1
            if depth == 0:
                text = text[i + 1:].strip()
                break

    extends = None
    implements = []

    ext_m = re.search(r'\bextends\b\s+', text)
    impl_m = re.search(r'\bimplements\b\s+', text)

    if ext_m and impl_m:
        extends = text[ext_m.end():impl_m.start()].strip()
        implements = split_type_list(text[impl_m.end():])
    elif ext_m:
        extends = text[ext_m.end():].strip()
    elif impl_m:
        implements = split_type_list(text[impl_m.end():])

    if extends:
        extends = extends.rstrip(',').strip()
        if not extends:
            extends = None

    return extends, implements


# --- Core parsing ---

def parse_java_file(filepath):
    """Parse a .java file. Returns (declarations, line_count, package)."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception:
        return [], 0, ''

    line_count = len(lines)
    package = ''

    # Package is always near the top
    for line in lines[:30]:
        m = PACKAGE_RE.match(line.strip())
        if m:
            package = m.group(1)
            break

    declarations = []
    in_block_comment = False

    for line in lines:
        stripped = line.lstrip()

        # Track block comments
        if in_block_comment:
            if '*/' in stripped:
                in_block_comment = False
            continue
        if stripped.startswith('/*'):
            if '*/' not in stripped:
                in_block_comment = True
            continue
        if stripped.startswith('//') or stripped.startswith('*'):
            continue

        m = DECL_RE.match(line)
        if not m:
            continue

        indent = len(m.group(1))
        mods_str = m.group(2).strip()
        kind = m.group(3)
        name = m.group(4)
        modifiers = mods_str.split() if mods_str else []

        rest = line[m.end():]
        extends, implements = parse_extends_implements(rest)

        declarations.append({
            'indent': indent,
            'modifiers': modifiers,
            'kind': kind,
            'name': name,
            'extends': extends,
            'implements': implements,
        })

    return declarations, line_count, package


def process_file(filepath, rel_path, submod_name, is_zkm):
    """Process one .java file. Returns list of (class_name, entry_dict)."""
    declarations, line_count, package = parse_java_file(filepath)
    if not declarations:
        return []

    # First declaration at indent 0 is the outer class
    outer = None
    inner_classes = []
    for d in declarations:
        if outer is None and d['indent'] == 0:
            outer = d
        elif outer is not None:
            inner_classes.append(d)

    # Fallback: use first declaration if none at indent 0
    if outer is None:
        outer = declarations[0]
        inner_classes = declarations[1:]

    entries = []

    # Outer class entry
    entries.append((outer['name'], {
        'package': package,
        'module': submod_name,
        'kind': outer['kind'],
        'extends': outer['extends'],
        'implements': outer['implements'],
        'modifiers': outer['modifiers'],
        'lines': line_count,
        'path': rel_path,
        'zkm': is_zkm,
        'inner_classes': [ic['name'] for ic in inner_classes],
        'outer_class': None,
    }))

    # Inner class entries
    for ic in inner_classes:
        entries.append((ic['name'], {
            'package': package,
            'module': submod_name,
            'kind': ic['kind'],
            'extends': ic['extends'],
            'implements': ic['implements'],
            'modifiers': ic['modifiers'],
            'lines': 0,
            'path': rel_path,
            'zkm': is_zkm,
            'inner_classes': [],
            'outer_class': outer['name'],
        }))

    return entries


# --- Index builder ---

def build_class_index(base_dir, organized_dir, verbose=False):
    """Build class index from all vineflower directories."""
    inv_path = os.path.join(base_dir, "indexes", "module-inventory.json")
    if not os.path.isfile(inv_path):
        print("ERROR: module-inventory.json not found.")
        print("Run: python tools/build_module_inventory.py")
        sys.exit(1)

    with open(inv_path, "r", encoding="utf-8") as f:
        inv_data = json.load(f)

    modules = inv_data["modules"]
    classes = {}  # name -> list of entry dicts
    stats = {
        'files_processed': 0,
        'files_no_decl': 0,
        'top_classes': 0,
        'inner_classes': 0,
        'interfaces': 0,
        'enums': 0,
        'abstract': 0,
        'packages': set(),
    }

    submod_count = 0
    submod_with_vf = sum(1 for v in modules.values() if v.get("has_vineflower"))

    for submod_name, info in sorted(modules.items()):
        if not info.get("has_vineflower"):
            continue

        submod_count += 1
        module_name = info["module"]
        is_zkm = info.get("zkm", False)
        vf_dir = os.path.join(organized_dir, module_name, submod_name, "vineflower")

        if not os.path.isdir(vf_dir):
            continue

        if verbose and submod_count % 50 == 0:
            print("  ... {}/{} submodules ({})".format(
                submod_count, submod_with_vf, submod_name))

        for root, dirs, files in os.walk(vf_dir):
            for fname in files:
                if not fname.endswith(".java"):
                    continue

                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, organized_dir).replace("\\", "/")

                entries = process_file(fpath, rel, submod_name, is_zkm)

                stats['files_processed'] += 1

                if not entries:
                    stats['files_no_decl'] += 1
                    continue

                for cname, entry in entries:
                    pkg = entry['package']
                    if pkg:
                        stats['packages'].add(pkg)

                    is_inner = entry['outer_class'] is not None
                    if is_inner:
                        stats['inner_classes'] += 1
                    else:
                        stats['top_classes'] += 1
                        if entry['kind'] == 'interface':
                            stats['interfaces'] += 1
                        elif entry['kind'] == 'enum':
                            stats['enums'] += 1
                        if 'abstract' in entry['modifiers']:
                            stats['abstract'] += 1

                    if cname not in classes:
                        classes[cname] = []
                    classes[cname].append(entry)

    stats['packages'] = len(stats['packages'])
    return classes, stats


def print_summary(classes, stats, elapsed):
    """Print build summary."""
    total_entries = sum(len(v) for v in classes.values())
    unique = len(classes)
    dupes = sum(1 for v in classes.values() if len(v) > 1)

    print("=" * 60)
    print("CLASS INDEX SUMMARY")
    print("=" * 60)
    print("")
    print("  Files processed:     {:>8,}".format(stats['files_processed']))
    print("  No declaration:      {:>8,}".format(stats['files_no_decl']))
    print("")
    print("  Top-level classes:   {:>8,}".format(stats['top_classes']))
    print("  Inner classes:       {:>8,}".format(stats['inner_classes']))
    print("  Total entries:       {:>8,}".format(total_entries))
    print("  Unique names:        {:>8,}".format(unique))
    print("  Duplicate names:     {:>8,}".format(dupes))
    print("")
    print("  Interfaces:          {:>8,}".format(stats['interfaces']))
    print("  Enums:               {:>8,}".format(stats['enums']))
    print("  Abstract classes:    {:>8,}".format(stats['abstract']))
    print("  Unique packages:     {:>8,}".format(stats['packages']))
    print("")
    print("  Build time:          {:>8.1f}s".format(elapsed))
    print("")

    # Top 10 most duplicated names
    duped = [(k, len(v)) for k, v in classes.items() if len(v) > 1]
    if duped:
        duped.sort(key=lambda x: -x[1])
        print("  Top 10 duplicated class names:")
        for name, count in duped[:10]:
            print("    {:40s} {:>4} entries".format(name, count))
        print("")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    indexes_dir = os.path.join(base_dir, "indexes")

    organized_dir = ORGANIZED_DIR
    if not os.path.isdir(organized_dir):
        print("ERROR: organized directory not found: {}".format(organized_dir))
        sys.exit(1)

    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("Building class index from: {}".format(organized_dir))
    print("")

    t0 = time.time()
    classes, stats = build_class_index(base_dir, organized_dir, verbose=verbose)
    elapsed = time.time() - t0

    print_summary(classes, stats, elapsed)

    # Write index
    os.makedirs(indexes_dir, exist_ok=True)
    out_path = os.path.join(indexes_dir, "class-index.json")

    total_entries = sum(len(v) for v in classes.values())

    output = {
        "_meta": {
            "description": "Class index for Niagara N4 decompiled modules",
            "source": organized_dir,
            "files_processed": stats['files_processed'],
            "top_classes": stats['top_classes'],
            "inner_classes": stats['inner_classes'],
            "total_entries": total_entries,
            "unique_names": len(classes),
            "interfaces": stats['interfaces'],
            "enums": stats['enums'],
            "abstract": stats['abstract'],
            "unique_packages": stats['packages'],
            "build_time_sec": round(elapsed, 1),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "classes": classes,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print("  Written: {} ({:.1f} MB)".format(out_path, size_mb))
    print("")


if __name__ == "__main__":
    main()
