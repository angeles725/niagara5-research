#!/usr/bin/env python3
"""n5-bytecode-xref.py — bytecode-level cross-reference over the N5 extracted class files.

Answers structural questions straight from the vendor's class files (organized/<mod>/extracted/,
byte-identical to the installed jars per the T13 census), never from decompiled text:

  callers  <class> <method> [--desc D] [--cha]   invoke sites naming <class>.<method> (exact symbolic owner);
                                                 --cha also lists sites whose owner is a SUPERTYPE of <class>
                                                 (the call MAY dispatch to <class>'s override at run time)
  subtypes <class>                               transitive subclasses/implementors across every indexed module
  overriders <class> <method>                    <class> and its subtypes that DECLARE <method>
  casts    <class>                               instanceof->checkcast->astore sites with a LineNumberTable
                                                 verdict: `classic-separate-line` (a line entry starts between the
                                                 instanceof and the checkcast: the cast was its own statement) or
                                                 `pattern-or-same-line` (undecidable from bytecode alone)

Every line number printed is the ORIGINAL source line (LineNumberTable; Tridium ships -g), so a result can
be joined with docSource originals, SootUp/Joern output and Vineflower's `--__dump_original_lines__` view.

Why this exists (B118): the source-text call graph (module-navigator) reports 0 callers of
BRootHistoryFolder.getPermissions; the bytecode has 5 (3 in BFoxHistorySpace.navEvent, 2 in
BHistorySpace.getNavChildren), corroborated by SootUp 3.0.1 and Joern jimple2cpg. The `casts` verdict was
validated against the docSource originals: 326/326 classic sites flagged classic, 1 of 93 pattern sites
misflagged (a multi-line condition) — it is a heuristic with a measured error rate, not a proof.

Read-only. Pure stdlib. Limits: static symbolic references only — reflection, invokedynamic targets
(lambdas, method refs) and Sys.loadType-style string dispatch are not call edges here.
"""
import argparse
import json
import os
import struct
import sys

DEFAULT_ORGANIZED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "organized")

# opcode -> operand byte length (fixed-size); variable-size ones handled explicitly
_OPLEN = {}
for _op in list(range(0x00, 0x10)) + list(range(0x1a, 0x36)) + list(range(0x3b, 0x84)) + \
        list(range(0x85, 0x99)) + list(range(0xac, 0xb2)) + [0xbe, 0xbf, 0xc2, 0xc3, 0xca, 0xfe, 0xff]:
    _OPLEN[_op] = 0
for _op in [0x10, 0x12, 0x15, 0x16, 0x17, 0x18, 0x19, 0x36, 0x37, 0x38, 0x39, 0x3a, 0xa9, 0xbc]:
    _OPLEN[_op] = 1
for _op in [0x11, 0x13, 0x14, 0x84] + list(range(0x99, 0xa9)) + [0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8,
                                                                  0xbb, 0xbd, 0xc0, 0xc1, 0xc6, 0xc7]:
    _OPLEN[_op] = 2
_OPLEN[0xc5] = 3  # multianewarray
_OPLEN[0xb9] = 4  # invokeinterface
_OPLEN[0xba] = 4  # invokedynamic
_OPLEN[0xc8] = 4  # goto_w
_OPLEN[0xc9] = 4  # jsr_w
INVOKES = {0xb6: "invokevirtual", 0xb7: "invokespecial", 0xb8: "invokestatic", 0xb9: "invokeinterface"}
ASTORES = set([0x3a, 0x4b, 0x4c, 0x4d, 0x4e])


