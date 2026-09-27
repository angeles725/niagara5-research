"""
Full-stack trace command for Module Navigator (Phase 32, Gap #5).

Call chain with semantic annotations by heuristic method-name matching.
Shows the flow: input -> BQL parse -> BQL exec -> data source -> iterate -> serialize -> output.

Commands:
  full-stack-trace <class>.<method> [--depth N] [--annotate all|data] [--json]

Index: callgraph-index.json (281K edges).
"""

import json
import os
import sys


# ---------------------------------------------------------------------------
# Annotation helpers
# ---------------------------------------------------------------------------

def _annotate_method(method_name):
    """Return the semantic annotation category for a method name, or None."""
    # Order matters: check more specific patterns first

    # [input] — HTTP/Servlet entry points and parameter retrieval
    if method_name.startswith("getParameter"):
        return "input"
    if method_name in ("doGet", "doPost", "doPut", "doDelete", "doService",
                       "handleGet", "handlePost", "handlePut", "handleDelete",
                       "handleRequest", "service"):
        return "input"
    if method_name.startswith("onInvoke"):
        return "input"

    # [bql-parse] — BQL/SQL parsing and query construction
    if method_name.startswith("BQL"):
        return "bql-parse"
    if ".parse" in method_name or method_name.endswith("parse"):
        return "bql-parse"
    if "Query" in method_name and ("parse" in method_name or "build" in method_name):
        return "bql-parse"

    # [bql-exec] — Query execution
    if ".execute" in method_name or method_name.endswith("execute"):
        return "bql-exec"
    if method_name.startswith("BQL"):
        return "bql-parse"
    if "Cursor" in method_name or "ResultSet" in method_name:
        return "bql-exec"

    # [data-source] — Methods that return collections / data sources
    if method_name.startswith("get"):
        lower = method_name.lower()
        if any(x in lower for x in ["list", "map", "set", "array",
                                      "table", "rows", "cursor",
                                      "result", "records", "data"]):
            return "data-source"
    if method_name.endswith("Query") and ("execute" not in method_name and "parse" not in method_name):
        return "data-source"

    # [iterate] — Loop/iteration control
    if method_name in ("next", "hasNext", "hasMoreElements", "nextElement",
                       "forEach", "forEachRemaining", "iterator"):
        return "iterate"
    if "Loop" in method_name or "loop" in method_name:
        return "iterate"

    # [serialize] — Serialization / JSON / encoding
    if method_name.startswith("write") or method_name.endswith("write"):
        return "serialize"
    if method_name.startswith("toJson") or method_name.startswith("toJSON"):
        return "serialize"
    if method_name.startswith("encode") or method_name.endswith("encode"):
        return "serialize"
    if method_name.startswith("serialize"):
        return "serialize"
    if method_name in ("toString", "toString", "stringify", "asString"):
        return "serialize"

    # [output] — Response / flush / send
    if method_name.startswith("flush"):
        return "output"
    if method_name.startswith("close"):
        return "output"
    if method_name in ("send", "sendError", "sendRedirect"):
        return "output"
    if "getWriter" in method_name or "getOutputStream" in method_name:
        return "output"

    return None


def _is_data_interesting(annotation):
    """Return True if this annotation is data-interesting (⚑ marker)."""
    return annotation in ("bql-parse", "bql-exec", "serialize")


# ---------------------------------------------------------------------------
# Trace building (BFS)
# ---------------------------------------------------------------------------

def _build_trace(class_name, method_name, max_depth, calls, visited):
    """Build a full-stack trace tree via BFS from class.method.

    Returns a list of node dicts:
        {'class', 'method', 'full_key', 'annotation', 'interesting',
         'children': [...], 'depth': int}
    """
    root_key = "{}.{}".format(class_name, method_name)
    root = {
        "class": class_name,
        "method": method_name,
        "full_key": root_key,
        "annotation": _annotate_method(method_name),
        "interesting": False,
        "children": [],
        "depth": 0,
    }
    if _is_data_interesting(root["annotation"]):
        root["interesting"] = True

    queue = [(root, 0)]  # (node, current_depth)
    visited_local = set()

    while queue:
        node, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        if node["full_key"] in visited_local:
            continue
        visited_local.add(node["full_key"])

        callees = calls.get(node["full_key"], [])
        for callee_key in callees:
            if callee_key in visited_local:
                continue
            dot = callee_key.rfind(".")
            if dot <= 0:
                continue
            callee_cls = callee_key[:dot]
            callee_meth = callee_key[dot + 1:]
            ann = _annotate_method(callee_meth)
            interesting = _is_data_interesting(ann)
            child = {
                "class": callee_cls,
                "method": callee_meth,
                "full_key": callee_key,
                "annotation": ann,
                "interesting": interesting,
                "children": [],
                "depth": depth + 1,
            }
            node["children"].append(child)
            if child["depth"] < max_depth:
                queue.append((child, depth + 1))

    return root


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render_trace_tree(node, prefix="  ", is_last=True, all_annot=True, annotation_map=None):
    """Render a trace node as plain text tree lines."""
    if annotation_map is None:
        annotation_map = {}

    lines = []

    # Build the display line
    ann_str = ""
    if node["annotation"] and (all_annot or node["interesting"]):
        ann_str = "  [{}]".format(node["annotation"])
    flag = "  ⚑" if node.get("interesting") else ""

    lines.append("{}{}{}{}".format(prefix, node["full_key"], ann_str, flag))

    # Render children
    children = node.get("children", [])
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        if i == 0:
            child_prefix = prefix + ("    " if is_last else "|   ")
        else:
            child_prefix = prefix + ("" if is_last else "|   ")
        if is_last_child:
            connector = "`-- "
        else:
            connector = "|-- "
        sublines = _render_trace_tree(
            child,
            prefix=child_prefix,
            is_last=is_last_child,
            all_annot=all_annot,
        )
        lines.extend(sublines)

    return lines


