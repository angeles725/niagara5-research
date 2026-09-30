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


def _compound_rewrites(text: str) -> list:
    def sub(m: re.Match) -> str:
        if not _single_operand(m.group("rhs")):
            return m.group(0)
        return f"{m.group('ind')}{m.group('lhs')} {m.group('op')}= {m.group('rhs')};"
    return [(_CAST_FORM, sub), (_PLAIN_FORM, sub)]


def _apply_all(text: str, rewrites: list) -> str:
    for pattern, rewrite in rewrites:
        text = pattern.sub(rewrite, text)
    return text


def compound_assign(text: str) -> str:
    """`a[i] = (byte)(a[i] | 4);` / `a[i] = a[i] + 1;` -> `a[i] |= 4;` / `a[i] += 1;`.

    javac compiles `a[i] op= x` with one evaluation of `a` and `i` (dup2), while the expanded
    statement evaluates them twice; the decompiler prints the expanded form for array elements.
    Only side-effect-free element expressions and a single-operand right side are rewritten."""
    return _apply_all(text, _compound_rewrites(text))


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


def _unfold_rewrites(text: str, max_len: int = 64) -> list:
    def sub(m: re.Match) -> str:
        parts = _split_elements(m.group("body"))
        if not parts or len(parts) > max_len:
            return m.group(0)
        ind, name = m.group("ind"), m.group("name")
        lines = [f"{ind}{m.group('final') or ''}{m.group('type')}[] {name} = new {m.group('type')}[{len(parts)}];"]
        lines += [f"{ind}{name}[{k}] = {e};" for k, e in enumerate(parts)]
        return "\n".join(lines)
    return [(_ARRAY_INIT, sub)]


def _unfold(text: str, max_len: int) -> str:
    return _apply_all(text, _unfold_rewrites(text, max_len))


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


def _expand_rewrites(text: str) -> list:
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
    return [(_STEP_STMT, stmt), (_STEP_FOR, loop)]


def expand_iinc(text: str) -> str:
    """`i++;` / `--i;` / `i += 2;` / `for (...; i++)` on an int variable -> `i = i + 1;` ...

    javac emits `iinc` only for the increment forms; source written as `i = i + 1` compiles to
    iload/iconst/iadd/istore. The decompiler normalizes every form to the increment."""
    return _apply_all(text, _expand_rewrites(text))


def _collapse_rewrites(text: str) -> list:
    ints = _int_names(text)

    def sub(m: re.Match) -> str:
        if m.group("v") not in ints:
            return m.group(0)
        return f"{m.group('ind')}{m.group('v')} {m.group('op')}= {m.group('n')};"
    return [(_ASSIGN_STEP, sub)]


def collapse_iinc(text: str) -> str:
    """`i = i + 2;` on an int variable -> `i += 2;` (the inverse of expand_iinc for statements)."""
    return _apply_all(text, _collapse_rewrites(text))


_INC_IN_STMT = re.compile(r"(?<![\w.])(?:(?P<pre>\+\+|--)(?P<a>[A-Za-z_]\w*)|(?P<b>[A-Za-z_]\w*)(?P<post>\+\+|--))(?![\w(])")
_PLAIN_STMT = re.compile(r"^(?P<ind>[ \t]*)(?P<body>[^\n{}]*;)[ \t]*$", re.M)


def _lift_rewrites(text: str) -> list:
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
        if new_body.strip() == var + ";":  # the statement is the increment itself
            return m.group(0)
        if h.group("pre"):
            return f"{step}\n{ind}{new_body}"
        if re.match(r"\s*(?:return|throw)\b", body):
            return m.group(0)
        return f"{ind}{new_body}\n{step}"
    return [(_PLAIN_STMT, sub)]


def lift_increments(text: str) -> str:
    """`x = a + ++i;` -> `i++; x = a + i;` and `out[i++] = v;` -> `out[i] = v; i++;` for int variables.

    The decompiler folds an increment statement into the neighbouring expression; javac compiles
    the folded form as iinc-inside-expression, the separate statement as a plain iinc. Only a
    single-line statement with no conditional evaluation (?:, &&, ||, lambda) in which the variable
    occurs exactly once is rewritten, so the evaluation order is unchanged."""
    return _apply_all(text, _lift_rewrites(text))


_PRIMS = {"B": "byte", "C": "char", "D": "double", "F": "float", "I": "int", "J": "long", "S": "short", "Z": "boolean",
          "V": "void"}