def parse_class(data):
    """Parse the parts of a class file this tool needs. Raises ValueError on non-class bytes."""
    if len(data) < 10 or data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("not a class file (bad magic)")
    minor, major, cpn = struct.unpack(">HHH", data[4:10])
    pos = 10
    cp = [None] * cpn
    i = 1
    while i < cpn:
        tag = data[pos]
        if tag == 1:
            ln = struct.unpack(">H", data[pos + 1:pos + 3])[0]
            cp[i] = ("utf8", data[pos + 3:pos + 3 + ln].decode("utf-8", "replace"))
            pos += 3 + ln
        elif tag in (3, 4):
            pos += 5
        elif tag in (5, 6):
            pos += 9
            i += 1
        elif tag in (7, 8, 16, 19, 20):
            cp[i] = (tag, struct.unpack(">H", data[pos + 1:pos + 3])[0])
            pos += 3
        elif tag in (9, 10, 11, 12, 17, 18):
            cp[i] = (tag,) + struct.unpack(">HH", data[pos + 1:pos + 5])
            pos += 5
        elif tag == 15:
            pos += 4
        else:
            raise ValueError("unknown constant-pool tag %d" % tag)
        i += 1

    def utf(k):
        return cp[k][1]

    def cls(k):
        return utf(cp[k][1])

    def member(k):
        _, ci, nti = cp[k]
        _, ni, di = cp[nti]
        return cls(ci), utf(ni), utf(di)

    access, this_c, super_c = struct.unpack(">HHH", data[pos:pos + 6])
    pos += 6
    nint = struct.unpack(">H", data[pos:pos + 2])[0]
    pos += 2
    interfaces = [cls(struct.unpack(">H", data[pos + 2 * j:pos + 2 * j + 2])[0]) for j in range(nint)]
    pos += 2 * nint

    def skip_attrs(p):
        n = struct.unpack(">H", data[p:p + 2])[0]
        p += 2
        for _ in range(n):
            ln = struct.unpack(">I", data[p + 2:p + 6])[0]
            p += 6 + ln
        return p

    nf = struct.unpack(">H", data[pos:pos + 2])[0]
    pos += 2
    for _ in range(nf):
        pos = skip_attrs(pos + 6)
    nm = struct.unpack(">H", data[pos:pos + 2])[0]
    pos += 2
    methods = []
    for _ in range(nm):
        macc, mni, mdi = struct.unpack(">HHH", data[pos:pos + 6])
        pos += 6
        na = struct.unpack(">H", data[pos:pos + 2])[0]
        pos += 2
        m = {"name": utf(mni), "desc": utf(mdi), "access": macc, "invokes": [], "insns": [], "lnt": []}
        for _ in range(na):
            ani, aln = struct.unpack(">HI", data[pos:pos + 6])
            body = data[pos + 6:pos + 6 + aln]
            pos += 6 + aln
            if utf(ani) != "Code":
                continue
            clen = struct.unpack(">I", body[4:8])[0]
            code = body[8:8 + clen]
            p = 8 + clen
            etl = struct.unpack(">H", body[p:p + 2])[0]
            p += 2 + 8 * etl
            nca = struct.unpack(">H", body[p:p + 2])[0]
            p += 2
            for _ in range(nca):
                cani, caln = struct.unpack(">HI", body[p:p + 6])
                if utf(cani) == "LineNumberTable":
                    n = struct.unpack(">H", body[p + 6:p + 8])[0]
                    for j in range(n):
                        spc, line = struct.unpack(">HH", body[p + 8 + 4 * j:p + 12 + 4 * j])
                        m["lnt"].append((spc, line))
                p += 6 + caln
            _walk(code, m, cp, member, cls)
        m["lnt"].sort()
        for s in m["invokes"]:
            s["line"] = line_at(m["lnt"], s["pc"])
        methods.append(m)
    return {"name": cls(this_c), "super": cls(super_c) if super_c else None, "interfaces": interfaces,
            "major": major, "minor": minor, "access": access, "methods": methods}


