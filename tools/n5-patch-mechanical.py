#!/usr/bin/env python3
"""n5-patch-mechanical.py -- javac-error-driven mechanical source patches for decompiled
N5 classes that stay bytecode-only because the source does not compile (C3b/C3c/C3a-G2).

The F8/C3a patcher (n5-patch-doprivileged.py) fixes one defect from bytecode evidence. This
stage generalises the pattern to the other Vineflower defects that have exactly one
deterministic source-level fix. Every patch is a `fixer`:

  * it recognises ONE javac error shape (message + the source line javac points at),
  * it rewrites only that construct (no guessing between alternatives: when the shape is
    not unambiguous the site is left alone and reported as residual),
  * javac re-verifies after every round: a round that does not reduce the error count is
    reverted and the fixer is blacklisted for that class.

The grader (tools/n5-fidelity.py --regrade-nonclean --patch-tree <tree>) decides whether a
patched class is faithful; this tool never claims fidelity. Input is the vineflower2p
tree when it has the class (the C3a output), else vineflower2. Output tree
(default vineflower2m) holds every vineflower2p file (carried unchanged, so the regrade of
the patched rung keeps the C3a results) plus the mechanically patched classes, and a
PATCHES.json manifest recording each patch (fixer kind, line, javac evidence) and each
unresolved class with its residual javac errors.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

MAX_ROUNDS = 8

_ERR_RE = re.compile(r"^(?:.*\.java):(\d+): error: (.*)$")


def parse_javac_errors(stderr: str) -> list[dict]:
    """[{line, col, message, detail}] for every javac error. `col` is the caret column
    (0-based) within the source line, `detail` the indented lines after the caret."""
    lines = stderr.splitlines()
    out: list[dict] = []
    i = 0
    while i < len(lines):
        m = _ERR_RE.match(lines[i])
        if not m:
            i += 1
            continue
        err = {"line": int(m.group(1)), "message": m.group(2), "col": None, "detail": []}
        j = i + 1
        # source line, caret line, then detail lines up to the next diagnostic
        if j < len(lines):
            j += 1
        if j < len(lines) and lines[j].rstrip().endswith("^") and set(lines[j].rstrip()[:-1]) <= {" ", "\t"}:
            err["col"] = len(lines[j].rstrip()) - 1
            j += 1
        while j < len(lines) and not re.match(r"^.*\.java:\d+: (error|warning)|^Note: |^\d+ errors?$", lines[j]):
            err["detail"].append(lines[j])
            j += 1
        out.append(err)
        i = j
    return out


def _error_count(stderr: str) -> int:
    return len(parse_javac_errors(stderr))


# ---------------------------------------------------------------------------
# fixers: fn(lines, errors) -> Optional[(new_lines, [patch records])]
# ---------------------------------------------------------------------------

def _indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


_BINDING_RE = re.compile(
    r"^(?P<ind>\s*)if \(!\((?P<expr>[\w.]+) instanceof (?P<type>[\w.<>?, \[\]]+?) (?P<var>\w+)\)\) \{\s*$")


def fix_pattern_binding_scope(lines: list[str], errors: list[dict], ctx=None):
    """`if (!(E instanceof T v)) { ...v = X; }` then `v` used after the if: javac puts a
    negated-instanceof binding in scope after the statement only when the block cannot
    complete normally. Vineflower folds `else v = (T)E;` into the binding. Restore the
    bytecode shape: declare `T v;`, test `!(E instanceof T)`, add `else { v = (T)E; }`."""
    missing = {}
    for e in errors:
        if e["message"] == "cannot find symbol":
            m = re.search(r"symbol:\s+variable (\w+)", "\n".join(e["detail"]))
            if m:
                missing.setdefault(m.group(1), e["line"])
    if not missing:
        return None
    new = list(lines)
    patches = []
    # bottom-up so earlier line numbers stay valid
    sites = []
    for var, err_line in missing.items():
        for k in range(min(err_line, len(lines)) - 1, -1, -1):
            m = _BINDING_RE.match(lines[k])
            if m and m.group("var") == var:
                sites.append((k, m))
                break
    for k, m in sorted(sites, key=lambda s: -s[0]):
        ind = m.group("ind")
        end = next((j for j in range(k + 1, len(new)) if _indent(new[j]) == ind and new[j].strip() == "}"), None)
        if end is None:
            continue
        typ, var, expr = m.group("type"), m.group("var"), m.group("expr")
        new[end:end + 1] = [f"{ind}}} else {{", f"{ind}   {var} = ({typ}){expr};", f"{ind}}}"]
        new[k] = f"{ind}if (!({expr} instanceof {typ})) {{"
        new.insert(k, f"{ind}{typ} {var};")
        patches.append({"kind": "pattern-binding-scope", "line": k + 1, "variable": var,
                        "evidence": f"javac: cannot find symbol variable {var} (negated instanceof binding not in scope)"})
    if not patches:
        return None
    return new, patches


_BOXED = {"int": "Integer", "long": "Long", "short": "Short", "byte": "Byte", "char": "Character",
          "boolean": "Boolean", "float": "Float", "double": "Double"}
_RAW_ITERABLES = ("List", "Set", "Collection", "Iterable", "ArrayList", "LinkedList", "HashSet", "LinkedHashSet",
                  "TreeSet", "SortedSet", "Vector", "Queue", "Deque", "ArrayDeque")
_FOREACH_RAW_RE = re.compile(
    r"(for \((?:final )?(?P<type>[\w.<>?\[\]]+) \w+ : )\((?P<raw>(?:[\w.]+\.)?(?:%s))\)" % "|".join(_RAW_ITERABLES))


def fix_foreach_raw_cast(lines: list[str], errors: list[dict], ctx=None):
    """`for (T v : (List)expr)` -- javac: `Object cannot be converted to T`. The decompiler
    dropped the type argument of the raw cast; the loop variable's type is the element
    type the bytecode checkcasts to, so the cast becomes `(List<T>)` (boxed for a primitive)."""
    new = list(lines)
    patches = []
    for e in errors:
        if not re.match(r"incompatible types: (?:java\.lang\.)?Object cannot be converted to ", e["message"]):
            continue
        k = e["line"] - 1
        m = _FOREACH_RAW_RE.search(new[k]) if 0 <= k < len(new) else None
        if not m:
            continue
        typ = m.group("type")
        arg = _BOXED.get(typ, typ)
        new[k] = new[k][:m.start()] + f"{m.group(1)}({m.group('raw')}<{arg}>)" + new[k][m.end():]
        patches.append({"kind": "foreach-raw-cast", "line": e["line"], "element_type": arg,
                        "evidence": "javac: " + e["message"]})
    return (new, patches) if patches else None


_BOOL_AS_INT_RE = re.compile(r"^(?P<ind>\s*)int (?P<var>\w+) = (?P<lit>true|false);\s*$")


def fix_boolean_declared_int(lines: list[str], errors: list[dict], ctx=None):
    """`int v = false;` -- javac: `boolean cannot be converted to int`. Vineflower typed the
    local by the JVM's int slot; the source only compiles with the literal's type."""
    new = list(lines)
    patches = []
    for e in errors:
        if e["message"] != "incompatible types: boolean cannot be converted to int":
            continue
        k = e["line"] - 1
        m = _BOOL_AS_INT_RE.match(new[k]) if 0 <= k < len(new) else None
        if not m:
            continue
        new[k] = f"{m.group('ind')}boolean {m.group('var')} = {m.group('lit')};"
        patches.append({"kind": "boolean-declared-int", "line": e["line"], "variable": m.group("var"),
                        "evidence": "javac: " + e["message"]})
    return (new, patches) if patches else None


_INSTANCEOF_GENERIC_RE = re.compile(r"instanceof (?P<raw>[\w.]+)<[^<>()]*(?:<[^<>()]*>[^<>()]*)*> (?P<var>\w+)")


def fix_instanceof_generic_raw(lines: list[str], errors: list[dict], ctx=None):
    """`x instanceof Comparable<T> v` -- javac: `Object cannot be safely cast to Comparable<T>`.
    instanceof is erased in the class file, so the type arguments carry no bytecode
    evidence; the raw type is the only spelling that is always legal."""
    new = list(lines)
    patches = []
    for e in errors:
        if not re.search(r"cannot be safely cast to ", e["message"]):
            continue
        k = e["line"] - 1
        m = _INSTANCEOF_GENERIC_RE.search(new[k]) if 0 <= k < len(new) else None
        if not m:
            continue
        new[k] = new[k][:m.start()] + f"instanceof {m.group('raw')} {m.group('var')}" + new[k][m.end():]
        patches.append({"kind": "instanceof-generic-raw", "line": e["line"], "variable": m.group("var"),
                        "evidence": "javac: " + e["message"]})
    return (new, patches) if patches else None


_LABEL_RE = re.compile(r"^\s*(?:case .*|default)\s*:\s*$")
_REDEF_RE = re.compile(r"variable (\w+) is already defined in ")


def _case_group(lines: list[str], k: int, ind: int):
    """(first_label, last_label, last_stmt) of the switch group holding line k whose
    statements sit at column `ind` (labels at ind-3), or None."""
    lab = None
    for j in range(k - 1, -1, -1):
        s = lines[j]
        if not s.strip():
            continue
        i = len(s) - len(s.lstrip())
        if i < ind - 3:
            return None
        if i == ind - 3:
            if _LABEL_RE.match(s):
                lab = j
                break
            return None
    if lab is None:
        return None
    first = lab
    while first > 0 and _LABEL_RE.match(lines[first - 1]) and _indent(lines[first - 1]) == _indent(lines[lab]):
        first -= 1
    end = None
    for j in range(lab + 1, len(lines)):
        s = lines[j]
        if not s.strip():
            continue
        i = len(s) - len(s.lstrip())
        if i < ind:
            break
        end = j
    return None if end is None else (first, lab, end)


def _add_declaring_groups(lines: list[str], groups: dict) -> None:
    """Add to `groups` every other group of the same switch(es) that declares a local at group
    level. The original scoped every declaring group (javac frees a braced group's slots for the
    next one), so bracing only the groups javac flagged leaves unflagged declarations holding
    slots and shifts the slot of every later local (C3b-G1: renaming the duplicates instead has
    the same defect and, unlike bracing, never reuses a slot at all)."""
    for first, _last_label, end in list(groups.values()):
        ind = len(lines[end]) - len(lines[end].lstrip())
        lo, hi = first, end
        while lo > 0:
            s = lines[lo - 1]
            if s.strip() and len(s) - len(s.lstrip()) < ind - 3:
                break
            lo -= 1
        while hi + 1 < len(lines):
            s = lines[hi + 1]
            if s.strip() and len(s) - len(s.lstrip()) < ind - 3:
                break
            hi += 1
        decl = re.compile(r"^\s{%d}(?:final )?[\w.<>\[\]?, ]+ \w+\s*(?:=|;)" % ind)
        for t in range(lo, hi + 1):
            if not _LABEL_RE.match(lines[t]) or len(_indent(lines[t])) != ind - 3:
                continue
            g = _case_group(lines, t + 1, ind)
            if g and g[1] == t and t not in groups and any(decl.match(lines[u]) for u in range(g[1] + 1, g[2] + 1)):
                groups[t] = g


def fix_switch_group_scope(lines: list[str], errors: list[dict], ctx=None):
    """`variable v is already defined` where the duplicate sits in a switch group: switch
    groups share one scope, so the original source had braces around each group (javac
    reuses the slot). Brace every group of the switch that declares `v`."""
    groups: dict[int, tuple] = {}
    for e in errors:
        m = _REDEF_RE.match(e["message"])
        k = e["line"] - 1
        if not m or not 0 <= k < len(lines):
            continue
        var = m.group(1)
        ind = len(lines[k]) - len(lines[k].lstrip())
        g = _case_group(lines, k, ind)
        if g is None:
            continue
        groups[g[1]] = g
        decl = re.compile(r"^\s{%d}(?:final )?[\w.<>\[\]?, ]+ %s\b\s*(?:=|;)" % (ind, re.escape(var)))
        # earlier groups of the same switch that declare the variable
        j = g[0] - 1
        while j >= 0:
            if lines[j].strip() and _indent(lines[j]) and len(_indent(lines[j])) < ind - 3:
                break
            if _LABEL_RE.match(lines[j]) and len(_indent(lines[j])) == ind - 3:
                eg = _case_group(lines, j + 1, ind)
                if eg and eg[1] == j and any(decl.match(lines[t]) for t in range(eg[1] + 1, eg[2] + 1)):
                    groups[eg[1]] = eg
                    j = eg[0]
            j -= 1
    if not groups:
        return None
    _add_declaring_groups(lines, groups)
    new = list(lines)
    patches = []
    for lab, first, end in sorted(((g[1], g[0], g[2]) for g in groups.values()), reverse=True):
        ind = _indent(new[lab])
        new.insert(end + 1, f"{ind}}}")
        new[lab] = new[lab].rstrip() + " {"
        patches.append({"kind": "switch-group-scope", "line": lab + 1,
                        "evidence": "javac: variable already defined across switch groups"})
    return new, patches


_CATCH_RE = re.compile(r"^(?P<ind>\s*)(?:\} )?catch \((?:final )?[\w.<>| ?]+ (?P<var>\w+)\) \{\s*$")


def _enclosing_catch(lines: list[str], k: int):
    """(catch_line, end_line, param) of the innermost catch block containing line k."""
    for j in range(k, -1, -1):
        m = _CATCH_RE.match(lines[j])
        if not m:
            continue
        ind = m.group("ind")
        end = next((t for t in range(j + 1, len(lines))
                    if _indent(lines[t]) == ind and lines[t].lstrip().startswith("}")), None)
        if end is not None and j < k <= end:
            return j, end, m.group("var")
    return None


def fix_catch_parameter_name(lines: list[str], errors: list[dict], ctx=None):
    """`catch (Exception e) { ... ex ... }` with `ex` undeclared -- javac: cannot find symbol.
    Vineflower renamed the catch parameter (to dodge a clash with an enclosing name) but not
    the uses in its body. The catch parameter is the only variable the body can mean."""
    new = list(lines)
    patches = []
    seen = set()
    for e in errors:
        m = re.search(r"symbol:\s+variable (\w+)", "\n".join(e["detail"])) if e["message"] == "cannot find symbol" else None
        k = e["line"] - 1
        if not m or not 0 <= k < len(new):
            continue
        blk = _enclosing_catch(new, k)
        if blk is None or (blk[0], m.group(1)) in seen or blk[2] == m.group(1):
            continue
        seen.add((blk[0], m.group(1)))
        pat = re.compile(r"(?<![\w.$])%s\b" % re.escape(m.group(1)))
        for t in range(blk[0] + 1, blk[1]):
            new[t] = pat.sub(blk[2], new[t])
        patches.append({"kind": "catch-parameter-name", "line": blk[0] + 1, "renamed": m.group(1), "to": blk[2],
                        "evidence": f"javac: cannot find symbol variable {m.group(1)} inside catch ({blk[2]})"})
    return (new, patches) if patches else None


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def _first_argument_span(text: str, open_paren: int):
    """(start, end) of the first call argument after `(` at `open_paren`, `end` at the
    delimiting `,` or `)`; skips nested brackets, string and char literals. None when
    the call has no arguments or the text is malformed."""
    i, depth, n = open_paren + 1, 0, len(text)
    while i < n and text[i].isspace():
        i += 1
    start = i
    while i < n:
        ch = text[i]
        if ch in "\"'":
            q = ch
            i += 1
            while i < n and text[i] != q:
                i += 2 if text[i] == "\\" else 1
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth == 0:
                return (start, i) if ch == ")" and i > start else None
            depth -= 1
        elif ch == "," and depth == 0:
            return start, i
        i += 1
    return None


_CTOR_ERR_RE = re.compile(r"constructor \w+ in class [\w.$<>]+ cannot be applied to given types;|"
                          r"no suitable constructor found for ")
_OUTER_THIS_RE = re.compile(r"^(?:[\w.$]+\.)?this$")


def fix_inner_ctor_outer_arg(lines: list[str], errors: list[dict], ctx=None):
    """`super(Outer.this, x)` / `new Inner(this, x)` -- javac: constructor cannot be applied
    (found one argument more than required). Vineflower prints the synthetic outer-instance
    constructor parameter of an inner class as an argument; source passes it implicitly.
    Only a first argument that is `this` / `Outer.this` is dropped."""
    text = "\n".join(lines)
    starts = _line_starts(text)
    edits = []
    for e in errors:
        if not _CTOR_ERR_RE.match(e["message"]) or e["col"] is None or e["line"] - 1 >= len(starts):
            continue
        detail = "\n".join(e["detail"])
        req = re.search(r"required: (.*)", detail)
        fnd = re.search(r"found:\s+(.*)", detail)
        if req and fnd:
            n_req = 0 if req.group(1).strip() == "no arguments" else len(req.group(1).split(","))
            if len(fnd.group(1).split(",")) != n_req + 1:
                continue
        off = starts[e["line"] - 1] + e["col"]
        m = re.compile(r"(?:super|this|new\s+[\w.$]+(?:<[^()]*>)?)\s*\(").match(text, off)
        if not m:
            continue
        span = _first_argument_span(text, m.end() - 1)
        if span is None or not _OUTER_THIS_RE.match(text[span[0]:span[1]].strip()):
            continue
        end = span[1]
        if text[end] == ",":
            end += 1
            while text[end] in " \t":
                end += 1
        edits.append((span[0], end, e["line"], text[span[0]:span[1]].strip()))
    if not edits:
        return None
    patches = []
    for a, b, line, arg in sorted(set(edits), reverse=True):
        text = text[:a] + text[b:]
        patches.append({"kind": "inner-ctor-outer-arg", "line": line, "dropped": arg,
                        "evidence": "javac: constructor cannot be applied (outer instance passed explicitly)"})
    return text.split("\n"), patches


_METHODREF_RE = re.compile(r"^\s*#\d+ = (?:Interface)?Methodref\s+#\d+\.#\d+\s+// +(?P<owner>[^.\s]+)\.(?P<name>\S+?):(?P<desc>\(.*\).+)$",
                           re.M)


def parse_methodrefs(javap_text: str) -> set:
    """{(owner, name, descriptor)} of every (Interface)Methodref in the constant pools of a
    `javap -v` dump (owner as an internal name, `<init>` for constructors)."""
    return {(m.group("owner").strip('"'), m.group("name").strip('"'), m.group("desc"))
            for m in _METHODREF_RE.finditer(javap_text)}


def _split_top(text: str) -> list[str]:
    out, depth, cur = [], 0, []
    for ch in text:
        if ch in "<([":
            depth += 1
        elif ch in ">)]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        out.append("".join(cur).strip())
    return out


def _simple_type(t: str) -> str:
    """`java.util.Map<String,Object>[]` -> `Map[]`; varargs `X...` -> `X[]`."""
    t = t.strip()
    dims = t.count("[]") + (1 if t.endswith("...") else 0)
    t = re.sub(r"<.*>", "", t.replace("...", "").replace("[]", ""))
    return t.rsplit(".", 1)[-1] + "[]" * dims


def _descriptor_params(desc: str) -> list[tuple[str, str]]:
    """[(simple, qualified-source)] per parameter of a method descriptor."""
    prims = {"Z": "boolean", "B": "byte", "C": "char", "S": "short", "I": "int", "J": "long", "F": "float", "D": "double"}
    body = desc[1:desc.index(")")]
    out, i = [], 0
    while i < len(body):
        dims = 0
        while body[i] == "[":
            dims += 1
            i += 1
        if body[i] == "L":
            j = body.index(";", i)
            q = body[i + 1:j].replace("/", ".").replace("$", ".")
            i = j + 1
        else:
            q = prims[body[i]]
            i += 1
        out.append((q.rsplit(".", 1)[-1] + "[]" * dims, q + "[]" * dims))
    return out


_AMBIG_RE = re.compile(r"reference to (?P<name>\w+) is ambiguous")
_BOTH_RE = re.compile(r"both (?:method|constructor) (?:<[^>]*> )?(?P<n1>\w+)\((?P<p1>.*?)\) in [\w.$]+ and "
                      r"(?:method|constructor) (?:<[^>]*> )?(?P<n2>\w+)\((?P<p2>.*?)\) in [\w.$]+ match")


def _call_arguments(text: str, open_paren: int):
    """[(start, end)] of every top-level argument of the call opened at `open_paren`."""
    spans, i, n = [], open_paren + 1, len(text)
    depth, start = 0, None
    while i < n:
        ch = text[i]
        if start is None and not ch.isspace():
            start = i
        if ch in "\"'":
            q = ch
            i += 1
            while i < n and text[i] != q:
                i += 2 if text[i] == "\\" else 1
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth == 0:
                if start is not None and start < i:
                    spans.append((start, len(text[:i].rstrip())))
                return spans
            depth -= 1
        elif ch == "," and depth == 0:
            spans.append((start, len(text[:i].rstrip())))
            start = None
        i += 1
    return None


def _methodrefs(ctx: Optional[dict]):
    """The class's shipped Methodref set: ctx["methodrefs"], else computed once (lazily, javap -v
    is not free) from ctx["methodrefs_fn"]."""
    if not ctx:
        return None
    if "methodrefs" not in ctx and "methodrefs_fn" in ctx:
        ctx["methodrefs"] = ctx["methodrefs_fn"]()
    return ctx.get("methodrefs")


def fix_ambiguous_overload_cast(lines: list[str], errors: list[dict], ctx=None):
    """`reference to m is ambiguous` (both m(A,..) and m(B,..) match, typically a `null` or
    conditional argument). The shipped class file's constant pool names exactly which
    descriptor the original source bound to: when exactly ONE of javac's two candidates is a
    Methodref of that name in the pool, the arguments at the positions where the candidates
    differ are cast to that descriptor's parameter types."""
    refs = _methodrefs(ctx)
    if not refs:
        return None
    text = "\n".join(lines)
    starts = _line_starts(text)
    edits = []
    for e in errors:
        am = _AMBIG_RE.match(e["message"])
        both = _BOTH_RE.search(" ".join(x.strip() for x in e["detail"]))
        if not am or not both or e["col"] is None or e["line"] - 1 >= len(starts):
            continue
        name = am.group("name")
        cands = [[_simple_type(p) for p in _split_top(both.group("p1"))],
                 [_simple_type(p) for p in _split_top(both.group("p2"))]]
        if len(cands[0]) != len(cands[1]):
            continue
        chosen = []
        for idx, params in enumerate(cands):
            for owner, mname, desc in refs:
                if mname not in (name, "<init>"):
                    continue
                dp = _descriptor_params(desc)
                if [d[0] for d in dp] == params:
                    chosen.append((idx, dp))
        uniq = {tuple(d[1] for d in dp) for _, dp in chosen}
        if len(chosen) < 1 or len(uniq) != 1 or len({i for i, _ in chosen}) != 1:
            continue
        idx, dp = chosen[0]
        off = starts[e["line"] - 1] + e["col"]
        m = re.compile(r"[.\s]*(?:this|super|new\s+[\w.$]+|%s)\s*\(" % re.escape(name)).match(text, off) or \
            re.compile(r"[^(]*?\b%s\s*\(" % re.escape(name)).match(text, off)
        if not m:
            continue
        args = _call_arguments(text, m.end() - 1)
        if args is None or len(args) != len(dp):
            continue
        other = cands[1 - idx]
        for pos, (a, b) in enumerate(args):
            if cands[idx][pos] == other[pos]:
                continue
            arg = text[a:b]
            if arg.startswith("(" + dp[pos][1] + ")") or re.match(r"^\(\w[\w.]*(?:\[\])*\)", arg):
                continue
            wrapped = arg if re.match(r"^[\w.$]+(?:\(\))?$", arg) else f"({arg})"
            edits.append((a, b, f"({dp[pos][1]}){wrapped}", e["line"], name))
    if not edits:
        return None
    patches = []
    for a, b, repl, line, name in sorted(set(edits), reverse=True):
        text = text[:a] + repl + text[b:]
        patches.append({"kind": "ambiguous-overload-cast", "line": line, "call": name, "cast": repl,
                        "evidence": "javac: reference to %s is ambiguous; shipped constant pool binds one descriptor" % name})
    return text.split("\n"), patches


