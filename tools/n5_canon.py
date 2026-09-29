"""n5_canon.py — sound control-flow canonicalization of one method's bytecode.

Used by tools/n5-fidelity.py for the `roundtrip-canonical` grades: a shipped
method and its recompiled counterpart that are NOT equal under the exact
normalizer can still be proven equivalent when both reduce to the same
canonical form. javac is not a canonicalizing compiler: the same semantics
compiled from two different (but equivalent) Java sources -- an early
`return` vs a ternary, `x = x + 1` vs `x++`, a dead temporary -- produce
different instruction streams. This module maps each method to a canonical
control-flow graph so that those codegen-shape differences disappear while
every semantic difference survives.

Soundness contract: every rule below is a semantics-preserving rewrite of the
method's control-flow graph (proof sketch in RULES). If canonical_form(a, R) ==
canonical_form(b, R) for a rule set R, then a and b behave identically for
every input, with two documented qualifications:

  * `cov` (ignore exception-range coverage of instructions that cannot throw)
    holds modulo asynchronous exceptions (JVMS 2.10: a VirtualMachineError may
    be thrown at ANY instruction) and IllegalMonitorStateException on a
    `*return` with unbalanced monitors (never produced by javac);
  * the TIER-2 rules (`cmp1`, `boolmat`) additionally rely on the JLS
    invariant that a boolean-typed value is 0 or 1, which javac-compiled code
    maintains but the JVM does not enforce for arbitrary bytecode. Grades that
    need them are labelled `roundtrip-canonical-t2`, never `roundtrip-canonical`.

Anything this module does not model (jsr/ret, a branch into the middle of an
instruction, non-uniform exception coverage it cannot split) raises
Unsupported, which the caller treats as "not proven equal" (fail-closed).

Baseline canonical form (always on, independent of the rule switches):
basic blocks; conditional-branch polarity normalized (`ifne T else F` ==
`ifeq F else T`); blocks numbered in DFS pre-order from the entry, so byte
layout disappears; unreachable blocks dropped; ldc_w/goto_w/iinc_w/xload_w
collapsed to their narrow form; locals named by first use with PARAMETER
slots pinned (their entry value comes from the caller); exception coverage
kept per block as the ORDERED list of (catch type, handler block) of the
table rows covering it -- table order is catch priority (JVMS 2.10), so it is
never sorted.
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

TIER1_RULES = ("cov", "thread", "const", "cmp0", "tail", "inl", "merge",
               "r1", "iinc", "peep", "dse", "min", "web")
TIER2_RULES = ("cmp1", "boolmat")
ALL_RULES = TIER1_RULES + TIER2_RULES

RULES = {
    "cov": (1, "An exception-table range only matters for instructions that can throw: coverage of loads, "
               "stores, constants, arithmetic other than integer div/rem, branches and returns is ignored. "
               "Modulo asynchronous exceptions (JVMS 2.10) and IllegalMonitorStateException on return."),
    "thread": (1, "A jump to an empty block that only jumps on is a jump to its final target (jump threading)."),
    "const": (1, "`<int constant c>; goto T` where T is an empty `ifeq/iflt/ifgt` block branches directly to "
                 "the successor the constant selects (constant-condition folding)."),
    "cmp0": (1, "`x; iconst_0; if_icmpeq/lt/gt` == `x; ifeq/lt/gt` and `x; aconst_null; if_acmpeq` == "
                "`x; ifnull`: comparing with zero/null is what the one-operand forms do."),
    "tail": (1, "A jump to a straight-line block that ends in *return/athrow executes exactly that block: "
                "inline a copy of it (tail duplication; at most 40 instructions)."),
    "inl": (1, "A jump to a block of at most 3 instructions that ends in a jump executes that block and then "
               "the jump: inline a copy of it."),
    "merge": (1, "A block reached only by an unconditional jump from one predecessor is concatenated to it."),
    "r1": (1, "`aconst_null; checkcast T` == `aconst_null`: null passes every checkcast (JVMS 6.5)."),
    "iinc": (1, "`iload k; <int c>; iadd|isub; istore k` == `iinc k +-c`: identical int wrap-around arithmetic."),
    "peep": (1, "Stack/local identities: `xstore k; xload k` == `dup; xstore k`, `xload k; xload k` == "
                "`xload k; dup` (dup2 for long/double), and a side-effect-free push immediately popped is "
                "removed."),
    "dse": (1, "A store (or iinc) to a local that no later instruction reads -- including through an "
               "exception handler that may be entered -- is dead: the store becomes a pop, the iinc vanishes."),
    "min": (1, "Blocks with identical code, terminator and catch types whose successors and handlers are "
               "equivalent are behaviourally identical and merged (bisimulation minimization)."),
    "web": (1, "Locals are named by def-use web (reaching definitions) instead of by slot: a bijective renaming "
               "of independent live ranges. Webs that contain a parameter's entry value keep the parameter "
               "slot's name."),
    "cmp1": (2, "`x; iconst_1; if_icmpeq` == `x; ifne` when x is produced by a Z-typed method/field or "
                "instanceof. Needs the JLS invariant that a boolean is 0 or 1."),
    "boolmat": (2, "`x ? 1 : 0` (branches that only push iconst_1/iconst_0 and rejoin) == `x` when x is Z-typed "
                   "or instanceof. Needs the JLS invariant that a boolean is 0 or 1."),
}

MAX_INSNS = 30000
TAIL_MAX = 40
INLINE_MAX = 3


class Unsupported(Exception):
    """The method uses a shape this canonicalizer does not model. Callers must
    treat it as NOT proven equal (fail-closed)."""


# ---------------------------------------------------------------------------
# javap Code parsing (shared with tools/n5-fidelity.py)
# ---------------------------------------------------------------------------

INSTR_LINE_RE = re.compile(r"^\s*(\d+):\s*(\S+)(.*)$")
# javap prints a negative case key bare (e.g. "-5: 36"); "-?\d+" is used for the
# target too so a malformed row is captured (and compared), never dropped.
SWITCH_CASE_RE = re.compile(r"^\s*(-?\d+|default)\s*:\s*(-?\d+)\s*$")
_CP_INDEX_RE = re.compile(r"#\d+(?:\.#\d+)?")


def parse_code_stream(raw_lines: list[str]) -> list[dict]:
    """Parse raw javap ``Code`` lines into instruction records.

    A ``tableswitch``/``lookupswitch`` is printed as a multi-line block whose
    ``<key>: <target>`` rows look exactly like instruction lines; they are
    consumed as the switch's operands, never as instructions.
    """
    records: list[dict] = []
    i = 0
    while i < len(raw_lines):
        m = INSTR_LINE_RE.match(raw_lines[i])
        if not m:
            i += 1
            continue
        offset = int(m.group(1))
        mnemonic = m.group(2)
        rest = m.group(3)
        if mnemonic in ("tableswitch", "lookupswitch"):
            entries: list[tuple[int, int]] = []
            default_target = None
            i += 1
            while i < len(raw_lines):
                line = raw_lines[i].strip()
                if line == "}":
                    i += 1
                    break
                cm = SWITCH_CASE_RE.match(line)
                if cm:
                    key, target = cm.group(1), int(cm.group(2))
                    if key == "default":
                        default_target = target
                    else:
                        entries.append((int(key), target))
                i += 1
            records.append({
                "kind": "switch", "offset": offset, "mnemonic": mnemonic,
                "entries": entries, "default": default_target,
            })
        else:
            records.append({"kind": "insn", "offset": offset, "mnemonic": mnemonic, "rest": rest})
            i += 1
    return records


# ---------------------------------------------------------------------------
# Instruction model
# ---------------------------------------------------------------------------

RETURNS = {"ireturn", "lreturn", "freturn", "dreturn", "areturn", "return"}
_NEGATE = {
    "ifne": "ifeq", "ifge": "iflt", "ifle": "ifgt", "ifnonnull": "ifnull",
    "if_icmpne": "if_icmpeq", "if_icmpge": "if_icmplt", "if_icmple": "if_icmpgt", "if_acmpne": "if_acmpeq",
}
CONDS = set(_NEGATE) | set(_NEGATE.values())
_SLOT_OP_RE = re.compile(r"^([ailfd])(load|store)(?:_([0-3])|_w)?$")
_THROWING = {
    "invokevirtual", "invokespecial", "invokestatic", "invokeinterface", "invokedynamic",
    "getfield", "putfield", "getstatic", "putstatic", "new", "newarray", "anewarray", "multianewarray",
    "arraylength", "athrow", "checkcast", "instanceof", "monitorenter", "monitorexit",
    "idiv", "irem", "ldiv", "lrem",
    "iaload", "laload", "faload", "daload", "aaload", "baload", "caload", "saload",
    "iastore", "lastore", "fastore", "dastore", "aastore", "bastore", "castore", "sastore",
}
# an ldc of one of these cannot throw (no class/method-handle/condy resolution)
_LDC_PLAIN_RE = re.compile(r"//\s*(String|int|float|long|double)\b")


def _operand(rest: str) -> str:
    return re.sub(r"\s+", " ", _CP_INDEX_RE.sub("", rest)).strip()


def _insn(op: str, slot: Optional[int] = None, arg: str = "") -> dict:
    return {"op": op, "slot": slot, "arg": arg}


def parse_instructions(raw_lines: list[str]) -> list[dict]:
    """javap Code lines -> instruction dicts {op, slot, arg[, t | sw, dflt]}.

    Branch/switch targets are instruction INDICES; width variants are collapsed
    (ldc_w->ldc, goto_w->goto, iinc_w->iinc, xload_w->xload); a slot operand is
    held in `slot` whatever its encoding (short, long or wide form)."""
    records = parse_code_stream(raw_lines)
    if len(records) > MAX_INSNS:
        raise Unsupported("method too large")
    index_of = {r["offset"]: i for i, r in enumerate(records)}

    def idx(offset: Optional[int]) -> int:
        if offset is None or offset not in index_of:
            raise Unsupported(f"branch target {offset} is not an instruction boundary")
        return index_of[offset]

    out = []
    for rec in records:
        op = rec["mnemonic"]
        if rec["kind"] == "switch":
            d = _insn(op)
            d["sw"] = sorted((k, idx(t)) for k, t in rec["entries"])
            d["dflt"] = idx(rec["default"])
            out.append(d)
            continue
        rest = rec["rest"]
        if op in ("jsr", "jsr_w", "ret"):
            raise Unsupported("jsr/ret subroutines")
        m = _SLOT_OP_RE.match(op)
        if m:
            if m.group(3) is not None:
                slot = int(m.group(3))
            else:
                sm = re.match(r"^\s*(\d+)", rest)
                if not sm:
                    raise Unsupported(f"slot operand missing: {op}{rest}")
                slot = int(sm.group(1))
            out.append(_insn(m.group(1) + m.group(2), slot))
            continue
        if op in ("iinc", "iinc_w"):
            im = re.match(r"^\s*(\d+)\s*,?\s*(-?\d+)", rest)
            if not im:
                raise Unsupported(f"iinc operand: {rest}")
            out.append(_insn("iinc", int(im.group(1)), str(int(im.group(2)))))
            continue
        if op == "ldc_w":
            op = "ldc"
        if op == "goto_w":
            op = "goto"
        if op in CONDS or op == "goto":
            tm = re.match(r"^\s*(\d+)", rest)
            if not tm:
                raise Unsupported(f"branch operand: {op}{rest}")
            d = _insn(op)
            d["t"] = idx(int(tm.group(1)))
            out.append(d)
            continue
        out.append(_insn(op, None, _operand(rest)))
    return out


def can_throw(d: dict) -> bool:
    op = d["op"]
    if op in _THROWING:
        return True
    if op in ("ldc", "ldc2_w"):
        return not _LDC_PLAIN_RE.search(d["arg"])
    return False


def int_const(d: dict) -> Optional[int]:
    op = d["op"]
    if op.startswith("iconst_"):
        v = op[len("iconst_"):]
        return -1 if v == "m1" else int(v)
    if op in ("bipush", "sipush"):
        try:
            return int(d["arg"].split()[0])
        except (ValueError, IndexError):
            return None
    return None


def render(d: dict, slot_name: Optional[str] = None) -> str:
    parts = [d["op"]]
    if d.get("slot") is not None:
        parts.append(slot_name if slot_name is not None else str(d["slot"]))
    if d.get("arg"):
        parts.append(d["arg"])
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Control-flow graph
# ---------------------------------------------------------------------------

class Block:
    __slots__ = ("body", "term", "succ", "cov")

    def __init__(self, body, term, succ, cov):
        self.body = body      # list[insn dict], terminator excluded
        self.term = term      # ("end", op) | ("jump",) | ("cond", op) | ("switch", op, keys)
        self.succ = succ      # list[int]: cond = [taken, not-taken]; switch = keys order + default
        self.cov = cov        # tuple[(catch type, handler block)], table (= priority) order

    def throws(self) -> bool:
        return self.term == ("end", "athrow") or any(can_throw(d) for d in self.body)


def _ordered_unique(items: Iterable) -> tuple:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return tuple(out)


def build_cfg(insns: list[dict], rows: list[tuple[int, int, int, str]], rules: frozenset) -> list[Block]:
    """`rows` are exception-table rows mapped to instruction indices
    (start, end, handler, type), end exclusive, in TABLE order."""
    n = len(insns)
    leaders = {0}
    for i, d in enumerate(insns):
        if "t" in d:
            leaders.update((d["t"], i + 1))
        elif "sw" in d:
            leaders.update(t for _, t in d["sw"])
            leaders.update((d["dflt"], i + 1))
        elif d["op"] in RETURNS or d["op"] == "athrow":
            leaders.add(i + 1)
    for start, end, handler, _t in rows:
        leaders.add(handler)
        if "cov" not in rules:
            leaders.update((start, end))

    def cover(i: int) -> tuple:
        return _ordered_unique((t, h) for s, e, h, t in rows if s <= i < e)

    if "cov" in rules:
        # split so that every throwing instruction of a block has the same coverage
        ordered = sorted(x for x in leaders if x < n)
        for k, start in enumerate(ordered):
            end = ordered[k + 1] if k + 1 < len(ordered) else n
            prev = None
            for i in range(start, end):
                if can_throw(insns[i]):
                    c = cover(i)
                    if prev is not None and c != prev:
                        leaders.add(i)
                        # a new block starts here; its first throwing insn sets the coverage
                    prev = c
    starts = sorted(x for x in leaders if x < n)
    bid = {}
    spans = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else n
        spans.append((s, e))
        for i in range(s, e):
            bid[i] = k

    blocks = []
    for s, e in spans:
        last = insns[e - 1]
        body = [insns[i] for i in range(s, e - 1)]
        op = last["op"]
        if op in RETURNS or op == "athrow":
            term, succ = ("end", op), []
        elif op == "goto":
            term, succ = ("jump",), [bid[last["t"]]]
        elif op in CONDS:
            if e >= n:
                raise Unsupported("conditional branch falls off the end")
            taken, fall = bid[last["t"]], bid[e]
            if op in _NEGATE:
                op, taken, fall = _NEGATE[op], fall, taken
            term, succ = ("cond", op), [taken, fall]
        elif "sw" in last:
            term = ("switch", op, tuple(k for k, _ in last["sw"]))
            succ = [bid[t] for _, t in last["sw"]] + [bid[last["dflt"]]]
        else:
            if e >= n:
                raise Unsupported("falls off the end of the code")
            body.append(last)
            term, succ = ("jump",), [bid[e]]
        if "cov" in rules:
            throwing = [i for i in range(s, e) if can_throw(insns[i])]
            cov_idx = cover(throwing[0]) if throwing else ()
            if any(cover(i) != cov_idx for i in throwing):
                raise Unsupported("non-uniform coverage within a block")
        else:
            cov_idx = cover(s)
            if any(cover(i) != cov_idx for i in range(s, e)):
                raise Unsupported("non-uniform coverage within a block")
        blocks.append(Block(body, term, succ, tuple((t, bid[h]) for t, h in cov_idx)))
    return blocks


def _map_rows(raw_lines: list[str], rows) -> list[tuple[int, int, int, str]]:
    records = parse_code_stream(raw_lines)
    index_of = {r["offset"]: i for i, r in enumerate(records)}
    n = len(records)
    code_end = None
    if records:
        # the exclusive `to` of a row may be the code length (one past the last insn)
        code_end = records[-1]["offset"]
    out = []
    for frm, to, target, etype in rows:
        if frm not in index_of or target not in index_of:
            raise Unsupported("exception row does not start at an instruction")
        if to in index_of:
            end = index_of[to]
        elif code_end is not None and to > code_end:
            end = n
        else:
            raise Unsupported("exception row does not end at an instruction")
        out.append((index_of[frm], end, index_of[target], re.sub(r"\s+", " ", etype).strip()))
    return out


def _reachable(blocks: list[Block], entry: int) -> list[int]:
    order, seen, stack = [], {entry}, [entry]
    while stack:
        x = stack.pop()
        order.append(x)
        for y in list(blocks[x].succ) + [h for _, h in blocks[x].cov]:
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return order


def _dfs_number(blocks: list[Block], entry: int) -> list[int]:
    num, order, stack = {}, [], [entry]
    while stack:
        y = stack.pop()
        if y in num:
            continue
        num[y] = len(order)
        order.append(y)
        nxt = list(blocks[y].succ) + [h for _, h in blocks[y].cov]
        for s in reversed(nxt):
            if s not in num:
                stack.append(s)
    return order


def _first_use_names(blocks, order, param_slots) -> dict:
    names, fresh = {}, {}
    for b in order:
        for i, d in enumerate(blocks[b].body):
            s = d.get("slot")
            if s is None:
                continue
            if s < param_slots:
                names[(b, i)] = f"p{s}"
            else:
                if s not in fresh:
                    fresh[s] = f"v{len(fresh)}"
                names[(b, i)] = fresh[s]
    return names


# ---------------------------------------------------------------------------
# Control-flow rules
# ---------------------------------------------------------------------------

def _compat(p: Block, t: Block, rules: frozenset) -> tuple[bool, tuple]:
    """Can T's instructions run under P's coverage (or vice versa) when the two
    are concatenated? Returns (ok, coverage of the concatenation)."""
    if "cov" in rules:
        if not p.throws():
            return True, t.cov
        if not t.throws():
            return True, p.cov
    return p.cov == t.cov, p.cov


_ZERO_TEST = {"if_icmpeq": "ifeq", "if_icmplt": "iflt", "if_icmpgt": "ifgt"}


def _zero_compare(blocks: list[Block]) -> None:
    for b in blocks:
        if b.term[0] != "cond" or not b.body:
            continue
        last = b.body[-1]
        if b.term[1] in _ZERO_TEST and int_const(last) == 0:
            b.body, b.term = b.body[:-1], ("cond", _ZERO_TEST[b.term[1]])
        elif b.term[1] == "if_acmpeq" and last["op"] == "aconst_null":
            b.body, b.term = b.body[:-1], ("cond", "ifnull")


def _is_boolean_producer(d: dict) -> bool:
    """instanceof, or a Z-typed method result / field read (javap comment
    `// Method owner.name:(...)Z` or `// Field owner.name:Z`)."""
    if d["op"] == "instanceof":
        return True
    if d["op"] in ("invokevirtual", "invokespecial", "invokestatic", "invokeinterface"):
        return bool(re.search(r"\)Z$", d["arg"]))
    if d["op"] in ("getfield", "getstatic"):
        return bool(re.search(r":Z$", d["arg"]))
    return False


def _one_compare(blocks: list[Block]) -> None:
    """TIER 2: `z; iconst_1; if_icmpeq T else F` == `z; ifeq F else T`."""
    for b in blocks:
        if (b.term == ("cond", "if_icmpeq") and len(b.body) >= 2 and int_const(b.body[-1]) == 1
                and _is_boolean_producer(b.body[-2])):
            b.body, b.term, b.succ = b.body[:-1], ("cond", "ifeq"), [b.succ[1], b.succ[0]]


def _thread(blocks: list[Block], entry: int) -> int:
    def resolve(x: int) -> int:
        seen = set()
        while blocks[x].term == ("jump",) and not blocks[x].body and not blocks[x].cov and x not in seen:
            seen.add(x)
            x = blocks[x].succ[0]
        return x
    for b in blocks:
        b.succ = [resolve(s) for s in b.succ]
        b.cov = tuple((t, resolve(h)) for t, h in b.cov)
    return resolve(entry)


def _fold_constants(blocks: list[Block], rules: frozenset) -> None:
    changed = True
    while changed:
        changed = False
        for b in blocks:
            if b.term != ("jump",) or not b.body:
                continue
            c = int_const(b.body[-1])
            t = blocks[b.succ[0]]
            if c is None or t is b or t.body or t.term[0] != "cond" or t.term[1] not in ("ifeq", "iflt", "ifgt"):
                continue
            if not _compat(b, t, rules)[0]:
                continue
            take = {"ifeq": c == 0, "iflt": c < 0, "ifgt": c > 0}[t.term[1]]
            b.body = b.body[:-1]
            b.succ = [t.succ[0] if take else t.succ[1]]
            changed = True


def _tail(blocks: list[Block], rules: frozenset) -> None:
    changed = True
    while changed:
        changed = False
        for x, b in enumerate(blocks):
            if b.term != ("jump",) or b.succ[0] == x:
                continue
            t = blocks[b.succ[0]]
            if t.term[0] != "end" or len(t.body) > TAIL_MAX:
                continue
            ok, cov = _compat(b, t, rules)
            if ok:
                b.body, b.term, b.succ, b.cov = b.body + t.body, t.term, [], cov
                changed = True


def _boolean_materialization(blocks: list[Block]) -> None:
    """TIER 2: `z; ifeq L0 else L1; L0: iconst_0 -> J; L1: iconst_1 -> J` == `z -> J`."""
    def literal(x: int, op: str) -> bool:
        return [d["op"] for d in blocks[x].body] == [op] and not blocks[x].cov
    for b in blocks:
        if b.term == ("cond", "ifeq") and b.body and not b.cov and _is_boolean_producer(b.body[-1]):
            s0, s1 = b.succ
            if (literal(s0, "iconst_0") and literal(s1, "iconst_1")
                    and blocks[s0].term == blocks[s1].term and blocks[s0].succ == blocks[s1].succ):
                b.term, b.succ = blocks[s0].term, list(blocks[s0].succ)


def _inline_small(blocks: list[Block], rules: frozenset) -> None:
    for _ in range(200):
        changed = False
        for x, b in enumerate(blocks):
            if b.term != ("jump",):
                continue
            ti = b.succ[0]
            t = blocks[ti]
            if ti == x or t.term != ("jump",) or len(t.body) > INLINE_MAX or t.succ[0] in (ti, x):
                continue
            ok, cov = _compat(b, t, rules)
            if ok:
                b.body, b.succ, b.cov = b.body + t.body, list(t.succ), cov
                changed = True
        if not changed:
            return


def _merge_chains(blocks: list[Block], entry: int, rules: frozenset) -> None:
    changed = True
    while changed:
        changed = False
        order = _reachable(blocks, entry)
        preds: dict[int, list[int]] = {}
        for x in order:
            for s in list(blocks[x].succ) + [h for _, h in blocks[x].cov]:
                preds.setdefault(s, []).append(x)
        for x in order:
            b = blocks[x]
            if b.term != ("jump",):
                continue
            ti = b.succ[0]
            if ti in (x, entry) or preds.get(ti) != [x]:
                continue
            t = blocks[ti]
            ok, cov = _compat(b, t, rules)
            if ok:
                b.body, b.term, b.succ, b.cov = b.body + t.body, t.term, list(t.succ), cov
                changed = True
                break


def _minimize(blocks: list[Block], entry: int) -> int:
    """Bisimulation: partition reachable blocks by (code, terminator, catch
    types), refine by successor/handler classes until stable, then redirect
    every edge to one representative per class."""
    live = _reachable(blocks, entry)

    def sig0(x):
        b = blocks[x]
        return (tuple(render(d) for d in b.body), b.term, tuple(t for t, _ in b.cov))
    ids: dict = {}
    cls = {x: ids.setdefault(sig0(x), len(ids)) for x in live}
    while True:
        ids2: dict = {}
        new = {}
        for x in live:
            b = blocks[x]
            key = (cls[x], tuple(cls[s] for s in b.succ), tuple(cls[h] for _, h in b.cov))
            new[x] = ids2.setdefault(key, len(ids2))
        stable = len(ids2) == len(set(cls.values()))
        cls = new
        if stable:
            break
    rep: dict = {}
    for x in live:
        rep.setdefault(cls[x], x)
    for x in live:
        b = blocks[x]
        b.succ = [rep[cls[s]] for s in b.succ]
        b.cov = tuple((t, rep[cls[h]]) for t, h in b.cov)
    return rep[cls[entry]]


# ---------------------------------------------------------------------------
# Data-flow rules
# ---------------------------------------------------------------------------

_PUSH1 = re.compile(r"^(aconst_null|iconst_\w+|fconst_\d|bipush|sipush|dup)$")
_PUSH2 = re.compile(r"^(lconst_\d|dconst_\d|dup2)$")


def _pure_push(d: dict, width: int) -> bool:
    op = d["op"]
    if d.get("slot") is not None:
        return op in (("iload", "fload", "aload") if width == 1 else ("lload", "dload"))
    if op in ("ldc", "ldc2_w"):
        return not can_throw(d) and (op == "ldc") == (width == 1)
    return bool((_PUSH1 if width == 1 else _PUSH2).match(op))


def _peephole(body: list[dict], rules: frozenset) -> list[dict]:
    out = list(body)
    changed = True
    while changed:
        changed = False
        new: list[dict] = []
        i = 0
        while i < len(out):
            d = out[i]
            n1 = out[i + 1] if i + 1 < len(out) else None
            if "r1" in rules and n1 is not None and d["op"] == "aconst_null" and n1["op"] == "checkcast":
                new.append(d)
                i += 2
                changed = True
                continue
            if "iinc" in rules and i + 3 < len(out):
                c, add, st = out[i + 1], out[i + 2], out[i + 3]
                k = int_const(c)
                if (d["op"] == "iload" and st["op"] == "istore" and d["slot"] == st["slot"]
                        and add["op"] in ("iadd", "isub") and k is not None):
                    new.append(_insn("iinc", d["slot"], str(k if add["op"] == "iadd" else -k)))
                    i += 4
                    changed = True
                    continue
            if "peep" in rules and n1 is not None:
                kind = d["op"][0]
                width = 2 if kind in "ld" else 1
                dup = _insn("dup2" if width == 2 else "dup")
                if (d["op"].endswith("store") and n1["op"] == kind + "load" and d["slot"] == n1["slot"]):
                    new.extend((dup, d))
                    i += 2
                    changed = True
                    continue
                if (d["op"].endswith("load") and d.get("slot") is not None and n1["op"] == d["op"]
                        and n1["slot"] == d["slot"]):
                    new.extend((d, dup))
                    i += 2
                    changed = True
                    continue
                if (n1["op"] == "pop" and _pure_push(d, 1)) or (n1["op"] == "pop2" and _pure_push(d, 2)):
                    i += 2
                    changed = True
                    continue
            new.append(d)
            i += 1
        out = new
    return out


def _dead_stores(blocks: list[Block], entry: int) -> None:
    """Liveness over slots; a handler's live-in is live at every point of a
    block it covers (the handler may be entered there)."""
    order = _reachable(blocks, entry)
    live_in: dict[int, set] = {x: set() for x in order}

    def walk(x: int, rewrite: bool):
        b = blocks[x]
        hl: set = set()
        for _, h in b.cov:
            hl |= live_in[h]
        live = set(hl)
        for s in b.succ:
            live |= live_in[s]
        body = []
        for d in reversed(b.body):
            s = d.get("slot")
            op = d["op"]
            if s is None:
                body.append(d)
            elif op.endswith("store"):
                if s in live or not rewrite:
                    body.append(d)
                else:
                    body.append(_insn("pop2" if op[0] in "ld" else "pop"))
                live.discard(s)
                live |= hl
            elif op == "iinc":
                if s in live or not rewrite:
                    body.append(d)
                # a dead iinc neither reads nor writes anything observable
            else:
                live.add(s)
                body.append(d)
        if rewrite:
            b.body = list(reversed(body))
        return live

    changed = True
    while changed:
        changed = False
        for x in reversed(order):
            live = walk(x, rewrite=False)
            if live != live_in[x]:
                live_in[x] = live
                changed = True
    for x in order:
        walk(x, rewrite=True)


def _web_names(blocks: list[Block], order: list[int], param_slots: int) -> dict:
    """Name every slot access by its def-use web. Reaching definitions per
    slot (a block's defs, and its entry state, reach every handler covering
    it); each use joins all definitions that reach it into one web. A web
    holding a parameter's entry value is named after that parameter slot."""
    parent: dict = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    rd_in: dict[int, dict] = {x: {} for x in order}
    for s in range(param_slots):
        rd_in[order[0]][s] = frozenset([("E", s)])

    def transfer(x: int, record: bool):
        state = dict(rd_in[x])
        to_handlers = {k: set(v) for k, v in state.items()}
        for i, d in enumerate(blocks[x].body):
            s = d.get("slot")
            if s is None:
                continue
            if not d["op"].endswith("store"):  # a load or an iinc reads s
                defs = state.get(s) or frozenset([("E", s)])
                if record:
                    node = ("U", x, i)
                    for df in defs:
                        union(node, df)
            if d["op"].endswith("store") or d["op"] == "iinc":
                if record and d["op"] == "iinc":
                    union(("U", x, i), (x, i))
                state[s] = frozenset([(x, i)])
                to_handlers.setdefault(s, set()).add((x, i))
        return state, to_handlers

    changed = True
    while changed:
        changed = False
        for x in order:
            out, to_handlers = transfer(x, record=False)
            targets = [(s, out) for s in blocks[x].succ] + [(h, to_handlers) for _, h in blocks[x].cov]
            for t, st in targets:
                cur = rd_in[t]
                for slot, defs in st.items():
                    merged = frozenset(defs) | cur.get(slot, frozenset())
                    if merged != cur.get(slot):
                        cur[slot] = merged
                        changed = True
    for x in order:
        transfer(x, record=True)

    pinned = {}
    for s in range(param_slots):
        pinned[find(("E", s))] = f"p{s}"
    names: dict = {}
    fresh: dict = {}
    for x in order:
        for i, d in enumerate(blocks[x].body):
            if d.get("slot") is None:
                continue
            node = (x, i) if d["op"].endswith("store") else ("U", x, i)
            root = find(node)
            if root in pinned:
                names[(x, i)] = pinned[root]
            else:
                if root not in fresh:
                    fresh[root] = f"v{len(fresh)}"
                names[(x, i)] = fresh[root]
    return names


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def _check_rules(rules: Iterable[str]) -> frozenset:
    rules = frozenset(rules)
    unknown = rules - set(ALL_RULES)
    if unknown:
        raise ValueError(f"unknown canonicalization rule(s): {sorted(unknown)}")
    return rules


