#!/usr/bin/env python3
"""n5-patch-doprivileged.py -- mechanical, bytecode-evidenced disambiguation of
`SecurityUtil.doPrivileged(...)` calls in a decompiled N5 tree (T21/F8).

niagara.nre.util.SecurityUtil has six `doPrivileged` overloads (java.security.
PrivilegedAction / PrivilegedExceptionAction and four niagara.nre.security.
privileged.* interfaces). Vineflower emits the argument as an implicit lambda or
a method reference, which javac cannot target-type: "reference to doPrivileged
is ambiguous". The shipped bytecode says which overload the original source
bound to, so the fix is not a guess:

  * For every `invokestatic niagara/nre/util/SecurityUtil.doPrivileged:(L<iface>;)
    Ljava/lang/Object;` the interface is read from the descriptor; for a lambda or
    method reference the preceding `invokedynamic`'s LambdaMetafactory arguments
    give the instantiated method type, whose return type is erasure(T), and the
    lambda implementation method's `throws` gives the exception type arguments.
  * Source call sites are matched to bytecode call sites IN ORDER within the same
    method of the same class file (binary names computed like javac: members
    Outer$Inner, anonymous Outer$N verified against the class file's supertypes,
    local Outer$NName). Sites nested in lambdas are matched against the union of
    the class's lambda$<method>$N methods and only when every bytecode site of
    that pool carries the same evidence (order across lambda bodies is not
    recoverable). Any count or kind mismatch refuses the whole scope.
  * Only sites javac reports as ambiguous are patched; the only edit is an
    inserted cast `(<iface><T[, E...]>) ` in front of the argument. javac feedback
    (at most --max-iterations feedback compiles per class, plus one verification
    compile when the last step changed a cast) advances a site to its next
    candidate cast: an exception type named by an "unreported exception X" error
    inside the site, then the raw interface. Every other javac error is left
    alone and reported (`residual_errors`): it is a different decompiler defect.

Output: organized/<mod>/<out-tree>/<package>/<Class>.java for patched classes only,
plus organized/<mod>/<out-tree>/PATCHES.json (per class: sha256 of the original
and patched source, every patch site with its bytecode evidence, every refused
site with the reason). The input tree is only read.

The site scanner is tools/n5-patch-doprivileged/DoPrivilegedSites.java (javac
Tree API, parse only), compiled once into --helper-cache-dir.

Usage:
  python3 tools/n5-patch-doprivileged.py --modules bacnetAws,baja --tree vineflower2
  python3 tools/n5-patch-doprivileged.py --all --jobs 4 --tool-server
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
HELPER_SRC = TOOLS_DIR / "n5-patch-doprivileged" / "DoPrivilegedSites.java"

SECURITY_UTIL = "niagara/nre/util/SecurityUtil"
ALLOWED_QUALIFIERS = ("SecurityUtil", "niagara.nre.util.SecurityUtil", "")
# type-parameter count of each doPrivileged argument interface: T, then exception types
IFACE_ARITY = {
    "java/security/PrivilegedAction": 1,
    "java/security/PrivilegedExceptionAction": 1,
    "niagara/nre/security/privileged/PrivilegedAction": 1,
    "niagara/nre/security/privileged/PrivilegedExceptionAction": 1,
    "niagara/nre/security/privileged/PrivilegedSingleExceptionAction": 2,
    "niagara/nre/security/privileged/PrivilegedDoubleExceptionAction": 3,
}
MANIFEST_NAME = "PATCHES.json"
MANIFEST_SCHEMA = 1
DEFAULT_MAX_ITERATIONS = 4

_PRIMS = {"Z": "boolean", "B": "byte", "C": "char", "S": "short", "I": "int", "J": "long",
          "F": "float", "D": "double", "V": "void"}


def _load_fidelity():
    spec = importlib.util.spec_from_file_location("n5_fidelity_for_patch", TOOLS_DIR / "n5-fidelity.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# JVM names -> Java source names
# ---------------------------------------------------------------------------

def internal_name_to_source(name: str) -> Optional[str]:
    """`java/util/Map$Entry` -> `java.util.Map.Entry`. None for a name that has
    no source spelling (anonymous/local class: a `$` followed by a digit)."""
    if re.search(r"\$\d", name) or name.endswith("$"):
        return None
    return name.replace("/", ".").replace("$", ".")


def descriptor_to_source(desc: str) -> Optional[str]:
    """One field descriptor (`Ljava/lang/String;`, `[I`, ...) -> source type."""
    dims = 0
    while desc.startswith("["):
        dims += 1
        desc = desc[1:]
    if desc.startswith("L") and desc.endswith(";"):
        base = internal_name_to_source(desc[1:-1])
    elif desc in _PRIMS:
        base = _PRIMS[desc]
    else:
        return None
    return None if base is None else base + "[]" * dims


def split_method_descriptor(desc: str) -> tuple[list[str], str]:
    """`(ILjava/lang/String;[J)V` -> (['I', 'Ljava/lang/String;', '[J'], 'V')."""
    m = re.match(r"^\((.*)\)(.+)$", desc)
    if not m:
        raise ValueError(f"not a method descriptor: {desc!r}")
    params, i, body = [], 0, m.group(1)
    while i < len(body):
        j = i
        while body[j] == "[":
            j += 1
        if body[j] == "L":
            j = body.index(";", j)
        params.append(body[i:j + 1])
        i = j + 1
    return params, m.group(2)


def _simple_erased(type_text: str) -> str:
    """Source type text -> erased simple name (`java.util.Map<K, V>` -> `Map`,
    `String...` -> `String[]`)."""
    t = type_text.strip()
    depth, out = 0, []
    for ch in t:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    t = "".join(out).replace("...", "[]").replace(" ", "")
    dims = t.count("[]")
    base = t.replace("[]", "")
    base = re.sub(r"^.*\.", "", base)
    return base + "[]" * dims


def _descriptor_simple(desc: str) -> Optional[str]:
    src = descriptor_to_source(desc)
    if src is None:
        return None
    dims = src.count("[]")
    return re.sub(r"^.*\.", "", src.replace("[]", "")) + "[]" * dims


# ---------------------------------------------------------------------------
# javap -v -p parsing (only what the patcher needs)
# ---------------------------------------------------------------------------

@dataclass
class BytecodeSite:
    offset: int
    iface: str                              # internal name of the descriptor's parameter
    indy: bool = False                      # preceded by a LambdaMetafactory invokedynamic
    impl: Optional[str] = None              # implementation method handle (symbolic)
    instantiated_return: Optional[str] = None   # return descriptor of the instantiated method type
    impl_throws: Optional[list[str]] = None     # `throws` of a same-class lambda implementation
    checkcast: Optional[str] = None          # checkcast right after the call, if any

    def evidence(self) -> tuple:
        return (self.iface, self.indy, self.instantiated_return, tuple(self.impl_throws or ()))


@dataclass
class BytecodeMethod:
    name: str
    descriptor: str
    throws: list[str] = field(default_factory=list)
    sites: list[BytecodeSite] = field(default_factory=list)


@dataclass
class BytecodeClass:
    name: str                               # internal binary name
    supers: list[str] = field(default_factory=list)   # erased simple names of superclass + interfaces
    methods: list[BytecodeMethod] = field(default_factory=list)


_INSN_RE = re.compile(r"^\s+(\d+): (\w+)\b\s*(.*)$")
_DP_RE = re.compile(r"// Method " + re.escape(SECURITY_UTIL) + r"\.doPrivileged:\(L([\w/$]+);\)Ljava/lang/Object;")
_INDY_RE = re.compile(r"// InvokeDynamic #(\d+):")
_CHECKCAST_RE = re.compile(r"// class (\S+)")


def _strip_generics(text: str) -> str:
    depth, out = 0, []
    for ch in text:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def _parse_bootstraps(lines: list[str]) -> list[list[str]]:
    out: list[list[str]] = []
    in_table = False
    for line in lines:
        if line and not line.startswith(" "):
            in_table = line.startswith("BootstrapMethods:")
            continue
        if not in_table:
            continue
        m = re.match(r"^  (\d+): #\d+ (.*)$", line)
        if m:
            out.append([m.group(2)])
            continue
        m = re.match(r"^      #\d+ (.*)$", line)
        if m and out:
            out[-1].append(m.group(1))
    return out


def parse_javap_classes(text: str) -> dict[str, BytecodeClass]:
    """Parse the concatenated `javap -v -p` output of one or more class files."""
    chunks = re.split(r"(?m)^Classfile ", text)
    classes: dict[str, BytecodeClass] = {}
    for chunk in chunks:
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        this = next((re.search(r"// (\S+)$", l).group(1) for l in lines
                     if l.strip().startswith("this_class:") and re.search(r"// (\S+)$", l)), None)
        if this is None:
            continue
        bc = BytecodeClass(this)
        sup = next((re.search(r"// (\S+)$", l).group(1) for l in lines
                    if l.strip().startswith("super_class:") and re.search(r"// (\S+)$", l)), None)
        if sup:
            bc.supers.append(re.sub(r"^.*[/$]", "", sup))
        # interfaces from the declaration line (the line before "  minor version:")
        for i, l in enumerate(lines):
            if l.startswith("  minor version:"):
                decl = _strip_generics(lines[i - 1])
                if " implements " in decl:
                    for itf in decl.split(" implements ", 1)[1].split(","):
                        bc.supers.append(re.sub(r"^.*[.$]", "", itf.strip()))
                if " extends " in decl and "interface " in decl:
                    for itf in decl.split(" extends ", 1)[1].split(","):
                        bc.supers.append(re.sub(r"^.*[.$]", "", itf.strip()))
                break
        try:
            body_start = lines.index("{")
            body_end = len(lines) - 1 - lines[::-1].index("}")
        except ValueError:
            classes[this] = bc
            continue
        bootstraps = _parse_bootstraps(lines[body_end + 1:])
        member: Optional[BytecodeMethod] = None
        in_exceptions = False
        insns: list[tuple[int, str, str]] = []

        def flush():
            if member is None:
                return
            prev = None
            for k, (off, op, rest) in enumerate(insns):
                m = _DP_RE.search(rest) if op == "invokestatic" else None
                if m:
                    site = BytecodeSite(offset=off, iface=m.group(1))
                    if prev is not None and prev[1] == "invokedynamic":
                        im = _INDY_RE.search(prev[2])
                        bsm = bootstraps[int(im.group(1))] if im and int(im.group(1)) < len(bootstraps) else None
                        if bsm and "LambdaMetafactory" in bsm[0] and len(bsm) >= 4:
                            site.indy = True
                            site.impl = bsm[2]
                            try:
                                site.instantiated_return = split_method_descriptor(bsm[3])[1]
                            except ValueError:
                                site.instantiated_return = None
                    if k + 1 < len(insns) and insns[k + 1][1] == "checkcast":
                        cm = _CHECKCAST_RE.search(insns[k + 1][2])
                        site.checkcast = cm.group(1).strip('"') if cm else None
                    member.sites.append(site)
                prev = (off, op, rest)

        for line in lines[body_start + 1:body_end]:
            if re.match(r"^  \S", line):
                flush()
                member = None
                insns = []
                in_exceptions = False
                continue
            s = line.strip()
            if s.startswith("descriptor:") and member is None and re.match(r"^    descriptor:", line):
                member = BytecodeMethod(name="", descriptor=s.split(":", 1)[1].strip())
                bc.methods.append(member)
                continue
            if member is None:
                continue
            if re.match(r"^    Exceptions:", line):
                in_exceptions = True
                continue
            if in_exceptions and s.startswith("throws "):
                member.throws = [t.strip() for t in s[len("throws "):].split(",")]
                in_exceptions = False
                continue
            # javap right-aligns offsets in a 10-column field: the indent
            # shrinks as the offset grows (`     65000:`), so no indent test
            m = _INSN_RE.match(line)
            if m:
                insns.append((int(m.group(1)), m.group(2), m.group(3)))
        flush()
        # method names come from the member declaration lines
        names = _member_names(lines[body_start + 1:body_end], this)
        methods = [m for m in bc.methods if m.descriptor.startswith("(")]
        for meth, name in zip(methods, names):
            meth.name = name
        bc.methods = methods
        classes[this] = bc
    # same-class lambda implementation throws
    for bc in classes.values():
        by_key = {(bc.name, m.name, m.descriptor): m for m in bc.methods}
        for meth in bc.methods:
            for site in meth.sites:
                if site.impl:
                    im = re.match(r"^REF_\w+ ([\w/$]+)\.([\w$<>]+):(\(.*)$", site.impl)
                    if im and (im.group(1), im.group(2), im.group(3)) in by_key:
                        site.impl_throws = list(by_key[(im.group(1), im.group(2), im.group(3))].throws)
    return classes


def _member_names(body_lines: list[str], this: str) -> list[str]:
    """Names of the method members in declaration order (fields skipped). javap
    declares a constructor with the class's dotted binary name."""
    names = []
    dotted = this.replace("/", ".")
    for i, line in enumerate(body_lines):
        if not re.match(r"^  \S", line):
            continue
        nxt = body_lines[i + 1].strip() if i + 1 < len(body_lines) else ""
        if not nxt.startswith("descriptor: ("):
            continue
        decl = _strip_generics(line.strip())
        if decl.startswith("static {}"):
            names.append("<clinit>")
            continue
        m = re.search(r"([\w$.]+)\(", decl)
        name = m.group(1) if m else "?"
        names.append("<init>" if name == dotted or "." in name else name)
    return names