def _sig_type(sig: str, i: int = 0) -> tuple[str, int]:
    """Java source text of the JVM type/generic signature starting at sig[i], and the next index."""
    ch = sig[i]
    if ch in _PRIMS:
        return _PRIMS[ch], i + 1
    if ch == "[":
        inner, j = _sig_type(sig, i + 1)
        return inner + "[]", j
    if ch == "T":
        end = sig.index(";", i)
        return sig[i + 1:end], end + 1
    if ch == "*":
        return "?", i + 1
    if ch in "+-":
        inner, j = _sig_type(sig, i + 1)
        return ("? extends " if ch == "+" else "? super ") + inner, j
    assert ch == "L", sig
    out, j = [], i + 1
    while True:
        k = j
        while sig[k] not in ";<.":
            k += 1
        out.append(sig[j:k].replace("/", ".").replace("$", "."))
        j = k
        if sig[j] == "<":
            args, j = [], j + 1
            while sig[j] != ">":
                a, j = _sig_type(sig, j)
                args.append(a)
            out.append("<" + ", ".join(args) + ">")
            j += 1
        if sig[j] == ";":
            return "".join(out), j + 1
        out.append(".")  # inner class of a parameterized type
        j += 1


_LVT_ROW = re.compile(r"^\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s*$")
_MEMBER_MODS = {"public", "private", "protected", "static", "final", "synchronized", "native", "abstract",
                "strictfp", "default"}


def lvt_types(javap_text: str) -> dict:
    """{(method name, descriptor): {local name: Java type text or None}} from a `javap -v -p` listing.
    The generic signature (LocalVariableTypeTable) wins over the erased descriptor; a name declared
    with different types in one method maps to None (ambiguous)."""
    out: dict = {}
    key = None
    kind = None
    seen: dict = {}
    types: dict = {}
    lines = javap_text.splitlines()

    def flush():
        if key is not None:
            merged = {}
            for (slot, start, name), t in types.items():
                merged.setdefault(name, set()).add(t)
            out[key] = {n: (next(iter(ts)) if len(ts) == 1 else None) for n, ts in merged.items()}
    for n, line in enumerate(lines):
        if re.match(r"^  \S", line) and line.rstrip().endswith(";") and n + 1 < len(lines) \
                and lines[n + 1].strip().startswith("descriptor:"):
            flush()
            head = line.strip().rstrip(";")
            desc = lines[n + 1].split("descriptor:", 1)[1].strip()
            if head == "static {}":
                name = "<clinit>"
            else:
                toks = [t for t in head.split("(", 1)[0].split() if t not in _MEMBER_MODS]
                name = "<init>" if len(toks) == 1 else toks[-1]
            key, kind, types = (name, desc), None, {}
            continue
        st = line.strip()
        if st.startswith("LocalVariableTable:"):
            kind = "d"
        elif st.startswith("LocalVariableTypeTable:"):
            kind = "s"
        elif kind and (m := _LVT_ROW.match(line)):
            slot_key = (int(m.group(3)), int(m.group(1)), m.group(4))
            if kind == "d":
                if slot_key not in types:
                    types[slot_key] = None if m.group(5) == "?" else _sig_type(m.group(5))[0]
            else:
                types[slot_key] = _sig_type(m.group(5))[0]
        elif kind and st and not st.startswith("Start"):
            kind = None
    flush()
    return out


_LOCAL_DECL = re.compile(r"^(?P<ind>[ \t]*)(?P<final>final )?(?P<type>var|[A-Za-z_][\w.]*(?:<[^;=()]*>)?(?:\[\])*) "
                         r"(?P<name>[A-Za-z_]\w*)(?P<rest> = [^\n]*| ?;)$", re.M)
_INTERSECTION = re.compile(r"^ = \((?P<a>[\w.<>?, ]+) & (?P<b>[\w.<>?, ]+)\)")


def _erased_simple(t: str) -> str:
    base = re.sub(r"<.*>", "", t)
    dims = base.count("[]")
    return base.replace("[]", "").rsplit(".", 1)[-1] + "[]" * dims


def declared_local_types(text: str, ctx: dict) -> str:
    """Give the locals of the currently mismatching methods the type of the shipped LocalVariableTable.

    The decompiler prints `var x = (A & B)expr` for a variable whose class it cannot pin down and
    sometimes a narrower/wider declared type than the original; the type changes which casts javac
    emits. `ctx`: {"methods": MethodSpans methods, "lvt": lvt_types(shipped), "mismatched": {(name, desc)}}."""
    edits = []
    for m in ctx["methods"]:
        key = (m["name"], m["desc"])
        types = ctx["lvt"].get(key)
        if key not in ctx["mismatched"] or not types or m["body_start"] < 0:
            continue
        seg_start, seg_end = m["body_start"], m["end"]
        for d in _LOCAL_DECL.finditer(text, seg_start, seg_end):
            want = types.get(d.group("name"))
            have = d.group("type")
            if not want or want in ("this",):
                continue
            rest = d.group("rest")
            if have == "var":
                rest = _INTERSECTION.sub(lambda i: f" = ({want})", rest, count=1)
            elif _erased_simple(have) == _erased_simple(want):
                continue
            edits.append((d.start(), d.end(), f"{d.group('ind')}{d.group('final') or ''}{want} {d.group('name')}{rest}"))
    for s0, e0, new in sorted(edits, reverse=True):
        text = text[:s0] + new + text[e0:]
    return text


