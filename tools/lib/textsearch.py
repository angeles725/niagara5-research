"""
textsearch.py — Canonical tokenized search core for niagara-research CLI tools.

This module is the single source of truth for query parsing, file-level
matching, line-level hit detection, and relevance scoring. It replaces the
ad-hoc ``query in text`` literal-phrase check that caused multi-word queries
to return false "No matches" when the words were present but not contiguous.

Importers:
    tools/corpus-nav.py
    niagara-help/tools/niagara_help_lib/find_search.py
    niagara-help/tools/niagara_help_lib/guide_search.py

Stdlib only. No external dependencies.
"""

from __future__ import annotations


def parse_query(q: str) -> list[str]:
    """Lowercase-split a query string into non-empty tokens.

    Examples::

        parse_query("BStatus overridden") -> ["bstatus", "overridden"]
        parse_query("DashboardPan")       -> ["dashboardpan"]
        parse_query("")                   -> []

    Single-word queries return a one-element list so all callers that
    iterate terms need no special-casing for the single-word case.
    """
    return [t for t in q.lower().split() if t]


def file_matches(terms: list[str], text_lower: str, mode: str) -> bool:
    """Return True when *text_lower* satisfies the match condition for *terms*.

    Parameters
    ----------
    terms:
        Token list from :func:`parse_query`.  Must already be lowercase.
    text_lower:
        The full file/block text pre-lowercased by the caller.
    mode:
        ``"and"`` — every term must appear at least once anywhere in the text.
        ``"or"``  — at least one term must appear anywhere in the text.

    An empty *terms* list always returns ``False``.
    """
    if not terms:
        return False
    if mode == "and":
        return all(t in text_lower for t in terms)
    # mode == "or"
    return any(t in text_lower for t in terms)


def line_hits(terms: list[str], line_lower: str) -> bool:
    """Return True if *any* term appears in *line_lower*.

    Used after :func:`file_matches` selects a file to decide which individual
    lines to display.  Always OR-logic: a line is shown as soon as it mentions
    at least one query term, regardless of the file-level AND/OR mode.
    """
    if not terms:
        return False
    return any(t in line_lower for t in terms)


def score(terms: list[str], text_lower: str) -> int:
    """Relevance score for ranking matched files/blocks (higher = more relevant).

    Formula::

        (distinct_terms_present * 1000) + total_term_occurrences

    Distinct-term coverage is weighted heavily (factor 1000) so a file
    containing *all* query terms ranks above a file that repeats only one term
    many times.  Within equal distinct coverage, occurrence count breaks ties.

    Examples
    --------
    terms = parse_query("alarm fault")
    score(terms, "alarm and fault and alarm again") -> 2 * 1000 + 3 = 2003
    score(terms, "just alarm")                     -> 1 * 1000 + 1 = 1001
    score(terms, "nothing here")                   -> 0
    """
    if not terms:
        return 0
    distinct = sum(1 for t in terms if t in text_lower)
    total_occ = sum(text_lower.count(t) for t in terms)
    return distinct * 1000 + total_occ
