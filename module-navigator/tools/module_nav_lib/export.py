"""
Export/Visualization commands for Module Navigator (Phase 20).

Commands:
  export <class> --html               Standalone HTML class report
  export <module> --mermaid            Mermaid class diagram for a module
  export <class> <method> --dot       DOT call-chain graph for Graphviz
  export <module> --dot               DOT class relationship graph
"""

import json
import os
import re
import time


# ---------------------------------------------------------------------------
# Shared helpers
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
            if e.get("outer_class") is None:
                return class_name, e
        return class_name, entries[0]

    name_lower = class_name.lower()
    for k, entries in classes.items():
        if k.lower() == name_lower:
            for e in entries:
                if e.get("outer_class") is None:
                    return k, e
            return k, entries[0]

    return None, None


def _safe_id(name):
    """Make a safe identifier for Mermaid/DOT (replace special chars)."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def _ensure_exports_dir(base_dir):
    """Ensure exports/ directory exists."""
    exports_dir = os.path.join(base_dir, "exports")
    if not os.path.isdir(exports_dir):
        os.makedirs(exports_dir)
    return exports_dir


# ---------------------------------------------------------------------------
# export --html: Standalone HTML class report
# ---------------------------------------------------------------------------

def cmd_export_html(base_dir, class_name, output_path=None):
    """Generate a standalone HTML report for a class."""
    t0 = time.time()

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

    # Load additional indexes
    mi_data = _load_json(base_dir, "method-index.json")
    fi_data = _load_json(base_dir, "field-index.json")
    ann_data = _load_json(base_dir, "annotations-index.json")
    ih_data = _load_json(base_dir, "inheritance.json")
    xr_data = _load_json(base_dir, "xref-index.json")
    ex_data = _load_json(base_dir, "exceptions-index.json")
    cg_data = _load_json(base_dir, "callgraph-index.json")

    # --- Gather data ---

    # Methods — method-index uses "methods" dict: {method_name: [{class, module, ...}]}
    methods_list = []
    if mi_data:
        methods_dict = mi_data.get("methods", {})
        target_module = entry.get("module", "")
        for mname, mclasses in methods_dict.items():
            for mc in mclasses:
                if mc.get("class") == resolved and mc.get("module") == target_module:
                    methods_list.append({
                        "name": mname,
                        "return_type": mc.get("return_type", "void"),
                        "params": mc.get("params", []),
                        "modifiers": mc.get("modifiers", []),
                    })

    # Fields — field-index uses "fields" dict: {field_name: [{class, module, ...}]}
    fields_list = []
    if fi_data:
        fields_dict = fi_data.get("fields", {})
        target_module = entry.get("module", "")
        for fname, fentries in fields_dict.items():
            for fe in fentries:
                if fe.get("class") == resolved and fe.get("module") == target_module:
                    fields_list.append({
                        "name": fname,
                        "type": fe.get("type", "?"),
                        "modifiers": fe.get("modifiers", []),
                        "value": fe.get("value"),
                    })

    # Annotations / Slots
    slots_info = {}
    if ann_data:
        niagara_types = ann_data.get("niagara_types", {})
        if resolved in niagara_types:
            slots_info = niagara_types[resolved]
            if isinstance(slots_info, list):
                slots_info = slots_info[0] if slots_info else {}

    # Inheritance chain — inheritance.json uses "class_to_chain"
    chain = []
    if ih_data:
        c2c = ih_data.get("class_to_chain", {})
        if resolved in c2c:
            chain = c2c[resolved]

    # Xref — xref-index uses short class names as keys
    importers = []
    imports = []
    if xr_data:
        imported_by = xr_data.get("class_imported_by", {})
        if resolved in imported_by:
            importers = imported_by[resolved][:30]
        class_imports = xr_data.get("class_imports", {})
        if resolved in class_imports:
            imports = class_imports[resolved][:30]

    # Exceptions — class_throws has {module, throws: [{method,line,exceptions}]},
    # class_catches has {module, catches: [{line, exceptions}]}
    throws_info = {}
    catches_info = {}
    if ex_data:
        class_throws = ex_data.get("class_throws", {})
        if resolved in class_throws:
            throws_info = class_throws[resolved]
        class_catches = ex_data.get("class_catches", {})
        if resolved in class_catches:
            catches_info = class_catches[resolved]

    # Call graph stats — calls dict maps "Class.method" -> [callee strings]
    callee_count = 0
    caller_count = 0
    if cg_data:
        calls = cg_data.get("calls", {})
        prefix = resolved + "."
        for key, callees in calls.items():
            if key.startswith(prefix):
                callee_count += len(callees) if isinstance(callees, list) else 0
            elif isinstance(callees, list):
                for c in callees:
                    if isinstance(c, str) and c.startswith(prefix):
                        caller_count += 1

    # --- Build HTML ---
    fqn = entry.get("package", "") + "." + resolved if entry.get("package") else resolved

    html = _build_html_report(
        resolved, entry, fqn, methods_list, fields_list,
        slots_info, chain, importers, imports, throws_info,
        catches_info, callee_count, caller_count
    )

    # Write file
    if not output_path:
        exports_dir = _ensure_exports_dir(base_dir)
        output_path = os.path.join(exports_dir, "{}.html".format(resolved))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    elapsed = time.time() - t0

    print("")
    print("  " + "=" * 65)
    print("  HTML EXPORT: {}".format(resolved))
    print("  " + "=" * 65)
    print("")
    print("  Class:       {}".format(resolved))
    print("  Package:     {}".format(entry.get("package", "-")))
    print("  Module:      {}".format(entry.get("module", "-")))
    print("  Methods:     {:,}".format(len(methods_list)))
    print("  Fields:      {:,}".format(len(fields_list)))
    print("  Slots:       {:,}".format(
        len(slots_info.get("properties", [])) +
        len(slots_info.get("actions", [])) +
        len(slots_info.get("topics", []))
        if isinstance(slots_info, dict) else 0))
    print("  Chain depth: {}".format(len(chain)))
    print("  Importers:   {:,}".format(len(importers)))
    print("  Imports:     {:,}".format(len(imports)))
    print("")
    print("  Output: {}".format(output_path))
    size_kb = os.path.getsize(output_path) / 1024.0
    print("  Size:   {:.1f} KB".format(size_kb))
    print("  Time:   {:.2f}s".format(elapsed))
    print("")


def _esc(text):
    """Escape HTML special chars."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _build_html_report(resolved, entry, fqn, methods, fields,
                       slots_info, chain, importers, imports,
                       throws_info, catches_info, callee_count, caller_count):
    """Build standalone HTML report string."""

    props = slots_info.get("properties", []) if isinstance(slots_info, dict) else []
    actions = slots_info.get("actions", []) if isinstance(slots_info, dict) else []
    topics = slots_info.get("topics", []) if isinstance(slots_info, dict) else []

    throws_methods = throws_info.get("throws", []) if isinstance(throws_info, dict) else []
    catch_blocks = catches_info.get("catches", []) if isinstance(catches_info, dict) else []

    # Sort methods by name
    methods_sorted = sorted(methods, key=lambda m: m["name"])
    fields_sorted = sorted(fields, key=lambda f: f["name"])

    # Separate public/private methods
    public_methods = [m for m in methods_sorted if "public" in m.get("modifiers", [])]
    other_methods = [m for m in methods_sorted if "public" not in m.get("modifiers", [])]

    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html lang="en">')
    lines.append('<head>')
    lines.append('<meta charset="UTF-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append('<title>{} - Module Navigator Report</title>'.format(_esc(resolved)))
    lines.append('<style>')
    lines.append(_get_html_css())
    lines.append('</style>')
    lines.append('</head>')
    lines.append('<body>')

    # Header
    lines.append('<header>')
    lines.append('<h1>{}</h1>'.format(_esc(resolved)))
    lines.append('<p class="subtitle">{}</p>'.format(_esc(fqn)))
    lines.append('<p class="meta">Module: <strong>{}</strong> | Kind: <strong>{}</strong> | Lines: <strong>{:,}</strong></p>'.format(
        _esc(entry.get("module", "?")),
        _esc(entry.get("kind", "?")),
        entry.get("lines", 0)))
    lines.append('</header>')

    lines.append('<main>')

    # --- Class Info section ---
    lines.append('<section>')
    lines.append('<h2>Class Info</h2>')
    lines.append('<table class="info-table">')
    lines.append('<tr><td>Modifiers</td><td>{}</td></tr>'.format(
        _esc(" ".join(entry.get("modifiers", []))) or "-"))
    if entry.get("extends"):
        lines.append('<tr><td>Extends</td><td><code>{}</code></td></tr>'.format(
            _esc(entry["extends"])))
    if entry.get("implements"):
        lines.append('<tr><td>Implements</td><td>{}</td></tr>'.format(
            ", ".join('<code>{}</code>'.format(_esc(i)) for i in entry["implements"])))
    if entry.get("zkm"):
        lines.append('<tr><td>ZKM</td><td class="warn">Obfuscated</td></tr>')
    lines.append('<tr><td>Call Graph</td><td>{:,} outgoing calls, {:,} incoming calls</td></tr>'.format(
        callee_count, caller_count))
    lines.append('</table>')
    lines.append('</section>')

    # --- Inheritance Chain ---
    if chain:
        lines.append('<section>')
        lines.append('<h2>Inheritance Chain</h2>')
        lines.append('<div class="chain">')
        for i, ancestor in enumerate(chain):
            indent = "  " * i
            arrow = " &#8594; " if i > 0 else ""
            lines.append('<div class="chain-item" style="margin-left:{}em">{}<code>{}</code></div>'.format(
                i * 1.5, arrow, _esc(ancestor)))
        lines.append('<div class="chain-item" style="margin-left:{}em"> &#8594; <code class="current">{}</code></div>'.format(
            len(chain) * 1.5, _esc(resolved)))
        lines.append('</div>')
        lines.append('</section>')

    # --- Niagara Slots ---
    if props or actions or topics:
        lines.append('<section>')
        lines.append('<h2>Niagara Slots ({:,})</h2>'.format(len(props) + len(actions) + len(topics)))

        if props:
            lines.append('<h3>Properties ({:,})</h3>'.format(len(props)))
            lines.append('<table><thead><tr><th>Name</th><th>Type</th></tr></thead><tbody>')
            for p in props:
                if isinstance(p, dict):
                    lines.append('<tr><td><code>{}</code></td><td>{}</td></tr>'.format(
                        _esc(p.get("name", "?")), _esc(p.get("type", "?"))))
                else:
                    lines.append('<tr><td colspan="2"><code>{}</code></td></tr>'.format(_esc(str(p))))
            lines.append('</tbody></table>')

        if actions:
            lines.append('<h3>Actions ({:,})</h3>'.format(len(actions)))
            lines.append('<table><thead><tr><th>Name</th><th>Details</th></tr></thead><tbody>')
            for a in actions:
                if isinstance(a, dict):
                    lines.append('<tr><td><code>{}</code></td><td>{}</td></tr>'.format(
                        _esc(a.get("name", "?")), _esc(a.get("return_type", ""))))
                else:
                    lines.append('<tr><td colspan="2"><code>{}</code></td></tr>'.format(_esc(str(a))))
            lines.append('</tbody></table>')

        if topics:
            lines.append('<h3>Topics ({:,})</h3>'.format(len(topics)))
            lines.append('<ul>')
            for t in topics:
                if isinstance(t, dict):
                    lines.append('<li><code>{}</code></li>'.format(_esc(t.get("name", str(t)))))
                else:
                    lines.append('<li><code>{}</code></li>'.format(_esc(str(t))))
            lines.append('</ul>')

        lines.append('</section>')

    # --- Methods ---
    if methods_sorted:
        lines.append('<section>')
        lines.append('<h2>Methods ({:,})</h2>'.format(len(methods_sorted)))

        if public_methods:
            lines.append('<h3>Public ({:,})</h3>'.format(len(public_methods)))
            lines.append('<table><thead><tr><th>Name</th><th>Return</th><th>Params</th><th>Modifiers</th></tr></thead><tbody>')
            for m in public_methods:
                params_str = ", ".join(m.get("params", [])) if m.get("params") else "-"
                lines.append('<tr><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                    _esc(m["name"]),
                    _esc(m.get("return_type", "void")),
                    _esc(params_str),
                    _esc(" ".join(m.get("modifiers", [])))))
            lines.append('</tbody></table>')

        if other_methods:
            lines.append('<details><summary>Non-public ({:,})</summary>'.format(len(other_methods)))
            lines.append('<table><thead><tr><th>Name</th><th>Return</th><th>Params</th><th>Modifiers</th></tr></thead><tbody>')
            for m in other_methods:
                params_str = ", ".join(m.get("params", [])) if m.get("params") else "-"
                lines.append('<tr><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                    _esc(m["name"]),
                    _esc(m.get("return_type", "void")),
                    _esc(params_str),
                    _esc(" ".join(m.get("modifiers", [])))))
            lines.append('</tbody></table>')
            lines.append('</details>')

        lines.append('</section>')

    # --- Fields ---
    if fields_sorted:
        lines.append('<section>')
        lines.append('<h2>Fields ({:,})</h2>'.format(len(fields_sorted)))
        lines.append('<table><thead><tr><th>Name</th><th>Type</th><th>Modifiers</th><th>Value</th></tr></thead><tbody>')
        for f in fields_sorted[:100]:
            lines.append('<tr><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                _esc(f["name"]),
                _esc(f.get("type", "?")),
                _esc(" ".join(f.get("modifiers", []))),
                _esc(str(f["value"])) if f.get("value") else "-"))
        if len(fields_sorted) > 100:
            lines.append('<tr><td colspan="4" class="more">... and {:,} more</td></tr>'.format(
                len(fields_sorted) - 100))
        lines.append('</tbody></table>')
        lines.append('</section>')

    # --- Exception Flow ---
    if throws_methods or catch_blocks:
        lines.append('<section>')
        lines.append('<h2>Exception Flow</h2>')
        if throws_methods:
            lines.append('<h3>Throws ({:,} methods)</h3>'.format(len(throws_methods)))
            lines.append('<table><thead><tr><th>Method</th><th>Line</th><th>Exceptions</th></tr></thead><tbody>')
            for tm in throws_methods[:30]:
                if isinstance(tm, dict):
                    lines.append('<tr><td><code>{}</code></td><td>{}</td><td>{}</td></tr>'.format(
                        _esc(tm.get("method", "?")),
                        tm.get("line", "?"),
                        _esc(", ".join(tm.get("exceptions", [])))))
                else:
                    lines.append('<tr><td colspan="3">{}</td></tr>'.format(_esc(str(tm))))
            lines.append('</tbody></table>')
        if catch_blocks:
            lines.append('<h3>Catches ({:,} blocks)</h3>'.format(len(catch_blocks)))
            lines.append('<table><thead><tr><th>Line</th><th>Exceptions</th></tr></thead><tbody>')
            for cb in catch_blocks[:30]:
                if isinstance(cb, dict):
                    lines.append('<tr><td>{}</td><td>{}</td></tr>'.format(
                        cb.get("line", "?"),
                        _esc(", ".join(cb.get("exceptions", [])))))
                else:
                    lines.append('<tr><td colspan="2">{}</td></tr>'.format(_esc(str(cb))))
            lines.append('</tbody></table>')
        lines.append('</section>')

    # --- Cross-References ---
    if importers or imports:
        lines.append('<section>')
        lines.append('<h2>Cross-References</h2>')
        if imports:
            lines.append('<h3>Imports ({:,})</h3>'.format(len(imports)))
            lines.append('<ul>')
            for imp in imports:
                lines.append('<li><code>{}</code></li>'.format(_esc(imp)))
            lines.append('</ul>')
        if importers:
            lines.append('<h3>Imported By ({:,})</h3>'.format(len(importers)))
            lines.append('<ul>')
            for imp in importers:
                lines.append('<li><code>{}</code></li>'.format(_esc(imp)))
            lines.append('</ul>')
        lines.append('</section>')

    lines.append('</main>')

    # Footer
    lines.append('<footer>')
    lines.append('<p>Generated by Module Navigator (Phase 20) | Niagara N4 Decompiled Code Analysis</p>')
    lines.append('</footer>')

    lines.append('</body>')
    lines.append('</html>')

    return "\n".join(lines)


