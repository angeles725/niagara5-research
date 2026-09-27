"""
Config & Resource Coupling for Module Navigator (Phase 25).

Commands:
  config-usage [--module mod] [-n N]    Classes that read configuration
  config-keys [-n N]                    Top config keys referenced in code
  resources-usage <module> [-n N]       How resources of a module are used

Traces configuration access patterns: System.getProperty, @NiagaraProperty,
BAbstractService configs, Properties loading, BOrd config lookups.
No builder needed — uses token-index.db + source grep on-demand, cached.
"""

import os
import re
import sqlite3
from collections import defaultdict


# ---------------------------------------------------------------------------
# Index loading (reuses existing loaders, on-demand cached)
# ---------------------------------------------------------------------------

def _load_class_index(base_dir):
    """Load class-index.json (on-demand, cached)."""
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


def _get_db(base_dir):
    """Get token-index.db connection (lazy)."""
    from module_nav_lib.tokens import _get_db as get_token_db
    return get_token_db(base_dir)


# ---------------------------------------------------------------------------
# Config pattern definitions
# ---------------------------------------------------------------------------

# Tokens to search in token-index.db for quick hit detection
CONFIG_TOKENS = [
    "getProperty",        # System.getProperty("key")
    "setProperty",        # System.setProperty("key", val)
    "getConfig",          # BAbstractService.getConfig()
    "loadProperties",     # Properties.load()
    "getResourceAsStream",  # ClassLoader.getResourceAsStream("file.properties")
    "NiagaraProperty",    # @NiagaraProperty annotation
    "BConfigProperty",    # Config property type
]

# Regex patterns applied to source lines for classification
CONFIG_PATTERNS = {
    "System.getProperty": re.compile(r'System\s*\.\s*getProperty\s*\('),
    "System.setProperty": re.compile(r'System\s*\.\s*setProperty\s*\('),
    "getConfig()": re.compile(r'\.\s*getConfig\s*\('),
    "@NiagaraProperty": re.compile(r'@NiagaraProperty'),
    "Properties.load": re.compile(r'\.load\s*\(.*(?:InputStream|Reader)'),
    "getResourceAsStream": re.compile(r'getResourceAsStream\s*\('),
    "BOrd.make": re.compile(r'BOrd\s*\.\s*make\s*\(\s*"'),
    ".properties ref": re.compile(r'["\']\S+\.properties["\']'),
    ".xml config ref": re.compile(r'["\']\S+(?:config|Config|setting|Setting)\S*\.xml["\']'),
}

# Regex for extracting specific keys
KEY_EXTRACTORS = {
    "System.getProperty": re.compile(
        r'System\s*\.\s*getProperty\s*\(\s*"([^"]+)"'),
    "System.setProperty": re.compile(
        r'System\s*\.\s*setProperty\s*\(\s*"([^"]+)"'),
    "BOrd.make": re.compile(
        r'BOrd\s*\.\s*make\s*\(\s*"([^"]+)"'),
    "getResourceAsStream": re.compile(
        r'getResourceAsStream\s*\(\s*"([^"]+)"'),
    ".properties ref": re.compile(
        r'["\'](\S+\.properties)["\']'),
}


# ---------------------------------------------------------------------------
# Source scanning (cached)
# ---------------------------------------------------------------------------

_config_scan_cache = {}