_SWITCH_EXPR_RE = re.compile(r"^(?P<ind>\s*)(?P<var>[\w.$\[\]]+) = switch \((?P<sel>.*)\) \{\s*$")


def fix_switch_yield_statement(lines: list[str], errors: list[dict], ctx=None):
    """`x = switch (e) { ... -> { if (c) { yield v; } } ... };` -- javac: switch rule completes
    without providing a value. Vineflower wrapped a switch STATEMENT whose arms assign `x`
    in a switch expression. Restore the statement: `switch (e) { ... x = v; ... }`. Only
    when the switch has no nested switch and every `yield`/arm expression is rewritten."""
    bad = [e["line"] - 1 for e in errors if e["message"] == "switch rule completes without providing a value"]
    if not bad:
        return None
    new = list(lines)
    patches = []
    done = set()
    for b in bad:
        head = next((j for j in range(b, -1, -1) if _SWITCH_EXPR_RE.match(new[j])), None)
        if head is None or head in done:
            continue
        m = _SWITCH_EXPR_RE.match(new[head])
        ind = m.group("ind")
        end = next((t for t in range(head + 1, len(new)) if new[t] == f"{ind}}};" or new[t].rstrip() == f"{ind}}};"), None)
        if end is None or end < b:
            continue
        body = new[head + 1:end]
        if any(re.search(r"\bswitch \(", x) for x in body):
            continue
        var = m.group("var")
        arm_ind = ind + "   "
        out = []
        ok = True
        for x in body:
            if re.match(r"^\s*yield ", x):
                x = re.sub(r"yield ", f"{var} = ", x, count=1)
            elif x.startswith(arm_ind) and re.match(r"^\s*(?:case .*|default) -> ", x) and not x.rstrip().endswith("{"):
                mm = re.match(r"^(\s*(?:case .*?|default) -> )(?!throw )(.*;)\s*$", x)
                if mm:
                    x = f"{mm.group(1)}{var} = {mm.group(2)}"
                elif not re.match(r"^\s*(?:case .*?|default) -> throw ", x):
                    ok = False
            out.append(x)
        if not ok:
            continue
        new[head + 1:end] = out
        new[head] = f"{ind}switch ({m.group('sel')}) {{"
        new[end] = f"{ind}}}"
        done.add(head)
        patches.append({"kind": "switch-yield-statement", "line": head + 1, "variable": var,
                        "evidence": "javac: switch rule completes without providing a value"})
    return (new, patches) if patches else None


