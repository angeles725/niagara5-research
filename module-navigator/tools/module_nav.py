#!/usr/bin/env python
"""
Module Navigator - CLI for searching Niagara N4 decompiled modules.

Navigates ALL decompiled code from 926 JARs (51K+ .java files),
including private classes, UI/Swing internals, and third-party libs.

Complements the Help Navigator (public API docs) with full source access.

Commands (Phase 0 - Inventory):
  inventory              Summary of all indexed modules
  module <name>          Detailed info for a specific submodule
  modules                List modules with filters
    --type <type>        Filter by type (rt, wb, ux, doc, se, standalone)
    --zkm                Show only ZKM-obfuscated modules
    --no-code            Show only modules without Java code
    --has-code           Show only modules with Java code
    --bytecode <ver>     Filter by bytecode version (e.g. 52)
    --top <N>            Show top N by java_files count

Commands (Phase 1 - Classes):
  class <name>           Look up a class by exact name
  search <pattern>       Search classes by glob pattern (e.g. "*Dialog*")
    -n <N>               Limit results (default 50)
  package <name>         List classes in a package
    --all                List all packages with class counts
    -n <N>               Limit results (default 50)

Commands (Phase 2 - Source Grep):
  grep <regex>           Regex search across all decompiled sources
    -n <N>               Max results (default 30)
    --module <mod>       Filter to a specific module
    --type <type>        Filter by type (rt, wb, ux)
  source <class>         Show info for a class
    --code               Show full source code with line numbers
    --grep <pattern>     Search regex within class source
  snippet <class> <method>  Extract a specific method's source code

Commands (Phase 6 - UI/Swing):
  ui dialogs [-n N]      List all dialog classes
  ui sizes [-n N]        List all hardcoded dimensions
  ui colors [-n N]       List all hardcoded colors
  ui fonts [-n N]        List all hardcoded fonts
  ui class <name>        Full UI details for a specific class
  ui customizable        Summary of all patcheable UI elements

Commands (Phase 3 - Hierarchy):
  hierarchy <class>        Show subclass tree (default depth 2)
    --depth <N>            Max tree depth
    --chain                Show inheritance chain to root
  implementors <iface>     Show classes implementing an interface
    -n <N>                 Limit results (default 50)

Commands (Phase 4 - Cross-references):
  xref <class>           Show imports and importers for a class
    --importers          Show only classes that import this class
    --imports            Show only what this class imports
    -n <N>               Limit results (default 50)
  deps <module>          Show module-level dependencies
    --reverse            Show modules that depend on this one
    -n <N>               Limit results (default 50)

Commands (Phase 5 - Methods):
  method <name>          All classes that define this method
    -n <N>               Limit results (default 50)
    --module <mod>       Filter by module
    --class <cls>        Show full signature in that class
  methods <class>        List all methods of a class
    -n <N>               Limit results (default 50)
    --public             Only public methods
    --grep <pattern>     Filter methods by regex pattern

Commands (Phase 7 - Annotations):
  slots <class>          List properties, actions, and topics
    --properties         Only properties
    --actions            Only actions
    --topics             Only topics
  slots --by-type <type> Classes with properties of that type
    [-n N]               Limit results (default 50)
    --module <mod>       Filter by module
  annotations <ann>      Classes with that annotation
    [-n N]               Limit results (default 50)
    --module <mod>       Filter by module

Commands (Phase 8 - CLI + REPL):
  stats [--json]         Corpus summary (modules, classes, indexes)
  profile <class>        Combined class + source + UI view
  repl                   Interactive REPL with all commands

Commands (Phase 9 - Help Navigator Integration):
  full-profile <class>   Combined view from BOTH navigators
    --help-dir <dir>     Help Navigator directory (auto-detected)
  cross-ref <class>      Docs + implementation + who uses it
    --help-dir <dir>     Help Navigator directory (auto-detected)

Commands (Phase 10 - Patch Workflow):
  patch-target <query>   Find patchable classes by natural language query
    -n <N>               Limit results (default 20)
  patch-plan <class>     Generate a complete patch plan for a class
  extract <module> <class>  Extract class to working directory for editing
    --patches-dir <dir>  Working directory (default: patches/)

Commands (Phase 11 - Analysis & Extras):
  orphans                Find classes never imported (dead code)
    [--module mod]       Filter by module
    [--type rt|wb|ux]    Filter by submodule type
    -n <N>               Limit results (default 50)
  deps-graph <module>    Module dependency graph
    --depth <N>          Traversal depth (default 1)
    --format mermaid|dot|text  Output format (default mermaid)
    --reverse            Show dependents instead of dependencies
  api-surface <module>   Public API surface summary
    -n <N>               Limit results (default 50)
  security-audit         Scan for insecure patterns
    [--module mod]       Filter by module
    -n <N>               Max findings per category (default 30)
  strings <pattern>      Search string literals across source
    [--module mod]       Filter by module
    [--class cls]        Filter by class
    -n <N>               Limit results (default 30)
  resources <module>     List non-Java resources in JAR
    [--type ext]         Filter by file extension
    -n <N>               Limit results (default 100)
  trace-type <type>      Map Niagara type to Java class
  version-diff <path>    Compare with another class-index.json
    -n <N>               Limit results (default 50)

Commands (Phase 12 - Call Graph):
  callers <class> <method>   Who calls this method
    -n <N>                   Limit results (default 50)
  callees <class> [<method>] What methods this class/method calls
    -n <N>                   Limit results (default 50)
  call-chain <class> <method> Transitive call chain (tree)
    --depth <N>              Max depth (default 2)
  hotspots [-n N]            Most-called methods (hub analysis)
    [--module mod]           Filter by module

Commands (Phase 13 - Fields):
  fields <class>             List all fields of a class
    -n <N>                   Limit results (default 50)
    --static                 Only static fields/constants
    --public                 Only public fields
    --grep <pattern>         Filter fields by regex pattern
  field <name>               All classes that define this field
    -n <N>                   Limit results (default 50)
    --module <mod>           Filter by module

Commands (Phase 14 - Type Flow):
  type-consumers <type>      Methods that receive this type as parameter
    -n <N>                   Limit results (default 50)
    --module <mod>           Filter by module
  type-producers <type>      Methods that return this type
    -n <N>                   Limit results (default 50)
    --module <mod>           Filter by module
  type-flow <type>           Producer -> consumer chain for a type
    --depth <N>              Trace depth via call graph (default 1)
    -n <N>                   Max results per section (default 30)

Commands (Phase 15 - Cross-Module Calls):
  module-calls <from> <to>   Methods of `to` called from `from`
    -n <N>                   Limit results (default 50)
  module-api-usage <mod>     Top external methods used by a module
    -n <N>                   Limit results (default 50)
  coupling <mod1> <mod2>     Coupling metrics between two modules

Commands (Phase 17 - Pattern Detection):
  patterns <module>          Detect architectural patterns in a module
    -n <N>                   Limit results per pattern (default 50)
  pattern <category> [-n N]  List all classes matching a pattern
    [--module mod]           Filter by module
    Categories: services, drivers, points, views, extensions, enums, structs

Commands (Phase 16 - BOG-Code Bridge):
  bog-trace <path-or-type>   Trace BOG component to Java class with profile
    [--bog-index path]       Path to bog_index.json (auto-detected)
  bog-classes                List unique Niagara types in BOG + resolution
    [--bog-index path]       Path to bog_index.json (auto-detected)
  bog-coverage               Code-base vs BOG coverage analysis
    [--bog-index path]       Path to bog_index.json (auto-detected)

Commands (Phase 19 - Exception Flow):
  throws <class>             Methods with throws declarations in a class
    -n <N>                   Limit results (default 50)
    --module <mod>           Filter by module (for duplicate class names)
  catches <exception>        Classes that catch this exception type
    -n <N>                   Limit results (default 50)
    --module <mod>           Filter by module

Commands (Phase 18 - Full-Text Token Search):
  token <word> [-n N]            Exact token search (instant via SQLite)
  token <word> --context [N]     Surrounding source lines (bare=2, N=custom)
  token <word> --module <mod>    Filter by module

Commands (Batch 6 - Developer Ergonomics):
  imports <class>                Raw .java header imports (incl. externals)
    --external-only              Only imports NOT resolved in the corpus
    -n <N>                       Max results (default 100)

Commands (Phase 20 - Export/Visualization):
  export <name> --html           Standalone HTML class report
  export <name> --mermaid        Mermaid class diagram for a module
  export <name> [<method>] --dot DOT graph (call-chain or module diagram)
    -o <path>                    Output file path (optional)

Commands (Phase 21 - Impact Analysis):
  impact <class>                 Transitive impact: callers + importers + modules
  impact <class> <method>        Impact of changing a specific method
    --depth <N>                  Max transitive depth (default 3)

Commands (Phase 22 - Fuzzy Search):
  find <query>                   Fuzzy search in class names (camelCase-aware)
    --source                     Also search in source tokens (slower)
    --module <mod>               Filter by module
    -n <N>                       Limit results (default 50)

Commands (Phase 23 - Deprecated Chain Analysis):
  deprecated [--module mod]      List @Deprecated classes and methods
    -n <N>                       Limit results (default 50)
  deprecated-users <class> [method]  Who uses something deprecated
    -n <N>                       Limit results (default 50)
  deprecated-risk [--module mod] Deprecated usage risk summary
    -n <N>                       Limit results (default 50)

Commands (Phase 24 - Code Similarity):
  similar <class> [-n N]         Find classes with similar structure
  clones [--module mod] [-n N]   Top duplicate class pairs

Commands (Phase 25 - Config & Resource Coupling):
  config-usage [--module mod] [-n N]  Classes that read configuration
  config-keys [-n N]                  Top config keys referenced in code
  resources-usage <module> [-n N]     How resources of a module are used

Commands (Phase 26 - Serialization Audit):
  serial <class>                      Serialization info for a class
  serial-audit [--module mod] [-n N]  Audit: missing UIDs, custom read/write, risks
  serial-conflicts [-n N]             Classes with same serialVersionUID (collision)

Commands (Phase 28 - Thread Safety):
  thread-safety <class>               Thread safety analysis for a class
  thread-scan [--module mod] [-n N]   Module-wide thread safety summary

Commands (Phase 29 - Niagara Lifecycle):
  lifecycle <class>                   Lifecycle methods implemented by a class
  lifecycle-scan [--module mod] [-n N] Classes with lifecycle overrides
  lifecycle --pattern <name>          Classes implementing a specific lifecycle
    [--module mod] [-n N]             Filter by module and limit results

Commands (Phase 31 - Natural Language Query):
  ask <question>                 Answer questions by searching all indexes

Commands (Phase 32 - Full-Stack Trace):
  full-stack-trace <class>.<method>  Call chain with semantic annotations
    --depth N                   Max traversal depth (default 6)
    --annotate all|data         Show all or only data-interesting annotations
    --json                      Output as JSON

Commands (Batch 5 - Runtime Validation):
  slot-validate <class>        Validate slot definitions against spec
  slot-collision               Cross-module slot name collisions
  ord-validate <module>         Validate ORDs referencing station tree paths
  resolve-audit <module>       Audit .resolve() calls for null-safety
  driver-cleanup-audit <module> Audit driver doStop() cleanup
  resource-leak <module>        Audit resource acquisitions for missing close()
  service-order <module>        Analyze service startup order issues
  module-health <module>        Consolidated A/B/C/D/F scorecard [--json]

Commands (Batch 8 - Security & Licensing):
  license-inspect              Parse installed .license files and summarize
    [--dir PATH]               Directory with .license files ($NIAGARA_HOME fallback)
    [--critical-features]      Show only bypass-enabling features table
  policy-inspect               Parse bin/policy/ triad (signing, java.policy, java.security)
    [--dir PATH]               Policy dir override
    [--verify-signatures]      Report NIAGARA SIGNATURE block presence
  trust-anchor-check <jar>     Verify JAR signer cert vs trust anchor (GO/NO-GO)
    [--anchor-dir PATH]        Override signing.properties location
    [--keytool PATH]           Explicit keytool binary (auto-detects)
  bypass-status                Report skipModuleValidation + SM-disable bypass state
    [--dir PATH]               Niagara install root override
  permissions --declared --summary
                                (new) Aggregate counts instead of row dump
  permissions -n N             (new) Default bumped 50 -> 200; -n now honored by --declared

Commands (Batch 9 - Module-level inspection & Feasibility):
  module <name> --permissions  Show the <permissions> block from module.xml
  module <name> --dependencies Show <dependencies> from module.xml
  module <name> --sma          Cross-ref module with license features (SMA, expiration, attrs)
  permission-report            Aggregate declared java-permissions into the 19 devguide groups
    [--group NAME]             Filter to one group; shows top 10 modules for it
    [--severity LEVEL]         MILD | MODERATE | SEVERE
  feasibility-check            Simulate if a module+cert would deploy against trust anchor
    --module-permissions PATH  Source module-permissions.xml
    --signing-cert PATH        Dev cert (PEM / DER / PKCS7 — anything keytool reads)
    [--anchor-dir PATH]        Override signing.properties
    [--keytool PATH]           Explicit keytool binary

Commands (Batch 10 - Discovery & Output formatting):
  explain <concept>            Cross-ref concept across devguide/guides/bajadoc + code
    [--help-root PATH]         Override niagara-help root
    [--no-content]             Skip content grep (filename-only, faster)
    [-n N]                     Max hits per doc tree (default 15)
  license-feature <name>       (enhanced) Now shows fallback hints when no hits:
                                related feature names, methods, classes + next commands
  license-inspect --md         (new) Markdown output with YAML frontmatter
  permission-report --md       (new) Markdown output with YAML frontmatter

Requires: Python 3.x (stdlib only, sqlite3)
Source:   /home/cristian/modules/Prototipos/modulos/organized/
Index:    indexes/module-inventory.json, indexes/class-index.json
"""

