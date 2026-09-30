"""n5_source_hypotheses.py -- source-level hypotheses about decompiler defects (C3d).

Each function maps a decompiled source text to a variant text that is equivalent Java when its
premise holds. None is trusted: tools/n5-splice-methods.py recompiles the variant and keeps one of
its methods only when that method's Code equals the shipped one (exact/allowlist/canonical, the
grader's own comparison), so a hypothesis that is wrong for a site is simply never used there.
A hypothesis therefore only has to be cheap, deterministic and semantics-preserving.
"""
from __future__ import annotations

import re
from typing import Callable

_OPS = r"(?:>>>|>>|<<|[+\-*/%&|^])"
# an array element with side-effect-free indices (no call, no ++/--, no assignment)
_ELEM = r"[\w.]+(?:\[(?:(?!\+\+|--)[^\[\]=;(){}])+\])+"
_CAST_FORM = re.compile(
    r"^(?P<ind>[ \t]*)(?P<lhs>%s) = \((?:byte|short|char|int|long)\)\((?P=lhs) (?P<op>%s) (?P<rhs>[^;]+?)\);[ \t]*$"
    % (_ELEM, _OPS), re.M)
_PLAIN_FORM = re.compile(
    r"^(?P<ind>[ \t]*)(?P<lhs>%s) = (?P=lhs) (?P<op>%s) (?P<rhs>[^;]+?);[ \t]*$" % (_ELEM, _OPS), re.M)
_BINARY_AT_TOP = re.compile(r" (?:[-+*/%&|^<>=!?]|instanceof|&&|\|\|)")


def _single_operand(rhs: str) -> bool:
    """True when `rhs` has no binary/conditional operator outside brackets and parentheses, so
    `L = L op rhs` and `L op= rhs` group identically."""
    depth = 0
    out = []
    for ch in rhs:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif depth == 0:
            out.append(ch)
        if depth < 0:
            return False
    return depth == 0 and not _BINARY_AT_TOP.search("".join(out))


def compound_assign(text: str) -> str:
    """`a[i] = (byte)(a[i] | 4);` / `a[i] = a[i] + 1;` -> `a[i] |= 4;` / `a[i] += 1;`.

    javac compiles `a[i] op= x` with one evaluation of `a` and `i` (dup2), while the expanded
    statement evaluates them twice; the decompiler prints the expanded form for array elements.
    Only side-effect-free element expressions and a single-operand right side are rewritten."""
    def sub(m: re.Match) -> str:
        if not _single_operand(m.group("rhs")):
            return m.group(0)
        return f"{m.group('ind')}{m.group('lhs')} {m.group('op')}= {m.group('rhs')};"
    return _PLAIN_FORM.sub(sub, _CAST_FORM.sub(sub, text))


_ARRAY_INIT = re.compile(
    r"^(?P<ind>[ \t]*)(?P<final>final )?(?P<type>[\w.]+)\[\] (?P<name>\w+) = new (?P=type)\[\]\{(?P<body>[^\n]*)\};[ \t]*$",
    re.M)


def _split_elements(body: str):
    """Top-level comma split of an array-initializer body; None when it is not safely splittable
    (nested initializer, generic arguments, unbalanced text)."""
    if "{" in body or "<" in body:
        return None
    parts, depth, cur, quote, i = [], 0, [], None, 0
    while i < len(body):
        ch = body[i]
        if quote:
            cur.append(ch)
            if ch == "\\" and i + 1 < len(body):
                cur.append(body[i + 1])
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch in "([":
            depth += 1
            cur.append(ch)
        elif ch in ")]":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    if quote or depth != 0:
        return None
    parts.append("".join(cur).strip())
    return parts if all(parts) else None


def _unfold(text: str, max_len: int) -> str:
    def sub(m: re.Match) -> str:
        parts = _split_elements(m.group("body"))
        if not parts or len(parts) > max_len:
            return m.group(0)
        ind, name = m.group("ind"), m.group("name")
        lines = [f"{ind}{m.group('final') or ''}{m.group('type')}[] {name} = new {m.group('type')}[{len(parts)}];"]
        lines += [f"{ind}{name}[{k}] = {e};" for k, e in enumerate(parts)]
        return "\n".join(lines)
    return _ARRAY_INIT.sub(sub, text)


def unfold_array_initializers(text: str) -> str:
    """`T[] a = new T[]{x, y};` -> `T[] a = new T[2]; a[0] = x; a[1] = y;` (local declarations).

    javac compiles an array initializer as newarray/dup/index/value/store per element, and the
    equivalent element assignments as newarray/astore/aload/index/value/store; the decompiler
    folds the second form into the first, so a method whose original source assigned the elements
    one by one only matches the unfolded text."""
    return _unfold(text, 64)


