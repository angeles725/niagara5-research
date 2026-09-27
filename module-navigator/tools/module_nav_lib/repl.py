"""
Interactive REPL for Module Navigator (Phase 8).

Features:
  - Pre-loads all indexes into memory
  - Supports all CLI commands
  - History (!N, !!)
  - Pipe (cmd | grep pattern, cmd | count)
  - Bookmarks (bookmark <name> <class>, bookmarks)
  - Focus by module (focus <module> / unfocus)
  - Help with complete command list
"""

import io
import json
import os
import sys

# Tab completion support
try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None


# ---------------------------------------------------------------------------
# Tab completion
# ---------------------------------------------------------------------------

class _ModuleNavCompleter(object):
    """Context-aware tab completer for Module Navigator REPL."""

    COMMANDS = [
        "inventory", "module", "modules", "class", "search", "package",
        "grep", "source", "snippet", "imports",
        "license-feature", "license-features",
        "ui", "hierarchy", "implementors",
        "xref", "deps", "method", "methods", "slots", "annotations",
        "stats", "profile", "full-profile", "cross-ref",
        "patch-target", "patch-plan", "extract",
        "orphans", "deps-graph", "api-surface", "security-audit",
        "strings", "resources", "trace-type", "version-diff",
        "callers", "callees", "call-chain", "hotspots",
        "fields", "field",
        "type-consumers", "type-producers", "type-flow",
        "module-calls", "module-api-usage", "coupling",
        "patterns", "pattern",
        "bog-trace", "bog-classes", "bog-coverage",
        "throws", "catches",
        "export", "token",
        "impact", "find",
        "deprecated", "deprecated-users", "deprecated-risk",
        "similar", "clones",
        "config-usage", "config-keys", "resources-usage",
        "serial", "serial-audit", "serial-conflicts",
        "thread-safety", "thread-scan",
        "lifecycle", "lifecycle-scan",
        "string-search", "string-constants",
        "ask",
        "servlets", "routes", "servlet",
        "ords", "ord-usage", "ord-flow",
        "topics", "subscribers", "pub-sub",
        "bql", "bql-tables", "bql-class",
        "permissions", "permission-flow", "credentials",
        "alarm-flow", "alarm-types", "alarm-trace",
        "cycles", "god-classes", "layer-check",
        "complexity", "complexity-scan", "metrics",
        "help", "quit", "exit", "q",
        "history", "bookmark", "bookmarks", "unbookmark", "focus", "unfocus",
        "unified", "compare",
        "integration-contract", "example-mine", "virtual-callers",
        "feature-brief",         "slot-validate", "slot-collision", "ord-validate",
        "resolve-audit", "driver-cleanup-audit", "resource-leak", "service-order",
        "dependency-audit", "module-health",
        "session",
    ]

    # Commands whose first positional arg is a class name
    CLASS_ARG_CMDS = frozenset([
        "class", "source", "snippet", "imports",
        "hierarchy", "implementors",
        "xref", "methods", "slots", "profile", "full-profile", "cross-ref",
        "patch-plan", "callers", "callees", "call-chain",
        "fields", "throws", "catches",
        "export", "impact", "similar", "serial",
        "deprecated-users", "bog-trace", "thread-safety", "lifecycle",
        "string-constants", "servlet", "ord-flow", "subscribers",
        "bql-class", "permission-flow", "alarm-trace", "complexity",
        "unbookmark", "compare",
        "integration-contract", "example-mine", "virtual-callers",
        "slot-validate",
    ])

    # Commands whose first positional arg is a module name
    MODULE_ARG_CMDS = frozenset([
        "module", "deps", "deps-graph", "api-surface",
        "module-calls", "module-api-usage", "coupling",
        "patterns", "resources", "resources-usage", "extract",
        "focus", "pub-sub", "layer-check", "metrics",
        "ord-validate", "service-order", "dependency-audit",
        "module-health",
    ])

    PATTERN_CATEGORIES = [
        "services", "drivers", "points", "views",
        "extensions", "enums", "structs",
    ]

    FEATURE_NAMES = [
        "alarms", "bql", "histories", "ords", "permissions",
        "points", "programs", "schedules", "servlets", "topics",
    ]

    UI_SUBCOMMANDS = [
        "dialogs", "sizes", "colors", "fonts", "class", "customizable",
    ]

    def __init__(self, class_names, module_names):
        self.class_names = class_names      # sorted list
        self.module_names = module_names    # sorted list
        self.matches = []

    def complete(self, text, state):
        if state == 0:
            try:
                line = readline.get_line_buffer()
                begin = readline.get_begidx()
            except Exception:
                line = text
                begin = 0
            self.matches = self._compute(line, text, begin)
        if state < len(self.matches):
            return self.matches[state]
        return None

    def _compute(self, line, text, begin):
        before = line[:begin]
        parts = before.strip().split() if before.strip() else []
        tl = text.lower()       # for command matching (case-insensitive)
        # Class/module names: use original text (case-sensitive)

        # --- completing command name (first word) ---
        if not parts:
            return [c + " " for c in self.COMMANDS if c.startswith(tl)]

        cmd = parts[0].lower()

        # --- after --module / -m flag → module names ---
        if parts[-1] in ("--module", "-m"):
            return self._match_modules(text)

        # --- after --class flag → class names ---
        if parts[-1] == "--class":
            return self._match_classes(text)

        arg_count = len(parts) - 1   # positional args already typed

        # --- first positional argument ---
        if arg_count == 0:
            if cmd in self.CLASS_ARG_CMDS:
                return self._match_classes(text)
            if cmd in self.MODULE_ARG_CMDS:
                return self._match_modules(text)
            if cmd == "pattern":
                return [c + " " for c in self.PATTERN_CATEGORIES
                        if c.startswith(tl)]
            if cmd == "ui":
                return [s + " " for s in self.UI_SUBCOMMANDS
                        if s.startswith(tl)]
            if cmd == "feature-brief":
                return [f + " " for f in self.FEATURE_NAMES
                        if f.startswith(tl)]

        # --- second positional argument ---
        if arg_count == 1:
            if cmd in ("module-calls", "coupling"):
                return self._match_modules(text)
            if cmd == "extract":
                return self._match_classes(text)
            if cmd == "ui" and parts[1] == "class":
                return self._match_classes(text)
            if cmd == "bookmark":
                return self._match_classes(text)

        return []

    # Binary-search prefix match for sorted lists (fast for 51K names)
    def _match_classes(self, prefix):
        return self._prefix_match(self.class_names, prefix, limit=50)

    def _match_modules(self, prefix):
        return self._prefix_match(self.module_names, prefix, limit=50)

    @staticmethod
    def _prefix_match(sorted_list, prefix, limit=50):
        if not prefix:
            return sorted_list[:limit]
        # bisect to find start position
        import bisect
        lo = bisect.bisect_left(sorted_list, prefix)
        results = []
        for i in range(lo, len(sorted_list)):
            item = sorted_list[i]
            if item.startswith(prefix):
                results.append(item)
                if len(results) >= limit:
                    break
            elif item > prefix and not item.startswith(prefix):
                break
        return results


def _setup_tab_completion(cache):
    """Set up readline tab completion from pre-loaded cache. Returns stats tuple or None."""
    if readline is None:
        return None

    # Build sorted completion lists from cache (case-sensitive, sorted)
    class_names = []
    if "class-index.json" in cache:
        class_names = sorted(cache["class-index.json"].get("classes", {}).keys())

    module_names = []
    if "module-inventory.json" in cache:
        module_names = sorted(cache["module-inventory.json"].get("modules", {}).keys())

    completer = _ModuleNavCompleter(class_names, module_names)

    try:
        readline.set_completer(completer.complete)
        readline.set_completer_delims(" \t\n")
        readline.parse_and_bind("tab: complete")
    except Exception:
        return None

    # Self-check: confirm the completer is actually wired. Some WSL/minimal
    # Python builds load readline but fail silently at set_completer time.
    try:
        if readline.get_completer() is not completer.complete:
            return None
    except Exception:
        pass

    return (len(class_names), len(module_names))


# ---------------------------------------------------------------------------
# Index pre-loading
# ---------------------------------------------------------------------------