def canonical_form(method: dict, rules: Iterable[str] = ALL_RULES) -> tuple:
    """Canonical form of one method. `method` carries the raw javap Code lines
    (`raw_code`), the raw exception rows (`raw_exception_rows`, table order) and
    `param_slots` (see n5-fidelity's parse_javap_verbose). Raises Unsupported."""
    rules = _check_rules(rules)
    raw = method.get("raw_code")
    if raw is None:
        raise Unsupported("no raw code recorded")
    insns = parse_instructions(raw)
    if not insns:
        return ("empty",)
    rows = _map_rows(raw, method.get("raw_exception_rows") or [])
    blocks = build_cfg(insns, rows, rules)
    entry = 0
    if "cmp0" in rules:
        _zero_compare(blocks)
    if "cmp1" in rules:
        _one_compare(blocks)
    if "thread" in rules:
        entry = _thread(blocks, entry)
    if "const" in rules:
        _fold_constants(blocks, rules)
        if "thread" in rules:
            entry = _thread(blocks, entry)  # a folded block is often an empty jump now
    if "tail" in rules:
        _tail(blocks, rules)
    if "boolmat" in rules:
        _boolean_materialization(blocks)
    if "inl" in rules:
        _inline_small(blocks, rules)
    if "merge" in rules:
        _merge_chains(blocks, entry, rules)
    if rules & {"r1", "iinc", "peep"}:
        for b in blocks:
            b.body = _peephole(b.body, rules)
    if "dse" in rules:
        _dead_stores(blocks, entry)
        for b in blocks:
            b.body = _peephole(b.body, rules)  # e.g. `push; pop` left by a dead store
    if "cov" in rules:
        for b in blocks:
            if not b.throws():
                b.cov = ()
    if "min" in rules:
        entry = _minimize(blocks, entry)
    order = _dfs_number(blocks, entry)
    param_slots = int(method.get("param_slots") or 0)
    if "web" in rules:
        names = _web_names(blocks, order, param_slots)
    else:
        names = _first_use_names(blocks, order, param_slots)
    num = {b: k for k, b in enumerate(order)}
    out = []
    for b in order:
        blk = blocks[b]
        body = tuple(render(d, names.get((b, i))) for i, d in enumerate(blk.body))
        out.append((body, blk.term, tuple(num[s] for s in blk.succ), tuple((t, num[h]) for t, h in blk.cov)))
    return tuple(out)


def canonical_equal(a: dict, b: dict, rules: Iterable[str] = ALL_RULES) -> bool:
    """True only when both methods canonicalize and the forms are identical;
    Unsupported on either side is False (fail-closed)."""
    try:
        return canonical_form(a, rules) == canonical_form(b, rules)
    except Unsupported:
        return False


def resolve_rules(a: dict, b: dict, tier2: bool = False) -> Optional[list[str]]:
    """Return an irreducible list of rules under which `a` and `b` canonicalize
    equal (greedy removal in ALL_RULES order from TIER1_RULES, plus TIER2_RULES
    when `tier2`), or None when even the full set does not prove them equal.
    The returned list is exactly what made them equal: a caller labels the
    result tier 2 only if it contains a TIER2_RULES name."""
    full = list(TIER1_RULES + (TIER2_RULES if tier2 else ()))
    if not canonical_equal(a, b, full):
        return None
    kept = list(full)
    for r in full:
        trial = [x for x in kept if x != r]
        if canonical_equal(a, b, trial):
            kept = trial
    return kept