# ---------------------------------------------------------------------------
# Source side (DoPrivilegedSites.java output) -> javac binary names and scopes
# ---------------------------------------------------------------------------

def binary_names(classes: list[dict], package: str) -> dict[int, str]:
    """javac's flat names for the scanner's class bodies (ids are pre-order):
    member Outer$Inner, anonymous Outer$<n> (n-th anonymous body whose innermost
    enclosing class is Outer), local Outer$<n><Name>."""
    out: dict[int, str] = {}
    anon_count: dict[int, int] = {}
    local_count: dict[tuple[int, str], int] = {}
    prefix = package.replace(".", "/") + "/" if package else ""
    for c in sorted(classes, key=lambda c: c["id"]):
        if c["kind"] == "top":
            out[c["id"]] = prefix + c["name"]
        elif c["kind"] == "member":
            out[c["id"]] = out[c["parent"]] + "$" + c["name"]
        elif c["kind"] == "anon":
            anon_count[c["parent"]] = anon_count.get(c["parent"], 0) + 1
            out[c["id"]] = out[c["parent"]] + "$" + str(anon_count[c["parent"]])
        else:
            key = (c["parent"], c["name"])
            local_count[key] = local_count.get(key, 0) + 1
            out[c["id"]] = out[c["parent"]] + "$" + str(local_count[key]) + c["name"]
    return out


