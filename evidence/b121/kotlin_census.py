#!/usr/bin/env python3
"""B121 step 1: which jars hold Kotlin-compiled classes?

A class is Kotlin-compiled iff its class-level RuntimeVisibleAnnotations attribute contains
an annotation of type Lkotlin/Metadata; (parsed from the class file, not a raw byte scan).
Roots (all jars, nested jars followed recursively):
  config-home modules, bin/ext, etc/m2, lib, javadoc   (install)
  organized/_etc-m2/*/extracted + _lib/*/extracted     (already-extracted Tridium build jars)
Outputs TSV rows: jar-path, classes, kotlin-classes, tridium-classes, kotlin-tridium-classes,
                  kind histogram, metadata-version histogram.
"""
import zipfile, io, os, sys, glob, struct, collections, json

INSTALL = "/mnt/c/Program Files/Niagara/5.0.0.28"
CONFIG = "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
TRIDIUM_PREFIXES = ("com/tridium/", "javax/baja/", "niagara/", "com/tridiumx/")


def parse_metadata(data):
    """Return dict(k=, mv=) if class carries @kotlin.Metadata, else None."""
    if data[:4] != b"\xca\xfe\xba\xbe":
        return None
    if b"kotlin/Metadata" not in data:  # cheap prefilter; the parse below is the authority
        return None
    p = 8
    n = struct.unpack(">H", data[p:p + 2])[0]; p += 2
    utf8 = {}
    i = 1
    while i < n:
        t = data[p]; p += 1
        if t == 1:
            l = struct.unpack(">H", data[p:p + 2])[0]; p += 2
            utf8[i] = data[p:p + l]; p += l
        elif t in (3, 4): p += 4
        elif t in (5, 6): p += 8; i += 1
        elif t in (7, 8, 16, 19, 20): p += 2
        elif t in (9, 10, 11, 12, 17, 18): p += 4
        elif t == 15: p += 3
        else: raise ValueError("cp tag %d" % t)
        i += 1
    p += 6
    ic = struct.unpack(">H", data[p:p + 2])[0]; p += 2 + 2 * ic

    def skip_members():
        nonlocal p
        cnt = struct.unpack(">H", data[p:p + 2])[0]; p += 2
        for _ in range(cnt):
            p += 6
            ac = struct.unpack(">H", data[p:p + 2])[0]; p += 2
            for _ in range(ac):
                p += 2
                l = struct.unpack(">I", data[p:p + 4])[0]; p += 4 + l
    skip_members(); skip_members()
    ac = struct.unpack(">H", data[p:p + 2])[0]; p += 2
    for _ in range(ac):
        name = utf8[struct.unpack(">H", data[p:p + 2])[0]]; p += 2
        l = struct.unpack(">I", data[p:p + 4])[0]; p += 4
        if name == b"RuntimeVisibleAnnotations":
            q = p
            na = struct.unpack(">H", data[q:q + 2])[0]; q += 2
            for _ in range(na):
                ty = utf8[struct.unpack(">H", data[q:q + 2])[0]]; q += 2
                npairs = struct.unpack(">H", data[q:q + 2])[0]; q += 2
                vals = {}
                for _ in range(npairs):
                    en = utf8[struct.unpack(">H", data[q:q + 2])[0]]; q += 2
                    q, v = read_ev(data, q, utf8)
                    vals[en.decode()] = v
                if ty == b"Lkotlin/Metadata;":
                    return {"k": vals.get("k"), "mv": tuple(vals.get("mv") or ())}
        p += l
    return None


def read_ev(data, q, utf8):
    tag = chr(data[q]); q += 1
    if tag in "BCDFIJSZs":
        idx = struct.unpack(">H", data[q:q + 2])[0]; q += 2
        return q, idx  # int-valued tags: index into cp; we only need k via cp lookup below
    if tag == "e": return q + 4, None
    if tag == "c": return q + 2, None
    if tag == "@":
        q += 2
        np_ = struct.unpack(">H", data[q:q + 2])[0]; q += 2
        for _ in range(np_):
            q += 2; q, _v = read_ev(data, q, utf8)
        return q, None
    if tag == "[":
        nv = struct.unpack(">H", data[q:q + 2])[0]; q += 2
        out = []
        for _ in range(nv):
            q, v = read_ev(data, q, utf8); out.append(v)
        return q, out
    raise ValueError(tag)


def cp_ints(data):
    """cp index -> int for CONSTANT_Integer entries (needed to resolve k / mv)."""
    p = 8
    n = struct.unpack(">H", data[p:p + 2])[0]; p += 2
    ints = {}
    i = 1
    while i < n:
        t = data[p]; p += 1
        if t == 1: p += 2 + struct.unpack(">H", data[p:p + 2])[0]
        elif t == 3: ints[i] = struct.unpack(">i", data[p:p + 4])[0]; p += 4
        elif t == 4: p += 4
        elif t in (5, 6): p += 8; i += 1
        elif t in (7, 8, 16, 19, 20): p += 2
        elif t in (9, 10, 11, 12, 17, 18): p += 4
        elif t == 15: p += 3
        i += 1
    return ints


def classify(data):
    m = parse_metadata(data)
    if m is None:
        return None
    ints = cp_ints(data)
    k = ints.get(m["k"]) if isinstance(m["k"], int) else m["k"]
    mv = tuple(ints.get(x) for x in m["mv"])
    return k, mv


def scan_zip(zf, label, rows, depth=0):
    tot = kt = tri = ktri = 0
    kinds = collections.Counter(); mvs = collections.Counter()
    for name in zf.namelist():
        if name.endswith(".jar") and depth < 4:
            try:
                scan_zip(zipfile.ZipFile(io.BytesIO(zf.read(name))), label + "!" + name, rows, depth + 1)
            except zipfile.BadZipFile:
                pass
            continue
        if not name.endswith(".class") or name.startswith("META-INF/versions/"):
            continue
        tot += 1
        is_tri = name.startswith(TRIDIUM_PREFIXES)
        tri += is_tri
        c = classify(zf.read(name))
        if c:
            kt += 1; ktri += is_tri
            kinds[c[0]] += 1; mvs[".".join(map(str, c[1]))] += 1
    rows.append((label, tot, kt, tri, ktri, dict(sorted(kinds.items())), dict(mvs)))


def main():
    rows = []
    jars = sorted(glob.glob(CONFIG + "/*.jar"))
    for root, _d, files in os.walk(INSTALL):
        for f in files:
            if f.endswith(".jar"):
                jars.append(os.path.join(root, f))
    for j in jars:
        scan_zip(zipfile.ZipFile(j), j.replace(INSTALL, "<install>").replace(CONFIG, "<config>/modules"), rows)
    w = sys.stdout.write
    w("jar\tclasses\tkotlin_classes\ttridium_classes\tkotlin_tridium_classes\tkinds\tmetadata_versions\n")
    for r in rows:
        w("\t".join(str(x) if not isinstance(x, dict) else json.dumps(x, sort_keys=True) for x in r) + "\n")
    hit = [r for r in rows if r[2]]
    sys.stderr.write("jar entries scanned (incl nested): %d; jars with >=1 Kotlin class: %d; Kotlin classes total: %d\n"
                     % (len(rows), len(hit), sum(r[2] for r in rows)))


if __name__ == "__main__":
    main()
