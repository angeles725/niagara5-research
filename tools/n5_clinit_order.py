"""n5_clinit_order.py -- restore the static-initializer ORDER of a decompiled class (C3d).

`<clinit>` runs the static field initializers and the `static { }` blocks in source order. A
decompiler that prints every field with its initializer at the declaration and the static
blocks elsewhere changes that order whenever the original interleaved them (a block that
fills a map between two fields, a field that reads state a block set up). The class still
compiles, but its `<clinit>` differs from the shipped one.

The shipped bytecode says what the order was: the shipped `<clinit>` is a concatenation of the
instruction runs of the source units (one per initialized static field, one per statement of a
static block). Each unit of the decompiled source is located in its own recompiled `<clinit>`
through the LineNumberTable, and the shipped run is matched against those runs. When the
shipped `<clinit>` is exactly a permutation of the recompiled runs, the permutation is the
original order, and only the field initializers that must move are un-hoisted into a static
block at the right place (`static T f = e;` -> `static T f;` plus `f = e;` after the unit that
precedes it). Anything else (a run that matches nothing, two units on one line, a statement
that would have to move, a multi-variable declaration) is refused, never guessed. The grader
decides afterwards whether the rewritten class is faithful.
"""
from __future__ import annotations

import bisect
import re
from typing import Optional

_PC_RE = re.compile(r"^\s+(\d+): (\S+)")
_LNT_RE = re.compile(r"^\s+line (\d+): (\d+)\s*$")


class Unsupported(Exception):
    """The class does not fit the ordering model; the source is left unchanged."""


def parse_clinit(javap_text: str) -> dict:
    """{"pcs": [pc per instruction], "lnt": [(line, pc)]} of the `static {};` method of a
    `javap -v -p` listing (instruction order equals the grader's normalized code order)."""
    lines = javap_text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip() == "static {};"), None)
    if start is None:
        raise Unsupported("no static initializer in the listing")
    pcs: list[int] = []
    lnt: list[tuple[int, int]] = []
    in_lnt = False
    for line in lines[start + 1:]:
        if line and not line.startswith(" "):
            break
        if re.match(r"^  \S", line) and not line.startswith("   "):
            break  # next member
        s = line.strip()
        if s.startswith("LineNumberTable:"):
            in_lnt = True
            continue
        if in_lnt:
            m = _LNT_RE.match(line)
            if m:
                lnt.append((int(m.group(1)), int(m.group(2))))
                continue
            in_lnt = False
        m = _PC_RE.match(line)
        if m and not in_lnt:
            pcs.append(int(m.group(1)))
    return {"pcs": pcs, "lnt": lnt}


def build_units(text: str, inits: list[dict]) -> list[dict]:
    """Ordered source units of the static initialization: an initialized static field or one
    statement of a static block. Refuses overlapping declarations (`int a = 1, b = 2;`)."""
    starts = [0]
    for m in re.finditer("\n", text):
        starts.append(m.end())

    def line_of(off: int) -> int:
        return bisect.bisect_right(starts, off)

    units: list[dict] = []
    seen_field_starts: set[int] = set()
    for b, blk in enumerate(inits):
        if blk["kind"] == "field":
            if blk["start"] in seen_field_starts:
                raise Unsupported("multi-variable static declaration")
            seen_field_starts.add(blk["start"])
            units.append({"kind": "field", "name": blk["name"], "start": blk["start"], "end": blk["end"],
                          "init_start": blk["init_start"], "init_end": blk["init_end"], "block": None})
        else:
            for k, (s, e) in enumerate(blk["stmts"]):
                units.append({"kind": "stmt", "start": s, "end": e, "block": b, "index": k,
                              "block_end": blk["end"]})
    # a following declaration of the same statement start means a multi-variable declaration
    fields = [u for u in units if u["kind"] == "field"]
    for a, b2 in zip(fields, fields[1:]):
        if b2["start"] < a["end"]:
            raise Unsupported("multi-variable static declaration")
    units.sort(key=lambda u: u["start"])
    for i, u in enumerate(units):
        u["id"] = i
        u["l1"] = line_of(u["start"])
        u["l2"] = line_of(max(u["start"], u["end"] - 1))
    spans = sorted((u["l1"], u["l2"]) for u in units)
    for (a1, a2), (b1, _b2) in zip(spans, spans[1:]):
        if b1 <= a2:
            raise Unsupported("two initializer units share a source line")
    return units


def slice_units(units: list[dict], parsed: dict, code: list[str]) -> dict[int, list[str]]:
    """{unit id: normalized instruction run} of the recompiled `<clinit>`. Units without code
    (constant variables) are absent. `code` is the grader's normalized instruction list
    (`insnN: op operand`), parallel to parsed["pcs"]; the final `return` belongs to no unit."""
    pcs = parsed["pcs"]
    if len(pcs) != len(code):
        raise Unsupported("listing and normalized code disagree")
    body = [_strip(c) for c in code]
    first_pc: dict[int, int] = {}
    for u in units:
        hits = [pc for line, pc in parsed["lnt"] if u["l1"] <= line <= u["l2"]]
        if hits:
            first_pc[u["id"]] = min(hits)
    ordered = sorted(first_pc, key=lambda i: first_pc[i])
    if ordered != sorted(ordered):
        raise Unsupported("unit code is not in source order")
    idx_of = {pc: i for i, pc in enumerate(pcs)}
    bounds = [idx_of[first_pc[i]] for i in ordered] + [len(body) - 1 if body and body[-1] == "return" else len(body)]
    out: dict[int, list[str]] = {}
    for n, uid in enumerate(ordered):
        out[uid] = body[bounds[n]:bounds[n + 1]]
    if ordered and bounds[0] != 0:
        raise Unsupported("code before the first unit")
    return out