def _get_html_css():
    """Return CSS for the HTML report (dark theme, control-room style)."""
    return """
:root {
    --bg: #0d1117;
    --surface: #161b22;
    --border: #30363d;
    --text: #c9d1d9;
    --text-dim: #8b949e;
    --accent: #58a6ff;
    --accent2: #3fb950;
    --warn: #d29922;
    --error: #f85149;
    --code-bg: #1c2128;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}
header {
    border-bottom: 2px solid var(--accent);
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
}
h1 {
    font-size: 2rem;
    color: var(--accent);
    font-family: 'Cascadia Code', 'Fira Code', monospace;
}
.subtitle {
    color: var(--text-dim);
    font-family: monospace;
    font-size: 0.95rem;
    margin-top: 0.3rem;
}
.meta {
    color: var(--text-dim);
    font-size: 0.85rem;
    margin-top: 0.5rem;
}
.meta strong { color: var(--text); }
h2 {
    color: var(--accent2);
    font-size: 1.3rem;
    margin-bottom: 0.8rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.3rem;
}
h3 {
    color: var(--text);
    font-size: 1rem;
    margin: 0.8rem 0 0.4rem;
}
section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem;
    margin-bottom: 1.5rem;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
th {
    text-align: left;
    padding: 0.5rem 0.8rem;
    background: var(--code-bg);
    color: var(--accent);
    border-bottom: 1px solid var(--border);
    font-weight: 600;
}
td {
    padding: 0.4rem 0.8rem;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
}
tr:hover { background: rgba(88, 166, 255, 0.05); }
.info-table td:first-child {
    color: var(--text-dim);
    width: 140px;
    font-weight: 500;
}
code {
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 0.85em;
    background: var(--code-bg);
    padding: 0.15em 0.4em;
    border-radius: 3px;
    color: var(--accent);
}
code.current { color: var(--accent2); font-weight: bold; }
.chain { padding: 0.5rem 0; }
.chain-item {
    padding: 0.2rem 0;
    font-size: 0.9rem;
    color: var(--text-dim);
}
ul { list-style: none; padding-left: 0; }
li {
    padding: 0.2rem 0;
    padding-left: 1rem;
    position: relative;
}
li::before {
    content: '>';
    position: absolute;
    left: 0;
    color: var(--accent);
    font-family: monospace;
}
.warn { color: var(--warn); font-weight: bold; }
.more { color: var(--text-dim); font-style: italic; text-align: center; }
details {
    margin-top: 0.5rem;
}
summary {
    cursor: pointer;
    color: var(--text-dim);
    font-size: 0.9rem;
    padding: 0.3rem 0;
}
summary:hover { color: var(--text); }
footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 0.75rem;
    text-align: center;
}
"""


