#!/usr/bin/env python3
"""check-coverage.py — the prior-coverage GATE for opening a new research focus.

Ported from niagara-research (N4 corpus kit tool) for the niagara5-research corpus.
Adaptation from the N4 original:
  - Block glob: `niagara5-block*.md` (N4 used `niagara-mental-model-bloque*.md`).
  - Also scans `RESEARCH-STATE*.md` (gap backlog / state files): a name mentioned
    only in an open-gap backlog row is real prior signal too — missing it was
    exactly the failure mode this gate exists to prevent (see the N4 retro this
    tool cites). Each hit is tagged with its source `kind` ("block" or "state")
    so a caller can tell "already mapped by a block" apart from "already on
    someone's backlog, not yet mapped".

Before a new focus (frontier-auto-opened or operator-opened) declares scope or seeds a
single gap, it MUST run this on the target's real MODULE / PACKAGE names — NOT on the
abstract topic, and NEVER trusting the blocks recalled from the parent terminal.

For each name it scans every niagara5-block*.md and RESEARCH-STATE*.md file and reports:
  - SUBJECT  : the name appears in the file's H1 title  -> that file MAPS it. Strong signal.
  - body     : the name appears only in the file body   -> mentioned; read before scoping.
  - (clear)  : no hits                                   -> genuinely unmapped.

Exit code:
  0  every name is clear (no prior coverage)             -> safe to open as net-new.
  2  at least one name has SUBJECT or body coverage      -> DO NOT claim "net-new" blindly;
     read the cited files, and in the bootstrap declare per module: net-new /
     deepening of B<n> (cite it) / already covered -> out of scope.

Usage:
  python3 tools/check-coverage.py honIrmConfig SomeOtherModule
  python3 tools/check-coverage.py --json bacnetObjectTypes
Pure stdlib; run from the repo root (or anywhere — paths resolve to this file's repo).
"""
import sys, os, re, json, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK_GLOB = os.path.join(REPO, "niagara5-block*.md")
STATE_GLOB = os.path.join(REPO, "RESEARCH-STATE*.md")
BLOCK_ID_RE = re.compile(r"niagara5-block([0-9A-Za-z-]+)\.md$")


def first_h1(path):
    """Return the file's H1 title line (first non-empty '# ...' line), else ''."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                s = line.strip()
                if s.startswith("# "):
                    return s[2:].strip()
    except OSError:
        pass
    return ""


def _id_for(path, kind):
    base = os.path.basename(path)
    if kind == "block":
        m = BLOCK_ID_RE.search(base)
        return m.group(1) if m else base
    return base  # state files: report by filename, no numeric id


def scan(names, block_glob=BLOCK_GLOB, state_glob=STATE_GLOB):
    """One pass over every block + state file; classify each name as SUBJECT / body."""
    lowered = [(n, n.lower()) for n in names]
    results = {n: {"subject": [], "body": []} for n in names}
    sources = [("block", block_glob), ("state", state_glob)]
    total_files = 0
    for kind, pattern in sources:
        files = sorted(glob.glob(pattern))
        total_files += len(files)
        for path in files:
            file_id = _id_for(path, kind)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            low = text.lower()
            h1 = None
            for orig, low_name in lowered:
                if low_name not in low:
                    continue
                if h1 is None:
                    h1 = first_h1(path)
                entry = {"kind": kind, "id": file_id, "h1": h1}
                if low_name in h1.lower():
                    results[orig]["subject"].append(entry)
                else:
                    results[orig]["body"].append(entry)
    return results, total_files


def main(argv):
    names = [a for a in argv if not a.startswith("-")]
    as_json = "--json" in argv
    if not names or "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0 if ("-h" in argv or "--help" in argv) else 1

    results, nfiles = scan(names)
    covered = any(results[n]["subject"] or results[n]["body"] for n in names)

    if as_json:
        print(json.dumps({
            "scanned_files": nfiles,
            "names": results,
            "verdict": "prior-coverage-found" if covered else "clear",
        }, indent=2, ensure_ascii=False))
        return 2 if covered else 0

    print(f"prior-coverage gate — scanned {nfiles} file(s) (blocks + RESEARCH-STATE)\n")
    for n in names:
        subj = results[n]["subject"]
        body = results[n]["body"]
        if not subj and not body:
            print(f"  [CLEAR]   {n} — no prior mention. Safe to open as net-new.")
            continue
        tag = "COVERED" if subj else "MENTIONED"
        print(f"  [{tag}] {n}:")
        for e in subj:
            label = f"B{e['id']}" if e["kind"] == "block" else e["id"]
            print(f"      SUBJECT  {label} ({e['kind']}) — {e['h1']}")
        for e in body[:12]:
            label = f"B{e['id']}" if e["kind"] == "block" else e["id"]
            print(f"      body     {label} ({e['kind']}) — {e['h1']}")
        if len(body) > 12:
            print(f"      body     … +{len(body) - 12} more file(s)")
        print()

    if covered:
        print("VERDICT: prior coverage found. DO NOT declare \"extends X, never re-derives\" blindly.")
        print("For each covered module, decide in the bootstrap: net-new / deepening of B<n> (cite it) /")
        print("already covered -> out of scope. A focus that is entirely covered does NOT open.")
        return 2
    print("VERDICT: clear. No prior coverage for any name — safe to open as net-new.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