def _walk(code, m, cp, member, cls):
    pc = 0
    n = len(code)
    while pc < n:
        op = code[pc]
        if op == 0xaa:  # tableswitch
            p = (pc + 4) & ~3
            lo, hi = struct.unpack(">ii", code[p + 4:p + 12])
            m["insns"].append((pc, op, None))
            pc = p + 12 + 4 * (hi - lo + 1)
            continue
        if op == 0xab:  # lookupswitch
            p = (pc + 4) & ~3
            npairs = struct.unpack(">i", code[p + 4:p + 8])[0]
            m["insns"].append((pc, op, None))
            pc = p + 8 + 8 * npairs
            continue
        if op == 0xc4:  # wide
            inner = code[pc + 1]
            m["insns"].append((pc, op, inner))
            pc += 6 if inner == 0x84 else 4
            continue
        if op not in _OPLEN:
            raise ValueError("unknown opcode 0x%02x at pc %d" % (op, pc))
        arg = None
        if op in INVOKES:
            owner, name, desc = member(struct.unpack(">H", code[pc + 1:pc + 3])[0])
            m["invokes"].append({"pc": pc, "kind": INVOKES[op], "owner": owner, "name": name, "desc": desc})
        elif op in (0xc0, 0xc1):  # checkcast / instanceof
            arg = cls(struct.unpack(">H", code[pc + 1:pc + 3])[0])
        m["insns"].append((pc, op, arg))
        pc += 1 + _OPLEN[op]


def line_at(lnt, pc):
    best = None
    for spc, line in lnt:
        if spc <= pc:
            best = line
        else:
            break
    return best


def cast_sites(m):
    """instanceof T ... checkcast T; astore sites with the LineNumberTable verdict (see module doc)."""
    out = []
    ins = m["insns"]
    for i, (pc, op, arg) in enumerate(ins):
        if op != 0xc1:
            continue
        for j in range(i + 1, min(i + 6, len(ins) - 1)):
            if ins[j][1] == 0xc0 and ins[j][2] == arg and ins[j + 1][1] in ASTORES:
                iline = line_at(m["lnt"], pc)
                sep = [line for spc, line in m["lnt"] if pc < spc <= ins[j][0] and line != iline]
                out.append({"pc": pc, "type": arg, "line": iline, "cast_line": sep[-1] if sep else iline,
                            "verdict": "classic-separate-line" if sep else "pattern-or-same-line"})
                break
    return out


def _module_dirs(organized, modules=None):
    for name in sorted(os.listdir(organized)):
        if name.startswith("_") and name != "_bin-ext":
            continue
        if name == "_bin-ext":
            for sub in sorted(os.listdir(os.path.join(organized, name))):
                mod = "_bin-ext/" + sub
                if modules is None or mod in modules:
                    d = os.path.join(organized, name, sub, "extracted")
                    if os.path.isdir(d):
                        yield mod, d
            continue
        if modules is not None and name not in modules:
            continue
        d = os.path.join(organized, name, "extracted")
        if os.path.isdir(d):
            yield name, d


def build_index(organized, modules=None):
    """Parse every .class under <organized>/<mod>/extracted (optionally only `modules`).

    A class name seen in more than one module (R2-002: e.g. the same third-party jar vendored
    into two modules) is never silently dropped: the first-parsed copy is what structural
    queries (subtypes/callers/overriders) use, but every module it was seen in is recorded in
    `duplicates` so a caller can see and count the collision instead of losing it quietly.
    """
    classes = {}
    seen_in = {}
    errors = []
    for mod, root in _module_dirs(organized, modules):
        for d, _, files in os.walk(root):
            for f in files:
                if not f.endswith(".class") or f == "module-info.class":
                    continue
                p = os.path.join(d, f)
                try:
                    with open(p, "rb") as fh:
                        c = parse_class(fh.read())
                except (ValueError, struct.error, IndexError) as e:
                    errors.append((p, str(e)))
                    continue
                c["module"] = mod
                c["path"] = p
                seen_in.setdefault(c["name"], []).append(mod)
                classes.setdefault(c["name"], c)
    duplicates = {name: mods for name, mods in seen_in.items() if len(mods) > 1}
    children = {}
    for c in classes.values():
        for s in ([c["super"]] if c["super"] else []) + c["interfaces"]:
            children.setdefault(s, []).append(c["name"])
    return {"classes": classes, "children": children, "errors": errors, "duplicates": duplicates}


def _internal(name):
    return name.replace(".", "/")


def _dotted(name):
    return name.replace("/", ".")


def supertypes(idx, name):
    seen, stack = [], [_internal(name)]
    while stack:
        c = idx["classes"].get(stack.pop())
        if not c:
            continue
        for s in ([c["super"]] if c["super"] else []) + c["interfaces"]:
            if s not in seen:
                seen.append(s)
                stack.append(s)
    return seen


