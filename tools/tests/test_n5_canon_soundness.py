"""Fail-closed soundness suite for tools/n5_canon.py.

Semantic mutations (tools/tests/n5_canon_mutations.py: negated conditions,
swapped operands of non-commutative ops, changed constants, changed field/
method references, deleted calls, reordered side effects, changed catch
types, reordered overlapping exception rows, re-targeted stores) are applied
to (a) ~40 real SHIPPED methods from several modules of the N5 corpus
(organized/<mod>/extracted, javap'd at test time; skipped when the corpus is
absent) and (b) the recompiled side of the real javac-25 pairs that the
canonical rules prove equal. Every mutant must canonicalize DIFFERENTLY from
the original under the full rule set and under tier 1 alone: a surviving
mutant is a soundness bug in a rule. The kill rate is printed to stderr.
"""
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import n5_canon  # noqa: E402
from n5_canon_mutations import mutations  # noqa: E402
from test_n5_canon import JDK25_JAVAP, _jdk_available, _load_fidelity, javac_methods  # noqa: E402

CORPUS_MODULES = ("haystack", "box", "batchJob", "bql", "alarm", "baja", "control")
METHODS_PER_MODULE = 7
MIN_INSNS, MAX_INSNS = 12, 400
_BRANCH_LINE = re.compile(r"^\s*\d+:\s*(if\w+|goto\w*|tableswitch|lookupswitch)\b")


def _corpus_dir():
    for cand in (os.environ.get("N5_ORGANIZED_DIR"), HERE.parent.parent / "organized",
                 Path.home() / "niagara5-research" / "organized"):
        if cand and Path(cand, "haystack", "extracted").is_dir():
            return Path(cand)
    return None