declared_local_types.needs_context = True  # type: ignore[attr-defined]


def _match_brace(text: str, open_at: int) -> int:
    """Index of the `}` matching the `{` at open_at, skipping string/char literals and comments
    (-1 when unbalanced)."""
    depth, i, n = 0, open_at, len(text)
    while i < n:
        ch = text[i]
        if ch in "\"'":
            q = ch
            if text.startswith('\"\"\"', i):
                i = text.find('\"\"\"', i + 3)
                if i < 0:
                    return -1
                i += 3
                continue
            i += 1
            while i < n and text[i] != q:
                i += 2 if text[i] == "\\" else 1
        elif text.startswith("//", i):
            i = text.find("\n", i)
            if i < 0:
                return -1
        elif text.startswith("/*", i):
            i = text.find("*/", i)
            if i < 0:
                return -1
            i += 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


_TOP_OPS = re.compile(r" (?:&&|\|\||\?|:) ")
_CMP = re.compile(r"^(?P<l>.+?) (?P<op>==|!=|<=|>=|<|>) (?P<r>.+)$")
_INV = {"==": "!=", "!=": "==", "<": ">=", ">=": "<", ">": "<=", "<=": ">"}


def _top_level(text: str) -> str:
    """`text` with everything inside brackets, parentheses and string literals blanked out."""
    out, depth, quote = [], 0, None
    for ch in text:
        if quote:
            if ch == quote:
                quote = None
            out.append("\x01")
        elif ch in "\"'":
            quote = ch
            out.append("\x01")
        elif ch in "([{":
            depth += 1
            out.append("\x01")
        elif ch in ")]}":
            depth -= 1
            out.append("\x01")
        else:
            out.append(ch if depth == 0 else "\x01")
    return "".join(out)


def _negate(cond: str) -> str:
    """The logical negation of a condition, undoing a leading `!` or flipping a comparison when the
    condition has no top-level && / || / ?:, else `!(cond)`."""
    top = _top_level(cond)
    if not _TOP_OPS.search(top):
        if cond.startswith("!") and not re.search(r" (?:==|!=|<=|>=|<|>) ", top):
            rest = cond[1:]
            if rest.startswith("(") and set(_top_level(rest)) == {"\x01"}:
                return rest[1:-1]
            if not re.search(r"\s", top[1:]):
                return rest
        m = _CMP.match(cond)
        if m and not top.startswith("!") and len(re.findall(r" (?:==|!=|<=|>=|<|>) ", top)) == 1:
            return f"{m.group('l')} {_INV[m.group('op')]} {m.group('r')}"
    if not cond.startswith("!") and not re.search(r"\s", top):
        return f"!{cond}"  # a plain name, field access or call
    return f"!({cond})"


_IF_HEAD = re.compile(r"^[ \t]*if \((?P<cond>.*)\) \{$", re.M)


class _SwapIfElse:
    """Site hypothesis: exchange the branches of an `if (c) {A} else {B}` and negate `c`."""

    @staticmethod
    def _parse(text: str):
        for m in _IF_HEAD.finditer(text):
            open1 = m.end() - 1
            close1 = _match_brace(text, open1)
            if close1 < 0 or not text.startswith("} else {", close1):
                continue
            open2 = close1 + len("} else ") 
            close2 = _match_brace(text, open2)
            if close2 < 0:
                continue
            yield (m.start("cond"), m.end("cond")), open1, close1, open2, close2

    def sites(self, text: str) -> list:
        return [cond for cond, *_ in self._parse(text)]

    def apply(self, text: str, site: tuple) -> str:
        for cond, open1, close1, open2, close2 in self._parse(text):
            if cond == tuple(site):
                a, b = text[open1 + 1:close1], text[open2 + 1:close2]
                return (text[:cond[0]] + _negate(text[cond[0]:cond[1]]) + text[cond[1]:open1 + 1] + b
                        + text[close1:open2 + 1] + a + text[close2:])
        return text


swap_if_else = _SwapIfElse()


def _leaves(block_lines: list[str]) -> bool:
    """True when the last statement of a block leaves it (return/throw/break/continue)."""
    for line in reversed(block_lines):
        if line.strip():
            return bool(re.match(r"\s*(?:return|throw|break|continue)\b", line))
    return False


