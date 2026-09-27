"""
Permission-group report — reverse-maps declared java-permissions (from
META-INF/module.xml across the corpus) back to the 19 permission groups
documented in niagara-help/devguide/security/requestingPermissions.html.

Command:
  permission-report [--group NAME] [--severity MILD|MODERATE|SEVERE]

Output: one row per group with risk, signing-required flag, number of modules
that declare permissions mapping to that group, total entry count, and the
top 5 modules.

Mapping strategy: classify each (class, name) pair by (a) exact match or
(b) prefix match against the known Java permission pattern for each group.
Unmapped entries are aggregated under "(unmapped)".
"""

import re
from collections import defaultdict

from module_nav_lib.permissions import cmd_permissions_declared

# --- 19 permission groups with their Java permission signatures ---------

# Each rule: (class_name_exact_or_None, name_regex_or_None) => group
# class_name None means "any"; name_regex None means "any name".
# Order matters — first match wins.
_RULES = [
    # ACCESS_CLASS — RuntimePermission "accessClassInPackage.*"
    ("ACCESS_CLASS", "java.lang.RuntimePermission",
     re.compile(r"^accessClassInPackage\.")),
    # MANAGE_EXECUTION — specific Runtime names
    ("MANAGE_EXECUTION", "java.lang.RuntimePermission",
     re.compile(r"^(modifyThread|modifyThreadGroup|setContextClassLoader"
                r"|enableContextClassLoaderOverride|getClassLoader)$")),
    # MODIFY_IO_STREAMS — RuntimePermission "setIO"
    ("MODIFY_IO_STREAMS", "java.lang.RuntimePermission",
     re.compile(r"^setIO$")),
    # SHUTDOWN_HOOKS — RuntimePermission "shutdownHooks"
    ("SHUTDOWN_HOOKS", "java.lang.RuntimePermission",
     re.compile(r"^shutdownHooks$")),
    # GET_ENVIRONMENT_VARIABLES — RuntimePermission "getenv.*"
    ("GET_ENVIRONMENT_VARIABLES", "java.lang.RuntimePermission",
     re.compile(r"^getenv\.")),
    # LOAD_LIBRARIES — RuntimePermission "loadLibrary.*"
    ("LOAD_LIBRARIES", "java.lang.RuntimePermission",
     re.compile(r"^loadLibrary\.")),
    # REFLECTION — ReflectPermission "suppressAccessChecks"
    ("REFLECTION", "java.lang.reflect.ReflectPermission",
     re.compile(r"^suppressAccessChecks$")),
    # LOGGING — FilePermission logging/*  +  LoggingPermission "control"
    ("LOGGING", "java.util.logging.LoggingPermission",
     re.compile(r"^control$")),
    ("LOGGING", "java.io.FilePermission",
     re.compile(r"logging", re.IGNORECASE)),
    # BACKUPS — FilePermission backups/*  +  NiagaraBasicPermission RESTORE_BACKUP
    ("BACKUPS", "com.tridium.nre.security.NiagaraBasicPermission",
     re.compile(r"^RESTORE_BACKUP$")),
    ("BACKUPS", "java.io.FilePermission",
     re.compile(r"backups", re.IGNORECASE)),
    # DIAGNOSTICS — ManagementPermission
    ("DIAGNOSTICS", "java.lang.management.ManagementPermission", None),
    # KEY_STORE — KeyStorePermission / NiagaraBasicPermission KEY_RING
    ("KEY_STORE", "com.tridium.nre.security.KeyStorePermission", None),
    ("KEY_STORE", "com.tridium.nre.security.KeyRingPermission", None),
    # SIGNING — SigningPasswordPermission / NiagaraBasicPermission SIGNING
    ("SIGNING", "com.tridium.nre.security.SigningPasswordPermission", None),
    # AUTHENTICATION — AuthPermission, NiagaraBasicPermission session/user
    ("AUTHENTICATION", "javax.security.auth.AuthPermission",
     re.compile(r"^modifyPrincipals$")),
    ("AUTHENTICATION", "com.tridium.nre.security.NiagaraBasicPermission",
     re.compile(r"^(MODIFY_SESSION_IDS|GET_AUTHENTICATED_USER)$")),
    # MBEAN_PERMISSION
    ("MBEAN_PERMISSION", "javax.management.MBeanPermission", None),
    ("MBEAN_PERMISSION", "javax.management.MBeanTrustPermission", None),
    ("MBEAN_PERMISSION", "javax.management.MBeanServerPermission", None),
    # SET_SYSTEM_TIME — NiagaraBasicPermission "SET_TIME"
    ("SET_SYSTEM_TIME", "com.tridium.nre.security.NiagaraBasicPermission",
     re.compile(r"^SET_TIME$")),
    # SYSTEM_PROPERTIES — PropertyPermission
    ("SYSTEM_PROPERTIES", "java.util.PropertyPermission", None),
    # NETWORK_COMMUNICATION — NiagaraSocketPermission / URLPermission /
    # NetPermission / CryptoServicesPermission exportPrivateKey
    ("NETWORK_COMMUNICATION",
     "com.tridium.nre.security.NiagaraSocketPermission", None),
    ("NETWORK_COMMUNICATION", "java.net.URLPermission", None),
    ("NETWORK_COMMUNICATION", "java.net.NetPermission", None),
    ("NETWORK_COMMUNICATION", "java.net.SocketPermission", None),
    # UI — AWTPermission
    ("UI", "java.awt.AWTPermission", None),
    # RUNTIME_EXECUTION — FilePermission with action "execute"
    # (detected separately via action field in _classify_row)
]