def _preload_indexes(base_dir):
    """Pre-load all JSON indexes into memory. Returns dict of filename -> data."""
    index_dir = os.path.join(base_dir, "indexes")
    cache = {}
    if not os.path.isdir(index_dir):
        print("  WARNING: indexes/ directory not found.")
        return cache

    index_files = [
        "module-inventory.json",
        "class-index.json",
        "swing-index.json",
        "inheritance.json",
        "xref-index.json",
        "method-index.json",
        "annotations-index.json",
        "field-index.json",
    ]

    loaded = 0
    for fname in index_files:
        path = os.path.join(index_dir, fname)
        if os.path.isfile(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            sys.stdout.write("  Loading {} ({:.1f} MB)...".format(fname, size_mb))
            sys.stdout.flush()
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cache[fname] = json.load(f)
                loaded += 1
                print(" OK")
            except Exception as e:
                print(" ERROR: {}".format(e))

    print("  Loaded {} indexes into memory.".format(loaded))
    return cache


# ---------------------------------------------------------------------------
# Monkey-patch loading functions to use cached data
# ---------------------------------------------------------------------------

def _patch_loaders(cache):
    """Patch the load functions in all modules to use pre-loaded cache."""
    from module_nav_lib import inventory as inv_mod
    from module_nav_lib import class_search as cls_mod
    from module_nav_lib import grep_search as grep_mod
    from module_nav_lib import swing_search as swing_mod

    if "module-inventory.json" in cache:
        original_load_inv = inv_mod.load_inventory

        def cached_load_inventory(base_dir):
            return cache["module-inventory.json"]

        inv_mod.load_inventory = cached_load_inventory

        # Also patch grep_search's inventory loader
        def cached_grep_inv(base_dir):
            return cache["module-inventory.json"]

        grep_mod._inventory_cache = cache["module-inventory.json"]

    if "class-index.json" in cache:
        def cached_load_class_index(base_dir):
            return cache["class-index.json"]

        cls_mod.load_class_index = cached_load_class_index
        grep_mod._class_index_cache = cache["class-index.json"]

    if "swing-index.json" in cache:
        swing_mod._swing_index_cache = cache["swing-index.json"]

    if "inheritance.json" in cache:
        from module_nav_lib import hierarchy as hier_mod
        hier_mod._inheritance_cache = cache["inheritance.json"]

    if "xref-index.json" in cache:
        from module_nav_lib import xref as xref_mod
        xref_mod._xref_cache = cache["xref-index.json"]

    if "method-index.json" in cache:
        from module_nav_lib import methods as meth_mod
        meth_mod._method_index_cache = cache["method-index.json"]

    if "annotations-index.json" in cache:
        from module_nav_lib import annotations as ann_mod
        ann_mod._annotations_cache = cache["annotations-index.json"]

    if "field-index.json" in cache:
        from module_nav_lib import fields as fld_mod
        fld_mod._field_index_cache = cache["field-index.json"]


# ---------------------------------------------------------------------------
# Command dispatch
# ---------------------------------------------------------------------------

def _dispatch(cmd, arg, base_dir, focus_module):
    """Route a command string to the appropriate handler."""
    from module_nav_lib.inventory import cmd_inventory, cmd_module, cmd_modules, cmd_stats
    from module_nav_lib.class_search import cmd_class, cmd_search, cmd_package
    from module_nav_lib.grep_search import cmd_grep, cmd_source, cmd_snippet
    from module_nav_lib.swing_search import (
        cmd_ui_dialogs, cmd_ui_sizes, cmd_ui_colors, cmd_ui_fonts,
        cmd_ui_class, cmd_ui_customizable,
    )
    from module_nav_lib.hierarchy import cmd_hierarchy, cmd_implementors
    from module_nav_lib.xref import cmd_xref, cmd_deps
    from module_nav_lib.methods import cmd_method, cmd_methods
    from module_nav_lib.annotations import cmd_slots, cmd_annotations
    from module_nav_lib.profile import cmd_profile
    from module_nav_lib.help_bridge import cmd_full_profile, cmd_cross_ref
    from module_nav_lib.patch import cmd_patch_target, cmd_patch_plan, cmd_extract
    from module_nav_lib.analysis import cmd_orphans, cmd_deps_graph, cmd_api_surface, cmd_security_audit
    from module_nav_lib.extras import cmd_strings, cmd_resources, cmd_trace_type, cmd_version_diff
    from module_nav_lib.callgraph import cmd_callers, cmd_callees, cmd_call_chain, cmd_hotspots
    from module_nav_lib.fields import cmd_fields, cmd_field
    from module_nav_lib.typeflow import cmd_type_consumers, cmd_type_producers, cmd_type_flow
    from module_nav_lib.coupling import cmd_module_calls, cmd_module_api_usage, cmd_coupling
    from module_nav_lib.patterns import cmd_patterns, cmd_pattern
    from module_nav_lib.bog_bridge import cmd_bog_trace, cmd_bog_classes, cmd_bog_coverage
    from module_nav_lib.exceptions import cmd_throws, cmd_catches
    from module_nav_lib.export import cmd_export_html, cmd_export_mermaid, cmd_export_dot
    from module_nav_lib.tokens import cmd_token
    from module_nav_lib.impact import cmd_impact
    from module_nav_lib.fuzzy import cmd_find
    from module_nav_lib.deprecated import cmd_deprecated, cmd_deprecated_users, cmd_deprecated_risk
    from module_nav_lib.similarity import cmd_similar, cmd_clones
    from module_nav_lib.config_coupling import cmd_config_usage, cmd_config_keys, cmd_resources_usage
    from module_nav_lib.serialization import cmd_serial, cmd_serial_audit, cmd_serial_conflicts
    from module_nav_lib.threading import cmd_thread_safety, cmd_thread_scan
    from module_nav_lib.lifecycle import cmd_lifecycle, cmd_lifecycle_scan, cmd_lifecycle_pattern
    from module_nav_lib.string_constants import cmd_string_search, cmd_string_constants
    from module_nav_lib.nlquery import cmd_ask
    from module_nav_lib.servlets import cmd_servlets, cmd_routes, cmd_servlet
    from module_nav_lib.ords import cmd_ords, cmd_ord_usage, cmd_ord_flow
    from module_nav_lib.topics import cmd_topics, cmd_subscribers, cmd_pub_sub
    from module_nav_lib.bql import cmd_bql, cmd_bql_tables, cmd_bql_class
    from module_nav_lib.permissions import cmd_permissions, cmd_permission_flow, cmd_credentials
    from module_nav_lib.alarm_domain import cmd_alarm_flow, cmd_alarm_types, cmd_alarm_trace
    from module_nav_lib.architecture import cmd_cycles, cmd_god_classes, cmd_layer_check
    from module_nav_lib.complexity import cmd_complexity, cmd_complexity_scan, cmd_metrics
    from module_nav_lib.bookmarks import cmd_bookmark, cmd_bookmarks, cmd_unbookmark, cmd_history as cmd_history_display
    from module_nav_lib.unified import cmd_unified, cmd_compare
    from module_nav_lib.contracts import cmd_integration_contract
    from module_nav_lib.mining import cmd_example_mine
    from module_nav_lib.virtual_dispatch import cmd_virtual_callers
    from module_nav_lib.research import cmd_feature_brief
    from module_nav_lib.slot_validate import cmd_slot_validate
    from module_nav_lib.slot_collision import cmd_slot_collision
    from module_nav_lib.ord_validate import cmd_ord_validate
    from module_nav_lib.resolve_audit import cmd_resolve_audit
    from module_nav_lib.driver_cleanup import cmd_driver_cleanup_audit
    from module_nav_lib.resource_leak import cmd_resource_leak
    from module_nav_lib.service_order import cmd_service_order
    from module_nav_lib.dependency_audit import cmd_dependency_audit
    from module_nav_lib.module_health import cmd_module_health
    from module_nav_lib.sessions import (
        cmd_session_save, cmd_session_load, cmd_session_list,
        cmd_session_note, cmd_session_export, cmd_session_delete,
    )

    parts = arg.split() if arg else []

    # Apply focus: inject --module filter for commands that support it
    effective_module = focus_module

    # --- Inventory commands ---
    if cmd == "inventory":
        cmd_inventory(base_dir)

    elif cmd == "module":
        if not arg.strip():
            print("  Usage: module <name>")
            return
        cmd_module(base_dir, arg.strip())

    elif cmd == "modules":
        # Parse flags from arg
        type_filter = None
        zkm_only = False
        no_code = False
        has_code = False
        bytecode = None
        top_n = None

        i = 0
        while i < len(parts):
            p = parts[i]
            if p in ("--type", "-t") and i + 1 < len(parts):
                type_filter = parts[i + 1]
                i += 2
            elif p == "--zkm":
                zkm_only = True
                i += 1
            elif p == "--no-code":
                no_code = True
                i += 1
            elif p == "--has-code":
                has_code = True
                i += 1
            elif p in ("--bytecode", "-b") and i + 1 < len(parts):
                try:
                    bytecode = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            elif p == "--top" and i + 1 < len(parts):
                try:
                    top_n = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1

        cmd_modules(base_dir, type_filter=type_filter, zkm_only=zkm_only,
                    no_code=no_code, has_code=has_code, bytecode=bytecode, top_n=top_n)

    # --- Class commands ---
    elif cmd == "class":
        if not arg.strip():
            print("  Usage: class <name>")
            return
        cmd_class(base_dir, arg.strip())

    elif cmd == "search":
        limit = 50
        pattern = arg.strip()
        if "-n" in parts:
            idx = parts.index("-n")
            if idx + 1 < len(parts):
                try:
                    limit = int(parts[idx + 1])
                except ValueError:
                    pass
                # Remove -n and value from pattern
                pattern = " ".join(parts[:idx] + parts[idx + 2:])
        if not pattern:
            print("  Usage: search <pattern> [-n N]")
            return
        cmd_search(base_dir, pattern, limit=limit)

    elif cmd == "package":
        if "--all" in parts:
            cmd_package(base_dir, show_all=True)
        elif arg.strip():
            limit = 50
            name = arg.strip()
            if "-n" in parts:
                idx = parts.index("-n")
                if idx + 1 < len(parts):
                    try:
                        limit = int(parts[idx + 1])
                    except ValueError:
                        pass
                    name = " ".join(parts[:idx] + parts[idx + 2:])
            cmd_package(base_dir, name=name, limit=limit)
        else:
            print("  Usage: package <name> | package --all")

    # --- Source commands ---
    elif cmd == "grep":
        limit = 30
        module_filter = effective_module
        type_filter = None
        pattern_parts = []

        i = 0
        while i < len(parts):
            p = parts[i]
            if p == "-n" and i + 1 < len(parts):
                try:
                    limit = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            elif p in ("--module", "-m") and i + 1 < len(parts):
                module_filter = parts[i + 1]
                i += 2
            elif p in ("--type", "-t") and i + 1 < len(parts):
                type_filter = parts[i + 1]
                i += 2
            else:
                pattern_parts.append(p)
                i += 1

        pattern = " ".join(pattern_parts)
        if not pattern:
            print("  Usage: grep <regex> [-n N] [--module mod] [--type rt|wb|ux]")
            return
        cmd_grep(base_dir, pattern, limit=limit,
                 module_filter=module_filter, type_filter=type_filter)

    elif cmd == "source":
        if not parts:
            print("  Usage: source <class> [--code] [--grep pattern]")
            print("         source --batch A,B,C [--code] [--grep pat]")
            return

        show_code = "--code" in parts
        grep_pattern = None
        if "--grep" in parts:
            idx = parts.index("--grep")
            if idx + 1 < len(parts):
                grep_pattern = parts[idx + 1]

        batch_csv = None
        if "--batch" in parts:
            idx = parts.index("--batch")
            if idx + 1 < len(parts):
                batch_csv = parts[idx + 1]

        if batch_csv:
            from module_nav_lib.grep_search import cmd_source_batch
            cmd_source_batch(base_dir, batch_csv,
                             show_code=show_code, grep_pattern=grep_pattern)
        else:
            class_name = parts[0]
            cmd_source(base_dir, class_name,
                       show_code=show_code, grep_pattern=grep_pattern)

    elif cmd == "snippet":
        if len(parts) < 2:
            print("  Usage: snippet <class> <method>")
            return
        cmd_snippet(base_dir, parts[0], parts[1])

    # --- UI commands ---
    elif cmd == "ui":
        if not parts:
            print("  Usage: ui dialogs|sizes|colors|fonts|class|customizable")
            return

        subcmd = parts[0]
        subarg = " ".join(parts[1:]) if len(parts) > 1 else ""
        subparts = parts[1:] if len(parts) > 1 else []

        limit = 50
        if "-n" in subparts:
            idx = subparts.index("-n")
            if idx + 1 < len(subparts):
                try:
                    limit = int(subparts[idx + 1])
                except ValueError:
                    pass

        if subcmd == "dialogs":
            cmd_ui_dialogs(base_dir, limit=limit)
        elif subcmd == "sizes":
            cmd_ui_sizes(base_dir, limit=limit)
        elif subcmd == "colors":
            cmd_ui_colors(base_dir, limit=limit)
        elif subcmd == "fonts":
            cmd_ui_fonts(base_dir, limit=limit)
        elif subcmd == "class":
            name = " ".join(subparts)
            # Remove -n flags from name
            if "-n" in subparts:
                idx = subparts.index("-n")
                name = " ".join(subparts[:idx] + subparts[idx + 2:])
            if not name.strip():
                print("  Usage: ui class <name>")
                return
            cmd_ui_class(base_dir, name.strip())
        elif subcmd == "customizable":
            cmd_ui_customizable(base_dir)
        else:
            print("  Unknown ui sub-command: '{}'".format(subcmd))
            print("  Available: dialogs, sizes, colors, fonts, class, customizable")

    # --- Hierarchy commands ---
    elif cmd == "hierarchy":
        if not parts:
            print("  Usage: hierarchy <class> [--depth N] [--chain]")
            return

        class_name = parts[0]
        show_chain = "--chain" in parts
        depth = 2
        if "--depth" in parts:
            idx = parts.index("--depth")
            if idx + 1 < len(parts):
                try:
                    depth = int(parts[idx + 1])
                except ValueError:
                    pass

        cmd_hierarchy(base_dir, class_name, depth=depth, show_chain=show_chain)

    elif cmd == "implementors":
        if not parts:
            print("  Usage: implementors <interface> [-n N]")
            return

        iface_name = parts[0]
        limit = 50
        if "-n" in parts:
            idx = parts.index("-n")
            if idx + 1 < len(parts):
                try:
                    limit = int(parts[idx + 1])
                except ValueError:
                    pass

        cmd_implementors(base_dir, iface_name, limit=limit)

    # --- Xref commands ---
    elif cmd == "xref":
        if not parts:
            print("  Usage: xref <class> [--importers] [--imports] [-n N]")
            return

        class_name = parts[0]
        show_importers = "--importers" in parts
        show_imports = "--imports" in parts
        limit = 50
        if "-n" in parts:
            idx = parts.index("-n")
            if idx + 1 < len(parts):
                try:
                    limit = int(parts[idx + 1])
                except ValueError:
                    pass

        cmd_xref(base_dir, class_name,
                 show_importers=show_importers,
                 show_imports=show_imports,
                 limit=limit)

    elif cmd == "deps":
        if not parts:
            print("  Usage: deps <module> [--reverse] [-n N]")
            return

        module_name = parts[0]
        reverse = "--reverse" in parts
        limit = 50
        if "-n" in parts:
            idx = parts.index("-n")
            if idx + 1 < len(parts):
                try:
                    limit = int(parts[idx + 1])
                except ValueError:
                    pass

        cmd_deps(base_dir, module_name, reverse=reverse, limit=limit)

    # --- Method commands ---
    elif cmd == "method":
        if not parts:
            print("  Usage: method <name> [-n N] [--module mod] [--class cls]")
            return

        method_name = parts[0]
        module_filter = None
        class_filter = None
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "--class" and i_p + 1 < len(parts):
                class_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_method(base_dir, method_name,
                   module_filter=module_filter,
                   class_filter=class_filter,
                   limit=limit)

    elif cmd == "methods":
        if not parts:
            print("  Usage: methods <class> [-n N] [--public] [--grep pat]")
            return

        cls_name = parts[0]
        public_only = "--public" in parts
        grep_pattern = None
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p == "--grep" and i_p + 1 < len(parts):
                grep_pattern = parts[i_p + 1]
                i_p += 2
            elif p == "--public":
                i_p += 1
            else:
                i_p += 1

        cmd_methods(base_dir, cls_name,
                    public_only=public_only,
                    grep_pattern=grep_pattern,
                    limit=limit)

    # --- Annotation commands ---
    elif cmd == "slots":
        # Parse flags
        class_name = None
        show_properties = "--properties" in parts
        show_actions = "--actions" in parts
        show_topics = "--topics" in parts
        by_type = None
        module_filter = effective_module
        limit = 50

        i_p = 0
        positional_args = []
        while i_p < len(parts):
            p = parts[i_p]
            if p == "--by-type" and i_p + 1 < len(parts):
                by_type = parts[i_p + 1]
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--properties", "--actions", "--topics"):
                i_p += 1
            else:
                positional_args.append(p)
                i_p += 1

        if positional_args and not by_type:
            class_name = positional_args[0]

        cmd_slots(base_dir, class_name=class_name,
                  show_properties=show_properties,
                  show_actions=show_actions,
                  show_topics=show_topics,
                  by_type=by_type,
                  module_filter=module_filter,
                  limit=limit)

    elif cmd == "annotations":
        if not parts:
            print("  Usage: annotations <annotation> [-n N] [--module mod]")
            return

        ann_name = parts[0]
        module_filter = None
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_annotations(base_dir, ann_name, module_filter=module_filter, limit=limit)

    # --- Stats ---
    elif cmd == "stats":
        as_json = "--json" in parts
        cmd_stats(base_dir, as_json=as_json)

    # --- Profile ---
    elif cmd == "profile":
        if not arg.strip():
            print("  Usage: profile <class>")
            return
        cmd_profile(base_dir, arg.strip())

    # --- Phase 9: Help Navigator integration ---
    elif cmd == "full-profile":
        if not parts:
            print("  Usage: full-profile <class> [--help-dir dir]")
            return
        class_name = parts[0]
        hdir = None
        if "--help-dir" in parts:
            idx = parts.index("--help-dir")
            if idx + 1 < len(parts):
                hdir = parts[idx + 1]
        cmd_full_profile(base_dir, class_name, help_dir=hdir)

    elif cmd == "cross-ref":
        if not parts:
            print("  Usage: cross-ref <class> [--help-dir dir]")
            return
        class_name = parts[0]
        hdir = None
        if "--help-dir" in parts:
            idx = parts.index("--help-dir")
            if idx + 1 < len(parts):
                hdir = parts[idx + 1]
        cmd_cross_ref(base_dir, class_name, help_dir=hdir)

    # --- Phase 11: Analysis & Extras ---
    elif cmd == "orphans":
        module_filter = effective_module
        type_filter = None
        limit = 50
        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p in ("--type", "-t") and i_p + 1 < len(parts):
                type_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1
        cmd_orphans(base_dir, module_filter=module_filter,
                    type_filter=type_filter, limit=limit)

    elif cmd == "deps-graph":
        if not parts:
            print("  Usage: deps-graph <module> [--depth N] [--format mermaid|dot|text] [--reverse]")
            return
        module_name = parts[0]
        depth = 1
        fmt = "mermaid"
        reverse = "--reverse" in parts
        if "--depth" in parts:
            idx = parts.index("--depth")
            if idx + 1 < len(parts):
                try:
                    depth = int(parts[idx + 1])
                except ValueError:
                    pass
        if "--format" in parts:
            idx = parts.index("--format")
            if idx + 1 < len(parts):
                fmt = parts[idx + 1]
        cmd_deps_graph(base_dir, module_name, depth=depth, fmt=fmt, reverse=reverse)

    elif cmd == "api-surface":
        if not parts:
            print("  Usage: api-surface <module> [-n N]")
            return
        module_name = parts[0]
        limit = 50
        if "-n" in parts:
            idx = parts.index("-n")
            if idx + 1 < len(parts):
                try:
                    limit = int(parts[idx + 1])
                except ValueError:
                    pass
        cmd_api_surface(base_dir, module_name, limit=limit)

    elif cmd == "security-audit":
        module_filter = effective_module
        limit = 30
        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1
        cmd_security_audit(base_dir, module_filter=module_filter, limit=limit)

    elif cmd == "strings":
        if not parts:
            print("  Usage: strings <pattern> [-n N] [--module mod] [--class cls]")
            return
        module_filter = effective_module
        class_filter = None
        limit = 30
        pattern_parts = []
        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "--class" and i_p + 1 < len(parts):
                class_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                pattern_parts.append(p)
                i_p += 1
        pattern = " ".join(pattern_parts)
        if not pattern:
            print("  Usage: strings <pattern> [-n N] [--module mod] [--class cls]")
            return
        cmd_strings(base_dir, pattern, module_filter=module_filter,
                    class_filter=class_filter, limit=limit)

    elif cmd == "resources":
        if not parts:
            print("  Usage: resources <module> [--type ext] [-n N]")
            return
        module_name = parts[0]
        type_filter = None
        limit = 100
        if "--type" in parts:
            idx = parts.index("--type")
            if idx + 1 < len(parts):
                type_filter = parts[idx + 1]
        if "-n" in parts:
            idx = parts.index("-n")
            if idx + 1 < len(parts):
                try:
                    limit = int(parts[idx + 1])
                except ValueError:
                    pass
        cmd_resources(base_dir, module_name, type_filter=type_filter, limit=limit)

    elif cmd == "trace-type":
        if not arg.strip():
            print("  Usage: trace-type <type> (e.g. control:NumericWritable)")
            return
        cmd_trace_type(base_dir, arg.strip())

    elif cmd == "version-diff":
        if not parts:
            print("  Usage: version-diff <path-to-other-class-index.json>")
            return
        other_path = parts[0]
        limit = 50
        if "-n" in parts:
            idx = parts.index("-n")
            if idx + 1 < len(parts):
                try:
                    limit = int(parts[idx + 1])
                except ValueError:
                    pass
        cmd_version_diff(base_dir, other_path, limit=limit)

    # --- Phase 10: Patch workflow commands ---
    elif cmd == "patch-target":
        if not arg.strip():
            print("  Usage: patch-target <query> [-n N]")
            return

        limit = 20
        query_parts = []
        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                query_parts.append(p)
                i_p += 1

        query = " ".join(query_parts)
        if not query:
            print("  Usage: patch-target <query> [-n N]")
            return
        cmd_patch_target(base_dir, query, limit=limit)

    elif cmd == "patch-plan":
        if not arg.strip():
            print("  Usage: patch-plan <class>")
            return
        cmd_patch_plan(base_dir, arg.strip())

    elif cmd == "extract":
        if len(parts) < 2:
            print("  Usage: extract <module> <class>")
            return
        patches_dir = None
        if "--patches-dir" in parts:
            idx = parts.index("--patches-dir")
            if idx + 1 < len(parts):
                patches_dir = parts[idx + 1]
        cmd_extract(base_dir, parts[0], parts[1], patches_dir=patches_dir)

    # --- Phase 12: Call Graph commands ---
    elif cmd == "callers":
        if len(parts) < 2:
            print("  Usage: callers <class> <method> [-n N]")
            return

        class_name = parts[0]
        method_name = parts[1]
        limit = 50
        if "-n" in parts:
            idx = parts.index("-n")
            if idx + 1 < len(parts):
                try:
                    limit = int(parts[idx + 1])
                except ValueError:
                    pass

        cmd_callers(base_dir, class_name, method_name, limit=limit)

    elif cmd == "callees":
        if not parts:
            print("  Usage: callees <class> [<method>] [-n N]")
            return

        class_name = parts[0]
        method_name = None
        limit = 50

        i_p = 1
        positional_done = False
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif not positional_done and not p.startswith("-"):
                method_name = p
                positional_done = True
                i_p += 1
            else:
                i_p += 1

        cmd_callees(base_dir, class_name, method_name=method_name, limit=limit)

    elif cmd == "call-chain":
        if len(parts) < 2:
            print("  Usage: call-chain <class> <method> [--depth N]")
            return

        class_name = parts[0]
        method_name = parts[1]
        depth = 2
        if "--depth" in parts:
            idx = parts.index("--depth")
            if idx + 1 < len(parts):
                try:
                    depth = int(parts[idx + 1])
                except ValueError:
                    pass

        cmd_call_chain(base_dir, class_name, method_name, depth=depth)

    elif cmd == "hotspots":
        limit = 20
        module_filter = effective_module
        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1
        cmd_hotspots(base_dir, limit=limit, module_filter=module_filter)

    # --- Phase 13: Field commands ---
    elif cmd == "fields":
        if not parts:
            print("  Usage: fields <class> [-n N] [--static] [--public] [--grep pat]")
            return

        cls_name = parts[0]
        static_only = "--static" in parts
        public_only = "--public" in parts
        grep_pattern = None
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p == "--grep" and i_p + 1 < len(parts):
                grep_pattern = parts[i_p + 1]
                i_p += 2
            elif p in ("--static", "--public"):
                i_p += 1
            else:
                i_p += 1

        cmd_fields(base_dir, cls_name,
                   static_only=static_only,
                   public_only=public_only,
                   grep_pattern=grep_pattern,
                   limit=limit)

    elif cmd == "field":
        if not parts:
            print("  Usage: field <name> [-n N] [--module mod]")
            return

        field_name = parts[0]
        module_filter = None
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_field(base_dir, field_name,
                  module_filter=module_filter,
                  limit=limit)

    # --- Phase 14: Type Flow commands ---
    elif cmd == "type-consumers":
        if not parts:
            print("  Usage: type-consumers <type> [-n N] [--module mod]")
            return

        type_name = parts[0]
        module_filter = effective_module
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_type_consumers(base_dir, type_name,
                           limit=limit, module_filter=module_filter)

    elif cmd == "type-producers":
        if not parts:
            print("  Usage: type-producers <type> [-n N] [--module mod]")
            return

        type_name = parts[0]
        module_filter = effective_module
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_type_producers(base_dir, type_name,
                           limit=limit, module_filter=module_filter)

    elif cmd == "type-flow":
        if not parts:
            print("  Usage: type-flow <type> [--depth N] [-n N]")
            return

        type_name = parts[0]
        depth = 1
        limit = 30

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "--depth" and i_p + 1 < len(parts):
                try:
                    depth = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_type_flow(base_dir, type_name, depth=depth, limit=limit)

    # --- Phase 15: Cross-Module Calls commands ---
    elif cmd == "module-calls":
        if len(parts) < 2:
            print("  Usage: module-calls <from> <to> [-n N]")
            return

        from_mod = parts[0]
        to_mod = parts[1]
        limit = 50

        i_p = 2
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_module_calls(base_dir, from_mod, to_mod, limit=limit)

    elif cmd == "module-api-usage":
        if not parts:
            print("  Usage: module-api-usage <module> [-n N]")
            return

        module_name = parts[0]
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_module_api_usage(base_dir, module_name, limit=limit)

    elif cmd == "coupling":
        if len(parts) < 2:
            print("  Usage: coupling <mod1> <mod2>")
            return
        cmd_coupling(base_dir, parts[0], parts[1])

    # --- Phase 17: Pattern Detection commands ---
    elif cmd == "patterns":
        if not parts:
            print("  Usage: patterns <module> [-n N]")
            return

        module_name = parts[0]
        limit = 50
        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_patterns(base_dir, module_name, limit=limit)

    elif cmd == "pattern":
        if not parts:
            print("  Usage: pattern <category> [-n N] [--module mod]")
            print("  Categories: services, drivers, points, views, extensions, enums, structs")
            return

        category = parts[0]
        module_filter = effective_module
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_pattern(base_dir, category, limit=limit, module_filter=module_filter)

    # --- Phase 16: BOG-Code Bridge commands ---
    elif cmd == "bog-trace":
        if not arg.strip():
            print("  Usage: bog-trace <path-or-type> [--bog-index path]")
            return
        bog_idx = None
        query_parts = []
        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "--bog-index" and i_p + 1 < len(parts):
                bog_idx = parts[i_p + 1]
                i_p += 2
            else:
                query_parts.append(p)
                i_p += 1
        query = " ".join(query_parts)
        if not query:
            print("  Usage: bog-trace <path-or-type> [--bog-index path]")
            return
        cmd_bog_trace(base_dir, query, bog_index_path=bog_idx)

    elif cmd == "bog-classes":
        bog_idx = None
        if "--bog-index" in parts:
            idx = parts.index("--bog-index")
            if idx + 1 < len(parts):
                bog_idx = parts[idx + 1]
        cmd_bog_classes(base_dir, bog_index_path=bog_idx)

    elif cmd == "bog-coverage":
        bog_idx = None
        if "--bog-index" in parts:
            idx = parts.index("--bog-index")
            if idx + 1 < len(parts):
                bog_idx = parts[idx + 1]
        cmd_bog_coverage(base_dir, bog_index_path=bog_idx)

    # --- Phase 19: Exception Flow commands ---
    elif cmd == "throws":
        if not parts:
            print("  Usage: throws <class> [-n N] [--module mod]")
            return

        class_name = parts[0]
        module_filter = None
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_throws(base_dir, class_name,
                   module_filter=module_filter,
                   limit=limit)

    elif cmd == "catches":
        if not parts:
            print("  Usage: catches <exception> [-n N] [--module mod]")
            return

        exception_name = parts[0]
        module_filter = effective_module
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_catches(base_dir, exception_name,
                    module_filter=module_filter,
                    limit=limit)

    # --- Phase 20: Export/Visualization commands ---
    elif cmd == "export":
        if not parts:
            print("  Usage: export <name> --html | --mermaid | --dot [method]")
            print("         export <name> --html         HTML class report")
            print("         export <name> --mermaid      Mermaid class diagram")
            print("         export <name> <method> --dot DOT call-chain graph")
            print("         export <name> --dot          DOT module class diagram")
            return

        name = parts[0]
        method = None
        fmt_html = "--html" in parts
        fmt_mermaid = "--mermaid" in parts
        fmt_dot = "--dot" in parts
        output_path = None

        # Parse flags
        i_p = 1
        positional_done = False
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("-o", "--output") and i_p + 1 < len(parts):
                output_path = parts[i_p + 1]
                i_p += 2
            elif p in ("--html", "--mermaid", "--dot"):
                i_p += 1
            elif not positional_done and not p.startswith("-"):
                method = p
                positional_done = True
                i_p += 1
            else:
                i_p += 1

        if fmt_html:
            cmd_export_html(base_dir, name, output_path=output_path)
        elif fmt_mermaid:
            cmd_export_mermaid(base_dir, name, output_path=output_path)
        elif fmt_dot:
            cmd_export_dot(base_dir, name, method=method, output_path=output_path)
        else:
            print("  Specify --html, --mermaid, or --dot")

    # --- Phase 18: Full-Text Token Search commands ---
    elif cmd == "token":
        if not parts:
            print("  Usage: token <word> [-n N] [--context [N]] [--module mod]")
            return

        word = parts[0]
        module_filter = effective_module
        context_lines = 0
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "--context":
                # Accept optional integer: --context N → N lines; bare → 2
                if i_p + 1 < len(parts) and parts[i_p + 1].lstrip("-").isdigit():
                    try:
                        context_lines = int(parts[i_p + 1])
                    except ValueError:
                        context_lines = 2
                    i_p += 2
                else:
                    context_lines = 2
                    i_p += 1
            else:
                i_p += 1

        cmd_token(base_dir, word,
                  module_filter=module_filter,
                  show_context=(context_lines > 0),
                  context_lines=context_lines,
                  limit=limit)

    # --- Batch 6: Header imports command ---
    elif cmd == "imports":
        if not parts:
            print("  Usage: imports <class> [--external-only] [-n N]")
            return

        class_name = parts[0]
        external_only = "--external-only" in parts
        limit = 100

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        from module_nav_lib.header_imports import cmd_imports
        cmd_imports(base_dir, class_name,
                    external_only=external_only,
                    limit=limit)

    # --- Batch 7: License feature gating (FEATURE-4) ---
    elif cmd == "license-feature":
        if not parts:
            print("  Usage: license-feature <name> [-n N]")
            return
        feature_name = parts[0]
        limit = 100
        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1
        from module_nav_lib.license_features import cmd_license_feature
        cmd_license_feature(base_dir, feature_name, limit=limit)

    elif cmd == "license-features":
        limit = 50
        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1
        from module_nav_lib.license_features import cmd_license_features
        cmd_license_features(base_dir, limit=limit)

    # --- Phase 21: Impact Analysis commands ---
    elif cmd == "impact":
        if not parts:
            print("  Usage: impact <class> [<method>] [--depth N]")
            return

        class_name = parts[0]
        method_name = None
        depth = 3

        i_p = 1
        positional_done = False
        while i_p < len(parts):
            p = parts[i_p]
            if p == "--depth" and i_p + 1 < len(parts):
                try:
                    depth = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif not positional_done and not p.startswith("-"):
                method_name = p
                positional_done = True
                i_p += 1
            else:
                i_p += 1

        cmd_impact(base_dir, class_name,
                   method_name=method_name,
                   depth=depth)

    # --- Phase 22: Fuzzy Search commands ---
    elif cmd == "find":
        if not parts:
            print("  Usage: find <query> [--source] [--module <mod>] [-n N]")
            return

        source_mode = False
        module_filter = effective_module
        limit = 50
        query_words = []

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "--source":
                source_mode = True
                i_p += 1
            elif p == "--module" and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                query_words.append(p)
                i_p += 1

        if not query_words:
            print("  Usage: find <query> [--source] [--module <mod>] [-n N]")
            return

        cmd_find(base_dir, " ".join(query_words),
                 source_mode=source_mode,
                 module_filter=module_filter,
                 limit=limit)

    # --- Phase 23: Deprecated Chain Analysis commands ---
    elif cmd == "deprecated":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_deprecated(base_dir, module_filter=module_filter, limit=limit)

    elif cmd == "deprecated-users":
        if not parts:
            print("  Usage: deprecated-users <class> [method] [-n N]")
            return

        class_name = parts[0]
        method_name = None
        limit = 50

        i_p = 1
        positional_done = False
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif not positional_done and not p.startswith("-"):
                method_name = p
                positional_done = True
                i_p += 1
            else:
                i_p += 1

        cmd_deprecated_users(base_dir, class_name,
                             method_name=method_name, limit=limit)

    elif cmd == "deprecated-risk":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_deprecated_risk(base_dir, module_filter=module_filter, limit=limit)

    # --- Phase 24: Code Similarity Detection commands ---
    elif cmd == "similar":
        if not parts:
            print("  Usage: similar <class> [-n N]")
            return

        class_name = parts[0]
        limit = 20

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_similar(base_dir, class_name, limit=limit)

    elif cmd == "clones":
        module_filter = effective_module
        limit = 20

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_clones(base_dir, module_filter=module_filter, limit=limit)

    # --- Phase 25: Config & Resource Coupling commands ---
    elif cmd == "config-usage":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_config_usage(base_dir, module_filter=module_filter, limit=limit)

    elif cmd == "config-keys":
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_config_keys(base_dir, limit=limit)

    elif cmd == "resources-usage":
        if not parts:
            print("  Usage: resources-usage <module> [-n N]")
            return

        module_name = parts[0]
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_resources_usage(base_dir, module_name, limit=limit)

    # --- Phase 26: Serialization Audit commands ---
    elif cmd == "serial":
        if not parts:
            print("  Usage: serial <class>")
            return

        class_name = parts[0]
        cmd_serial(base_dir, class_name)

    elif cmd == "serial-audit":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_serial_audit(base_dir, module_filter=module_filter, limit=limit)

    elif cmd == "serial-conflicts":
        limit = 30

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_serial_conflicts(base_dir, limit=limit)

    # --- Phase 28: Thread Safety commands ---
    elif cmd == "thread-safety":
        if not parts:
            print("  Usage: thread-safety <class>")
            return

        class_name = parts[0]
        cmd_thread_safety(base_dir, class_name)

    elif cmd == "thread-scan":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_thread_scan(base_dir, module_filter=module_filter, limit=limit)

    # --- Phase 29: Niagara Lifecycle commands ---
    elif cmd == "lifecycle":
        # lifecycle --pattern <name> [--module mod] [-n N]
        # lifecycle <class>
        pattern_name = None
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--pattern", "-p") and i_p + 1 < len(parts):
                pattern_name = parts[i_p + 1]
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                break

        if pattern_name:
            cmd_lifecycle_pattern(base_dir, pattern_name,
                                 module_filter=module_filter, limit=limit)
        elif parts and parts[0] not in ("-p", "--pattern", "-m", "--module", "-n"):
            cmd_lifecycle(base_dir, parts[0])
        else:
            print("  Usage: lifecycle <class>  or  lifecycle --pattern <name>")

    elif cmd == "lifecycle-scan":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_lifecycle_scan(base_dir, module_filter=module_filter, limit=limit)

    # --- Phase 30: String Constant Index commands ---
    elif cmd == "string-search":
        if not parts:
            print("  Usage: string-search <pattern> [-n N] [--module mod]")
            return

        pattern = parts[0]
        module_filter = effective_module
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        cmd_string_search(base_dir, pattern,
                          module_filter=module_filter, limit=limit)

    elif cmd == "string-constants":
        if not parts:
            print("  Usage: string-constants <class> [-n N]")
            return

        class_name = parts[0]
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_string_constants(base_dir, class_name, limit=limit)

    # --- Phase 31: Natural Language Query commands ---
    elif cmd == "ask":
        if not parts:
            print("  Usage: ask <question>")
            return

        question = " ".join(parts)
        cmd_ask(base_dir, question)

    # --- Phase 33: Servlet & Web Route Index commands ---
    elif cmd == "servlets":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_servlets(base_dir, module_filter=module_filter, limit=limit)

    elif cmd == "routes":
        verb_filter = None
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "--verb" and i_p + 1 < len(parts):
                verb_filter = parts[i_p + 1]
                i_p += 2
            elif p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_routes(base_dir, verb_filter=verb_filter,
                   module_filter=module_filter, limit=limit)

    elif cmd == "servlet":
        if not parts:
            print("  Usage: servlet <class>")
            return

        cmd_servlet(base_dir, parts[0])

    # --- Phase 34: ORD Resolution Graph commands ---
    elif cmd == "ords":
        module_filter = effective_module
        scheme_filter = None
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p in ("--scheme", "-s") and i_p + 1 < len(parts):
                scheme_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_ords(base_dir, module_filter=module_filter,
                 scheme_filter=scheme_filter, limit=limit)

    elif cmd == "ord-usage":
        if not parts:
            print("  Usage: ord-usage <scheme> [--module mod] [-n N]")
            return

        scheme = parts[0]
        module_filter = effective_module
        limit = 50

        i_p = 1
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_ord_usage(base_dir, scheme,
                      module_filter=module_filter, limit=limit)

    elif cmd == "ord-flow":
        if not parts:
            print("  Usage: ord-flow <class>")
            return

        cmd_ord_flow(base_dir, parts[0])

    # --- Phase 35: Subscription & Topic Graph commands ---
    elif cmd == "topics":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_topics(base_dir, module_filter=module_filter, limit=limit)

    elif cmd == "subscribers":
        if not parts:
            print("  Usage: subscribers <topic|class>")
            return

        cmd_subscribers(base_dir, parts[0])

    elif cmd == "pub-sub":
        if not parts:
            print("  Usage: pub-sub <module>")
            return

        cmd_pub_sub(base_dir, parts[0])

    # --- Phase 36: BQL Query Analyzer commands ---
    elif cmd == "bql":
        module_filter = effective_module
        type_filter = None
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p in ("--type", "-t") and i_p + 1 < len(parts):
                type_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_bql(base_dir, module_filter=module_filter,
                type_filter=type_filter, limit=limit)

    elif cmd == "bql-tables":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_bql_tables(base_dir, module_filter=module_filter, limit=limit)

    elif cmd == "bql-class":
        if not parts:
            print("  Usage: bql-class <class>")
            return

        cmd_bql_class(base_dir, parts[0])

    # --- Phase 37: Permission & Security Model commands ---
    elif cmd == "permissions":
        module_filter = effective_module
        limit = 50
        declared = "--declared" in parts
        type_filter = None

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p == "--type" and i_p + 1 < len(parts):
                type_filter = parts[i_p + 1]
                i_p += 2
            else:
                i_p += 1

        if declared:
            from module_nav_lib.permissions import cmd_permissions_declared
            cmd_permissions_declared(base_dir,
                                     module_filter=module_filter,
                                     type_filter=type_filter)
        else:
            cmd_permissions(base_dir, module_filter=module_filter, limit=limit)

    elif cmd == "permission-flow":
        if not parts:
            print("  Usage: permission-flow <class>")
            return

        cmd_permission_flow(base_dir, parts[0])

    elif cmd == "credentials":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_credentials(base_dir, module_filter=module_filter, limit=limit)

    # --- Phase 38: Alarm Domain Tracer commands ---
    elif cmd == "alarm-flow":
        module_filter = effective_module
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_filter = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_alarm_flow(base_dir, module_filter=module_filter, limit=limit)

    elif cmd == "alarm-types":
        cmd_alarm_types(base_dir)

    elif cmd == "alarm-trace":
        if not parts:
            print("  Usage: alarm-trace <class>")
            return

        cmd_alarm_trace(base_dir, parts[0])

    # --- Phase 39: Cyclic Dependency & Architecture commands ---
    elif cmd == "cycles":
        max_depth = 6
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p == "--depth" and i_p + 1 < len(parts):
                try:
                    max_depth = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_cycles(base_dir, max_depth=max_depth, limit=limit)

    elif cmd == "god-classes":
        threshold = 100
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--threshold", "-t") and i_p + 1 < len(parts):
                try:
                    threshold = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        cmd_god_classes(base_dir, threshold=threshold, limit=limit)

    elif cmd == "layer-check":
        module_filter = None
        if parts:
            module_filter = parts[0]
        elif effective_module:
            module_filter = effective_module

        cmd_layer_check(base_dir, module_filter=module_filter)

    # --- Phase 40: Complexity Metrics commands ---
    elif cmd == "complexity":
        if not parts:
            print("  Usage: complexity <class>")
            return

        cmd_complexity(base_dir, parts[0])

    elif cmd == "complexity-scan":
        module_f = None
        limit = 50

        i_p = 0
        while i_p < len(parts):
            p = parts[i_p]
            if p in ("--module", "-m") and i_p + 1 < len(parts):
                module_f = parts[i_p + 1]
                i_p += 2
            elif p == "-n" and i_p + 1 < len(parts):
                try:
                    limit = int(parts[i_p + 1])
                except ValueError:
                    pass
                i_p += 2
            else:
                i_p += 1

        if not module_f and effective_module:
            module_f = effective_module

        cmd_complexity_scan(base_dir, module_filter=module_f, limit=limit)

    elif cmd == "metrics":
        mod = None
        if parts:
            mod = parts[0]
        elif effective_module:
            mod = effective_module

        if not mod:
            print("  Usage: metrics <module>")
            return

        cmd_metrics(base_dir, mod)

    # --- Phase 41: Bookmarks & Session (CLI dispatch) ---
    elif cmd == "bookmark":
        if not parts:
            print("  Usage: bookmark <class> [note]")
            return
        cls = parts[0]
        note = " ".join(parts[1:]) if len(parts) > 1 else None
        cmd_bookmark(base_dir, cls, note=note)

    elif cmd == "bookmarks":
        sort_by = "time"
        limit = None
        i = 0
        while i < len(parts):
            if parts[i] == "--sort" and i + 1 < len(parts):
                sort_by = parts[i + 1]
                i += 2
            elif parts[i] == "-n" and i + 1 < len(parts):
                try:
                    limit = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1
        cmd_bookmarks(base_dir, sort_by=sort_by, limit=limit)

    elif cmd == "unbookmark":
        if not parts:
            print("  Usage: unbookmark <class>")
            return
        cmd_unbookmark(base_dir, parts[0])

    elif cmd == "history":
        limit = 50
        show_all = False
        grep_pat = None
        i = 0
        while i < len(parts):
            if parts[i] == "-n" and i + 1 < len(parts):
                try:
                    limit = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            elif parts[i] == "--all":
                show_all = True
                i += 1
            elif parts[i] == "--grep" and i + 1 < len(parts):
                grep_pat = parts[i + 1]
                i += 2
            else:
                i += 1
        cmd_history_display(base_dir, limit=limit, show_all=show_all,
                            grep_pattern=grep_pat)

    # --- Phase 42: Cross-Navigator Unified Search (CLI dispatch) ---
    elif cmd == "unified":
        if not arg.strip():
            print("  Usage: unified <query> [--limit N]")
            return
        limit = 10
        query_parts = []
        i = 0
        while i < len(parts):
            if parts[i] == "--limit" and i + 1 < len(parts):
                try:
                    limit = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                query_parts.append(parts[i])
                i += 1
        cmd_unified(base_dir, " ".join(query_parts), limit=limit)

    elif cmd == "compare":
        if not parts:
            print("  Usage: compare <class>")
            return
        cmd_compare(base_dir, parts[0])

    # --- Phase 43: Research Automation (Batch 4) ---
    elif cmd == "integration-contract":
        if not parts:
            print("  Usage: integration-contract <class> "
                  "[--min-callers N] [--resolve-virtual] [--json]")
            return
        cls = parts[0]
        min_callers = 5
        as_json = False
        resolve_virtual = False
        i = 1
        while i < len(parts):
            if parts[i] == "--min-callers" and i + 1 < len(parts):
                try:
                    min_callers = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            elif parts[i] == "--json":
                as_json = True
                i += 1
            elif parts[i] == "--resolve-virtual":
                resolve_virtual = True
                i += 1
            else:
                i += 1
        cmd_integration_contract(base_dir, cls,
                                 min_callers=min_callers, as_json=as_json,
                                 resolve_virtual=resolve_virtual)

    elif cmd == "example-mine":
        if not parts:
            print("  Usage: example-mine <class> [--pattern S] [--top N] "
                  "[--exclude-tridium] [--include-docsource] "
                  "[--min-lines N] [--json]")
            return
        cls = parts[0]
        pattern = None
        top = 3
        excl = False
        incl_doc = False
        min_lines = 5
        as_json = False
        i = 1
        while i < len(parts):
            if parts[i] == "--pattern" and i + 1 < len(parts):
                pattern = parts[i + 1]
                i += 2
            elif parts[i] == "--top" and i + 1 < len(parts):
                try:
                    top = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            elif parts[i] == "--exclude-tridium":
                excl = True
                i += 1
            elif parts[i] == "--include-docsource":
                incl_doc = True
                i += 1
            elif parts[i] == "--min-lines" and i + 1 < len(parts):
                try:
                    min_lines = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            elif parts[i] == "--json":
                as_json = True
                i += 1
            else:
                i += 1
        cmd_example_mine(base_dir, cls,
                         pattern=pattern, top=top,
                         exclude_tridium=excl, min_lines=min_lines,
                         as_json=as_json,
                         include_docsource=incl_doc)

    elif cmd == "virtual-callers":
        if len(parts) < 2:
            print("  Usage: virtual-callers <class> <method> "
                  "[--depth N] [--no-self] [--json]")
            return
        cls = parts[0]
        method = parts[1]
        max_depth = 0
        no_self = False
        as_json = False
        i = 2
        while i < len(parts):
            if parts[i] == "--depth" and i + 1 < len(parts):
                try:
                    max_depth = int(parts[i + 1])
                except ValueError:
                    pass
                i += 2
            elif parts[i] == "--no-self":
                no_self = True
                i += 1
            elif parts[i] == "--json":
                as_json = True
                i += 1
            else:
                i += 1
        cmd_virtual_callers(base_dir, cls, method,
                            max_depth=max_depth,
                            include_self=not no_self,
                            as_json=as_json)

    elif cmd == "feature-brief":
        if not parts:
            print("  Usage: feature-brief <feature> "
                  "[--depth quick|full] [--out path] [--json]")
            return
        feat = parts[0]
        depth = "quick"
        out_path = None
        as_json = False
        i = 1
        while i < len(parts):
            if parts[i] == "--depth" and i + 1 < len(parts):
                depth = parts[i + 1]
                i += 2
            elif parts[i] == "--out" and i + 1 < len(parts):
                out_path = parts[i + 1]
                i += 2
            elif parts[i] == "--json":
                as_json = True
                i += 1
            else:
                i += 1
        cmd_feature_brief(base_dir, feat, depth=depth,
                          out_path=out_path, as_json=as_json)

    elif cmd == "slot-validate":
        if not parts:
            print("  Usage: slot-validate <class> --add name:type[:default] "
                  "[--kind property|action|topic] [--json]")
            return
        cls = parts[0]
        add_spec = None
        kind = "property"
        as_json = False
        i = 1
        while i < len(parts):
            if parts[i] == "--add" and i + 1 < len(parts):
                add_spec = parts[i + 1]
                i += 2
            elif parts[i] == "--kind" and i + 1 < len(parts):
                kind = parts[i + 1]
                i += 2
            elif parts[i] == "--json":
                as_json = True
                i += 1
            else:
                i += 1
        if not add_spec:
            print("  ERROR: --add is required.")
            print("  Usage: slot-validate <class> --add name:type[:default]")
            return
        cmd_slot_validate(base_dir, cls, add_spec=add_spec,
                          kind=kind, as_json=as_json)

    elif cmd == "slot-collision":
        module_filter = None
        as_json = False
        i = 1
        while i < len(parts):
            if parts[i] == "--module" and i + 1 < len(parts):
                module_filter = parts[i + 1]
                i += 2
            elif parts[i] == "--json":
                as_json = True
                i += 1
            else:
                i += 1
        cmd_slot_collision(base_dir, module_filter=module_filter,
                          as_json=as_json)

    elif cmd == "ord-validate":
        if not parts:
            print("  Usage: ord-validate <module> [--json]")
            return
        module_name = parts[0]
        as_json = "--json" in parts
        cmd_ord_validate(base_dir, module_name, as_json=as_json)

    elif cmd == "resolve-audit":
        if not parts:
            print("  Usage: resolve-audit <module> [--json]")
            return
        module_name = parts[0]
        as_json = "--json" in parts
        cmd_resolve_audit(base_dir, module_name, as_json=as_json)

    # Batch 5, Gap #12: driver-cleanup-audit
    elif cmd == "driver-cleanup-audit":
        if not parts:
            print("  Usage: driver-cleanup-audit <module> [--json]")
            return
        module_name = parts[0]
        as_json = "--json" in parts
        cmd_driver_cleanup_audit(base_dir, module_name, as_json=as_json)

    # Batch 5, Gap #11: resource-leak
    elif cmd == "resource-leak":
        if not parts:
            print("  Usage: resource-leak <module> [--json]")
            return
        module_name = parts[0]
        as_json = "--json" in parts
        cmd_resource_leak(base_dir, module_name, as_json=as_json)

    # Batch 5, Gap #13: service-order
    elif cmd == "service-order":
        if not parts:
            print("  Usage: service-order <module> [--json]")
            return
        module_name = parts[0]
        as_json = "--json" in parts
        cmd_service_order(base_dir, module_name, as_json=as_json)

    # Batch 5, Gap #14: dependency-audit
    elif cmd == "dependency-audit":
        if not parts:
            print("  Usage: dependency-audit <module> [--json]")
            return
        module_name = parts[0]
        as_json = "--json" in parts
        cmd_dependency_audit(base_dir, module_name, as_json=as_json)

    # Batch 5, Gap #21: module-health
    elif cmd == "module-health":
        if not parts:
            print("  Usage: module-health <module> [--json]")
            return
        module_name = parts[0]
        as_json = "--json" in parts
        cmd_module_health(base_dir, module_name, as_json=as_json)

    # --- Phase 44: Session management ---
    elif cmd == "session":
        if not parts:
            print("  Usage: session <save|load|list|note|export|delete> [args]")
            return
        sub = parts[0]
        if sub == "save":
            if len(parts) < 2:
                print("  Usage: session save <name>")
                return
            cmd_session_save(base_dir, parts[1])
        elif sub == "load":
            if len(parts) < 2:
                print("  Usage: session load <name>")
                return
            cmd_session_load(base_dir, parts[1])
        elif sub == "list":
            limit = 50
            i = 1
            while i < len(parts):
                if parts[i] == "-n" and i + 1 < len(parts):
                    try:
                        limit = int(parts[i + 1])
                    except ValueError:
                        pass
                    i += 2
                else:
                    i += 1
            cmd_session_list(base_dir, limit=limit)
        elif sub == "note":
            if len(parts) < 2:
                print("  Usage: session note <text>")
                return
            cmd_session_note(base_dir, " ".join(parts[1:]))
        elif sub == "export":
            name = None
            fmt = "md"
            out_path = None
            i = 1
            while i < len(parts):
                if parts[i] == "--as" and i + 1 < len(parts):
                    fmt = parts[i + 1]
                    i += 2
                elif parts[i] == "--out" and i + 1 < len(parts):
                    out_path = parts[i + 1]
                    i += 2
                elif not name:
                    name = parts[i]
                    i += 1
                else:
                    i += 1
            if not name:
                print("  Usage: session export <name> [--as md|json] [--out <path>]")
                return
            cmd_session_export(base_dir, name, fmt=fmt, out_path=out_path)
        elif sub == "delete":
            if len(parts) < 2:
                print("  Usage: session delete <name>")
                return
            cmd_session_delete(base_dir, parts[1])
        else:
            print("  Unknown session subcommand: '{}'.".format(sub))
            print("  Usage: session <save|load|list|note|export|delete>")

    else:
        print("  Unknown command: '{}'. Type 'help' for usage.".format(cmd))


# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------

HELP_TEXT = """
  Module Navigator — Interactive REPL
  ====================================

  INVENTORY:
    inventory                     Summary of all indexed modules
    module <name>                 Detailed info for a submodule
    modules [--type T] [--zkm]    List modules with filters
    stats [--json]                Corpus statistics

  CLASSES:
    class <name>                  Look up a class by exact name
    search <pattern> [-n N]       Glob search (e.g. "*Dialog*")
    package <name> | --all        List classes in a package
    profile <class>               Combined class + source + UI view

  HIERARCHY:
    hierarchy <class> [--depth N] Subclass tree (default depth 2)
    hierarchy <class> --chain     Inheritance chain to root
    implementors <iface> [-n N]   Classes implementing an interface

  XREF:
    xref <class>                  Imports + importers for a class
    xref <class> --importers      Only classes that import it
    xref <class> --imports        Only what this class imports
    deps <module> [-n N]          Modules it depends on
    deps <module> --reverse       Modules that depend on it

  METHODS:
    method <name> [-n N]          All classes defining this method
    method <name> --module <mod>  Filter by module
    method <name> --class <cls>   Full signature in that class
    methods <class> [-n N]        List all methods of a class
    methods <class> --public      Only public methods
    methods <class> --grep <pat>  Filter methods by regex

  SOURCE:
    grep <regex> [-n N]           Regex search across sources
      [--module mod] [--type T]   Filter by module or type
    source <class|FQN>            Show class info (accepts FQN)
      [--code] [--grep pat]       Full source or grep within
    source --batch A,B,C          Read multiple classes in one call
      [--code] [--grep pat]       Options propagate to each class
    snippet <class|FQN> <method>  Extract method source code (accepts FQN)
    imports <class|FQN>           Raw .java header imports (incl. externals)
      [--external-only] [-n N]    Only imports not in corpus
    license-feature <name> [-n N] Callsites for checkFeature('tridium', <name>)
    license-features [-n N]       Top feature names referenced, with counts

  UI/SWING:
    ui dialogs [-n N]             List dialog classes
    ui sizes [-n N]               List hardcoded dimensions
    ui colors [-n N]              List hardcoded colors
    ui fonts [-n N]               List hardcoded fonts
    ui class <name>               Full UI details for a class
    ui customizable               Summary of patcheable elements

  ANNOTATIONS:
    slots <class>                 Properties, actions, topics
    slots <class> --properties    Only properties
    slots <class> --actions       Only actions
    slots <class> --topics        Only topics
    slots --by-type <type> [-n N] Classes with that property type
      [--module mod]              Filter by module
    annotations <ann> [-n N]      Classes with that annotation
      [--module mod]              Filter by module

  HELP NAVIGATOR INTEGRATION:
    full-profile <class>          Combined view from BOTH navigators
      [--help-dir dir]            Help Navigator dir (auto-detected)
    cross-ref <class>             Docs + implementation + who uses it
      [--help-dir dir]            Help Navigator dir (auto-detected)

  PATCH WORKFLOW:
    patch-target <query> [-n N]   Find patchable classes by description
    patch-plan <class>            Generate complete patch plan
    extract <module> <class>      Extract class for editing + build scripts

  ANALYSIS:
    orphans [--module mod] [-n N] Dead code (never imported)
      [--type rt|wb|ux]           Filter by submodule type
    deps-graph <module>           Module dependency graph
      [--depth N] [--format F]    F: mermaid, dot, text
      [--reverse]                 Show dependents instead
    api-surface <module> [-n N]   Public API summary
    security-audit [-n N]         Scan for insecure patterns
      [--module mod]              (recommended: filter by module)

  CALL GRAPH:
    callers <class> <method>      Who calls this method
      [-n N]                      Limit results (default 50)
    callees <class> [<method>]    What methods a class/method calls
      [-n N]                      Limit results (default 50)
    call-chain <class> <method>   Transitive call chain (tree)
      [--depth N]                 Max depth (default 2)
    hotspots [-n N]               Most-called methods (hub analysis)
      [--module mod]              Filter by module

  FIELDS:
    fields <class> [-n N]         List all fields of a class
    fields <class> --static       Only static fields/constants
    fields <class> --public       Only public fields
    fields <class> --grep <pat>   Filter fields by regex
    field <name> [-n N]           All classes defining this field
    field <name> --module <mod>   Filter by module

  TYPE FLOW:
    type-consumers <type> [-n N]  Methods receiving this type as param
      [--module mod]              Filter by module
    type-producers <type> [-n N]  Methods returning this type
      [--module mod]              Filter by module
    type-flow <type> [--depth N]  Producer -> consumer chain
      [-n N]                      Limit per section (default 30)

  CROSS-MODULE CALLS:
    module-calls <from> <to>      Methods of <to> called from <from>
      [-n N]                      Limit results (default 50)
    module-api-usage <mod> [-n N] Top external methods used by module
    coupling <mod1> <mod2>        Coupling metrics between two modules

  PATTERNS:
    patterns <module> [-n N]      Detect patterns in a module
    pattern services [-n N]       All Service classes
    pattern drivers [-n N]        Driver stack classes
    pattern points [-n N]         Control points and extensions
    pattern views [-n N]          UI view/editor classes
    pattern extensions [-n N]     BExtension descendants
    pattern enums [-n N]          Frozen enum classes
    pattern structs [-n N]        Struct/value type classes
      [--module mod]              Filter by module

  BOG BRIDGE:
    bog-trace <path-or-type>      BOG component -> Java class + profile
      [--bog-index path]          Path to bog_index.json (auto)
    bog-classes                    Unique types in BOG + Java resolution
      [--bog-index path]          Path to bog_index.json (auto)
    bog-coverage                   Code-base vs BOG coverage
      [--bog-index path]          Path to bog_index.json (auto)

  EXCEPTION FLOW:
    throws <class> [-n N]         Methods with throws declarations
      [--module mod]              Filter by module
    catches <exception> [-n N]    Classes that catch this exception
      [--module mod]              Filter by module

  FULL-TEXT TOKEN SEARCH:
    token <word> [-n N]           Exact token search (instant via SQLite)
    token <word> --context [N]    Surrounding source lines (bare=2, N=custom)
    token <word> --module <mod>   Filter by module

  EXPORT/VISUALIZATION:
    export <class> --html         Standalone HTML class report
      [-o path]                   Output file (default: exports/<class>.html)
    export <module> --mermaid     Mermaid class diagram for a module
      [-o path]                   Output file (default: stdout)
    export <class> <method> --dot DOT call-chain graph for Graphviz
    export <module> --dot         DOT module class diagram
      [-o path]                   Output file (default: stdout)

  IMPACT ANALYSIS:
    impact <class>                Transitive impact: importers + callers + modules
    impact <class> <method>       Impact of changing a specific method
      [--depth N]                 Max transitive depth (default 3)

  FUZZY SEARCH:
    find <query> [-n N]           Fuzzy search in class names (camelCase-aware)
    find <query> --source         Also search in source tokens (slower)
    find <query> --module <mod>   Filter by module

  DEPRECATED CHAIN:
    deprecated [--module mod]     List @Deprecated classes and methods
      [-n N]                      Limit results (default 50)
    deprecated-users <class>      Who imports/calls a deprecated class
    deprecated-users <class> <m>  Who calls a deprecated method
      [-n N]                      Limit results (default 50)
    deprecated-risk               Deprecated usage risk per module
      [--module mod] [-n N]       Filter by module or limit

  CODE SIMILARITY:
    similar <class> [-n N]        Find classes with similar structure
    clones [--module mod] [-n N]  Top duplicate class pairs

  CONFIG & RESOURCE COUPLING:
    config-usage [--module mod]   Classes that read configuration
      [-n N]                      Limit results (default 50)
    config-keys [-n N]            Top config keys referenced in code
    resources-usage <module>      How resources of a module are used
      [-n N]                      Limit results (default 50)

  SERIALIZATION AUDIT:
    serial <class>                Serialization info for a class
    serial-audit [--module mod]   Audit: missing UIDs, custom read/write, risks
      [-n N]                      Limit results (default 50)
    serial-conflicts [-n N]       Classes with same serialVersionUID (collision)

  THREAD SAFETY:
    thread-safety <class>         Thread safety analysis for a class
    thread-scan [--module mod]    Module-wide thread safety summary
      [-n N]                      Limit results (default 50)

  NIAGARA LIFECYCLE:
    lifecycle <class>             Lifecycle methods for a class
    lifecycle --pattern <name>    Classes implementing a lifecycle method
      [--module mod] [-n N]       Filter by module and limit
    lifecycle-scan [--module mod] Scan lifecycle overrides across classes
      [-n N]                      Limit results (default 50)

  STRING CONSTANT INDEX:
    string-search <pattern> [-n N]  Regex search in indexed string literals
      [--module mod]                Filter by module
    string-constants <class> [-n N] All string literals in a class (categorized)

  SERVLET & WEB ROUTES:
    servlets [--module mod] [-n N]  List all web servlets with routes/handlers
    routes [--verb V] [-n N]        Map HTTP verbs -> servlet -> method
      [--module mod]                Filter by module
    servlet <class>                 Detailed info for a servlet class

  ORD RESOLUTION:
    ords [--scheme s] [-n N]        List all ORDs grouped by scheme prefix
      [--module mod]                Filter by module
    ord-usage <scheme> [-n N]       Classes that use a specific ORD scheme
      [--module mod]                Filter by module
    ord-flow <class>                ORDs created/resolved by a class

  SUBSCRIPTION & TOPICS:
    topics [--module mod] [-n N]    List @NiagaraTopic declarations
    subscribers <topic|class>       Who fires/subscribes to a topic or class
    pub-sub <module>                Publish->subscribe graph for a module

  BQL QUERY ANALYZER:
    bql [--module mod] [-n N]       List BQL/SQL queries in the corpus
      [--type bql|sql]              Filter by kind (BQL or SQL)
    bql-tables [--module mod]       Tables/sources most queried
    bql-class <class>               Queries used by a specific class

  PERMISSION & SECURITY:
    permissions [--module mod] [-n]  Classes with permission checks/auth methods
    permissions --declared           Declared <permissions> in META-INF/module.xml
      [--module m] [--type T]        T = station | all | workbench
    permission-flow <class>          Permission verification chain for a class
    credentials [--module mod] [-n]  Credential handling (password, token, secret)

  ALARM DOMAIN TRACING:
    alarm-flow [--module mod] [-n]   Classes in the alarm chain by role
    alarm-types                      Alarm types defined in the corpus
    alarm-trace <class>              Role of a class in the alarm flow

  ARCHITECTURE QUALITY:
    cycles [--depth N] [-n N]        Cyclic module dependencies (Tarjan SCC + DFS)
    god-classes [--threshold N] [-n] Classes with excessive methods/fields/deps
    layer-check [<module>]           Layer violations: RT must not import WB/UX

  COMPLEXITY METRICS:
    complexity <class>               LOC, methods, fields, fan-in/out, depth, score
    complexity-scan [--module] [-n]  Ranking of most complex classes
    metrics <module>                 Module-level complexity summary

  NATURAL LANGUAGE QUERY:
    ask <question>                  Answer questions by searching all indexes
                                    (heuristic-based, no LLM needed)

  EXTRAS:
    strings <pattern> [-n N]      Search string literals in source (live grep)
      [--module mod] [--class c]  Filter scope
    resources <module>            List non-Java resources in JAR
      [--type ext] [-n N]         Filter by extension
    trace-type <type>             Niagara type -> Java class
    version-diff <index-path>     Compare two class-index files

  BOOKMARKS & SESSION:
    bookmark <class> [note]       Save a class bookmark with optional note
    bookmarks [--sort S] [-n N]   List bookmarks (sort: time|name|access)
    unbookmark <class>            Remove a bookmark
    history [-n N] [--all]        Show persistent command history (last 500)
    history --grep <pattern>      Filter history by pattern
    @ClassName                    Reference a bookmarked class in any command

  CROSS-NAVIGATOR UNIFIED SEARCH:
    unified <query> [--limit N]   Search Help + Module + BOG simultaneously
    compare <class>               Docs vs implementation vs station usage

  RESEARCH AUTOMATION (Batch 4):
    integration-contract <class>  Real imports, instantiation pattern,
                                  entry-point methods, lifecycle, warnings
                                  [--min-callers N] [--resolve-virtual] [--json]
    example-mine <class>          Full method bodies that use a class
                                  [--pattern S] [--top N]
                                  [--exclude-tridium] [--include-docsource]
                                  [--min-lines N] [--json]
    virtual-callers <class> <m>   Aggregate callers via virtual dispatch
                                  [--depth N] [--no-self] [--json]
    feature-brief <feature>       One-command research brief for a domain
                                  [--depth quick|full] [--out path] [--json]
                                  Features: alarms schedules histories points
                                  bql topics programs servlets ords permissions
    slot-validate <class>         Pre-flight slot validation vs inheritance
                                  --add name:type[:default]
                                  [--kind property|action|topic] [--json]

  SESSION MANAGEMENT:
    session save <name>           Snapshot bookmarks + history as named session
    session load <name>           Restore a saved session as active
    session list [-n N]           List all saved sessions
    session note <text>           Add a note to the active session
    session export <name>         Export session to stdout
                                  [--as md|json] [--out <path>]
    session delete <name>         Delete a saved session

  REPL FEATURES:
    !N                            Repeat command N from session history
    !!                            Repeat last command
    focus <module>                Filter grep to a module
    unfocus                       Clear module filter
    cmd | grep <pattern>          Pipe output through grep
    cmd | count                   Count output lines
    help                          This help text
    quit / exit / q               Exit REPL

  TAB COMPLETION:
    <Tab>                         Complete command name
    class B<Tab>                  Complete class names (51K+)
    module alar<Tab>              Complete module names (926)
    --module ba<Tab>              Complete module after --module flag
    pattern s<Tab>                Complete pattern categories
    ui c<Tab>                     Complete UI sub-commands
"""


# ---------------------------------------------------------------------------
# REPL main loop
# ---------------------------------------------------------------------------

def cmd_repl(base_dir):
    """Launch the interactive REPL."""
    print("")
    print("  " + "=" * 55)
    print("  Module Navigator — Interactive REPL")
    print("  " + "=" * 55)
    print("")
    print("  Base: {}".format(base_dir))
    print("")

    # Pre-load indexes
    cache = _preload_indexes(base_dir)
    _patch_loaders(cache)

    # Tab completion
    tab_stats = _setup_tab_completion(cache)
    if tab_stats:
        print("  Tab completion: ENABLED ({:,} classes, {:,} modules)".format(
            tab_stats[0], tab_stats[1]))
    else:
        if readline is None:
            if sys.platform.startswith("win"):
                print("  Tab completion: DISABLED (install pyreadline3: pip install pyreadline3)")
            else:
                print("  Tab completion: DISABLED (readline stdlib not available — reinstall python with readline support)")
        else:
            print("  Tab completion: DISABLED (readline setup failed)")

    print("")
    print("  Type 'help' for commands, 'quit' to exit.")
    print("")

    from module_nav_lib.bookmarks import (
        migrate_old_bookmarks, record_history, resolve_bookmark_refs,
        _load_bookmarks, _load_history,
    )

    # Migrate old bookmarks.json (root) -> session/bookmarks.json
    migrated = migrate_old_bookmarks(base_dir)
    if migrated > 0:
        print("  Migrated {} old bookmark(s) to session/bookmarks.json".format(migrated))

    # Load session data
    bkmks = _load_bookmarks(base_dir)
    if bkmks:
        print("  Loaded {} bookmark(s) from session/".format(len(bkmks)))

    hist = _load_history(base_dir)
    if hist:
        print("  Loaded {} history entries from session/".format(len(hist)))

    session_history = []  # in-memory for !N recall within this session
    focus_module = None

    while True:
        # Build prompt
        try:
            prompt = "module-nav"
            if focus_module:
                prompt += "[{}]".format(focus_module)
            line = input(prompt + "> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Bye.")
            break

        if not line:
            continue

        if line in ("quit", "exit", "q"):
            print("  Bye.")
            break

        # --- History recall (session-local !N / !!) ---
        if line.startswith("!"):
            if line == "!!":
                if session_history:
                    line = session_history[-1]
                    print("  -> {}".format(line))
                else:
                    print("  (no history)")
                    continue
            else:
                try:
                    idx = int(line[1:]) - 1
                    if 0 <= idx < len(session_history):
                        line = session_history[idx]
                        print("  -> {}".format(line))
                    else:
                        print("  History index out of range (1-{}).".format(len(session_history)))
                        continue
                except ValueError:
                    print("  Usage: !N or !! (e.g. !3 to repeat command 3)")
                    continue

        # --- Help ---
        if line == "help":
            print(HELP_TEXT)
            session_history.append(line)
            record_history(base_dir, line)
            continue

        # Resolve bookmark @references
        line, _ = resolve_bookmark_refs(base_dir, line)

        # --- Focus ---
        if line.startswith("focus "):
            focus_module = line.split(None, 1)[1].strip()
            print("  Focused on module: {}".format(focus_module))
            print("")
            session_history.append(line)
            record_history(base_dir, line)
            continue

        if line == "unfocus":
            if focus_module:
                print("  Focus cleared (was: {}).".format(focus_module))
            else:
                print("  (no focus active)")
            focus_module = None
            print("")
            session_history.append(line)
            record_history(base_dir, line)
            continue

        # --- Record history (persistent + session) ---
        session_history.append(line)
        record_history(base_dir, line)

        # --- Pipe support ---
        pipe_filter = None
        pipe_count = False
        if " | " in line:
            pipe_parts = line.split(" | ", 1)
            line = pipe_parts[0].strip()
            pipe_cmd = pipe_parts[1].strip()

            if pipe_cmd == "count":
                pipe_count = True
            elif pipe_cmd.startswith("grep "):
                pipe_filter = pipe_cmd[5:].strip()
            else:
                pipe_filter = pipe_cmd  # treat as grep

        # --- Execute command ---
        cmd_parts = line.split(None, 1)
        cmd = cmd_parts[0].lower()
        arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

        if pipe_filter or pipe_count:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured = io.StringIO()
            try:
                _dispatch(cmd, arg, base_dir, focus_module)
            except Exception as e:
                sys.stdout = old_stdout
                print("  ERROR: {}".format(e))
                continue
            sys.stdout = old_stdout
            output = captured.getvalue()

            if pipe_count:
                line_count = len([l for l in output.splitlines() if l.strip()])
                print("  {} lines".format(line_count))
            elif pipe_filter:
                filter_lower = pipe_filter.lower()
                matched = 0
                for out_line in output.splitlines():
                    if filter_lower in out_line.lower():
                        print(out_line)
                        matched += 1
                if matched == 0:
                    print("  (no matches for '{}')".format(pipe_filter))
            print("")
        else:
            try:
                _dispatch(cmd, arg, base_dir, focus_module)
            except Exception as e:
                print("  ERROR: {}".format(e))
                import traceback
                traceback.print_exc()
