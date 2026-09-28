#!/usr/bin/env python3
"""Flag RESEARCH-STATE backlog rows whose text drifted from the parent block's child-gap bullet.

For every pending `B<n>-G<m>` row in RESEARCH-STATE.md, locate the bullet that defines that ID in
niagara5-block<n>.md ("- **B<n>-G<m>** ..." in its child-gaps section) and compare content words.
A row whose word overlap with its bullet falls below the threshold is printed as suspected drift.

Output lines:
  DRIFT?    <gid>  row text shares too few content words with its bullet
  NO-BULLET <gid>  block exists but defines the gap only in prose (no "- **<gid>**" bullet)
  NO-BLOCK  <gid>  the parent block file does not exist
  UNPARSED  <line> a backlog-looking row the row grammar could not parse (never silently skipped)

Usage: python3 tools/check-gap-drift.py [--threshold 0.2] [--all] [--root DIR]
Exit: 0 = no drift suspected, 1 = drift or unparsed rows, 2 = usage/IO error.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = set("""a an the of to in on for and or vs via is are be by with from at as it its this that
whether which what why how not no any all full real exact own other""".split())
ROW = re.compile(r"^\| (?:high|medium|low|deferred) \| (B(\d+)-G\d+) (.*?) \| .*\| (.*?) \|$")
# Any table row whose second cell starts with a gap ID: used to catch rows ROW failed to parse.
GAP_ROW = re.compile(r"^\|\s*\w+\s*\|\s*B\d+-G\d+\b")
BULLET = r"^\s*[-*] \*\*{gid}\*\*(.*)$"
# Child-gap bullets in this corpus wrap to at most a handful of lines; reading further risks
# pulling in the next section's prose. Tune here if a longer bullet produces a false DRIFT.
MAX_CONTINUATION_LINES = 7
# Share of the row's content words that must also occur in the bullet. 0.2 flags rewritten
# topics (observed drift scored 0.0-0.14) while tolerating short paraphrases (observed >= 0.3).
DEFAULT_THRESHOLD = 0.2


def words(text):
    return {w for w in re.findall(r"[A-Za-z][A-Za-z0-9_.]{2,}", text.lower()) if w not in STOP}


def bullet_text(block, gid):
    lines = block.splitlines()
    pat = re.compile(BULLET.format(gid=re.escape(gid)))
    for i, line in enumerate(lines):
        if pat.match(line):
            body = [line]
            for nxt in lines[i + 1:i + 1 + MAX_CONTINUATION_LINES]:
                if re.match(r"^\s*[-*] \*\*B\d+-G\d+\*\*", nxt) or nxt.startswith("#") or not nxt.strip():
                    break
                body.append(nxt)
            return " ".join(body)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help="minimum share of row words found in the bullet (default %(default)s)")
    ap.add_argument("--all", action="store_true", help="also check non-pending rows")
    ap.add_argument("--root", type=Path, default=ROOT, help="corpus root (default: repo root)")
    ap.add_argument("--state", type=Path, default=None,
                    help="alternate path to RESEARCH-STATE.md (default: --root/RESEARCH-STATE.md); "
                         "lets a caller point at a materialized copy of the staged blob instead of "
                         "the working-tree file")
    ap.add_argument("--block-dir", type=Path, default=None,
                    help="alternate directory to read niagara5-block<N>.md from (default: --root)")
    args = ap.parse_args()
    root = args.root
    state = args.state if args.state is not None else root / "RESEARCH-STATE.md"
    block_dir = args.block_dir if args.block_dir is not None else root
    try:
        state_text = state.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"cannot read {state}: {exc}", file=sys.stderr)
        return 2
    suspects, no_bullet, no_block, unparsed, checked = [], [], [], [], 0
    for line in state_text.splitlines():
        m = ROW.match(line)
        if not m:
            if GAP_ROW.match(line):
                unparsed.append(line[:90])
            continue
        gid, bnum, text, status = m.groups()
        if not args.all and not status.startswith("pending"):
            continue
        block_path = block_dir / f"niagara5-block{bnum}.md"
        if not block_path.exists():
            no_block.append(gid)
            continue
        try:
            block_text = block_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"cannot read {block_path}: {exc}", file=sys.stderr)
            return 2
        bullet = bullet_text(block_text, gid)
        if bullet is None:
            no_bullet.append(gid)
            continue
        checked += 1
        rw = words(text)
        overlap = len(rw & words(bullet)) / max(len(rw), 1)
        if overlap < args.threshold:
            suspects.append((gid, round(overlap, 2), text[:90]))
    for gid, ov, text in suspects:
        print(f"DRIFT? {gid} overlap={ov} row='{text}'")
    for gid in no_bullet:
        print(f"NO-BULLET {gid} (no '- **{gid}**' bullet in its block; prose-only definition)")
    for gid in no_block:
        print(f"NO-BLOCK {gid} (parent block file does not exist)")
    for row in unparsed:
        print(f"UNPARSED {row}")
    print(f"checked={checked} suspects={len(suspects)} no_bullet={len(no_bullet)} "
          f"no_block={len(no_block)} unparsed={len(unparsed)}")
    return 1 if suspects or unparsed else 0


if __name__ == "__main__":
    sys.exit(main())