def _lambda_pool_name(member: dict) -> Optional[str]:
    kind = member.get("kind")
    if kind == "method":
        return member["name"]
    if kind in ("ctor", "instinit"):
        return "new"
    if kind == "clinit":
        return "static"
    return None


def _resolve_method(bc: BytecodeClass, member: dict) -> tuple[Optional[BytecodeMethod], Optional[str]]:
    kind = member.get("kind")
    if kind == "clinit":
        ms = [m for m in bc.methods if m.name == "<clinit>"]
        return (ms[0], None) if len(ms) == 1 else (None, "no-clinit")
    if kind == "instinit":
        return None, "instance-initializer"
    if kind not in ("method", "ctor"):
        return None, f"member-kind-{kind}"
    name = "<init>" if kind == "ctor" else member["name"]
    want = [_simple_erased(p) for p in member["params"]]
    # rank 0: erased simple parameter names equal; rank 1 (constructors only):
    # equal after javac's leading synthetic parameters (outer instance, enum
    # name/ordinal); rank 2: same arity / any constructor. The best rank must
    # hold exactly one method.
    cands = []
    for m in bc.methods:
        if m.name != name:
            continue
        params = [_descriptor_simple(p) for p in split_method_descriptor(m.descriptor)[0]]
        if params == want:
            cands.append((0, m))
        elif kind == "ctor" and len(params) > len(want) and params[len(params) - len(want):] == want:
            cands.append((1, m))
        elif kind == "ctor" or len(params) == len(want):
            cands.append((2, m))
    for rank in (0, 1, 2):
        group = [m for r, m in cands if r == rank]
        if len(group) == 1:
            return group[0], None
        if group:
            break
    return None, "overload-unresolved" if cands else "method-not-found"