# ---------------------------------------------------------------------------
# export --mermaid: Module class diagram
# ---------------------------------------------------------------------------

def cmd_export_mermaid(base_dir, module_name, output_path=None):
    """Generate a Mermaid class diagram for all classes in a module."""
    t0 = time.time()

    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    ih_data = _load_json(base_dir, "inheritance.json")
    ann_data = _load_json(base_dir, "annotations-index.json")

    classes = ci_data.get("classes", {})

    # Collect classes in this module
    mod_classes = []
    for cname, entries in classes.items():
        for e in entries:
            if e.get("outer_class") is not None:
                continue
            if e["module"] == module_name:
                mod_classes.append((cname, e))

    if not mod_classes:
        print("  Module '{}' not found or has no classes.".format(module_name))
        print("  Try: modules --has-code")
        return

    mod_classes.sort(key=lambda x: x[0])

    # Get annotations for slot counts
    niagara_types = ann_data.get("niagara_types", {}) if ann_data else {}

    # Build Mermaid output
    lines = []
    lines.append("```mermaid")
    lines.append("classDiagram")
    lines.append("  direction TB")
    lines.append("")

    # Class definitions
    for cname, e in mod_classes:
        sid = _safe_id(cname)
        kind = e.get("kind", "class")
        if kind == "interface":
            lines.append("  class {} {{".format(sid))
            lines.append("    <<interface>>")
        elif kind == "enum":
            lines.append("  class {} {{".format(sid))
            lines.append("    <<enum>>")
        elif "abstract" in e.get("modifiers", []):
            lines.append("  class {} {{".format(sid))
            lines.append("    <<abstract>>")
        else:
            lines.append("  class {} {{".format(sid))

        # Add Niagara slots if available
        if cname in niagara_types:
            nt = niagara_types[cname]
            if isinstance(nt, list):
                nt = nt[0] if nt else {}
            for prop in (nt.get("properties", []) or [])[:8]:
                if isinstance(prop, dict):
                    pname = prop.get("name", "?")
                    ptype = prop.get("type", "?")
                    lines.append("    +{} {}".format(_esc_mermaid(ptype), _esc_mermaid(pname)))
                else:
                    lines.append("    +{}".format(_esc_mermaid(str(prop))))
            for act in (nt.get("actions", []) or [])[:5]:
                if isinstance(act, dict):
                    aname = act.get("name", "?")
                    lines.append("    +{}()".format(_esc_mermaid(aname)))
                else:
                    lines.append("    +{}()".format(_esc_mermaid(str(act))))
            remaining = (len(nt.get("properties", []) or []) - 8) + (len(nt.get("actions", []) or []) - 5)
            if remaining > 0:
                pass  # Don't add "..." to avoid clutter

        lines.append("  }")

    lines.append("")

    # Build a set of class names in this module for filtering relationships
    mod_class_names = set(c[0] for c in mod_classes)

    # Inheritance relationships
    for cname, e in mod_classes:
        sid = _safe_id(cname)
        parent = e.get("extends")
        if parent and parent in mod_class_names:
            lines.append("  {} <|-- {}".format(_safe_id(parent), sid))
        elif parent:
            # External parent - add as a note
            lines.append("  {} <|-- {} : extends".format(_safe_id(parent), sid))

        for iface in (e.get("implements") or []):
            if iface in mod_class_names:
                lines.append("  {} <|.. {}".format(_safe_id(iface), sid))

    lines.append("```")

    mermaid_text = "\n".join(lines)
    elapsed = time.time() - t0

    # Output
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(mermaid_text)
        print("")
        print("  " + "=" * 65)
        print("  MERMAID EXPORT: {}".format(module_name))
        print("  " + "=" * 65)
        print("")
        print("  Output: {}".format(output_path))
        size_kb = os.path.getsize(output_path) / 1024.0
        print("  Size:   {:.1f} KB".format(size_kb))
    else:
        print("")
        print("  " + "=" * 65)
        print("  MERMAID CLASS DIAGRAM: {}".format(module_name))
        print("  " + "=" * 65)
        print("")
        print(mermaid_text)

    print("")
    print("  Classes: {:,}  Relationships: {:,}  Time: {:.2f}s".format(
        len(mod_classes),
        sum(1 for _, e in mod_classes if e.get("extends") and e["extends"] in mod_class_names) +
        sum(len([i for i in (e.get("implements") or []) if i in mod_class_names])
            for _, e in mod_classes),
        elapsed))
    print("  Tip: paste into https://mermaid.live/ to render")
    print("")


