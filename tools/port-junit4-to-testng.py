#!/usr/bin/env python3
"""
port-junit4-to-testng.py — B29 reusable JUnit4 -> TestNG source-port recipe.

Mechanical port of a plain-Java (no Baja/BComponent) JUnit4 test file that uses only:
  import org.junit.Test;
  import static org.junit.Assert.*;
  assertTrue(...) / assertFalse(...) / assertNull(...) / assertNotNull(...) /
  assertSame(...) / assertNotSame(...) / assertEquals(...)

into a TestNG-annotated file:
  import org.testng.annotations.Test;
  import org.testng.Assert;
  Assert.assertTrue(...) / Assert.assertFalse(...) / ... / Assert.assertEquals(...)

THE ONE GENUINE GOTCHA THIS SCRIPT HANDLES (see niagara5-block29.md mapping table):
  JUnit4  assertEquals(expected, actual)                -> TestNG assertEquals(actual, expected)
  JUnit4  assertEquals(message, expected, actual)        -> TestNG assertEquals(actual, expected, message)
  (message position moves from FIRST to LAST; expected/actual swap position too).
A naive `sed 's/assertEquals(/Assert.assertEquals(/'` is INSUFFICIENT: it prefixes the
call correctly but leaves the argument order/position wrong, which is silently harmless
for a pure equality check's pass/fail outcome (equality is symmetric) but WRONG for what
TestNG reports as "expected" vs "actual" on failure, and OUTRIGHT WRONG (message swallowed
as a value / ClassCastException-shaped failure at test-execution time, not compile time,
if the message string were ever passed positionally where a value is expected) for the
3-argument message form. This script does a paren/bracket/string-literal-aware top-level
argument split before reordering, so it is correct on nested calls like
`assertEquals(interval, delay(interval, Long.MIN_VALUE, NOW))`.

Scope: this recipe is for PURE (no-Baja) JUnit4 tests only, per niagara5-block16.md's own
finding that porting a module's srcTest is a SEPARATE problem from porting src/ (JUnit4's
org.junit does not compile against N5's shipped `test` module at all, and TestNG's own
assertEquals(actual, expected[, message]) parameter order is a DIFFERENT ORDER than JUnit's,
which is the part a plain import-rename miss). It does NOT attempt to rewrite a test that
would need niagara.test.BTestNg lifecycle (@BeforeMethod/@AfterMethod, BComponent slots) --
none of the 5 ColdRoomPan-rt JUnit4 files need that (all pure static-method seam tests).

Usage: python3 port-junit4-to-testng.py <src.java> <dest.java>
"""
import re
import sys


def split_top_level_args(s: str):
    """Split a comma-separated argument list on TOP-LEVEL commas only, respecting
    (), [], {} nesting and "..."/'...' string/char literals with backslash escapes."""
    args = []
    depth = 0
    cur = []
    i = 0
    n = len(s)
    in_str = None  # None, '"' or "'"
    while i < n:
        c = s[i]
        if in_str:
            cur.append(c)
            if c == "\\" and i + 1 < n:
                cur.append(s[i + 1])
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c in "\"'":
            in_str = c
            cur.append(c)
        elif c in "([{":
            depth += 1
            cur.append(c)
        elif c in ")]}":
            depth -= 1
            cur.append(c)
        elif c == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    tail = "".join(cur).strip()
    if tail:
        args.append(tail)
    return args