def fix_loop_exit_break(lines: list[str], errors: list[dict], ctx=None):
    """`unreachable statement` right after `while (true) { ... ; ... }`: Vineflower lost the
    `break` of a duplicated-finally loop exit and left an empty statement. When the endless
    loop directly before the unreachable statement holds exactly one empty statement `;`
    on its own line, that is the exit."""
    new = list(lines)
    patches = []
    for e in errors:
        if e["message"] != "unreachable statement":
            continue
        k = e["line"] - 1
        # the closing brace of the loop is the previous non-blank line
        c = k - 1
        while c >= 0 and not new[c].strip():
            c -= 1
        if c < 0 or new[c].strip() != "}":
            continue
        ind = _indent(new[c])
        w = next((j for j in range(c - 1, -1, -1) if _indent(new[j]) == ind and new[j].strip()
                  and not new[j].lstrip().startswith("}")), None)
        if w is None or new[w].strip() != "while (true) {":
            continue
        semis = [j for j in range(w + 1, c) if new[j].strip() == ";"]
        if len(semis) != 1:
            continue
        new[semis[0]] = _indent(new[semis[0]]) + "break;"
        patches.append({"kind": "loop-exit-break", "line": semis[0] + 1,
                        "evidence": "javac: unreachable statement after an endless loop with one empty statement"})
    return (new, patches) if patches else None