def _anon_verified(bc: Optional[BytecodeClass], cls: dict) -> bool:
    if bc is None:
        return False
    if cls["kind"] != "anon":
        return True
    want = _simple_erased(cls["supers"][0]) if cls["supers"] else None
    return want is not None and want in bc.supers


# ---------------------------------------------------------------------------
# Matching: source sites <-> bytecode sites
# ---------------------------------------------------------------------------

def match_sites(scan: dict, package: str, bytecode: dict[str, BytecodeClass]) -> tuple[dict[int, dict], list[dict]]:
    """Return ({inv_start: {site, bytecode_site, class, method, index}}, refused).

    `refused` lists every doPrivileged site (lambda/method-ref argument) that has
    no unambiguous bytecode partner, with the reason."""
    names = binary_names(scan["classes"], package)
    classes = {c["id"]: c for c in scan["classes"]}
    sites = [s for s in scan["sites"] if s["qualifier"] in ALLOWED_QUALIFIERS and s["nargs"] == 1]
    scopes: dict[tuple, list[dict]] = {}
    refused: list[dict] = []
    for s in sites:
        member = s.get("member") or {}
        if s["lambda_depth"] > 0:
            pool = _lambda_pool_name(member)
            key = ("lambda", s["class_id"], pool)
        else:
            key = ("method", s["class_id"], json.dumps(member, sort_keys=True))
        scopes.setdefault(key, []).append(s)

    matched: dict[int, dict] = {}

    def refuse(group, reason, **extra):
        for s in group:
            if s["arg_kind"] in ("LAMBDA_EXPRESSION", "MEMBER_REFERENCE"):
                refused.append({"inv_start": s["inv_start"], "reason": reason, **extra})

    for key, group in scopes.items():
        group.sort(key=lambda s: s["inv_start"])
        cls = classes.get(key[1])
        binary = names.get(key[1])
        bc = bytecode.get(binary) if binary else None
        if cls is None or not _anon_verified(bc, cls):
            refuse(group, "class-file-unmatched", binary=binary)
            continue
        if key[0] == "method":
            member = group[0].get("member") or {}
            meth, why = _resolve_method(bc, member)
            if meth is None:
                refuse(group, why, binary=binary)
                continue
            bsites = [(meth, i, b) for i, b in enumerate(meth.sites)]
        else:
            pool = key[2]
            if pool is None:
                refuse(group, "lambda-pool-unknown", binary=binary)
                continue
            lam = [m for m in bc.methods if re.fullmatch(r"lambda\$" + re.escape(pool) + r"\$\d+", m.name)]
            bsites = [(m, i, b) for m in lam for i, b in enumerate(m.sites)]
            if len({b.evidence() for _, _, b in bsites}) > 1:
                refuse(group, "lambda-pool-mixed-evidence", binary=binary,
                       source_count=len(group), bytecode_count=len(bsites))
                continue
        if len(bsites) != len(group):
            refuse(group, "count-mismatch", binary=binary, source_count=len(group), bytecode_count=len(bsites))
            continue
        kinds_ok = all((s["arg_kind"] in ("LAMBDA_EXPRESSION", "MEMBER_REFERENCE")) == b.indy
                       for s, (_, _, b) in zip(group, bsites))
        if not kinds_ok:
            refuse(group, "argument-kind-mismatch", binary=binary)
            continue
        for s, (meth, idx, b) in zip(group, bsites):
            matched[s["inv_start"]] = {"site": s, "bytecode": b, "class": binary,
                                       "method": meth.name + meth.descriptor, "index": idx,
                                       "scope": key[0]}
    return matched, refused