def _ends_a_block(text: str, after: int, indent: int) -> bool:
    """True when the next non-blank line after `after` closes an enclosing block (a `}` indented less
    than `indent`), i.e. the statement that ended at `after` is the last one of its block."""
    for line in text[after:].split("\n")[1:]:
        if line.strip():
            return line.strip().startswith("}") and len(line) - len(line.lstrip()) < indent
    return False


def _dedent(lines: list[str]) -> list[str]:
    return [l[3:] if l.startswith("   ") else l for l in lines]


class _EarlyReturn:
    """Site hypotheses at the end of a block: `early-return-else` turns `if (c) {A} else {B}` into
    `if (c) {A return;} B`, `guard-return` turns `if (c) {A}` into `if (!c) {return;} A`."""

    def __init__(self, with_else: bool, leave: str = "return;"):
        self.with_else = with_else
        self.leave = leave  # `return;` (end of a void method) or `continue;` (end of a loop body)

    def _parse(self, text: str):
        for m in _IF_HEAD.finditer(text):
            open1 = m.end() - 1
            close1 = _match_brace(text, open1)
            if close1 < 0:
                continue
            ind = len(m.group(0)) - len(m.group(0).lstrip())
            a_lines = text[open1 + 1:close1].split("\n")[1:-1]
            if self.with_else:
                if not text.startswith("} else {", close1):
                    continue
                open2 = close1 + len("} else ")
                close2 = _match_brace(text, open2)
                if close2 < 0 or not _ends_a_block(text, close2, ind) or _leaves(a_lines):
                    continue
                yield (m.start(), close2 + 1), m, open1, close1, open2, close2, ind
            else:
                if text.startswith("} else", close1) or not _ends_a_block(text, close1, ind):
                    continue
                yield (m.start(), close1 + 1), m, open1, close1, None, None, ind

    def sites(self, text: str) -> list:
        return [span for span, *_ in self._parse(text)]

    def apply(self, text: str, site: tuple) -> str:
        for span, m, open1, close1, open2, close2, ind in self._parse(text):
            if span != tuple(site):
                continue
            pad = " " * ind
            a_lines = text[open1 + 1:close1].split("\n")[1:-1]
            head = text[:m.start("cond")]
            if self.with_else:
                b_lines = _dedent(text[open2 + 1:close2].split("\n")[1:-1])
                new = (text[:open1 + 1] + "\n" + "\n".join(a_lines + [pad + "   " + self.leave]) + "\n" + pad + "}\n"
                       + "\n".join(b_lines) + text[close2 + 1:])
                return new
            new = (head + _negate(m.group("cond")) + text[m.end("cond"):open1 + 1] + "\n" + pad + "   " + self.leave + "\n" + pad
                   + "}\n" + "\n".join(_dedent(a_lines)) + text[close1 + 1:])
            return new
        return text


early_return_else = _EarlyReturn(True)
guard_return = _EarlyReturn(False)
guard_continue = _EarlyReturn(False, "continue;")


_RETURN_LINE = re.compile(r"^(?P<ind>[ \t]*)return (?P<expr>[^;\n]+);$", re.M)
_BOOL_OPS = re.compile(r" (?:==|!=|<=|>=|<|>|&&|\|\||instanceof) ")


def _unparen(expr: str) -> str:
    """`expr` without one pair of parentheses that enclose all of it."""
    if expr.startswith("(") and expr.endswith(")") and set(_top_level(expr)) == {"\x01"}:
        return expr[1:-1]
    return expr


def _split_ternary(expr: str):
    """(condition, then, else) of an expression whose top level is one `c ? a : b`, else None."""
    top = _top_level(expr)
    q = top.find(" ? ")
    if q < 0:
        return None
    depth, i = 1, q + 3
    while i < len(top):
        if top.startswith(" ? ", i):
            depth += 1
            i += 3
        elif top.startswith(" : ", i):
            depth -= 1
            if depth == 0:
                return expr[:q], _unparen(expr[q + 3:i]), _unparen(expr[i + 3:])
            i += 3
        else:
            i += 1
    return None


def _statement_position(text: str, at: int) -> bool:
    """True when the line at `at` starts a statement: the previous non-blank line ends a block, a
    statement or a case label -- not a braceless `if (c)` / `else` header."""
    for line in reversed(text[:at].split("\n")[:-1]):
        if line.strip():
            return line.rstrip().endswith(("{", "}", ";", ":"))
    return True