_META = {
    # group => (severity, signed_required)
    "ACCESS_CLASS":               ("SEVERE",   True),
    "AUTHENTICATION":             ("MILD",     False),
    "BACKUPS":                    ("SEVERE",   False),
    "DIAGNOSTICS":                ("SEVERE",   False),
    "GET_ENVIRONMENT_VARIABLES":  ("MILD",     False),
    "KEY_STORE":                  ("MODERATE", False),
    "LOAD_LIBRARIES":             ("SEVERE",   False),
    "LOGGING":                    ("MODERATE", False),
    "MANAGE_EXECUTION":           ("MODERATE", False),
    "MBEAN_PERMISSION":           ("SEVERE",   True),
    "MODIFY_IO_STREAMS":          ("MODERATE", False),
    "NETWORK_COMMUNICATION":      ("MODERATE", False),
    "REFLECTION":                 ("SEVERE",   True),
    "RUNTIME_EXECUTION":          ("SEVERE",   False),
    "SET_SYSTEM_TIME":            ("MILD",     False),
    "SHUTDOWN_HOOKS":             ("MILD",     False),
    "SIGNING":                    ("-",        False),
    "SYSTEM_PROPERTIES":          ("MILD",     False),
    "THIRD_PARTY_PERMISSION":     ("SEVERE",   True),
    "UI":                         ("MILD",     False),
    "(unmapped)":                 ("-",        False),
}


def _classify(cls, name, action):
    """Return the group name this (class, name, action) tuple maps to."""
    # RUNTIME_EXECUTION — FilePermission with action=execute
    if (cls == "java.io.FilePermission" and "execute" in (action or "")):
        return "RUNTIME_EXECUTION"

    for group, rule_cls, rule_re in _RULES:
        if cls != rule_cls:
            continue
        if rule_re is None:
            return group
        if rule_re.search(name or ""):
            return group

    # Any non-Java / non-Niagara / non-BC class is THIRD_PARTY_PERMISSION
    if not (cls.startswith("java.") or cls.startswith("javax.")
            or cls.startswith("com.tridium.") or cls.startswith("org.bouncycastle.")):
        return "THIRD_PARTY_PERMISSION"

    return "(unmapped)"


def _collect_declared_rows():
    """Reuse the declared-permissions scanner but capture rows instead of
    printing them. We monkeypatch nothing — instead, we duplicate the small
    scan here. The scan is cheap (reads module.xml files once).
    """
    # Cheap duplication of the scan (no need for an API split yet): call
    # cmd_permissions_declared with a high limit and parse its output? No —
    # better to factor. We re-implement here to avoid coupling to print format.
    import glob
    import os
    import xml.etree.ElementTree as ET
    import sys as _sys
    from module_nav_lib.grep_search import (
        _load_class_index, _resolve_source_root, _print_source_root_error,
    )

    data = _load_class_index(".")
    if not data:
        return None
    meta_source = data.get("_meta", {}).get("source_root", "")
    root, tried = _resolve_source_root(meta_source)
    if not root:
        _print_source_root_error(tried)
        return None

    pattern = os.path.join(root, "*", "*", "extracted", "META-INF", "module.xml")
    rows = []
    modules_scanned = 0
    modules_with_perms = 0

    for xml_path in sorted(glob.glob(pattern)):
        submodule_dir = os.path.basename(
            os.path.dirname(os.path.dirname(os.path.dirname(xml_path))))
        modules_scanned += 1
        try:
            tree = ET.parse(xml_path)
        except (ET.ParseError, IOError, OSError):
            continue
        module_root = tree.getroot()
        perms_block = module_root.find("permissions")
        if perms_block is None:
            continue
        local_count = 0
        for jps in perms_block.findall("java-permissions"):
            perm_type = jps.get("type", "")
            for jp in jps.findall("java-permission"):
                rows.append({
                    "module": submodule_dir,
                    "type": perm_type,
                    "class": jp.get("class", "") or "",
                    "name": jp.get("name", "") or "",
                    "action": jp.get("action", "") or "",
                })
                local_count += 1
        if local_count:
            modules_with_perms += 1
    return {
        "rows": rows,
        "modules_scanned": modules_scanned,
        "modules_with_perms": modules_with_perms,
    }


