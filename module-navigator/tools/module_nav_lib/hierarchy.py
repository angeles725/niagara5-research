"""
Hierarchy commands for Module Navigator (Phase 3).

Commands:
  hierarchy <class> [--depth N]   Show subclass tree (default depth 2)
  hierarchy <class> --chain       Show inheritance chain to root
  implementors <interface> [-n N] Show classes implementing an interface
"""

import json
import os


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

_inheritance_cache = None


def load_inheritance(base_dir):
    """Load inheritance.json (or use cached version from REPL)."""
    global _inheritance_cache
    if _inheritance_cache is not None:
        return _inheritance_cache

    path = os.path.join(base_dir, "indexes", "inheritance.json")
    if not os.path.isfile(path):
        print("ERROR: inheritance.json not found.")
        print("Run: python tools/build_inheritance.py")
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def _load_class_index(base_dir):
    """Load class-index.json for module info lookups."""
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


# ---------------------------------------------------------------------------
# hierarchy command
# ---------------------------------------------------------------------------

def cmd_hierarchy(base_dir, class_name, depth=2, show_chain=False):
    """Show subclass tree or inheritance chain for a class."""
    if show_chain:
        _show_chain(base_dir, class_name)
    else:
        _show_subtree(base_dir, class_name, depth)


def _show_subtree(base_dir, class_name, max_depth):
    """Show subclass tree rooted at class_name."""
    inh = load_inheritance(base_dir)
    if not inh:
        return

    p2c = inh.get("parent_to_children", {})
    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}

    # Check if class exists as a parent
    if class_name not in p2c:
        # Check if the class exists at all in class-index
        if ci_classes and class_name in ci_classes:
            print("")
            print("  {} has no known subclasses.".format(class_name))
            # Show its own chain for context
            c2c = inh.get("class_to_chain", {})
            if class_name in c2c:
                chain = c2c[class_name]
                print("  Chain: {} -> {}".format(class_name, " -> ".join(chain)))
            print("")
        else:
            print("  Class '{}' not found.".format(class_name))
            print("  Try: search '*{}*'".format(class_name))
        return

    # Count total descendants recursively
    total_desc = _count_descendants(class_name, p2c)

    # Get module info for root
    root_info = _get_module_info(class_name, ci_classes)

    print("")
    print("  Hierarchy: {} ({} direct children, {} total descendants)".format(
        class_name, len(p2c.get(class_name, [])), total_desc))
    if root_info:
        print("  Module: {}  Package: {}".format(root_info[0], root_info[1]))
    print("  Depth limit: {}".format(max_depth))
    print("")

    # Print tree
    _print_tree(class_name, p2c, ci_classes, max_depth, prefix="  ", is_last=True, current_depth=0)
    print("")


def _count_descendants(name, p2c, seen=None):
    """Count total descendants recursively (with cycle protection)."""
    if seen is None:
        seen = set()
    if name in seen:
        return 0
    seen.add(name)
    children = p2c.get(name, [])
    count = len(children)
    for child in children:
        count += _count_descendants(child, p2c, seen)
    return count


def _get_module_info(class_name, ci_classes):
    """Get (module, package) for a class from class-index, or None."""
    if class_name in ci_classes:
        entries = ci_classes[class_name]
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            return (top[0]["module"], top[0]["package"])
    return None


def _print_tree(name, p2c, ci_classes, max_depth, prefix, is_last, current_depth):
    """Recursively print a tree of subclasses."""
    # Connector characters
    if current_depth == 0:
        connector = ""
        child_prefix = prefix
    else:
        connector = "`-- " if is_last else "|-- "
        child_prefix = prefix + ("    " if is_last else "|   ")

    # Get module info
    info = _get_module_info(name, ci_classes)
    module_str = "  ({})".format(info[0]) if info else ""

    children = p2c.get(name, [])
    child_count_str = ""
    if children:
        total_desc = _count_descendants(name, p2c)
        child_count_str = "  [{} children]".format(len(children))

    line = "{}{}{}{}{}".format(prefix if current_depth == 0 else "", connector, name, module_str, child_count_str if current_depth < max_depth else "")

    if current_depth > 0:
        line = "{}{}{}{}".format(child_prefix.rstrip(), "", connector, name)
        # Add module info inline
        if info:
            line += "  ({})".format(info[0])

    if current_depth == 0:
        print("{}{}{}".format(prefix, name, module_str))
    else:
        # Build the prefix correctly
        pref = prefix[:-4] if prefix.endswith("    ") else prefix[:-4] if len(prefix) >= 4 else prefix
        # Simpler approach: use prefix directly
        print("{}{}{}{}".format(prefix, connector, name, module_str))

    # If at depth limit but has children, show count
    if current_depth >= max_depth:
        if children:
            total = _count_descendants(name, p2c)
            trunc_prefix = child_prefix if current_depth > 0 else prefix + "    "
            print("{}... {} descendants (use --depth {} to expand)".format(
                trunc_prefix, total, max_depth + 1))
        return

    # Print children
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        next_prefix = child_prefix if current_depth > 0 else prefix + "    "

        _print_tree(child, p2c, ci_classes, max_depth,
                    prefix=next_prefix, is_last=is_last_child,
                    current_depth=current_depth + 1)


