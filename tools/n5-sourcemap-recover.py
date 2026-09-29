#!/usr/bin/env python3
"""
n5-sourcemap-recover.py — recover the original sources embedded in shipped source maps (B119).

Walks <organized-dir>/<module>/extracted/**/*.map (only the byte-exact `extracted/` tree, never the
decompiler copies, and never `_`-prefixed pseudo-modules), and for every JSON source map that carries
`sourcesContent` writes each original to <out-dir>/<module>/<normalized source path>, plus a
deterministic manifest.json (map sha256, source path as written in the map, normalized path, content
sha256, status). Maps without `sourcesContent` are listed in the manifest with status
`no-sourcesContent` and write nothing.

Usage:
  n5-sourcemap-recover.py --organized-dir DIR [--out-dir DIR]     (default out-dir: DIR/_sourcemaps)
Exit: 0 ok, 2 usage/read error.

Path safety (pinned by tools/tests/test_n5_sourcemap_recover.py):
  * `webpack:///`, `webpack://<ns>/` prefixes and a leading `./` are removed; backslashes become `/`.
  * Absolute paths, drive letters, NUL bytes, empty results and any `..` segment that is NOT part of the
    leading run are rejected (status rejected-unsafe-path).
  * A LEADING run of `../` is stripped and its length recorded as `parent_dirs_stripped`: real maps point
    out of the jar at the vendor build tree (`../../../../src/rc/x.js`), so rejecting every `..` would
    recover nothing. The stripped path is always contained in <out-dir>/<module>; a final realpath
    containment check guards every write.
  * A second source normalizing to an already-written path with different bytes is reported as
    `collision` and never overwrites.
"""
import argparse
import hashlib
import json
import os
import sys

_SCHEMES = ("webpack:///", "webpack://")


def normalize_source(raw):
    """Return (safe_relative_posix_path, leading_parent_dirs_stripped) or None when unsafe."""
    if not isinstance(raw, str) or "\0" in raw:
        return None
    s = raw.replace("\\", "/")
    if len(s) >= 2 and s[1] == ":" and s[0].isalpha():
        return None
    if s.startswith("webpack:///"):
        s = s[len("webpack:///"):]
    elif s.startswith("webpack://"):
        rest = s[len("webpack://"):]
        s = rest.split("/", 1)[1] if "/" in rest else ""
    if s.startswith("/") or "://" in s:
        return None
    segs = [x for x in s.split("/") if x not in ("",)]
    stripped = 0
    while segs and segs[0] in (".", ".."):
        if segs[0] == "..":
            stripped += 1
        segs.pop(0)
    if not segs or any(x in ("..",) for x in segs):
        return None
    segs = [x for x in segs if x != "."]
    if not segs:
        return None
    return "/".join(segs), stripped


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _contained(base, target):
    base = os.path.realpath(base)
    target = os.path.realpath(target)
    return os.path.commonpath([base, target]) == base and target != base


def _find_maps(organized):
    for module in sorted(os.listdir(organized)):
        if module.startswith("_"):
            continue
        root = os.path.join(organized, module, "extracted")
        if not os.path.isdir(root):
            continue
        found = []
        for d, dirs, files in os.walk(root):
            dirs.sort()
            found.extend(os.path.join(d, f) for f in files if f.endswith(".map"))
        for p in sorted(found):
            yield module, p


def recover(organized, out_dir):
    written = {}  # rel out path -> content sha256
    maps = []
    summary = dict(maps=0, maps_with_sourcesContent=0, maps_not_sourcemap=0, sources=0, recovered=0,
                   duplicate=0, no_sourcesContent=0, no_content=0, collision=0, rejected_unsafe_path=0)
    for module, path in _find_maps(organized):
        raw = open(path, "rb").read()
        rec = {"map": os.path.relpath(path, organized).replace(os.sep, "/"), "module": module,
               "map_sha256": _sha(raw)}
        summary["maps"] += 1
        try:
            j = json.loads(raw.decode("utf-8-sig"))
            if not (isinstance(j, dict) and isinstance(j.get("sources"), list) and "mappings" in j):
                raise ValueError("no sources/mappings")
        except ValueError:
            rec["status"] = "not-a-sourcemap"
            summary["maps_not_sourcemap"] += 1
            maps.append(rec)
            continue
        sc = j.get("sourcesContent")
        has_sc = isinstance(sc, list) and len(sc) > 0
        rec.update(status="ok", file=j.get("file"), has_sourcesContent=has_sc, sources=[])
        summary["maps_with_sourcesContent"] += int(has_sc)
        for i, src in enumerate(j["sources"]):
            summary["sources"] += 1
            e = {"source": src}
            content = sc[i] if has_sc and i < len(sc) else None
            if not has_sc:
                e["status"] = "no-sourcesContent"
                summary["no_sourcesContent"] += 1
            elif not isinstance(content, str):
                e["status"] = "no-content"
                summary["no_content"] += 1
            else:
                norm = normalize_source(src)
                if norm is None:
                    e["status"] = "rejected-unsafe-path"
                    summary["rejected_unsafe_path"] += 1
                else:
                    rel, stripped = norm
                    outrel = module + "/" + rel
                    data = content.encode("utf-8")
                    dest = os.path.join(out_dir, *outrel.split("/"))
                    e["path"] = outrel
                    e["content_sha256"] = _sha(data)
                    if stripped:
                        e["parent_dirs_stripped"] = stripped
                    if not _contained(os.path.join(out_dir, module), dest):
                        e["status"] = "rejected-unsafe-path"
                        summary["rejected_unsafe_path"] += 1
                    elif outrel in written:
                        if written[outrel] == e["content_sha256"]:
                            e["status"] = "duplicate"
                            summary["duplicate"] += 1
                        else:
                            e["status"] = "collision"
                            summary["collision"] += 1
                    else:
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with open(dest, "wb") as fh:
                            fh.write(data)
                        written[outrel] = e["content_sha256"]
                        e["status"] = "recovered"
                        summary["recovered"] += 1
            rec["sources"].append(e)
        maps.append(rec)
    os.makedirs(out_dir, exist_ok=True)
    manifest = {"schema": "n5-sourcemap-recover.v1", "summary": summary, "maps": maps}
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--organized-dir", required=True)
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.organized_dir):
        print("error: --organized-dir is not a directory: %s" % a.organized_dir, file=sys.stderr)
        return 2
    out = a.out_dir or os.path.join(a.organized_dir, "_sourcemaps")
    s = recover(a.organized_dir, out)
    print("maps %d (with sourcesContent %d, not a source map %d) | sources %d | recovered %d, duplicate %d, "
          "no-sourcesContent %d, no-content %d, collision %d, rejected %d -> %s" % (
              s["maps"], s["maps_with_sourcesContent"], s["maps_not_sourcemap"], s["sources"], s["recovered"],
              s["duplicate"], s["no_sourcesContent"], s["no_content"], s["collision"], s["rejected_unsafe_path"], out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