_TWR_RE = re.compile(r"variable (\w+) used as a try-with-resources resource neither final nor effectively final")


def fix_twr_field_resource(lines: list[str], errors: list[dict], ctx=None):
    """`try (this.f; ...)` where the field is reassigned in the body -- javac: neither final nor
    effectively final. The original bound the field to a resource local; the local's name
    has no bytecode effect, its type is the field's declared type."""
    new = list(lines)
    patches = []
    for e in errors:
        m = _TWR_RE.match(e["message"])
        k = e["line"] - 1
        if not m or not 0 <= k < len(new):
            continue
        name = m.group(1)
        mm = re.match(r"^(\s*)this\.%s;\s*$" % re.escape(name), new[k])
        if not mm:
            continue
        decl = re.compile(r"^\s+(?:(?:private|protected|public|static|final|volatile|transient) )*"
                          r"(?P<type>[\w.$<>\[\]?, ]+?) %s\s*(?:=.*)?;\s*$" % re.escape(name))
        types = {d.group("type") for d in map(decl.match, new) if d and not d.group("type").startswith(("return", "this"))}
        if len(types) != 1:
            continue
        typ = types.pop()
        new[k] = f"{mm.group(1)}{typ} {name}_res = this.{name};"
        patches.append({"kind": "twr-field-resource", "line": e["line"], "field": name, "type": typ,
                        "evidence": "javac: " + e["message"]})
    return (new, patches) if patches else None


