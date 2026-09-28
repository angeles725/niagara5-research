#!/usr/bin/env python3
"""Mechanically enforce the decompiler-fidelity / method-blind-spot rules over niagara5-block*.md.

Prevention for odd/tasks/decompiler-fidelity-audit.md's failure classes: prose rules already failed
once (B84 was written after B90 established the resugaring rule), so this tool fails CLOSED on the
recurring mistakes instead of relying on a writer re-reading a prompt.

Rules (heuristic; see fixtures under tools/tests/fixtures/lint_block/ for the exact positive/negative
shapes each one is tuned against):
  R0  a `<!-- lint-ok: R<n> ... -->` waiver whose reason is empty.
  R1  syntax-adoption / N4-N5 syntax-delta claim (pattern-match, var, text block, switch expression,
      enhanced for, lambda, ...) with an adoption verb (uses/adopts/rewrites/replaces/...) and no
      bytecode/docSource evidence token in the same paragraph or table row.
  R2  absence claim (does not ship / missing from / removed from / ...) without a class-level,
      across-all-jars census token. `unzip -l`/`ls | grep` against ONE named jar do not count.
  R3  a Self-verify row marked [CERT-hw]/[CERT-live] whose evidence cites only a /tmp path.
  R4  a "Child gaps opened" bullet missing `coverage-check:` (or `measured-by:` when it quotes a
      3+-digit figure or a percentage).
  R5  a fail-open/bypass/null-Context permission claim with no `dispatch:` clause naming the resolved
      override.
  R6  "[Block N] ... does not mention/show/contain/include ..." without citing a raw artifact path.
  R7  a dead/unused/unreferenced-constant or shadow-literal/hardcoded-duplicate claim without a
      compile-time-constant-inlining evidence token.
  R8  an "N5-only"/"new in N5"/"absent from N4"-style claim without a 4.15/PowerB/N4.15 baseline
      token.

Usage:
  python3 tools/lint-block.py [--audit] [--min-block N] [--root DIR] [<files>...]

With no <files>, the default is every niagara5-block*.md directly under --root (default: repo root).

Enforced mode (default): rules apply only to files whose block number is >= --min-block (default
115); files below the threshold are skipped entirely. Exit 1 if any (non-waived) finding remains.

--audit: rules apply to every given file regardless of number; always exits 0 (report only), and
prints a per-rule count summary line after the findings. Meant to drive fixes in older blocks, not to
gate anything.

Waiver: a line whose text contains `<!-- lint-ok: R<n> <non-empty reason> -->` suppresses rule <n> for
the table row or paragraph that comment is part of. An empty reason is itself an R0 finding (the
waiver still suppresses the original rule).

Exit: 0 = no findings (or --audit), 1 = enforced findings present, 2 = usage/IO error.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MIN_BLOCK = 115

BLOCK_NAME_RE = re.compile(r"niagara5-block(\d+)\.md$")

# ---------------------------------------------------------------------------
# Markdown unit extraction: split a block file into "paragraph"/"list item"/
# "table row"/"heading" units, each carrying the (1-indexed) line it starts
# on. A leading blockquote marker ("> ") is stripped before classification so
# a block's header blockquote behaves like ordinary prose/lists.
# ---------------------------------------------------------------------------
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
LIST_ITEM_RE = re.compile(r"^\s*(?:\d+\.|[-*])\s+")
HEADING_RE = re.compile(r"^\s*(#{1,6})\s*(.*)$")
BLOCKQUOTE_RE = re.compile(r"^\s*>\s?")


def _dequote(line):
    return BLOCKQUOTE_RE.sub("", line, count=1)


def extract_units(lines):
    """Return [(text, start_line, kind)] for kind in {"para", "row", "heading"}.

    "para" also covers list items (bullets/numbered items) and their continuation lines: a new
    top-level list item, a blank line, a heading, or a table row all close the current unit.
    """
    units = []
    buf = []
    buf_start = None

    def flush():
        nonlocal buf, buf_start
        if buf:
            units.append((" ".join(buf).strip(), buf_start, "para"))
        buf = []
        buf_start = None

    for i, raw in enumerate(lines, start=1):
        content = _dequote(raw)
        stripped = content.strip()
        if not stripped:
            flush()
            continue
        if TABLE_SEP_RE.match(content):
            flush()
            continue
        if TABLE_ROW_RE.match(content):
            flush()
            units.append((stripped, i, "row"))
            continue
        m = HEADING_RE.match(content)
        if m:
            flush()
            units.append((stripped, i, "heading"))
            continue
        if LIST_ITEM_RE.match(content) and buf:
            flush()
        if buf_start is None:
            buf_start = i
        buf.append(stripped)
    flush()
    return units


def heading_sections(lines):
    """Return [(start_line, end_line_exclusive, title)] for every heading-delimited section."""
    starts = []
    for i, raw in enumerate(lines, start=1):
        m = HEADING_RE.match(_dequote(raw))
        if m:
            starts.append((i, m.group(2)))
    sections = []
    for idx, (start, title) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines) + 1
        sections.append((start, end, title))
    return sections


def lines_in_sections(sections, title_pattern):
    pat = re.compile(title_pattern, re.IGNORECASE)
    out = set()
    for start, end, title in sections:
        if pat.search(title):
            out.update(range(start, end))
    return out


# ---------------------------------------------------------------------------
# Waivers
# ---------------------------------------------------------------------------
WAIVER_RE = re.compile(r"<!--\s*lint-ok:\s*(R\d+)\s*(.*?)-->", re.IGNORECASE)


def find_waivers(lines):
    """Return [(line, rule, reason)] for every waiver comment in the file."""
    out = []
    for i, raw in enumerate(lines, start=1):
        for m in WAIVER_RE.finditer(raw):
            out.append((i, m.group(1).upper(), m.group(2).strip()))
    return out


def waived(text, rule):
    return re.search(r"<!--\s*lint-ok:\s*" + re.escape(rule) + r"\b", text, re.IGNORECASE) is not None


def excerpt(text, n=100):
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


# A block's numbered/bulleted items and table cells routinely pack several independent,
# semicolon-joined claims into one paragraph/row (see B84 item 3 in the real corpus). Scanning a
# whole unit for "feature term ... anywhere ... verb ... anywhere" lets an unrelated clause's verb
# or evidence token silently pair with (or suppress) a different clause's claim. Splitting into
# clauses on ".;!?" boundaries (guarded so "4.15.3.28"-style version numbers don't split) keeps each
# rule's co-occurrence and evidence checks scoped to the one clause actually making the claim.
CLAUSE_SPLIT_RE = re.compile(r"(?<=[a-z0-9)`\]])[.;!?]\s+(?=[A-Z0-9`*\[(])")


def clauses(text):
    parts = [c.strip() for c in CLAUSE_SPLIT_RE.split(text) if c.strip()]
    return parts or [text]


# ---------------------------------------------------------------------------
# R1 — syntax adoption / N4-N5 syntax delta without bytecode evidence
# ---------------------------------------------------------------------------
R1_FEATURES = [
    r"pattern-\s*match(?:ing)?",
    r"instanceof\s+pattern",
    r"JEP\s*394",
    r"switch\s+expression",
    r"arrow\s+switch",
    r"text\s+block",
    r"\bvar\b",
    r"record\s+pattern",
    r"\bsealed\b",
    r"enhanced\s+for",
    r"for-each",
    r"for\s+each",
    r"\blambda\b",
]
R1_FEATURE_RE = re.compile("|".join(R1_FEATURES), re.IGNORECASE)

R1_VERBS = [
    r"\buses?\b", r"\badopts?\b", r"\badopted\b", r"\badoption\b",
    r"\brewrites?\b", r"\brewritten\b", r"\breplaces?\b", r"\breplaced\b",
    r"\bmodernized\b", r"migrated to", r"converted to",
    r"N5 now", r"new in N5", r"Java[\s-]21[\s-]?style",
]
R1_VERB_RE = re.compile("|".join(R1_VERBS), re.IGNORECASE)

R1_EVIDENCE = [
    r"\bjavap\b", r"\btypeSwitch\b", r"\bSwitchBootstraps\b", r"\bLambdaMetafactory\b",
    r"\bPermittedSubclasses\b", r"Record attribute", r"extends\s+java\.lang\.Record",
    r"\bdocSource\b", r"\bCFR\b", r"\bbytecode\b", r"class-file attribute",
    r"\bLocalVariableTable\b",
]
R1_EVIDENCE_RE = re.compile("|".join(R1_EVIDENCE), re.IGNORECASE)


def rule_r1(units):
    out = []
    for text, line, kind in units:
        if kind not in ("para", "row", "heading"):
            continue
        if waived(text, "R1"):
            continue
        for clause in clauses(text):
            if not (R1_FEATURE_RE.search(clause) and R1_VERB_RE.search(clause)):
                continue
            if R1_EVIDENCE_RE.search(clause):
                continue
            out.append((line, "R1", f"syntax-adoption claim without bytecode/docSource evidence: {excerpt(clause)}"))
            break
    return out


# ---------------------------------------------------------------------------
# R2 — absence claim without class-level census
# ---------------------------------------------------------------------------
R2_ABSENCE = [
    r"\babsent\b", r"\babsence\b", r"not shipped", r"does not ship", r"doesn't ship",
    r"no longer ships", r"missing from", r"removed from", r"not present", r"zero hits",
    r"does not exist",
]
R2_ABSENCE_RE = re.compile("|".join(R2_ABSENCE), re.IGNORECASE)

# Deliberately excludes "unzip -l" / "ls ... | grep" on their own: a single named-jar lookup does
# NOT count as a class-level census (see the T8 spec's B98 example).
R2_STRONG_CENSUS = [
    r"all 247", r"every jar", r"all jars", r"config-home", r"config home", r"bin/ext",
    r"LIB-INF", r"class-level", r"package-level", r"\bcallers\b", r"\bcensus\b",
]
R2_STRONG_CENSUS_RE = re.compile("|".join(R2_STRONG_CENSUS), re.IGNORECASE)

# R2 targets absence-of-a-software-artifact claims (the B98 saml.jar shape), not an arbitrary
# config-key/property value being "absent" from one table row -- scope it to jar/class/module/
# package-shaped language so a two-column config diff table doesn't drown the real signal.
R2_ARTIFACT_RE = re.compile(
    r"\.jar\b|\.class\b|\.dll\b|\.exe\b|\bjars?\b|\bclasses?\b|\bmodules?\b|\bpackages?\b|\bcorpus\b",
    re.IGNORECASE)


def rule_r2(units):
    out = []
    for text, line, kind in units:
        if kind not in ("para", "row", "heading"):
            continue
        if waived(text, "R2"):
            continue
        for clause in clauses(text):
            if not (R2_ABSENCE_RE.search(clause) and R2_ARTIFACT_RE.search(clause)):
                continue
            if R2_STRONG_CENSUS_RE.search(clause):
                continue
            out.append((line, "R2", f"absence claim without a class-level census: {excerpt(clause)}"))
            break
    return out


# ---------------------------------------------------------------------------
# R3 — ephemeral evidence in Self-verify
# ---------------------------------------------------------------------------
R3_MARKER_RE = re.compile(r"\[CERT-hw\]|\[CERT-live\]")
R3_DURABLE_RE = re.compile(r"evidence/|sources/|organized/|poc/|[\w./-]*/[\w.-]+\.\w{1,6}:\d+")


def split_row_cells(row_text):
    inner = row_text.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip() for c in inner.split("|")]


def rule_r3(units, lines):
    sv_lines = lines_in_sections(heading_sections(lines), r"self-verify")
    out = []
    for text, line, kind in units:
        if kind != "row" or line not in sv_lines:
            continue
        cells = split_row_cells(text)
        if len(cells) < 4:
            continue
        marker, evidence = cells[2], cells[3]
        if not R3_MARKER_RE.search(marker):
            continue
        if "/tmp/" not in evidence:
            continue
        if R3_DURABLE_RE.search(evidence):
            continue
        if waived(text, "R3"):
            continue
        out.append((line, "R3", f"[CERT-hw]/[CERT-live] evidence cites only /tmp: {excerpt(evidence)}"))
    return out


# ---------------------------------------------------------------------------
# R4 — child-gap hygiene
# ---------------------------------------------------------------------------
GAP_BULLET_RE = re.compile(r"^-\s+(B\d+-G\d+)\b")  # text is already de-bolded (see lint_file)
DIGIT3_RE = re.compile(r"\b\d{3,}\b")
PERCENT_RE = re.compile(r"\d+(?:\.\d+)?%")


def rule_r4(units, lines):
    gap_lines = lines_in_sections(heading_sections(lines), r"child gaps? opened")
    out = []
    for text, line, kind in units:
        if kind != "para" or line not in gap_lines:
            continue
        m = GAP_BULLET_RE.match(text)
        if not m:
            continue
        gid = m.group(1)
        missing = []
        if "coverage-check:" not in text:
            missing.append("coverage-check:")
        if (DIGIT3_RE.search(text) or PERCENT_RE.search(text)) and "measured-by:" not in text:
            missing.append("measured-by:")
        if not missing:
            continue
        if waived(text, "R4"):
            continue
        out.append((line, "R4", f"{gid} missing {', '.join(missing)}: {excerpt(text)}"))
    return out


# ---------------------------------------------------------------------------
# R5 — permission consequence without a resolved dispatch target
# ---------------------------------------------------------------------------
R5_CONSEQUENCE = [
    r"fail-open", r"fails?\s+open", r"\bno-op\b", r"\bbypass(?:es|ed)?\b", r"\bungated\b",
    r"drops?\s+cx\b", r"null\s+Context", r"getPermissions\(null\)",
]
R5_CONSEQUENCE_RE = re.compile("|".join(R5_CONSEQUENCE), re.IGNORECASE)

# "bypass"/"ungated"/"no-op" are common outside the permission-dispatch failure class this rule
# targets (Gradle flags, test-mode shortcuts, module-verification skips, ...) -- require the clause
# to actually be about permissions/security, not just use one of those generic words.
R5_PERM_CONTEXT_RE = re.compile(
    r"\bpermissions?\b|getPermissions|\bContext\b|\bcx\b|\bsecurity\b|\bcredentials?\b|\bauth\w*\b",
    re.IGNORECASE)


def rule_r5(units):
    out = []
    for text, line, kind in units:
        if kind not in ("para", "row", "heading"):
            continue
        if waived(text, "R5"):
            continue
        for clause in clauses(text):
            if not (R5_CONSEQUENCE_RE.search(clause) and R5_PERM_CONTEXT_RE.search(clause)):
                continue
            if "dispatch:" in clause.lower():
                continue
            out.append((line, "R5", f"permission consequence claim without a resolved dispatch: target: {excerpt(clause)}"))
            break
    return out


# ---------------------------------------------------------------------------
# R6 — prose-vs-raw
# ---------------------------------------------------------------------------
R6_TRIGGER_RE = re.compile(r"\b(?:does not|doesn't|never)\s+(?:mention|show|contain|include)s?\b", re.IGNORECASE)
R6_BLOCK_REF_RE = re.compile(r"\[Block\s*\d+\]", re.IGNORECASE)
R6_RAW_PATH_RE = re.compile(r"evidence/|[\w./-]*/[\w.-]+\.\w{1,6}")


def rule_r6(units):
    out = []
    for text, line, kind in units:
        if kind not in ("para", "row", "heading"):
            continue
        if waived(text, "R6"):
            continue
        # R6 stays unit-scoped (not per-clause): the "[Block N]" reference and the "does not
        # mention" verdict are routinely split across neighboring clauses/sentences of the same
        # paragraph, and the raw-path citation that would clear it is often a later clause too.
        if not (R6_TRIGGER_RE.search(text) and R6_BLOCK_REF_RE.search(text)):
            continue
        if R6_RAW_PATH_RE.search(text):
            continue
        out.append((line, "R6", f"comparison against another block without citing its raw artifact: {excerpt(text)}"))
    return out


# ---------------------------------------------------------------------------
# R7 — constant inlining without evidence
# ---------------------------------------------------------------------------
R7_TRIGGERS = [
    r"\b(?:dead|unused|unreferenced)\s+constants?\b",
    r"\bconstants?\b.{0,15}\b(?:is|are)\b.{0,15}\b(?:dead|unused|unreferenced)\b",
    r"\bshadow\w*\b.{0,40}\bliteral\b",
    r"\bliteral\b.{0,40}\bshadow\w*\b",
    r"\bduplicat\w*\b.{0,25}(?:its own\s+)?constants?\b",
    r"\bconstants?\b.{0,25}\bduplicat\w*\b",
    r"\bhardcod\w*\b.{0,80}\binstead of\b.{0,40}\bconstant\b",
]
R7_TRIGGER_RE = re.compile("|".join(R7_TRIGGERS), re.IGNORECASE)

# The naive substring "inlin" also matches ordinary prose ("an inline literal duplicate", the exact
# phrasing of the real B96 positive) -- require it to co-occur with a technical term so that phrasing
# doesn't silently suppress the finding it is describing.
R7_EVIDENCE = [
    r"compile-time constant",
    r"JLS\s*4\.12\.4",
    r"JLS\s*13\.1",
    r"\bldc\b",
    r"\bdocSource\b",
    r"\binlin\w*\b.{0,25}(?:constant|compiler|javac|javap|bytecode)",
    r"(?:constant|compiler|javac|javap|bytecode).{0,25}\binlin\w*\b",
]
R7_EVIDENCE_RE = re.compile("|".join(R7_EVIDENCE), re.IGNORECASE)


def rule_r7(units):
    out = []
    for text, line, kind in units:
        if kind not in ("para", "row", "heading"):
            continue
        if waived(text, "R7"):
            continue
        for clause in clauses(text):
            if not R7_TRIGGER_RE.search(clause):
                continue
            if R7_EVIDENCE_RE.search(clause):
                continue
            out.append((line, "R7", f"constant-inlining claim without bytecode/docSource evidence: {excerpt(clause)}"))
            break
    return out


# ---------------------------------------------------------------------------
# R8 — baseline attribution
# ---------------------------------------------------------------------------
R8_TRIGGER_RE = re.compile(
    r"N5-only|new in N5|added in N5|introduced in N5|absent from N4", re.IGNORECASE)
R8_BASELINE_RE = re.compile(r"4\.15|PowerB|N4\.15", re.IGNORECASE)
# Scope to software-surface claims (module/class/jar/package/feature), not e.g. a Gradle build
# property or doc-cited config key being "new in N5" -- those aren't the N4.14-vs-4.15 module-census
# failure class this rule targets.
R8_SURFACE_RE = re.compile(
    r"\.jar\b|\.class\b|\bjars?\b|\bclasses?\b|\bmodules?\b|\bpackages?\b|\bfeatures?\b|\bAPI\b",
    re.IGNORECASE)


def rule_r8(units):
    out = []
    for text, line, kind in units:
        if kind not in ("para", "row", "heading"):
            continue
        if waived(text, "R8"):
            continue
        for clause in clauses(text):
            if not (R8_TRIGGER_RE.search(clause) and R8_SURFACE_RE.search(clause)):
                continue
            if R8_BASELINE_RE.search(clause):
                continue
            out.append((line, "R8", f"N5-only/baseline claim without a 4.15 baseline check: {excerpt(clause)}"))
            break
    return out


RULES = [rule_r1, rule_r2, rule_r5, rule_r6, rule_r7, rule_r8]  # unit-only rules
# R3 and R4 need the raw lines too (section scoping) and are invoked separately.


def lint_file(path):
    """Return sorted [(line, rule, message)] findings for one file (R0-R8)."""
    text = path.read_text(encoding="utf-8")
    # Strip markdown bold markers before matching: this corpus routinely emphasizes the load-
    # bearing word inside a trigger phrase ("does **not** ship"), which would otherwise split the
    # phrase across the "**" delimiters and silently miss it. Waivers/markers/paths never carry
    # "**", so this is safe for every other check too, and only changes what regexes SEE -- the
    # line count and every other character are untouched.
    text = text.replace("**", "")
    lines = text.splitlines()
    units = extract_units(lines)
    findings = []
    for waiver_line, rule, reason in find_waivers(lines):
        if not reason:
            findings.append((waiver_line, "R0", f"waiver has an empty reason: {rule}"))
    for rule_fn in RULES:
        findings.extend(rule_fn(units))
    findings.extend(rule_r3(units, lines))
    findings.extend(rule_r4(units, lines))
    findings.sort(key=lambda f: (f[0], f[1]))
    return findings


def block_number(path):
    m = BLOCK_NAME_RE.search(path.name)
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--audit", action="store_true",
                     help="report findings for ALL given files, exit 0, print a per-rule summary")
    ap.add_argument("--min-block", type=int, default=DEFAULT_MIN_BLOCK,
                     help="enforced mode: minimum block number rules apply to (default %(default)s)")
    ap.add_argument("--root", type=Path, default=ROOT,
                     help="corpus root for default file discovery (default: repo root)")
    args = ap.parse_args()

    files = args.files
    if not files:
        files = sorted(args.root.glob("niagara5-block*.md"),
                        key=lambda p: block_number(p) if block_number(p) is not None else 0)

    counts = {}
    total_findings = 0
    any_error = False
    for path in files:
        try:
            findings = lint_file(path)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"cannot read {path}: {exc}", file=sys.stderr)
            any_error = True
            continue
        bnum = block_number(path)
        if not args.audit:
            if bnum is None or bnum < args.min_block:
                continue
        for line, rule, message in findings:
            print(f"{rule} {path.name}:{line}: {message}")
            counts[rule] = counts.get(rule, 0) + 1
            total_findings += 1

    if any_error:
        return 2

    if args.audit:
        parts = " ".join(f"{r}={counts.get(r, 0)}" for r in ("R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"))
        print(f"{parts} total={total_findings}")
        return 0

    print(f"checked={len(files)} findings={total_findings}")
    return 1 if total_findings else 0


if __name__ == "__main__":
    sys.exit(main())
