"""
Analysis commands for Module Navigator (Phase 11).

Commands using EXISTING indexes (no new index build):
  orphans          Classes never imported by any other class (dead code)
  deps-graph       Module dependency graph in Mermaid/DOT format
  api-surface      Public API surface of a module
  security-audit   Scan for insecure patterns in source code
"""

import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_json(base_dir, filename):
    """Load a JSON index file."""
    path = os.path.join(base_dir, "indexes", filename)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_source_root(ci_data):
    return ci_data.get("_meta", {}).get("source", "")


def _read_source(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except (IOError, OSError):
        return []


# ---------------------------------------------------------------------------
# orphans: dead code detection
# ---------------------------------------------------------------------------

def cmd_orphans(base_dir, module_filter=None, type_filter=None, limit=50):
    """Find classes that are never imported by any other class."""
    ci_data = _load_json(base_dir, "class-index.json")
    xr_data = _load_json(base_dir, "xref-index.json")
    inv_data = _load_json(base_dir, "module-inventory.json")

    if not ci_data or not xr_data:
        print("ERROR: class-index.json and xref-index.json required.")
        return

    classes = ci_data.get("classes", {})
    imported_by = xr_data.get("class_imported_by", {})
    inv = inv_data.get("modules", {}) if inv_data else {}

    # Build set of all imported FQNs
    imported_set = set(imported_by.keys())

    # Build type filter set if needed
    type_set = None
    if type_filter and inv:
        type_set = set(k for k, v in inv.items() if v.get("type") == type_filter)

    orphans = []
    for class_name, entries in classes.items():
        for entry in entries:
            if entry.get("outer_class") is not None:
                continue
            if entry.get("zkm"):
                continue
            if module_filter and entry["module"] != module_filter:
                continue
            if type_set and entry["module"] not in type_set:
                continue

            # Build FQN
            pkg = entry.get("package", "")
            fqn = "{}.{}".format(pkg, class_name) if pkg else class_name

            if fqn not in imported_set:
                orphans.append((class_name, entry))

    # Sort by module then name
    orphans.sort(key=lambda x: (x[1]["module"], x[0]))

    print("")
    print("  " + "=" * 65)
    print("  ORPHAN CLASSES (never imported)")
    if module_filter:
        print("  Module: {}".format(module_filter))
    if type_filter:
        print("  Type: {}".format(type_filter))
    print("  " + "=" * 65)
    print("")
    print("  Total orphans: {:,}".format(len(orphans)))
    print("  (Note: may be used via reflection, Niagara type system, or bajadoc)")
    print("")

    shown = orphans[:limit]
    current_module = None
    for class_name, entry in shown:
        if entry["module"] != current_module:
            current_module = entry["module"]
            print("  --- {} ---".format(current_module))
        print("    {:40s} {:>5} lines  {}".format(
            class_name, entry.get("lines", 0), entry.get("package", "")))

    if len(orphans) > limit:
        print("")
        print("  ... and {:,} more (use -n to show more)".format(len(orphans) - limit))
    print("")


# ---------------------------------------------------------------------------
# deps-graph: module dependency graph visualization
# ---------------------------------------------------------------------------

def cmd_deps_graph(base_dir, module_name, depth=1, fmt="mermaid", reverse=False):
    """Generate module dependency graph in Mermaid or DOT format."""
    xr_data = _load_json(base_dir, "xref-index.json")
    if not xr_data:
        print("ERROR: xref-index.json not found.")
        return

    if reverse:
        dep_map = xr_data.get("module_depended_by", {})
        direction = "dependents"
    else:
        dep_map = xr_data.get("module_deps", {})
        direction = "dependencies"

    if module_name not in dep_map:
        print("  Module '{}' not found in {} map.".format(module_name, direction))
        return

    # BFS to collect edges up to depth
    edges = []
    visited = set()
    queue = [(module_name, 0)]
    visited.add(module_name)

    while queue:
        node, d = queue.pop(0)
        if d >= depth:
            continue
        deps = dep_map.get(node, [])
        if isinstance(deps, list):
            for dep in deps:
                edges.append((node, dep))
                if dep not in visited:
                    visited.add(dep)
                    queue.append((dep, d + 1))

    if not edges:
        print("  No {} found for '{}'.".format(direction, module_name))
        return

    # Sanitize node names for graph formats (replace hyphens)
    def safe(name):
        return name.replace("-", "_").replace(".", "_")

    print("")
    if fmt == "mermaid":
        print("  " + "=" * 65)
        arrow = " --> " if not reverse else " <-- "
        label = "DEPENDENCIES" if not reverse else "DEPENDENTS"
        print("  {} GRAPH: {} (depth {})".format(label, module_name, depth))
        print("  " + "=" * 65)
        print("")
        print("```mermaid")
        print("graph LR")
        for src, dst in edges:
            print("  {}[\"{}\"] --> {}[\"{}\"]".format(safe(src), src, safe(dst), dst))
        print("```")
    elif fmt == "dot":
        print("  " + "=" * 65)
        label = "DEPENDENCIES" if not reverse else "DEPENDENTS"
        print("  {} GRAPH: {} (depth {})".format(label, module_name, depth))
        print("  " + "=" * 65)
        print("")
        print("digraph {} {{".format(safe(module_name)))
        print("  rankdir=LR;")
        print('  node [shape=box, fontsize=10];')
        print('  "{}" [style=filled, fillcolor=lightblue];'.format(module_name))
        for src, dst in edges:
            print('  "{}" -> "{}";'.format(src, dst))
        print("}")
    else:
        print("  " + "=" * 65)
        label = "DEPENDENCIES" if not reverse else "DEPENDENTS"
        print("  {} OF: {} (depth {})".format(label, module_name, depth))
        print("  " + "=" * 65)
        print("")
        print("  Nodes: {:,}  Edges: {:,}".format(len(visited), len(edges)))
        print("")
        # Group by source
        from_map = {}
        for src, dst in edges:
            from_map.setdefault(src, []).append(dst)
        for src in sorted(from_map.keys()):
            dsts = sorted(from_map[src])
            print("  {} ({})".format(src, len(dsts)))
            for d in dsts[:10]:
                print("    -> {}".format(d))
            if len(dsts) > 10:
                print("    ... and {} more".format(len(dsts) - 10))

    print("")
    print("  Nodes: {:,}  Edges: {:,}".format(len(visited), len(edges)))
    print("")


# ---------------------------------------------------------------------------
# api-surface: public API summary of a module
# ---------------------------------------------------------------------------

def cmd_api_surface(base_dir, module_name, limit=50):
    """Show the public API surface of a module: types, methods, actions, servlets."""
    ci_data = _load_json(base_dir, "class-index.json")
    ann_data = _load_json(base_dir, "annotations-index.json")
    mi_data = _load_json(base_dir, "method-index.json")

    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    classes = ci_data.get("classes", {})

    # Collect public classes in this module
    public_classes = []
    for class_name, entries in classes.items():
        for entry in entries:
            if entry.get("outer_class") is not None:
                continue
            if entry["module"] != module_name:
                continue
            if "public" in entry.get("modifiers", []):
                public_classes.append((class_name, entry))

    if not public_classes:
        print("  No public classes found in module '{}'.".format(module_name))
        print("  Try: modules --has-code")
        return

    public_classes.sort(key=lambda x: x[0])

    print("")
    print("  " + "=" * 65)
    print("  API SURFACE: {}".format(module_name))
    print("  " + "=" * 65)

    # Summary counts
    niagara_types = 0
    total_properties = 0
    total_actions = 0
    servlets = []
    services = []
    components = []

    ann_types = ann_data.get("niagara_types", {}) if ann_data else {}

    for class_name, entry in public_classes:
        ext = entry.get("extends", "")
        if "Servlet" in (ext or "") or "Servlet" in class_name:
            servlets.append(class_name)
        if "Service" in (ext or "") or "Service" in class_name:
            services.append(class_name)
        if ext and ext.startswith("B"):
            components.append(class_name)

        # Check annotations
        if class_name in ann_types:
            niagara_types += 1
            ann_entry = ann_types[class_name]
            if isinstance(ann_entry, list):
                ann_entry = ann_entry[0]
            total_properties += len(ann_entry.get("properties", []))
            total_actions += len(ann_entry.get("actions", []))

    print("")
    print("  SUMMARY:")
    print("    Public classes:     {:>5}".format(len(public_classes)))
    print("    Niagara types:     {:>5}".format(niagara_types))
    print("    Total properties:  {:>5}".format(total_properties))
    print("    Total actions:     {:>5}".format(total_actions))
    print("    Services:          {:>5}  ({})".format(
        len(services), ", ".join(services[:5]) if services else "-"))
    print("    Servlets:          {:>5}  ({})".format(
        len(servlets), ", ".join(servlets[:5]) if servlets else "-"))

    # List public classes with details
    print("")
    print("  PUBLIC CLASSES ({})".format(min(limit, len(public_classes))))
    print("  " + "-" * 65)

    for class_name, entry in public_classes[:limit]:
        kind = entry["kind"]
        ext = entry.get("extends", "")
        mods = " ".join(entry.get("modifiers", []))

        tags = []
        if class_name in ann_types:
            ann_entry = ann_types[class_name]
            if isinstance(ann_entry, list):
                ann_entry = ann_entry[0]
            props = ann_entry.get("properties", [])
            acts = ann_entry.get("actions", [])
            if props:
                tags.append("{}p".format(len(props)))
            if acts:
                tags.append("{}a".format(len(acts)))

        tag_str = " [{}]".format(",".join(tags)) if tags else ""
        print("    {:40s} {:>9} {:>5}L{}".format(
            class_name, kind, entry.get("lines", 0), tag_str))

    if len(public_classes) > limit:
        print("    ... and {} more".format(len(public_classes) - limit))

    # Show methods for top classes (if method-index available)
    if mi_data and public_classes:
        methods_map = mi_data.get("methods", {})
        print("")
        print("  PUBLIC METHODS (top 5 classes):")
        print("  " + "-" * 65)
        for class_name, entry in public_classes[:5]:
            pub_methods = []
            for mname, defs in methods_map.items():
                if mname == "<init>":
                    continue
                for d in defs:
                    if isinstance(d, dict) and d.get("class") == class_name and d.get("module") == module_name:
                        if "public" in d.get("modifiers", []):
                            pub_methods.append(mname)
                            break
                    elif isinstance(d, str) and d == class_name:
                        pub_methods.append(mname)
                        break
            if pub_methods:
                print("    {} ({} public)".format(class_name, len(pub_methods)))
                for m in sorted(pub_methods)[:8]:
                    print("      {}()".format(m))
                if len(pub_methods) > 8:
                    print("      ... and {} more".format(len(pub_methods) - 8))

    print("")


# ---------------------------------------------------------------------------
# security-audit: scan for insecure patterns
# ---------------------------------------------------------------------------

_SECURITY_PATTERNS = [
    ("HARDCODED_PASSWORD", re.compile(
        r'(?:password|passwd|secret|apiKey|api_key)\s*=\s*"[^"]+"|'
        r'(?:password|passwd|secret|apiKey|api_key)\s*=\s*\'[^\']+\'',
        re.IGNORECASE)),
    ("PLAINTEXT_HTTP", re.compile(
        r'"http://[^"]*"')),
    ("COMMAND_EXEC", re.compile(
        r'Runtime\.getRuntime\(\)\.exec\(|'
        r'ProcessBuilder\s*\(|'
        r'Process\s+\w+\s*=',
        re.IGNORECASE)),
    ("WEAK_CRYPTO", re.compile(
        r'MessageDigest\.getInstance\(\s*"(?:MD5|SHA-1|SHA1|DES)"\)|'
        r'Cipher\.getInstance\(\s*"DES',
        re.IGNORECASE)),
    ("HARDCODED_IP", re.compile(
        r'"(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?"')),
    ("TEMP_FILE", re.compile(
        r'File\.createTempFile\(|'
        r'"(?:/tmp/|C:\\\\[Tt]emp\\\\)[^"]*"')),
    ("DESERIALIZATION", re.compile(
        r'ObjectInputStream\s*\(|'
        r'\.readObject\(\s*\)')),
    ("SQL_CONCAT", re.compile(
        r'(?:SELECT|INSERT|UPDATE|DELETE)\s+.*"\s*\+\s*\w+',
        re.IGNORECASE)),
    ("HARDCODED_PORT", re.compile(
        r'(?:port|PORT)\s*=\s*(?:4911|1911|3011|443[0-9]|80[0-9]{2})\b')),
]


def cmd_security_audit(base_dir, module_filter=None, limit=30):
    """Scan source files for insecure patterns."""
    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    source_root = _get_source_root(ci_data)
    if not source_root:
        print("ERROR: source root not found in class-index metadata.")
        return

    classes = ci_data.get("classes", {})
    inv_data = _load_json(base_dir, "module-inventory.json")
    inv = inv_data.get("modules", {}) if inv_data else {}

    print("")
    print("  " + "=" * 65)
    print("  SECURITY AUDIT")
    if module_filter:
        print("  Module: {}".format(module_filter))
    else:
        print("  Scope: ALL modules with code")
    print("  " + "=" * 65)
    print("")

    findings = {}  # category -> [(class, module, line_no, line)]
    files_scanned = 0

    sys.stdout.write("  Scanning...")
    sys.stdout.flush()

    for class_name, entries in classes.items():
        for entry in entries:
            if entry.get("outer_class") is not None:
                continue
            if entry.get("zkm"):
                continue
            if module_filter and entry["module"] != module_filter:
                continue

            filepath = os.path.join(source_root, entry["path"])
            if not os.path.isfile(filepath):
                continue

            lines = _read_source(filepath)
            files_scanned += 1

            for i, line in enumerate(lines, 1):
                for category, pattern in _SECURITY_PATTERNS:
                    if pattern.search(line):
                        if category not in findings:
                            findings[category] = []
                        stripped = line.strip()
                        if len(stripped) > 100:
                            stripped = stripped[:97] + "..."
                        findings[category].append(
                            (class_name, entry["module"], i, stripped))
                        break  # one finding per line

    print(" done ({:,} files)".format(files_scanned))
    print("")

    total_findings = sum(len(v) for v in findings.values())
    print("  FINDINGS: {:,} total in {:,} categories".format(
        total_findings, len(findings)))
    print("")

    for category in sorted(findings.keys()):
        items = findings[category]
        print("  [{}] ({} findings)".format(category, len(items)))
        for cls, mod, line_no, line in items[:limit]:
            print("    {}:{} ({})".format(cls, line_no, mod))
            print("      {}".format(line))
        if len(items) > limit:
            print("    ... and {} more".format(len(items) - limit))
        print("")

    if not findings:
        print("  No security issues found.")
    print("")
