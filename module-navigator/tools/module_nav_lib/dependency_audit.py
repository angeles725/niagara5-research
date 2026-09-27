"""
Dependency Audit for Module Navigator (Batch 5, Gap #14).

Detects third-party and honeywell add-on dependencies that may require
separate licenses or be unavailable in standard Supervisor deployments.

Commands:
  dependency-audit <module> [--json]
"""

import json
import os
from collections import defaultdict

# ---------------------------------------------------------------------------
# Known platform packages (always available in any Supervisor N4)
# These are the core Niagara N4 platform packages
# ---------------------------------------------------------------------------
_PLATFORM_PACKAGES = {
    # Core Baja framework
    'jakarta.',
    'javax.baja.',
    'javax.xml.',
    'org.xml.',
    'org.w3c.',
    # baja packages
    'baja.',
    'bajaux.',
    'bajaui.',
    # tridium platform
    'com.tridium.',
    # JDK standard packages
    'java.',
    'javax.',
    'sun.',
    'com.sun.',
    # Scripting
    'org.mozilla.javascript.',
    # BTnet protocol
    'com.tridium.btnet.',
    # NiagaraDataBeans
    'com.niagara.',
    # Utility packages found in platform
    'com.icl.',
    'org.activeio.',
    # Lowagie (iText) for PDF — included in platform
    'com.lowagie.',
    # Apache XML beans (used by platform)
    'org.apache.xmlbeans.',
    # log4j in some older versions
    'org.apache.log4j.',
    'org.slf4j.',
    # Protocol buffers (used by some drivers)
    'com.google.protobuf.',
    # Jython (sometimes bundled)
    'org.python.',
    # Commons codec/net/http components used by web-rt/platform
    'org.apache.commons.codec.',
    'org.apache.commons.net.',
    'org.apache.commons.httpclient.',
    'org.apache.http.',
    # Commons Lang3 and Math3 (used by platform Alarm extensions)
    'org.apache.commons.lang3.',
    'org.apache.commons.math3.',
    'org.apache.commons.collections4.',
    # Apache POI (used by alarm-rt for Excel export)
    'org.apache.poi.',
    # Apache Velocity (used by alarm-rt)
    'org.apache.velocity.',
    # Apache Qpid Proton (AMQP, used by platform)
    'org.apache.qpid.proton.',
    # Jackson used by web-rt/platform
    'com.fasterxml.aether.',
    # Kotlin (sometimes bundled)
    'kotlin.',
    'kotlinx.',
    # Internal Niagara packages
    'com.tridium.nre.',
    'com.tridium.sys.',
    'com.tridium.util.',
    'com.tridium.driver.',
}

# Known Honeywell add-on packages (pre-installed in Honeywell distributions)
_HONEYWELL_PACKAGES = {
    'cl.',
    'clHVAC.',
    'clAlarm.',
    'clWeather.',
    'clLighting.',
    'clEnergy.',
    'clSecurity.',
    'clFire.',
    'clBACnet.',
    'clN2.',
    'clModbus.',
    'clLon.',
    'clMbus.',
    'clPortal.',
    'clDashboard.',
    'clReport.',
    'clAudit.',
    'clCredential.',
    'clAccess.',
}