class _ReturnRewrite:
    """Site hypotheses on a single-line `return <expr>;`. javac compiles `return c ? a : b;` and
    `return <boolean expression>;` with a jump to one shared `*return`; the shipped code often has
    a `*return` per branch (`if (c) return a; return b;`), which the decompiler folds back into the
    expression form. Each rewrite is one level; the splice keeps it only when the bytecode agrees."""

    def __init__(self, kind: str):
        self.kind = kind

    def _matches(self, text: str):
        for m in _RETURN_LINE.finditer(text):
            expr = m.group("expr")
            if not _statement_position(text, m.start()):
                continue
            if self.kind == "ternary":
                if _split_ternary(expr) is not None:
                    yield m
            else:
                top = _top_level(expr)
                if " ? " not in top and (_BOOL_OPS.search(top) or top.startswith("!")):
                    yield m

    def sites(self, text: str) -> list:
        return [(m.start(), m.end()) for m in self._matches(text)]

    def apply(self, text: str, site: tuple) -> str:
        for m in self._matches(text):
            if (m.start(), m.end()) != tuple(site):
                continue
            ind, expr = m.group("ind"), m.group("expr")
            if self.kind == "ternary":
                cond, a, b = _split_ternary(expr)
                new = f"{ind}if ({cond}) {{\n{ind}   return {a};\n{ind}}}\n\n{ind}return {b};"
            else:
                new = f"{ind}if ({expr}) {{\n{ind}   return true;\n{ind}}}\n\n{ind}return false;"
            return text[:m.start()] + new + text[m.end():]
        return text


split_return_ternary = _ReturnRewrite("ternary")
split_return_boolean = _ReturnRewrite("boolean")


_PLAIN_VALUE = re.compile(r"^(?:[\w.$]+|\"[^\"]*\")$")
_TEMP_RETURN = re.compile(
    r"^(?P<ind>[ \t]*)(?:final )?[\w.$<>\[\]?, ]+ (?P<name>\w+) = (?P<expr>[^;\n]+);\n(?P=ind)return (?P=name);$", re.M)


class _ReturnTemp:
    """Site hypotheses on the temporary of `T t = <expr>; return t;`. javac keeps the store/load pair
    for it (the shipped code has it when the original source had the local); the decompiler folds it
    into `return <expr>;`. `introduce` adds the local, `inline` removes one the decompiler kept."""

    def __init__(self, introduce: bool):
        self.introduce = introduce

    def _matches(self, text: str):
        if self.introduce:
            for m in _RETURN_LINE.finditer(text):
                expr = m.group("expr")
                if _PLAIN_VALUE.match(expr) or " -> " in expr or not _statement_position(text, m.start()):
                    continue
                yield m
        else:
            yield from _TEMP_RETURN.finditer(text)

    def sites(self, text: str) -> list:
        return [(m.start(), m.end()) for m in self._matches(text)]

    def apply(self, text: str, site: tuple) -> str:
        for m in self._matches(text):
            if (m.start(), m.end()) != tuple(site):
                continue
            ind, expr = m.group("ind"), m.group("expr")
            new = (f"{ind}var retTmp = {expr};\n{ind}return retTmp;" if self.introduce
                   else f"{ind}return {expr};")
            return text[:m.start()] + new + text[m.end():]
        return text


introduce_return_temp = _ReturnTemp(True)
inline_return_temp = _ReturnTemp(False)


_DECL_LINE = re.compile(
    r"^(?P<ind>[ \t]*)(?:final )?(?P<type>[A-Za-z_][\w.$]*(?:<[^;=()]*>)?(?:\[\])*) (?P<name>\w+)(?P<init> = [^\n]*)?;$", re.M)
_NOT_A_TYPE = {"return", "throw", "break", "continue", "new", "else", "case", "yield", "assert", "goto", "package",
               "import"}
HOIST_WINDOW = 4  # previous declarations of the block a declaration may be moved above


class _HoistDeclaration:
    """Site hypothesis: move an uninitialized local declaration (`T x;`) above one of the previous
    declarations of its block. javac numbers locals in declaration order, so this permutes slots;
    an initialized declaration is never moved (that would reorder its side effects)."""

    @staticmethod
    def _decls(text: str):
        for m in _DECL_LINE.finditer(text):
            if m.group("type") not in _NOT_A_TYPE:
                yield m

    def _found(self, text: str):
        decls = list(self._decls(text))
        for i, d in enumerate(decls):
            if d.group("init") is not None:
                continue
            ind = d.group("ind")
            reach = []
            for prev in reversed(decls[:i]):
                between = text[prev.start():d.start()].split("\n")
                if any(l.strip() and len(l) - len(l.lstrip()) < len(ind) for l in between[1:]):
                    break  # left the block
                if prev.group("ind") == ind:
                    reach.append(prev)
            for prev in reach[:HOIST_WINDOW]:
                yield d, prev

    def sites(self, text: str) -> list:
        return [(d.start(), prev.start()) for d, prev in self._found(text)]

    def apply(self, text: str, site: tuple) -> str:
        for d, prev in self._found(text):
            if (d.start(), prev.start()) != tuple(site):
                continue
            line = d.group(0)
            without = text[:d.start()] + text[d.end() + 1:]
            return without[:prev.start()] + line + "\n" + without[prev.start():]
        return text