_PROTECTED_RE = re.compile(r"^[\w.$]+ has protected access in [\w.$]+$")


def fix_protected_member_import(lines: list[str], errors: list[dict], ctx=None):
    """`import pkg.Outer.Inner;` -- javac: Inner has protected access in Outer. A protected
    member class is not importable from another package, but a subclass sees it by its
    simple name as an inherited member; the original source had no such import."""
    drop = {}
    for e in errors:
        k = e["line"] - 1
        if _PROTECTED_RE.match(e["message"]) and 0 <= k < len(lines) and re.match(r"^import [\w.$]+;\s*$", lines[k]):
            drop[k] = e["message"]
    if not drop:
        return None
    new = [x for i, x in enumerate(lines) if i not in drop]
    patches = [{"kind": "protected-member-import", "line": k + 1, "import": lines[k].strip(),
                "evidence": "javac: " + msg} for k, msg in sorted(drop.items())]
    return new, patches


FIXERS: list[tuple[str, Callable]] = [
    ("pattern-binding-scope", fix_pattern_binding_scope),
    ("foreach-raw-cast", fix_foreach_raw_cast),
    ("boolean-declared-int", fix_boolean_declared_int),
    ("instanceof-generic-raw", fix_instanceof_generic_raw),
    ("switch-group-scope", fix_switch_group_scope),
    ("catch-parameter-name", fix_catch_parameter_name),
    ("protected-member-import", fix_protected_member_import),
    ("inner-ctor-outer-arg", fix_inner_ctor_outer_arg),
    ("ambiguous-overload-cast", fix_ambiguous_overload_cast),
    ("switch-yield-statement", fix_switch_yield_statement),
    ("loop-exit-break", fix_loop_exit_break),
    ("twr-field-resource", fix_twr_field_resource),
]