# ---------------------------------------------------------------------------
# Casts and source rewriting
# ---------------------------------------------------------------------------

def cast_candidates(b: BytecodeSite) -> list[dict]:
    """Ordered cast candidates for one bytecode site: the fully evidenced
    parameterization first, the raw interface last."""
    iface_src = internal_name_to_source(b.iface)
    arity = IFACE_ARITY.get(b.iface)
    if iface_src is None or arity is None:
        return []
    out = []
    t = descriptor_to_source(b.instantiated_return) if b.instantiated_return else None
    if t is not None and t not in _PRIMS.values():
        excs = []
        if arity > 1:
            thrown = [x for x in (b.impl_throws or [])]
            if len(thrown) >= arity - 1:
                excs = thrown[:arity - 1]
            elif len(thrown) == 1:
                excs = thrown * (arity - 1)
            else:
                excs = ["java.lang.RuntimeException"] * (arity - 1)
        out.append({"type_args": [t] + excs})
    out.append({"type_args": None})
    return [dict(c, iface=iface_src) for c in out]


def cast_text(candidate: dict) -> str:
    if candidate["type_args"]:
        return f"({candidate['iface']}<{', '.join(candidate['type_args'])}>) "
    return f"({candidate['iface']}) "


def render(original: str, insertions: dict[int, str]) -> str:
    out, last = [], 0
    for pos in sorted(insertions):
        out.append(original[last:pos])
        out.append(insertions[pos])
        last = pos
    out.append(original[last:])
    return "".join(out)


def rendered_to_original(offset: int, insertions: dict[int, str]) -> int:
    shift = 0
    for pos in sorted(insertions):
        rp = pos + shift
        n = len(insertions[pos])
        if offset >= rp + n:
            shift += n
        elif offset >= rp:
            return pos
        else:
            break
    return offset - shift


_JAVAC_ERR_RE = re.compile(r"^(.*\.java):(\d+): error: (.*)$")


