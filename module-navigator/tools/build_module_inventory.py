#!/usr/bin/env python
"""
Build module-inventory.json from pipeline/fase1-recon.json files.

Scans organized/{module}/{submodule}/pipeline/fase1-recon.json for each
submodule and counts .java files in vineflower/ directories.  Extracts
package names and identifies third-party packages.

Source: /home/cristian/modules/Prototipos/modulos/organized/
Output: indexes/module-inventory.json

Requires: Python 3.x (stdlib only)
"""

import json
import os
import sys
import time


# Niagara/Honeywell package prefixes (not third-party)
NIAGARA_PREFIXES = (
    "javax.baja",
    "com.tridium",
    "com.honeywell",
    "com.vykon",
    "com.niagara",
)

# Known submodule type suffixes
TYPE_SUFFIXES = ("rt", "wb", "ux", "doc", "se")


def detect_type(module_name, submodule_name):
    """Derive submodule type from its name suffix."""
    if submodule_name == module_name:
        return ""  # standalone
    for suffix in TYPE_SUFFIXES:
        if submodule_name.endswith("-" + suffix):
            return suffix
    return ""


def scan_packages(vineflower_dir):
    """Walk vineflower/ and collect top-level package names + third-party."""
    packages = set()
    third_party = set()

    if not os.path.isdir(vineflower_dir):
        return [], []

    for root, dirs, files in os.walk(vineflower_dir):
        for f in files:
            if not f.endswith(".java"):
                continue
            rel = os.path.relpath(root, vineflower_dir).replace("\\", "/")
            if rel == ".":
                continue
            pkg = rel.replace("/", ".")

            # Top-level package (first two segments)
            parts = pkg.split(".")
            if len(parts) >= 2:
                top = parts[0] + "." + parts[1]
            else:
                top = parts[0]

            packages.add(top)

            # Classify as third-party or niagara
            is_niagara = False
            for prefix in NIAGARA_PREFIXES:
                if pkg.startswith(prefix):
                    is_niagara = True
                    break
            if not is_niagara and len(parts) >= 2:
                third_party.add(top)

    return sorted(packages), sorted(third_party)


def count_java_files(vineflower_dir):
    """Count .java files in vineflower/ directory."""
    if not os.path.isdir(vineflower_dir):
        return 0
    count = 0
    for root, dirs, files in os.walk(vineflower_dir):
        for f in files:
            if f.endswith(".java"):
                count += 1
    return count


def build_inventory(organized_dir, verbose=False):
    """Build inventory dict from organized/ directory."""
    inventory = {}
    skipped = []

    modules = sorted(os.listdir(organized_dir))
    total = 0

    for module_name in modules:
        module_path = os.path.join(organized_dir, module_name)
        if not os.path.isdir(module_path):
            continue

        for submodule_name in sorted(os.listdir(module_path)):
            submodule_path = os.path.join(module_path, submodule_name)
            if not os.path.isdir(submodule_path):
                continue

            recon_path = os.path.join(submodule_path, "pipeline", "fase1-recon.json")
            if not os.path.isfile(recon_path):
                skipped.append(submodule_name)
                continue

            total += 1

            # Read recon JSON (may have BOM)
            with open(recon_path, "r", encoding="utf-8-sig") as f:
                try:
                    recon = json.load(f)
                except json.JSONDecodeError as e:
                    if verbose:
                        print("  WARN: bad JSON in {}: {}".format(recon_path, e))
                    skipped.append(submodule_name)
                    continue

            vineflower_dir = os.path.join(submodule_path, "vineflower")
            has_vineflower = os.path.isdir(vineflower_dir)
            has_cfr = os.path.isdir(os.path.join(submodule_path, "decompiled"))

            java_files = count_java_files(vineflower_dir)
            packages, third_party = scan_packages(vineflower_dir)

            sub_type = detect_type(module_name, submodule_name)

            entry = {
                "module": module_name,
                "type": sub_type,
                "jar": submodule_name + ".jar",
                "class_count": recon.get("class_count", 0),
                "java_files": java_files,
                "zkm": bool(recon.get("ofuscador_detectado", False)),
                "bytecode": recon.get("bytecode_major_version", 0),
                "has_vineflower": has_vineflower,
                "has_cfr": has_cfr,
                "has_code": bool(recon.get("tiene_codigo_java", False)),
                "packages": packages,
                "third_party": third_party,
            }

            inventory[submodule_name] = entry

            if verbose and total % 100 == 0:
                print("  ... processed {} submodules".format(total))

    return inventory, skipped