def patch_source(original: str, compile_fn: Callable[[str], str], fixers=None, max_rounds: int = MAX_ROUNDS,
                 ctx: Optional[dict] = None) -> dict:
    """Apply fixers driven by javac feedback. `compile_fn(text) -> ''` on success, else stderr.
    `ctx` carries shipped-bytecode evidence for the fixers that need it: {"methodrefs": set of
    (owner, name, descriptor)} (see parse_methodrefs).
    Returns {text, patches, compiles, residual_errors, rounds}."""
    fixers = list(FIXERS if fixers is None else fixers)
    text = original
    err = compile_fn(text)
    patches: list[dict] = []
    banned: set[str] = set()
    rounds = 0
    while err and rounds < max_rounds:
        errors = parse_javac_errors(err)
        applied = False
        for name, fn in fixers:
            if name in banned:
                continue
            lines = text.split("\n")
            got = fn(lines, errors, ctx)
            if got is None:
                continue
            new_text = "\n".join(got[0])
            new_err = compile_fn(new_text)
            if new_err and _error_count(new_err) >= len(errors):
                banned.add(name)
                continue
            text, err = new_text, new_err
            patches.extend(got[1])
            applied = True
            break
        rounds += 1
        if not applied:
            break
    residual = parse_javac_errors(err) if err else []
    return {"text": text, "patches": patches, "compiles": not err, "rounds": rounds,
            "residual_errors": [{"line": e["line"], "message": e["message"]} for e in residual],
            "residual_error_count": len(residual)}


