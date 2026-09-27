"""
Patch workflow commands for Module Navigator (Phase 10).

Assists the complete patching process:
  find -> analyze -> extract -> patch -> rebuild -> deploy

Commands:
  patch-target <query>          Find patchable classes by natural language query
  patch-plan <class>            Generate a complete patch plan for a class
  extract <module> <class>      Extract class to working directory for editing
"""

import json
import os
import re
import shutil
import sys


# ---------------------------------------------------------------------------
# Index loading (uses caches from REPL when available)
# ---------------------------------------------------------------------------

def _load_json(base_dir, filename):
    """Load a JSON index file."""
    path = os.path.join(base_dir, "indexes", filename)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_class(classes, class_name):
    """Resolve class name to (name, entry) or (None, None)."""
    if class_name in classes:
        entries = classes[class_name]
        for e in entries:
            if e["outer_class"] is None:
                return class_name, e
        return class_name, entries[0]
    name_lower = class_name.lower()
    for k, entries in classes.items():
        if k.lower() == name_lower:
            for e in entries:
                if e["outer_class"] is None:
                    return k, e
            return k, entries[0]
    return None, None


def _get_source_root(ci_data):
    """Get the source root path from class-index metadata."""
    return ci_data.get("_meta", {}).get("source", "")


def _read_source_lines(filepath):
    """Read source file lines, return list of strings."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except (IOError, OSError):
        return []


# ---------------------------------------------------------------------------
# patch-target: fuzzy search for patchable classes
# ---------------------------------------------------------------------------

# Keyword maps for natural language -> regex patterns
_KEYWORD_PATTERNS = {
    # Size/dimension related
    "size": [r"setPreferredSize", r"setMinimumSize", r"setMaximumSize", r"setBounds", r"Dimension"],
    "height": [r"setPreferredSize", r"setMinimumSize", r"setBounds", r"height"],
    "width": [r"setPreferredSize", r"setMinimumSize", r"setBounds", r"width"],
    "dimension": [r"setPreferredSize", r"setMinimumSize", r"setMaximumSize", r"Dimension"],
    "resize": [r"setPreferredSize", r"setMinimumSize", r"setMaximumSize"],

    # Dialog related
    "dialog": [r"Dialog", r"openInDialog", r"showDialog", r"BOptionDialog"],
    "popup": [r"Dialog", r"openInDialog", r"showDialog", r"popup"],
    "window": [r"Dialog", r"Frame", r"Window", r"setTitle"],
    "modal": [r"Dialog", r"modal", r"BOptionDialog"],

    # Color related
    "color": [r"new Color", r"setBackground", r"setForeground", r"Color\."],
    "background": [r"setBackground", r"Background"],
    "foreground": [r"setForeground", r"Foreground"],
    "theme": [r"Color", r"Font", r"setBackground", r"setForeground"],

    # Font related
    "font": [r"new Font", r"setFont", r"Font"],

    # Timeout/timing related
    "timeout": [r"timeout", r"TIMEOUT", r"Timeout", r"millis", r"delay"],
    "timer": [r"Timer", r"timer", r"setTimeout", r"schedule"],
    "delay": [r"delay", r"sleep", r"Thread\.sleep", r"millis"],
    "interval": [r"interval", r"period", r"poll", r"schedule"],

    # Alarm related
    "alarm": [r"[Aa]larm", r"BAlarm"],
    "alert": [r"[Aa]lert", r"[Aa]larm", r"notify"],

    # Link related
    "link": [r"[Ll]ink", r"BLink"],

    # Icon related
    "icon": [r"BImage", r"ImageIcon", r"icon", r"Icon"],

    # Layout related
    "layout": [r"Layout", r"setPreferredSize", r"setBounds", r"GridBag"],
    "margin": [r"margin", r"insets", r"Insets", r"padding"],
    "padding": [r"padding", r"insets", r"Insets", r"margin"],

    # Service related
    "service": [r"Service", r"BService"],

    # Network related
    "port": [r"port", r"Port", r"PORT"],
    "host": [r"host", r"Host", r"hostname"],
    "url": [r"url", r"URL", r"Url"],
}


def _tokenize_query(query):
    """Break query into lowercase tokens."""
    return [t.lower() for t in re.split(r'\s+', query.strip()) if t]


def _query_to_patterns(tokens):
    """Convert query tokens to regex patterns using keyword map."""
    patterns = []
    unmatched = []
    for token in tokens:
        if token in _KEYWORD_PATTERNS:
            patterns.extend(_KEYWORD_PATTERNS[token])
        else:
            # Use as a direct regex pattern (case-insensitive)
            patterns.append(token)
            unmatched.append(token)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique, unmatched


def _search_class_index(ci_data, tokens):
    """Search class names matching query tokens. Returns list of (name, entry, score)."""
    classes = ci_data.get("classes", {})
    results = []
    for class_name, entries in classes.items():
        name_lower = class_name.lower()
        score = 0
        for token in tokens:
            if token in name_lower:
                score += 2
        if score > 0:
            for e in entries:
                if e["outer_class"] is None:
                    results.append((class_name, e, score))
                    break
    return results


def _search_swing_index(si_data, tokens, patterns):
    """Search swing-index for UI-related matches. Returns list of (class_name, details, score)."""
    if not si_data:
        return []
    classes = si_data.get("classes", {})
    results = []

    # Check if query is UI-related
    ui_keywords = {"size", "height", "width", "dimension", "dialog", "color",
                   "font", "icon", "resize", "layout", "popup", "window", "modal",
                   "background", "foreground", "theme"}
    is_ui_query = any(t in ui_keywords for t in tokens)

    for class_name, val in classes.items():
        rec = val[0] if isinstance(val, list) else val
        score = 0
        details = []

        name_lower = class_name.lower()
        for token in tokens:
            if token in name_lower:
                score += 2

        if is_ui_query:
            # Check dimensions
            if rec.get("dimensions") and any(t in {"size", "height", "width", "dimension", "resize", "layout"} for t in tokens):
                score += 3
                for dim in rec["dimensions"]:
                    details.append("Line {:>5}: {}({}, {})".format(
                        dim["line"], dim["method"], dim["w"], dim["h"]))

            # Check dialogs
            if rec.get("dialog_methods") and any(t in {"dialog", "popup", "window", "modal"} for t in tokens):
                score += 2
                details.append("Dialog methods: {}".format(", ".join(rec["dialog_methods"])))

            # Check colors
            if rec.get("colors") and any(t in {"color", "background", "foreground", "theme"} for t in tokens):
                score += 2
                details.append("{} color(s)".format(len(rec["colors"])))

            # Check fonts
            if rec.get("fonts") and any(t in {"font", "theme"} for t in tokens):
                score += 2
                details.append("{} font(s)".format(len(rec["fonts"])))

            # Check titles
            if rec.get("titles"):
                for title in rec["titles"]:
                    title_lower = title.lower()
                    for token in tokens:
                        if token in title_lower:
                            score += 3
                            details.append('Title: "{}"'.format(title))

        if score > 0:
            results.append((class_name, rec.get("module", ""), details, score))

    return results


def _search_source_grep(ci_data, patterns, limit=5, priority_classes=None):
    """Grep source files for patterns. Returns list of (class_name, module, matches, score).

    priority_classes: set of class names to check FIRST (from name/UI matches).
    This ensures relevant classes get grep-checked before hitting the limit.
    """
    source_root = _get_source_root(ci_data)
    if not source_root or not os.path.isdir(source_root):
        return []

    classes = ci_data.get("classes", {})
    results = {}  # class_name -> {module, matches[], score}
    priority_set = priority_classes or set()

    # Compile patterns
    compiled = []
    for p in patterns:
        try:
            compiled.append(re.compile(p, re.IGNORECASE))
        except re.error:
            compiled.append(re.compile(re.escape(p), re.IGNORECASE))

    def _scan_class(class_name, entry):
        """Scan a single class file. Returns (score, match_lines) or None."""
        if entry["outer_class"] is not None:
            return None
        if entry.get("zkm"):
            return None

        filepath = os.path.join(source_root, entry["path"])
        if not os.path.isfile(filepath):
            return None

        lines = _read_source_lines(filepath)
        if not lines:
            return None

        match_count = 0
        match_lines = []
        distinct_pats = set()

        for i, line in enumerate(lines, 1):
            for pi, pat in enumerate(compiled):
                if pat.search(line):
                    match_count += 1
                    distinct_pats.add(pi)
                    stripped = line.rstrip()
                    if len(stripped) > 120:
                        stripped = stripped[:117] + "..."
                    match_lines.append("  Line {:>5}: {}".format(i, stripped))
                    break  # one match per line

        if match_count > 0:
            # Cap score per class + diversity bonus
            capped = min(match_count, 10)
            diversity = len(distinct_pats) * 2
            return (capped + diversity, match_lines[:5])
        return None

    # Phase 1: Check priority classes FIRST (from name/UI matches)
    for cname in priority_set:
        if cname in classes:
            for entry in classes[cname]:
                result = _scan_class(cname, entry)
                if result:
                    score, matches = result
                    if cname not in results or results[cname]["score"] < score:
                        results[cname] = {
                            "module": entry["module"],
                            "matches": matches,
                            "score": score,
                            "entry": entry,
                        }
                    break

    # Phase 2: Scan remaining classes (with limit)
    count = 0
    for class_name, entries in classes.items():
        if class_name in priority_set:
            continue  # already scanned
        for entry in entries:
            result = _scan_class(class_name, entry)
            if result:
                score, matches = result
                if class_name not in results or results[class_name]["score"] < score:
                    results[class_name] = {
                        "module": entry["module"],
                        "matches": matches,
                        "score": score,
                        "entry": entry,
                    }
                count += 1
                if count >= 500:
                    break
                break
        if count >= 500:
            break

    return [(k, v["module"], v["matches"], v["score"], v["entry"])
            for k, v in sorted(results.items(), key=lambda x: -x[1]["score"])][:limit * 3]


def cmd_patch_target(base_dir, query, limit=20, patches_dir=None):
    """Find patchable classes based on natural language query.

    Combines results from: class-index (name match), swing-index (UI match),
    and source grep (content match) into a ranked list.
    """
    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    tokens = _tokenize_query(query)
    if not tokens:
        print("  Usage: patch-target <query>")
        print("  Example: patch-target \"Link dialog height\"")
        return

    patterns, unmatched = _query_to_patterns(tokens)

    print("")
    print("  " + "=" * 65)
    print("  PATCH TARGET SEARCH: \"{}\"".format(query))
    print("  " + "=" * 65)
    print("")
    print("  Query tokens:  {}".format(", ".join(tokens)))
    print("  Search patterns: {}".format(", ".join(patterns[:10])))
    if len(patterns) > 10:
        print("                   ... and {} more".format(len(patterns) - 10))
    print("")

    # --- Channel 1: Class name matching ---
    name_results = _search_class_index(ci_data, tokens)

    # --- Channel 2: Swing/UI index matching ---
    si_data = _load_json(base_dir, "swing-index.json")
    ui_results = _search_swing_index(si_data, tokens, patterns)

    # Collect priority classes (from name + UI channels) for targeted grep
    priority_classes = set()
    for class_name, entry, score in name_results:
        priority_classes.add(class_name)
    for class_name, module, details, score in ui_results:
        priority_classes.add(class_name)

    # --- Channel 3: Source grep (most expensive, do last) ---
    sys.stdout.write("  Searching source files...")
    sys.stdout.flush()
    grep_results = _search_source_grep(ci_data, patterns, limit=limit,
                                        priority_classes=priority_classes)
    print(" done ({} matches)".format(len(grep_results)))
    print("")

    # --- Merge and rank ---
    merged = {}  # class_name -> {module, score, sources[], details[]}

    for class_name, entry, score in name_results:
        key = class_name
        if key not in merged:
            merged[key] = {"module": entry["module"], "score": 0,
                           "sources": [], "details": [], "entry": entry}
        merged[key]["score"] += score
        merged[key]["sources"].append("name")

    for class_name, module, details, score in ui_results:
        key = class_name
        if key not in merged:
            # Need to look up entry
            resolved, entry = _resolve_class(ci_data.get("classes", {}), class_name)
            if not entry:
                continue
            merged[key] = {"module": module or entry["module"], "score": 0,
                           "sources": [], "details": [], "entry": entry}
        merged[key]["score"] += score * 2  # UI matches are highly relevant for patching
        if "ui" not in merged[key]["sources"]:
            merged[key]["sources"].append("ui")
        merged[key]["details"].extend(details)

    for class_name, module, matches, score, entry in grep_results:
        key = class_name
        if key not in merged:
            merged[key] = {"module": module, "score": 0,
                           "sources": [], "details": [], "entry": entry}
        merged[key]["score"] += score
        if "source" not in merged[key]["sources"]:
            merged[key]["sources"].append("source")
        merged[key]["details"].extend(matches)

    # Multi-channel bonus: classes found by multiple sources rank higher
    for key, info in merged.items():
        channel_count = len(info["sources"])
        if channel_count >= 3:
            info["score"] += 15  # found by name + UI + source
        elif channel_count >= 2:
            info["score"] += 8   # found by 2 channels

    # Sort by score descending
    ranked = sorted(merged.items(), key=lambda x: -x[1]["score"])[:limit]

    if not ranked:
        print("  No matches found for \"{}\"".format(query))
        print("  Try broader terms or check: search \"*{}*\"".format(tokens[0] if tokens else ""))
        return

    print("  RESULTS ({} candidates, showing top {})".format(len(merged), min(limit, len(ranked))))
    print("  " + "-" * 65)

    for i, (class_name, info) in enumerate(ranked, 1):
        source_tags = " ".join("[{}]".format(s) for s in info["sources"])
        print("")
        print("  {:>2}. {} (score: {}) {}".format(
            i, class_name, info["score"], source_tags))
        print("      Module: {}  |  Lines: {:,}".format(
            info["module"], info["entry"].get("lines", 0)))
        if info.get("entry", {}).get("package"):
            print("      Package: {}".format(info["entry"]["package"]))

        # Show details (max 3 per result)
        for detail in info["details"][:3]:
            print("      {}".format(detail))
        if len(info["details"]) > 3:
            print("      ... and {} more".format(len(info["details"]) - 3))

    print("")
    print("  Next steps:")
    if ranked:
        top_class = ranked[0][0]
        print("    patch-plan {}".format(top_class))
        print("    profile {}".format(top_class))
        print("    source {} --code".format(top_class))
    print("")


# ---------------------------------------------------------------------------
# patch-plan: generate a complete patch plan for a class
# ---------------------------------------------------------------------------

def cmd_patch_plan(base_dir, class_name, patches_dir=None):
    """Generate a complete patch plan for a class."""
    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    classes = ci_data.get("classes", {})
    resolved, entry = _resolve_class(classes, class_name)

    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        print("  Try: search '*{}*'".format(class_name))
        return

    source_root = _get_source_root(ci_data)
    filepath = os.path.join(source_root, entry["path"]) if source_root else ""
    source_lines = _read_source_lines(filepath) if filepath else []

    if not patches_dir:
        patches_dir = os.path.join(base_dir, "patches")

    # Determine NIAGARA_HOME from base_dir (parent of module-navigator)
    niagara_home = os.path.dirname(base_dir)
    jar_name = entry["module"].split("/")[-1] if "/" in entry["module"] else entry["module"]
    if not jar_name.endswith(".jar"):
        jar_name += ".jar"
    jar_path = os.path.join(niagara_home, "modules", jar_name)

    # Full class path for recompilation
    package = entry.get("package", "")
    class_file_rel = ""
    if package:
        class_file_rel = package.replace(".", os.sep) + os.sep + resolved + ".class"

    print("")
    print("  " + "=" * 65)
    print("  PATCH PLAN: {}".format(resolved))
    print("  " + "=" * 65)

    # --- Section 1: Target identification ---
    print("")
    print("  1. TARGET:")
    print("     Class:    {}".format(resolved))
    print("     Package:  {}".format(entry.get("package", "")))
    print("     Module:   {}".format(entry["module"]))
    print("     Kind:     {}".format(entry["kind"]))
    if entry.get("extends"):
        print("     Extends:  {}".format(entry["extends"]))
    if entry.get("implements"):
        print("     Implements: {}".format(", ".join(entry["implements"])))
    print("     Lines:    {:,}".format(entry.get("lines", 0)))
    print("     ZKM:      {}".format("YES (may need deobfuscation)" if entry.get("zkm") else "no"))

    # --- Section 2: Source location ---
    print("")
    print("  2. SOURCE FILE:")
    print("     Decompiled: {}".format(entry["path"]))
    if filepath and os.path.isfile(filepath):
        size_bytes = os.path.getsize(filepath)
        print("     Full path:  {}".format(filepath))
        print("     Size:       {:,} bytes".format(size_bytes))
    else:
        print("     (source file not found on disk)")

    # --- Section 3: Patchable elements ---
    print("")
    print("  3. PATCHABLE ELEMENTS:")

    patchable = []

    if source_lines:
        # Find hardcoded sizes
        size_pat = re.compile(
            r'(setPreferredSize|setMinimumSize|setMaximumSize|setBounds)\s*\('
            r'([^)]+)\)')
        for i, line in enumerate(source_lines, 1):
            m = size_pat.search(line)
            if m:
                patchable.append(("SIZE", i, m.group(0).strip(), line.strip()))

        # Find hardcoded colors
        color_pat = re.compile(r'new\s+Color\s*\([^)]+\)')
        for i, line in enumerate(source_lines, 1):
            m = color_pat.search(line)
            if m:
                patchable.append(("COLOR", i, m.group(0).strip(), line.strip()))

        # Find hardcoded fonts
        font_pat = re.compile(r'new\s+Font\s*\([^)]+\)')
        for i, line in enumerate(source_lines, 1):
            m = font_pat.search(line)
            if m:
                patchable.append(("FONT", i, m.group(0).strip(), line.strip()))

        # Find hardcoded strings (titles, labels)
        title_pat = re.compile(r'setTitle\s*\(\s*"([^"]+)"\s*\)')
        for i, line in enumerate(source_lines, 1):
            m = title_pat.search(line)
            if m:
                patchable.append(("TITLE", i, m.group(0).strip(), line.strip()))

        # Find hardcoded timeouts/delays
        timeout_pat = re.compile(
            r'(?:timeout|TIMEOUT|Timeout|delay|DELAY|millis|sleep)\s*[=(]\s*(\d+)')
        for i, line in enumerate(source_lines, 1):
            m = timeout_pat.search(line)
            if m:
                patchable.append(("TIMEOUT", i, m.group(0).strip(), line.strip()))

        # Find hardcoded numeric constants (potential config values)
        dimension_pat = re.compile(r'new\s+Dimension\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)')
        for i, line in enumerate(source_lines, 1):
            m = dimension_pat.search(line)
            if m:
                patchable.append(("DIMENSION", i, m.group(0).strip(), line.strip()))

    # Also check swing-index for richer UI info
    si_data = _load_json(base_dir, "swing-index.json")
    ui_rec = None
    if si_data:
        si_classes = si_data.get("classes", {})
        if resolved in si_classes:
            val = si_classes[resolved]
            ui_rec = val[0] if isinstance(val, list) else val
        else:
            for k, val in si_classes.items():
                if k.lower() == resolved.lower():
                    ui_rec = val[0] if isinstance(val, list) else val
                    break

    if patchable:
        for ptype, line_no, match, full_line in patchable:
            print("     [{:>9}] Line {:>5}: {}".format(ptype, line_no, match))
    elif ui_rec:
        if ui_rec.get("dimensions"):
            for dim in ui_rec["dimensions"]:
                print("     [{:>9}] Line {:>5}: {}({}, {})".format(
                    "SIZE", dim["line"], dim["method"], dim["w"], dim["h"]))
        if ui_rec.get("colors"):
            for col in ui_rec["colors"][:5]:
                print("     [{:>9}] Line {:>5}: {} -> {}".format(
                    "COLOR", col["line"], col["target"], col["value"]))
        if not ui_rec.get("dimensions") and not ui_rec.get("colors"):
            print("     (no obvious patchable elements found via source scan)")
    else:
        print("     (no obvious patchable elements found via source scan)")
        print("     Tip: use 'source {} --code' to inspect manually".format(resolved))

    # --- Section 4: JAR information ---
    print("")
    print("  4. JAR TO PATCH:")
    print("     JAR name:   {}".format(jar_name))
    print("     JAR path:   {}".format(jar_path))
    if os.path.isfile(jar_path):
        jar_size = os.path.getsize(jar_path)
        print("     JAR size:   {:,} bytes ({:.1f} MB)".format(
            jar_size, jar_size / (1024 * 1024)))
        print("     JAR exists: YES")
    else:
        print("     JAR exists: NO (check path)")
    print("     Class path: {}".format(class_file_rel))

    # --- Section 5: Dependencies ---
    print("")
    print("  5. DEPENDENCIES:")
    xr_data = _load_json(base_dir, "xref-index.json")
    if xr_data:
        class_imports = xr_data.get("class_imports", {})
        fqn = "{}.{}".format(package, resolved) if package else resolved

        # Find imports for this class (values are lists of class names)
        imports = class_imports.get(fqn, [])
        if not imports:
            # Try by simple name
            for key, val in class_imports.items():
                if key.endswith("." + resolved):
                    imports = val if isinstance(val, list) else []
                    break

        if imports and isinstance(imports, list):
            niagara_imports = [i for i in imports if isinstance(i, str) and
                               (i.startswith("javax.baja.") or i.startswith("com.tridium."))]
            print("     Niagara imports: {}".format(len(niagara_imports)))
            for imp in niagara_imports[:10]:
                print("       {}".format(imp))
            if len(niagara_imports) > 10:
                print("       ... and {} more".format(len(niagara_imports) - 10))
        else:
            print("     (import data not available for this class)")

        # Module-level deps (values are lists of module names)
        module_deps = xr_data.get("module_deps", {})
        mod_key = entry["module"]
        deps = module_deps.get(mod_key, [])
        if isinstance(deps, list) and deps:
            print("     Module deps: {} ({})".format(
                len(deps), ", ".join(deps[:8])))
            if len(deps) > 8:
                print("                  ... and {} more".format(len(deps) - 8))
    else:
        print("     (xref-index.json not available)")

    # --- Section 6: Step-by-step instructions ---
    extract_dir = os.path.join(patches_dir, resolved)
    java_filename = resolved + ".java"

    print("")
    print("  6. PATCH STEPS:")
    print("")
    print("     Step 1 - Extract source:")
    print("       extract {} {}".format(entry["module"], resolved))
    print("       (or manually copy from decompiled source)")
    print("")
    print("     Step 2 - Edit the .java file:")
    print("       {}".format(os.path.join(extract_dir, "src",
                              package.replace(".", os.sep), java_filename)
                              if package else os.path.join(extract_dir, "src", java_filename)))
    if patchable:
        print("")
        print("       Suggested edits:")
        for ptype, line_no, match, full_line in patchable:
            print("         Line {}: change {}".format(line_no, match))
    print("")
    print("     Step 3 - Recompile:")
    print("       Run: {}".format(os.path.join(extract_dir, "recompile.cmd")))
    print("")
    print("     Step 4 - Repack JAR:")
    print("       Run: {}".format(os.path.join(extract_dir, "repack.cmd")))
    print("")
    print("     Step 5 - Sign JAR:")
    print("       jarsigner -keystore SEJOFA_C.jks {} SEJOFA_C".format(jar_name))
    print("")
    print("     Step 6 - Deploy:")
    print("       1. Stop Niagara station")
    print("       2. Copy {} to %NIAGARA_HOME%\\modules\\".format(jar_name))
    print("       3. Start station")
    print("")


# ---------------------------------------------------------------------------
# extract: copy class to working directory for editing
# ---------------------------------------------------------------------------

def cmd_extract(base_dir, module_name, class_name, patches_dir=None):
    """Extract a decompiled class to a working directory for patching."""
    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    classes = ci_data.get("classes", {})
    resolved, entry = _resolve_class(classes, class_name)

    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        print("  Try: search '*{}*'".format(class_name))
        return

    # Verify module matches (if specified and doesn't match)
    if module_name and entry["module"] != module_name:
        # Try to find the entry in the specified module
        found = False
        if class_name in classes:
            for e in classes[class_name]:
                if e["module"] == module_name:
                    entry = e
                    found = True
                    break
        if not found:
            print("  WARNING: {} is in module '{}', not '{}'.".format(
                resolved, entry["module"], module_name))
            print("  Using module '{}' instead.".format(entry["module"]))

    source_root = _get_source_root(ci_data)
    src_path = os.path.join(source_root, entry["path"]) if source_root else ""

    if not src_path or not os.path.isfile(src_path):
        print("  ERROR: Source file not found: {}".format(src_path))
        return

    if not patches_dir:
        patches_dir = os.path.join(base_dir, "patches")

    # Determine paths
    package = entry.get("package", "")
    java_filename = resolved + ".java"
    package_path = package.replace(".", os.sep) if package else ""
    class_file_rel = os.path.join(package_path, resolved + ".class") if package else resolved + ".class"

    # Determine NIAGARA_HOME
    niagara_home = os.path.dirname(base_dir)
    jar_module = entry["module"]
    jar_name = jar_module
    if not jar_name.endswith(".jar"):
        jar_name += ".jar"
    jar_path = os.path.join(niagara_home, "modules", jar_name)

    # Create extract directory structure
    extract_dir = os.path.join(patches_dir, resolved)
    src_dir = os.path.join(extract_dir, "src", package_path) if package_path else os.path.join(extract_dir, "src")
    build_dir = os.path.join(extract_dir, "build")

    print("")
    print("  " + "=" * 65)
    print("  EXTRACT: {} from {}".format(resolved, entry["module"]))
    print("  " + "=" * 65)
    print("")

    # Create directories
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)

    # Copy source file
    dest_java = os.path.join(src_dir, java_filename)
    shutil.copy2(src_path, dest_java)
    print("  Copied: {} -> {}".format(java_filename, dest_java))

    # Also check for inner class source files in same directory
    src_parent = os.path.dirname(src_path)
    inner_count = 0
    if entry.get("inner_classes"):
        for inner in entry["inner_classes"]:
            inner_file = resolved + "$" + inner + ".java"
            inner_src = os.path.join(src_parent, inner_file)
            if os.path.isfile(inner_src):
                inner_dest = os.path.join(src_dir, inner_file)
                shutil.copy2(inner_src, inner_dest)
                inner_count += 1

    if inner_count > 0:
        print("  Copied: {} inner class file(s)".format(inner_count))

    # Generate recompile.cmd
    recompile_cmd = os.path.join(extract_dir, "recompile.cmd")
    modules_dir = os.path.join(niagara_home, "modules")

    # Escape backslashes for the .cmd file
    cmd_content = '@echo off\r\n'
    cmd_content += 'REM Recompile {} for patching\r\n'.format(resolved)
    cmd_content += 'REM Generated by Module Navigator - Phase 10\r\n'
    cmd_content += 'REM\r\n'
    cmd_content += 'REM Prerequisites:\r\n'
    cmd_content += 'REM   - JDK 8 (javac) must be on PATH\r\n'
    cmd_content += 'REM   - NIAGARA_HOME must be set or modules dir must exist\r\n'
    cmd_content += '\r\n'
    cmd_content += 'set MODULES_DIR={}\r\n'.format(modules_dir)
    cmd_content += 'set SRC_DIR=%~dp0src\r\n'
    cmd_content += 'set BUILD_DIR=%~dp0build\r\n'
    cmd_content += '\r\n'
    cmd_content += 'echo Compiling {}...\r\n'.format(java_filename)
    cmd_content += 'javac -cp "%MODULES_DIR%\\*" -source 1.8 -target 1.8 '
    cmd_content += '-d "%BUILD_DIR%" '

    # Include all .java files in src dir
    cmd_content += '"%SRC_DIR%\\{}\\{}"\r\n'.format(
        package_path.replace("/", "\\"), java_filename) if package_path else '"%SRC_DIR%\\{}"\r\n'.format(java_filename)

    cmd_content += '\r\n'
    cmd_content += 'if %ERRORLEVEL% neq 0 (\r\n'
    cmd_content += '    echo COMPILATION FAILED\r\n'
    cmd_content += '    pause\r\n'
    cmd_content += '    exit /b 1\r\n'
    cmd_content += ')\r\n'
    cmd_content += '\r\n'
    cmd_content += 'echo Compilation successful.\r\n'
    cmd_content += 'echo Output: %BUILD_DIR%\r\n'
    cmd_content += 'echo.\r\n'
    cmd_content += 'echo Next: run repack.cmd to update the JAR\r\n'
    cmd_content += 'pause\r\n'

    with open(recompile_cmd, "w", encoding="utf-8") as f:
        f.write(cmd_content)
    print("  Created: recompile.cmd")

    # Generate repack.cmd
    repack_cmd = os.path.join(extract_dir, "repack.cmd")

    repack_content = '@echo off\r\n'
    repack_content += 'REM Repack {} into {}\r\n'.format(resolved, jar_name)
    repack_content += 'REM Generated by Module Navigator - Phase 10\r\n'
    repack_content += 'REM\r\n'
    repack_content += 'REM IMPORTANT: Make a backup of the original JAR first!\r\n'
    repack_content += '\r\n'
    repack_content += 'set JAR_PATH={}\r\n'.format(jar_path)
    repack_content += 'set BUILD_DIR=%~dp0build\r\n'
    repack_content += 'set BACKUP_DIR=%~dp0backup\r\n'
    repack_content += '\r\n'
    repack_content += 'REM Create backup\r\n'
    repack_content += 'if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"\r\n'
    repack_content += 'if not exist "%BACKUP_DIR%\\{}" (\r\n'.format(jar_name)
    repack_content += '    echo Creating backup of original JAR...\r\n'
    repack_content += '    copy "%JAR_PATH%" "%BACKUP_DIR%\\{}"\r\n'.format(jar_name)
    repack_content += '    echo Backup saved to: %BACKUP_DIR%\\{}\r\n'.format(jar_name)
    repack_content += ') else (\r\n'
    repack_content += '    echo Backup already exists: %BACKUP_DIR%\\{}\r\n'.format(jar_name)
    repack_content += ')\r\n'
    repack_content += '\r\n'
    repack_content += 'echo.\r\n'
    repack_content += 'echo Repacking {} into {}...\r\n'.format(resolved, jar_name)
    repack_content += 'jar uf "%JAR_PATH%" -C "%BUILD_DIR%" {}\r\n'.format(
        class_file_rel.replace(os.sep, "/"))

    # Also repack inner classes if any
    if entry.get("inner_classes"):
        for inner in entry["inner_classes"]:
            inner_class_rel = os.path.join(package_path, "{}${}.class".format(resolved, inner))
            inner_class_rel_fwd = inner_class_rel.replace(os.sep, "/")
            repack_content += 'if exist "%BUILD_DIR%\\{}" (\r\n'.format(inner_class_rel.replace("/", "\\"))
            repack_content += '    jar uf "%JAR_PATH%" -C "%BUILD_DIR%" {}\r\n'.format(inner_class_rel_fwd)
            repack_content += '    echo   Repacked: {}${}.class\r\n'.format(resolved, inner)
            repack_content += ')\r\n'

    repack_content += '\r\n'
    repack_content += 'if %ERRORLEVEL% neq 0 (\r\n'
    repack_content += '    echo REPACK FAILED\r\n'
    repack_content += '    pause\r\n'
    repack_content += '    exit /b 1\r\n'
    repack_content += ')\r\n'
    repack_content += '\r\n'
    repack_content += 'echo Repack successful.\r\n'
    repack_content += 'echo.\r\n'
    repack_content += 'echo Next steps:\r\n'
    repack_content += 'echo   1. Sign the JAR:  jarsigner -keystore SEJOFA_C.jks "%JAR_PATH%" SEJOFA_C\r\n'
    repack_content += 'echo   2. Stop the Niagara station\r\n'
    repack_content += 'echo   3. Copy {} to %%NIAGARA_HOME%%\\modules\\\r\n'.format(jar_name)
    repack_content += 'echo   4. Start the station\r\n'
    repack_content += 'pause\r\n'

    with open(repack_cmd, "w", encoding="utf-8") as f:
        f.write(repack_content)
    print("  Created: repack.cmd")

    # Generate README.txt with full instructions
    readme_path = os.path.join(extract_dir, "README.txt")
    readme_content = "PATCH: {}\r\n".format(resolved)
    readme_content += "=" * 60 + "\r\n"
    readme_content += "\r\n"
    readme_content += "Class:    {}\r\n".format(resolved)
    readme_content += "Package:  {}\r\n".format(package)
    readme_content += "Module:   {}\r\n".format(entry["module"])
    readme_content += "JAR:      {}\r\n".format(jar_name)
    readme_content += "Source:   {}\r\n".format(entry["path"])
    readme_content += "\r\n"
    readme_content += "WORKFLOW:\r\n"
    readme_content += "  1. Edit src\\{}\\{}\r\n".format(
        package_path.replace("/", "\\"), java_filename) if package_path else "  1. Edit src\\{}\r\n".format(java_filename)
    readme_content += "  2. Run recompile.cmd  (compiles .java -> .class)\r\n"
    readme_content += "  3. Run repack.cmd     (updates .class in JAR + backup)\r\n"
    readme_content += "  4. Sign: jarsigner -keystore SEJOFA_C.jks {} SEJOFA_C\r\n".format(jar_path)
    readme_content += "  5. Deploy: stop station, copy JAR, start station\r\n"
    readme_content += "\r\n"
    readme_content += "NOTES:\r\n"
    readme_content += "  - JDK 8 javac must be on PATH\r\n"
    readme_content += "  - The backup/ directory contains the original JAR\r\n"
    readme_content += "  - To revert: copy backup\\{} to modules\\\r\n".format(jar_name)
    readme_content += "  - Inner classes ({}$*.class) are repacked automatically\r\n".format(resolved)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("  Created: README.txt")

    # Summary
    print("")
    print("  EXTRACT COMPLETE:")
    print("    Directory:  {}".format(extract_dir))
    print("    Java file:  {}".format(os.path.relpath(dest_java, extract_dir)))
    if inner_count:
        print("    Inner classes: {}".format(inner_count))
    print("    Scripts:    recompile.cmd, repack.cmd")
    print("    README:     README.txt")
    print("")
    print("  Next steps:")
    print("    1. Edit the .java file")
    print("    2. Run recompile.cmd")
    print("    3. Run repack.cmd")
    print("    4. Sign and deploy")
    print("")