def cmd_permission_report(base_dir, group_filter=None, severity_filter=None,
                          md_output=False):
    _ = base_dir
    scan = _collect_declared_rows()
    if scan is None:
        return
    rows = scan["rows"]

    by_group_entries = defaultdict(int)
    by_group_modules = defaultdict(set)
    top_per_group = defaultdict(lambda: defaultdict(int))
    class_counter = defaultdict(lambda: defaultdict(int))

    for r in rows:
        g = _classify(r["class"], r["name"], r["action"])
        by_group_entries[g] += 1
        by_group_modules[g].add(r["module"])
        top_per_group[g][r["module"]] += 1
        class_counter[g][r["class"]] += 1

    sorted_groups = sorted(
        by_group_entries.keys(),
        key=lambda g: (-len(by_group_modules[g]), g))

    if md_output:
        _print_md_report(
            scan, sorted_groups, by_group_entries, by_group_modules,
            class_counter, top_per_group,
            group_filter, severity_filter)
        return

    print("")
    print("=" * 72)
    print("  PERMISSION-GROUP REPORT")
    print("=" * 72)
    print("  module.xml scanned:      {}".format(scan["modules_scanned"]))
    print("  modules with permissions: {}".format(scan["modules_with_perms"]))
    print("  total java-permission entries: {}".format(len(rows)))
    print("")
    print("  Reference: niagara-help/devguide/security/requestingPermissions.html")
    print("")
    print("  {:28s} {:10s} {:7s} {:>8s} {:>8s}  TOP JAVA PERMISSION CLASSES".format(
        "GROUP", "SEVERITY", "SIGNED", "MODULES", "ENTRIES"))
    print("  " + "-" * 120)

    for g in sorted_groups:
        severity, signed = _META.get(g, ("-", False))
        if severity_filter and severity != severity_filter.upper():
            continue
        if group_filter and group_filter.upper() != g:
            continue
        top_classes = sorted(
            class_counter[g].items(), key=lambda x: -x[1])[:3]
        tc_str = ", ".join("{}({})".format(c.split(".")[-1], n)
                           for c, n in top_classes)
        print("  {:28s} {:10s} {:7s} {:>8d} {:>8d}  {}".format(
            g[:28], severity[:10], "yes" if signed else "-",
            len(by_group_modules[g]), by_group_entries[g], tc_str))

    if not (group_filter or severity_filter):
        print("")
        print("  Note: '(unmapped)' and 'THIRD_PARTY_PERMISSION' entries may "
              "indicate custom permission classes. Use --group <NAME> for the top modules.")

    if group_filter:
        g = group_filter.upper()
        print("")
        print("  TOP MODULES for {}:".format(g))
        for mod, cnt in sorted(top_per_group[g].items(),
                               key=lambda x: -x[1])[:10]:
            print("    {:32s} {:>6d} entries".format(mod[:32], cnt))
    print("")


def _print_md_report(scan, sorted_groups, by_group_entries, by_group_modules,
                     class_counter, top_per_group,
                     group_filter, severity_filter):
    """Markdown output variant with YAML frontmatter."""
    from datetime import datetime

    print("---")
    print("title: Permission-group report")
    print("generated: {}".format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
    print("source: tools/module_nav.py permission-report")
    print("modules_scanned: {}".format(scan["modules_scanned"]))
    print("modules_with_permissions: {}".format(scan["modules_with_perms"]))
    print("total_entries: {}".format(sum(by_group_entries.values())))
    if group_filter:
        print("group_filter: {}".format(group_filter.upper()))
    if severity_filter:
        print("severity_filter: {}".format(severity_filter.upper()))
    print("---")
    print("")
    print("# Permission-group report")
    print("")
    print("**Reference:** `niagara-help/devguide/security/requestingPermissions.html`")
    print("")
    print("## Summary")
    print("")
    print("| metric | value |")
    print("|--------|-------|")
    print("| `module.xml` scanned | {} |".format(scan["modules_scanned"]))
    print("| modules with `<permissions>` | {} |".format(scan["modules_with_perms"]))
    print("| total `java-permission` entries | {} |".format(sum(by_group_entries.values())))
    print("")
    print("## Groups")
    print("")
    print("| Group | Severity | Signed | Modules | Entries | Top classes |")
    print("|-------|----------|--------|--------:|--------:|-------------|")
    for g in sorted_groups:
        severity, signed = _META.get(g, ("-", False))
        if severity_filter and severity != severity_filter.upper():
            continue
        if group_filter and group_filter.upper() != g:
            continue
        top_classes = sorted(
            class_counter[g].items(), key=lambda x: -x[1])[:3]
        tc_str = ", ".join("`{}`({})".format(c.split(".")[-1], n)
                           for c, n in top_classes)
        anchor = g.lower().replace("_", "-").replace("(", "").replace(")", "")
        g_link = "[`{}`](#{}-)".format(g, anchor) if group_filter else "`{}`".format(g)
        print("| {} | {} | {} | {} | {} | {} |".format(
            g_link, severity, "yes" if signed else "—",
            len(by_group_modules[g]), by_group_entries[g], tc_str))
    print("")

    if group_filter:
        g = group_filter.upper()
        print("## Top modules — {}".format(g))
        print("")
        print("| Module | Entries |")
        print("|--------|--------:|")
        for mod, cnt in sorted(top_per_group[g].items(),
                               key=lambda x: -x[1])[:10]:
            print("| `{}` | {} |".format(mod, cnt))
        print("")
