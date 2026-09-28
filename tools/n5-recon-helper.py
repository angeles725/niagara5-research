#!/usr/bin/env python3
"""
n5-recon-helper.py — writes organized/<module>/recon.json for n5-decompile.sh.

Computes, from the already-extracted class files:
  - class count and class-file-major-version histogram (from the 4-byte header)
  - an obfuscation heuristic: fraction of top-level (non-nested) class simple
    names that are <= 2 characters, ZKM/proguard-style (a.class, b.class, ...)
  - docSource.jar coverage: how many of this module's classes have a matching
    original .java under organized/docSource/<module>/...
  - decompile failure markers left by the primary decompiler in its output
    (used as "decompile_failures" in recon.json; whole-module fallback is
    counted separately via --primary-status/--fallback-used)

Not a general-purpose library; kept intentionally small and dependency-free
(stdlib only) so the pipeline has no extra install step.
"""
import argparse
import json
import os
import struct
import sys


def iter_class_files(root):
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".class"):
                yield os.path.join(dirpath, f)


def class_major_version(path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(8)
        if len(head) < 8 or head[:4] != b"\xca\xfe\xba\xbe":
            return None
        _minor, major = struct.unpack(">HH", head[4:8])
        return major
    except OSError:
        return None


def obfuscation_heuristic(root):
    """Fraction of top-level class simple names with length <= 2 (a.class,
    b.class, Aa.class, ...). Nested classes ($-named) are excluded because
    short synthetic inner-class names (e.g. Foo$1) are normal, not obfuscation.
    """
    total = 0
    short = 0
    for path in iter_class_files(root):
        name = os.path.basename(path)[:-len(".class")]
        if "$" in name:
            continue
        total += 1
        # strip common non-obfuscated single-letter-prefix Niagara conventions
        # (B-prefixed BObject subclasses are long; this only catches truly
        # short raw names)
        if len(name) <= 2:
            short += 1
    ratio = (short / total) if total else 0.0
    return {"top_level_classes": total, "short_named": short, "ratio": round(ratio, 4)}


def docsource_coverage(extracted_root, docsource_root):
    if not os.path.isdir(docsource_root):
        return {"available": False, "covered": 0, "total": 0, "ratio": 0.0}
    total = 0
    covered = 0
    for path in iter_class_files(extracted_root):
        rel = os.path.relpath(path, extracted_root)
        top = rel.split("$")[0]
        if not top.endswith(".class"):
            continue
        total += 1
        java_rel = top[: -len(".class")] + ".java"
        if os.path.exists(os.path.join(docsource_root, java_rel)):
            covered += 1
    ratio = (covered / total) if total else 0.0
    return {"available": True, "covered": covered, "total": total, "ratio": round(ratio, 4)}


def count_decompile_markers(vineflower_dir):
    markers = ("// $VF: ", "Unable to fully decompile class", "COULD NOT DECOMPILE", "<unknown>")
    n = 0
    if not os.path.isdir(vineflower_dir):
        return 0
    for dirpath, _dirs, files in os.walk(vineflower_dir):
        for f in files:
            if not f.endswith(".java"):
                continue
            p = os.path.join(dirpath, f)
            try:
                with open(p, "r", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            if any(m in text for m in markers):
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", required=True)
    ap.add_argument("--jar", required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--extracted", required=True)
    ap.add_argument("--docsource", required=True)
    ap.add_argument("--signed", required=True)
    ap.add_argument("--sig-name", required=True)
    ap.add_argument("--primary-status", required=True)
    ap.add_argument("--primary-time", required=True)
    ap.add_argument("--fallback-used", required=True)
    ap.add_argument("--fallback-reason", required=True)
    # T24 (odd/tasks/decompiler-fidelity-audit.md): optional, only meaningful when a
    # whole-jar primary run originally timed out and vf_handle_primary_timeout
    # (tools/n5-decompile.sh) attempted to isolate the hanging class(es). Defaults keep
    # recon.json unchanged for every module where isolation never ran.
    ap.add_argument("--excluded-classes", default="[]")
    ap.add_argument("--isolate-time", default="0")
    ap.add_argument("--isolation-status", default="")
    ap.add_argument("--timeout-attempt-time", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    class_files = list(iter_class_files(args.extracted))
    majors = {}
    for p in class_files:
        m = class_major_version(p)
        if m is None:
            continue
        majors[str(m)] = majors.get(str(m), 0) + 1

    vineflower_dir = os.path.join(os.path.dirname(args.extracted), "vineflower")
    recon = {
        "module": args.module,
        "jar_path": args.jar,
        "jar_sha256": args.sha256,
        "class_count": len(class_files),
        "class_major_version_histogram": majors,
        "signed": args.signed == "true",
        "signature_file": json.loads(args.sig_name),
        "obfuscation_heuristic": obfuscation_heuristic(args.extracted),
        "docsource_coverage": docsource_coverage(args.extracted, args.docsource),
        "primary_decompiler": "vineflower-1.12.0",
        "primary_status": args.primary_status,
        "primary_time_seconds": int(args.primary_time),
        "fallback_decompiler": "cfr-0.152",
        "fallback_used": args.fallback_used == "true",
        "fallback_reason": args.fallback_reason,
        "decompile_failure_markers": count_decompile_markers(vineflower_dir),
        "excluded_classes": json.loads(args.excluded_classes),
        "isolate_time_seconds": int(args.isolate_time),
    }
    if args.isolation_status:
        recon["isolation_status"] = args.isolation_status
    if args.timeout_attempt_time:
        recon["primary_timeout_attempt_seconds"] = int(args.timeout_attempt_time)

    # T27: this v1 write used to replace recon.json wholesale, silently dropping
    # the "v2"/"cons" sub-objects that --variant runs merge in. Carry each one
    # over only while it still describes the SAME jar; a sub-object for an older
    # jar no longer matches the tree v1 just rebuilt, so it is dropped and named.
    dropped = []
    try:
        with open(args.out) as fh:
            previous = json.load(fh)
    except (OSError, ValueError):
        previous = {}
    for key in ("v2", "cons"):
        sub = previous.get(key)
        if not isinstance(sub, dict):
            continue
        if sub.get("jar_sha256") == args.sha256:
            recon[key] = sub
        else:
            dropped.append(key)
    if dropped:
        recon["dropped_stale_variants"] = dropped

    with open(args.out, "w") as fh:
        json.dump(recon, fh, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    sys.exit(main())