hoist_declaration = _HoistDeclaration()


_FOR_DECL = re.compile(
    r"^(?P<ind>[ \t]*)for \((?P<type>[A-Za-z_][\w.$]*(?:<[^;=()]*>)?(?:\[\])*) (?P<name>\w+) = (?P<init>[^;\n]+);", re.M)


class _HoistForVariable:
    """Site hypothesis: `for (T i = e; ...)` -> `T i;` + `for (i = e; ...)`. A loop variable declared
    before the loop keeps its slot after it, the `for` scope frees it for the next local."""

    def _matches(self, text: str):
        for m in _FOR_DECL.finditer(text):
            if "," not in _top_level(m.group("init")):
                yield m

    def sites(self, text: str) -> list:
        return [(m.start(), m.end()) for m in self._matches(text)]

    def apply(self, text: str, site: tuple) -> str:
        for m in self._matches(text):
            if (m.start(), m.end()) == tuple(site):
                ind = m.group("ind")
                new = f"{ind}{m.group('type')} {m.group('name')};\n{ind}for ({m.group('name')} = {m.group('init')};"
                return text[:m.start()] + new + text[m.end():]
        return text


hoist_for_var = _HoistForVariable()


class _UnguardElse:
    """Site hypothesis: `if (g) { L } REST` (L leaves) -> `if (!g) { REST } else { L }`. javac puts the
    else branch last, so the shipped `if (c) { REST } else { throw }` differs from the decompiler's
    early-throw guard."""

    def _parse(self, text: str):
        for m in _IF_HEAD.finditer(text):
            open1 = m.end() - 1
            close1 = _match_brace(text, open1)
            if close1 < 0 or text.startswith("} else", close1):
                continue
            ind = len(m.group(0)) - len(m.group(0).lstrip())
            a_lines = text[open1 + 1:close1].split("\n")[1:-1]
            if not _leaves(a_lines):
                continue
            rest_end, pos = close1 + 1, close1 + 1
            for line in text[close1 + 1:].split("\n")[1:]:
                pos += len(line) + 1
                if line.strip() and len(line) - len(line.lstrip()) < ind:
                    break
                rest_end = pos
            rest = text[close1 + 1:rest_end].strip("\n")
            if not rest.strip():
                continue
            yield (m.start(), close1 + 1), m, open1, close1, close1 + 1, rest_end, rest.split("\n"), a_lines, ind

    def sites(self, text: str) -> list:
        return [span for span, *_ in self._parse(text)]

    def apply(self, text: str, site: tuple) -> str:
        for span, m, open1, close1, rest_from, rest_end, rest, a_lines, ind in self._parse(text):
            if span != tuple(site):
                continue
            pad = " " * ind
            moved = ["   " + l if l.strip() else l for l in rest]
            new = (text[:m.start("cond")] + _negate(m.group("cond")) + text[m.end("cond"):open1 + 1] + "\n"
                   + "\n".join(moved) + "\n" + pad + "} else {\n" + "\n".join(a_lines) + "\n" + pad + "}\n")
            return new + text[rest_end:]
        return text


unguard_else = _UnguardElse()


_RETURN_OR_THROW = re.compile(r"^\s*(?:return\b[^;]*|throw\b[^;]*);$")
_RETURN_STMT = re.compile(r"^(?P<ind>[ \t]*)return (?P<expr>[^;\n]+);$")


def _block_rest(text: str, after: int, ind: int):
    """(end offset, text) of the statements that follow the statement ending at `after`, up to the
    closing brace of the enclosing block (a line indented less than `ind`)."""
    rest_end, pos = after, after
    for line in text[after:].split("\n")[1:]:
        pos += len(line) + 1
        if line.strip() and len(line) - len(line.lstrip()) < ind:
            break
        rest_end = pos
    return rest_end, text[after:rest_end].strip("\n")


