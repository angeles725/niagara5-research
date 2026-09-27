"""
Code Similarity Detection for Module Navigator (Phase 24).

Commands:
  similar <class> [-n N]             Classes with similar structure
  clones [--module mod] [-n N]       Top duplicate class pairs in a module

Computes Jaccard similarity over method names + field names + parent class.
No builder needed — reads method-index, field-index, inheritance on-demand.
"""

import json
import os
from collections import defaultdict


# ---------------------------------------------------------------------------
# Index loading (reuse existing loaders, on-demand cached)
# ---------------------------------------------------------------------------

def _load_method_index(base_dir):
    """Load method-index.json via methods module (cached)."""
    from module_nav_lib.methods import load_method_index
    return load_method_index(base_dir)


def _load_field_index(base_dir):
    """Load field-index.json via fields module (cached)."""
    from module_nav_lib.fields import load_field_index
    return load_field_index(base_dir)


def _load_inheritance(base_dir):
    """Load inheritance.json via hierarchy module (cached)."""
    from module_nav_lib.hierarchy import load_inheritance
    return load_inheritance(base_dir)


def _load_class_index(base_dir):
    """Load class-index.json (on-demand, cached)."""
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


# ---------------------------------------------------------------------------
# Fingerprint building
# ---------------------------------------------------------------------------

_fingerprint_cache = {}


def _build_fingerprints(base_dir, module_filter=None):
    """Build fingerprint dicts: class -> (method_set, field_set, parent, module).

    Returns dict of class_name -> fingerprint tuple.
    Uses cached result if available (key = module_filter or '__all__').
    """
    cache_key = module_filter or "__all__"
    if cache_key in _fingerprint_cache:
        return _fingerprint_cache[cache_key]

    mi = _load_method_index(base_dir)
    fi = _load_field_index(base_dir)
    inh = _load_inheritance(base_dir)
    ci_data = _load_class_index(base_dir)

    if not mi or not fi or not inh or not ci_data:
        return {}

    class_methods = mi.get("class_methods", {})
    class_fields = fi.get("class_fields", {})
    c2c = inh.get("class_to_chain", {})
    ci_classes = ci_data.get("classes", {})

    # Build module lookup
    class_module = {}
    for cname, entries in ci_classes.items():
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            class_module[cname] = top[0].get("module", "?")
        elif entries:
            class_module[cname] = entries[0].get("module", "?")

    # All classes that have at least methods OR fields
    all_classes = set(class_methods.keys()) | set(class_fields.keys())

    fingerprints = {}
    for cname in all_classes:
        mod = class_module.get(cname, "?")
        if module_filter and mod != module_filter:
            continue

        methods = set(class_methods.get(cname, []))
        fields = set(class_fields.get(cname, []))
        chain = c2c.get(cname, [])
        parent = chain[0] if chain else ""

        # Skip tiny classes (< 2 methods) — they produce noisy matches
        if len(methods) < 2:
            continue

        fingerprints[cname] = (methods, fields, parent, mod)

    _fingerprint_cache[cache_key] = fingerprints
    return fingerprints