def unfold_single_element_arrays(text: str) -> str:
    """The one-element case of unfold_array_initializers (the usual `final boolean[] flag = new
    boolean[1]` capture holder), leaving longer initializers as the decompiler wrote them."""
    return _unfold(text, 1)


_PRIM_DECL = re.compile(r"\b(int|long|short|byte|char|float|double|boolean)((?:\[\])*)\s+(\w+)\s*(?=[=;,):])")
_REF_DECL = re.compile(r"\b[A-Z][\w.]*(?:<[^<>;=()]*>)?(?:\[\])*\s+(\w+)\s*(?=[=;,):])")


def _int_names(text: str) -> set[str]:
    """Names every declaration of which (parameter, local, field) is a plain `int`."""
    kinds: dict[str, set[str]] = {}
    for m in _PRIM_DECL.finditer(text):
        kinds.setdefault(m.group(3), set()).add(m.group(1) + m.group(2))
    for m in _REF_DECL.finditer(text):
        kinds.setdefault(m.group(1), set()).add("ref")
    return {n for n, k in kinds.items() if k == {"int"}}


_STEP_STMT = re.compile(r"^(?P<ind>[ \t]*)(?:(?P<a>\w+)(?P<op1>\+\+|--)|(?P<op2>\+\+|--)(?P<b>\w+)|"
                        r"(?P<c>\w+) (?P<op3>[+-])= (?P<n>-?\d+));[ \t]*$", re.M)
_STEP_FOR = re.compile(r"^(?P<head>[ \t]*for \(.*; )(?P<v>\w+)(?P<op>\+\+|--)(?P<tail>\) \{)[ \t]*$", re.M)
_ASSIGN_STEP = re.compile(r"^(?P<ind>[ \t]*)(?P<v>\w+) = (?P=v) (?P<op>[+-]) (?P<n>\d+);[ \t]*$", re.M)


def expand_iinc(text: str) -> str:
    """`i++;` / `--i;` / `i += 2;` / `for (...; i++)` on an int variable -> `i = i + 1;` ...

    javac emits `iinc` only for the increment forms; source written as `i = i + 1` compiles to
    iload/iconst/iadd/istore. The decompiler normalizes every form to the increment."""
    ints = _int_names(text)

    def stmt(m: re.Match) -> str:
        var = m.group("a") or m.group("b") or m.group("c")
        if var not in ints:
            return m.group(0)
        if m.group("c"):
            return f"{m.group('ind')}{var} = {var} {m.group('op3')} {m.group('n')};"
        op = m.group("op1") or m.group("op2")
        return f"{m.group('ind')}{var} = {var} {'+' if op == '++' else '-'} 1;"

    def loop(m: re.Match) -> str:
        if m.group("v") not in ints:
            return m.group(0)
        v = m.group("v")
        return f"{m.group('head')}{v} = {v} {'+' if m.group('op') == '++' else '-'} 1{m.group('tail')}"
    return _STEP_FOR.sub(loop, _STEP_STMT.sub(stmt, text))


def collapse_iinc(text: str) -> str:
    """`i = i + 2;` on an int variable -> `i += 2;` (the inverse of expand_iinc for statements)."""
    ints = _int_names(text)

    def sub(m: re.Match) -> str:
        if m.group("v") not in ints:
            return m.group(0)
        return f"{m.group('ind')}{m.group('v')} {m.group('op')}= {m.group('n')};"
    return _ASSIGN_STEP.sub(sub, text)


_INC_IN_STMT = re.compile(r"(?<![\w.])(?:(?P<pre>\+\+|--)(?P<a>[A-Za-z_]\w*)|(?P<b>[A-Za-z_]\w*)(?P<post>\+\+|--))(?![\w(])")
_PLAIN_STMT = re.compile(r"^(?P<ind>[ \t]*)(?P<body>[^\n{}]*;)[ \t]*$", re.M)


