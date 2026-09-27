#!/usr/bin/env python3
"""
gen-catalog.py — Generate CATALOG.md from niagara5-block*.md files.

Ported from niagara-research (N4 kit tool) for the niagara5-research corpus.
Adaptation from the N4 original:
  - Filename pattern: `niagara5-block<N>.md` (N4 used `niagara-mental-model-bloque<N>.md`).
  - H1 prefix is English "Block N" (N4 used Spanish "Bloque N").
  - No consolidated "1-3" snapshot file and no N4 TITLE_OVERRIDES content — N5
    blocks are written directly in English with a descriptive H1, so title
    overrides start empty. The mechanism is kept (curate here if a block's H1
    ever lacks a title) but nothing is pre-seeded from the N4 corpus.

Run from the repo root:
    python3 tools/gen-catalog.py

Output: CATALOG.md (idempotent — safe to run multiple times).
"""

import re
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Repository root — always relative to this script's location
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent

CATALOG_PATH = REPO_ROOT / "CATALOG.md"

# ---------------------------------------------------------------------------
# Title overrides for blocks whose H1 lacks a descriptive title.
# Empty for a fresh N5 corpus — curate here as blocks are written, if any H1
# ever ships without a descriptive title after "Block N".
# ---------------------------------------------------------------------------
TITLE_OVERRIDES: dict[str, str] = {}

# ---------------------------------------------------------------------------
# Snapshot files to exclude from the main catalog (none in the N5 corpus yet).
# ---------------------------------------------------------------------------
SNAPSHOTS: list[str] = []

# ---------------------------------------------------------------------------
# H1 normalization: strip known prefixes to get the descriptive title only.
#
# Handled patterns:
#   "# Niagara N5 — Block N: T"
#   "# Block N — T"
#   "# Block #N — T"
#   "# Block N: T"
#   "# Block TI — T"
# ---------------------------------------------------------------------------
_H1_PREFIX_RE = re.compile(
    r"^#\s+"
    r"(?:Niagara\s+N5\s+[—\-]+\s+)?"
    r"Block\s+(?:#?\d+|TI)\s*[—:\-]+\s*",
    re.IGNORECASE,
)

# Matches H1 lines that contain ONLY block metadata (no descriptive title follows).
# e.g. "# Niagara N5 — Block 27"
_H1_NO_TITLE_RE = re.compile(
    r"^(?:Niagara\s+N5\s+[—\-]+\s+)?Block\s+(?:#?\d+|TI)\s*$",
    re.IGNORECASE,
)


def extract_h1(path: Path) -> str:
    """Return the first H1 line from a file, or empty string if absent."""
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# "):
                return line
    return ""


def normalize_title(h1: str) -> str:
    """Strip block-number prefixes from an H1 string, returning only the title.

    Returns empty string when the H1 contains no descriptive title (only block metadata).
    """
    if not h1:
        return ""
    # Remove leading "# "
    text = h1.lstrip("# ").strip()
    # If the entire H1 is just block metadata (no title), return empty so override kicks in.
    if _H1_NO_TITLE_RE.match(text):
        return ""
    # Remove known prefix patterns that precede the actual title
    text = _H1_PREFIX_RE.sub("", "# " + text).lstrip("# ").strip()
    return text


# ---------------------------------------------------------------------------
# Filename → block key extraction
# ---------------------------------------------------------------------------
_FILENAME_RE = re.compile(
    r"^niagara5-block(\d+)(?:-[\w-]+)?\.md$"
    r"|^niagara5-block-(test-infrastructure)\.md$"
)


def parse_filename(filename: str) -> dict | None:
    """
    Parse a niagara5-block*.md filename into a sortable entry dict.

    Returns None for files that should be skipped (snapshots handled separately,
    or the filename simply isn't a block file).
    Returns a dict with keys: sort_key, block_label, filename, title_override_key.
    """
    if filename in SNAPSHOTS:
        return None

    m = _FILENAME_RE.match(filename)
    if not m:
        return None

    # Numeric block
    if m.group(1):
        num = int(m.group(1))
        return {
            "sort_key": (1, num),
            "block_label": str(num),
            "filename": filename,
            "title_override_key": str(num),
        }

    # Test infrastructure block
    if m.group(2):
        return {
            "sort_key": (2, 0),        # always last
            "block_label": "TI",
            "filename": filename,
            "title_override_key": "TI",
        }

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def collect_entries() -> list[dict]:
    """Scan REPO_ROOT for niagara5-block*.md and build sorted entries."""
    entries = []

    for path in REPO_ROOT.glob("niagara5-block*.md"):
        filename = path.name
        parsed = parse_filename(filename)
        if parsed is None:
            continue

        h1 = extract_h1(path)
        title = normalize_title(h1)

        # An explicit override always wins: curated on purpose, because the
        # H1 is not descriptive.
        override_key = parsed["title_override_key"]
        if override_key in TITLE_OVERRIDES:
            title = TITLE_OVERRIDES[override_key]

        # Fallback to raw H1 text (stripped of "# ")
        if not title and h1:
            title = h1.lstrip("# ").strip()

        entries.append({
            "sort_key": parsed["sort_key"],
            "block_label": parsed["block_label"],
            "filename": filename,
            "title": title or "(no title)",
        })

    entries.sort(key=lambda e: e["sort_key"])
    return entries


def render_catalog(entries: list[dict]) -> str:
    """Render the full CATALOG.md content."""
    lines = []

    lines.append(
        "<!-- AUTOGENERATED by tools/gen-catalog.py — DO NOT EDIT BY HAND. "
        "Regenerate: python3 tools/gen-catalog.py -->"
    )
    lines.append("")
    lines.append("# Block catalog")
    lines.append("")
    lines.append(f"Total: **{len(entries)} blocks**")
    lines.append("")
    lines.append("| Block | File | Title |")
    lines.append("|-------|------|-------|")

    for e in entries:
        link = f"[{e['filename']}]({e['filename']})"
        lines.append(f"| {e['block_label']} | {link} | {e['title']} |")

    lines.append("")

    if SNAPSHOTS:
        lines.append("## Snapshots")
        lines.append("")
        lines.append("Historical snapshot files (excluded from the active catalog):")
        lines.append("")
        for s in SNAPSHOTS:
            lines.append(f"- [{s}]({s})")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    entries = collect_entries()
    content = render_catalog(entries)

    CATALOG_PATH.write_text(content, encoding="utf-8")
    print(f"Generated {CATALOG_PATH.name} — {len(entries)} blocks listed.")
    for e in entries:
        print(f"  Block {e['block_label']:>4}  {e['filename']}")


if __name__ == "__main__":
    main()