class _InvertGuardReturn:
    """Site hypothesis: `if (c) { A return y; } return x;` -> `if (!c) { return x; } A return y;`. javac
    emits the early `return x`; the decompiler folds it into the trailing return."""

    def _parse(self, text: str):
        for m in _IF_HEAD.finditer(text):
            open1 = m.end() - 1
            close1 = _match_brace(text, open1)
            if close1 < 0 or text.startswith("} else", close1):
                continue
            ind = len(m.group(0)) - len(m.group(0).lstrip())
            a_lines = text[open1 + 1:close1].split("\n")[1:-1]
            if not a_lines or not _RETURN_OR_THROW.match(next((l for l in reversed(a_lines) if l.strip()), "")):
                continue
            rest_end, rest = _block_rest(text, close1 + 1, ind)
            lines = [l for l in rest.split("\n") if l.strip()]
            ret = _RETURN_STMT.match(lines[0]) if len(lines) == 1 else None
            if ret is None or len(ret.group("ind")) != ind:
                continue
            yield (m.start(), rest_end), m, open1, close1, rest_end, ret.group("expr"), a_lines, ind

    def sites(self, text: str) -> list:
        return [span for span, *_ in self._parse(text)]

    def apply(self, text: str, site: tuple) -> str:
        for span, m, open1, close1, rest_end, expr, a_lines, ind in self._parse(text):
            if span != tuple(site):
                continue
            pad = " " * ind
            new = (text[:m.start("cond")] + _negate(m.group("cond")) + text[m.end("cond"):open1 + 1] + "\n"
                   + pad + "   return " + expr + ";\n" + pad + "}\n" + "\n".join(_dedent(a_lines)) + "\n")
            return new + text[rest_end:].lstrip("\n") if text[rest_end:].strip() else new
        return text


invert_guard_return = _InvertGuardReturn()

_INSTANCEOF_COND = re.compile(r"^(?P<neg>!\()?(?P<x>[A-Za-z_]\w*) instanceof (?P<t>[\w.$]+(?:<[^()]*>)?)\)?$")


class _InstanceofBinding:
    """Site hypothesis: `if (x instanceof T) { .. (T)x .. }` -> `if (x instanceof T x_p) { .. x_p .. }`
    (and the negated guard, whose binding is in scope for the rest of the block). The decompiler drops
    the pattern binding whose store/load javac keeps."""

    def _parse(self, text: str):
        for m in _IF_HEAD.finditer(text):
            cm = _INSTANCEOF_COND.match(m.group("cond"))
            if cm is None or (cm.group("neg") is None) != (not m.group("cond").startswith("!(")):
                continue
            x, t, negated = cm.group("x"), cm.group("t"), cm.group("neg") is not None
            cast = re.compile(r"\(" + re.escape(t) + r"\)" + re.escape(x) + r"\b")
            open1 = m.end() - 1
            close1 = _match_brace(text, open1)
            if close1 < 0:
                continue
            ind = len(m.group(0)) - len(m.group(0).lstrip())
            if negated:
                if text.startswith("} else", close1) or not _leaves(text[open1 + 1:close1].split("\n")[1:-1]):
                    continue
                lo, hi = close1 + 1, _block_rest(text, close1 + 1, ind)[0]
            else:
                lo, hi = open1 + 1, close1
            if cast.search(text[lo:hi]):
                yield (m.start(), close1 + 1), m, x, t, negated, cast, lo, hi

    def sites(self, text: str) -> list:
        return [span for span, *_ in self._parse(text)]

    def apply(self, text: str, site: tuple) -> str:
        for span, m, x, t, negated, cast, lo, hi in self._parse(text):
            if span != tuple(site):
                continue
            name = f"{x}_p"
            cond = f"!({x} instanceof {t} {name})" if negated else f"{x} instanceof {t} {name}"
            return (text[:m.start("cond")] + cond + text[m.end("cond"):lo] + cast.sub(name, text[lo:hi]) + text[hi:])
        return text


instanceof_binding = _InstanceofBinding()


_RAW_PRIV = re.compile(r"\(niagara\.nre\.security\.privileged\.(PrivilegedAction|PrivilegedExceptionAction)\)(?= \()")


def privileged_void(text: str) -> str:
    """`(PrivilegedAction) () -> {..}` -> `(PrivilegedAction<Void>) () -> {..}`.

    The doPrivileged patch (F8) cast the lambda to the raw interface when it could not name the type
    argument; javac then infers an Object-returning lambda, while the shipped lambda returns Void
    (`return null;`). Only the raw, lambda-following casts are rewritten."""
    return _RAW_PRIV.sub(lambda m: f"(niagara.nre.security.privileged.{m.group(1)}<Void>)", text)


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


class RegexSites:
    """Site view of a regex-driven text hypothesis: every match the hypothesis would rewrite is one
    site, applicable alone (so a method that needs only some of the rewrites can be matched)."""

    def __init__(self, rewrites: Callable[[str], list]):
        self.rewrites = rewrites

    def sites(self, text: str) -> list:
        found = []
        for i, (pattern, rewrite) in enumerate(self.rewrites(text)):
            found += [(i, m.start(), m.end()) for m in pattern.finditer(text) if rewrite(m) != m.group(0)]
        return sorted(found, key=lambda s: s[1])

    def apply(self, text: str, site: tuple) -> str:
        i, start, end = site
        pattern, rewrite = self.rewrites(text)[i]
        m = pattern.search(text, start)
        if not m or m.start() != start or m.end() != end:
            return text
        return text[:start] + rewrite(m) + text[end:]