def find_matching_paren(s: str, open_idx: int) -> int:
    """Given the index of an opening '(' in s, return the index of its matching ')'."""
    depth = 0
    i = open_idx
    in_str = None
    n = len(s)
    while i < n:
        c = s[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c in "\"'":
            in_str = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced parens")


def is_string_literal(arg: str) -> bool:
    a = arg.strip()
    return a.startswith('"')


def reorder_assert_equals_args(inner: str) -> str:
    """assertEquals / assertSame / assertNotSame: JUnit (expected, actual[, message]) with
    the message FIRST when present -> TestNG (actual, expected[, message]) with the message
    moved to LAST."""
    args = split_top_level_args(inner)
    if len(args) == 2:
        expected, actual = args
        return f"{actual}, {expected}"
    if len(args) == 3 and is_string_literal(args[0]):
        message, expected, actual = args
        return f"{actual}, {expected}, {message}"
    # 3-arg numeric-delta assertEquals(expected, actual, delta) form: not present in the
    # ColdRoomPan-rt corpus (grep-confirmed, niagara5-block29.md §29.x), but TestNG's delta
    # overload keeps the SAME (actual, expected, delta) shape as the 2-arg case for the
    # first two positions, so swap those two and leave delta last, unchanged.
    if len(args) == 3:
        expected, actual, delta = args
        return f"{actual}, {expected}, {delta}"
    # Fallback: unknown arity — leave untouched (flagged by the caller via a marker below).
    return inner


def reorder_message_last_args(inner: str) -> str:
    """assertTrue / assertFalse / assertNull / assertNotNull: JUnit puts an optional message
    FIRST — assertTrue(String message, boolean condition) — while TestNG's Assert class has
    NO (String, boolean) overload at all, only assertTrue(boolean) and
    assertTrue(boolean condition, String message) (message LAST). A bare `Assert.` prefix
    with no reorder is not just semantically backwards here, it is a COMPILE ERROR against
    TestNG's actual overload set (confirmed by javac output, niagara5-block29.md §29.x) —
    the single most important gotcha this recipe exists to catch."""
    args = split_top_level_args(inner)
    if len(args) == 2 and is_string_literal(args[0]):
        message, condition = args
        return f"{condition}, {message}"
    # 1-arg form (no message) is already correct as-is for both frameworks.
    return inner


# kind -> reorder function (None = no reorder needed, just prefix with Assert.)
ASSERT_KINDS = {
    "assertTrue": reorder_message_last_args,
    "assertFalse": reorder_message_last_args,
    "assertNull": reorder_message_last_args,
    "assertNotNull": reorder_message_last_args,
    "assertEquals": reorder_assert_equals_args,
    "assertSame": reorder_assert_equals_args,
    "assertNotSame": reorder_assert_equals_args,
    # TestNG's Assert class has NO assertArrayEquals method at all — arrays go through the
    # SAME overloaded assertEquals(actual[], expected[]) family, so the call is renamed to
    # assertEquals and reordered exactly like assertEquals (niagara5-block97.md §97.8, B29-G3).
    "assertArrayEquals": reorder_assert_equals_args,
}

# JUnit name -> TestNG name when they differ.
TESTNG_NAME = {"assertArrayEquals": "assertEquals"}

# One name list drives both the rewrite and the self-checks in main().
_ASSERT_NAMES = "|".join(ASSERT_KINDS)
ASSERT_CALL = re.compile(r'(?<!Assert\.)\b(' + _ASSERT_NAMES + r')\s*\(')
ANY_ASSERT_CALL = re.compile(r'\b(?:' + _ASSERT_NAMES + r')\s*\(')


def port_source(src: str) -> str:
    out = src

    out = out.replace("import org.junit.Test;", "import org.testng.annotations.Test;")
    out = out.replace("import static org.junit.Assert.*;", "import org.testng.Assert;")

    # Single pass, paren-aware: every assert* call is found, its balanced argument list is
    # extracted, reordered per its kind's TestNG signature (see the two reorder_* functions
    # above), and reassembled with an explicit Assert. prefix. Regex alone cannot do this
    # correctly because arguments can themselves be nested calls with their own commas
    # (e.g. `delay(interval, last, NOW)`), and because the message-position gotcha differs
    # by assertion kind (assertTrue/assertFalse/assertNull/assertNotNull: message LAST;
    # assertEquals/assertSame/assertNotSame: expected/actual swap AND message LAST).
    result = []
    pos = 0
    for m in ASSERT_CALL.finditer(out):
        start = m.start()
        if start < pos:
            continue  # already consumed inside a previous replacement span
        kind = m.group(1)
        open_idx = m.end() - 1  # index of the '(' just matched
        close_idx = find_matching_paren(out, open_idx)
        result.append(out[pos:start])
        inner = out[open_idx + 1:close_idx]
        reorder_fn = ASSERT_KINDS[kind]
        new_inner = reorder_fn(inner)
        result.append(f"Assert.{TESTNG_NAME.get(kind, kind)}({new_inner})")
        pos = close_idx + 1
    result.append(out[pos:])
    out = "".join(result)

    return out


def unported_calls(src: str) -> int:
    """Number of JUnit-style assert* calls left without an Assert. prefix (should be 0 after a port)."""
    return len(ASSERT_CALL.findall(src))


def exit_code(n_before: int, n_after: int, left: int) -> int:
    """0 when every assert* call survived the port and none is left without an Assert. prefix."""
    return 0 if n_before == n_after and left == 0 else 1


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    src_path, dest_path = sys.argv[1], sys.argv[2]
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()
    ported = port_source(src)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(ported)
    # assertArrayEquals is renamed to assertEquals, so count every known assert name on both sides.
    n_before = len(ANY_ASSERT_CALL.findall(src))
    n_after = len(ANY_ASSERT_CALL.findall(ported))
    left = unported_calls(ported)
    code = exit_code(n_before, n_after, left)
    print(f"{src_path} -> {dest_path}: {n_before} assert* calls in, {n_after} out, {left} unported "
          f"({'OK — count preserved, none unported' if code == 0 else 'MISMATCH — investigate'})")
    return code


if __name__ == "__main__":
    sys.exit(main())