def _esc_mermaid(text):
    """Escape text for Mermaid (remove angle brackets, etc.)."""
    if not text:
        return ""
    return str(text).replace("<", "~").replace(">", "~").replace("{", "(").replace("}", ")")


# ---------------------------------------------------------------------------
# export --dot: DOT graph (call-chain or module classes)
# ---------------------------------------------------------------------------

def cmd_export_dot(base_dir, name, method=None, output_path=None):
    """Generate DOT graph for Graphviz.

    If method is given: call-chain graph for class.method
    If method is None: class relationship graph for module
    """
    if method:
        _export_dot_callchain(base_dir, name, method, output_path)
    else:
        _export_dot_module(base_dir, name, output_path)


def _export_dot_callchain(base_dir, class_name, method_name, output_path=None):
    """Generate DOT call-chain graph for a specific method."""
    t0 = time.time()

    cg_data = _load_json(base_dir, "callgraph-index.json")
    if not cg_data:
        print("ERROR: callgraph-index.json not found.")
        print("Run: python tools/build_callgraph_index.py")
        return

    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    classes = ci_data.get("classes", {})
    resolved, entry = _resolve_class(classes, class_name)

    if not resolved:
        print("  Class '{}' not found.".format(class_name))
        return

    # callgraph-index uses calls dict: "Class.method" -> [callee strings "Class.method"]
    calls = cg_data.get("calls", {})

    root_key = "{}.{}".format(resolved, method_name)
    if root_key not in calls:
        print("  No callees found for {}.{}".format(resolved, method_name))
        print("  Try: callees {} {}".format(resolved, method_name))
        return

    # BFS to build call-chain tree (depth 3)
    max_depth = 3
    edges = []
    visited = set()
    queue = [(root_key, 0)]
    visited.add(root_key)

    while queue:
        node, depth = queue.pop(0)
        if depth >= max_depth:
            continue

        callees = calls.get(node, [])
        if not isinstance(callees, list):
            continue

        for callee in callees:
            if not isinstance(callee, str):
                continue
            edges.append((node, callee))
            if callee not in visited:
                visited.add(callee)
                queue.append((callee, depth + 1))

    if not edges:
        print("  No callees found for {}.{}".format(resolved, method_name))
        print("  Try: callees {} {}".format(resolved, method_name))
        return

    # Build DOT
    lines = []
    lines.append('digraph call_chain {')
    lines.append('  rankdir=LR;')
    lines.append('  node [shape=box, fontsize=9, fontname="Consolas"];')
    lines.append('  edge [fontsize=8];')
    # Deduplicate edges
    unique_edges = list(set(edges))

    lines.append('  "{}" [style=filled, fillcolor="#58a6ff", fontcolor=white];'.format(root_key))
    lines.append('')

    for src, dst in unique_edges:
        lines.append('  "{}" -> "{}";'.format(src, dst))

    lines.append('}')

    dot_text = "\n".join(lines)
    elapsed = time.time() - t0

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(dot_text)
        print("")
        print("  " + "=" * 65)
        print("  DOT CALL-CHAIN: {}.{}".format(resolved, method_name))
        print("  " + "=" * 65)
        print("")
        print("  Output: {}".format(output_path))
        size_kb = os.path.getsize(output_path) / 1024.0
        print("  Size:   {:.1f} KB".format(size_kb))
    else:
        print("")
        print("  " + "=" * 65)
        print("  DOT CALL-CHAIN: {}.{}".format(resolved, method_name))
        print("  " + "=" * 65)
        print("")
        print(dot_text)

    print("")
    print("  Nodes: {:,}  Edges: {:,}  Depth: {}  Time: {:.2f}s".format(
        len(visited), len(unique_edges), max_depth, elapsed))
    print("  Tip: render with 'dot -Tpng output.dot -o output.png'")
    print("")


