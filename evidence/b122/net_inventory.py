#!/usr/bin/env python3
"""B122 step 1: content-based census of every PE with a CLR header (.NET) reachable from the N5 install.

Sources scanned (by magic bytes, never by file name):
  jars  = the 247 config-home module jars, every entry, recursing into nested jars/zips
  inst  = /mnt/c/Program Files/Niagara/5.0.0.28 (loose files; nested jars again recursed)
  org   = /home/cristian/niagara5-research/organized (non-decompile trees) as a cross-check of `jars`
Output: TSV on stdout, one row per (source, container, member) that is a PE; `--net` keeps CLR only.
"""
import glob
import hashlib
import io
import os
import sys
import zipfile

import clrlib
import pelib

MODS = "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
INST = "/mnt/c/Program Files/Niagara/5.0.0.28"
ORG = "/home/cristian/niagara5-research/organized"
SKIP = ("vineflower", "fallback", "extracted", "_evidence", "_upstream", "_v2-libcache")
ZIPS = (".jar", ".zip", ".war", ".nupkg")


def describe(data):
    pe = pelib.PE(data)
    row = dict(machine="%#06x" % pe.machine, pe32p=int(pe.is64), clr=0, asm="", ver="", tfm="", sn="", token="",
               authenticode=int(pe.authenticode() is not None), exports=len(pe.exports()))
    c = clrlib.Clr(pe)
    if c.ok:
        a = c.assembly()
        row.update(clr=1, asm=a["name"], ver=a["version"], tfm=c.target_framework() or "",
                   sn=int(bool(c.flags & 8)), token=c.token_of_pubkey() or "-")
    return row


def scan_zip(zf, source, container, out, depth=0):
    for zi in zf.infolist():
        if zi.is_dir():
            continue
        try:
            data = zf.read(zi)
        except Exception:
            continue
        member = container + "!" + zi.filename
        if data[:2] == b"MZ":
            record(data, source, member, out)
        elif zi.filename.lower().endswith(ZIPS) and depth < 3:
            try:
                scan_zip(zipfile.ZipFile(io.BytesIO(data)), source, member, out, depth + 1)
            except zipfile.BadZipFile:
                pass


def record(data, source, member, out):
    try:
        row = describe(data)
    except Exception as e:  # not a PE after all (MZ stub only) - keep the evidence
        row = dict(machine="?", pe32p="", clr=0, asm="", ver="", tfm="", sn="", token="", authenticode="",
                   exports="", err=type(e).__name__)
    row.update(source=source, member=member, size=len(data), sha256=hashlib.sha256(data).hexdigest())
    out.append(row)


def walk_dir(root, source, out, skip=()):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if not d.startswith(skip)] if skip else dns
        for fn in fns:
            p = os.path.join(dp, fn)
            if os.path.islink(p):
                continue
            try:
                with open(p, "rb") as f:
                    head = f.read(4)
                    if head[:2] == b"MZ":
                        record(head + f.read(), source, os.path.relpath(p, root), out)
                    elif fn.lower().endswith(ZIPS):
                        scan_zip(zipfile.ZipFile(p), source, os.path.relpath(p, root), out)
            except (OSError, zipfile.BadZipFile):
                pass


def main():
    out = []
    for j in sorted(glob.glob(MODS + "/*.jar")):
        scan_zip(zipfile.ZipFile(j), "jars", os.path.basename(j), out)
    walk_dir(INST, "inst", out)
    walk_dir(ORG, "org", out, skip=SKIP)
    cols = ["source", "member", "sha256", "size", "machine", "pe32p", "clr", "asm", "ver", "tfm", "sn", "token",
            "authenticode", "exports"]
    net_only = "--net" in sys.argv
    print("\t".join(cols))
    for r in out:
        if net_only and not r["clr"]:
            continue
        print("\t".join(str(r.get(c, "")) for c in cols))


if __name__ == "__main__":
    main()
