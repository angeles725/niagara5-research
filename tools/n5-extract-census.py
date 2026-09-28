#!/usr/bin/env python3
"""
n5-extract-census.py — extraction completeness + byte-integrity census for the
N5 decompile pipeline (tools/n5-decompile.sh -> organized/<mod>/).

Question it answers: are the bytes the corpus analysed exactly the vendor's jar
bytes, and was anything inside a jar left unanalysed (nested LIB-INF jars,
multi-release version entries, native payloads, minified JS)?

Subcommands:
  module <jar> <moddir> [--release N] [--json]
      Census one module jar against organized/<mod>/{extracted,resources,
      vineflower,fallback}. Exit 0 = byte-exact and complete, 1 = at least one
      class mismatch/missing or resource mismatch/missing, 2 = usage/read error.
  sweep <jar-dir> <organized-dir> [--release N] [--json]
      Run `module` for every <jar-dir>/*.jar that has organized/<stem>/recon.json
      and print an aggregate. Same exit convention (1 if any module is not clean).

Rules (each pinned by tools/tests/test_n5_extract_census.py):
  * Byte-exactness: sha256 of each jar entry vs the file at extracted/<entry>
    (classes) and resources/<entry> (every non-.class file).
  * Nested jars: an entry whose bytes are a ZIP is opened in memory; its
    classes, Tridium-namespace share (com/tridium/, niagara/, javax/baja/),
    Multi-Release flag and version entries are reported. A nested class counts
    as "decompiled" only if vineflower/ or fallback/ holds <path>.java for its
    top-level class (the pipeline decompiles the outer jar only).
  * Multi-Release: honoured only when the jar MANIFEST says `Multi-Release: true`
    (JarFile semantics); for release N the JVM loads the highest
    META-INF/versions/<v>/ entry with v <= N, else the base entry.
  * Native payloads: detected by magic bytes (PE "MZ", ELF, Mach-O), not by name.
  * Minified JS: longest line >= 1000 bytes or mean line length >= 250 bytes.
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile

TRIDIUM_PREFIXES = ("com/tridium/", "niagara/", "javax/baja/")
VERSIONS_RE = re.compile(r"^META-INF/versions/(\d+)/(.+)$")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def tridium_share(names):
    classes = [n for n in names if n.endswith(".class")]
    trid = sum(1 for n in classes if n.startswith(TRIDIUM_PREFIXES))
    return trid, len(classes)


def native_format(data):
    if data[:2] == b"MZ":
        return "PE"
    if data[:4] == b"\x7fELF":
        return "ELF"
    if data[:4] in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xfe\xed\xfa\xce"):
        return "Mach-O"
    return None


def is_minified_js(data):
    lines = data.split(b"\n")
    if not lines:
        return False
    longest = max(len(line) for line in lines)
    mean = len(data) / len(lines)
    return longest >= 1000 or mean >= 250


def _is_multi_release(zf):
    try:
        mf = zf.read("META-INF/MANIFEST.MF").decode("utf-8", "replace")
    except KeyError:
        return False
    return any(line.strip().lower() == "multi-release: true" for line in mf.splitlines())


def mr_resolution(zf, release):
    """Return (versions, selected) where selected maps a logical class path to the
    entry the JVM would load for `release`, only for classes overridden by a version entry."""
    if not _is_multi_release(zf):
        return [], {}
    versions = set()
    per_path = {}
    for name in zf.namelist():
        mt = VERSIONS_RE.match(name)
        if not mt:
            continue
        v, rel = int(mt.group(1)), mt.group(2)
        versions.add(v)
        if rel.endswith(".class") and v <= release:
            if rel not in per_path or v > per_path[rel]:
                per_path[rel] = v
    selected = {rel: f"META-INF/versions/{v}/{rel}" for rel, v in per_path.items()}
    return sorted(versions), selected


def _top_level_java(class_name):
    base = class_name[:-len(".class")]
    mt = VERSIONS_RE.match(base)
    if mt:
        base = mt.group(2)
    return base.split("$", 1)[0] + ".java"


def nested_jar_census(name, data, release):
    zf = zipfile.ZipFile(io.BytesIO(data))
    names = [n for n in zf.namelist() if not n.endswith("/")]
    trid, total = tridium_share(names)
    versions, selected = mr_resolution(zf, release)
    natives = []
    for n in names:
        fmt = native_format(zf.read(n)[:8])
        if fmt:
            natives.append({"name": n, "format": fmt, "sha256": sha256(zf.read(n))})
    return {
        "name": name,
        "sha256": sha256(data),
        "size": len(data),
        "classes": total,
        "tridium_classes": trid,
        "signed": any(n.startswith("META-INF/") and n.upper().endswith(".SF") for n in names),
        "multi_release": _is_multi_release(zf),
        "mr_versions": versions,
        "mr_selected": selected,
        "mr_overridden_classes": len(selected),
        "class_names": [n for n in names if n.endswith(".class")],
        "natives": natives,
    }


def _read_file(path):
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return None


def census_module(jar, moddir, release=25):
    zf = zipfile.ZipFile(jar)
    result = {
        "jar": jar,
        "jar_sha256": sha256(_read_file(jar)),
        "moddir": moddir,
        "classes": {"checked": 0, "mismatched": [], "missing": []},
        "resources": {"expected": 0, "present_exact": 0, "mismatched": [], "missing": []},
        "nested": [],
        "nested_classes_total": 0,
        "nested_classes_decompiled": 0,
        "natives": [],
        "js": {"total": 0, "minified": 0, "source_maps": 0},
        "multi_release": _is_multi_release(zf),
    }
    ext_dir = os.path.join(moddir, "extracted")
    res_dir = os.path.join(moddir, "resources")
    decomp_dirs = [os.path.join(moddir, "vineflower"), os.path.join(moddir, "fallback")]
    for info in zf.infolist():
        name = info.filename
        if name.endswith("/"):
            continue
        data = zf.read(name)
        if name.endswith(".class"):
            result["classes"]["checked"] += 1
            got = _read_file(os.path.join(ext_dir, name))
            if got is None:
                result["classes"]["missing"].append(name)
            elif sha256(got) != sha256(data):
                result["classes"]["mismatched"].append(name)
            continue
        result["resources"]["expected"] += 1
        got = _read_file(os.path.join(res_dir, name))
        if got is None:
            result["resources"]["missing"].append(name)
        elif sha256(got) != sha256(data):
            result["resources"]["mismatched"].append(name)
        else:
            result["resources"]["present_exact"] += 1
        lower = name.lower()
        if lower.endswith(".js"):
            result["js"]["total"] += 1
            if is_minified_js(data):
                result["js"]["minified"] += 1
        elif lower.endswith(".map"):
            result["js"]["source_maps"] += 1
        fmt = native_format(data[:8])
        if fmt:
            result["natives"].append({"name": name, "format": fmt, "sha256": sha256(data),
                                      "size": len(data)})
        if data[:4] == b"PK\x03\x04":
            try:
                nested = nested_jar_census(name, data, release)
            except zipfile.BadZipFile:
                continue
            decompiled = 0
            tops = {_top_level_java(c) for c in nested["class_names"]
                    if not c.endswith("module-info.class")}
            for top in tops:
                if any(os.path.isfile(os.path.join(d, top)) for d in decomp_dirs):
                    decompiled += 1
            nested["top_level_classes"] = len(tops)
            nested["top_level_decompiled"] = decompiled
            del nested["class_names"]
            result["nested"].append(nested)
            result["nested_classes_total"] += nested["classes"]
            result["nested_classes_decompiled"] += decompiled
    return result


def is_clean(r):
    return not (r["classes"]["mismatched"] or r["classes"]["missing"]
                or r["resources"]["mismatched"] or r["resources"]["missing"])


def sweep(jar_dir, organized, release=25):
    modules = []
    for fn in sorted(os.listdir(jar_dir)):
        if not fn.endswith(".jar"):
            continue
        moddir = os.path.join(organized, fn[:-4])
        if not os.path.isfile(os.path.join(moddir, "recon.json")):
            continue
        modules.append(census_module(os.path.join(jar_dir, fn), moddir, release))
    agg = {
        "modules": len(modules),
        "classes_checked": sum(m["classes"]["checked"] for m in modules),
        "class_mismatches": sum(len(m["classes"]["mismatched"]) for m in modules),
        "class_missing": sum(len(m["classes"]["missing"]) for m in modules),
        "resources_expected": sum(m["resources"]["expected"] for m in modules),
        "resource_mismatches": sum(len(m["resources"]["mismatched"]) for m in modules),
        "resource_missing": sum(len(m["resources"]["missing"]) for m in modules),
        "nested_jars": sum(len(m["nested"]) for m in modules),
        "nested_classes_total": sum(m["nested_classes_total"] for m in modules),
        "nested_top_level_decompiled": sum(m["nested_classes_decompiled"] for m in modules),
        "natives": sum(len(m["natives"]) for m in modules),
        "js_total": sum(m["js"]["total"] for m in modules),
        "js_minified": sum(m["js"]["minified"] for m in modules),
        "unclean_modules": [os.path.basename(m["moddir"]) for m in modules if not is_clean(m)],
    }
    return agg, modules


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("module")
    p1.add_argument("jar")
    p1.add_argument("moddir")
    p2 = sub.add_parser("sweep")
    p2.add_argument("jar_dir")
    p2.add_argument("organized")
    p2.add_argument("--detail", help="write per-module JSON to this path")
    for p in (p1, p2):
        p.add_argument("--release", type=int, default=25)
        p.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "module":
            r = census_module(args.jar, args.moddir, args.release)
            clean = is_clean(r)
            out = r
        else:
            agg, mods = sweep(args.jar_dir, args.organized, args.release)
            if args.detail:
                with open(args.detail, "w") as fh:
                    json.dump(mods, fh, indent=1)
            clean = not agg["unclean_modules"]
            out = agg
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(out, indent=1))
    else:
        for k, v in out.items():
            if not isinstance(v, (list, dict)):
                print(f"{k}: {v}")
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