# Third-party packages requiring separate licenses
_THIRD_PARTY_PACKAGES = {
    # AWS
    'com.amazonaws.',
    # Microsoft
    'com.microsoft.',
    'com.microsoft.sqlserver.',
    'com.sun.media.jpeg.',  # JAI ImageIO
    # Google
    'com.google.',
    # Apache (non-platform)
    'org.apache.poi.',
    'org.apache.httpcomponents.',
    'org.apache.jackrabbit.',
    'org.apache.chemistry.',
    'org.apache.pdfbox.',
    'org.apache.commons.io.',
    'org.apache.commons.lang.',
    'org.apache.commons.collections.',
    'org.apache.commons.configuration.',
    'org.apache.shiro.',
    # OPC UA
    'com.prosysopc.',
    'org.opcfoundation.',
    'org-opcua.',
    # oBix
    'obix.',
    # ThingWorx
    'com.thingworx.',
    # Database drivers
    'oracle.',
    'oracle.jdbc.',
    'com.mysql.',
    'org.postgresql.',
    'com.embeddedMQ.',
    # Other commercial
    'com.factorypm.',
    'com.se.wiser.',
    'com.energyict.',
    'com.energymonitor.',
    # Honeywell commercial products (CBus, etc.)
    'com.honeywell.',
    # Tridium extensions (not standard platform)
    'com.tridiumx.',
    # JSON
    'org.json.',
    'com.eclipsesource.json.',
    # XML (non-platform)
    'org.simpleframework.',
    # Charting
    'net.sf.jasperreports.',
    'com.jamonapi.',
    # Chart.js and similar
    'org.pepstock.',
    # Fonts/PDF
    'com.itextpdf.',
    'com.itext.',
    # Kotlin.collections / kotlin.jvm etc.
    'kotlin.',
}

# Package display names for readability
_PACKAGE_DISPLAY = {
    'com.amazonaws.': 'AWS SDK',
    'com.microsoft.': 'Microsoft',
    'com.google.': 'Google',
    'org.apache.': 'Apache',
    'cl.': 'Honeywell cl* family',
    'clHVAC.': 'Honeywell clHVAC',
    'obix.': 'oBix',
    'com.prosysopc.': 'Prosys OPC UA',
    'com.thingworx.': 'ThingWorx',
    'org.opcfoundation.': 'OPC Foundation',
    'oracle.': 'Oracle DB',
    'com.mysql.': 'MySQL',
    'org.postgresql.': 'PostgreSQL',
    'com.fasterxml.': 'Jackson / FasterXML',
}


# ---------------------------------------------------------------------------
# Index loading (on-demand, cached per process)
# ---------------------------------------------------------------------------

_class_index_cache = None
_xref_index_cache = None
_module_inventory_cache = None


def _load_json(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print("  ERROR loading {}: {}".format(os.path.basename(path), exc))
        return None


def _load_class_index(base_dir):
    global _class_index_cache
    if _class_index_cache is not None:
        return _class_index_cache
    _class_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "class-index.json"))
    return _class_index_cache


def _load_xref_index(base_dir):
    global _xref_index_cache
    if _xref_index_cache is not None:
        return _xref_index_cache
    _xref_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "xref-index.json"))
    return _xref_index_cache


def _load_module_inventory(base_dir):
    global _module_inventory_cache
    if _module_inventory_cache is not None:
        return _module_inventory_cache
    _module_inventory_cache = _load_json(
        os.path.join(base_dir, "indexes", "module-inventory.json"))
    return _module_inventory_cache


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def _classify_package(package):
    """Classify a package as PLATFORM, HONEYWELL, or THIRD_PARTY.

    Returns (category, display_name)
    """
    if not package:
        return 'THIRD_PARTY', 'Unknown (no package)'

    # Check third-party first (most specific)
    for prefix in _THIRD_PARTY_PACKAGES:
        if package.startswith(prefix):
            display = _PACKAGE_DISPLAY.get(prefix, prefix.rstrip('.'))
            return 'THIRD_PARTY', display

    # Check Honeywell add-ons
    for prefix in _HONEYWELL_PACKAGES:
        if package.startswith(prefix):
            display = _PACKAGE_DISPLAY.get(prefix, prefix.rstrip('.'))
            return 'HONEYWELL', display

    # Check platform
    for prefix in _PLATFORM_PACKAGES:
        if package.startswith(prefix):
            return 'PLATFORM', 'Niagara N4 platform'

    # Unknown — classify as third-party to be conservative
    return 'THIRD_PARTY', 'Unknown third-party'