def lift_increments(text: str) -> str:
    """`x = a + ++i;` -> `i++; x = a + i;` and `out[i++] = v;` -> `out[i] = v; i++;` for int variables.

    The decompiler folds an increment statement into the neighbouring expression; javac compiles
    the folded form as iinc-inside-expression, the separate statement as a plain iinc. Only a
    single-line statement with no conditional evaluation (?:, &&, ||, lambda) in which the variable
    occurs exactly once is rewritten, so the evaluation order is unchanged."""
    ints = _int_names(text)

    def sub(m: re.Match) -> str:
        body = m.group("body")
        if re.match(r"\s*(?:if|while|for|switch|else|do|case|default|try|catch|synchronized)\b", body) \
                or re.search(r"\?|&&|\|\||->", body):
            return m.group(0)
        hits = list(_INC_IN_STMT.finditer(body))
        if len(hits) != 1:
            return m.group(0)
        h = hits[0]
        var = h.group("a") or h.group("b")
        if var not in ints or len(re.findall(r"(?<![\w.])%s(?!\w)" % re.escape(var), body)) != 1:
            return m.group(0)
        op = h.group("pre") or h.group("post")
        ind = m.group("ind")
        step = f"{ind}{var}{op};"
        new_body = body[:h.start()] + var + body[h.end():]
        if h.group("pre"):
            return f"{step}\n{ind}{new_body}"
        if re.match(r"\s*(?:return|throw)\b", body):
            return m.group(0)
        return f"{ind}{new_body}\n{step}"
    return _PLAIN_STMT.sub(sub, text)


_NN_CALL = "invokestatic // Method java/util/Objects.requireNonNull:(Ljava/lang/Object;)Ljava/lang/Object;"
_ALOAD = re.compile(r"^aload(?:_(\d)| (\d+))$")


def _strip_insn(line: str) -> str:
    return re.sub(r"^insn\d+:\s*", "", line)


def _param_slots(desc: str, static: bool) -> list[int]:
    """First JVM local slot of each parameter of a method descriptor."""
    slots, slot, i = [], 0 if static else 1, 1
    while desc[i] != ")":
        slots.append(slot)
        wide = desc[i] in "JD"
        while desc[i] == "[":
            i += 1
            wide = False
        if desc[i] == "L":
            i = desc.index(";", i)
        i += 1
        slot += 2 if wide else 1
    return slots


def _null_check_prologue(code: list[str]) -> list[int]:
    """Local slots checked by the leading `aload x; Objects.requireNonNull; pop` triples."""
    body = [_strip_insn(c) for c in code]
    slots = []
    i = 0
    while i + 2 < len(body) and body[i + 1] == _NN_CALL and body[i + 2] == "pop":
        m = _ALOAD.match(body[i])
        if not m:
            break
        slots.append(int(m.group(1) or m.group(2)))
        i += 3
    return slots


def restore_null_checks(text: str, ctx: dict) -> str:
    """Insert `java.util.Objects.requireNonNull(p);` at the start of a method whose shipped code
    begins with that call and whose recompiled code does not.

    Vineflower's remove-getclass drops every `Objects.requireNonNull(x);` statement (javac emits
    the same call for `x.new Inner()` and `x::m`, and the decompiler cannot tell them apart).
    `ctx`: {"methods": MethodSpans methods, "shipped"/"ours": {(name, desc): normalized code},
    "static": {(name, desc): bool}}. Constructors are skipped (`this(...)`/`super(...)` come first)."""
    edits = []
    for m in ctx["methods"]:
        key = (m["name"], m["desc"])
        if m["name"] == "<init>" or m["body_start"] < 0 or key not in ctx["shipped"] or key not in ctx["ours"]:
            continue
        wanted = _null_check_prologue(ctx["shipped"][key])
        if not wanted or _null_check_prologue(ctx["ours"][key]) == wanted:
            continue
        static = ctx["static"].get(key, False)
        by_slot = dict(zip(_param_slots(m["desc"], static), m["params"]))
        if any(sl not in by_slot for sl in wanted):
            continue
        open_brace = m["body_start"]
        line_start = text.rfind("\n", 0, open_brace) + 1
        indent = re.match(r"[ \t]*", text[line_start:]).group(0) + "  "
        edits.append((open_brace + 1, "".join(f"\n{indent}java.util.Objects.requireNonNull({by_slot[sl]});" for sl in wanted)))
    for at, add in sorted(edits, reverse=True):
        text = text[:at] + add + text[at:]
    return text


restore_null_checks.needs_context = True  # type: ignore[attr-defined]


# name -> hypothesis, in the order the splice tries them
HYPOTHESES: dict[str, Callable[..., str]] = {
    "compound-assign": compound_assign,
    "unfold-single-array": unfold_single_element_arrays,
    "unfold-arrays": unfold_array_initializers,
    "expand-iinc": expand_iinc,
    "collapse-iinc": collapse_iinc,
    "restore-null-checks": restore_null_checks,
    "lift-increments": lift_increments,
}