def _strip(line: str) -> str:
    return re.sub(r"^insn\d+:\s*", "", line)


def match_order(shipped: list[str], slices: dict[int, list[str]]) -> Optional[list[int]]:
    """The unit order whose runs concatenate to the shipped `<clinit>` body, or None."""
    body = [_strip(c) for c in shipped]
    if body and body[-1] == "return":
        body = body[:-1]
    ids = sorted(slices)
    budget = [200_000]

    def go(pos: int, used: frozenset) -> Optional[list[int]]:
        budget[0] -= 1
        if budget[0] < 0:
            return None
        if pos == len(body):
            return [] if len(used) == len(ids) else None
        for i in ids:
            run = slices[i]
            if i in used or not run or body[pos:pos + len(run)] != run:
                continue
            rest = go(pos + len(run), used | {i})
            if rest is not None:
                return [i, *rest]
        return None
    empty = [i for i in ids if not slices[i]]
    if empty:
        return None
    return go(0, frozenset())


def longest_kept(order: list[int], desired: list[int], mandatory: frozenset = frozenset()) -> set[int]:
    """Units that keep their textual place: a heaviest common subsequence of `order` (source
    order) and `desired` (shipped order), both permutations of the same ids. `mandatory` units
    (static-block statements, which cannot move) weigh more than any number of the others, so
    they are kept whenever any order keeps them all; the caller checks that."""
    rank = {u: i for i, u in enumerate(desired)}
    n = len(order)
    weight = [1000 if u in mandatory else 1 for u in order]
    best = list(weight)
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if rank[order[j]] < rank[order[i]] and best[j] + weight[i] > best[i]:
                best[i] = best[j] + weight[i]
                prev[i] = j
    kept: set[int] = set()
    i = max(range(n), key=lambda k: best[k], default=-1)
    while i != -1:
        kept.add(order[i])
        i = prev[i]
    return kept


def rewrite(text: str, units: list[dict], slices_ids: list[int], desired: list[int]) -> str:
    """Source with the shipped initialization order; Unsupported when a statement would move."""
    by_id = {u["id"]: u for u in units}
    order = [u for u in slices_ids]  # source order of the units that have code
    kept = longest_kept(order, desired, frozenset(u for u in order if by_id[u]["kind"] != "field"))
    moved = [u for u in desired if u not in kept]
    if not moved:
        return text
    if any(by_id[u]["kind"] != "field" for u in moved):
        raise Unsupported("a static-block statement would have to move")
    edits: list[tuple[int, int, str]] = []
    inserts: dict[tuple[str, int], list[str]] = {}
    for u in moved:
        un = by_id[u]
        eq = text.rfind("=", un["start"], un["init_start"])
        if eq < 0:
            raise Unsupported("initializer without '='")
        head = eq
        while head > un["start"] and text[head - 1] in " \t\n":
            head -= 1
        edits.append((head, un["end"] - 1, ""))  # keeps the terminating ';' of the declaration
        decl_end = un["end"]
        if text[decl_end - 1] != ";":
            raise Unsupported("declaration does not end with ';'")
        stmt = f"{un['name']} = {text[un['init_start']:un['init_end']]};"
        pos = desired.index(u)
        anchor = next((d for d in reversed(desired[:pos]) if d in kept), None)
        if anchor is not None:
            a = by_id[anchor]
            key = ("after_stmt", a["end"]) if a["kind"] == "stmt" else ("after_field", a["end"])
        else:
            nxt = next((d for d in desired[pos + 1:] if d in kept), None)
            if nxt is None:
                raise Unsupported("no anchor unit")
            n = by_id[nxt]
            key = ("before_stmt", n["start"]) if n["kind"] == "stmt" else ("before_field", n["start"])
        inserts.setdefault(key, []).append(stmt)
    for (kind, off), stmts in inserts.items():
        indent = _indent_at(text, off if kind.endswith("stmt") or kind.startswith("before") else off)
        if kind == "after_stmt":
            edits.append((off, off, "".join(f"\n{indent}{s}" for s in stmts)))
        elif kind == "before_stmt":
            edits.append((off, off, "".join(f"{s}\n{indent}" for s in stmts)))
        elif kind == "after_field":
            edits.append((off, off, f"\n{indent}static {{\n" + "".join(f"{indent}   {s}\n" for s in stmts)
                          + f"{indent}}}"))
        else:  # before_field
            edits.append((off, off, f"static {{\n" + "".join(f"{indent}   {s}\n" for s in stmts)
                          + f"{indent}}}\n{indent}"))
    out = text
    for s, e, new in sorted(edits, key=lambda x: (x[0], x[1]), reverse=True):
        out = out[:s] + new + out[e:]
    return out


def _indent_at(text: str, off: int) -> str:
    line_start = text.rfind("\n", 0, off) + 1
    m = re.match(r"[ \t]*", text[line_start:off])
    return m.group(0) if m else ""


def reorder_clinit(text: str, inits: list[dict], shipped_code: list[str], ours_javap: str,
                   ours_code: list[str]) -> Optional[str]:
    """The source with the shipped static-initialization order, None when the order already
    matches; raises Unsupported when the class does not fit the model."""
    units = build_units(text, inits)
    parsed = parse_clinit(ours_javap)
    slices = slice_units(units, parsed, ours_code)
    desired = match_order(shipped_code, slices)
    if desired is None:
        raise Unsupported("the shipped <clinit> is not a permutation of the recompiled unit runs")
    order = sorted(slices)
    if desired == order:
        return None
    return rewrite(text, units, order, desired)
