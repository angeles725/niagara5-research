#!/usr/bin/env python
"""
Build module-inventory.json from a decompiled Niagara corpus.

Two corpus layouts are supported via --layout / NAV_LAYOUT (default: flat):

  flat (N5, default)  organized/<module>/{vineflower,fallback,recon.json,...}
                       organized/_bin-ext/<jar>/{...} -> keyed "_bin-ext/<jar>"
                       No submodule split; the inventory key IS the module
                       name. Reads organized/<module>/recon.json directly.

  n4 (legacy)          organized/{module}/{submodule}/pipeline/fase1-recon.json
                       for each submodule, counting .java files under
                       vineflower/. This is the original N4 corpus shape.

The corpus root is resolved via --organized, NAV_ORGANIZED_DIR, a sibling
organized/ directory, or an existing indexes/module-inventory.json --
see corpus_config.resolve_organized_dir().

Output: indexes/module-inventory.json

Requires: Python 3.x (stdlib only)
"""

import argparse
import json
import os
import sys
import time

import corpus_config


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


def build_inventory_n4(organized_dir, verbose=False):
    """Build inventory dict from an N4-shaped organized/ directory
    (organized/{module}/{submodule}/pipeline/fase1-recon.json)."""
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


def _module_bytecode_major(recon):
    """Pick the dominant bytecode major version from recon.json's
    class_major_version_histogram (N5 recon shape has no single
    'bytecode_major_version' field like N4's fase1-recon.json)."""
    hist = recon.get("class_major_version_histogram") or {}
    if not hist:
        return 0
    try:
        return int(max(hist.items(), key=lambda kv: kv[1])[0])
    except (ValueError, TypeError):
        return 0


def _module_zkm_heuristic(recon):
    """Best-effort obfuscation heuristic from recon.json's
    obfuscation_heuristic.ratio (N5 recon has no direct 'ofuscador_detectado'
    boolean like N4's fase1-recon.json)."""
    ratio = (recon.get("obfuscation_heuristic") or {}).get("ratio", 0.0)
    try:
        return float(ratio) >= 0.3
    except (ValueError, TypeError):
        return False


def build_inventory_flat(organized_dir, verbose=False):
    """Build inventory dict from a flat N5-shaped organized/ directory.

    organized/<module>/{vineflower,fallback,extracted,resources,recon.json}
    organized/_bin-ext/<jar>/{...same layout...} -> keyed "_bin-ext/<jar>"

    No submodule split: the inventory key IS the module name. Housekeeping
    dirs (docSource, _logs, _recon) are skipped; any module dir missing a
    recon.json is skipped (recorded, not a crash).
    """
    inventory = {}
    skipped = []
    total = 0

    for module_key, module_path in corpus_config.iter_flat_module_dirs(organized_dir):
        recon_path = os.path.join(module_path, "recon.json")

        with open(recon_path, "r", encoding="utf-8-sig") as f:
            try:
                recon = json.load(f)
            except json.JSONDecodeError as e:
                if verbose:
                    print("  WARN: bad JSON in {}: {}".format(recon_path, e))
                skipped.append(module_key)
                continue

        total += 1

        vineflower_dir = os.path.join(module_path, "vineflower")
        fallback_dir = os.path.join(module_path, "fallback")
        has_vineflower = os.path.isdir(vineflower_dir)
        has_fallback = os.path.isdir(fallback_dir)

        java_files = count_java_files(vineflower_dir)
        fallback_java_files = count_java_files(fallback_dir)
        packages, third_party = scan_packages(vineflower_dir)
        if has_fallback:
            fb_packages, fb_third_party = scan_packages(fallback_dir)
            packages = sorted(set(packages) | set(fb_packages))
            third_party = sorted(set(third_party) | set(fb_third_party))

        jar_path = recon.get("jar_path", "")
        jar_name = os.path.basename(jar_path) if jar_path else (
            module_key.split("/")[-1] + ".jar"
        )

        entry = {
            "module": module_key,
            "type": "",  # N5 flat layout has no -rt/-ux submodule split
            "jar": jar_name,
            "class_count": recon.get("class_count", 0),
            "java_files": java_files,
            "fallback_java_files": fallback_java_files,
            "zkm": _module_zkm_heuristic(recon),
            "bytecode": _module_bytecode_major(recon),
            "has_vineflower": has_vineflower,
            "has_fallback": has_fallback,
            "has_cfr": has_fallback,  # fallback/ is CFR output in N5
            "has_code": java_files > 0 or fallback_java_files > 0,
            "packages": packages,
            "third_party": third_party,
        }

        inventory[module_key] = entry

        if verbose and total % 50 == 0:
            print("  ... processed {} modules".format(total))

    return inventory, skipped


def build_inventory(organized_dir, layout="flat", verbose=False):
    """Dispatch to the layout-specific inventory builder."""
    if layout == "n4":
        return build_inventory_n4(organized_dir, verbose=verbose)
    return build_inventory_flat(organized_dir, verbose=verbose)


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


def _parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organized", default=None,
                         help="Path to the organized/ corpus dir "
                              "(default: NAV_ORGANIZED_DIR env, sibling "
                              "organized/, or existing inventory source)")
    parser.add_argument("--layout", default=None, choices=corpus_config.VALID_LAYOUTS,
                         help="Corpus layout: flat (N5, default) or n4 (legacy)")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--print-organized-dir", action="store_true",
                         help="Print the resolved organized/ dir and exit "
                              "(used by reindex.sh preflight)")
    return parser.parse_args(argv)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # tools/ -> module-navigator/
    indexes_dir = os.path.join(base_dir, "indexes")

    args = _parse_args(sys.argv[1:])
    organized_dir = corpus_config.resolve_organized_dir(base_dir, args.organized)
    layout = corpus_config.resolve_layout(args.layout)

    if args.print_organized_dir:
        print(organized_dir)
        return

    if not os.path.isdir(organized_dir):
        print("ERROR: organized directory not found: {}".format(organized_dir))
        print("  Override with --organized <dir> or NAV_ORGANIZED_DIR env var.")
        sys.exit(1)

    verbose = args.verbose

    print("Building module inventory from: {} (layout={})".format(organized_dir, layout))
    print("")

    t0 = time.time()
    inventory, skipped = build_inventory(organized_dir, layout=layout, verbose=verbose)
    elapsed = time.time() - t0

    print_summary(inventory)

    # Write index
    os.makedirs(indexes_dir, exist_ok=True)
    out_path = os.path.join(indexes_dir, "module-inventory.json")

    # Add metadata wrapper
    output = {
        "_meta": {
            "description": "Module inventory for Niagara N5 decompiled modules",
            "source": organized_dir,
            "layout": layout,
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
        recon_name = "fase1-recon.json" if layout == "n4" else "recon.json"
        print("")
        print("  Skipped {} submodules (bad/missing {}):".format(len(skipped), recon_name))
        for s in skipped[:10]:
            print("    - {}".format(s))
        if len(skipped) > 10:
            print("    ... and {} more".format(len(skipped) - 10))


if __name__ == "__main__":
    main()
