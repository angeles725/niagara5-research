"""
Header imports command for Module Navigator (Batch 6).

Reads the raw `import` statements from the .java file header, including
imports that point to classes OUTSIDE the decompiled corpus (for example,
`com.tridium.nre.security.*` from `bin/ext/nre.jar`, which the main corpus
does not cover).

Complements `xref --imports`, which lists imports RESOLVED via the xref
index (i.e. classes the tool already knows about). This command exposes
the raw header so cross-jar dependencies are visible.

Commands:
  imports <Class>                  List raw imports from the .java header
  imports <Class> --external-only  Only imports to classes not in the corpus
  imports <Class> -n N             Limit results
"""

import json
import os
import re


# Matches: import [static] pkg.sub.Name;    or    import pkg.sub.*;
# Captures: group(1) = "static " or empty; group(2) = FQN (may end in .*)
IMPORT_RE = re.compile(
    r'^\s*import\s+(static\s+)?([\w.]+(?:\.\*)?)\s*;'
)

# Matches the first top-level type declaration (class / interface / enum)
# — once we see this, the header is over and we stop scanning imports.
DECL_RE = re.compile(
    r'^\s*(?:(?:public|protected|private|abstract|final|static|strictfp)\s+)*'
    r'(?:class|interface|enum)\s+\w+'
)


_xref_known_classes_cache = None


def _load_known_classes(base_dir):
    """Return the set of simple class names that exist in xref-index.

    Cached after first call. Used to flag imports as [external] when their
    simple name is NOT in the xref index (i.e. the class is not in our
    decompiled corpus).
    """
    global _xref_known_classes_cache
    if _xref_known_classes_cache is not None:
        return _xref_known_classes_cache

    path = os.path.join(base_dir, "indexes", "xref-index.json")
    if not os.path.isfile(path):
        _xref_known_classes_cache = set()
        return _xref_known_classes_cache

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, OSError, ValueError):
        _xref_known_classes_cache = set()
        return _xref_known_classes_cache

    known = set()
    known.update(data.get("class_imports", {}).keys())
    known.update(data.get("class_imported_by", {}).keys())
    _xref_known_classes_cache = known
    return known


def _is_external(fqn, known):
    """Is this import pointing outside the corpus?

    Wildcards (pkg.*) cannot be classified and are never treated as external.
    """
    if fqn.endswith(".*"):
        return False
    simple = fqn.rsplit(".", 1)[-1]
    return simple not in known


def cmd_imports(base_dir, class_name, external_only=False, limit=100):
    """List raw import statements from a class's .java header."""
    # Import lazily to avoid a circular top-level dependency when this module
    # is registered in module_nav.py. Also lets us reuse the shared helpers.
    from module_nav_lib.grep_search import (
        _load_class_index, _resolve_class, _get_source_root,
    )

    data = _load_class_index(base_dir)
    if not data:
        return

    resolved, entry = _resolve_class(data, class_name)
    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        print("  Try: search '*{}*'".format(class_name))
        return

    source_root = _get_source_root(data)
    if not source_root:
        return  # error already printed

    filepath = os.path.join(source_root, entry["path"])
    if not os.path.isfile(filepath):
        print("  ERROR: Source file not found: {}".format(filepath))
        return

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (IOError, OSError) as e:
        print("  ERROR: Cannot read source: {}".format(e))
        return

    # Parse imports until the first class/interface/enum declaration
    imports = []
    for lineno, line in enumerate(lines, 1):
        if DECL_RE.match(line):
            break
        m = IMPORT_RE.match(line)
        if m:
            is_static = bool(m.group(1))
            fqn = m.group(2)
            imports.append((lineno, is_static, fqn))

    known = _load_known_classes(base_dir)

    total_imports = len(imports)
    ext_count_all = sum(1 for _, _, f in imports if _is_external(f, known))

    if external_only:
        imports = [i for i in imports if _is_external(i[2], known)]

    title = "IMPORTS (external only)" if external_only else "IMPORTS"

    print("")
    print("  {} of {}: {} entries{}".format(
        title, resolved, len(imports),
        "" if external_only else " ({} external)".format(ext_count_all),
    ))
    print("  Package: {}  Module: {}".format(entry["package"], entry["module"]))
    print("  Path:    {}".format(entry["path"]))

    if not imports:
        if external_only and total_imports > 0:
            print("")
            print("  No external imports. All {} imports resolve in corpus.".format(total_imports))
        elif total_imports == 0:
            print("")
            print("  No import statements in header.")
        print("")
        return

    # Group by root package (first dot segment)
    grouped = {}
    for lineno, is_static, fqn in imports:
        root = fqn.split(".", 1)[0]
        grouped.setdefault(root, []).append((lineno, is_static, fqn))

    print("")
    shown = 0
    truncated = False
    for root in sorted(grouped.keys()):
        if shown >= limit:
            truncated = True
            break
        print("  [{}]".format(root))
        for lineno, is_static, fqn in grouped[root]:
            if shown >= limit:
                truncated = True
                break
            tags = []
            if is_static:
                tags.append("static")
            if _is_external(fqn, known):
                tags.append("external")
            tag_str = "  [{}]".format(",".join(tags)) if tags else ""
            print("    L{:<5d} {}{}".format(lineno, fqn, tag_str))
            shown += 1
        if shown >= limit:
            truncated = True

    if truncated:
        print("")
        print("    ... limit reached ({}) — use -n to increase".format(limit))

    if not external_only and ext_count_all > 0:
        print("")
        print("  {} import(s) not resolved in corpus — rerun with --external-only to isolate.".format(
            ext_count_all))
    print("")