def _render_annotations(root, annotate_mode):
    """Render the ANNOTATIONS summary block."""
    lines = []

    interesting_count = 0
    annotations_seen = set()
    data_source_types = set()

    def walk(n):
        nonlocal interesting_count
        if n.get("interesting"):
            interesting_count += 1
        if n.get("annotation"):
            annotations_seen.add(n["annotation"])
        if n["annotation"] == "data-source":
            # Try to infer the data type from class name
            data_source_types.add(n["class"])
        for c in n.get("children", []):
            walk(c)

    walk(root)

    if annotate_mode == "data" and interesting_count == 0:
        return lines

    lines.append("")
    lines.append("  ANNOTATIONS:")
    lines.append("    ⚑ Data-interesting nodes: {}".format(interesting_count))

    categories = ["input", "bql-parse", "bql-exec", "data-source", "iterate", "serialize", "output"]
    present = [c for c in categories if c in annotations_seen]
    if present:
        lines.append("    Categories seen: {}".format(", ".join(present)))

    if data_source_types:
        lines.append("    Data sources: {}".format(
            ", ".join(sorted(data_source_types))))

    return lines


def _render_plain(root, annotate_mode):
    """Render full trace as plain text."""
    all_annot = (annotate_mode == "all")

    lines = []
    lines.append("")
    lines.append("  FULL STACK TRACE: {}".format(root["full_key"]))
    lines.append("")

    tree_lines = _render_trace_tree(root, all_annot=all_annot)
    for line in tree_lines:
        lines.append(line)

    # Annotations summary
    lines.extend(_render_annotations(root, annotate_mode))

    lines.append("")
    return "\n".join(lines)


def _render_json(root, annotate_mode):
    """Render full trace as JSON."""
    all_annot = (annotate_mode == "all")

    def node_to_dict(n):
        ann = n.get("annotation")
        result = {
            "key": n["full_key"],
            "annotation": ann,
            "interesting": n.get("interesting", False),
        }
        if all_annot or ann:
            result["annotation"] = ann
        children = n.get("children", [])
        if children:
            result["children"] = [node_to_dict(c) for c in children]
        return result

    import json as _json
    output = {
        "root": root["full_key"],
        "tree": node_to_dict(root),
    }
    return _json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# Command entry point
# ---------------------------------------------------------------------------

def cmd_full_stack_trace(base_dir, class_method, depth=6,
                         annotate="all", as_json=False):
    """Full-stack semantic trace of a method with annotated call chain.

    Args:
        base_dir:     Base directory (module-navigator/)
        class_method: Class.method string, e.g. "BAlarmServlet.doGet"
        depth:        Max traversal depth (default 6)
        annotate:     'all' or 'data' (only show data-interesting annotations)
        as_json:      Output as JSON instead of plain text
    """
    # Parse class.method
    dot = class_method.rfind(".")
    if dot <= 0:
        print("")
        print("  ERROR: class_method must be in 'Class.method' format.")
        print("  Example: full-stack-trace BAlarmServlet.doGet")
        print("")
        return
    class_name = class_method[:dot]
    method_name = class_method[dot + 1:]

    # Load callgraph
    path = os.path.join(base_dir, "indexes", "callgraph-index.json")
    if not os.path.isfile(path):
        print("")
        print("  ERROR: callgraph-index.json not found.")
        print("  Run: python tools/build_callgraph_index.py")
        print("")
        return

    import sys as _sys
    _sys.stderr.write("  Loading callgraph-index.json...")
    _sys.stderr.flush()
    with open(path, "r", encoding="utf-8") as f:
        cg = json.load(f)
    _sys.stderr.write(" OK\n")

    calls = cg.get("calls", {})

    root_key = class_method
    if root_key not in calls:
        print("")
        print("  '{}' not found in call graph.".format(root_key))
        prefix = class_name + "."
        candidates = sorted([k for k in calls if k.startswith(prefix)])[:15]
        if candidates:
            print("  Available methods for {}:".format(class_name))
            for c in candidates:
                print("    {}".format(c))
        print("")
        return

    visited = set()
    root = _build_trace(class_name, method_name, depth, calls, visited)

    if as_json:
        print(_render_json(root, annotate))
    else:
        print(_render_plain(root, annotate))