_NULL_CAST = re.compile(r"\((?:[A-Za-z_][\w.$]*(?:<[^()]*>)?(?:\[\])*)\)null\b")


def _null_cast_rewrites(text: str) -> list:
    """`(T)null` -> `null`. The decompiler keeps the cast to steer overload resolution and javac then
    emits `checkcast T` after `aconst_null`; the shipped code, compiled from a plain `null`, does
    not (a cast of null is a no-op, JVMS 6.5)."""
    return [(_NULL_CAST, lambda m: "null")]


remove_null_cast = RegexSites(_null_cast_rewrites)


# canonical rules (tools/n5_canon.py) -> the site hypotheses that can explain them: the climb of an
# `exact` splice only tries these for a method that was proven by those rules
_LAYOUT_SITES = ("split-return-ternary", "split-return-boolean", "guard-return", "guard-continue",
                 "early-return-else", "swap-if-else", "unguard-else", "invert-guard-return")
_TEMP_SITES = ("introduce-return-temp", "inline-return-temp", "compound-assign-site", "lift-increments-site")
RULE_SITES = {
    "tail": _LAYOUT_SITES, "min": _LAYOUT_SITES, "inl": _LAYOUT_SITES, "merge": _LAYOUT_SITES,
    "thread": _LAYOUT_SITES, "const": _LAYOUT_SITES, "cov": _LAYOUT_SITES, "cmp0": _LAYOUT_SITES,
    "cmp1": _LAYOUT_SITES, "boolmat": ("split-return-boolean", "split-return-ternary"),
    "dse": _TEMP_SITES + ("instanceof-binding",), "peep": _TEMP_SITES + ("instanceof-binding",), "r1": ("remove-null-cast",),
    "iinc": ("expand-iinc-site", "collapse-iinc-site", "lift-increments-site"),
    "web": ("hoist-declaration", "hoist-for-var", "instanceof-binding"),
}


def sites_for_rules(names: tuple, rule_sets: list) -> tuple:
    """`names` narrowed to the hypotheses that can explain the rules of the mismatching methods
    (`rule_sets`: one rule list per method); a method without rules (a true mismatch) keeps them all."""
    if not rule_sets or any(not rules for rules in rule_sets):
        return tuple(names)
    wanted = {n for rules in rule_sets for r in rules for n in RULE_SITES.get(r, names)}
    return tuple(n for n in names if n in wanted)


def site_pos(site: tuple) -> int:
    """Source offset of a site: RegexSites sites are (pattern index, start, end), every other site is
    a (start, end) span."""
    return site[1] if len(site) == 3 else site[0]


# name -> site hypothesis (`sites(text)` and `apply(text, site)`): repairs a class's structure, and
# with the splice's --climb the mismatching methods (one site at a time)
SITE_HYPOTHESES = {
    "swap-if-else": swap_if_else,
    "early-return-else": early_return_else,
    "guard-return": guard_return,
    "guard-continue": guard_continue,
    "hoist-declaration": hoist_declaration,
    "hoist-for-var": hoist_for_var,
    "unguard-else": unguard_else,
    "invert-guard-return": invert_guard_return,
    "instanceof-binding": instanceof_binding,
    "compound-assign-site": RegexSites(_compound_rewrites),
    "unfold-arrays-site": RegexSites(_unfold_rewrites),
    "expand-iinc-site": RegexSites(_expand_rewrites),
    "collapse-iinc-site": RegexSites(_collapse_rewrites),
    "lift-increments-site": RegexSites(_lift_rewrites),
    "split-return-ternary": split_return_ternary,
    "split-return-boolean": split_return_boolean,
    "remove-null-cast": remove_null_cast,
    "introduce-return-temp": introduce_return_temp,
    "inline-return-temp": inline_return_temp,
}

# hypotheses whose application makes progress and eventually leaves no site: the splice's site donor
# re-applies them to a fixed point (swap-if-else flips back and the other regex sites persist, so
# those make one pass)
for _name in ("split-return-ternary", "split-return-boolean", "guard-return", "guard-continue", "unguard-else",
              "early-return-else", "hoist-declaration", "hoist-for-var", "introduce-return-temp",
              "inline-return-temp", "remove-null-cast", "invert-guard-return", "instanceof-binding"):
    SITE_HYPOTHESES[_name].fixpoint = True


# name -> hypothesis, in the order the splice tries them
HYPOTHESES: dict[str, Callable[..., str]] = {
    "compound-assign": compound_assign,
    "unfold-single-array": unfold_single_element_arrays,
    "unfold-arrays": unfold_array_initializers,
    "expand-iinc": expand_iinc,
    "collapse-iinc": collapse_iinc,
    "restore-null-checks": restore_null_checks,
    "lift-increments": lift_increments,
    "declared-local-types": declared_local_types,
    "privileged-void": privileged_void,
}