def _jaccard(set_a, set_b):
    """Jaccard similarity: |A ∩ B| / |A ∪ B|. Returns 0.0 if both empty."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _similarity_score(fp_a, fp_b):
    """Compute weighted similarity between two fingerprints.

    fp = (method_set, field_set, parent, module)
    Score: 0.5 * method_jaccard + 0.3 * field_jaccard + 0.2 * parent_match
    """
    methods_a, fields_a, parent_a, _ = fp_a
    methods_b, fields_b, parent_b, _ = fp_b

    mj = _jaccard(methods_a, methods_b)
    fj = _jaccard(fields_a, fields_b)
    pm = 1.0 if (parent_a and parent_b and parent_a == parent_b) else 0.0

    return 0.5 * mj + 0.3 * fj + 0.2 * pm


# ---------------------------------------------------------------------------
# similar <class> — find structurally similar classes
# ---------------------------------------------------------------------------

def cmd_similar(base_dir, class_name, limit=20):
    """Find classes with similar structure to the target class."""
    fingerprints = _build_fingerprints(base_dir)
    if not fingerprints:
        print("  ERROR: Could not build fingerprints (indexes missing).")
        return

    if class_name not in fingerprints:
        # Try case-insensitive
        found = None
        lower = class_name.lower()
        for k in fingerprints:
            if k.lower() == lower:
                found = k
                break
        if found:
            class_name = found
        else:
            print("")
            print("  Class '{}' not found in fingerprint index.".format(class_name))
            print("  (Needs >= 2 methods to be indexed)")
            partial = [c for c in fingerprints if class_name.lower() in c.lower()]
            if partial:
                shown = sorted(partial)[:10]
                print("  Partial matches: {}".format(", ".join(shown)))
            print("")
            return

    target_fp = fingerprints[class_name]
    target_methods, target_fields, target_parent, target_module = target_fp

    # Compute similarity against all other classes
    scores = []
    for other_name, other_fp in fingerprints.items():
        if other_name == class_name:
            continue

        # Pre-filter: skip classes with very different method count
        other_methods = other_fp[0]
        ratio = len(other_methods) / len(target_methods) if target_methods else 0
        if ratio < 0.3 or ratio > 3.0:
            continue

        score = _similarity_score(target_fp, other_fp)
        if score > 0.15:  # threshold: at least 15% similar
            scores.append((other_name, score, other_fp))

    scores.sort(key=lambda x: -x[1])
    top = scores[:limit]

    # Print results
    print("")
    print("  SIMILAR CLASSES: {}".format(class_name))
    print("  " + "=" * 65)
    print("  Target module:  {}".format(target_module))
    print("  Target methods: {}".format(len(target_methods)))
    print("  Target fields:  {}".format(len(target_fields)))
    print("  Target parent:  {}".format(target_parent or "(none)"))
    print("")

    if not top:
        print("  No similar classes found (threshold > 15%).")
        print("")
        return

    print("  {:5s}  {:40s}  {:25s}  {:>5s}  {:>5s}  {:>6s}".format(
        "SCORE", "CLASS", "MODULE", "METH", "FLD", "PARENT"))
    print("  " + "-" * 90)

    for other_name, score, other_fp in top:
        other_methods, other_fields, other_parent, other_module = other_fp
        # Count method overlap
        shared_methods = len(target_methods & other_methods)
        parent_match = "Y" if (other_parent == target_parent and target_parent) else ""

        print("  {:5.1%}  {:40s}  {:25s}  {:>3d}/{:<1d}  {:>5d}  {:>6s}".format(
            score,
            other_name[:40],
            other_module[:25],
            shared_methods, len(other_methods),
            len(other_fields),
            parent_match,
        ))

    if len(scores) > limit:
        print("")
        print("  ... and {} more matches (use -n {} to see all)".format(
            len(scores) - limit, len(scores)))

    # Show shared methods with top match
    if top:
        best_name, best_score, best_fp = top[0]
        best_methods = best_fp[0]
        shared = sorted(target_methods & best_methods)
        unique_target = sorted(target_methods - best_methods)
        unique_other = sorted(best_methods - target_methods)

        print("")
        print("  TOP MATCH DETAIL: {} ({:.1%})".format(best_name, best_score))
        print("  " + "-" * 50)
        if shared:
            print("  Shared methods ({}): {}".format(
                len(shared), ", ".join(shared[:20])))
            if len(shared) > 20:
                print("    ... and {} more".format(len(shared) - 20))
        if unique_target:
            print("  Only in {} ({}): {}".format(
                class_name, len(unique_target),
                ", ".join(unique_target[:10])))
            if len(unique_target) > 10:
                print("    ... and {} more".format(len(unique_target) - 10))
        if unique_other:
            print("  Only in {} ({}): {}".format(
                best_name, len(unique_other),
                ", ".join(unique_other[:10])))
            if len(unique_other) > 10:
                print("    ... and {} more".format(len(unique_other) - 10))

    print("")
    print("  Total candidates scanned: {:,}".format(len(fingerprints) - 1))
    print("  Matches above threshold:  {:,}".format(len(scores)))
    print("")


# ---------------------------------------------------------------------------
# clones [--module mod] — top duplicate pairs
# ---------------------------------------------------------------------------

def cmd_clones(base_dir, module_filter=None, limit=20):
    """Find top pairs of structurally similar (near-clone) classes."""
    fingerprints = _build_fingerprints(base_dir, module_filter=module_filter)
    if not fingerprints:
        if module_filter:
            print("  No classes found in module '{}'.".format(module_filter))
        else:
            print("  ERROR: Could not build fingerprints (indexes missing).")
        return

    # Group by parent class to reduce O(n^2) to manageable
    by_parent = defaultdict(list)
    for cname, fp in fingerprints.items():
        parent = fp[2]  # parent class
        if parent:
            by_parent[parent].append(cname)
        else:
            by_parent["__no_parent__"].append(cname)

    # Also group by method-count bucket (within ±30%) for cross-parent clones
    by_size = defaultdict(list)
    for cname, fp in fingerprints.items():
        n = len(fp[0])  # method count
        bucket = n // 3  # bucket of 3
        by_size[bucket].append(cname)

    # Compute pairs within each group
    pairs = []
    seen_pairs = set()

    def _add_pair(a, b, score):
        key = (min(a, b), max(a, b))
        if key not in seen_pairs:
            seen_pairs.add(key)
            pairs.append((a, b, score))

    # Compare within same-parent groups (highest chance of clones)
    for parent, members in by_parent.items():
        if len(members) < 2 or len(members) > 500:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                score = _similarity_score(fingerprints[a], fingerprints[b])
                if score > 0.40:  # stricter threshold for clones
                    _add_pair(a, b, score)

    # Compare within same-size bucket (catch cross-parent clones)
    for bucket, members in by_size.items():
        if len(members) < 2 or len(members) > 300:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                score = _similarity_score(fingerprints[a], fingerprints[b])
                if score > 0.50:  # even stricter for cross-parent
                    _add_pair(a, b, score)

    pairs.sort(key=lambda x: -x[2])
    top = pairs[:limit]

    scope = module_filter if module_filter else "ALL MODULES"

    print("")
    print("  CODE CLONES: {}".format(scope))
    print("  " + "=" * 75)
    print("  Classes scanned: {:,}".format(len(fingerprints)))
    print("  Parent groups:   {:,}".format(len(by_parent)))
    print("  Clone pairs found: {:,} (>{:.0%} similarity)".format(
        len(pairs), 0.40))
    print("")

    if not top:
        print("  No clone pairs found above threshold.")
        print("")
        return

    print("  {:5s}  {:35s}  {:35s}".format("SCORE", "CLASS A", "CLASS B"))
    print("  " + "-" * 80)

    for a, b, score in top:
        fp_a = fingerprints[a]
        fp_b = fingerprints[b]
        shared = len(fp_a[0] & fp_b[0])
        total = len(fp_a[0] | fp_b[0])

        print("  {:5.1%}  {:35s}  {:35s}  ({}/{} methods)".format(
            score, a[:35], b[:35], shared, total))

    if len(pairs) > limit:
        print("")
        print("  ... and {} more pairs (use -n {} to see all)".format(
            len(pairs) - limit, len(pairs)))

    # Summary by module
    if not module_filter and top:
        mod_counts = defaultdict(int)
        for a, b, score in pairs:
            mod_a = fingerprints[a][3]
            mod_b = fingerprints[b][3]
            mod_counts[mod_a] += 1
            if mod_a != mod_b:
                mod_counts[mod_b] += 1

        print("")
        print("  TOP MODULES BY CLONE PAIRS:")
        for mod, count in sorted(mod_counts.items(), key=lambda x: -x[1])[:10]:
            print("    {:35s}  {:>5,} pairs".format(mod, count))

    print("")