def _scan_config_patterns(base_dir, module_filter=None):
    """Scan source files for config access patterns.

    Returns dict with:
      - by_class: {class_name: {pattern_type: [line_info, ...], "module": mod}}
      - by_pattern: {pattern_type: count}
      - keys: {key_source: {key: count}}
      - total_files: int
    """
    cache_key = module_filter or "__all__"
    if cache_key in _config_scan_cache:
        return _config_scan_cache[cache_key]

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return None

    ci_classes = ci_data.get("classes", {})
    source_root = ci_data.get("_meta", {}).get("source", "")

    # Build file list: (class_name, module, source_path)
    file_list = []
    for cname, entries in ci_classes.items():
        for entry in entries:
            if entry.get("outer_class"):
                continue
            mod = entry.get("module", "?")
            if module_filter and mod != module_filter:
                continue
            rel_path = entry.get("path", "")
            if rel_path and source_root:
                src = os.path.join(source_root, rel_path)
                if os.path.isfile(src):
                    file_list.append((cname, mod, src))

    by_class = {}
    by_pattern = defaultdict(int)
    keys = defaultdict(lambda: defaultdict(int))
    total_files = len(file_list)
    files_with_config = 0

    for cname, mod, src_path in file_list:
        try:
            with open(src_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except Exception:
            continue

        class_hits = defaultdict(list)
        found_any = False

        for line_no, line in enumerate(source.split("\n"), 1):
            for pname, pat in CONFIG_PATTERNS.items():
                if pat.search(line):
                    class_hits[pname].append({
                        "line": line_no,
                        "text": line.strip()[:120],
                    })
                    by_pattern[pname] += 1
                    found_any = True

                    # Extract keys
                    if pname in KEY_EXTRACTORS:
                        for m in KEY_EXTRACTORS[pname].finditer(line):
                            keys[pname][m.group(1)] += 1

        if found_any:
            files_with_config += 1
            by_class[cname] = {
                "patterns": dict(class_hits),
                "module": mod,
                "source": src_path,
            }

    result = {
        "by_class": by_class,
        "by_pattern": dict(by_pattern),
        "keys": {k: dict(v) for k, v in keys.items()},
        "total_files": total_files,
        "files_with_config": files_with_config,
    }

    _config_scan_cache[cache_key] = result
    return result


# ---------------------------------------------------------------------------
# config-usage — classes that access configuration
# ---------------------------------------------------------------------------

def cmd_config_usage(base_dir, module_filter=None, limit=50):
    """Show classes that read configuration, grouped by access pattern."""
    print("")
    print("  Scanning source files for config access patterns...")

    result = _scan_config_patterns(base_dir, module_filter=module_filter)
    if not result:
        print("  ERROR: Could not load class-index.")
        return

    by_class = result["by_class"]
    by_pattern = result["by_pattern"]

    scope = module_filter if module_filter else "ALL MODULES"

    print("")
    print("  CONFIG USAGE: {}".format(scope))
    print("  " + "=" * 70)
    print("  Files scanned:       {:>7,}".format(result["total_files"]))
    print("  Files with config:   {:>7,}".format(result["files_with_config"]))
    print("")

    # Pattern summary
    if by_pattern:
        print("  PATTERN SUMMARY:")
        print("  {:30s}  {:>7s}".format("PATTERN", "HITS"))
        print("  " + "-" * 40)
        for pname, count in sorted(by_pattern.items(), key=lambda x: -x[1]):
            print("  {:30s}  {:>7,}".format(pname, count))
        print("")

    # Top classes by number of config patterns
    if by_class:
        ranked = sorted(
            by_class.items(),
            key=lambda x: sum(len(v) for v in x[1]["patterns"].values()),
            reverse=True
        )[:limit]

        # Group by module
        by_module = defaultdict(list)
        for cname, info in ranked:
            by_module[info["module"]].append((cname, info))

        print("  TOP CLASSES WITH CONFIG ACCESS:")
        print("  {:35s}  {:25s}  {:>5s}  {:s}".format(
            "CLASS", "MODULE", "HITS", "PATTERNS"))
        print("  " + "-" * 90)

        shown = 0
        for mod in sorted(by_module.keys()):
            for cname, info in sorted(by_module[mod], key=lambda x: -sum(len(v) for v in x[1]["patterns"].values())):
                if shown >= limit:
                    break
                total_hits = sum(len(v) for v in info["patterns"].values())
                pattern_names = sorted(info["patterns"].keys())
                print("  {:35s}  {:25s}  {:>5,}  {}".format(
                    cname[:35],
                    info["module"][:25],
                    total_hits,
                    ", ".join(pattern_names),
                ))
                shown += 1

        remaining = len(by_class) - limit
        if remaining > 0:
            print("")
            print("  ... and {:,} more classes (use -n {} to see all)".format(
                remaining, len(by_class)))

    # Module summary
    if by_class and not module_filter:
        mod_counts = defaultdict(int)
        for cname, info in by_class.items():
            mod_counts[info["module"]] += 1

        print("")
        print("  MODULES WITH CONFIG ACCESS ({:,} total):".format(len(mod_counts)))
        for mod, count in sorted(mod_counts.items(), key=lambda x: -x[1])[:20]:
            print("    {:35s}  {:>5,} classes".format(mod, count))
        if len(mod_counts) > 20:
            print("    ... and {} more modules".format(len(mod_counts) - 20))

    print("")


# ---------------------------------------------------------------------------
# config-keys — top configuration keys referenced in code
# ---------------------------------------------------------------------------

def cmd_config_keys(base_dir, limit=50):
    """Show top configuration keys referenced in source code."""
    print("")
    print("  Scanning source files for config keys...")

    result = _scan_config_patterns(base_dir)
    if not result:
        print("  ERROR: Could not load class-index.")
        return

    keys = result["keys"]

    print("")
    print("  CONFIG KEYS REFERENCED IN CODE")
    print("  " + "=" * 70)
    print("  Files scanned:       {:>7,}".format(result["total_files"]))
    print("  Files with config:   {:>7,}".format(result["files_with_config"]))
    print("")

    if not keys:
        print("  No config keys extracted.")
        print("")
        return

    # Flatten all keys with their source pattern
    all_keys = []
    for source, key_counts in keys.items():
        for key, count in key_counts.items():
            all_keys.append((key, count, source))

    all_keys.sort(key=lambda x: -x[1])

    # Group by source pattern
    for source in sorted(keys.keys()):
        key_counts = keys[source]
        sorted_keys = sorted(key_counts.items(), key=lambda x: -x[1])[:limit]

        print("  {} ({:,} unique keys):".format(source, len(key_counts)))
        print("  {:55s}  {:>7s}".format("KEY", "REFS"))
        print("  " + "-" * 65)

        for key, count in sorted_keys:
            display_key = key[:55] if len(key) <= 55 else key[:52] + "..."
            print("  {:55s}  {:>7,}".format(display_key, count))

        remaining = len(key_counts) - limit
        if remaining > 0:
            print("  ... and {:,} more keys".format(remaining))
        print("")

    # Overall top keys
    top_overall = sorted(all_keys, key=lambda x: -x[1])[:limit]
    if len(all_keys) > 5:
        print("  TOP KEYS OVERALL ({:,} unique):".format(len(all_keys)))
        print("  {:>5s}  {:50s}  {:s}".format("REFS", "KEY", "SOURCE"))
        print("  " + "-" * 75)
        for key, count, source in top_overall:
            display_key = key[:50] if len(key) <= 50 else key[:47] + "..."
            display_src = source[:20]
            print("  {:>5,}  {:50s}  {}".format(count, display_key, display_src))
        print("")

    print("")


# ---------------------------------------------------------------------------
# resources-usage — how resources of a module are used
# ---------------------------------------------------------------------------

def cmd_resources_usage(base_dir, module_name, limit=50):
    """Show non-Java resources in a module and where they're referenced."""
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: Could not load class-index.")
        return

    ci_classes = ci_data.get("classes", {})
    source_root = ci_data.get("_meta", {}).get("source", "")

    # Find module's source root to locate extracted/ resources
    organized_root = None
    for cname, entries in ci_classes.items():
        for entry in entries:
            mod = entry.get("module", "")
            if mod == module_name:
                rel_path = entry.get("path", "")
                if rel_path and source_root:
                    full = os.path.join(source_root, rel_path).replace("\\", "/")
                    parts = full.split("/")
                    try:
                        vf_idx = parts.index("vineflower")
                        organized_root = "/".join(parts[:vf_idx])
                    except ValueError:
                        pass
                if organized_root:
                    break
        if organized_root:
            break

    if not organized_root:
        print("")
        print("  Module '{}' not found or has no source files.".format(module_name))
        print("")
        return

    # Find resources in extracted/ directory
    extracted_dir = os.path.join(organized_root, "extracted")
    resources = []

    if os.path.isdir(extracted_dir):
        for root, dirs, files in os.walk(extracted_dir):
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                # Skip compiled classes
                if ext in (".class", ".java"):
                    continue
                rel_path = os.path.relpath(
                    os.path.join(root, fname), extracted_dir
                ).replace("\\", "/")
                resources.append({
                    "name": fname,
                    "path": rel_path,
                    "ext": ext,
                    "size": os.path.getsize(os.path.join(root, fname)),
                })

    print("")
    print("  RESOURCES USAGE: {}".format(module_name))
    print("  " + "=" * 70)
    print("  Module root:     {}".format(organized_root))
    print("  Resources found: {:,}".format(len(resources)))
    print("")

    if not resources:
        print("  No non-Java resources found in extracted/ directory.")
        print("")
        return

    # Group by extension
    by_ext = defaultdict(list)
    for r in resources:
        by_ext[r["ext"]].append(r)

    print("  RESOURCE TYPES:")
    print("  {:10s}  {:>5s}  {:>10s}".format("EXT", "COUNT", "TOTAL SIZE"))
    print("  " + "-" * 30)
    for ext in sorted(by_ext.keys()):
        items = by_ext[ext]
        total_size = sum(r["size"] for r in items)
        size_str = _format_size(total_size)
        print("  {:10s}  {:>5,}  {:>10s}".format(ext or "(none)", len(items), size_str))
    print("")

    # Search for resource references in source code
    # Use token-index.db for fast lookups of resource filenames
    conn = _get_db(base_dir)
    resource_refs = {}

    # Key resource names to search for (skip very generic names)
    searchable = []
    for r in resources:
        name = r["name"]
        # Skip generic names unlikely to be meaningful
        if name in ("MANIFEST.MF", "pom.xml", "module-include.xml",
                     "module-permissions.xml", "module.lexicon"):
            continue
        # Skip binary resources (images etc) — focus on config files
        if r["ext"] in (".png", ".gif", ".jpg", ".jpeg", ".ico", ".bmp",
                         ".jar", ".zip", ".so", ".dll"):
            continue
        searchable.append(r)

    if conn and searchable:
        print("  RESOURCE REFERENCES IN CODE:")
        print("  {:30s}  {:>5s}  {:s}".format("RESOURCE", "REFS", "REFERENCING CLASSES"))
        print("  " + "-" * 80)

        cur = conn.cursor()
        found_count = 0

        for r in sorted(searchable, key=lambda x: x["name"]):
            name = r["name"]
            # Search for the filename as a token
            base_name = os.path.splitext(name)[0]

            # Search by full filename first
            cur.execute("""
                SELECT DISTINCT f.class_name, f.module
                FROM postings p
                JOIN files f ON p.file_id = f.id
                WHERE p.token = ?
                LIMIT 100
            """, (name,))
            rows = cur.fetchall()

            # Also try base name for .properties files
            if not rows and r["ext"] in (".properties", ".xml", ".cfg"):
                cur.execute("""
                    SELECT DISTINCT f.class_name, f.module
                    FROM postings p
                    JOIN files f ON p.file_id = f.id
                    WHERE p.token = ?
                    LIMIT 100
                """, (base_name,))
                rows = cur.fetchall()

            if rows:
                found_count += 1
                # Show classes referencing this resource
                classes = [r[0] for r in rows[:5]]
                more = len(rows) - 5 if len(rows) > 5 else 0
                classes_str = ", ".join(classes)
                if more > 0:
                    classes_str += " +{}".format(more)
                print("  {:30s}  {:>5,}  {}".format(
                    name[:30], len(rows), classes_str))

                if found_count >= limit:
                    break

        if found_count == 0:
            print("  (no direct token references found for resources)")
        print("")

    # List key resources
    key_resources = [r for r in resources
                     if r["ext"] in (".properties", ".xml", ".cfg", ".json",
                                      ".yaml", ".yml", ".csv", ".txt", ".lexicon")]
    if key_resources:
        print("  CONFIG/DATA RESOURCES ({:,}):".format(len(key_resources)))
        shown = 0
        for r in sorted(key_resources, key=lambda x: -x["size"])[:limit]:
            size_str = _format_size(r["size"])
            print("    {:45s}  {:>8s}".format(r["path"][:45], size_str))
            shown += 1
        if len(key_resources) > limit:
            print("    ... and {:,} more".format(len(key_resources) - limit))
        print("")

    print("")


def _format_size(size_bytes):
    """Format byte size to human-readable string."""
    if size_bytes < 1024:
        return "{} B".format(size_bytes)
    elif size_bytes < 1024 * 1024:
        return "{:.1f} KB".format(size_bytes / 1024)
    else:
        return "{:.1f} MB".format(size_bytes / (1024 * 1024))