def parse_javac_errors(stderr: str, text: str) -> list[dict]:
    """[{offset, message}] for every javac error, offset into `text` (the caret
    column is the character index within the line)."""
    line_starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            line_starts.append(i + 1)
    lines = stderr.splitlines()
    out = []
    for i, l in enumerate(lines):
        m = _JAVAC_ERR_RE.match(l)
        if not m:
            continue
        lineno = int(m.group(2))
        col = None
        for j in range(i + 1, min(i + 4, len(lines))):
            if lines[j].rstrip().endswith("^") and set(lines[j].rstrip()[:-1]) <= {" ", "\t"}:
                col = len(lines[j].rstrip()) - 1
                break
        if col is None or lineno - 1 >= len(line_starts):
            continue
        out.append({"offset": line_starts[lineno - 1] + col, "message": m.group(3)})
    return out


_UNREPORTED_RE = re.compile(r"unreported exception ([\w.$]+); must be caught or declared to be thrown")


def patch_source(original: str, matched: dict[int, dict], compile_fn, max_iterations: int) -> dict:
    """javac-feedback loop for one source file. `compile_fn(text) -> stderr`
    ('' when it compiles). Returns {text, patches, unresolved, iterations}."""
    chosen: dict[int, int] = {}          # inv_start -> candidate index
    cand: dict[int, list[dict]] = {}
    history: dict[int, list[str]] = {}
    unresolved: list[dict] = []
    iterations = 0
    stderr = ""
    changed = False
    for iterations in range(1, max_iterations + 1):
        insertions = {matched[k]["site"]["arg_start"]: cast_text(cand[k][chosen[k]]) for k in chosen}
        text = render(original, insertions)
        stderr = compile_fn(text)
        errors = parse_javac_errors(stderr, text)
        changed = False
        unresolved = []
        for e in errors:
            e["orig"] = rendered_to_original(e["offset"], insertions)
        for e in errors:
            if "reference to doPrivileged is ambiguous" not in e["message"]:
                continue
            site = next((s for s in _all_sites(matched) if s["inv_start"] <= e["orig"] < max(s["arg_start"], s["inv_start"] + 1)), None)
            key = site["inv_start"] if site else None
            if key is None or key not in matched:
                unresolved.append({"offset": e["orig"], "reason": "ambiguous-site-unmatched"})
                continue
            if key in chosen:
                continue
            cs = cast_candidates(matched[key]["bytecode"])
            if not cs:
                unresolved.append({"offset": e["orig"], "reason": "no-cast-evidence"})
                continue
            cand[key], chosen[key] = cs, 0
            history.setdefault(key, []).append(cast_text(cs[0]).strip())
            changed = True
        for key in list(chosen):
            s = matched[key]["site"]
            inside = [e for e in errors if s["inv_start"] <= e["orig"] < s["inv_end"]
                      and "reference to doPrivileged is ambiguous" not in e["message"]]
            if not inside:
                continue
            cur = cand[key][chosen[key]]
            unrep = next((_UNREPORTED_RE.search(e["message"]) for e in inside if _UNREPORTED_RE.search(e["message"])), None)
            nxt = None
            if unrep and cur["type_args"] and len(cur["type_args"]) > 1:
                exc = unrep.group(1)
                if exc not in cur["type_args"][1:]:
                    nxt = dict(cur, type_args=[cur["type_args"][0]] + [exc] * (len(cur["type_args"]) - 1))
                    cand[key].insert(chosen[key] + 1, nxt)
            if nxt is None and chosen[key] + 1 >= len(cand[key]):
                continue
            chosen[key] += 1
            history[key].append(cast_text(cand[key][chosen[key]]).strip())
            changed = True
        if not changed:
            break
    insertions = {matched[k]["site"]["arg_start"]: cast_text(cand[k][chosen[k]]) for k in chosen}
    final_text = render(original, insertions)
    if changed:
        # the last feedback step changed a cast: verify what is actually emitted
        stderr = compile_fn(final_text)
    final_errors = parse_javac_errors(stderr, final_text)
    patches = []
    for key in sorted(chosen):
        m = matched[key]
        b = m["bytecode"]
        patches.append({
            "inv_start": key, "arg_start": m["site"]["arg_start"], "inserted": cast_text(cand[key][chosen[key]]),
            "arg_kind": m["site"]["arg_kind"], "class": m["class"], "method": m["method"],
            "bytecode_site_index": m["index"], "scope": m["scope"],
            "evidence": {"invokestatic_iface": b.iface, "indy_impl": b.impl,
                         "instantiated_return": b.instantiated_return, "impl_throws": b.impl_throws,
                         "checkcast": b.checkcast},
            "candidates_tried": history.get(key, []),
        })
    line_of = lambda off: final_text.count("\n", 0, off) + 1  # noqa: E731
    return {"text": final_text, "patches": patches, "unresolved": unresolved,
            "iterations": iterations, "compiles": stderr.strip() == "" if chosen else None,
            "residual_errors": [{"line": line_of(e["offset"]), "message": e["message"][:200]}
                                for e in final_errors[:10]],
            "residual_error_count": len(final_errors)}


