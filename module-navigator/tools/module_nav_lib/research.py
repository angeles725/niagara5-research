"""
Feature Brief generator for Module Navigator (Batch 4, Gap #1).

One-command research brief that orchestrates Help Nav + Module Nav + BOG Nav
to produce a ready-to-paste Markdown report for a Niagara feature domain.
Replaces the 15-command manual protocol from the research prompt.

Commands:
  feature-brief <feature>
    [--depth quick|full]   quick = top-level; full = includes code examples (default quick)
    [--out <path>]         Write brief to file instead of stdout
    [--json]               Structured JSON output

Features: alarms, schedules, histories, points, bql, topics, programs,
          servlets, ords, permissions

Reuses existing indexes (no new builders):
  class-index.json, xref-index.json, method-index.json, inheritance.json,
  callgraph-index.json, annotations-index.json, token-index.db,
  Help Nav indexes, bog_index.json
"""

import io
import json
import os
import sys
from collections import Counter


# ---------------------------------------------------------------------------
# Feature Registry
# ---------------------------------------------------------------------------

FEATURE_REGISTRY = {
    "alarms": {
        "base": "BAlarmService",
        "pkg": "javax.baja.alarm",
        "description": "Alarm management service (station singleton)",
        "resolve_virtual": False,
        "gotchas": [
            "BAlarmService is a station singleton -- resolve via BOrd, do NOT instantiate.",
            "BAlarmRecord should NOT be constructed manually -- use BAlarmSourceExt on points.",
            "offnormalText may arrive HTML-encoded on legacy stations.",
        ],
    },
    "schedules": {
        "base": "BWeekSchedule",
        "pkg": "javax.baja.schedule",
        "description": "Weekly schedule component for timed automation",
        "resolve_virtual": True,
        "gotchas": [
            "Schedules are components, not services -- attach under a device or folder.",
            "BWeekSchedule stores events in a 7-day matrix; BCalendarSchedule is separate.",
            "Use getEffectiveOutput() for the current calculated value, not raw slot reads.",
        ],
    },
    "histories": {
        "base": "BHistoryService",
        "pkg": "javax.baja.history",
        "description": "History collection and storage service (station singleton)",
        "resolve_virtual": False,
        "gotchas": [
            "BHistoryService is a station singleton -- resolve via BOrd.",
            "History data lives in BHistoryDatabase, not in the service itself.",
            "Use BHistoryExt on points to enable collection; do not call record() directly.",
            "History IDs are BHistoryId, not String -- resolve via BHistoryService.getHistory().",
        ],
    },
    "points": {
        "base": "BControlPoint",
        "pkg": "javax.baja.control",
        "description": "Base class for all control points (numeric, boolean, enum, string)",
        "resolve_virtual": True,
        "gotchas": [
            "Never subclass BControlPoint directly -- use BNumericWritable, BBooleanWritable, etc.",
            "The execute() cycle is: execute() -> doExecute() -> onExecute() (Template Method).",
            "Point status is BStatusValue, not raw value -- always check .getStatus() flags.",
            "Use readValue()/writeValue() for data access, not direct slot manipulation.",
        ],
    },
    "bql": {
        "base": "BqlQuery",
        "pkg": "javax.baja.bql",
        "description": "Baja Query Language query execution",
        "resolve_virtual": False,
        "gotchas": [
            "BQL queries run against the component tree, not a relational DB.",
            "Always close Cursor results (use try-finally or Context).",
            "BQL injection is possible if query strings include user input -- sanitize.",
            "Use BOrd.make(\"local:|bql:select ...\") to execute BQL via ORD resolution.",
        ],
    },
    "topics": {
        "base": "BTopic",
        "pkg": "javax.baja.sys",
        "description": "Pub/sub topic for event-driven communication",
        "resolve_virtual": True,
        "gotchas": [
            "Topics are declared via @NiagaraTopic annotation on BComponent subclasses.",
            "Subscribers receive events asynchronously -- do not block in handlers.",
            "Topic events are NOT persisted -- if the subscriber is offline, events are lost.",
        ],
    },
    "programs": {
        "base": "BProgram",
        "pkg": "com.tridium.program",
        "description": "Custom logic programs (PX, Spy, SpyderTool)",
        "resolve_virtual": True,
        "gotchas": [
            "BProgram lives in com.tridium.program, not javax.baja.program.",
            "Programs execute in the station's Java VM -- avoid blocking or long loops.",
            "Use BProgramSlot for wiring inputs/outputs to points.",
        ],
    },
    "servlets": {
        "base": "BWebServlet",
        "pkg": "javax.baja.web",
        "description": "HTTP servlet for custom web endpoints in Niagara",
        "resolve_virtual": True,
        "gotchas": [
            "BWebServlet is added as a service in the station -- not deployed via WAR.",
            "Override doGet/doPost/doPut -- the base class handles auth and session.",
            "getServletName() defines the URL path segment (e.g. 'alarm' -> /alarm/*).",
            "Use WebOp for request/response context, not raw HttpServletRequest.",
        ],
    },
    "ords": {
        "base": "BOrd",
        "pkg": "javax.baja.naming",
        "description": "Niagara Object Resolution Descriptor (URI-like addressing)",
        "resolve_virtual": False,
        "gotchas": [
            "BOrd is immutable -- BOrd.make() returns a new instance, never modify.",
            "Always use BOrd.make(String), never new BOrd(String).",
            "station:|slot:/ is the root ORD for the local station.",
            "BOrd.resolve() can be expensive -- cache the resolved component when possible.",
        ],
    },
    "permissions": {
        "base": "BPermissions",
        "pkg": "javax.baja.security",
        "description": "Role-based access control and permissions model",
        "resolve_virtual": False,
        "gotchas": [
            "Permissions are checked by the framework -- do not bypass with reflection.",
            "BPermissions values are bitmasks (read, write, invoke, admin).",
            "Use Context.getUser() to get the current user, not static state.",
        ],
    },
}