# ---------------------------------------------------------------------------
# population + module driver
# ---------------------------------------------------------------------------

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
MANIFEST_NAME = "PATCHES.json"
MANIFEST_SCHEMA = 1
# ladder order, lowest first; a later rung wins a rank tie (see n5-fidelity.py _GRADE_RANK)
RUNGS = ("vineflower", "vineflower2", "vineflower2.canon", "vineflower2.patched", "vineflower2.spliced")
GRADE_RANK = {"no-compile": 0, "timeout": 0, "harness-error": 0, "compiles-mismatch": 1, "bytecode-only": 1,
              "roundtrip-canonical-t2": 2, "roundtrip-canonical": 3, "roundtrip-equivalent": 4, "roundtrip-exact": 5}
SOURCE_TREES = ("vineflower2p", "vineflower2")  # preferred first


def _load_fidelity():
    spec = importlib.util.spec_from_file_location("n5_fidelity_for_mech", TOOLS_DIR / "n5-fidelity.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def module_population(mod_dir: Path, patched_json: Optional[Path] = None) -> dict[str, dict]:
    """{fqcn: {best_grade, tree, source_grade}} for the module's best-of-ladder
    `bytecode-only` classes; `tree` is the source tree that is graded no-compile on the most
    advanced rung that recorded it (vineflower2p when it has the class, else vineflower2)
    and `source_grade` that attempt's grade. Uses the grader JSON only. `patched_json` replaces the
    module's live fidelity.vineflower2.patched.json (a regrade of the output tree rewrites it, so a
    rerun must read the pre-regrade copy)."""
    recs: dict[str, dict] = {}
    for r in RUNGS:
        p = mod_dir / f"fidelity.{r}.json"
        if r == "vineflower2.patched" and patched_json is not None:
            p = Path(patched_json)
        if p.is_file():
            try:
                recs[r] = json.loads(p.read_text())["classes"]
            except (json.JSONDecodeError, OSError, KeyError):
                pass
    names = set()
    for c in recs.values():
        names |= set(c)
    out = {}
    for f in names:
        best_grade, rung_recs = -1, {}
        for r in RUNGS:
            rec = recs.get(r, {}).get(f)
            if rec is None:
                continue
            rung_recs[r] = rec
            best_grade = max(best_grade, GRADE_RANK.get(rec["grade"], -1))
        # the class's best grade is the best over the rungs; only bytecode-only classes are targets
        best_names = [rec["grade"] for rec in rung_recs.values() if GRADE_RANK.get(rec["grade"], -1) == best_grade]
        if "bytecode-only" not in best_names or best_grade != GRADE_RANK["bytecode-only"]:
            continue
        tree = next((t for t in SOURCE_TREES if (mod_dir / t / f"{f}.java").is_file()), None)
        if tree is None:
            continue
        source_grade = None
        for r in reversed(RUNGS):
            if r in rung_recs:
                source_grade = next((g for n, g in rung_recs[r].get("attempted", []) if n == tree), None)
                if source_grade:
                    break
        out[f] = {"tree": tree, "source_grade": source_grade}
    return out


def make_compile_fn(fid, classpath: str, javac_bin: str, tool_server: bool, class_short: str):
    def compile_fn(text: str) -> str:
        with tempfile.TemporaryDirectory(prefix=f"n5mech-{class_short}-") as td:
            src = Path(td) / "src" / f"{class_short}.java"
            src.parent.mkdir()
            src.write_text(text, encoding="utf-8")
            args = ["--release", "25", "-g", "-implicit:none", "-proc:none", "-nowarn", "-Xmaxerrs", "100000",
                    "-d", str(Path(td) / "out")]
            if classpath:
                args += ["-cp", classpath]
            args.append(str(src))
            rc, _o, e = fid._run_jdk_tool("javac", javac_bin, args, 300, tool_server)
            return "" if rc == 0 else (e or "javac failed")
    return compile_fn


def patch_module(module: str, organized: Path, out_tree: str, *, fid, classpath: str, javac_bin: str,
                 tool_server: bool, javap_bin: Optional[str] = None, baseline_dir: Optional[Path] = None, only: Optional[set] = None, class_jobs: int = 1) -> dict:
    javap_bin = javap_bin or fid.DEFAULT_JAVAP
    mod_dir = organized / module
    baseline = Path(baseline_dir) / module / "fidelity.vineflower2.patched.json" if baseline_dir else None
    pop = module_population(mod_dir, patched_json=baseline)
    targets = {f: v for f, v in pop.items() if v["source_grade"] == "no-compile" and (only is None or f in only)}
    out_dir = mod_dir / out_tree
    records: dict[str, dict] = {}

    def one(f: str):
        v = targets[f]
        src = mod_dir / v["tree"] / f"{f}.java"
        original = src.read_text(encoding="utf-8")
        top = mod_dir / "extracted" / f"{f}.class"

        def methodrefs():
            files = [top] + sorted(top.parent.glob(top.stem + "$*.class")) if top.is_file() else []
            if not files:
                return set()
            rc, out, _e = fid._run_jdk_tool("javap", javap_bin, ["-v", "-p", *map(str, files)], 120, tool_server)
            return parse_methodrefs(out)

        res = patch_source(original, make_compile_fn(fid, classpath, javac_bin, tool_server, src.stem),
                           ctx={"methodrefs_fn": methodrefs})
        rec = {"source_tree": v["tree"], "original_sha256": sha256_text(original),
               "patched_sha256": sha256_text(res["text"]), "patches": res["patches"], "compiles": res["compiles"],
               "residual_error_count": res["residual_error_count"], "residual_errors": res["residual_errors"][:20],
               "rounds": res["rounds"]}
        return f, rec, res["text"]

    results = []
    if class_jobs > 1 and len(targets) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=class_jobs) as pool:
            results = list(pool.map(one, sorted(targets)))
    else:
        results = [one(f) for f in sorted(targets)]

    if out_dir.is_dir():
        shutil.rmtree(out_dir)
    carried = 0
    p_dir = mod_dir / "vineflower2p"
    if p_dir.is_dir():
        for p in p_dir.rglob("*.java"):
            dest = out_dir / p.relative_to(p_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
            carried += 1
    for f, rec, text in results:
        records[f] = rec
        if rec["patches"] and rec["compiles"]:
            dest = out_dir / f"{f}.java"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
    manifest = {"schema": MANIFEST_SCHEMA, "module": module, "tool": "tools/n5-patch-mechanical.py",
                "carried_from": "vineflower2p", "carried_files": carried, "classes": records}
    if records or carried:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def main(argv: Optional[list[str]] = None) -> int:
    fid = _load_fidelity()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modules")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--organized-dir", default=str(fid.DEFAULT_ORGANIZED_DIR))
    ap.add_argument("--out-tree", default="vineflower2m")
    ap.add_argument("--modules-dir", default=str(fid.DEFAULT_MODULES_DIR))
    ap.add_argument("--bin-ext-dir", default=str(fid.DEFAULT_BIN_EXT_DIR))
    ap.add_argument("--jre-dir", default=str(fid.DEFAULT_JRE_DIR))
    ap.add_argument("--bc-variant", choices=fid.BC_VARIANTS, default=fid.DEFAULT_BC_VARIANT)
    ap.add_argument("--classpath-cache-dir", default=None)
    ap.add_argument("--baseline-patched-dir", default=None,
                    help="<dir>/<module>/fidelity.vineflower2.patched.json: pre-regrade patched-rung JSONs "
                         "(population is read from these, so a rerun after an m-tree regrade is stable)")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--class-jobs", type=int, default=1)
    ap.add_argument("--tool-server", action="store_true")
    args = ap.parse_args(argv)
    organized = Path(args.organized_dir)
    if args.all:
        modules = [p.name for p in sorted(organized.iterdir())
                   if p.is_dir() and not p.name.startswith("_") and (p / "vineflower2").is_dir()]
    elif args.modules:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    else:
        ap.error("pass --modules a,b or --all")
    cache = Path(args.classpath_cache_dir) if args.classpath_cache_dir \
        else Path(tempfile.gettempdir()) / "n5-fidelity-classpath-cache"
    classpath = fid.build_classpath(cache, Path(args.modules_dir), Path(args.bin_ext_dir), bc_variant=args.bc_variant,
                                    jre_dir=Path(args.jre_dir) if args.jre_dir else None)
    failed = []

    def run(module: str):
        try:
            man = patch_module(module, organized, args.out_tree, fid=fid, classpath=classpath,
                               javac_bin=fid.DEFAULT_JAVAC, tool_server=args.tool_server, class_jobs=args.class_jobs,
                               baseline_dir=Path(args.baseline_patched_dir) if args.baseline_patched_dir else None)
            n_t = len(man["classes"])
            n_p = sum(1 for r in man["classes"].values() if r["patches"])
            n_c = sum(1 for r in man["classes"].values() if r["compiles"])
            print(f"[{module}] targets {n_t} patched {n_p} now-compiling {n_c}", file=sys.stderr, flush=True)
        except Exception as exc:  # noqa: BLE001 -- one module must not abort the batch
            print(f"[{module}] FAILED: {exc!r}", file=sys.stderr, flush=True)
            failed.append(module)

    if args.jobs > 1 and len(modules) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            list(pool.map(run, modules))
    else:
        for m in modules:
            run(m)
    fid.shutdown_tool_servers()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
