#!/usr/bin/env python
"""
Build cross-reference (xref) index from decompiled Java sources.

Reads class-index.json as a catalog of all top-level .java files,
parses import statements from each file, and produces indexes/xref-index.json
with four maps:

  class_imports:       { "BLinkPad": ["BEdgePane", "BComponent", ...] }
  class_imported_by:   { "BEdgePane": ["BLinkPad", "BConstrainedPane", ...] }
  module_deps:         { "workbench-wb": ["bajaui-wb", "baja", ...] }
  module_depended_by:  { "baja": ["workbench-wb", "alarm-rt", ...] }

Resolves wildcard imports (import pkg.*) using the package index from
class-index.json. Ignores java.* and javax.* EXCEPT javax.baja.* (Niagara).

Usage:
  python tools/build_xref.py [--base-dir DIR]
"""

import json
import os
import re
import sys
import time


# Regex for import statements
RE_IMPORT = re.compile(r'^\s*import\s+(static\s+)?([\w.]+(?:\.\*)?)\s*;', re.MULTILINE)


def detect_base_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(script_dir)
    if os.path.isdir(os.path.join(base, "indexes")):
        return base
    return None


def build_xref(base_dir):
    ci_path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(ci_path):
        print("ERROR: class-index.json not found at {}".format(ci_path))
        sys.exit(1)

    inv_path = os.path.join(base_dir, "indexes", "module-inventory.json")
    if not os.path.isfile(inv_path):
        print("ERROR: module-inventory.json not found at {}".format(inv_path))
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Load indexes
    # -------------------------------------------------------------------------
    print("Loading class-index.json...")
    t0 = time.time()
    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = json.load(f)
    classes = ci_data.get("classes", {})
    ci_meta = ci_data.get("_meta", {})
    t_load = time.time() - t0
    print("  Loaded in {:.1f}s ({} unique names)".format(t_load, len(classes)))

    print("Loading module-inventory.json...")
    with open(inv_path, "r", encoding="utf-8") as f:
        inv_data = json.load(f)
    source_base = inv_data.get("_meta", {}).get("source", "")
    print("  Source base: {}".format(source_base))

    # -------------------------------------------------------------------------
    # Build package -> [class_names] map (top-level only)
    # Also build fqcn -> (class_name, module) map for import resolution
    # -------------------------------------------------------------------------
    print("Building package index for wildcard resolution...")
    t1 = time.time()

    package_classes = {}   # "com.tridium.workbench.util" -> ["BLinkPad", "BEditorPane", ...]
    fqcn_to_info = {}      # "com.tridium.workbench.util.BLinkPad" -> ("BLinkPad", "workbench-wb")
    class_to_module = {}   # "BLinkPad" -> set("workbench-wb")

    # Collect all top-level entries and build lookup structures
    top_level_files = []   # (class_name, entry) for files to parse

    for class_name, entries in classes.items():
        for e in entries:
            if e.get("outer_class"):
                continue

            pkg = e.get("package", "")
            module = e.get("module", "")

            # Build package -> classes map
            if pkg:
                if pkg not in package_classes:
                    package_classes[pkg] = []
                if class_name not in package_classes[pkg]:
                    package_classes[pkg].append(class_name)

            # Build FQCN -> info map
            if pkg:
                fqcn = pkg + "." + class_name
            else:
                fqcn = class_name
            fqcn_to_info[fqcn] = (class_name, module)

            # Build class -> modules map
            if class_name not in class_to_module:
                class_to_module[class_name] = set()
            class_to_module[class_name].add(module)

            # Collect files to parse (deduplicate by path)
            top_level_files.append((class_name, e))

    t2 = time.time()
    print("  Built in {:.1f}s: {} packages, {} FQCNs, {} files to parse".format(
        t2 - t1, len(package_classes), len(fqcn_to_info), len(top_level_files)))

    # -------------------------------------------------------------------------
    # Parse imports from each .java file
    # -------------------------------------------------------------------------
    print("Parsing imports from {} files...".format(len(top_level_files)))
    t3 = time.time()

    class_imports = {}      # class_name -> set of imported class names
    files_parsed = 0
    files_failed = 0
    total_import_stmts = 0
    wildcard_imports = 0
    wildcard_resolved = 0
    skipped_stdlib = 0
    resolved_imports = 0

    progress_interval = 5000

    for class_name, entry in top_level_files:
        rel_path = entry.get("path", "")
        if not rel_path:
            continue

        full_path = os.path.join(source_base, rel_path)
        if not os.path.isfile(full_path):
            files_failed += 1
            continue

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            files_failed += 1
            continue

        files_parsed += 1
        if files_parsed % progress_interval == 0:
            elapsed = time.time() - t3
            rate = files_parsed / elapsed if elapsed > 0 else 0
            print("  {:>6,} / {:,} files ({:.0f}/s)...".format(
                files_parsed, len(top_level_files), rate))

        # Extract imports (only from the top of the file, before class declaration)
        # Optimization: only scan first ~150 lines (imports are always at top)
        lines = content.split("\n", 200)
        header = "\n".join(lines[:200])

        imported_classes = set()
        source_module = entry.get("module", "")

        for match in RE_IMPORT.finditer(header):
            is_static = bool(match.group(1))
            import_path = match.group(2)
            total_import_stmts += 1

            # Skip java.* stdlib (but keep javax.baja.*)
            if import_path.startswith("java.") or import_path.startswith("javax."):
                if not import_path.startswith("javax.baja."):
                    skipped_stdlib += 1
                    continue

            if import_path.endswith(".*"):
                # Wildcard import: resolve to all classes in that package
                wildcard_imports += 1
                pkg = import_path[:-2]
                if pkg in package_classes:
                    for cls in package_classes[pkg]:
                        imported_classes.add(cls)
                        wildcard_resolved += 1
            else:
                # Explicit import: extract class name
                # For static imports like "import static com.foo.Bar.FIELD",
                # the class is the second-to-last component
                parts = import_path.split(".")
                if is_static and len(parts) >= 2:
                    # Try FQCN without last part (field/method name)
                    candidate_fqcn = ".".join(parts[:-1])
                    if candidate_fqcn in fqcn_to_info:
                        cls_name = fqcn_to_info[candidate_fqcn][0]
                        imported_classes.add(cls_name)
                        resolved_imports += 1
                    else:
                        # Last part might be the class name
                        cls_name = parts[-2] if len(parts) >= 2 else parts[-1]
                        if cls_name in class_to_module:
                            imported_classes.add(cls_name)
                            resolved_imports += 1
                else:
                    # Regular import
                    if import_path in fqcn_to_info:
                        cls_name = fqcn_to_info[import_path][0]
                        imported_classes.add(cls_name)
                        resolved_imports += 1
                    else:
                        # Fallback: use last component as class name
                        cls_name = parts[-1]
                        if cls_name in class_to_module:
                            imported_classes.add(cls_name)
                            resolved_imports += 1

        # Remove self-import
        imported_classes.discard(class_name)

        if imported_classes:
            if class_name not in class_imports:
                class_imports[class_name] = set()
            class_imports[class_name].update(imported_classes)

    t4 = time.time()
    parse_time = t4 - t3
    print("  Parsed {} files in {:.1f}s ({:.0f}/s)".format(
        files_parsed, parse_time, files_parsed / parse_time if parse_time > 0 else 0))
    print("  Failed to read: {}".format(files_failed))
    print("  Total import statements: {:,}".format(total_import_stmts))
    print("  Skipped stdlib: {:,}".format(skipped_stdlib))
    print("  Resolved imports: {:,}".format(resolved_imports))
    print("  Wildcard imports: {:,} ({:,} classes resolved)".format(
        wildcard_imports, wildcard_resolved))
    print("  Classes with imports: {:,}".format(len(class_imports)))

    # -------------------------------------------------------------------------
    # Build reverse map: class_imported_by
    # -------------------------------------------------------------------------
    print("Building reverse xref (class_imported_by)...")
    t5 = time.time()

    class_imported_by = {}
    for importer, importees in class_imports.items():
        for importee in importees:
            if importee not in class_imported_by:
                class_imported_by[importee] = set()
            class_imported_by[importee].add(importer)

    t6 = time.time()
    print("  Built in {:.1f}s: {:,} classes referenced by others".format(
        t6 - t5, len(class_imported_by)))

    # -------------------------------------------------------------------------
    # Build module-level dependency maps
    # -------------------------------------------------------------------------
    print("Building module dependency maps...")
    t7 = time.time()

    module_deps = {}         # module -> set of modules it depends on
    module_depended_by = {}  # module -> set of modules that depend on it

    for importer_class, importees in class_imports.items():
        # Get modules of the importer
        importer_modules = class_to_module.get(importer_class, set())

        for importee in importees:
            importee_modules = class_to_module.get(importee, set())

            for imp_mod in importer_modules:
                for dep_mod in importee_modules:
                    if imp_mod == dep_mod:
                        continue  # Skip self-dependency

                    # Forward: imp_mod depends on dep_mod
                    if imp_mod not in module_deps:
                        module_deps[imp_mod] = set()
                    module_deps[imp_mod].add(dep_mod)

                    # Reverse: dep_mod is depended on by imp_mod
                    if dep_mod not in module_depended_by:
                        module_depended_by[dep_mod] = set()
                    module_depended_by[dep_mod].add(imp_mod)

    t8 = time.time()
    print("  Built in {:.1f}s: {:,} modules with deps, {:,} modules depended on".format(
        t8 - t7, len(module_deps), len(module_depended_by)))

    # -------------------------------------------------------------------------
    # Convert sets to sorted lists for JSON serialization
    # -------------------------------------------------------------------------
    print("Serializing...")

    class_imports_out = {}
    for k, v in class_imports.items():
        class_imports_out[k] = sorted(v)

    class_imported_by_out = {}
    for k, v in class_imported_by.items():
        class_imported_by_out[k] = sorted(v)

    module_deps_out = {}
    for k, v in module_deps.items():
        module_deps_out[k] = sorted(v)

    module_depended_by_out = {}
    for k, v in module_depended_by.items():
        module_depended_by_out[k] = sorted(v)

    # -------------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------------
    # Top imported classes
    top_imported = sorted(class_imported_by.items(),
                          key=lambda x: len(x[1]), reverse=True)[:20]

    # Top module dependencies
    top_mod_deps = sorted(module_depended_by.items(),
                          key=lambda x: len(x[1]), reverse=True)[:20]

    # Import count distribution
    import_counts = [len(v) for v in class_imports.values()]
    max_imports = max(import_counts) if import_counts else 0
    avg_imports = sum(import_counts) / len(import_counts) if import_counts else 0

    importee_counts = [len(v) for v in class_imported_by.values()]
    max_importers = max(importee_counts) if importee_counts else 0

    print("")
    print("  Top 10 most-imported classes:")
    for name, importers in top_imported[:10]:
        print("    {:40s} {:>5,} importers".format(name, len(importers)))

    print("")
    print("  Top 10 most-depended-on modules:")
    for name, dependents in top_mod_deps[:10]:
        print("    {:40s} {:>5,} dependents".format(name, len(dependents)))

    # -------------------------------------------------------------------------
    # Build output
    # -------------------------------------------------------------------------
    total_time = time.time() - t0
    meta = {
        "description": "Cross-reference (import) index for Niagara N4 decompiled modules",
        "source_index": "class-index.json",
        "files_parsed": files_parsed,
        "files_failed": files_failed,
        "total_import_statements": total_import_stmts,
        "skipped_stdlib": skipped_stdlib,
        "resolved_imports": resolved_imports,
        "wildcard_imports": wildcard_imports,
        "wildcard_classes_resolved": wildcard_resolved,
        "classes_with_imports": len(class_imports),
        "classes_imported_by_others": len(class_imported_by),
        "modules_with_deps": len(module_deps),
        "modules_depended_on": len(module_depended_by),
        "max_imports_per_class": max_imports,
        "avg_imports_per_class": round(avg_imports, 1),
        "max_importers_per_class": max_importers,
        "total_class_import_edges": sum(len(v) for v in class_imports.values()),
        "total_module_dep_edges": sum(len(v) for v in module_deps.values()),
        "build_time_sec": round(total_time, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    output = {
        "_meta": meta,
        "class_imports": class_imports_out,
        "class_imported_by": class_imported_by_out,
        "module_deps": module_deps_out,
        "module_depended_by": module_depended_by_out,
    }

    # Write
    out_path = os.path.join(base_dir, "indexes", "xref-index.json")
    print("")
    print("Writing {}...".format(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"), ensure_ascii=False)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print("  Done: {:.1f} MB in {:.1f}s".format(size_mb, total_time))
    print("")

    # Summary
    print("=" * 60)
    print("XREF INDEX SUMMARY")
    print("=" * 60)
    print("  Files parsed:                {:>7,}".format(files_parsed))
    print("  Import statements:           {:>7,}".format(total_import_stmts))
    print("  Resolved imports:            {:>7,}".format(resolved_imports))
    print("  Wildcard imports:            {:>7,}".format(wildcard_imports))
    print("  Wildcard classes resolved:   {:>7,}".format(wildcard_resolved))
    print("  Skipped stdlib:              {:>7,}".format(skipped_stdlib))
    print("  Classes with imports:        {:>7,}".format(len(class_imports)))
    print("  Classes imported by others:  {:>7,}".format(len(class_imported_by)))
    print("  Total class import edges:    {:>7,}".format(
        sum(len(v) for v in class_imports.values())))
    print("  Modules with dependencies:   {:>7,}".format(len(module_deps)))
    print("  Modules depended on:         {:>7,}".format(len(module_depended_by)))
    print("  Total module dep edges:      {:>7,}".format(
        sum(len(v) for v in module_deps.values())))
    print("  Max imports per class:       {:>7,}".format(max_imports))
    print("  Avg imports per class:       {:>7.1f}".format(avg_imports))
    print("  Max importers per class:     {:>7,}".format(max_importers))
    print("  Index size:                  {:>6.1f} MB".format(size_mb))
    print("  Build time:                  {:>6.1f}s".format(total_time))
    print("")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build cross-reference (xref) index")
    parser.add_argument("--base-dir", "-d", help="Base directory")
    args = parser.parse_args()

    base_dir = args.base_dir or detect_base_dir()
    if not base_dir:
        print("ERROR: Cannot detect base directory.")
        sys.exit(1)

    build_xref(base_dir)