FEATURE_NAMES = sorted(FEATURE_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached)
# ---------------------------------------------------------------------------

_ci_cache = None
_ci_source = None
_xref_cache = None
_mi_cache = None
_inh_cache = None
_ann_cache = None


def _load_json(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_ci(base_dir):
    global _ci_cache, _ci_source
    if _ci_cache is not None:
        return _ci_cache
    _ci_cache = _load_json(os.path.join(base_dir, "indexes", "class-index.json"))
    if _ci_cache:
        _ci_source = _ci_cache.get("_meta", {}).get("source", "")
    return _ci_cache


def _load_xref(base_dir):
    global _xref_cache
    if _xref_cache is not None:
        return _xref_cache
    _xref_cache = _load_json(os.path.join(base_dir, "indexes", "xref-index.json"))
    return _xref_cache


def _load_mi(base_dir):
    global _mi_cache
    if _mi_cache is not None:
        return _mi_cache
    _mi_cache = _load_json(os.path.join(base_dir, "indexes", "method-index.json"))
    return _mi_cache


def _load_inh(base_dir):
    global _inh_cache
    if _inh_cache is not None:
        return _inh_cache
    _inh_cache = _load_json(os.path.join(base_dir, "indexes", "inheritance.json"))
    return _inh_cache


def _load_ann(base_dir):
    global _ann_cache
    if _ann_cache is not None:
        return _ann_cache
    _ann_cache = _load_json(os.path.join(base_dir, "indexes", "annotations-index.json"))
    return _ann_cache


def _get_called_by(base_dir):
    from module_nav_lib.callgraph import load_callgraph, _build_called_by
    cg = load_callgraph(base_dir)
    if not cg:
        return None
    return _build_called_by(cg)


# ---------------------------------------------------------------------------
# Resolve helpers
# ---------------------------------------------------------------------------

def _resolve_class(ci, name):
    """Resolve a class name (case-insensitive) from class-index."""
    classes = ci.get("classes", {})
    if name in classes:
        return name
    lower = name.lower()
    for k in classes:
        if k.lower() == lower:
            return k
    return None


def _get_top_entry(ci, name):
    """Get the top-level (non-inner, non-docSource) class entry."""
    classes = ci.get("classes", {})
    entries = classes.get(name, [])
    for e in entries:
        if e.get("outer_class") is None and e.get("module") != "docSource-doc":
            return e
    for e in entries:
        if e.get("outer_class") is None:
            return e
    return entries[0] if entries else None


def _get_class_module(ci_classes, name):
    entries = ci_classes.get(name, [])
    for e in entries:
        if e.get("outer_class") is None and e.get("module") != "docSource-doc":
            return e.get("module")
    for e in entries:
        if e.get("outer_class") is None:
            return e.get("module")
    return entries[0].get("module") if entries else None


# ---------------------------------------------------------------------------
# Help Navigator helpers (import from unified)
# ---------------------------------------------------------------------------

def _get_help_dir(base_dir):
    from module_nav_lib.unified import _detect_help_dir
    return _detect_help_dir(base_dir)


def _help_class_exists(help_dir, class_name):
    """Check if a class is in the Help Nav class-index."""
    if not help_dir:
        return False
    from module_nav_lib.unified import _load_help_index
    ci = _load_help_index(help_dir, "class-index.json")
    if not ci:
        return False
    if class_name in ci:
        return True
    for k in ci:
        if k.lower() == class_name.lower():
            return True
    return False


def _help_slots(help_dir, class_name):
    """Get slots from Help Nav slots-index."""
    if not help_dir:
        return {"properties": [], "actions": [], "topics": []}
    from module_nav_lib.unified import _load_help_index
    sl = _load_help_index(help_dir, "slots-index.json")
    if not sl:
        return {"properties": [], "actions": [], "topics": []}
    entry = sl.get(class_name)
    if not entry:
        for k, v in sl.items():
            if k.lower() == class_name.lower():
                entry = v
                break
    if not entry:
        return {"properties": [], "actions": [], "topics": []}
    return {
        "properties": entry.get("properties", []),
        "actions": entry.get("actions", []),
        "topics": entry.get("topics", []),
    }


# ---------------------------------------------------------------------------
# BOG Navigator helpers (import from unified)
# ---------------------------------------------------------------------------

def _bog_search(base_dir, class_name):
    """Search BOG for instances of a class. Returns (count, sample_paths)."""
    from module_nav_lib.unified import _search_bog
    results = _search_bog(base_dir, class_name, limit=20)
    type_count = 0
    paths = []
    for r in results:
        if r.get("type") == "component":
            type_count += r.get("count", 0)
        elif r.get("type") == "instance":
            paths.append(r.get("path", ""))
    return type_count, paths[:5]


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_canonical(ci, xref, class_name, entry, help_dir, base_dir, feature):
    """Build canonical class section data."""
    all_importers = xref.get("class_imported_by", {}).get(class_name, [])
    ci_classes = ci.get("classes", {})
    target_module = entry.get("module", "")

    external = []
    for imp in all_importers:
        imp_mod = _get_class_module(ci_classes, imp)
        if imp_mod and imp_mod != target_module and imp_mod != "docSource-doc":
            external.append(imp)

    help_hit = _help_class_exists(help_dir, class_name)
    bog_count, bog_paths = _bog_search(base_dir, class_name)

    return {
        "class": class_name,
        "package": entry.get("package", ""),
        "module": target_module,
        "lines": entry.get("lines", 0),
        "help_hit": help_hit,
        "external_importers": len(external),
        "bog_count": bog_count,
        "bog_paths": bog_paths,
        "description": FEATURE_REGISTRY[feature]["description"],
    }


def _build_slots(ann, help_dir, class_name):
    """Build slots section from both Help Nav and Module Nav annotations."""
    h_slots = _help_slots(help_dir, class_name)

    m_props = []
    m_actions = []
    m_topics = []
    if ann:
        nt = ann.get("niagara_types", {})
        ann_entry = nt.get(class_name, {})
        m_props = ann_entry.get("properties", [])
        m_actions = ann_entry.get("actions", [])
        m_topics = ann_entry.get("topics", [])

    return {
        "help_properties": h_slots["properties"],
        "help_actions": h_slots["actions"],
        "help_topics": h_slots["topics"],
        "mod_properties": m_props,
        "mod_actions": m_actions,
        "mod_topics": m_topics,
    }


def _build_entry_points(class_name, mi, called_by, inh, resolve_virtual,
                        min_callers=3):
    """Build entry-point methods section."""
    if resolve_virtual and inh:
        from module_nav_lib.contracts import _extract_virtual_entry_points
        return _extract_virtual_entry_points(
            class_name, mi, called_by, inh, min_callers=min_callers)
    else:
        from module_nav_lib.contracts import _extract_entry_points
        return _extract_entry_points(
            class_name, mi, called_by, min_callers=min_callers)


def _build_private_warnings(mi, called_by, class_name):
    """Find private methods with external callers (APIs to avoid)."""
    if called_by is None:
        return []
    methods_map = mi.get("methods", {})
    class_methods = mi.get("class_methods", {}).get(class_name, [])
    warnings = []

    for mname in class_methods:
        entry = None
        for e in methods_map.get(mname, []):
            if e.get("class") == class_name:
                entry = e
                break
        if not entry:
            continue
        mods = entry.get("modifiers", [])
        if "private" not in mods:
            continue
        key = "{}.{}".format(class_name, mname)
        ext_count = 0
        for c in called_by.get(key, []):
            dot = c.rfind(".")
            if dot > 0 and c[:dot] != class_name:
                ext_count += 1
        if ext_count > 0:
            warnings.append({
                "method": mname,
                "external_callers": ext_count,
            })

    warnings.sort(key=lambda w: -w["external_callers"])
    return warnings


def _build_companions(xref, ci, class_name, entry):
    """Build companion classes section."""
    from module_nav_lib.contracts import _extract_companion_imports

    ci_classes = ci.get("classes", {})
    target_module = entry.get("module", "")
    all_importers = xref.get("class_imported_by", {}).get(class_name, [])

    external = []
    for imp in all_importers:
        imp_mod = _get_class_module(ci_classes, imp)
        if imp_mod and imp_mod != target_module and imp_mod != "docSource-doc":
            external.append(imp)

    return _extract_companion_imports(xref, class_name, external, top=8)


def _build_examples(base_dir, class_name, top=3):
    """Capture example-mine JSON output for --depth full."""
    from module_nav_lib.mining import cmd_example_mine

    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()
    try:
        cmd_example_mine(base_dir, class_name, top=top, as_json=True)
    finally:
        sys.stdout = old_stdout

    text = buf.getvalue()
    # Find JSON start (skip any loading messages)
    lines = text.strip().splitlines()
    json_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            json_start = i
            break
    if json_start is not None:
        try:
            return json.loads("\n".join(lines[json_start:]))
        except (json.JSONDecodeError, ValueError):
            pass
    return None


# ---------------------------------------------------------------------------
# Markdown formatter
# ---------------------------------------------------------------------------

def _format_markdown(feature, canonical, slots, entry_points, private_warns,
                     companions, gotchas, examples):
    """Format all sections into a Markdown string."""
    lines = []

    def ln(s=""):
        lines.append(s)

    # Title
    ln("# Feature brief: {}".format(feature))
    ln()

    # Canonical class
    c = canonical
    ln("## Canonical class")
    ln("- **{}** ({}) -- {}, {:,} lines".format(
        c["class"], c["package"], c["module"], c["lines"]))
    ln("- Public API: {}".format("YES (Help Nav hit)" if c["help_hit"]
                                  else "NO (internal/private)"))
    ln("- Real usages: {} external modules".format(c["external_importers"]))
    if c["bog_count"] > 0:
        ln("- BOG presence: {} instance(s)".format(c["bog_count"]))
        for p in c["bog_paths"][:3]:
            ln("  - {}".format(p))
    else:
        ln("- BOG presence: none in current station")
    ln()

    # Slots
    ln("## Public slots")
    h_props = slots["help_properties"]
    m_props = slots["mod_properties"]
    h_acts = slots["help_actions"]
    m_acts = slots["mod_actions"]
    h_tops = slots["help_topics"]
    m_tops = slots["mod_topics"]

    if h_props:
        ln("Help Nav properties ({}):" .format(len(h_props)))
        for p in h_props[:10]:
            dv = ""
            if p.get("defaultValue"):
                dv = " = {}".format(p["defaultValue"])
            ln("  - {} : {}{}".format(p["name"], p.get("type", "?"), dv))
        if len(h_props) > 10:
            ln("  - ... ({} more)".format(len(h_props) - 10))
    if m_props:
        ln("Module Nav @NiagaraProperty ({}):" .format(len(m_props)))
        for p in m_props[:10]:
            dv = ""
            if p.get("defaultValue"):
                dv = " = {}".format(p["defaultValue"])
            ln("  - {} : {}{}".format(p["name"], p.get("type", "?"), dv))
    if h_acts or m_acts:
        total_acts = max(len(h_acts), len(m_acts))
        ln("Actions: {}".format(total_acts))
        for a in (h_acts or m_acts)[:5]:
            ln("  - {}".format(a.get("name", "?")))
    if h_tops or m_tops:
        total_tops = max(len(h_tops), len(m_tops))
        ln("Topics: {}".format(total_tops))
        for t in (h_tops or m_tops)[:5]:
            ln("  - {}".format(t.get("name", "?")))
    if not h_props and not m_props and not h_acts and not m_acts:
        ln("(no slots data available)")
    ln()

    # Entry-point methods
    ln("## Entry-point methods (top callers from external modules)")
    if entry_points:
        for ep in entry_points[:10]:
            sig = ep.get("signature", ep.get("name", "?"))
            if len(sig) > 60:
                sig = sig[:57] + "..."
            virt = ""
            if ep.get("virtual_callers", 0) > 0:
                virt = " ({} direct + {} virtual)".format(
                    ep["direct_callers"], ep["virtual_callers"])
            ln("- {} -- {} callers{}".format(sig, ep["external_callers"], virt))
    else:
        ln("(no methods meet the external-callers threshold)")
    ln()

    # Private APIs to avoid
    if private_warns:
        ln("## Private APIs -- AVOID")
        for w in private_warns[:5]:
            ln("- {} [private] -- called externally by {} class(es)".format(
                w["method"], w["external_callers"]))
        ln()

    # Companion classes
    if companions:
        ln("## Companion classes (top co-imports)")
        for cls, count in companions[:8]:
            ln("- {:30s}  {} co-imports".format(cls, count))
        ln()

    # Gotchas
    if gotchas:
        ln("## Gotchas")
        for g in gotchas:
            ln("- {}".format(g))
        ln()

    # BOG references
    if canonical["bog_paths"]:
        ln("## BOG references (station instances)")
        for p in canonical["bog_paths"]:
            ln("- {}".format(p))
        ln()

    # Examples (--depth full only)
    if examples:
        ex_list = examples.get("examples", [])
        ln("## Real code examples ({} candidates, showing top {})".format(
            examples.get("total_candidates", 0), len(ex_list)))
        for i, ex in enumerate(ex_list, 1):
            ln()
            ln("### Example {} -- {} / {} (score {})".format(
                i, ex.get("module", "?"), ex.get("class", "?") + ".java",
                ex.get("score", 0)))
            ln("Method: {}  Lines: {}-{}".format(
                ex.get("method", "?"), ex.get("start_line", "?"),
                ex.get("end_line", "?")))
            ln("```java")
            for bl in ex.get("body", []):
                ln(bl)
            ln("```")
        ln()

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

def _format_json(feature, canonical, slots, entry_points, private_warns,
                 companions, gotchas, examples):
    """Build structured JSON result."""
    return {
        "feature": feature,
        "canonical": canonical,
        "slots": {
            "help_properties": slots["help_properties"],
            "help_actions": slots["help_actions"],
            "help_topics": slots["help_topics"],
            "mod_properties": slots["mod_properties"],
            "mod_actions": slots["mod_actions"],
            "mod_topics": slots["mod_topics"],
        },
        "entry_points": entry_points,
        "private_warnings": private_warns,
        "companions": [{"class": c, "count": n} for c, n in companions],
        "gotchas": gotchas,
        "examples": examples,
    }


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_feature_brief(base_dir, feature, depth="quick", out_path=None,
                      as_json=False):
    """Generate a one-command research brief for a Niagara feature domain."""
    feature = feature.lower().strip()

    if feature not in FEATURE_REGISTRY:
        print("  Unknown feature: '{}'".format(feature))
        print("")
        print("  Available features:")
        for fn in FEATURE_NAMES:
            entry = FEATURE_REGISTRY[fn]
            print("    {:<14s}  {} ({})".format(
                fn, entry["base"], entry["description"]))
        print("")
        print("  Usage: feature-brief <feature> [--depth quick|full]")
        return

    reg = FEATURE_REGISTRY[feature]
    base_class = reg["base"]

    # Load indexes
    ci = _load_ci(base_dir)
    if not ci:
        print("  ERROR: class-index.json not found.")
        return

    resolved = _resolve_class(ci, base_class)
    if not resolved:
        print("  ERROR: class '{}' not found in class-index.".format(base_class))
        return
    base_class = resolved

    entry = _get_top_entry(ci, base_class)
    if not entry:
        print("  ERROR: no top-level entry for '{}'.".format(base_class))
        return

    xref = _load_xref(base_dir)
    mi = _load_mi(base_dir)
    inh = _load_inh(base_dir)
    ann = _load_ann(base_dir)
    help_dir = _get_help_dir(base_dir)

    # Build sections
    canonical = _build_canonical(ci, xref, base_class, entry, help_dir,
                                 base_dir, feature)

    slots = _build_slots(ann, help_dir, base_class)

    # Entry-points need callgraph (loads on demand)
    called_by = _get_called_by(base_dir)
    entry_points = []
    if mi and called_by is not None:
        entry_points = _build_entry_points(
            base_class, mi, called_by, inh,
            resolve_virtual=reg.get("resolve_virtual", False))

    private_warns = []
    if mi and called_by is not None:
        private_warns = _build_private_warnings(mi, called_by, base_class)

    companions = []
    if xref:
        companions = _build_companions(xref, ci, base_class, entry)

    gotchas = reg.get("gotchas", [])

    # Examples (only in full depth)
    examples = None
    if depth == "full":
        examples = _build_examples(base_dir, base_class, top=3)

    # Format output
    if as_json:
        result = _format_json(feature, canonical, slots, entry_points,
                              private_warns, companions, gotchas, examples)
        text = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        text = _format_markdown(feature, canonical, slots, entry_points,
                                private_warns, companions, gotchas, examples)

    # Write or print
    if out_path:
        try:
            parent = os.path.dirname(out_path)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            print("  Brief written to: {}".format(out_path))
            print("  Feature: {} ({})".format(feature, base_class))
            if examples:
                print("  Depth: full (includes {} examples)".format(
                    len(examples.get("examples", []))))
            else:
                print("  Depth: quick")
        except Exception as exc:
            print("  ERROR writing {}: {}".format(out_path, exc))
    else:
        print(text)
