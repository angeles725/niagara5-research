#!/usr/bin/env python3
"""n5-modules.py — inventory + diff for the N5 module set.

NEW tool for niagara5-research (no N4 kit equivalent covers this — it replaces
the N4 corpus's station-modules.py problem class, which read a LIVE station's
module list; N5 has no live station yet, so this reads the module JARS
directly from the N5 install's module directory).

N5 ships one jar per module (name.jar), unlike N4's split -rt/-ux/-wb/-se/-doc
jars. Each jar carries:
  - META-INF/module.xml   — name/vendor/vendorVersion/description, dependency
                            list, and the <types> registry.
  - module-info.class     — a real JPMS module descriptor (requires/exports),
                            parsed with tools/lib/moduleinfo.py (pure Python,
                            no `javap`/JVM dependency).

Subcommands:
  list                 every N5 module: name, vendor, vendorVersion, description,
                        dependency list, runtime-profile-hint counts (derived from
                        <type class=...> package segments — see below), and JPMS
                        requires/exports summary.
  diff-n4               N4 (collapsed -rt/-ux/-wb/-se/-doc -> base name) vs N5
                        module sets: added / removed / common, with the N4 parts
                        list per common/removed module.
  deps <module>          transitive module.xml <dependency> closure.
  show <module>          module.xml + JPMS summary for one module.

Runtime-profile hints: N5's <type class="..."> carries no explicit rt/ux/wb/px/se
attribute (module.xml is flat — one registry per module, not per profile, since
there is no profile split any more). This tool derives a HINT by scanning each
type's fully-qualified class name for a package segment that is exactly one of
rt/ux/wb/px/se (a real, still-observed Niagara package convention, e.g.
`com.tridium.alarm.ux.baja.BAlarmInstructionsTypeExt`) and counts them per
module; a type with no such segment is counted "unclassified". This is a
heuristic, not an authoritative profile split — document that in any report
that cites it.

--json / --csv on all subcommands. Read-only; never writes. Pure stdlib
(+ tools/lib/moduleinfo.py). Python3 -> exit 3.
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import moduleinfo  # noqa: E402

DEFAULT_N5_MODULES = "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
DEFAULT_N4_MODULES = "/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules"

_PROFILE_SEGMENTS = {"rt", "ux", "wb", "px", "se"}
_N4_SUFFIX_RE = re.compile(r"-(rt|ux|wb|se|doc)$")


def profile_hint_for_class(cls: str) -> str:
    """Heuristic runtime-profile hint from a class's package segments.
    Returns one of rt/ux/wb/px/se, or 'unclassified' if none match."""
    if not cls:
        return "unclassified"
    for seg in cls.split("."):
        if seg in _PROFILE_SEGMENTS:
            return seg
    return "unclassified"


def module_name_from_jar(path: str) -> str:
    base = os.path.basename(path)
    return base[:-4] if base.endswith(".jar") else base


def iter_jars(modules_dir: str):
    return sorted(glob.glob(os.path.join(modules_dir, "*.jar")))


def read_module_xml(jar_path: str) -> dict:
    """Parse META-INF/module.xml out of a module jar. Raises on any failure —
    callers report it rather than silently returning a partial record."""
    with zipfile.ZipFile(jar_path) as z:
        data = z.read("META-INF/module.xml")
    root = ET.fromstring(data)

    deps = [
        {"name": d.get("name"), "vendor": d.get("vendor"), "vendorVersion": d.get("vendorVersion")}
        for d in root.findall("./installation/dependencies/dependency")
    ]
    nres = [
        {"name": d.get("name"), "version": d.get("version")}
        for d in root.findall("./installation/dependencies/nre")
    ]

    types = []
    profile_hints: dict = {}
    for t in root.findall(".//type"):
        cls = t.get("class")
        types.append({"class": cls, "name": t.get("name")})
        hint = profile_hint_for_class(cls)
        profile_hints[hint] = profile_hints.get(hint, 0) + 1

    return {
        "name": root.get("name"),
        "vendor": root.get("vendor"),
        "vendorVersion": root.get("vendorVersion"),
        "description": root.get("description"),
        "moduleName": root.get("moduleName"),
        "schemaVersion": root.get("schemaVersion"),
        "releaseDate": root.get("releaseDate"),
        "dependencies": deps,
        "nre_dependencies": nres,
        "type_count": len(types),
        "profile_hints": profile_hints,
    }


def read_module_info(jar_path: str):
    """Return the parsed JPMS module descriptor, {'error': ...} on a parse
    failure, or None if the jar carries no module-info.class at all."""
    try:
        with zipfile.ZipFile(jar_path) as z:
            data = z.read("module-info.class")
    except KeyError:
        return None
    except Exception as exc:
        return {"error": f"cannot read module-info.class: {exc}"}
    try:
        return moduleinfo.parse_module_info(data)
    except moduleinfo.ClassFileError as exc:
        return {"error": str(exc)}


def build_module_record(jar_path: str, include_jpms: bool = True) -> dict:
    name = module_name_from_jar(jar_path)
    rec = {"module": name, "jar": os.path.basename(jar_path)}
    try:
        rec.update(read_module_xml(jar_path))
    except Exception as exc:
        rec["error"] = f"module.xml: {exc}"
        return rec

    if include_jpms:
        info = read_module_info(jar_path)
        if info is None:
            rec["jpms"] = None
        elif "error" in info:
            rec["jpms_error"] = info["error"]
        else:
            rec["jpms"] = {
                "name": info["name"],
                "requires": [r["name"] for r in info["requires"]],
                "requires_transitive": [r["name"] for r in info["requires"] if r["transitive"]],
                "exports": [e["package"] for e in info["exports"]],
            }
    return rec


# ---------------------------------------------------------------------------
# N4 module-set collapsing (for diff-n4)
# ---------------------------------------------------------------------------

def collapse_n4_modules(n4_modules_dir: str) -> dict:
    """{base_name: [part, ...]} from an N4 modules/ dir's *.jar filenames,
    stripping -rt/-ux/-wb/-se/-doc suffixes. A jar with no such suffix (e.g.
    baja.jar) is its own base with part 'main'."""
    out: dict = {}
    for path in sorted(glob.glob(os.path.join(n4_modules_dir, "*.jar"))):
        stem = module_name_from_jar(path)
        m = _N4_SUFFIX_RE.search(stem)
        if m:
            base = stem[: m.start()]
            part = m.group(1)
        else:
            base = stem
            part = "main"
        out.setdefault(base, []).append(part)
    for base in out:
        out[base].sort()
    return out


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render(rows, args, line_fn, empty="(none)", cols=None):
    if getattr(args, "json", False):
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    if getattr(args, "csv", False):
        if rows:
            keys = cols or list(rows[0].keys())
            w = csv.writer(sys.stdout)
            w.writerow(keys)
            for r in rows:
                w.writerow([r.get(k, "") for k in keys])
        return
    if not rows:
        print(empty)
        return
    for r in rows:
        print(line_fn(r))


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_list(args):
    jars = iter_jars(args.modules_dir)
    rows = [build_module_record(j, include_jpms=not args.no_jpms) for j in jars]

    def line(r):
        if "error" in r and "name" not in r:
            return f"{r['module']:<28} ERROR: {r['error']}"
        hints = ",".join(f"{k}={v}" for k, v in sorted(r.get("profile_hints", {}).items()))
        return (f"{r['module']:<28} v{r.get('vendorVersion','?'):<10} "
                f"deps={len(r.get('dependencies', [])):<3} types={r.get('type_count', 0):<4} "
                f"[{hints}]")

    _render(rows, args, line, cols=["module", "vendor", "vendorVersion", "description",
                                     "type_count", "dependencies", "profile_hints"])


def cmd_diff_n4(args):
    n4 = collapse_n4_modules(args.n4_modules_dir)
    n5_jars = iter_jars(args.modules_dir)
    n5_names = {module_name_from_jar(j) for j in n5_jars}
    n4_names = set(n4.keys())

    added = sorted(n5_names - n4_names)
    removed = sorted(n4_names - n5_names)
    common = sorted(n4_names & n5_names)

    result = {
        "n4_module_count": len(n4_names),
        "n5_module_count": len(n5_names),
        "added_in_n5": added,
        "removed_from_n4": [{"module": m, "n4_parts": n4[m]} for m in removed],
        "common": [{"module": m, "n4_parts": n4[m]} for m in common],
    }

    if getattr(args, "json", False):
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"N4 modules (collapsed): {result['n4_module_count']}  "
          f"N5 modules: {result['n5_module_count']}")
    print(f"\nAdded in N5 ({len(added)}):")
    for m in added:
        print(f"  + {m}")
    print(f"\nRemoved from N4 ({len(removed)}):")
    for r in result["removed_from_n4"]:
        print(f"  - {r['module']}  (N4 parts: {','.join(r['n4_parts'])})")
    print(f"\nCommon ({len(common)}):")
    if args.verbose:
        for r in result["common"]:
            print(f"  = {r['module']}  (N4 parts: {','.join(r['n4_parts'])})")
    else:
        print(f"  {len(common)} module(s) present in both (use --verbose to list)")


def cmd_deps(args):
    jars = {module_name_from_jar(j): j for j in iter_jars(args.modules_dir)}
    if args.module not in jars:
        sys.stderr.write(f"n5-modules: no such module: {args.module}\n")
        sys.exit(1)

    seen = set()
    order = []

    def visit(name):
        if name in seen or name not in jars:
            return
        seen.add(name)
        try:
            info = read_module_xml(jars[name])
        except Exception:
            order.append({"module": name, "depth": len(order), "error": "unreadable"})
            return
        for d in info["dependencies"]:
            visit(d["name"])
        order.append({"module": name})

    visit(args.module)
    rows = [r for r in order if r["module"] != args.module] if not args.include_self else order
    _render(rows, args, lambda r: r["module"])


def cmd_show(args):
    jars = {module_name_from_jar(j): j for j in iter_jars(args.modules_dir)}
    if args.module not in jars:
        sys.stderr.write(f"n5-modules: no such module: {args.module}\n")
        sys.exit(1)
    rec = build_module_record(jars[args.module], include_jpms=not args.no_jpms)
    if getattr(args, "json", False):
        print(json.dumps(rec, indent=2, ensure_ascii=False))
        return
    print(f"module        : {rec.get('name')}")
    print(f"vendor        : {rec.get('vendor')} {rec.get('vendorVersion')}")
    print(f"description   : {rec.get('description')}")
    print(f"schemaVersion : {rec.get('schemaVersion')}")
    print(f"types         : {rec.get('type_count')}")
    print(f"profile hints : {rec.get('profile_hints')}")
    print("dependencies  :")
    for d in rec.get("dependencies", []):
        print(f"  - {d['name']} ({d['vendor']} {d['vendorVersion']})")
    if rec.get("jpms"):
        j = rec["jpms"]
        print(f"jpms module   : {j['name']}")
        print(f"  requires    : {', '.join(j['requires']) or '(none)'}")
        print(f"  exports     : {len(j['exports'])} package(s)")
    elif rec.get("jpms_error"):
        print(f"jpms module   : ERROR: {rec['jpms_error']}")


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(prog="n5-modules.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--modules-dir", default=DEFAULT_N5_MODULES,
                    help=f"N5 modules directory (default: {DEFAULT_N5_MODULES})")
    common_out = argparse.ArgumentParser(add_help=False)
    common_out.add_argument("--json", action="store_true")
    common_out.add_argument("--csv", action="store_true")

    sub = p.add_subparsers(dest="cmd", required=True)

    ls = sub.add_parser("list", parents=[common_out], help="list every N5 module")
    ls.add_argument("--no-jpms", action="store_true", help="skip module-info.class parsing (faster)")
    ls.set_defaults(func=cmd_list)

    dn4 = sub.add_parser("diff-n4", parents=[common_out],
                          help="N4 (collapsed) vs N5 module set diff")
    dn4.add_argument("--n4-modules-dir", default=DEFAULT_N4_MODULES,
                      help=f"N4 modules directory (default: {DEFAULT_N4_MODULES})")
    dn4.add_argument("--verbose", action="store_true", help="also list the common modules")
    dn4.set_defaults(func=cmd_diff_n4)

    dep = sub.add_parser("deps", parents=[common_out], help="transitive dependency closure")
    dep.add_argument("module")
    dep.add_argument("--include-self", action="store_true")
    dep.set_defaults(func=cmd_deps)

    sh = sub.add_parser("show", parents=[common_out], help="module.xml + JPMS summary")
    sh.add_argument("module")
    sh.add_argument("--no-jpms", action="store_true")
    sh.set_defaults(func=cmd_show)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    if sys.version_info[0] < 3:
        sys.stderr.write("n5-modules: requires python3\n")
        sys.exit(3)
    main()