def _all_sites(matched: dict[int, dict]):
    return [m["site"] for m in matched.values()]


# ---------------------------------------------------------------------------
# Tools: site scanner, javap, javac
# ---------------------------------------------------------------------------

def compile_helper(cache_dir: Path, javac_bin: str) -> Path:
    cache_dir = Path(cache_dir)
    stamp = hashlib.sha256(HELPER_SRC.read_bytes()).hexdigest()[:16]
    out = cache_dir / f"helper-{stamp}"
    if not (out / "DoPrivilegedSites.class").is_file():
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run([javac_bin, "-d", str(out), str(HELPER_SRC)], check=True, capture_output=True, text=True)
    return out


def scan_sources(files: list[Path], helper_dir: Path, java_bin: str) -> dict[str, dict]:
    if not files:
        return {}
    proc = subprocess.run([java_bin, "-cp", str(helper_dir), "DoPrivilegedSites", *map(str, files)],
                          capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"DoPrivilegedSites failed: {proc.stderr.strip()[:500]}")
    out = {}
    for line in proc.stdout.splitlines():
        if line.strip():
            d = json.loads(line)
            out[d["file"]] = d
    return out


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def patch_class(fqcn: str, src_path: Path, extracted_dir: Path, scan: dict, *, classpath: str, fid,
                javac_bin: str, javap_bin: str, tool_server: bool, max_iterations: int) -> Optional[dict]:
    """Patch one top-level class. Returns the manifest record (with the patched
    text under `_text`), or None when the source has no ambiguous doPrivileged."""
    original = src_path.read_text(encoding="utf-8")
    if any(ord(ch) > 0xFFFF for ch in original):
        return {"skipped": "non-BMP characters (javac offsets are UTF-16)"}
    top = extracted_dir / f"{fqcn}.class"
    class_files = [top] + sorted(top.parent.glob(top.stem + "$*.class"))
    rc, out, err = fid._run_jdk_tool("javap", javap_bin, ["-v", "-p", *map(str, class_files)], 120, tool_server)
    bytecode = parse_javap_classes(out)
    package = fqcn.rsplit("/", 1)[0].replace("/", ".") if "/" in fqcn else ""
    matched, refused = match_sites(scan, package, bytecode)
    class_short = fqcn.rsplit("/", 1)[-1]

    def compile_fn(text: str) -> str:
        with tempfile.TemporaryDirectory(prefix=f"n5dp-{class_short}-") as td:
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

    result = patch_source(original, matched, compile_fn, max_iterations)
    if not result["patches"]:
        amb = [u for u in result["unresolved"]]
        if not amb:
            return None
    ambiguous_refused = []
    line_of = lambda off: original.count("\n", 0, off) + 1  # noqa: E731
    for r in refused:
        ambiguous_refused.append(dict(r, line=line_of(r["inv_start"])))
    for p in result["patches"]:
        p["line"] = line_of(p["inv_start"])
    return {
        "original_sha256": sha256_text(original),
        "patched_sha256": sha256_text(result["text"]),
        "patches": result["patches"],
        "refused": ambiguous_refused,
        "unresolved_ambiguous": result["unresolved"],
        "javac_iterations": result["iterations"],
        "residual_errors": result["residual_errors"],
        "residual_error_count": result["residual_error_count"],
        "compiles": result["compiles"],
        "_text": result["text"],
    }