def _pick_corpus_methods():
    """Deterministic sample: per module, classes in sorted path order, methods
    with a branch and MIN..MAX instructions, preferring ones that have an
    exception table, until METHODS_PER_MODULE are taken."""
    fid = _load_fidelity()
    root = _corpus_dir()
    picked = []
    for module in CORPUS_MODULES:
        extracted = root / module / "extracted"
        if not extracted.is_dir():
            continue
        with_rows, without = [], []
        for cls in sorted(extracted.rglob("*.class"))[:60]:
            try:
                text = fid.run_javap_verbose(str(cls), javap_bin=JDK25_JAVAP)
            except subprocess.TimeoutExpired:
                continue
            for (name, desc), meth in fid.parse_javap_verbose(text)["methods"].items():
                raw = meth["raw_code"]
                if not (MIN_INSNS <= len(raw) <= MAX_INSNS):
                    continue
                if not any(_BRANCH_LINE.match(line) for line in raw):
                    continue
                label = f"{module}/{cls.relative_to(extracted)}::{name}{desc}"
                (with_rows if meth["raw_exception_rows"] else without).append((label, meth))
            if len(with_rows) >= METHODS_PER_MODULE:
                break
        take = with_rows[:METHODS_PER_MODULE // 2 + 1]
        take += without[:METHODS_PER_MODULE - len(take)]
        picked.extend(take)
    return picked


def _check(testcase, pairs):
    """pairs: [(label, original, mutant-source)] where every mutant of
    mutant-source must canonicalize differently from `original`."""
    total, killed, unsupported = 0, 0, 0
    per_kind: dict = {}
    survivors = []
    for label, original, source in pairs:
        for kind, desc, mutant in mutations(source):
            total += 1
            stats = per_kind.setdefault(kind, [0, 0])
            stats[0] += 1
            try:
                n5_canon.canonical_form(mutant, n5_canon.ALL_RULES)
            except n5_canon.Unsupported:
                unsupported += 1
            same = [rules for rules in (n5_canon.ALL_RULES, n5_canon.TIER1_RULES)
                    if n5_canon.canonical_equal(original, mutant, rules)]
            if same:
                survivors.append(f"{label} {kind} {desc}")
            else:
                killed += 1
                stats[1] += 1
    return total, killed, unsupported, per_kind, survivors


def _report(name, total, killed, unsupported, per_kind):
    rate = 100.0 * killed / total if total else 0.0
    kinds = ", ".join(f"{k} {v[1]}/{v[0]}" for k, v in sorted(per_kind.items()))
    print(f"\n[{name}] mutation kill rate {killed}/{total} ({rate:.1f}%); "
          f"{unsupported} mutants unsupported (fail-closed, counted as killed); {kinds}", file=sys.stderr)


@unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
@unittest.skipUnless(_corpus_dir() is not None, "N5 corpus (organized/*/extracted) not present")
class TestMutationSoundnessOnShippedMethods(unittest.TestCase):
    def test_every_mutation_of_a_shipped_method_is_detected(self):
        methods = _pick_corpus_methods()
        self.assertGreaterEqual(len(methods), 30, "too few corpus methods sampled")
        pairs = []
        for label, meth in methods:
            try:
                n5_canon.canonical_form(meth, n5_canon.ALL_RULES)
            except n5_canon.Unsupported:
                continue
            pairs.append((label, meth, meth))
        total, killed, unsupported, per_kind, survivors = _check(self, pairs)
        _report(f"shipped: {len(pairs)} methods", total, killed, unsupported, per_kind)
        self.assertGreater(total, 300)
        self.assertEqual(survivors, [], f"{len(survivors)} surviving mutants:\n" + "\n".join(survivors[:40]))


JAVAC_PAIRS = [
    ('if (v == 0) return "a"; return "b";', 'return v == 0 ? "a" : "b";', "static String f(long v)", ""),
    ("x = x + 1; return x;", "x++; return x;", "static int f(int x, int y)", ""),
    ("int t = g(); return x - y;", "g(); return x - y;", "static int f(int x, int y)",
     "static int g() { return 1; }"),
    ("m((String) null); return x;", "m(null); return x;", "static int f(int x, int y)", "static void m(String s) {}"),
    ("{ int a = g(); h(a); } { int b = g() + x; h(b); } return y;",
     "int a = g(); h(a); int b = g() + x; h(b); return y;", "static int f(int x, int y)",
     "static int g() { return 1; } static void h(int i) {}"),
    ("for (int i = 0; i < x; i++) { if (i == y) continue; h(i); } return 0;",
     "for (int i = 0; i < x; i++) { if (i != y) h(i); } return 0;", "static int f(int x, int y)",
     "static void h(int i) {}"),
    ("if (x > 0) { h(1); return 0; } if (y > 0) { h(2); return 0; } return 0;",
     "if (x > 0) h(1); else if (y > 0) h(2); return 0;", "static int f(int x, int y)", "static void h(int i) {}"),
    ("try { h(x); } catch (RuntimeException e) { return 1; } return 0;",
     "try { h(x); return 0; } catch (RuntimeException e) { return 1; }", "static int f(int x, int y)",
     "static void h(int i) {}"),
    ("return o instanceof String ? true : false;", "return o instanceof String;", "static boolean f(Object o)", ""),
]


_PAIR_CACHE: list = []


def _javac_pairs():
    """(label, method_a, method_b) per JAVAC_PAIRS entry, compiled once per run."""
    if not _PAIR_CACHE:
        for body_a, body_b, header, extra in JAVAC_PAIRS:
            a, b = javac_methods(body_a, body_b, header=header, extra=extra)
            _PAIR_CACHE.append((body_b, a, b))
    return _PAIR_CACHE


@unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
class TestMutationSoundnessOnRecompiledSide(unittest.TestCase):
    def test_every_mutation_of_the_recompiled_side_of_an_equal_pair_is_detected(self):
        pairs = _javac_pairs()
        for label, a, b in pairs:
            self.assertIsNotNone(n5_canon.resolve_rules(a, b, tier2=True), f"pair not proven equal: {label}")
        total, killed, unsupported, per_kind, survivors = _check(self, pairs)
        _report("javac pairs, recompiled side", total, killed, unsupported, per_kind)
        self.assertGreater(total, 30)
        self.assertEqual(survivors, [], f"{len(survivors)} surviving mutants:\n" + "\n".join(survivors))


def _sabotaged(transform):
    real = n5_canon.canonical_form

    def fake(method, rules=n5_canon.ALL_RULES):
        form = real(method, rules)
        return tuple(transform(blk) for blk in form) if form != ("empty",) else form
    return fake


@unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
class TestMutationSuiteIsSensitive(unittest.TestCase):
    """The suite must be able to FAIL: a deliberately unsound canonicalizer
    (one that forgets branch polarity, instruction order or catch types) has
    to leave survivors of the matching mutation kind."""

    def test_a_sabotaged_canonicalizer_leaves_survivors(self):
        pairs = _javac_pairs()
        sabotage = {
            "reorder-side-effects": lambda blk: (tuple(sorted(blk[0])), blk[1], blk[2], blk[3]),
            "change-catch-type": lambda blk: (blk[0], blk[1], blk[2], tuple(("?", h) for _t, h in blk[3])),
        }
        fakes = {kind: _sabotaged(t) for kind, t in sabotage.items()}
        real = n5_canon.canonical_form
        polarity_blind = {v: k for k, v in n5_canon._NEGATE.items()}

        def forget_polarity(method, rules=n5_canon.ALL_RULES):
            raw = [re.sub(r"^(\s*\d+:\s*)(\w+)", lambda x: x.group(1) + polarity_blind.get(x.group(2), x.group(2)),
                          line) for line in method["raw_code"]]
            return real({**method, "raw_code": raw}, rules)
        fakes["negate-cond"] = forget_polarity
        for kind, fake in fakes.items():
            with mock.patch.object(n5_canon, "canonical_form", fake):
                *_rest, survivors = _check(self, pairs)
            self.assertTrue(any(f" {kind} " in sv for sv in survivors), f"sabotage of {kind} went unnoticed")


if __name__ == "__main__":
    unittest.main()