import argparse
import os
import sys

# Add parent of this script to path so module_nav_lib is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from module_nav_lib.inventory import cmd_inventory, cmd_module, cmd_modules, cmd_stats
from module_nav_lib.class_search import cmd_class, cmd_search, cmd_package
from module_nav_lib.grep_search import cmd_grep, cmd_source, cmd_snippet, cmd_source_batch
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
from module_nav_lib.bookmarks import cmd_bookmark, cmd_bookmarks, cmd_unbookmark, cmd_history
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
from module_nav_lib.repl import cmd_repl
from module_nav_lib.fullstack import cmd_full_stack_trace
from module_nav_lib.palette_lexicon_agents import cmd_palette_lexicon_agents


def detect_base_dir():
    """Auto-detect base directory (parent of tools/)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(script_dir)  # tools/ -> module-navigator/
    if os.path.isdir(os.path.join(base, "indexes")):
        return base
    return None


def main():
    parser = argparse.ArgumentParser(
        prog="module-nav",
        description="Module Navigator - CLI for Niagara N4 decompiled modules",
    )
    parser.add_argument(
        "--base-dir", "-d",
        help="Base directory (auto-detected if omitted)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # inventory
    sp_inv = subparsers.add_parser(
        "inventory", help="Summary of all indexed modules")

    # module <name> [--permissions|--dependencies|--sma]
    sp_mod = subparsers.add_parser(
        "module", help="Detailed info for a specific submodule")
    sp_mod.add_argument("name", help="Submodule name (e.g. workbench-wb)")
    sp_mod.add_argument(
        "--permissions", action="store_true", dest="mod_show_perms",
        help="Show only the <permissions> block from module.xml")
    sp_mod.add_argument(
        "--dependencies", action="store_true", dest="mod_show_deps",
        help="Show only the <dependencies> block from module.xml")
    sp_mod.add_argument(
        "--sma", action="store_true", dest="mod_show_sma",
        help="Cross-reference the module with installed license features "
             "(SMA-exempt, expiration, feature attributes)")

    # modules (list with filters)
    sp_mods = subparsers.add_parser(
        "modules", help="List modules with filters")
    sp_mods.add_argument(
        "--type", "-t", dest="mod_type",
        help="Filter by type: rt, wb, ux, doc, se, standalone")
    sp_mods.add_argument(
        "--zkm", action="store_true",
        help="Show only ZKM-obfuscated modules")
    sp_mods.add_argument(
        "--no-code", action="store_true",
        help="Show only modules without Java code")
    sp_mods.add_argument(
        "--has-code", action="store_true",
        help="Show only modules with Java code")
    sp_mods.add_argument(
        "--bytecode", "-b", type=int,
        help="Filter by bytecode version (e.g. 52 for Java 8)")
    sp_mods.add_argument(
        "--top", type=int,
        help="Show top N modules by java_files count")

    # --- Phase 1: Class commands ---

    # class <name>
    sp_cls = subparsers.add_parser(
        "class", help="Look up a class by exact name")
    sp_cls.add_argument("name", help="Class name (e.g. BLinkPad)")

    # search <pattern>
    sp_search = subparsers.add_parser(
        "search", help="Search classes by glob pattern")
    sp_search.add_argument("pattern", help="Glob pattern (e.g. '*Dialog*', 'BLink*')")
    sp_search.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # package <name> | --all
    sp_pkg = subparsers.add_parser(
        "package", help="List classes in a package")
    sp_pkg.add_argument("name", nargs="?", help="Package name (e.g. com.tridium.workbench.util)")
    sp_pkg.add_argument(
        "--all", action="store_true", dest="show_all",
        help="List all packages with class counts")
    sp_pkg.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # --- Phase 2: Source grep commands ---

    # grep <regex>
    sp_grep = subparsers.add_parser(
        "grep", help="Regex search across all decompiled sources")
    sp_grep.add_argument("pattern", help="Regex pattern (e.g. 'setPreferredSize')")
    sp_grep.add_argument(
        "-n", type=int, default=30,
        help="Max results to show (default 30)")
    sp_grep.add_argument(
        "--module", "-m", dest="grep_module",
        help="Filter to a specific module (e.g. workbench-wb)")
    sp_grep.add_argument(
        "--type", "-t", dest="grep_type",
        help="Filter by submodule type (rt, wb, ux)")

    # source <class>   or   source --batch A,B,C
    sp_src = subparsers.add_parser(
        "source", help="Show info or source code for a class")
    sp_src.add_argument("name", nargs="?", default=None,
                        help="Class name (e.g. BLinkPad). Omit when using --batch.")
    sp_src.add_argument(
        "--code", action="store_true",
        help="Show full source code with line numbers")
    sp_src.add_argument(
        "--grep", dest="src_grep",
        help="Search regex within the class source")
    sp_src.add_argument(
        "--batch", dest="src_batch", default=None,
        help="CSV of class names to read in sequence (e.g. BLinkPad,BAlarmService)")

    # snippet <class> <method>
    sp_snip = subparsers.add_parser(
        "snippet", help="Extract a specific method's source code")
    sp_snip.add_argument("class_name", help="Class name (e.g. BLinkPad)")
    sp_snip.add_argument("method", help="Method name (e.g. openInDialog)")

    # imports <class>           Batch 6 — raw .java header imports
    sp_imp = subparsers.add_parser(
        "imports",
        help="Raw import statements from the .java header (includes externals)")
    sp_imp.add_argument(
        "name",
        help="Class name or FQN (e.g. BAlarmService or javax.baja.alarm.BAlarmService)")
    sp_imp.add_argument(
        "--external-only", action="store_true", dest="imports_external",
        help="Only imports to classes NOT present in the decompiled corpus")
    sp_imp.add_argument(
        "-n", type=int, default=100,
        help="Max results to show (default 100)")

    # license-feature <name>            Batch 7 — FEATURE-4
    sp_lf = subparsers.add_parser(
        "license-feature",
        help="Callsites for checkFeature('tridium', '<name>')")
    sp_lf.add_argument("name", help="Feature name (e.g. historyImport)")
    sp_lf.add_argument(
        "-n", type=int, default=100,
        help="Max results to show (default 100)")

    # license-features                  Batch 7 — FEATURE-4 aggregate
    sp_lfs = subparsers.add_parser(
        "license-features",
        help="Top feature names referenced by checkFeature with counts")
    sp_lfs.add_argument(
        "-n", type=int, default=50,
        help="Max feature names to show (default 50)")

    # --- Phase 6: UI/Swing commands ---

    sp_ui = subparsers.add_parser(
        "ui", help="UI/Swing pattern search (dialogs, sizes, colors, fonts)")
    ui_sub = sp_ui.add_subparsers(dest="ui_command", help="UI sub-commands")

    # ui dialogs
    sp_ui_dlg = ui_sub.add_parser("dialogs", help="List all dialog classes")
    sp_ui_dlg.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # ui sizes
    sp_ui_sz = ui_sub.add_parser("sizes", help="List all hardcoded dimensions")
    sp_ui_sz.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # ui colors
    sp_ui_col = ui_sub.add_parser("colors", help="List all hardcoded colors")
    sp_ui_col.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # ui fonts
    sp_ui_fnt = ui_sub.add_parser("fonts", help="List all hardcoded fonts")
    sp_ui_fnt.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # ui class <name>
    sp_ui_cls = ui_sub.add_parser("class", help="Full UI details for a specific class")
    sp_ui_cls.add_argument("name", help="Class name (e.g. BLinkPad)")

    # ui customizable
    sp_ui_cust = ui_sub.add_parser(
        "customizable", help="Summary of all patcheable UI elements")

    # --- Phase 3: Hierarchy commands ---

    # hierarchy <class>
    sp_hier = subparsers.add_parser(
        "hierarchy", help="Show subclass tree or inheritance chain")
    sp_hier.add_argument("name", help="Class name (e.g. BEdgePane)")
    sp_hier.add_argument(
        "--depth", type=int, default=2,
        help="Max depth for subclass tree (default 2)")
    sp_hier.add_argument(
        "--chain", action="store_true",
        help="Show inheritance chain to root instead of subtree")

    # implementors <interface>
    sp_impl = subparsers.add_parser(
        "implementors", help="Show classes implementing an interface")
    sp_impl.add_argument("name", help="Interface name (e.g. BIDialogPane)")
    sp_impl.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # --- Phase 4: Xref commands ---

    # xref <class>
    sp_xref = subparsers.add_parser(
        "xref", help="Show cross-references (imports/importers) for a class")
    sp_xref.add_argument("name", help="Class name (e.g. BLinkPad)")
    sp_xref.add_argument(
        "--importers", action="store_true",
        help="Show only classes that import this class")
    sp_xref.add_argument(
        "--imports", action="store_true",
        help="Show only what this class imports")
    sp_xref.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # deps <module>
    sp_deps = subparsers.add_parser(
        "deps", help="Show module-level dependencies")
    sp_deps.add_argument("name", help="Module name (e.g. workbench-wb)")
    sp_deps.add_argument(
        "--reverse", action="store_true",
        help="Show modules that depend on this one")
    sp_deps.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # --- Phase 5: Method commands ---

    # method <name>
    sp_method = subparsers.add_parser(
        "method", help="Show classes that define a given method")
    sp_method.add_argument("name", help="Method name (e.g. setPreferredSize)")
    sp_method.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_method.add_argument(
        "--module", "-m", dest="method_module",
        help="Filter to a specific module")
    sp_method.add_argument(
        "--class", dest="method_class",
        help="Show full signature in that class")

    # methods <class>
    sp_methods = subparsers.add_parser(
        "methods", help="List all methods of a class")
    sp_methods.add_argument("name", help="Class name (e.g. BLinkPad)")
    sp_methods.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_methods.add_argument(
        "--public", action="store_true", dest="methods_public",
        help="Show only public methods")
    sp_methods.add_argument(
        "--grep", dest="methods_grep",
        help="Filter methods by regex pattern")

    # --- Phase 7: Annotation commands ---

    # slots
    sp_slots = subparsers.add_parser(
        "slots", help="Show Niagara slots (properties, actions, topics)")
    sp_slots.add_argument("name", nargs="?", help="Class name (e.g. BAlarmRecord)")
    sp_slots.add_argument(
        "--properties", action="store_true",
        help="Show only properties")
    sp_slots.add_argument(
        "--actions", action="store_true",
        help="Show only actions")
    sp_slots.add_argument(
        "--topics", action="store_true",
        help="Show only topics")
    sp_slots.add_argument(
        "--by-type", dest="by_type",
        help="Find classes with properties of this type (e.g. BStatusNumeric)")
    sp_slots.add_argument(
        "--module", "-m", dest="slots_module",
        help="Filter by module")
    sp_slots.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # annotations
    sp_ann = subparsers.add_parser(
        "annotations", help="List classes with a specific Niagara annotation")
    sp_ann.add_argument("name", help="Annotation name (e.g. NiagaraType, NiagaraAction)")
    sp_ann.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_ann.add_argument(
        "--module", "-m", dest="ann_module",
        help="Filter by module")

    # --- Phase 8: stats, profile, repl ---

    # stats
    sp_stats = subparsers.add_parser(
        "stats", help="Corpus summary (modules, classes, indexes)")
    sp_stats.add_argument(
        "--json", action="store_true",
        help="Output in JSON format")

    # profile <class>
    sp_profile = subparsers.add_parser(
        "profile", help="Combined class + source + UI view")
    sp_profile.add_argument("name", help="Class name (e.g. BLinkPad)")

    # repl
    sp_repl = subparsers.add_parser(
        "repl", help="Interactive REPL with all commands")

    # --- Phase 9: Help Navigator integration ---

    # full-profile <class>
    sp_fp = subparsers.add_parser(
        "full-profile", help="Combined view from BOTH navigators")
    sp_fp.add_argument("name", help="Class name (e.g. BAlarmService)")
    sp_fp.add_argument(
        "--help-dir", dest="help_dir",
        help="Help Navigator directory (auto-detected if omitted)")

    # cross-ref <class>
    sp_cr = subparsers.add_parser(
        "cross-ref", help="Docs + implementation + who uses it")
    sp_cr.add_argument("name", help="Class name (e.g. BWebServlet)")
    sp_cr.add_argument(
        "--help-dir", dest="help_dir",
        help="Help Navigator directory (auto-detected if omitted)")

    # --- Phase 10: Patch workflow commands ---

    # patch-target <query>
    sp_pt = subparsers.add_parser(
        "patch-target", help="Find patchable classes by natural language query")
    sp_pt.add_argument("query", help="Natural language query (e.g. 'Link dialog height')")
    sp_pt.add_argument(
        "-n", type=int, default=20,
        help="Max results to show (default 20)")
    sp_pt.add_argument(
        "--patches-dir", dest="patches_dir",
        help="Working directory for patches (default: patches/)")

    # patch-plan <class>
    sp_pp = subparsers.add_parser(
        "patch-plan", help="Generate a complete patch plan for a class")
    sp_pp.add_argument("name", help="Class name (e.g. BLinkPad)")
    sp_pp.add_argument(
        "--patches-dir", dest="patches_dir",
        help="Working directory for patches (default: patches/)")

    # extract <module> <class>
    sp_ext = subparsers.add_parser(
        "extract", help="Extract class to working directory for editing")
    sp_ext.add_argument("module", help="Module name (e.g. workbench-wb)")
    sp_ext.add_argument("class_name", help="Class name (e.g. BLinkPad)")
    sp_ext.add_argument(
        "--patches-dir", dest="patches_dir",
        help="Working directory for patches (default: patches/)")

    # --- Phase 11: Analysis & Extras ---

    # orphans
    sp_orph = subparsers.add_parser(
        "orphans", help="Find classes never imported (dead code)")
    sp_orph.add_argument(
        "--module", "-m", dest="orph_module",
        help="Filter by module")
    sp_orph.add_argument(
        "--type", "-t", dest="orph_type",
        help="Filter by submodule type (rt, wb, ux)")
    sp_orph.add_argument(
        "-n", type=int, default=50,
        help="Max results (default 50)")

    # deps-graph
    sp_dg = subparsers.add_parser(
        "deps-graph", help="Module dependency graph")
    sp_dg.add_argument("name", help="Module name (e.g. workbench-wb)")
    sp_dg.add_argument(
        "--depth", type=int, default=1,
        help="Traversal depth (default 1)")
    sp_dg.add_argument(
        "--format", dest="graph_format", default="mermaid",
        choices=["mermaid", "dot", "text"],
        help="Output format (default: mermaid)")
    sp_dg.add_argument(
        "--reverse", action="store_true",
        help="Show dependents instead of dependencies")

    # api-surface
    sp_api = subparsers.add_parser(
        "api-surface", help="Public API surface of a module")
    sp_api.add_argument("name", help="Module name (e.g. alarm-rt)")
    sp_api.add_argument(
        "-n", type=int, default=50,
        help="Max results (default 50)")

    # security-audit
    sp_sec = subparsers.add_parser(
        "security-audit", help="Scan for insecure patterns")
    sp_sec.add_argument(
        "--module", "-m", dest="sec_module",
        help="Filter by module (recommended)")
    sp_sec.add_argument(
        "-n", type=int, default=30,
        help="Max findings per category (default 30)")

    # strings
    sp_str = subparsers.add_parser(
        "strings", help="Search string literals across source")
    sp_str.add_argument("pattern", help="Regex pattern to match in strings")
    sp_str.add_argument(
        "--module", "-m", dest="str_module",
        help="Filter by module")
    sp_str.add_argument(
        "--class", dest="str_class",
        help="Filter by class name")
    sp_str.add_argument(
        "-n", type=int, default=30,
        help="Max results (default 30)")

    # resources
    sp_res = subparsers.add_parser(
        "resources", help="List non-Java resources in module JAR")
    sp_res.add_argument("name", help="Module name (e.g. workbench-wb)")
    sp_res.add_argument(
        "--type", dest="res_type",
        help="Filter by file extension (e.g. xml, properties)")
    sp_res.add_argument(
        "-n", type=int, default=100,
        help="Max results (default 100)")

    # trace-type
    sp_tt = subparsers.add_parser(
        "trace-type", help="Map Niagara type to Java class")
    sp_tt.add_argument("type_spec",
        help="Type spec (e.g. 'control:NumericWritable' or 'BAlarmService')")

    # version-diff
    sp_vd = subparsers.add_parser(
        "version-diff", help="Compare with another class-index.json")
    sp_vd.add_argument("other_index",
        help="Path to another class-index.json")
    sp_vd.add_argument(
        "-n", type=int, default=50,
        help="Max results per section (default 50)")

    # --- Phase 12: Call Graph commands ---

    # callers <class> <method>
    sp_callers = subparsers.add_parser(
        "callers", help="Who calls this method")
    sp_callers.add_argument("class_name", help="Class name (e.g. BLinkPad)")
    sp_callers.add_argument("method", help="Method name (e.g. setPreferredSize)")
    sp_callers.add_argument(
        "-n", type=int, default=50,
        help="Max results (default 50)")

    # callees <class> [<method>]
    sp_callees = subparsers.add_parser(
        "callees", help="What methods this class/method calls")
    sp_callees.add_argument("class_name", help="Class name (e.g. BLinkPad)")
    sp_callees.add_argument("method", nargs="?", default=None,
        help="Method name (optional; omit to see all class callees)")
    sp_callees.add_argument(
        "-n", type=int, default=50,
        help="Max results (default 50)")

    # call-chain <class> <method>
    sp_cc = subparsers.add_parser(
        "call-chain", help="Transitive call chain (tree)")
    sp_cc.add_argument("class_name", help="Class name (e.g. BAlarmService)")
    sp_cc.add_argument("method", help="Method name (e.g. routeAlarm)")
    sp_cc.add_argument(
        "--depth", type=int, default=2,
        help="Max tree depth (default 2)")

    # hotspots
    sp_hot = subparsers.add_parser(
        "hotspots", help="Most-called methods (hub analysis)")
    sp_hot.add_argument(
        "-n", type=int, default=20,
        help="Max results (default 20)")
    sp_hot.add_argument(
        "--module", "-m", dest="hot_module",
        help="Filter by module")

    # --- Phase 13: Field commands ---

    # fields <class>
    sp_fields = subparsers.add_parser(
        "fields", help="List all fields of a class")
    sp_fields.add_argument("name", help="Class name (e.g. BAlarmService)")
    sp_fields.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_fields.add_argument(
        "--static", action="store_true", dest="fields_static",
        help="Show only static fields/constants")
    sp_fields.add_argument(
        "--public", action="store_true", dest="fields_public",
        help="Show only public fields")
    sp_fields.add_argument(
        "--grep", dest="fields_grep",
        help="Filter fields by regex pattern")

    # field <name>
    sp_field = subparsers.add_parser(
        "field", help="Show classes that define a given field")
    sp_field.add_argument("name", help="Field name (e.g. alarmDb)")
    sp_field.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_field.add_argument(
        "--module", "-m", dest="field_module",
        help="Filter to a specific module")

    # --- Phase 14: Type Flow commands ---

    # type-consumers <type>
    sp_tc = subparsers.add_parser(
        "type-consumers", help="Methods that receive this type as parameter")
    sp_tc.add_argument("type_name", help="Type name (e.g. BAlarmRecord)")
    sp_tc.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_tc.add_argument(
        "--module", "-m", dest="tc_module",
        help="Filter to a specific module")

    # type-producers <type>
    sp_tp = subparsers.add_parser(
        "type-producers", help="Methods that return this type")
    sp_tp.add_argument("type_name", help="Type name (e.g. BOrd)")
    sp_tp.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_tp.add_argument(
        "--module", "-m", dest="tp_module",
        help="Filter to a specific module")

    # type-flow <type>
    sp_tf = subparsers.add_parser(
        "type-flow", help="Producer -> consumer chain for a type")
    sp_tf.add_argument("type_name", help="Type name (e.g. BAlarmRecord)")
    sp_tf.add_argument(
        "--depth", type=int, default=1,
        help="Trace depth via call graph (default 1)")
    sp_tf.add_argument(
        "-n", type=int, default=30,
        help="Max results per section (default 30)")

    # --- Phase 15: Cross-Module Calls commands ---

    # module-calls <from> <to>
    sp_mc = subparsers.add_parser(
        "module-calls", help="Methods of target module called from source module")
    sp_mc.add_argument("from_mod", help="Source module (e.g. alarm-rt)")
    sp_mc.add_argument("to_mod", help="Target module (e.g. baja)")
    sp_mc.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # module-api-usage <mod>
    sp_mau = subparsers.add_parser(
        "module-api-usage", help="Top external methods used by a module")
    sp_mau.add_argument("name", help="Module name (e.g. workbench-wb)")
    sp_mau.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # coupling <mod1> <mod2>
    sp_coup = subparsers.add_parser(
        "coupling", help="Coupling metrics between two modules")
    sp_coup.add_argument("mod1", help="First module (e.g. alarm-rt)")
    sp_coup.add_argument("mod2", help="Second module (e.g. baja)")

    # --- Phase 17: Pattern Detection commands ---

    # patterns <module>
    sp_patterns = subparsers.add_parser(
        "patterns", help="Detect architectural patterns in a module")
    sp_patterns.add_argument("name", help="Module name (e.g. alarm-rt)")
    sp_patterns.add_argument(
        "-n", type=int, default=50,
        help="Max results per pattern (default 50)")

    # pattern <category>
    sp_pattern = subparsers.add_parser(
        "pattern", help="List all classes matching a pattern category")
    sp_pattern.add_argument("category",
        help="Pattern category (services, drivers, points, views, extensions, enums, structs)")
    sp_pattern.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_pattern.add_argument(
        "--module", "-m", dest="pat_module",
        help="Filter to a specific module")

    # --- Phase 16: BOG-Code Bridge commands ---

    # bog-trace <path-or-type>
    sp_bt = subparsers.add_parser(
        "bog-trace", help="Trace BOG component to Java class with profile")
    sp_bt.add_argument("query",
        help="BOG path (e.g. '/Drivers/BacnetNetwork/Termo1') or type (e.g. 'c:NumericWritable')")
    sp_bt.add_argument(
        "--bog-index", dest="bog_index",
        help="Path to bog_index.json (auto-detected if omitted)")

    # bog-classes
    sp_bc = subparsers.add_parser(
        "bog-classes", help="List unique Niagara types in BOG + Java resolution")
    sp_bc.add_argument(
        "--bog-index", dest="bog_index",
        help="Path to bog_index.json (auto-detected if omitted)")

    # bog-coverage
    sp_bv = subparsers.add_parser(
        "bog-coverage", help="Code-base vs BOG coverage analysis")
    sp_bv.add_argument(
        "--bog-index", dest="bog_index",
        help="Path to bog_index.json (auto-detected if omitted)")

    # --- Phase 19: Exception Flow commands ---

    # throws <class>
    sp_throws = subparsers.add_parser(
        "throws", help="Methods with throws declarations in a class")
    sp_throws.add_argument("name", help="Class name (e.g. BAlarmService)")
    sp_throws.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_throws.add_argument(
        "--module", "-m", dest="throws_module",
        help="Filter to a specific module")

    # catches <exception>
    sp_catches = subparsers.add_parser(
        "catches", help="Classes that catch this exception type")
    sp_catches.add_argument("name", help="Exception type (e.g. IOException)")
    sp_catches.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_catches.add_argument(
        "--module", "-m", dest="catches_module",
        help="Filter to a specific module")

    # --- Phase 20: Export/Visualization commands ---

    # export <name> --html | --mermaid | --dot [method]
    sp_export = subparsers.add_parser(
        "export", help="Export class report or module diagram")
    sp_export.add_argument("name", help="Class name or module name")
    sp_export.add_argument("method", nargs="?", default=None,
                           help="Method name (for call-chain with --dot)")
    sp_export.add_argument(
        "--html", action="store_true",
        help="Generate standalone HTML class report")
    sp_export.add_argument(
        "--mermaid", action="store_true",
        help="Generate Mermaid class diagram for a module")
    sp_export.add_argument(
        "--dot", action="store_true",
        help="Generate DOT graph (call-chain if method given, module if not)")
    sp_export.add_argument(
        "-o", "--output", dest="export_output",
        help="Output file path (default: exports/<name>.html|.md|.dot)")

    # --- Phase 18: Full-Text Token Search commands ---

    # token <word>
    sp_token = subparsers.add_parser(
        "token", help="Exact token search (instant via SQLite index)")
    sp_token.add_argument("word", help="Token to search (e.g. setPreferredSize)")
    sp_token.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_token.add_argument(
        "--context", nargs="?", type=int, const=2, default=0, dest="token_context",
        metavar="N",
        help="Show N surrounding source lines per match "
             "(bare flag = 2, omitted = 0 compact, N = custom window)")
    sp_token.add_argument(
        "--module", "-m", dest="token_module",
        help="Filter to a specific module")

    # --- Phase 21: Impact Analysis commands ---

    # impact <class> [<method>] [--depth N]
    sp_impact = subparsers.add_parser(
        "impact", help="Transitive impact analysis for a class or method")
    sp_impact.add_argument("class_name", help="Class name (e.g. BLinkPad)")
    sp_impact.add_argument("method", nargs="?", default=None,
        help="Method name (optional; omit for class-level impact)")
    sp_impact.add_argument(
        "--depth", type=int, default=3,
        help="Max transitive depth (default 3)")

    # Phase 22: Fuzzy Search
    sp_find = subparsers.add_parser(
        "find", help="Fuzzy search in class names (camelCase-aware)")
    sp_find.add_argument("query", nargs="+",
        help="Search query words (e.g. 'alarm service')")
    sp_find.add_argument(
        "--source", action="store_true", default=False,
        help="Also search in source tokens (slower)")
    sp_find.add_argument(
        "--module", dest="find_module", default=None,
        help="Filter by module")
    sp_find.add_argument(
        "-n", type=int, default=50,
        help="Limit results (default 50)")

    # --- Phase 23: Deprecated Chain Analysis commands ---

    # deprecated [--module mod]
    sp_deprecated = subparsers.add_parser(
        "deprecated", help="List @Deprecated classes and methods")
    sp_deprecated.add_argument(
        "--module", "-m", dest="dep_module",
        help="Filter by module")
    sp_deprecated.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # deprecated-users <class> [method]
    sp_dep_users = subparsers.add_parser(
        "deprecated-users", help="Who uses a deprecated class or method")
    sp_dep_users.add_argument("class_name",
        help="Class name (e.g. BLegacyService)")
    sp_dep_users.add_argument("method", nargs="?", default=None,
        help="Method name (optional; omit for class-level)")
    sp_dep_users.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # deprecated-risk [--module mod]
    sp_dep_risk = subparsers.add_parser(
        "deprecated-risk", help="Deprecated usage risk summary")
    sp_dep_risk.add_argument(
        "--module", "-m", dest="deprisk_module",
        help="Filter by module")
    sp_dep_risk.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # --- Phase 24: Code Similarity Detection commands ---

    # similar <class> [-n N]
    sp_similar = subparsers.add_parser(
        "similar", help="Find classes with similar structure")
    sp_similar.add_argument("class_name",
        help="Class name (e.g. BNumericWritable)")
    sp_similar.add_argument(
        "-n", type=int, default=20,
        help="Limit results (default 20)")

    # clones [--module mod] [-n N]
    sp_clones = subparsers.add_parser(
        "clones", help="Top duplicate class pairs")
    sp_clones.add_argument(
        "--module", "-m", dest="clones_module",
        help="Filter by module")
    sp_clones.add_argument(
        "-n", type=int, default=20,
        help="Limit results (default 20)")

    # --- Phase 25: Config & Resource Coupling commands ---

    # config-usage [--module mod] [-n N]
    sp_cfgu = subparsers.add_parser(
        "config-usage", help="Classes that read configuration")
    sp_cfgu.add_argument(
        "--module", "-m", dest="cfgu_module",
        help="Filter by module")
    sp_cfgu.add_argument(
        "-n", type=int, default=50,
        help="Limit results (default 50)")

    # config-keys [-n N]
    sp_cfgk = subparsers.add_parser(
        "config-keys", help="Top config keys referenced in code")
    sp_cfgk.add_argument(
        "-n", type=int, default=50,
        help="Limit results (default 50)")

    # resources-usage <module> [-n N]
    sp_resu = subparsers.add_parser(
        "resources-usage", help="How resources of a module are used")
    sp_resu.add_argument("name", help="Module name (e.g. alarm-rt)")
    sp_resu.add_argument(
        "-n", type=int, default=50,
        help="Limit results (default 50)")

    # --- Phase 26: Serialization Audit commands ---

    # serial <class>
    sp_serial = subparsers.add_parser(
        "serial", help="Serialization info for a class")
    sp_serial.add_argument("class_name",
        help="Class name (e.g. BAlarmRecord)")

    # serial-audit [--module mod] [-n N]
    sp_sa = subparsers.add_parser(
        "serial-audit", help="Audit Serializable classes: missing UIDs, risks")
    sp_sa.add_argument(
        "--module", "-m", dest="sa_module",
        help="Filter by module")
    sp_sa.add_argument(
        "-n", type=int, default=50,
        help="Limit results (default 50)")

    # serial-conflicts [-n N]
    sp_sc = subparsers.add_parser(
        "serial-conflicts", help="Classes with same serialVersionUID (collision)")
    sp_sc.add_argument(
        "-n", type=int, default=30,
        help="Limit results (default 30)")

    # --- Phase 28: Thread Safety commands ---

    # thread-safety <class>
    sp_ts = subparsers.add_parser(
        "thread-safety", help="Thread safety analysis for a class")
    sp_ts.add_argument("class_name",
        help="Class name (e.g. BAlarmService)")

    # thread-scan [--module mod] [-n N]
    sp_tscan = subparsers.add_parser(
        "thread-scan", help="Module-wide thread safety summary")
    sp_tscan.add_argument(
        "--module", "-m", dest="ts_module",
        help="Filter by module")
    sp_tscan.add_argument(
        "-n", type=int, default=50,
        help="Limit results (default 50)")

    # --- Phase 29: Niagara Lifecycle commands ---

    # lifecycle <class>
    sp_lc = subparsers.add_parser(
        "lifecycle", help="Lifecycle methods implemented by a class")
    sp_lc.add_argument("class_name", nargs="?",
        help="Class name (e.g. BAlarmService)")
    sp_lc.add_argument(
        "--pattern", "-p", dest="lc_pattern",
        help="Show classes implementing a specific lifecycle (e.g. started)")
    sp_lc.add_argument(
        "--module", "-m", dest="lc_module",
        help="Filter by module")
    sp_lc.add_argument(
        "-n", type=int, default=50,
        help="Limit results (default 50)")

    # lifecycle-scan [--module mod] [-n N]
    sp_lcscan = subparsers.add_parser(
        "lifecycle-scan", help="Classes with lifecycle overrides")
    sp_lcscan.add_argument(
        "--module", "-m", dest="lcs_module",
        help="Filter by module")
    sp_lcscan.add_argument(
        "-n", type=int, default=50,
        help="Limit results (default 50)")

    # --- Phase 30: String Constant Index commands ---

    # string-search <pattern> [-n N] [--module mod]
    sp_ssearch = subparsers.add_parser(
        "string-search", help="Regex search in indexed string literals (instant via SQLite)")
    sp_ssearch.add_argument("pattern", help="Pattern to search (substring or regex)")
    sp_ssearch.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")
    sp_ssearch.add_argument(
        "--module", "-m", dest="ss_module",
        help="Filter to a specific module")

    # string-constants <class> [-n N]
    sp_sconst = subparsers.add_parser(
        "string-constants", help="All string literals in a class (categorized)")
    sp_sconst.add_argument("class_name", help="Class name (e.g. BAlarmService)")
    sp_sconst.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # --- Phase 31: Natural Language Query commands ---

    # ask <question>
    sp_ask = subparsers.add_parser(
        "ask", help="Answer questions by searching all indexes (heuristic NL query)")
    sp_ask.add_argument("question", nargs="+",
                        help="Question in natural language (e.g. 'how does alarm routing work')")

    # --- Phase 33: Servlet & Web Route Index commands ---

    # servlets [--module mod] [-n N]
    sp_servlets = subparsers.add_parser(
        "servlets", help="List all web servlets with their routes and HTTP handlers")
    sp_servlets.add_argument(
        "--module", "-m", dest="srv_module",
        help="Filter to a specific module")
    sp_servlets.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # routes [--verb GET|POST] [--module mod] [-n N]
    sp_routes = subparsers.add_parser(
        "routes", help="Map HTTP verbs to servlet classes and handler methods")
    sp_routes.add_argument(
        "--verb", dest="rt_verb",
        help="Filter by HTTP verb (GET, POST, PUT, DELETE, SERVICE)")
    sp_routes.add_argument(
        "--module", "-m", dest="rt_module",
        help="Filter to a specific module")
    sp_routes.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # servlet <class>
    sp_servlet = subparsers.add_parser(
        "servlet", help="Detailed info for a specific servlet class")
    sp_servlet.add_argument("class_name",
                            help="Servlet class name (e.g. BBoxServlet)")

    # Phase 34: ORD Resolution Graph commands

    # ords [--module mod] [--scheme s] [-n N]
    sp_ords = subparsers.add_parser(
        "ords", help="List all ORDs (Object Resolution Descriptors) grouped by scheme")
    sp_ords.add_argument(
        "--module", "-m", dest="ords_module",
        help="Filter to a specific module")
    sp_ords.add_argument(
        "--scheme", "-s", dest="ords_scheme",
        help="Filter by ORD scheme (station, slot, history, module, etc.)")
    sp_ords.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # ord-usage <scheme> [--module mod] [-n N]
    sp_ord_usage = subparsers.add_parser(
        "ord-usage", help="Classes that use a specific ORD scheme")
    sp_ord_usage.add_argument("scheme",
                              help="ORD scheme (e.g. station, history, module)")
    sp_ord_usage.add_argument(
        "--module", "-m", dest="ordu_module",
        help="Filter to a specific module")
    sp_ord_usage.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # ord-flow <class>
    sp_ord_flow = subparsers.add_parser(
        "ord-flow", help="ORDs created/resolved by a specific class")
    sp_ord_flow.add_argument("class_name",
                             help="Class name (e.g. BAlarmService)")

    # Phase 35: Subscription & Topic Graph commands

    # topics [--module mod] [-n N]
    sp_topics = subparsers.add_parser(
        "topics", help="List all @NiagaraTopic declarations with publishers/subscribers")
    sp_topics.add_argument(
        "--module", "-m", dest="topics_module",
        help="Filter to a specific module")
    sp_topics.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # subscribers <topic|class>
    sp_subscribers = subparsers.add_parser(
        "subscribers", help="Who subscribes to or fires a specific topic or class")
    sp_subscribers.add_argument("query",
                                help="Topic name (e.g. alarm) or class name (e.g. BAlarmService)")

    # pub-sub <module>
    sp_pub_sub = subparsers.add_parser(
        "pub-sub", help="Publish->subscribe graph for a module")
    sp_pub_sub.add_argument("module_name",
                            help="Module name (e.g. alarm-rt)")

    # Phase 36: BQL Query Analyzer commands

    # bql [--module mod] [--type bql|sql] [-n N]
    sp_bql = subparsers.add_parser(
        "bql", help="List BQL/SQL queries found in the corpus")
    sp_bql.add_argument(
        "--module", "-m", dest="bql_module",
        help="Filter to a specific module")
    sp_bql.add_argument(
        "--type", "-t", dest="bql_type",
        help="Filter by kind: bql or sql")
    sp_bql.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # bql-tables [--module mod] [-n N]
    sp_bql_tables = subparsers.add_parser(
        "bql-tables", help="Tables/sources most queried by BQL and SQL")
    sp_bql_tables.add_argument(
        "--module", "-m", dest="bqlt_module",
        help="Filter to a specific module")
    sp_bql_tables.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # bql-class <class>
    sp_bql_class = subparsers.add_parser(
        "bql-class", help="BQL/SQL queries used by a specific class")
    sp_bql_class.add_argument("class_name",
                              help="Class name (e.g. BAlarmService)")

    # permissions [--module mod] [-n N]   or   permissions --declared [...]
    sp_perms = subparsers.add_parser(
        "permissions", help="List classes with permission checks and auth methods")
    sp_perms.add_argument(
        "--module", "-m", dest="perm_module",
        help="Filter to a specific module")
    sp_perms.add_argument(
        "-n", type=int, default=200,
        help="Max results to show (default 200)")
    sp_perms.add_argument(
        "--declared", action="store_true",
        help="Scan META-INF/module.xml <permissions> blocks instead of callsites")
    sp_perms.add_argument(
        "--type", dest="perm_type", choices=["station", "all", "workbench"],
        help="Restrict --declared results to one permission type")
    sp_perms.add_argument(
        "--summary", action="store_true", dest="perm_summary",
        help="With --declared: show aggregate counts (per module/type/class) instead of rows")

    # license-inspect [--dir PATH] [--critical-features]
    sp_licins = subparsers.add_parser(
        "license-inspect",
        help="Parse installed .license files and aggregate features")
    sp_licins.add_argument(
        "--dir", dest="lic_dir",
        help="Directory with .license files (default: $NIAGARA_HOME/security/licenses)")
    sp_licins.add_argument(
        "--critical-features", action="store_true", dest="lic_critical_only",
        help="Only show critical (bypass-enabling) features — skip headers and summary")
    sp_licins.add_argument(
        "--md", action="store_true", dest="lic_md",
        help="Emit markdown with YAML frontmatter instead of ASCII table")

    # policy-inspect [--dir PATH] [--verify-signatures]
    sp_polins = subparsers.add_parser(
        "policy-inspect",
        help="Parse bin/policy/{signing.properties,java.policy,java.security}")
    sp_polins.add_argument(
        "--dir", dest="pol_dir",
        help="Directory containing policy files (default: $NIAGARA_HOME/bin/policy)")
    sp_polins.add_argument(
        "--verify-signatures", action="store_true", dest="pol_verify",
        help="Report signature block status (PKCS7 verification not implemented)")

    # trust-anchor-check <jar> [--anchor-dir PATH] [--keytool PATH]
    sp_trust = subparsers.add_parser(
        "trust-anchor-check",
        help="Verify a JAR's signer cert against the trust anchor")
    sp_trust.add_argument("jar", help="Path to the JAR file")
    sp_trust.add_argument(
        "--anchor-dir", dest="anchor_dir",
        help="Directory with signing.properties (default: $NIAGARA_HOME/bin/policy)")
    sp_trust.add_argument(
        "--keytool", dest="keytool_path",
        help="Path to keytool binary (auto-resolved from $NIAGARA_HOME/jre/bin)")

    # bypass-status [--dir PATH]
    sp_bypass = subparsers.add_parser(
        "bypass-status",
        help="Report skipModuleValidation & security-manager-disable bypass state")
    sp_bypass.add_argument(
        "--dir", dest="bypass_dir",
        help="Niagara install root (default: $NIAGARA_HOME)")

    # permission-report [--group NAME] [--severity LEVEL]
    sp_preport = subparsers.add_parser(
        "permission-report",
        help="Aggregate declared java-permissions into the 19 devguide groups")
    sp_preport.add_argument(
        "--group", dest="preport_group",
        help="Filter to one group (e.g. NETWORK_COMMUNICATION). "
             "When set, also shows top 10 modules for that group.")
    sp_preport.add_argument(
        "--severity", dest="preport_severity",
        choices=["MILD", "MODERATE", "SEVERE"],
        help="Filter groups by severity level")
    sp_preport.add_argument(
        "--md", action="store_true", dest="preport_md",
        help="Emit markdown with YAML frontmatter instead of ASCII table")

    # explain <concept> [--help-root PATH] [--no-content] [-n N]
    sp_explain = subparsers.add_parser(
        "explain",
        help="Cross-reference a concept across devguide/guides/bajadoc + code")
    sp_explain.add_argument("concept", help="Concept to explain (e.g. 'SMA', 'skipModuleValidation')")
    sp_explain.add_argument(
        "--help-root", dest="explain_help_root",
        help="Override niagara-help root (default: $NIAGARA_HOME/niagara-help)")
    sp_explain.add_argument(
        "--no-content", action="store_true", dest="explain_no_content",
        help="Only do filename matching (skip content grep — faster)")
    sp_explain.add_argument(
        "-n", type=int, default=15, dest="explain_n",
        help="Max hits per doc tree (default 15)")

    # feasibility-check --module-permissions X --signing-cert Y
    sp_feas = subparsers.add_parser(
        "feasibility-check",
        help="Simulate whether a module+cert would deploy against the trust anchor")
    sp_feas.add_argument(
        "--module-permissions", dest="feas_perms", required=True,
        help="Path to source module-permissions.xml")
    sp_feas.add_argument(
        "--signing-cert", dest="feas_cert", required=True,
        help="Path to signing certificate (PEM or DER, anything keytool accepts)")
    sp_feas.add_argument(
        "--anchor-dir", dest="feas_anchor",
        help="Override signing.properties location (default: $NIAGARA_HOME/bin/policy)")
    sp_feas.add_argument(
        "--keytool", dest="feas_keytool",
        help="Explicit keytool binary path")

    # permission-flow <class>
    sp_perm_flow = subparsers.add_parser(
        "permission-flow", help="Permission verification chain for a class")
    sp_perm_flow.add_argument("class_name",
                              help="Class name (e.g. BWebServlet)")

    # credentials [--module mod] [-n N]
    sp_creds = subparsers.add_parser(
        "credentials", help="Detect credential handling (password, token, secret)")
    sp_creds.add_argument(
        "--module", "-m", dest="cred_module",
        help="Filter to a specific module")
    sp_creds.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # alarm-flow [--module mod] [-n N]
    sp_alarm_flow = subparsers.add_parser(
        "alarm-flow", help="Classes in the alarm chain by role")
    sp_alarm_flow.add_argument(
        "--module", "-m", dest="alarm_module",
        help="Filter to a specific module")
    sp_alarm_flow.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # alarm-types
    subparsers.add_parser(
        "alarm-types", help="Alarm types defined in the corpus")

    # alarm-trace <class>
    sp_alarm_trace = subparsers.add_parser(
        "alarm-trace", help="Role of a class in the alarm flow")
    sp_alarm_trace.add_argument("class_name",
                                help="Class name (e.g. BAlarmService)")

    # cycles [--depth N] [-n N]
    sp_cycles = subparsers.add_parser(
        "cycles", help="Cyclic module dependencies (DFS/Tarjan)")
    sp_cycles.add_argument(
        "--depth", type=int, default=6,
        help="Max cycle depth for DFS (default 6)")
    sp_cycles.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # god-classes [--threshold N] [-n N]
    sp_god = subparsers.add_parser(
        "god-classes", help="Classes with excessive methods/fields/deps")
    sp_god.add_argument(
        "--threshold", "-t", type=int, default=100,
        help="Min score to qualify (default 100)")
    sp_god.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # layer-check [<module>]
    sp_layer = subparsers.add_parser(
        "layer-check", help="Layer violations: RT must not import WB/UX")
    sp_layer.add_argument(
        "layer_module", nargs="?", default=None,
        help="Module to check (omit for full scan)")

    # complexity <class>
    sp_cplx = subparsers.add_parser(
        "complexity", help="Complexity metrics for a class")
    sp_cplx.add_argument("class_name",
                         help="Class name (e.g. BAlarmService)")

    # complexity-scan [--module mod] [-n N]
    sp_cplx_scan = subparsers.add_parser(
        "complexity-scan", help="Ranking of most complex classes")
    sp_cplx_scan.add_argument(
        "--module", "-m", dest="cplx_module", default=None,
        help="Filter by module")
    sp_cplx_scan.add_argument(
        "-n", type=int, default=50,
        help="Max results to show (default 50)")

    # metrics <module>
    sp_metrics = subparsers.add_parser(
        "metrics", help="Module-level complexity summary")
    sp_metrics.add_argument("metrics_module",
                            help="Module name (e.g. alarm-rt)")

    # Phase 41: Bookmarks & Session commands
    sp_bkmk = subparsers.add_parser(
        "bookmark", help="Save a class bookmark with optional note")
    sp_bkmk.add_argument("class_name", help="Class name to bookmark")
    sp_bkmk.add_argument("note", nargs="?", default=None,
                         help="Optional note for the bookmark")

    sp_bkmks = subparsers.add_parser(
        "bookmarks", help="List all bookmarks")
    sp_bkmks.add_argument("--sort", dest="bkmk_sort", default="time",
                          choices=["time", "name", "access"],
                          help="Sort order (default: time)")
    sp_bkmks.add_argument("-n", type=int, default=None,
                          help="Limit results")

    sp_unbkmk = subparsers.add_parser(
        "unbookmark", help="Remove a bookmark")
    sp_unbkmk.add_argument("class_name", help="Class name to remove")

    sp_hist = subparsers.add_parser(
        "history", help="Show command history")
    sp_hist.add_argument("-n", type=int, default=50,
                         help="Limit results (default 50)")
    sp_hist.add_argument("--all", dest="hist_all", action="store_true",
                         help="Show all history (up to 500)")
    sp_hist.add_argument("--grep", dest="hist_grep", default=None,
                         help="Filter by pattern")

    # Phase 42: Cross-Navigator Unified Search
    sp_unified = subparsers.add_parser(
        "unified", help="Search Help + Module + BOG simultaneously")
    sp_unified.add_argument("query", help="Search query")
    sp_unified.add_argument("--limit", type=int, default=10,
                            help="Limit results per source (default 10)")

    sp_compare = subparsers.add_parser(
        "compare", help="Docs vs implementation vs station usage")
    sp_compare.add_argument("class_name", help="Class name to compare")

    # Phase 43: Research Automation (Batch 4)
    sp_ic = subparsers.add_parser(
        "integration-contract",
        help="Extract integration contract from real corpus usages")
    sp_ic.add_argument("class_name", help="Class name (e.g. BAlarmService)")
    sp_ic.add_argument("--min-callers", type=int, default=5,
                       dest="ic_min_callers",
                       help="Min external callers for entry-point methods (default 5)")
    sp_ic.add_argument("--json", action="store_true", dest="ic_json",
                       help="Structured JSON output")
    sp_ic.add_argument("--resolve-virtual", action="store_true",
                       dest="ic_resolve_virtual",
                       help="Aggregate entry-points via virtual dispatch")

    sp_em = subparsers.add_parser(
        "example-mine",
        help="Mine real usage examples (full method bodies) of a class")
    sp_em.add_argument("class_name", help="Class name (e.g. BAlarmService)")
    sp_em.add_argument("--pattern", dest="em_pattern", default=None,
                       help="Filter method bodies by substring (case-insensitive)")
    sp_em.add_argument("--top", type=int, default=3, dest="em_top",
                       help="Max examples to return (default 3)")
    sp_em.add_argument("--exclude-tridium", action="store_true",
                       dest="em_excl",
                       help="Skip com/tridium/* files")
    sp_em.add_argument("--include-docsource", action="store_true",
                       dest="em_incl_doc",
                       help="Include docSource-doc module (mirror copy; excluded by default)")
    sp_em.add_argument("--min-lines", type=int, default=5,
                       dest="em_min_lines",
                       help="Minimum method body lines (default 5)")
    sp_em.add_argument("--json", action="store_true", dest="em_json",
                       help="Structured JSON output")

    sp_vc = subparsers.add_parser(
        "virtual-callers",
        help="Aggregate callers via virtual dispatch (inheritance chain)")
    sp_vc.add_argument("class_name",
                       help="Base class (e.g. BControlPoint)")
    sp_vc.add_argument("method_name",
                       help="Method name (e.g. execute)")
    sp_vc.add_argument("--depth", type=int, default=0, dest="vc_depth",
                       help="Max subclass depth (0=unlimited, default 0)")
    sp_vc.add_argument("--no-self", action="store_true", dest="vc_no_self",
                       help="Exclude direct callers of the base class")
    sp_vc.add_argument("--json", action="store_true", dest="vc_json",
                       help="Structured JSON output")

    sp_fb = subparsers.add_parser(
        "feature-brief",
        help="One-command research brief for a Niagara feature domain")
    sp_fb.add_argument("feature",
                       help="Feature name (e.g. alarms, schedules, points)")
    sp_fb.add_argument("--depth", choices=["quick", "full"], default="quick",
                       dest="fb_depth",
                       help="quick=top-level, full=with code examples (default quick)")
    sp_fb.add_argument("--out", dest="fb_out", default=None,
                       help="Write brief to file instead of stdout")
    sp_fb.add_argument("--json", action="store_true", dest="fb_json",
                       help="Structured JSON output")

    sp_sv = subparsers.add_parser(
        "slot-validate",
        help="Pre-flight validation for @NiagaraProperty slots")
    sp_sv.add_argument("class_name",
                       help="Target class (e.g. BMyDashboardService)")
    sp_sv.add_argument("--add", required=True, dest="sv_add",
                       help="Slot spec: name:type[:defaultValue]")
    sp_sv.add_argument("--kind", choices=["property", "action", "topic"],
                       default="property", dest="sv_kind",
                       help="Slot kind (default: property)")
    sp_sv.add_argument("--json", action="store_true", dest="sv_json",
                       help="Structured JSON output")

    # Batch 5, Gap #8: Slot collision detection
    sp_sc = subparsers.add_parser(
        "slot-collision",
        help="Detect slot name collisions across modules")
    sp_sc.add_argument("--module", dest="sc_module",
                       help="Filter: only show collisions involving this module")
    sp_sc.add_argument("--json", action="store_true", dest="sc_json",
                       help="Structured JSON output")

    # Batch 5, Gap #9: ORD validation
    sp_ov = subparsers.add_parser(
        "ord-validate",
        help="Validate ORDs referencing non-existent station tree paths")
    sp_ov.add_argument("module",
                       help="Module name (e.g. alarm-rt)")
    sp_ov.add_argument("--json", action="store_true", dest="ov_json",
                       help="Structured JSON output")

    # Batch 5, Gap #10: resolve-audit
    sp_ra = subparsers.add_parser(
        "resolve-audit",
        help="Audit .resolve() calls for null-safety")
    sp_ra.add_argument("module",
                       help="Module name (e.g. alarm-rt)")
    sp_ra.add_argument("--json", action="store_true", dest="ra_json",
                       help="Structured JSON output")

    # Batch 5, Gap #12: driver-cleanup-audit
    sp_dca = subparsers.add_parser(
        "driver-cleanup-audit",
        help="Audit driver doStop() cleanup")
    sp_dca.add_argument("module",
                       help="Module name (e.g. bacnet-rt)")
    sp_dca.add_argument("--json", action="store_true", dest="dca_json",
                       help="Structured JSON output")

    # Batch 5, Gap #11: resource-leak
    sp_rl = subparsers.add_parser(
        "resource-leak",
        help="Audit resource acquisitions for missing close()")
    sp_rl.add_argument("module",
                       help="Module name (e.g. fox-rt)")
    sp_rl.add_argument("--json", action="store_true", dest="rl_json",
                       help="Structured JSON output")

    # Batch 5, Gap #13: service-order
    sp_so = subparsers.add_parser(
        "service-order",
        help="Analyze service startup order issues")
    sp_so.add_argument("module",
                       help="Module name (e.g. nmodsreflow-rt)")
    sp_so.add_argument("--json", action="store_true", dest="so_json",
                       help="Structured JSON output")

    # Batch 5, Gap #14: dependency-audit
    sp_da = subparsers.add_parser(
        "dependency-audit",
        help="Audit third-party and external dependencies")
    sp_da.add_argument("module",
                       help="Module name (e.g. alarm-rt)")
    sp_da.add_argument("--json", action="store_true", dest="da_json",
                       help="Structured JSON output")

    # Batch 5, Gap #21: module-health
    sp_mh = subparsers.add_parser(
        "module-health",
        help="Overall module health scorecard (A/B/C/D/F)")
    sp_mh.add_argument("module",
                       help="Module name (e.g. alarm-rt)")
    sp_mh.add_argument("--json", action="store_true", dest="mh_json",
                       help="Structured JSON output")

    # Phase 44: Session management (Batch 4, Gap #6)
    sp_sess = subparsers.add_parser(
        "session", help="Session save/load/export management")
    sess_sub = sp_sess.add_subparsers(dest="session_cmd", help="Session sub-commands")

    sp_sess_save = sess_sub.add_parser(
        "save", help="Save current bookmarks + history + notes as a session")
    sp_sess_save.add_argument("name", help="Session name")

    sp_sess_load = sess_sub.add_parser(
        "load", help="Restore a saved session as active")
    sp_sess_load.add_argument("name", help="Session name")

    sp_sess_list = sess_sub.add_parser(
        "list", help="List all saved sessions")
    sp_sess_list.add_argument(
        "-n", type=int, default=50, help="Limit results")

    sp_sess_note = sess_sub.add_parser(
        "note", help="Add a note to the active session")
    sp_sess_note.add_argument("text", help="Note text")

    sp_sess_exp = sess_sub.add_parser(
        "export", help="Export session to file or stdout")
    sp_sess_exp.add_argument("name", help="Session name")
    sp_sess_exp.add_argument(
        "--as", choices=["md", "json"], default="md", dest="export_fmt",
        help="Export format (default: md)")
    sp_sess_exp.add_argument(
        "--out", dest="export_out", help="Output file path")

    sp_sess_del = sess_sub.add_parser(
        "delete", help="Delete a saved session")
    sp_sess_del.add_argument("name", help="Session name")

    # Phase 32 (Gap #5): Full-Stack Trace command
    sp_fst = subparsers.add_parser(
        "full-stack-trace",
        help="Call chain with semantic annotations (input, BQL, data-source, serialize, output)")
    sp_fst.add_argument(
        "class_method",
        help="Class.method to trace (e.g. BAlarmServlet.doGet)")
    sp_fst.add_argument(
        "--depth", type=int, default=6,
        help="Max traversal depth (default 6)")
    sp_fst.add_argument(
        "--annotate", choices=["all", "data"], default="all",
        help="'all' = show all annotations; 'data' = only data-interesting nodes (default: all)")
    sp_fst.add_argument(
        "--json", action="store_true", dest="fst_json",
        help="Output trace as JSON instead of plain text")

    # palette-lexicon-agents <module>
    sp_pla = subparsers.add_parser(
        "palette-lexicon-agents",
        help="Palette entries, lexicon keys (+ dup-key report), and agent registrations for a module")
    sp_pla.add_argument(
        "module",
        help="Module name in organized/ (e.g. alarm)")
    sp_pla.add_argument(
        "--json", action="store_true", dest="pla_json",
        help="Structured JSON output")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Detect base directory
    base_dir = args.base_dir or detect_base_dir()
    if not base_dir:
        print("ERROR: Cannot detect base directory.")
        print("Use --base-dir or run from module-navigator/tools/")
        sys.exit(1)



    # Phase 0: Inventory / module listing commands
    if args.command == "inventory":
        cmd_inventory(base_dir)

    elif args.command == "module":
        cmd_module(
            base_dir,
            args.name,
            show_permissions=args.mod_show_perms,
            show_deps=args.mod_show_deps,
            show_sma=args.mod_show_sma,
        )

    elif args.command == "modules":
        cmd_modules(
            base_dir,
            type_filter=args.mod_type,
            zkm_only=args.zkm,
            no_code=args.no_code,
            has_code=args.has_code,
            bytecode=args.bytecode,
            top_n=args.top,
        )

    # Phase 1: Class commands
    elif args.command == "class":
        cmd_class(base_dir, args.name)

    elif args.command == "search":
        cmd_search(base_dir, args.pattern, limit=args.n)

    elif args.command == "package":
        cmd_package(base_dir, name=args.name, show_all=args.show_all, limit=args.n)

    # Phase 2: Source grep commands
    elif args.command == "grep":
        cmd_grep(
            base_dir, args.pattern,
            limit=args.n,
            module_filter=args.grep_module,
            type_filter=args.grep_type,
        )

    elif args.command == "source":
        if args.src_batch:
            cmd_source_batch(
                base_dir, args.src_batch,
                show_code=args.code,
                grep_pattern=args.src_grep,
            )
        elif args.name:
            cmd_source(
                base_dir, args.name,
                show_code=args.code,
                grep_pattern=args.src_grep,
            )
        else:
            print("  Usage: source <class> [--code] [--grep pat]")
            print("         source --batch A,B,C [--code] [--grep pat]")

    elif args.command == "snippet":
        cmd_snippet(base_dir, args.class_name, args.method)

    # Phase 6: UI/Swing commands
    elif args.command == "ui":
        if not args.ui_command:
            for action in subparsers._group_actions:
                for key, sp in action._name_parser_map.items():
                    if key == "ui":
                        sp.print_help()
                        break
            return

        if args.ui_command == "dialogs":
            cmd_ui_dialogs(base_dir, limit=args.n)
        elif args.ui_command == "sizes":
            cmd_ui_sizes(base_dir, limit=args.n)
        elif args.ui_command == "colors":
            cmd_ui_colors(base_dir, limit=args.n)
        elif args.ui_command == "fonts":
            cmd_ui_fonts(base_dir, limit=args.n)
        elif args.ui_command == "class":
            cmd_ui_class(base_dir, args.name)
        elif args.ui_command == "customizable":
            cmd_ui_customizable(base_dir)

    # Phase 3: Hierarchy commands
    elif args.command == "hierarchy":
        cmd_hierarchy(base_dir, args.name, depth=args.depth, show_chain=args.chain)

    elif args.command == "implementors":
        cmd_implementors(base_dir, args.name, limit=args.n)

    # Phase 4: Xref commands
    elif args.command == "xref":
        cmd_xref(
            base_dir, args.name,
            show_importers=args.importers,
            show_imports=args.imports,
            limit=args.n,
        )

    elif args.command == "deps":
        cmd_deps(base_dir, args.name, reverse=args.reverse, limit=args.n)

    # Phase 5: Method commands
    elif args.command == "method":
        cmd_method(
            base_dir, args.name,
            module_filter=args.method_module,
            class_filter=args.method_class,
            limit=args.n,
        )

    elif args.command == "methods":
        cmd_methods(
            base_dir, args.name,
            public_only=args.methods_public,
            grep_pattern=args.methods_grep,
            limit=args.n,
        )

    # Phase 7: Annotation commands
    elif args.command == "slots":
        cmd_slots(
            base_dir,
            class_name=args.name,
            show_properties=args.properties,
            show_actions=args.actions,
            show_topics=args.topics,
            by_type=args.by_type,
            module_filter=args.slots_module,
            limit=args.n,
        )

    elif args.command == "annotations":
        cmd_annotations(
            base_dir, args.name,
            module_filter=args.ann_module,
            limit=args.n,
        )

    # Phase 8: stats, profile, repl
    elif args.command == "stats":
        cmd_stats(base_dir, as_json=args.json)

    elif args.command == "profile":
        cmd_profile(base_dir, args.name)

    elif args.command == "repl":
        cmd_repl(base_dir)

    # Phase 9: Help Navigator integration
    elif args.command == "full-profile":
        cmd_full_profile(base_dir, args.name, help_dir=args.help_dir)

    elif args.command == "cross-ref":
        cmd_cross_ref(base_dir, args.name, help_dir=args.help_dir)

    # Phase 10: Patch workflow commands
    elif args.command == "patch-target":
        cmd_patch_target(base_dir, args.query, limit=args.n,
                         patches_dir=args.patches_dir)

    elif args.command == "patch-plan":
        cmd_patch_plan(base_dir, args.name, patches_dir=args.patches_dir)

    elif args.command == "extract":
        cmd_extract(base_dir, args.module, args.class_name,
                    patches_dir=args.patches_dir)

    # Phase 11: Analysis & Extras
    elif args.command == "orphans":
        cmd_orphans(base_dir, module_filter=args.orph_module,
                    type_filter=args.orph_type, limit=args.n)

    elif args.command == "deps-graph":
        cmd_deps_graph(base_dir, args.name, depth=args.depth,
                       fmt=args.graph_format, reverse=args.reverse)

    elif args.command == "api-surface":
        cmd_api_surface(base_dir, args.name, limit=args.n)

    elif args.command == "security-audit":
        cmd_security_audit(base_dir, module_filter=args.sec_module, limit=args.n)

    elif args.command == "strings":
        cmd_strings(base_dir, args.pattern,
                    module_filter=args.str_module,
                    class_filter=args.str_class,
                    limit=args.n)

    elif args.command == "resources":
        cmd_resources(base_dir, args.name, type_filter=args.res_type, limit=args.n)

    elif args.command == "trace-type":
        cmd_trace_type(base_dir, args.type_spec)

    elif args.command == "version-diff":
        cmd_version_diff(base_dir, args.other_index, limit=args.n)

    # Phase 12: Call Graph commands
    elif args.command == "callers":
        cmd_callers(base_dir, args.class_name, args.method, limit=args.n)

    elif args.command == "callees":
        cmd_callees(base_dir, args.class_name, method_name=args.method, limit=args.n)

    elif args.command == "call-chain":
        cmd_call_chain(base_dir, args.class_name, args.method, depth=args.depth)

    elif args.command == "hotspots":
        cmd_hotspots(base_dir, limit=args.n, module_filter=args.hot_module)

    # Phase 13: Field commands
    elif args.command == "fields":
        cmd_fields(
            base_dir, args.name,
            static_only=args.fields_static,
            public_only=args.fields_public,
            grep_pattern=args.fields_grep,
            limit=args.n,
        )

    elif args.command == "field":
        cmd_field(
            base_dir, args.name,
            module_filter=args.field_module,
            limit=args.n,
        )

    # Phase 14: Type Flow commands
    elif args.command == "type-consumers":
        cmd_type_consumers(
            base_dir, args.type_name,
            limit=args.n,
            module_filter=args.tc_module,
        )

    elif args.command == "type-producers":
        cmd_type_producers(
            base_dir, args.type_name,
            limit=args.n,
            module_filter=args.tp_module,
        )

    elif args.command == "type-flow":
        cmd_type_flow(
            base_dir, args.type_name,
            depth=args.depth,
            limit=args.n,
        )

    # Phase 15: Cross-Module Calls commands
    elif args.command == "module-calls":
        cmd_module_calls(base_dir, args.from_mod, args.to_mod, limit=args.n)

    elif args.command == "module-api-usage":
        cmd_module_api_usage(base_dir, args.name, limit=args.n)

    elif args.command == "coupling":
        cmd_coupling(base_dir, args.mod1, args.mod2)

    # Phase 17: Pattern Detection commands
    elif args.command == "patterns":
        cmd_patterns(base_dir, args.name, limit=args.n)

    elif args.command == "pattern":
        cmd_pattern(base_dir, args.category, limit=args.n,
                    module_filter=args.pat_module)

    # Phase 16: BOG-Code Bridge commands
    elif args.command == "bog-trace":
        cmd_bog_trace(base_dir, args.query, bog_index_path=args.bog_index)

    elif args.command == "bog-classes":
        cmd_bog_classes(base_dir, bog_index_path=args.bog_index)

    elif args.command == "bog-coverage":
        cmd_bog_coverage(base_dir, bog_index_path=args.bog_index)

    # Phase 19: Exception Flow commands
    elif args.command == "throws":
        cmd_throws(base_dir, args.name,
                   module_filter=args.throws_module,
                   limit=args.n)

    elif args.command == "catches":
        cmd_catches(base_dir, args.name,
                    module_filter=args.catches_module,
                    limit=args.n)

    # Phase 20: Export/Visualization commands
    elif args.command == "export":
        if args.html:
            cmd_export_html(base_dir, args.name, output_path=args.export_output)
        elif args.mermaid:
            cmd_export_mermaid(base_dir, args.name, output_path=args.export_output)
        elif args.dot:
            cmd_export_dot(base_dir, args.name, method=args.method,
                           output_path=args.export_output)
        else:
            print("ERROR: Specify --html, --mermaid, or --dot")
            print("  export <class> --html         HTML class report")
            print("  export <module> --mermaid      Mermaid class diagram")
            print("  export <class> <method> --dot  DOT call-chain graph")
            print("  export <module> --dot          DOT module class diagram")

    # Phase 18: Full-Text Token Search commands
    elif args.command == "token":
        cmd_token(
            base_dir, args.word,
            module_filter=args.token_module,
            show_context=(args.token_context > 0),
            context_lines=args.token_context,
            limit=args.n,
        )

    # Batch 6: Header imports (raw .java imports, includes externals)
    elif args.command == "imports":
        from module_nav_lib.header_imports import cmd_imports
        cmd_imports(
            base_dir, args.name,
            external_only=args.imports_external,
            limit=args.n,
        )

    # Batch 7: License feature gating (FEATURE-4)
    elif args.command == "license-feature":
        from module_nav_lib.license_features import cmd_license_feature
        cmd_license_feature(base_dir, args.name, limit=args.n)

    elif args.command == "license-features":
        from module_nav_lib.license_features import cmd_license_features
        cmd_license_features(base_dir, limit=args.n)

    # Phase 21: Impact Analysis commands
    elif args.command == "impact":
        cmd_impact(base_dir, args.class_name,
                   method_name=args.method,
                   depth=args.depth)

    # Phase 22: Fuzzy Search commands
    elif args.command == "find":
        cmd_find(base_dir, " ".join(args.query),
                 source_mode=args.source,
                 module_filter=args.find_module,
                 limit=args.n)

    # Phase 23: Deprecated Chain Analysis commands
    elif args.command == "deprecated":
        cmd_deprecated(base_dir, module_filter=args.dep_module, limit=args.n)

    elif args.command == "deprecated-users":
        cmd_deprecated_users(base_dir, args.class_name,
                             method_name=args.method, limit=args.n)

    elif args.command == "deprecated-risk":
        cmd_deprecated_risk(base_dir, module_filter=args.deprisk_module,
                            limit=args.n)

    # Phase 24: Code Similarity Detection commands
    elif args.command == "similar":
        cmd_similar(base_dir, args.class_name, limit=args.n)

    elif args.command == "clones":
        cmd_clones(base_dir, module_filter=args.clones_module, limit=args.n)

    # Phase 25: Config & Resource Coupling commands
    elif args.command == "config-usage":
        cmd_config_usage(base_dir, module_filter=args.cfgu_module, limit=args.n)

    elif args.command == "config-keys":
        cmd_config_keys(base_dir, limit=args.n)

    elif args.command == "resources-usage":
        cmd_resources_usage(base_dir, args.name, limit=args.n)

    # Phase 26: Serialization Audit commands
    elif args.command == "serial":
        cmd_serial(base_dir, args.class_name)

    elif args.command == "serial-audit":
        cmd_serial_audit(base_dir, module_filter=args.sa_module, limit=args.n)

    elif args.command == "serial-conflicts":
        cmd_serial_conflicts(base_dir, limit=args.n)

    # Phase 28: Thread Safety commands
    elif args.command == "thread-safety":
        cmd_thread_safety(base_dir, args.class_name)

    elif args.command == "thread-scan":
        cmd_thread_scan(base_dir, module_filter=args.ts_module, limit=args.n)

    # Phase 29: Niagara Lifecycle commands
    elif args.command == "lifecycle":
        if args.lc_pattern:
            cmd_lifecycle_pattern(base_dir, args.lc_pattern,
                                 module_filter=args.lc_module, limit=args.n)
        elif args.class_name:
            cmd_lifecycle(base_dir, args.class_name)
        else:
            print("  Usage: lifecycle <class>  or  lifecycle --pattern <name>")

    elif args.command == "lifecycle-scan":
        cmd_lifecycle_scan(base_dir, module_filter=args.lcs_module, limit=args.n)

    # Phase 30: String Constant Index commands
    elif args.command == "string-search":
        cmd_string_search(base_dir, args.pattern,
                          module_filter=args.ss_module, limit=args.n)

    elif args.command == "string-constants":
        cmd_string_constants(base_dir, args.class_name, limit=args.n)

    # Phase 31: Natural Language Query commands
    elif args.command == "ask":
        cmd_ask(base_dir, " ".join(args.question))

    # Phase 33: Servlet & Web Route Index commands
    elif args.command == "servlets":
        cmd_servlets(base_dir, module_filter=args.srv_module, limit=args.n)

    elif args.command == "routes":
        cmd_routes(base_dir, verb_filter=args.rt_verb,
                   module_filter=args.rt_module, limit=args.n)

    elif args.command == "servlet":
        cmd_servlet(base_dir, args.class_name)

    # Phase 34: ORD Resolution Graph commands
    elif args.command == "ords":
        cmd_ords(base_dir, module_filter=args.ords_module,
                 scheme_filter=args.ords_scheme, limit=args.n)

    elif args.command == "ord-usage":
        cmd_ord_usage(base_dir, args.scheme,
                      module_filter=args.ordu_module, limit=args.n)

    elif args.command == "ord-flow":
        cmd_ord_flow(base_dir, args.class_name)

    # Phase 35: Subscription & Topic Graph commands
    elif args.command == "topics":
        cmd_topics(base_dir, module_filter=args.topics_module, limit=args.n)

    elif args.command == "subscribers":
        cmd_subscribers(base_dir, args.query)

    elif args.command == "pub-sub":
        cmd_pub_sub(base_dir, args.module_name)

    # Phase 36: BQL Query Analyzer commands
    elif args.command == "bql":
        cmd_bql(base_dir, module_filter=args.bql_module,
                type_filter=args.bql_type, limit=args.n)

    elif args.command == "bql-tables":
        cmd_bql_tables(base_dir, module_filter=args.bqlt_module, limit=args.n)

    elif args.command == "bql-class":
        cmd_bql_class(base_dir, args.class_name)

    # Phase 37: Permission & Security Model commands
    elif args.command == "license-inspect":
        from module_nav_lib.license_inspect import cmd_license_inspect
        cmd_license_inspect(
            base_dir,
            license_dir=args.lic_dir,
            critical_only=args.lic_critical_only,
            md_output=args.lic_md,
        )

    elif args.command == "policy-inspect":
        from module_nav_lib.policy_inspect import cmd_policy_inspect
        cmd_policy_inspect(
            base_dir,
            policy_dir=args.pol_dir,
            verify_signatures=args.pol_verify,
        )

    elif args.command == "trust-anchor-check":
        from module_nav_lib.trust_anchor import cmd_trust_anchor_check
        cmd_trust_anchor_check(
            base_dir,
            jar_path=args.jar,
            anchor_dir=args.anchor_dir,
            keytool=args.keytool_path,
        )

    elif args.command == "bypass-status":
        from module_nav_lib.bypass_status import cmd_bypass_status
        cmd_bypass_status(base_dir, niagara_dir=args.bypass_dir)

    elif args.command == "permission-report":
        from module_nav_lib.permission_report import cmd_permission_report
        cmd_permission_report(
            base_dir,
            group_filter=args.preport_group,
            severity_filter=args.preport_severity,
            md_output=args.preport_md,
        )

    elif args.command == "explain":
        from module_nav_lib.explain import cmd_explain
        cmd_explain(
            base_dir,
            args.concept,
            help_root=args.explain_help_root,
            no_content=args.explain_no_content,
            limit=args.explain_n,
        )

    elif args.command == "feasibility-check":
        from module_nav_lib.feasibility import cmd_feasibility_check
        cmd_feasibility_check(
            base_dir,
            module_permissions=args.feas_perms,
            signing_cert=args.feas_cert,
            anchor_dir=args.feas_anchor,
            keytool=args.feas_keytool,
        )

    elif args.command == "permissions":
        from module_nav_lib.permissions import cmd_permissions_cli
        cmd_permissions_cli(
            base_dir,
            declared=args.declared,
            module_filter=args.perm_module,
            type_filter=args.perm_type,
            limit=args.n,
            summary=args.perm_summary,
        )

    elif args.command == "permission-flow":
        cmd_permission_flow(base_dir, args.class_name)

    elif args.command == "credentials":
        cmd_credentials(base_dir, module_filter=args.cred_module, limit=args.n)

    # Phase 38: Alarm Domain Tracer commands
    elif args.command == "alarm-flow":
        cmd_alarm_flow(base_dir, module_filter=args.alarm_module, limit=args.n)

    elif args.command == "alarm-types":
        cmd_alarm_types(base_dir)

    elif args.command == "alarm-trace":
        cmd_alarm_trace(base_dir, args.class_name)

    # Phase 39: Cyclic Dependency & Architecture commands
    elif args.command == "cycles":
        cmd_cycles(base_dir, max_depth=args.depth, limit=args.n)

    elif args.command == "god-classes":
        cmd_god_classes(base_dir, threshold=args.threshold, limit=args.n)

    elif args.command == "layer-check":
        cmd_layer_check(base_dir, module_filter=args.layer_module)

    # Phase 40: Complexity Metrics commands
    elif args.command == "complexity":
        cmd_complexity(base_dir, args.class_name)

    elif args.command == "complexity-scan":
        cmd_complexity_scan(base_dir, module_filter=args.cplx_module, limit=args.n)

    elif args.command == "metrics":
        cmd_metrics(base_dir, args.metrics_module)

    # Phase 41: Bookmarks & Session commands
    elif args.command == "bookmark":
        cmd_bookmark(base_dir, args.class_name, note=args.note)

    elif args.command == "bookmarks":
        cmd_bookmarks(base_dir, sort_by=args.bkmk_sort, limit=args.n)

    elif args.command == "unbookmark":
        cmd_unbookmark(base_dir, args.class_name)

    elif args.command == "history":
        cmd_history(base_dir, limit=args.n, show_all=args.hist_all,
                    grep_pattern=args.hist_grep)

    # Phase 42: Cross-Navigator Unified Search
    elif args.command == "unified":
        cmd_unified(base_dir, args.query, limit=args.limit)

    elif args.command == "compare":
        cmd_compare(base_dir, args.class_name)

    # Phase 43: Research Automation (Batch 4)
    elif args.command == "integration-contract":
        cmd_integration_contract(
            base_dir, args.class_name,
            min_callers=args.ic_min_callers,
            as_json=args.ic_json,
            resolve_virtual=args.ic_resolve_virtual,
        )

    elif args.command == "example-mine":
        cmd_example_mine(
            base_dir, args.class_name,
            pattern=args.em_pattern,
            top=args.em_top,
            exclude_tridium=args.em_excl,
            min_lines=args.em_min_lines,
            as_json=args.em_json,
            include_docsource=args.em_incl_doc,
        )

    elif args.command == "virtual-callers":
        cmd_virtual_callers(
            base_dir, args.class_name, args.method_name,
            max_depth=args.vc_depth,
            include_self=not args.vc_no_self,
            as_json=args.vc_json,
        )

    elif args.command == "feature-brief":
        cmd_feature_brief(
            base_dir, args.feature,
            depth=args.fb_depth,
            out_path=args.fb_out,
            as_json=args.fb_json,
        )

    elif args.command == "slot-validate":
        cmd_slot_validate(
            base_dir, args.class_name,
            add_spec=args.sv_add,
            kind=args.sv_kind,
            as_json=args.sv_json,
        )

    elif args.command == "slot-collision":
        cmd_slot_collision(
            base_dir,
            module_filter=args.sc_module,
            as_json=args.sc_json,
        )

    elif args.command == "ord-validate":
        cmd_ord_validate(
            base_dir,
            args.module,
            as_json=args.ov_json,
        )

    elif args.command == "resolve-audit":
        cmd_resolve_audit(
            base_dir,
            args.module,
            as_json=args.ra_json,
        )

    # Batch 5, Gap #12: driver-cleanup-audit
    elif args.command == "driver-cleanup-audit":
        cmd_driver_cleanup_audit(
            base_dir,
            args.module,
            as_json=args.dca_json,
        )

    # Batch 5, Gap #11: resource-leak
    elif args.command == "resource-leak":
        cmd_resource_leak(
            base_dir,
            args.module,
            as_json=args.rl_json,
        )

    # Batch 5, Gap #13: service-order
    elif args.command == "service-order":
        cmd_service_order(
            base_dir,
            args.module,
            as_json=args.so_json,
        )

    # Batch 5, Gap #14: dependency-audit
    elif args.command == "dependency-audit":
        cmd_dependency_audit(
            base_dir,
            args.module,
            as_json=args.da_json,
        )

    # Batch 5, Gap #21: module-health
    elif args.command == "module-health":
        cmd_module_health(
            base_dir,
            args.module,
            as_json=args.mh_json,
        )

    # Phase 44: Session management
    elif args.command == "session":
        if args.session_cmd == "save":
            cmd_session_save(base_dir, args.name)
        elif args.session_cmd == "load":
            cmd_session_load(base_dir, args.name)
        elif args.session_cmd == "list":
            cmd_session_list(base_dir, limit=args.n)
        elif args.session_cmd == "note":
            cmd_session_note(base_dir, args.text)
        elif args.session_cmd == "export":
            cmd_session_export(
                base_dir, args.name,
                fmt=args.export_fmt,
                out_path=args.export_out,
            )
        elif args.session_cmd == "delete":
            cmd_session_delete(base_dir, args.name)

    # Phase 32 (Gap #5): Full-Stack Trace command
    elif args.command == "full-stack-trace":
        cmd_full_stack_trace(
            base_dir, args.class_method,
            depth=args.depth,
            annotate=args.annotate,
            as_json=args.fst_json,
        )

    # Palette / Lexicon / Agents census
    elif args.command == "palette-lexicon-agents":
        cmd_palette_lexicon_agents(
            base_dir,
            args.module,
            as_json=args.pla_json,
        )


if __name__ == "__main__":
    main()