def patch_module(module: str, organized_dir: Path, tree: str, out_tree: str, *, classpath: str, fid,
                 helper_dir: Path, javac_bin: str, javap_bin: str, java_bin: str, tool_server: bool,
                 max_iterations: int, class_jobs: int = 1) -> dict:
    mod_dir = Path(organized_dir) / module
    tree_dir = mod_dir / tree
    extracted = mod_dir / "extracted"
    files = sorted(p for p in tree_dir.rglob("*.java")
                   if "$" not in p.name and "doPrivileged(" in p.read_text(encoding="utf-8", errors="replace"))
    scans = scan_sources(files, helper_dir, java_bin)
    out_dir = mod_dir / out_tree
    records: dict[str, dict] = {}

    def one(p: Path):
        fqcn = p.relative_to(tree_dir).with_suffix("").as_posix()
        scan = scans.get(str(p))
        if scan is None or not (extracted / f"{fqcn}.class").is_file():
            return fqcn, None
        return fqcn, patch_class(fqcn, p, extracted, scan, classpath=classpath, fid=fid, javac_bin=javac_bin,
                                 javap_bin=javap_bin, tool_server=tool_server, max_iterations=max_iterations)

    if class_jobs > 1 and len(files) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=class_jobs) as pool:
            results = list(pool.map(one, files))
    else:
        results = [one(p) for p in files]
    for fqcn, rec in results:
        if rec is not None and rec.get("patches"):
            records[fqcn] = rec
        elif rec is not None and (rec.get("unresolved_ambiguous") or rec.get("skipped")):
            records[fqcn] = rec
    # write: only classes with at least one patch get a source file
    if out_dir.is_dir():
        for old in out_dir.rglob("*.java"):
            old.unlink()
    for fqcn, rec in records.items():
        text = rec.pop("_text", None)
        if text is not None and rec.get("patches"):
            dest = out_dir / f"{fqcn}.java"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "module": module,
        "source_tree": tree,
        "tool": "tools/n5-patch-doprivileged.py",
        "helper_sha256": hashlib.sha256(HELPER_SRC.read_bytes()).hexdigest(),
        "max_iterations": max_iterations,
        "scanned_files": len(files),
        "classes": records,
    }
    if records or out_dir.is_dir():
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def main(argv: Optional[list[str]] = None) -> int:
    fid = _load_fidelity()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modules")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--organized-dir", default=str(fid.DEFAULT_ORGANIZED_DIR))
    ap.add_argument("--tree", default="vineflower2")
    ap.add_argument("--out-tree", default=None, help="default: <tree>p")
    ap.add_argument("--modules-dir", default=str(fid.DEFAULT_MODULES_DIR))
    ap.add_argument("--bin-ext-dir", default=str(fid.DEFAULT_BIN_EXT_DIR))
    ap.add_argument("--jre-dir", default=str(fid.DEFAULT_JRE_DIR))
    ap.add_argument("--bc-variant", choices=fid.BC_VARIANTS, default=fid.DEFAULT_BC_VARIANT)
    ap.add_argument("--classpath-cache-dir", default=None)
    ap.add_argument("--helper-cache-dir", default=None)
    ap.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--class-jobs", type=int, default=1)
    ap.add_argument("--tool-server", action="store_true")
    args = ap.parse_args(argv)
    organized = Path(args.organized_dir)
    if args.all:
        modules = [p.name for p in sorted(organized.iterdir())
                   if p.is_dir() and not p.name.startswith("_") and (p / args.tree).is_dir()]
    elif args.modules:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    else:
        ap.error("pass --modules a,b or --all")
    out_tree = args.out_tree or args.tree + "p"
    tmp = Path(tempfile.gettempdir())
    cache = Path(args.classpath_cache_dir) if args.classpath_cache_dir else tmp / "n5-fidelity-classpath-cache"
    classpath = fid.build_classpath(cache, Path(args.modules_dir), Path(args.bin_ext_dir), bc_variant=args.bc_variant,
                                    jre_dir=Path(args.jre_dir) if args.jre_dir else None)
    helper = compile_helper(Path(args.helper_cache_dir) if args.helper_cache_dir else tmp / "n5-patch-doprivileged",
                            fid.DEFAULT_JAVAC)
    failed = []

    def run(module: str):
        try:
            man = patch_module(module, organized, args.tree, out_tree, classpath=classpath, fid=fid,
                               helper_dir=helper, javac_bin=fid.DEFAULT_JAVAC, javap_bin=fid.DEFAULT_JAVAP,
                               java_bin=fid.DEFAULT_JAVA, tool_server=args.tool_server,
                               max_iterations=args.max_iterations, class_jobs=args.class_jobs)
            n_p = sum(len(r.get("patches", [])) for r in man["classes"].values())
            n_r = sum(len(r.get("refused", [])) for r in man["classes"].values())
            n_c = sum(1 for r in man["classes"].values() if r.get("patches"))
            print(f"[{module}] scanned {man['scanned_files']} patched-classes {n_c} sites {n_p} refused {n_r}",
                  file=sys.stderr, flush=True)
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