def _export_dot_module(base_dir, module_name, output_path=None):
    """Generate DOT class relationship graph for a module."""
    t0 = time.time()

    ci_data = _load_json(base_dir, "class-index.json")
    if not ci_data:
        print("ERROR: class-index.json not found.")
        return

    ann_data = _load_json(base_dir, "annotations-index.json")

    classes = ci_data.get("classes", {})

    # Collect classes in this module
    mod_classes = []
    for cname, entries in classes.items():
        for e in entries:
            if e.get("outer_class") is not None:
                continue
            if e["module"] == module_name:
                mod_classes.append((cname, e))

    if not mod_classes:
        print("  Module '{}' not found or has no classes.".format(module_name))
        return

    mod_classes.sort(key=lambda x: x[0])
    mod_class_names = set(c[0] for c in mod_classes)

    niagara_types = ann_data.get("niagara_types", {}) if ann_data else {}

    # Build DOT
    lines = []
    lines.append('digraph {} {{'.format(_safe_id(module_name)))
    lines.append('  rankdir=TB;')
    lines.append('  node [shape=record, fontsize=9, fontname="Consolas"];')
    lines.append('  label="Module: {}";'.format(module_name))
    lines.append('  labelloc=t;')
    lines.append('  fontsize=14;')
    lines.append('')

    # Nodes
    for cname, e in mod_classes:
        sid = _safe_id(cname)
        kind = e.get("kind", "class")

        label_parts = [cname]
        stereo = ""
        if kind == "interface":
            stereo = "\\n<<interface>>"
        elif kind == "enum":
            stereo = "\\n<<enum>>"
        elif "abstract" in e.get("modifiers", []):
            stereo = "\\n<<abstract>>"

        # Color by type
        if kind == "interface":
            color = "#3fb950"
        elif kind == "enum":
            color = "#d29922"
        elif "abstract" in e.get("modifiers", []):
            color = "#bc8cff"
        elif cname.startswith("B"):
            color = "#58a6ff"
        else:
            color = "#8b949e"

        # Slot summary
        slot_label = ""
        if cname in niagara_types:
            nt = niagara_types[cname]
            if isinstance(nt, list):
                nt = nt[0] if nt else {}
            np = len(nt.get("properties", []) or [])
            na = len(nt.get("actions", []) or [])
            nt_count = len(nt.get("topics", []) or [])
            if np or na or nt_count:
                slot_label = "\\n[{} props, {} acts, {} topics]".format(np, na, nt_count)

        lines.append('  {} [label="{}{}{}", style=filled, fillcolor="{}"];'.format(
            sid, cname, stereo, slot_label, color))

    lines.append('')

    # Edges
    edge_count = 0
    for cname, e in mod_classes:
        sid = _safe_id(cname)
        parent = e.get("extends")
        if parent and parent in mod_class_names:
            lines.append('  {} -> {} [arrowhead=empty];'.format(sid, _safe_id(parent)))
            edge_count += 1

        for iface in (e.get("implements") or []):
            if iface in mod_class_names:
                lines.append('  {} -> {} [style=dashed, arrowhead=empty];'.format(
                    sid, _safe_id(iface)))
                edge_count += 1

    lines.append('}')

    dot_text = "\n".join(lines)
    elapsed = time.time() - t0

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(dot_text)
        print("")
        print("  " + "=" * 65)
        print("  DOT MODULE DIAGRAM: {}".format(module_name))
        print("  " + "=" * 65)
        print("")
        print("  Output: {}".format(output_path))
        size_kb = os.path.getsize(output_path) / 1024.0
        print("  Size:   {:.1f} KB".format(size_kb))
    else:
        print("")
        print("  " + "=" * 65)
        print("  DOT MODULE DIAGRAM: {}".format(module_name))
        print("  " + "=" * 65)
        print("")
        print(dot_text)

    print("")
    print("  Classes: {:,}  Edges: {:,}  Time: {:.2f}s".format(
        len(mod_classes), edge_count, elapsed))
    print("  Tip: render with 'dot -Tpng output.dot -o output.png'")
    print("")
