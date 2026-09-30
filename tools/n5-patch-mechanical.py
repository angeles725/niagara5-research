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


def fix_pattern_binding_scope(lines: list[str], errors: list[dict]):
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


def fix_foreach_raw_cast(lines: list[str], errors: list[dict]):
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


def fix_boolean_declared_int(lines: list[str], errors: list[dict]):
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


def fix_instanceof_generic_raw(lines: list[str], errors: list[dict]):
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


FIXERS: list[tuple[str, Callable]] = [
    ("pattern-binding-scope", fix_pattern_binding_scope),
    ("foreach-raw-cast", fix_foreach_raw_cast),
    ("boolean-declared-int", fix_boolean_declared_int),
    ("instanceof-generic-raw", fix_instanceof_generic_raw),
]


def patch_source(original: str, compile_fn: Callable[[str], str], fixers=None, max_rounds: int = MAX_ROUNDS) -> dict:
    """Apply fixers driven by javac feedback. `compile_fn(text) -> ''` on success, else stderr.
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
            got = fn(lines, errors)
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