# ---------------------------------------------------------------------------
# hierarchy --chain
# ---------------------------------------------------------------------------

def _show_chain(base_dir, class_name):
    """Show full inheritance chain from class to root."""
    inh = load_inheritance(base_dir)
    if not inh:
        return

    c2c = inh.get("class_to_chain", {})
    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}

    if class_name not in c2c:
        # Check if class exists
        if ci_classes and class_name in ci_classes:
            print("")
            print("  {} has no superclass chain (root class or interface).".format(class_name))
            # Show implements if any
            top = [e for e in ci_classes[class_name] if not e.get("outer_class")]
            if top and top[0].get("implements"):
                print("  Implements: {}".format(", ".join(top[0]["implements"])))
            print("")
        else:
            print("  Class '{}' not found.".format(class_name))
            print("  Try: search '*{}*'".format(class_name))
        return

    chain = c2c[class_name]

    print("")
    print("  Inheritance chain for {} (depth {}):".format(class_name, len(chain)))
    print("")

    # Print chain with module info
    all_classes = [class_name] + chain
    max_name_len = max(len(c) for c in all_classes)

    for i, cls in enumerate(all_classes):
        info = _get_module_info(cls, ci_classes)
        module_str = info[0] if info else "?"
        package_str = info[1] if info else "?"

        indent = "  " * i
        arrow = "^-- " if i > 0 else ""

        print("  {}{}{:>{w}s}  ({}, {})".format(
            indent, arrow, cls,
            module_str, package_str,
            w=max_name_len if i == 0 else 0,
        ))

    # Show implements for the queried class
    if ci_classes and class_name in ci_classes:
        top = [e for e in ci_classes[class_name] if not e.get("outer_class")]
        if top and top[0].get("implements"):
            print("")
            print("  Implements: {}".format(", ".join(top[0]["implements"])))

    # Show sibling count for the queried class
    p2c = inh.get("parent_to_children", {})
    if chain:
        parent = chain[0]
        siblings = p2c.get(parent, [])
        sibling_count = len(siblings) - 1  # exclude self
        if sibling_count > 0:
            print("  Siblings under {}: {}".format(parent, sibling_count))

    print("")


# ---------------------------------------------------------------------------
# implementors command
# ---------------------------------------------------------------------------

def cmd_implementors(base_dir, interface_name, limit=50):
    """Show classes that implement an interface."""
    inh = load_inheritance(base_dir)
    if not inh:
        return

    i2i = inh.get("interface_to_implementors", {})
    ci_data = _load_class_index(base_dir)
    ci_classes = ci_data.get("classes", {}) if ci_data else {}

    if interface_name not in i2i:
        # Try case-insensitive
        matches = [k for k in i2i if k.lower() == interface_name.lower()]
        if matches:
            interface_name = matches[0]
        else:
            # Check if it exists as a parent (class, not interface)
            p2c = inh.get("parent_to_children", {})
            if interface_name in p2c:
                print("  '{}' is a class, not an interface. Use 'hierarchy {}' instead.".format(
                    interface_name, interface_name))
            else:
                print("  Interface '{}' not found in implementors index.".format(interface_name))
                print("  Try: search '*{}*'".format(interface_name))
            return

    implementors = i2i[interface_name]

    print("")
    print("  Implementors of {}: {} classes".format(interface_name, len(implementors)))
    print("")
    print("  {:>35s}  {:20s}  {:s}".format("CLASS", "MODULE", "PACKAGE"))
    print("  " + "-" * 85)

    shown = 0
    for cls in implementors:
        if shown >= limit:
            break
        info = _get_module_info(cls, ci_classes)
        module_str = info[0] if info else "?"
        package_str = info[1] if info else "?"
        print("  {:>35s}  {:20s}  {:s}".format(cls, module_str, package_str))
        shown += 1

    if len(implementors) > limit:
        print("")
        print("  ... and {} more (use -n to show more)".format(len(implementors) - limit))

    print("")
