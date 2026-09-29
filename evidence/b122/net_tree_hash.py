#!/usr/bin/env python3
"""B122: identity of the out-of-git ilspycmd output trees: files, lines and a tree sha256 per assembly.

tree sha256 = sha256 over the sorted "<relpath>\\t<file sha256>" lines of every *.cs file, so a re-run of
decompile-net.sh is comparable without committing any decompiled source.
Usage: net_tree_hash.py <root-with-one-dir-per-assembly> > net-decompile.tsv
"""
import hashlib
import sys
from pathlib import Path


def main(root):
    print("assembly\tcs_files\tcs_lines\ttree_sha256")
    for d in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        lines, files = 0, []
        for f in sorted(d.rglob("*.cs")):
            b = f.read_bytes()
            lines += b.count(b"\n")
            files.append("%s\t%s" % (f.relative_to(d), hashlib.sha256(b).hexdigest()))
        tree = hashlib.sha256("\n".join(files).encode()).hexdigest()
        print("%s\t%d\t%d\t%s" % (d.name, len(files), lines, tree))


if __name__ == "__main__":
    main(sys.argv[1])
