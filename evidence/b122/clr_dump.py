#!/usr/bin/env python3
"""B122 step 2: per-assembly facts from CLR metadata, an instrument independent of ilspycmd.

Writes three TSVs next to --out: assemblies (identity, TFM, signing, table sizes, ilspycmd type-count
agreement), pinvoke (ImplMap rows) and asmrefs (AssemblyRef rows).
Usage: clr_dump.py <dir-with-dlls> --out <dir> [--ilspy]
"""
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import clrlib
import pelib

ILSPY = os.path.expanduser(os.environ.get("ILSPYCMD", "~/.dotnet/tools/ilspycmd"))
DOTNET = os.environ.get("DOTNET_ROOT", "/home/linuxbrew/.linuxbrew/Cellar/dotnet/10.0.400/libexec")
FLAGS = {1: "ILONLY", 2: "32BITREQ", 8: "STRONGNAMESIGNED", 0x10000: "32BITPREF"}


def signer(pe):
    """(digest algorithm whose digest bytes occur in the signed blob, leaf cert subject: the one that issues nobody)."""
    blob = pe.authenticode()
    if not blob:
        return "", ""
    alg = next((a for a in ("sha1", "sha256", "sha384", "sha512") if bytes.fromhex(pe.authenticode_hash(a)) in blob), "NO-MATCH")
    with tempfile.NamedTemporaryFile(suffix=".p7") as t:
        t.write(blob)
        t.flush()
        out = subprocess.run(["openssl", "pkcs7", "-inform", "DER", "-in", t.name, "-print_certs", "-noout"],
                             capture_output=True, text=True).stdout
    pairs, cur = [], None
    for ln in out.splitlines():
        if ln.startswith("subject="):
            cur = ln[8:]
        elif ln.startswith("issuer=") and cur:
            pairs.append((cur, ln[7:]))
    issuers = {i for _, i in pairs}
    leaf = next((s for s, i in pairs if s not in issuers), "")
    return alg, leaf


def ilspy_types(path):
    n = 0
    for kind in "cisde":
        p = subprocess.run([ILSPY, "-l", kind, str(path)], capture_output=True, text=True,
                           env=dict(os.environ, DOTNET_ROOT=DOTNET, DOTNET_ROLL_FORWARD="Major"))
        n += sum(1 for ln in p.stdout.splitlines() if ln.split(" ", 1)[0] in ("Class", "Interface", "Struct", "Delegate", "Enum"))
    return n


def main(d, out, ilspy):
    out = Path(out)
    asm, pinv, refs = [], [], []
    for f in sorted(Path(d).iterdir()):
        if f.suffix.lower() not in (".dll", ".exe"):
            continue
        data = f.read_bytes()
        pe = pelib.PE(data)
        c = clrlib.Clr(pe)
        if not c.ok:
            continue
        a = c.assembly()
        alg, leaf = signer(pe)
        flags = "|".join(v for k, v in FLAGS.items() if c.flags & k)
        row = [f.name, hashlib.sha256(data).hexdigest(), str(len(data)), a["name"], a["version"], c.token_of_pubkey() or "-",
               c.target_framework() or "", c.version, flags, "PE32+" if pe.is64 else "PE32", str(len(c.tab[2])),
               str(len(c.tab[6])), str(len(c.tab.get(10, []))), alg or "unsigned", leaf]
        if ilspy:
            row.append("%d/%s" % (ilspy_types(f), len(c.tab[2])))
        asm.append(row)
        pinv += [[f.name, m, n, e] for m, n, e in c.pinvokes()]
        refs += [[f.name, n, v] for n, v in c.asm_refs()]
    hdr = "file sha256 size assembly version pubkey_token target_framework runtime clr_flags pe typedefs methoddefs memberrefs authenticode_digest authenticode_leaf".split()
    tables = {"assemblies": (hdr + (["ilspy_vs_metadata_types"] if ilspy else []), asm),
              "pinvoke": (["file", "module", "entry", "managed_method"], pinv), "asmrefs": (["file", "ref", "version"], refs)}
    for name, (h, rows) in tables.items():
        (out / (name + ".tsv")).write_text("\n".join("\t".join(r) for r in [h] + rows) + "\n")
    print("assemblies=%d pinvoke=%d asmrefs=%d" % (len(asm), len(pinv), len(refs)), file=sys.stderr)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[a.index("--out") + 1], "--ilspy" in a)
