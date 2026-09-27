#!/usr/bin/env python3
"""n5-api-diff.py — compare the Java API surface between N4 and N5.

NEW tool for niagara5-research (no N4 kit equivalent). Two independent modes:

SOURCE mode (default) — compares DECOMPILED/SHIPPED .java SOURCE trees:
  N4 side : niagara-research's docSource-doc/extracted/ (real Tridium sources
            shipped in N4's docSource.jar, one dir per module, package
            javax.baja.*/com.tridium.*).
  N5 side : N5's docSource.jar read directly (zipfile), package niagara.*/
            com.tridium.* (see niagara5-block3.md B3-G2: the core API package
            prefix moved javax.baja.* -> niagara.*, near 1:1 method-for-method).

  Because of that rename, a naive per-package name match would report every
  renamed package as 100% removed + 100% added noise. This tool applies a
  PACKAGE-RENAME MAPPING before comparing: by default
  `javax.baja.<x> -> niagara.<x>` (repeatable --map old=new adds more rules,
  tried in order before the default; --no-default-map disables the built-in
  rule). A package is reported RENAMED (with member deltas) when it only
  matches its counterpart through a mapping rule, common/unchanged when the
  name matches unchanged (e.g. com.tridium.*), and reported as
  "no counterpart after mapping" when neither side's mapped name exists on
  the other.

  Per-type comparison is a LIGHTWEIGHT regex-based .java parser (documented
  limits below), not a real Java parser — good enough to answer "what public/
  protected method signatures were added/removed", not exhaustive for
  generics-heavy overloads or multi-line signatures.

  Limits (documented, not silently hidden):
    - Multi-line method signatures (return type or params wrapping across
      lines) are not matched.
    - Param "types" are extracted by naive comma-splitting; a generic param
      type containing an unbracketed comma (rare, e.g. a raw multi-arg
      functional type written without <>) will mis-split.
    - Overload resolution is by (name, paramCount, param head token) — this
      can conflate two overloads that only differ in a generic argument.
    - Type-level match is by SIMPLE class name within the mapped package; a
      type that was also renamed (not just its package) will show as
      removed+added, not RENAMED — only package renames are modeled.

BINARY mode (subcommand `binary`, i.e. --binary in spirit) — wraps japicmp
  (github.com/siom79/japicmp) 0.26.2 to do a real bytecode-level API diff
  between an N4 jar (or several, e.g. the -rt/-ux/-wb parts of one N4 module)
  and its N5 jar:
    python3 tools/n5-api-diff.py binary \\
        --old-jar path/to/N4/alarm-rt.jar --old-jar path/to/N4/alarm-ux.jar \\
        --old-jar path/to/N4/alarm-wb.jar --new-jar path/to/N5/alarm.jar
  Multiple --old-jar/--new-jar flags are joined with ';' (japicmp's own
  multi-jar separator) into one -o/-n argument. Requires:
    - tools/decompilers/japicmp-0.26.2-jar-with-dependencies.jar (gitignored;
      download URL + sha256 in tools/README.md — NOT fetched by this script).
    - java (default: /home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java,
      override with --java).
  Emits japicmp's own XML report (--xml-file, default a temp file, kept with
  --keep-xml) plus a compact summary parsed from it: total classes compared,
  added/removed/modified counts, binary-incompatible count, and a capped list
  of removed classes/methods. Because japicmp has no notion of the
  javax.baja->niagara rename, a binary diff across that rename reports the
  rename as wholesale removal+addition — this is documented, not a bug; use
  SOURCE mode (with --map) for rename-aware comparison, and BINARY mode for
  same-package (typically com.tridium.*) modules or as a raw bytecode cross-
  check. If japicmp itself fails (e.g. on Java 25 classfiles it cannot read),
  this command reports a typed failure and exits non-zero; it never silently
  falls back — SOURCE mode remains the primary, always-available comparison.

--json on all modes. Read-only; writes only an explicitly-requested report
file. Pure stdlib.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_N4_SOURCE = os.path.join(
    "/home/cristian/niagara-research/organized/docSource/docSource-doc/extracted"
)
DEFAULT_N5_DOCSOURCE_JAR = "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docSource.jar"

DEFAULT_JAPICMP_JAR = os.path.join(REPO_ROOT, "tools", "decompilers",
                                    "japicmp-0.26.2-jar-with-dependencies.jar")
DEFAULT_JAVA = "/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java"

DEFAULT_PACKAGE_MAP = [("javax.baja.", "niagara.")]


# ---------------------------------------------------------------------------
# Package rename mapping
# ---------------------------------------------------------------------------

def parse_map_args(map_args):
    """--map old=new (repeatable) -> [(old, new), ...], order preserved."""
    rules = []
    for spec in map_args or []:
        if "=" not in spec:
            raise ValueError(f"--map must be OLD=NEW, got: {spec!r}")
        old, new = spec.split("=", 1)
        rules.append((old, new))
    return rules


def map_package(pkg: str, rules) -> str:
    """Apply the first matching prefix rule to `pkg`; identity if none match.
    A rule (old, new) matches when pkg == old.rstrip('.') or pkg starts with
    old (old may or may not end in '.')."""
    for old, new in rules:
        old_dot = old if old.endswith(".") else old + "."
        if pkg == old.rstrip("."):
            return new.rstrip(".")
        if pkg.startswith(old_dot):
            return new.rstrip(".") + "." + pkg[len(old_dot):]
    return pkg


def effective_rules(user_rules, no_default_map: bool):
    return list(user_rules) + ([] if no_default_map else list(DEFAULT_PACKAGE_MAP))


# ---------------------------------------------------------------------------
# Lightweight .java parsing (documented limits — see module docstring)
# ---------------------------------------------------------------------------

_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
_TYPE_DECL_RE = re.compile(
    r"^\s*(?:public|protected)\s+(?:static\s+|final\s+|abstract\s+)*"
    r"(?:class|interface|enum|@interface)\s+(\w+)",
    re.MULTILINE,
)
_METHOD_RE = re.compile(
    r"^[ \t]*(public|protected)\s+"
    r"(?:static\s+|final\s+|abstract\s+|synchronized\s+|native\s+|default\s+)*"
    r"(?:<[^>]*>\s+)?"
    r"([\w.]+(?:<[^;{}]*?>)?(?:\[\])*)\s+"
    r"(\w+)\s*\(([^;{}]*)\)",
    re.MULTILINE,
)


def source_package(text: str) -> str | None:
    m = _PACKAGE_RE.search(text)
    return m.group(1) if m else None


def _param_types(params_str: str):
    params_str = params_str.strip()
    if not params_str:
        return []
    out = []
    for raw in params_str.split(","):
        tokens = raw.strip().split()
        if not tokens:
            continue
        # last token is the param name (possibly "...name" varargs / "name[]");
        # everything before it is the type.
        out.append(" ".join(tokens[:-1]) if len(tokens) > 1 else tokens[0])
    return out


def extract_public_methods(text: str):
    """Return a sorted list of 'methodName(type1,type2,...)' signatures for
    every public/protected method-looking declaration found (see module
    docstring for the documented matching limits)."""
    sigs = set()
    for m in _METHOD_RE.finditer(text):
        _modifier, _ret, name, params = m.groups()
        types = _param_types(params)
        sigs.add(f"{name}({','.join(types)})")
    return sorted(sigs)


def extract_type_names(text: str):
    return sorted(set(_TYPE_DECL_RE.findall(text)))


# ---------------------------------------------------------------------------
# Source trees: {package: {simple_class_name: source_text}}
# ---------------------------------------------------------------------------

def load_n4_source_tree(root_dir: str) -> dict:
    tree: dict = {}
    if not os.path.isdir(root_dir):
        return tree
    for dirpath, _dirs, files in os.walk(root_dir):
        for fname in files:
            if not fname.endswith(".java"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            pkg = source_package(text)
            if not pkg:
                continue
            cls = fname[:-5]
            tree.setdefault(pkg, {})[cls] = text
    return tree


def load_n5_source_tree_from_jar(jar_path: str) -> dict:
    tree: dict = {}
    if not os.path.isfile(jar_path):
        return tree
    with zipfile.ZipFile(jar_path) as z:
        for name in z.namelist():
            if not name.endswith(".java"):
                continue
            text = z.read(name).decode("utf-8", errors="replace")
            pkg = source_package(text)
            if not pkg:
                continue
            cls = os.path.basename(name)[:-5]
            tree.setdefault(pkg, {})[cls] = text
    return tree


# ---------------------------------------------------------------------------
# Source-mode comparison
# ---------------------------------------------------------------------------

def compare_type(n4_text: str, n5_text: str) -> dict:
    n4_methods = set(extract_public_methods(n4_text))
    n5_methods = set(extract_public_methods(n5_text))
    return {
        "methods_added": sorted(n5_methods - n4_methods),
        "methods_removed": sorted(n4_methods - n5_methods),
    }


def compare_source_trees(n4_tree: dict, n5_tree: dict, rules) -> dict:
    n4_pkgs = set(n4_tree)
    n5_pkgs = set(n5_tree)
    mapped_targets = {p: map_package(p, rules) for p in n4_pkgs}
    reached_n5 = set(mapped_targets.values()) & n5_pkgs

    packages = []
    n4_no_counterpart = []
    for n4_pkg, mapped in sorted(mapped_targets.items()):
        if mapped not in n5_pkgs:
            n4_no_counterpart.append(n4_pkg)
            continue
        n5_types = n5_tree[mapped]
        n4_types = n4_tree[n4_pkg]
        common = sorted(set(n4_types) & set(n5_types))
        entry = {
            "n4_package": n4_pkg,
            "n5_package": mapped,
            "renamed": mapped != n4_pkg,
            "types_added": sorted(set(n5_types) - set(n4_types)),
            "types_removed": sorted(set(n4_types) - set(n5_types)),
            "types_common": [
                {"type": t, **compare_type(n4_types[t], n5_types[t])}
                for t in common
            ],
        }
        packages.append(entry)

    n5_no_counterpart = sorted(n5_pkgs - reached_n5)

    return {
        "package_count_n4": len(n4_pkgs),
        "package_count_n5": len(n5_pkgs),
        "packages": packages,
        "n4_packages_no_counterpart": n4_no_counterpart,
        "n5_packages_no_counterpart": n5_no_counterpart,
    }


def summarize_source_diff(result: dict) -> dict:
    renamed = sum(1 for p in result["packages"] if p["renamed"])
    unchanged = len(result["packages"]) - renamed
    types_added = sum(len(p["types_added"]) for p in result["packages"])
    types_removed = sum(len(p["types_removed"]) for p in result["packages"])
    methods_added = sum(
        len(t["methods_added"]) for p in result["packages"] for t in p["types_common"]
    )
    methods_removed = sum(
        len(t["methods_removed"]) for p in result["packages"] for t in p["types_common"]
    )
    return {
        "packages_matched": len(result["packages"]),
        "packages_renamed": renamed,
        "packages_unchanged_name": unchanged,
        "packages_n4_no_counterpart": len(result["n4_packages_no_counterpart"]),
        "packages_n5_no_counterpart": len(result["n5_packages_no_counterpart"]),
        "types_added": types_added,
        "types_removed": types_removed,
        "methods_added": methods_added,
        "methods_removed": methods_removed,
    }


# ---------------------------------------------------------------------------
# Binary mode: japicmp wrapper
# ---------------------------------------------------------------------------

class JapicmpError(RuntimeError):
    """Typed failure for the --binary wrapper: missing jar, java failure, or
    an unparsable report. Source mode remains available regardless."""


def build_japicmp_command(java, japicmp_jar, old_jars, new_jars, xml_file,
                           access_modifier="protected", ignore_missing_classes=True,
                           html_file=None):
    if not old_jars:
        raise JapicmpError("--old-jar is required for --binary mode (repeatable)")
    if not new_jars:
        raise JapicmpError("--new-jar is required for --binary mode (repeatable)")
    cmd = [
        java, "-jar", japicmp_jar,
        "-o", ";".join(old_jars),
        "-n", ";".join(new_jars),
        "-a", access_modifier,
        "-x", xml_file,
    ]
    if ignore_missing_classes:
        cmd.append("--ignore-missing-classes")
    if html_file:
        cmd += ["--html-file", html_file]
    return cmd


def run_japicmp(java, japicmp_jar, old_jars, new_jars, access_modifier="protected",
                 html_file=None, xml_file=None, timeout=600):
    if not os.path.isfile(japicmp_jar):
        raise JapicmpError(
            f"japicmp jar not found at {japicmp_jar} — download it into "
            f"tools/decompilers/ first (see tools/README.md for the URL + sha256)"
        )
    if not os.path.isfile(java):
        raise JapicmpError(f"java not found at {java} (pass --java to override)")

    owns_tmp = xml_file is None
    if owns_tmp:
        fd, xml_file = tempfile.mkstemp(suffix=".xml", prefix="japicmp-")
        os.close(fd)

    cmd = build_japicmp_command(java, japicmp_jar, old_jars, new_jars, xml_file,
                                 access_modifier=access_modifier, html_file=html_file)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise JapicmpError(f"japicmp timed out after {timeout}s: {exc}") from exc
    except OSError as exc:
        raise JapicmpError(f"could not launch java/japicmp: {exc}") from exc

    if proc.returncode != 0:
        raise JapicmpError(
            f"japicmp exited {proc.returncode}\nstdout(tail): {proc.stdout[-2000:]}\n"
            f"stderr(tail): {proc.stderr[-2000:]}"
        )
    if not os.path.isfile(xml_file) or os.path.getsize(xml_file) == 0:
        raise JapicmpError("japicmp reported success but produced no XML report")

    try:
        summary = parse_japicmp_report(xml_file)
    finally:
        if owns_tmp:
            try:
                os.remove(xml_file)
            except OSError:
                pass
    return summary


def parse_japicmp_report(xml_path: str, max_listed: int = 25) -> dict:
    """Parse a japicmp XML report into a compact summary. See japicmp.xsd:
    each <class> carries changeStatus (NEW/REMOVED/MODIFIED/UNCHANGED) and
    binaryCompatible (true/false); each nested <method>/<constructor>/<field>
    carries the same two attributes."""
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raise JapicmpError(f"cannot parse japicmp XML report: {exc}") from exc

    classes_el = root.find("classes")
    classes = list(classes_el) if classes_el is not None else []

    by_status = {"NEW": 0, "REMOVED": 0, "MODIFIED": 0, "UNCHANGED": 0}
    binary_incompatible = 0
    removed_classes = []
    removed_methods = []
    added_methods = []

    for c in classes:
        status = c.get("changeStatus", "UNCHANGED")
        by_status[status] = by_status.get(status, 0) + 1
        if c.get("binaryCompatible") == "false":
            binary_incompatible += 1
        if status == "REMOVED":
            removed_classes.append(c.get("fullyQualifiedName"))
        for member_tag in ("methods", "constructors"):
            container = c.find(member_tag)
            if container is None:
                continue
            for m in container:
                mstatus = m.get("changeStatus")
                fqcn = c.get("fullyQualifiedName")
                mname = m.get("name", m.tag)
                if mstatus == "REMOVED":
                    removed_methods.append(f"{fqcn}#{mname}")
                elif mstatus == "NEW":
                    added_methods.append(f"{fqcn}#{mname}")

    return {
        "old_jar": root.get("oldJar"),
        "new_jar": root.get("newJar"),
        "total_classes_compared": len(classes),
        "classes_new": by_status.get("NEW", 0),
        "classes_removed": by_status.get("REMOVED", 0),
        "classes_modified": by_status.get("MODIFIED", 0),
        "classes_unchanged": by_status.get("UNCHANGED", 0),
        "binary_incompatible_classes": binary_incompatible,
        "removed_classes_sample": removed_classes[:max_listed],
        "removed_classes_total": len(removed_classes),
        "removed_methods_sample": removed_methods[:max_listed],
        "removed_methods_total": len(removed_methods),
        "added_methods_total": len(added_methods),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_source(args):
    rules = effective_rules(parse_map_args(args.map), args.no_default_map)
    n4_tree = load_n4_source_tree(args.n4_source)
    n5_tree = load_n5_source_tree_from_jar(args.n5_docsource_jar)
    if not n4_tree:
        sys.stderr.write(f"n5-api-diff: no .java sources found under {args.n4_source}\n")
    if not n5_tree:
        sys.stderr.write(f"n5-api-diff: no .java sources found in {args.n5_docsource_jar}\n")
    result = compare_source_trees(n4_tree, n5_tree, rules)
    summary = summarize_source_diff(result)

    if args.json:
        out = {"summary": summary}
        if not args.summary_only:
            out["detail"] = result
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    print("n5-api-diff (source mode) — N4 javax.baja.*/com.tridium.* vs N5 niagara.*/com.tridium.*")
    print(f"  packages: N4={summary_pkg_n4(result)} N5={summary_pkg_n5(result)} "
          f"matched={summary['packages_matched']} "
          f"(renamed={summary['packages_renamed']}, unchanged-name={summary['packages_unchanged_name']})")
    print(f"  no counterpart after mapping: N4-only={summary['packages_n4_no_counterpart']} "
          f"N5-only={summary['packages_n5_no_counterpart']}")
    print(f"  types:   added={summary['types_added']} removed={summary['types_removed']}")
    print(f"  methods: added={summary['methods_added']} removed={summary['methods_removed']}")
    if not args.summary_only:
        for p in result["packages"]:
            if not (p["types_added"] or p["types_removed"] or
                    any(t["methods_added"] or t["methods_removed"] for t in p["types_common"])):
                continue
            tag = "RENAMED" if p["renamed"] else "same-name"
            print(f"\n  [{tag}] {p['n4_package']} -> {p['n5_package']}")
            for t in p["types_added"]:
                print(f"      + type {t}")
            for t in p["types_removed"]:
                print(f"      - type {t}")
            for t in p["types_common"]:
                if t["methods_added"] or t["methods_removed"]:
                    print(f"      ~ type {t['type']}: +{len(t['methods_added'])} -{len(t['methods_removed'])} method(s)")


def summary_pkg_n4(result):
    return result["package_count_n4"]


def summary_pkg_n5(result):
    return result["package_count_n5"]


def cmd_binary(args):
    try:
        summary = run_japicmp(
            args.java, args.japicmp_jar, args.old_jar, args.new_jar,
            access_modifier=args.access_modifier, html_file=args.html_file,
            xml_file=args.xml_file,
        )
    except JapicmpError as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            sys.stderr.write(f"n5-api-diff --binary: {exc}\n")
            sys.stderr.write("Source mode remains available (omit --binary).\n")
        sys.exit(1)

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return
    print("n5-api-diff (binary mode via japicmp 0.26.2)")
    print(f"  old: {summary['old_jar']}")
    print(f"  new: {summary['new_jar']}")
    print(f"  classes compared: {summary['total_classes_compared']}  "
          f"new={summary['classes_new']} removed={summary['classes_removed']} "
          f"modified={summary['classes_modified']} unchanged={summary['classes_unchanged']}")
    print(f"  binary-incompatible classes: {summary['binary_incompatible_classes']}")
    print(f"  removed methods: {summary['removed_methods_total']} "
          f"(sample: {summary['removed_methods_sample'][:5]})")
    print(f"  added methods:   {summary['added_methods_total']}")


def build_parser():
    p = argparse.ArgumentParser(prog="n5-api-diff.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    src = sub.add_parser("source", help="source-level diff (default mode)")
    src.add_argument("--n4-source", default=DEFAULT_N4_SOURCE)
    src.add_argument("--n5-docsource-jar", default=DEFAULT_N5_DOCSOURCE_JAR)
    src.add_argument("--map", action="append", default=[],
                      help="OLD=NEW package-prefix rename rule, repeatable")
    src.add_argument("--no-default-map", action="store_true",
                      help="disable the built-in javax.baja.->niagara. rule")
    src.add_argument("--json", action="store_true")
    src.add_argument("--summary-only", action="store_true")
    src.set_defaults(func=cmd_source)

    binm = sub.add_parser("binary", help="binary (bytecode) diff via japicmp")
    binm.add_argument("--old-jar", action="append", default=[], required=False)
    binm.add_argument("--new-jar", action="append", default=[], required=False)
    binm.add_argument("--java", default=DEFAULT_JAVA)
    binm.add_argument("--japicmp-jar", default=DEFAULT_JAPICMP_JAR)
    binm.add_argument("--access-modifier", default="protected",
                       choices=["public", "protected", "package", "private"])
    binm.add_argument("--xml-file", default=None, help="keep the japicmp XML report at this path")
    binm.add_argument("--html-file", default=None)
    binm.add_argument("--json", action="store_true")
    binm.set_defaults(func=cmd_binary)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    if sys.version_info[0] < 3:
        sys.stderr.write("n5-api-diff: requires python3\n")
        sys.exit(3)
    main()
