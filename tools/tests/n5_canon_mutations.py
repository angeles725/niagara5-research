"""Semantic mutation operators over one method's raw javap Code lines, for the
fail-closed soundness suite of tools/n5_canon.py (test_n5_canon_soundness.py).

Every operator produces a method that behaves DIFFERENTLY from the original
for some input (or that no longer verifies) -- never a semantic no-op, except
where a generator filter below documents why the candidate it skips would be
one. A sound canonicalizer must therefore give every mutant a canonical form
different from the original's.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import n5_canon  # noqa: E402

_LINE_RE = re.compile(r"^(\s*\d+:\s*)(\S+)(.*)$")
_NEGATE = {
    "ifeq": "ifne", "ifne": "ifeq", "iflt": "ifge", "ifge": "iflt", "ifgt": "ifle", "ifle": "ifgt",
    "ifnull": "ifnonnull", "ifnonnull": "ifnull",
    "if_icmpeq": "if_icmpne", "if_icmpne": "if_icmpeq", "if_icmplt": "if_icmpge", "if_icmpge": "if_icmplt",
    "if_icmpgt": "if_icmple", "if_icmple": "if_icmpgt", "if_acmpeq": "if_acmpne", "if_acmpne": "if_acmpeq",
}
# non-commutative binary ops whose two operands are pushed by the two
# preceding instructions when both are simple pushes
_NON_COMMUTATIVE = {"isub", "idiv", "irem", "ishl", "ishr", "iushr", "lsub", "ldiv", "lrem", "lcmp",
                    "fsub", "fdiv", "dsub", "ddiv", "fcmpl", "fcmpg", "dcmpl", "dcmpg",
                    "if_icmplt", "if_icmpgt", "if_icmpge", "if_icmple"}
_SIMPLE_PUSH = re.compile(r"^([ilfda]load(_\d)?|[ilfd]const_\w+|bipush|sipush|ldc|ldc_w|ldc2_w|aconst_null)$")
_SIDE_EFFECT = re.compile(r"^(invoke\w+|putfield|putstatic)$")
_MEMBER_REF = re.compile(r"(// (?:Method|InterfaceMethod|Field) (?:[\w/$]+\.)?)([\w$<>]+)")
_STORE = re.compile(r"^([ilfda])store(?:_(\d)|_w)?$")
_LOAD = re.compile(r"^([ilfda])load(?:_(\d)|_w)?$")


def _split(line: str):
    m = _LINE_RE.match(line)
    return (m.group(1), m.group(2), m.group(3)) if m else None


def _instr_indices(raw: list[str]) -> list[int]:
    """Indices into `raw` of real instruction lines (switch case rows skipped)."""
    out, in_switch = [], False
    for i, line in enumerate(raw):
        s = line.strip()
        if in_switch:
            if s == "}":
                in_switch = False
            continue
        parts = _split(line)
        if parts is None:
            continue
        out.append(i)
        if parts[1] in ("tableswitch", "lookupswitch"):
            in_switch = True
    return out


def _slot(op: str, rest: str):
    for rx in (_STORE, _LOAD):
        m = rx.match(op)
        if m:
            if m.group(2) is not None:
                return m.group(1), int(m.group(2))
            sm = re.match(r"^\s*(\d+)", rest)
            return (m.group(1), int(sm.group(1))) if sm else None
    return None


def _leader_offsets(method: dict) -> set:
    """Offsets that start a basic block: branch and switch targets, handlers."""
    raw = method["raw_code"]
    out = {h for _f, _t, h, _ty in method.get("raw_exception_rows") or []}
    in_switch = False
    for line in raw:
        s = line.strip()
        if in_switch:
            if s == "}":
                in_switch = False
                continue
            cm = n5_canon.SWITCH_CASE_RE.match(s)
            if cm:
                out.add(int(cm.group(2)))
            continue
        parts = _split(line)
        if parts is None:
            continue
        if parts[1] in ("tableswitch", "lookupswitch"):
            in_switch = True
        elif parts[1] in _NEGATE or parts[1] in ("goto", "goto_w"):
            tm = re.match(r"^\s*(\d+)", parts[2])
            if tm:
                out.add(int(tm.group(1)))
    return out


def _offset(line: str) -> int:
    return int(line.strip().split(":")[0])


def _with(method: dict, raw=None, rows=None) -> dict:
    out = dict(method)
    if raw is not None:
        out["raw_code"] = raw
    if rows is not None:
        out["raw_exception_rows"] = rows
    return out


def _decoded(method: dict):
    """(instruction records, exception rows as index ranges) or None."""
    try:
        insns = n5_canon.parse_instructions(method["raw_code"])
        rows = n5_canon._map_rows(method["raw_code"], method.get("raw_exception_rows") or [])
    except n5_canon.Unsupported:
        return None
    return insns, rows


def mutations(method: dict, per_kind: int = 4) -> list[tuple[str, str, dict]]:
    """[(kind, description, mutant)] -- at most `per_kind` mutants per kind."""
    raw = method["raw_code"]
    idxs = _instr_indices(raw)
    leaders = _leader_offsets(method)
    out: dict[str, list] = {}

    def add(kind, desc, mutant):
        bucket = out.setdefault(kind, [])
        if len(bucket) < per_kind:
            bucket.append((kind, desc, mutant))

    def replace(i, new_line):
        r = list(raw)
        r[i] = new_line
        return r

    for pos, i in enumerate(idxs):
        prefix, op, rest = _split(raw[i])
        # 1. negate a conditional, targets unchanged
        if op in _NEGATE:
            add("negate-cond", f"{op}->{_NEGATE[op]} @{_offset(raw[i])}",
                _with(method, replace(i, f"{prefix}{_NEGATE[op]}{rest}")))
        # 2. swap the two pushes feeding a non-commutative op
        if op in _NON_COMMUTATIVE and pos >= 2:
            i1, i2 = idxs[pos - 2], idxs[pos - 1]
            p1, p2 = _split(raw[i1]), _split(raw[i2])
            if (_SIMPLE_PUSH.match(p1[1]) and _SIMPLE_PUSH.match(p2[1])
                    and (p1[1] + p1[2]).strip() != (p2[1] + p2[2]).strip()
                    and _offset(raw[i2]) not in leaders and _offset(raw[i]) not in leaders):
                r = list(raw)
                r[i1] = p1[0] + p2[1] + p2[2]
                r[i2] = p2[0] + p1[1] + p1[2]
                add("swap-operands", f"{op} @{_offset(raw[i])}", _with(method, r))
        # 3. change an int / ldc constant
        cm = re.match(r"^iconst_(m1|\d)$", op)
        if cm:
            v = -1 if cm.group(1) == "m1" else int(cm.group(1))
            new = f"iconst_{v + 1}" if v < 5 else "bipush 6"
            add("change-const", f"{op}->{new} @{_offset(raw[i])}", _with(method, replace(i, f"{prefix}{new}")))
        elif op in ("bipush", "sipush"):
            vm = re.match(r"^\s*(-?\d+)", rest)
            if vm:
                add("change-const", f"{op} +1 @{_offset(raw[i])}",
                    _with(method, replace(i, f"{prefix}{op} {int(vm.group(1)) + 1}")))
        elif op in ("ldc", "ldc_w", "ldc2_w"):
            lm = re.search(r"// (String|int|long|float|double) (.*)$", rest)
            if lm:
                kind, val = lm.group(1), lm.group(2)
                newval = val + "_mut" if kind == "String" else re.sub(r"(-?\d+)", lambda x: str(int(x.group(1)) + 1),
                                                                     val, count=1)
                if newval != val:
                    add("change-const", f"{op} {kind} @{_offset(raw[i])}",
                        _with(method, replace(i, f"{prefix}{op}{rest[:lm.start(2)]}{newval}")))
        elif op == "invokedynamic" and "]:" in rest:
            # the resolved bootstrap arguments (string-concat recipe, lambda target)
            add("change-const", f"indy bootstrap args @{_offset(raw[i])}",
                _with(method, replace(i, f"{prefix}{op}{rest.replace(']:', '_mut]:', 1)}")))
        # 4. change a field or method reference
        mm = _MEMBER_REF.search(rest)
        if mm and op.startswith(("invoke", "get", "put")) and mm.group(2) not in ("<init>", "<clinit>"):
            new_rest = rest[:mm.start(2)] + mm.group(2) + "_mut" + rest[mm.end(2):]
            add("change-member-ref", f"{op} {mm.group(2)} @{_offset(raw[i])}",
                _with(method, replace(i, f"{prefix}{op}{new_rest}")))
        # 5. delete a call (not a block leader)
        if op.startswith("invoke") and _offset(raw[i]) not in leaders:
            add("delete-call", f"{op} @{_offset(raw[i])}", _with(method, raw[:i] + raw[i + 1:]))

    # 6. reorder two side-effecting instructions of one straight-line run
    run: list[int] = []
    for i in idxs:
        prefix, op, rest = _split(raw[i])
        if _offset(raw[i]) in leaders:
            run = []
        if _SIDE_EFFECT.match(op):
            if run:
                j = run[-1]
                a, b = _split(raw[j]), _split(raw[i])
                if (a[1] + a[2]).strip() != (b[1] + b[2]).strip():
                    r = list(raw)
                    r[j], r[i] = a[0] + b[1] + b[2], b[0] + a[1] + a[2]
                    add("reorder-side-effects", f"@{_offset(raw[j])}<->@{_offset(raw[i])}", _with(method, r))
            run = [i]
        if op in _NEGATE or op in ("goto", "goto_w", "tableswitch", "lookupswitch", "athrow") \
                or op.endswith("return"):
            run = []

    # 7/8. exception table: change a catch type / swap two overlapping rows
    decoded = _decoded(method)
    rows = list(method.get("raw_exception_rows") or [])
    if decoded is not None and rows:
        insns, idx_rows = decoded

        def effective(k):
            """Row k is reachable for some throwing instruction: it covers one
            that no EARLIER catch-all (`any`) row already covers. A row fully
            shadowed by earlier `any` rows is never selected, so changing it
            would be a semantic no-op and is not generated."""
            s, e, _h, _t = idx_rows[k]
            for x in range(s, min(e, len(insns))):
                if not n5_canon.can_throw(insns[x]):
                    continue
                if not any(idx_rows[j][3] == "any" and idx_rows[j][0] <= x < idx_rows[j][1] for j in range(k)):
                    return True
            return False

        for k, (frm, to, target, etype) in enumerate(rows):
            if not effective(k):
                continue
            new = "Class java/lang/IllegalStateException" if etype != "Class java/lang/IllegalStateException" \
                else "Class java/lang/Error"
            r2 = list(rows)
            r2[k] = (frm, to, target, new)
            add("change-catch-type", f"row {k} {etype}->{new}", _with(method, rows=r2))
        for k in range(len(rows) - 1):
            a, b = idx_rows[k], idx_rows[k + 1]
            overlap = any(n5_canon.can_throw(insns[x]) for x in range(max(a[0], b[0]), min(a[1], b[1], len(insns))))
            if overlap and (a[2], a[3]) != (b[2], b[3]) and effective(k) and effective(k + 1):
                r2 = list(rows)
                r2[k], r2[k + 1] = r2[k + 1], r2[k]
                add("reorder-exc-rows", f"rows {k}<->{k + 1}", _with(method, rows=r2))

    # 9. local-slot data flow: a store whose value is read by the next access
    #    of that slot in the same straight-line run goes to a different slot
    slots_by_kind: dict[str, set] = {}
    for i in idxs:
        _p, op, rest = _split(raw[i])
        sl = _slot(op, rest)
        if sl:
            slots_by_kind.setdefault(sl[0], set()).add(sl[1])
    max_slot = max((s for v in slots_by_kind.values() for s in v), default=0)
    for pos, i in enumerate(idxs):
        prefix, op, rest = _split(raw[i])
        sm = _STORE.match(op)
        if not sm:
            continue
        kind, slot = _slot(op, rest)
        read = False
        for j in idxs[pos + 1:]:
            if _offset(raw[j]) in leaders:
                break
            _pj, opj, restj = _split(raw[j])
            slj = _slot(opj, restj)
            if opj == "iinc" and re.match(rf"^\s*{slot}\b", restj):
                read = True
                break
            if slj and slj[1] == slot:
                read = _LOAD.match(opj) is not None
                break
            if opj in _NEGATE or opj.startswith(("goto", "tableswitch", "lookupswitch", "athrow")) \
                    or opj.endswith("return"):
                break
        if not read:
            continue
        others = sorted(s for s in slots_by_kind.get(kind, set()) if s != slot)
        for new_slot in others[:1] + [max_slot + 2]:
            if new_slot == slot:
                continue
            add("retarget-store", f"{op} {slot}->{new_slot} @{_offset(raw[i])}",
                _with(method, replace(i, f"{prefix}{kind}store {new_slot}")))
    return [x for bucket in out.values() for x in bucket]
