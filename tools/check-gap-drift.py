#!/usr/bin/env python3
"""Flag RESEARCH-STATE backlog rows whose text drifted from the parent block's child-gap bullet.

For every pending `B<n>-G<m>` row in RESEARCH-STATE.md, locate the bullet that defines that ID in
niagara5-block<n>.md ("- **B<n>-G<m>** ..." in its child-gaps section) and compare content words.
A row whose word overlap with its bullet falls below the threshold is printed as suspected drift.

Usage: python3 tools/check-gap-drift.py [--threshold 0.2] [--all] [--root DIR]
Exit: 0 = no drift suspected, 1 = drift suspected, 2 = usage/IO error.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = set("""a an the of to in on for and or vs via is are be by with from at as it its this that
whether which what why how not no any all full real exact own other""".split())
ROW = re.compile(r"^\| (?:high|medium|low|deferred) \| (B(\d+)-G\d+) (.*?) \| .*\| (.*?) \|$")
BULLET = r"^\s*[-*] \*\*{gid}\*\*(.*)$"


def words(text):
    return {w for w in re.findall(r"[A-Za-z][A-Za-z0-9_.]{2,}", text.lower()) if w not in STOP}


def bullet_text(block, gid):
    lines = block.splitlines()
    pat = re.compile(BULLET.format(gid=re.escape(gid)))
    for i, line in enumerate(lines):
        if pat.match(line):
            body = [line]
            for nxt in lines[i + 1:i + 8]:
                if re.match(r"^\s*[-*] \*\*B\d+-G\d+\*\*", nxt) or nxt.startswith("#") or not nxt.strip():
                    break
                body.append(nxt)
            return " ".join(body)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.2)
    ap.add_argument("--all", action="store_true", help="also check non-pending rows")
    ap.add_argument("--root", type=Path, default=ROOT, help="corpus root (default: repo root)")
    args = ap.parse_args()
    root = args.root
    state = root / "RESEARCH-STATE.md"
    if not state.exists():
        print("RESEARCH-STATE.md not found", file=sys.stderr)
        return 2
    suspects, missing, checked = [], [], 0
    for line in state.read_text().splitlines():
        m = ROW.match(line)
        if not m:
            continue
        gid, bnum, text, status = m.groups()
        if not args.all and not status.startswith("pending"):
            continue
        block_path = root / f"niagara5-block{bnum}.md"
        if not block_path.exists():
            missing.append(gid)
            continue
        bullet = bullet_text(block_path.read_text(), gid)
        if bullet is None:
            missing.append(gid)
            continue
        checked += 1
        rw = words(text)
        overlap = len(rw & words(bullet)) / max(len(rw), 1)
        if overlap < args.threshold:
            suspects.append((gid, round(overlap, 2), text[:90]))
    for gid, ov, text in suspects:
        print(f"DRIFT? {gid} overlap={ov} row='{text}'")
    for gid in missing:
        print(f"NO-BULLET {gid} (no '- **{gid}**' bullet in its block; prose-only definition)")
    print(f"checked={checked} suspects={len(suspects)} no_bullet={len(missing)}")
    return 1 if suspects else 0


if __name__ == "__main__":
    sys.exit(main())