def print_summary(inventory):
    """Print summary statistics."""
    total = len(inventory)
    with_code = sum(1 for v in inventory.values() if v["has_code"])
    without_code = total - with_code
    total_java = sum(v["java_files"] for v in inventory.values())
    total_classes = sum(v["class_count"] for v in inventory.values())
    zkm_count = sum(1 for v in inventory.values() if v["zkm"])
    with_vineflower = sum(1 for v in inventory.values() if v["has_vineflower"])

    # Type breakdown
    types = {}
    for v in inventory.values():
        t = v["type"] if v["type"] else "standalone"
        types[t] = types.get(t, 0) + 1

    # Bytecode breakdown
    bytecodes = {}
    for v in inventory.values():
        bc = v["bytecode"] or 0
        if bc > 0:
            bytecodes[bc] = bytecodes.get(bc, 0) + 1

    # Module count (unique top-level)
    modules = set(v["module"] for v in inventory.values())

    print("=" * 60)
    print("MODULE INVENTORY SUMMARY")
    print("=" * 60)
    print("")
    print("  Total submodules (JARs):   {}".format(total))
    print("  With Java code:            {}".format(with_code))
    print("  Without code (docs/res):   {}".format(without_code))
    print("  Total .java files:         {}".format(total_java))
    print("  Total .class files:        {}".format(total_classes))
    print("  With vineflower/:          {}".format(with_vineflower))
    print("  ZKM obfuscated:            {}".format(zkm_count))
    print("  Unique modules:            {}".format(len(modules)))
    print("")
    print("  Type breakdown:")
    for t in sorted(types.keys()):
        print("    {:12s} {:>5d}".format(t, types[t]))
    print("")
    print("  Bytecode versions:")
    for bc in sorted(bytecodes.keys()):
        label = "Java {}".format(bc - 44) if bc >= 45 else str(bc)
        print("    v{} ({}): {:>5d}".format(bc, label, bytecodes[bc]))
    print("")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # tools/ -> module-navigator/
    indexes_dir = os.path.join(base_dir, "indexes")

    organized_dir = r"/home/cristian/modules/Prototipos/modulos/organized"

    if not os.path.isdir(organized_dir):
        print("ERROR: organized directory not found: {}".format(organized_dir))
        sys.exit(1)

    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("Building module inventory from: {}".format(organized_dir))
    print("")

    t0 = time.time()
    inventory, skipped = build_inventory(organized_dir, verbose=verbose)
    elapsed = time.time() - t0

    print_summary(inventory)

    # Write index
    os.makedirs(indexes_dir, exist_ok=True)
    out_path = os.path.join(indexes_dir, "module-inventory.json")

    # Add metadata wrapper
    output = {
        "_meta": {
            "description": "Module inventory for Niagara N4 decompiled modules",
            "source": organized_dir,
            "total_submodules": len(inventory),
            "build_time_sec": round(elapsed, 1),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "modules": inventory,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print("  Written: {} ({:.1f} MB)".format(out_path, size_mb))
    print("  Build time: {:.1f}s".format(elapsed))

    if skipped:
        print("")
        print("  Skipped {} submodules (no fase1-recon.json):".format(len(skipped)))
        for s in skipped[:10]:
            print("    - {}".format(s))
        if len(skipped) > 10:
            print("    ... and {} more".format(len(skipped) - 10))


if __name__ == "__main__":
    main()