def subtypes(idx, name):
    seen, stack = set(), [_internal(name)]
    while stack:
        for ch in idx["children"].get(stack.pop(), []):
            if ch not in seen:
                seen.add(ch)
                stack.append(ch)
    return sorted(_dotted(s) for s in seen)


def _infer_desc(idx, name, method, desc):
    """Resolve the descriptor to filter on for (<name>, <method>): the explicit `desc` if given,
    else <name>'s own declaration of <method> IF that declaration is unambiguous (exactly one
    descriptor); otherwise None (every descriptor named <method> is accepted -- best effort when
    the base declaration is not indexed, e.g. an interface method with no body in <name> itself).

    Shared by overriders() (R2-001) and _inheriting_subtypes() (R2-002/R3-004): both need to tell
    a genuine override (same name AND descriptor) apart from an unrelated overload (same name,
    different descriptor) on a subtype, and a name-only comparison reports/accepts the overload as
    if it were the real thing."""
    if desc is not None:
        return desc
    base = idx["classes"].get(_internal(name))
    if base:
        base_descs = sorted(set(m["desc"] for m in base["methods"] if m["name"] == method))
        if len(base_descs) == 1:
            return base_descs[0]
    return None


def overriders(idx, name, method, desc=None):
    """<name> and its subtypes that DECLARE <method> (R2-001: name AND descriptor must match, not
    name alone -- otherwise an unrelated overload with the same name is reported as a false
    overrider). When `desc` is omitted, it is inferred from <name>'s own declaration of <method>
    if that declaration is unambiguous (exactly one descriptor); otherwise every descriptor named
    <method> is accepted, same as before (best effort when the base declaration is not indexed,
    e.g. an interface method with no body in <name> itself)."""
    desc = _infer_desc(idx, name, method, desc)
    out = []
    for c in [_internal(name)] + [_internal(s) for s in subtypes(idx, name)]:
        k = idx["classes"].get(c)
        if k and any(m["name"] == method and (desc is None or m["desc"] == desc) for m in k["methods"]):
            out.append(_dotted(c))
    return sorted(out)


def _inheriting_subtypes(idx, name, method, desc):
    """R3-001: internal names of subtypes of <name> whose invokevirtual/invokeinterface still
    dispatches to <name>'s own (method, desc) at run time -- i.e. no override of it exists between
    them and <name>. Descent stops at any subtype that redeclares (method, desc): its own
    descendants belong to THAT override, not to <name>'s.

    When `desc` is omitted, it is inferred the same way overriders() infers it (R2-002/R3-004):
    without this, a subtype that merely OVERLOADS <method> with an unrelated descriptor was wrongly
    treated as redeclaring it, stopping descent early and silently dropping every real
    subtype-owner candidate beneath that subtype."""
    desc = _infer_desc(idx, name, method, desc)
    out = []
    stack = list(idx["children"].get(_internal(name), []))
    while stack:
        c = stack.pop()
        k = idx["classes"].get(c)
        if not k:
            continue
        redeclares = any(m["name"] == method and (desc is None or m["desc"] == desc) for m in k["methods"])
        if redeclares:
            continue
        out.append(c)
        stack.extend(idx["children"].get(c, []))
    return out


