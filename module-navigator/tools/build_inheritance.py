#!/usr/bin/env python
"""
Build inheritance index from class-index.json.

Reads the class index (already has extends/implements per class) and produces
indexes/inheritance.json with three maps:

  parent_to_children:       { "BEdgePane": ["BLinkPad", "BConstrainedPane", ...] }
  interface_to_implementors: { "BIDialogPane": ["BDialog", ...] }
  class_to_chain:           { "BLinkPad": ["BEdgePane", "BPane", "BWidget", ...] }

Only processes top-level classes (outer_class=null).

Usage:
  python tools/build_inheritance.py [--base-dir DIR]
"""

import json
import os
import sys
import time


def detect_base_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(script_dir)
    if os.path.isdir(os.path.join(base, "indexes")):
        return base
    return None


def build_inheritance(base_dir):
    ci_path = os.path.join(base_dir, "indexes", "class-index.json")
    if not os.path.isfile(ci_path):
        print("ERROR: class-index.json not found at {}".format(ci_path))
        sys.exit(1)

    print("Loading class-index.json...")
    t0 = time.time()
    with open(ci_path, "r", encoding="utf-8") as f:
        ci_data = json.load(f)
    classes = ci_data.get("classes", {})
    t_load = time.time() - t0
    print("  Loaded in {:.1f}s ({} unique names)".format(t_load, len(classes)))

    # -------------------------------------------------------------------------
    # Pass 1: Build parent_to_children and interface_to_implementors
    # Also collect extends info for chain building
    # -------------------------------------------------------------------------
    print("Building inheritance maps...")
    t1 = time.time()

    parent_to_children = {}       # parent_name -> [child_name, ...]
    interface_to_implementors = {}  # iface_name -> [class_name, ...]
    extends_map = {}               # class_name -> extends_name (for chain)

    top_level_count = 0
    with_extends = 0
    with_implements = 0
    multi_entry_skips = 0

    for class_name, entries in classes.items():
        # Filter to top-level only
        top_entries = [e for e in entries if not e.get("outer_class")]
        if not top_entries:
            continue

        # For classes with multiple top-level entries (duplicates across modules),
        # process ALL of them — each module's class is a valid child/implementor.
        # For extends_map (used in chain building), use the first entry's extends.
        for e in top_entries:
            top_level_count += 1

            ext = e.get("extends")
            if ext:
                with_extends += 1
                # Add to parent_to_children
                if ext not in parent_to_children:
                    parent_to_children[ext] = []
                if class_name not in parent_to_children[ext]:
                    parent_to_children[ext].append(class_name)

                # Record for chain building (first occurrence wins)
                if class_name not in extends_map:
                    extends_map[class_name] = ext

            impls = e.get("implements", [])
            if impls:
                with_implements += 1
                for iface in impls:
                    if iface not in interface_to_implementors:
                        interface_to_implementors[iface] = []
                    if class_name not in interface_to_implementors[iface]:
                        interface_to_implementors[iface].append(class_name)

    # Sort children/implementors for deterministic output
    for k in parent_to_children:
        parent_to_children[k].sort()
    for k in interface_to_implementors:
        interface_to_implementors[k].sort()

    t2 = time.time()
    print("  Pass 1 done in {:.1f}s".format(t2 - t1))
    print("    Top-level entries processed: {:,}".format(top_level_count))
    print("    With extends: {:,}".format(with_extends))
    print("    With implements: {:,}".format(with_implements))
    print("    Unique parents: {:,}".format(len(parent_to_children)))
    print("    Unique interfaces: {:,}".format(len(interface_to_implementors)))

    # -------------------------------------------------------------------------
    # Pass 2: Build class_to_chain (walk extends until root)
    # -------------------------------------------------------------------------
    print("Building inheritance chains...")
    t3 = time.time()

    class_to_chain = {}
    max_depth = 0
    circular_count = 0

    for class_name in extends_map:
        chain = []
        current = extends_map.get(class_name)
        seen = {class_name}

        while current:
            if current in seen:
                # Circular reference — stop
                circular_count += 1
                break
            chain.append(current)
            seen.add(current)
            current = extends_map.get(current)

        if chain:
            class_to_chain[class_name] = chain
            if len(chain) > max_depth:
                max_depth = len(chain)

    t4 = time.time()
    print("  Pass 2 done in {:.1f}s".format(t4 - t3))
    print("    Classes with chains: {:,}".format(len(class_to_chain)))
    print("    Max chain depth: {}".format(max_depth))
    if circular_count:
        print("    Circular references: {}".format(circular_count))

    # -------------------------------------------------------------------------
    # Compute stats
    # -------------------------------------------------------------------------
    # Children distribution
    child_counts = [len(v) for v in parent_to_children.values()]
    child_counts.sort(reverse=True)

    impl_counts = [len(v) for v in interface_to_implementors.values()]
    impl_counts.sort(reverse=True)

    chain_depths = [len(v) for v in class_to_chain.values()]

    # Depth distribution
    depth_dist = {}
    for d in chain_depths:
        depth_dist[d] = depth_dist.get(d, 0) + 1

    # Top parents by children count
    top_parents = sorted(parent_to_children.items(),
                         key=lambda x: len(x[1]), reverse=True)[:20]

    # Top interfaces by implementors count
    top_interfaces = sorted(interface_to_implementors.items(),
                            key=lambda x: len(x[1]), reverse=True)[:20]

    print("")
    print("  Top 10 parents by children:")
    for name, children in top_parents[:10]:
        print("    {:40s} {:>5,} children".format(name, len(children)))

    print("")
    print("  Top 10 interfaces by implementors:")
    for name, impls in top_interfaces[:10]:
        print("    {:40s} {:>5,} implementors".format(name, len(impls)))

    print("")
    print("  Depth distribution:")
    for d in sorted(depth_dist.keys()):
        print("    depth {:2d}: {:>6,} classes".format(d, depth_dist[d]))

    # -------------------------------------------------------------------------
    # Build output
    # -------------------------------------------------------------------------
    meta = {
        "description": "Inheritance index for Niagara N4 decompiled modules",
        "source_index": "class-index.json",
        "top_level_processed": top_level_count,
        "with_extends": with_extends,
        "with_implements": with_implements,
        "unique_parents": len(parent_to_children),
        "unique_interfaces_implemented": len(interface_to_implementors),
        "classes_with_chains": len(class_to_chain),
        "max_chain_depth": max_depth,
        "circular_references": circular_count,
        "total_children_entries": sum(len(v) for v in parent_to_children.values()),
        "total_implementor_entries": sum(len(v) for v in interface_to_implementors.values()),
        "avg_children_per_parent": round(
            sum(len(v) for v in parent_to_children.values()) / max(len(parent_to_children), 1), 1),
        "avg_chain_depth": round(
            sum(chain_depths) / max(len(chain_depths), 1), 1),
        "depth_distribution": {str(k): v for k, v in sorted(depth_dist.items())},
        "build_time_sec": round(time.time() - t0, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    output = {
        "_meta": meta,
        "parent_to_children": parent_to_children,
        "interface_to_implementors": interface_to_implementors,
        "class_to_chain": class_to_chain,
    }

    # Write
    out_path = os.path.join(base_dir, "indexes", "inheritance.json")
    print("")
    print("Writing {}...".format(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"), ensure_ascii=False)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    total_time = time.time() - t0
    print("  Done: {:.1f} MB in {:.1f}s".format(size_mb, total_time))
    print("")

    # Summary
    print("=" * 60)
    print("INHERITANCE INDEX SUMMARY")
    print("=" * 60)
    print("  Top-level classes:           {:>7,}".format(top_level_count))
    print("  With extends:                {:>7,}".format(with_extends))
    print("  With implements:             {:>7,}".format(with_implements))
    print("  Unique parents:              {:>7,}".format(len(parent_to_children)))
    print("  Unique interfaces impl:      {:>7,}".format(len(interface_to_implementors)))
    print("  Classes with chains:         {:>7,}".format(len(class_to_chain)))
    print("  Max chain depth:             {:>7}".format(max_depth))
    print("  Avg chain depth:             {:>7.1f}".format(
        sum(chain_depths) / max(len(chain_depths), 1)))
    print("  Index size:                  {:>6.1f} MB".format(size_mb))
    print("  Build time:                  {:>6.1f}s".format(total_time))
    print("")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build inheritance index")
    parser.add_argument("--base-dir", "-d", help="Base directory")
    args = parser.parse_args()

    base_dir = args.base_dir or detect_base_dir()
    if not base_dir:
        print("ERROR: Cannot detect base directory.")
        sys.exit(1)

    build_inheritance(base_dir)