def _get_package_for_class(class_name, class_index):
    """Look up the package for a class name from class-index.json.

    Returns the package string (e.g. 'com.tridium.baja.sys') or None.
    Prefers the first non-docSource entry.
    """
    classes = class_index.get("classes", {})
    entries = classes.get(class_name, [])
    if not entries:
        return None

    # Prefer non-docSource entries (they're the "real" ones)
    for entry in entries:
        mod = entry.get("module", "")
        if mod and not mod.endswith("-doc") and not mod.endswith("-docSource"):
            return entry.get("package", None)

    # Fallback: any entry
    return entries[0].get("package", None)


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_dependency_audit(base_dir, module_name, as_json=False):
    """Audit external dependencies of a module.

    Args:
        base_dir: module-navigator root directory
        module_name: module to audit (e.g. 'alarm-rt')
        as_json: if True, emit JSON instead of human-readable output
    """
    ci = _load_class_index(base_dir)
    if not ci:
        print("ERROR: class-index.json not found.")
        return

    xi = _load_xref_index(base_dir)
    if not xi:
        print("ERROR: xref-index.json not found.")
        return

    mi = _load_module_inventory(base_dir)
    if not mi:
        print("ERROR: module-inventory.json not found.")
        return

    classes = ci.get("classes", {})
    class_imports = xi.get("class_imports", {})
    modules_inv = mi.get("modules", {})

    # Step 1: Find all classes belonging to the target module
    module_classes = []
    for class_name, entries in classes.items():
        for entry in entries:
            if entry.get("module") == module_name:
                module_classes.append(class_name)
                break

    if not module_classes:
        # Try partial match
        print("ERROR: Module '{}' not found.".format(module_name))
        # Show available modules similar to this
        available = [k for k in modules_inv.keys()]
        similar = [m for m in available if module_name.split('-')[0] in m]
        if similar:
            print("  Did you mean: {}".format(", ".join(similar[:5])))
        return

    # Step 2: Get module info from inventory
    mod_info = modules_inv.get(module_name, {})
    mod_package = None
    for class_name in module_classes[:10]:
        for entry in classes.get(class_name, []):
            if entry.get("module") == module_name:
                mod_package = entry.get("package", "")
                if mod_package:
                    # Try to find a com.sejofa or similar root package
                    if '.' in mod_package:
                        parts = mod_package.split('.')
                        # find where module name appears
                        for i, p in enumerate(parts):
                            if module_name.split('-')[0] in p.lower():
                                mod_package = '.'.join(parts[:i+1])
                                break
                    break
        if mod_package:
            break

    # Step 3: Aggregate all imported packages for module classes
    package_imports = defaultdict(set)  # package -> set of importing classes

    for cls_name in module_classes:
        imported_list = class_imports.get(cls_name, [])
        for imported_cls in imported_list:
            pkg = _get_package_for_class(imported_cls, ci)
            if pkg:
                # Exclude imports from same package (internal)
                src_entries = classes.get(cls_name, [])
                src_pkg = None
                for se in src_entries:
                    if se.get("module") == module_name:
                        src_pkg = se.get("package", "")
                        break

                if src_pkg and (pkg == src_pkg or pkg.startswith(src_pkg + '.')):
                    continue  # Skip internal package imports

                package_imports[pkg].add(cls_name)

    # Step 4: Classify each package
    categorized = defaultdict(list)  # category -> list of (package, display, importing_classes)
    for pkg, importers in sorted(package_imports.items()):
        category, display = _classify_package(pkg)
        categorized[category].append({
            "package": pkg,
            "display": display,
            "importing_classes": sorted(importers),
            "count": len(importers),
        })

    # Step 5: Also check module-inventory's third_party field for reference
    inventory_third_party = mod_info.get("third_party", [])

    # Build output
    platform_deps = sorted(categorized.get("PLATFORM", []), key=lambda x: -x["count"])
    honeywell_deps = sorted(categorized.get("HONEYWELL", []), key=lambda x: -x["count"])
    third_party_deps = sorted(categorized.get("THIRD_PARTY", []), key=lambda x: -x["count"])

    total_classes = len(module_classes)

    if as_json:
        output = {
            "command": "dependency-audit",
            "module": module_name,
            "package": mod_package or "unknown",
            "summary": {
                "classes_analyzed": total_classes,
                "platform": len(platform_deps),
                "honeywell": len(honeywell_deps),
                "third_party": len(third_party_deps),
            },
            "external_dependencies": {
                "platform": platform_deps,
                "honeywell": honeywell_deps,
                "third_party": third_party_deps,
            },
            "inventory_third_party": inventory_third_party,
            "risk": {
                "third_party_count": len(third_party_deps),
                "honeywell_count": len(honeywell_deps),
                "third_party_risk": "HIGH" if third_party_deps else "LOW",
                "honeywell_risk": "MEDIUM" if honeywell_deps else "NONE",
            },
        }
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    sep = "=" * 70
    sep2 = "-" * 70

    print("")
    print("DEPENDENCY AUDIT: {}".format(module_name))
    print(sep)
    print("")
    print("Module: {} ({})".format(module_name, mod_package or "unknown"))
    print("Classes analyzed: {}".format(total_classes))
    print("")

    # Third-party dependencies
    if third_party_deps:
        print("External dependencies (imported packages not in standard Supervisor):")
        print("")
        for dep in third_party_deps:
            pkg = dep["package"]
            disp = dep["display"]
            # Find short version for display
            short_pkg = pkg
            for prefix, name in sorted(_PACKAGE_DISPLAY.items(), key=lambda x: -len(x[0])):
                if pkg.startswith(prefix):
                    short_pkg = pkg[len(prefix):]
                    disp = name
                    break
            print("  {:35s} {:20s} ({}) → THIRD-PARTY (license required)".format(
                pkg[:35], short_pkg[:20], disp))
        print("")

    # Honeywell add-on dependencies
    if honeywell_deps:
        print("Honeywell add-on dependencies:")
        print("")
        for dep in honeywell_deps:
            pkg = dep["package"]
            disp = dep["display"]
            print("  {:35s} {:20s} ({}) → HONEYWELL (may require license)".format(
                pkg[:35], disp[:20], "honeywell"))
        print("")

    # Platform dependencies
    if platform_deps:
        print("Platform dependencies (built into any Supervisor):")
        print("")
        for dep in platform_deps[:15]:  # Limit to first 15 to avoid noise
            pkg = dep["package"]
            disp = dep["display"]
            print("  {:35s} {} → PLATFORM".format(pkg[:35], disp[:30]))
        if len(platform_deps) > 15:
            print("  ... ({} more platform packages)".format(len(platform_deps) - 15))
        print("")

    # Inventory reference
    if inventory_third_party:
        print("Referenced JAR dependencies (from module-inventory.json):")
        for jar in inventory_third_party[:10]:
            print("  - {}".format(jar))
        if len(inventory_third_party) > 10:
            print("  ... ({} more)".format(len(inventory_third_party) - 10))
        print("")

    # Summary
    print(sep)
    print("SUMMARY:")
    print("  Platform:   {:4d}  |  Honeywell: {:3d}  |  Third-party: {:3d}".format(
        len(platform_deps), len(honeywell_deps), len(third_party_deps)))
    print("")

    if third_party_deps:
        print("  → RISK HIGH: {} third-party dependency group(s) require separate licenses".format(
            len(third_party_deps)))
    if honeywell_deps:
        print("  → RISK MEDIUM: {} Honeywell add-on(s) may require licenses".format(
            len(honeywell_deps)))
    if not third_party_deps and not honeywell_deps:
        print("  → RISK LOW: No external (non-platform) dependencies found")
        print("    This module should work in any standard Supervisor deployment")
    print("")