def callers(idx, name, method, desc=None, cha=False):
    target = _internal(name)
    if target not in idx["classes"]:
        raise KeyError(name)
    owners = {target: "exact"}
    if cha:
        for s in supertypes(idx, name):
            owners.setdefault(s, "supertype-owner")
        for s in _inheriting_subtypes(idx, name, method, desc):
            owners.setdefault(s, "subtype-owner")
    out = []
    for c in idx["classes"].values():
        for m in c["methods"]:
            for s in m["invokes"]:
                if s["name"] == method and s["owner"] in owners and (desc is None or s["desc"] == desc):
                    out.append({"caller_class": _dotted(c["name"]), "caller_method": m["name"],
                                "caller_desc": m["desc"], "module": c["module"], "line": s["line"],
                                "invoke": s["kind"], "owner": _dotted(s["owner"]), "desc": s["desc"],
                                "kind": owners[s["owner"]]})
    out.sort(key=lambda r: (r["kind"] != "exact", r["caller_class"], r["caller_method"], r["line"] or 0))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--organized", default=DEFAULT_ORGANIZED)
    ap.add_argument("--module", action="append", help="restrict the index to these modules (repeatable)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("callers")
    p.add_argument("cls")
    p.add_argument("method")
    p.add_argument("--desc")
    p.add_argument("--cha", action="store_true")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("subtypes")
    p.add_argument("cls")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("overriders")
    p.add_argument("cls")
    p.add_argument("method")
    p.add_argument("--desc", help="require this exact method descriptor (disambiguates overloads; R2-001)")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("casts")
    p.add_argument("cls")
    p.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    idx = build_index(a.organized, a.module)
    # R4: every subcommand surfaces parse errors and duplicate class names in its own
    # output/summary -- never silently skipped -- while keeping existing CLI shape compatible
    # (these are additional keys/lines, nothing removed or renumbered).
    parse_errors = len(idx["errors"])
    duplicate_classes = len(idx["duplicates"])
    if _internal(a.cls) not in idx["classes"]:
        print("n5-bytecode-xref: class %s not found in %d indexed classes under %s "
              "(%d parse error(s), %d duplicate class name(s))" %
              (a.cls, len(idx["classes"]), a.organized, parse_errors, duplicate_classes), file=sys.stderr)
        return 2
    if a.cmd == "callers":
        res = {"target": a.cls + "." + a.method, "cha": a.cha, "indexed_classes": len(idx["classes"]),
               "parse_errors": parse_errors, "duplicate_classes": duplicate_classes,
               "sites": callers(idx, a.cls, a.method, a.desc, a.cha)}
        text = ["%s %s.%s%s:%s  -> %s.%s%s  [%s, %s]" % (r["kind"], r["caller_class"], r["caller_method"],
                                                         r["caller_desc"], r["line"], r["owner"], a.method,
                                                         r["desc"], r["invoke"], r["module"]) for r in res["sites"]]
        text.append("%d site(s); %d classes indexed; %d parse errors; %d duplicate class name(s)" %
                    (len(res["sites"]), res["indexed_classes"], parse_errors, duplicate_classes))
    elif a.cmd == "subtypes":
        res = {"target": a.cls, "subtypes": subtypes(idx, a.cls), "parse_errors": parse_errors,
               "duplicate_classes": duplicate_classes}
        text = res["subtypes"] + ["%d subtype(s); %d parse error(s); %d duplicate class name(s)" %
                                  (len(res["subtypes"]), parse_errors, duplicate_classes)]
    elif a.cmd == "overriders":
        declared_in = overriders(idx, a.cls, a.method, a.desc)
        # R2-003: "desc" is the raw --desc CLI argument (None when omitted); "resolved_desc" is
        # what was ACTUALLY filtered on, including a descriptor silently inferred from a.cls's own
        # unambiguous declaration -- without this, --json output for an inferred query looked
        # identical to one where every overload was accepted, with no way to tell which happened.
        res = {"target": a.cls + "." + a.method, "desc": a.desc,
               "resolved_desc": _infer_desc(idx, a.cls, a.method, a.desc),
               "declared_in": declared_in,
               "parse_errors": parse_errors, "duplicate_classes": duplicate_classes}
        text = declared_in + ["%d overrider(s); %d parse error(s); %d duplicate class name(s)" %
                              (len(declared_in), parse_errors, duplicate_classes)]
    else:
        c = idx["classes"][_internal(a.cls)]
        sites = [dict(s, method=m["name"]) for m in c["methods"] for s in cast_sites(m)]
        res = {"target": a.cls, "sites": sites, "parse_errors": parse_errors,
               "duplicate_classes": duplicate_classes}
        text = ["%s:%s instanceof %s -> cast line %s  %s" % (s["method"], s["line"], _dotted(s["type"]),
                                                             s["cast_line"], s["verdict"]) for s in sites]
        text.append("%d cast site(s); %d parse error(s); %d duplicate class name(s)" %
                    (len(sites), parse_errors, duplicate_classes))
    print(json.dumps(res, indent=1) if a.json else "\n".join(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
