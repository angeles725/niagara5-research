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


# name -> hypothesis, in the order the splice tries them
HYPOTHESES: dict[str, Callable[[str], str]] = {
    "compound-assign": compound_assign,
    "unfold-single-array": unfold_single_element_arrays,
    "unfold-arrays": unfold_array_initializers,
}
