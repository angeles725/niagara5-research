"""
Service Order Analysis for Module Navigator (Batch 5, Gap #13).

Detects modules that resolve external services in serviceStarted() lifecycle
hook, which can cause NPE if the module starts before the service's module.

Commands:
  service-order <module>
    [--json]              # structured JSON output

Reuses existing indexes (no new builders):
  method-index.json, class-index.json, inheritance.json

Classification:
  INTERNAL  - service defined in same module (safe in serviceStarted)
  EXTERNAL  - service from different module (risky in serviceStarted)
"""

import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Index loading (on-demand, cached per process)
# ---------------------------------------------------------------------------

_method_index_cache = None
_class_index_cache = None
_inheritance_cache = None

# ORD extraction: BOrd.make("...") patterns
_ORD_MAKE_RE = re.compile(r'BOrd\.make\s*\(\s*"([^"]+)"\s*\)')

# Known Niagara service slot names → canonical class names
# These are the standard station services and their implementation classes.
_KNOWN_SERVICES = {
    "AlarmService":      "BAlarmService",
    "HistoryService":    "BHistoryService",
    "LogService":        "BLogService",
    "SecurityService":   "BSecurityService",
    "ScheduleService":   "BScheduleService",
    "TrendService":      "BHistoryService",
    "AuditService":      "BAuditService",
    "DriverRegistry":    "BDriverRegistry",
    "StationManager":    "BStationManager",
    "SystemService":     "BSystemService",
    "PartitionService":  "BPartitionService",
    "UserService":       "BUserService",
    "AlarmServiceExt":   "BAlarmServiceExt",
}


def _load_json(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print("  ERROR loading {}: {}".format(os.path.basename(path), exc))
        return None


def _load_method_index(base_dir):
    global _method_index_cache
    if _method_index_cache is not None:
        return _method_index_cache
    _method_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "method-index.json"))
    return _method_index_cache


def _load_class_index(base_dir):
    global _class_index_cache
    if _class_index_cache is not None:
        return _class_index_cache
    _class_index_cache = _load_json(
        os.path.join(base_dir, "indexes", "class-index.json"))
    return _class_index_cache


def _load_inheritance(base_dir):
    global _inheritance_cache
    if _inheritance_cache is not None:
        return _inheritance_cache
    _inheritance_cache = _load_json(
        os.path.join(base_dir, "indexes", "inheritance.json"))
    return _inheritance_cache


def _read_source_lines(filepath):
    """Read source file as list of lines (with errors replaced)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except (IOError, OSError):
        return []


def _get_source_root(class_index):
    return class_index.get("_meta", {}).get("source", "")


def _extract_service_name_from_ord(ord_value):
    """Extract the service slot name from an ORD value.

    'station:|slot:/Services/AlarmService'  → ('AlarmService', 'BAlarmService')
    'station:|slot:/Services/HistoryService' → ('HistoryService', 'BHistoryService')
    'slot:/Services/AlarmService/alarmDbConfig' → ('AlarmService', 'BAlarmService')
    Returns (slot_name, canonical_class_name) or (None, None) if not a service ORD.
    """
    val = ord_value.strip()
    # Strip scheme prefix
    if "|" in val:
        body = val.split("|", 1)[1]
        if body.startswith("slot:/"):
            body = body[6:]
        elif body.startswith("/"):
            body = body[1:]
    elif val.startswith("slot:/"):
        body = val[6:]
    elif ":" in val:
        body = val.split(":", 1)[1]
    else:
        body = val

    # Normalize: remove leading/trailing slashes
    body = body.strip("/")

    # Check if this is a /Services/<Name> path
    if body.startswith("Services/"):
        parts = body.split("/")
        if len(parts) >= 2:
            slot_name = parts[1]
            # Check known services table
            if slot_name in _KNOWN_SERVICES:
                return slot_name, _KNOWN_SERVICES[slot_name]
            # Fallback: capitalize first letter
            return slot_name, slot_name
    return None, None


def _find_class_for_service_slot(class_index, slot_name):
    """Find the service class that occupies /Services/<slot_name>.

    We scan class-index.json for classes that are known service types
    and whose simple name matches. This is an approximation for the
    purpose of classification.
    """
    candidates = [
        slot_name,                           # e.g. "AlarmService"
        "B" + slot_name,                     # e.g. "BAlarmService"
    ]
    classes = class_index.get("classes", {})
    for candidate in candidates:
        entries = classes.get(candidate, [])
        if entries:
            return entries[0]
    return None


def _extract_service_class_from_source(lines, ord_value):
    """Try to extract the service class name from source lines near the ORD.

    Looks for patterns like:
      BAlarmService svc = (BAlarmService) BOrd.make("...").resolve().get();
      BAlarmService svc = BOrd.make("...").resolve();
      (BAlarmService) BOrd.make("...").resolve().get();
    """
    ord_str = ord_value.replace("\\", "\\\\")
    # Build a regex that matches the ORD string anywhere in a line
    try:
        ord_re = re.compile(re.escape(ord_str[:50]))
    except re.error:
        return None

    # Also look for cast patterns: (BXXXService) ... .resolve()
    cast_re = re.compile(r'\((B[A-Za-z]+Service)\)\s*[^;]*\.resolve\(\)')

    # Try: find line containing the ORD
    for i, line in enumerate(lines):
        if not ord_re.search(line):
            continue

        # Look backward from this line for variable declarations
        for back in range(5, 0, -1):
            if i - back < 0:
                break
            prev = lines[i - back].strip()
            # Match: BAlarmService svc =
            m = re.match(r'(B[A-Za-z]+Service)\s+\w+\s*=', prev)
            if m:
                return m.group(1)

        # Look in the same line for a cast
        m = cast_re.search(line)
        if m:
            return m.group(1)

    return None


def _extract_ords_from_method_body(lines, start_line, end_line):
    """Extract all BOrd.make("...") ORDs from a method's line range.

    start_line and end_line are 1-indexed.
    Returns list of ORD string values.
    """
    ords = []
    for i in range(start_line - 1, min(end_line, len(lines))):
        line = lines[i]
        for m in _ORD_MAKE_RE.finditer(line):
            ords.append(m.group(1))
    return ords


def _find_method_body(lines, method_name, start_line):
    """Find the body of a method starting at start_line (1-indexed).

    Returns (start_line, end_line) of the method body (exclusive).
    Returns (start_line, start_line) if the method has no body.
    """
    # Find opening brace on or after start_line
    open_line = start_line - 1
    for i in range(open_line, len(lines)):
        if "{" in lines[i]:
            open_line = i
            break
    else:
        return start_line, start_line

    # Count braces to find matching close
    depth = 0
    for i in range(open_line, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return start_line, i + 1  # 1-indexed end
    return start_line, start_line


def _classify_service_resolution(ord_value, service_class, class_index, current_module):
    """Classify a service resolution as INTERNAL or EXTERNAL.

    Returns (classification, service_module).
    """
    if not service_class or service_class == "?":
        return "UNKNOWN", None

    classes = class_index.get("classes", {})
    entries = classes.get(service_class, [])
    if not entries:
        return "UNKNOWN", None

    service_module = entries[0].get("module", "?")
    if service_module == current_module:
        return "INTERNAL", service_module
    return "EXTERNAL", service_module


def _get_imports_for_module(class_index, current_module):
    """Get set of service-like imports from classes in the module.

    Returns dict: {class_name -> package} for service-class imports.
    """
    classes = class_index.get("classes", {})
    service_imports = {}

    for class_name, entries in classes.items():
        for entry in entries:
            if entry.get("module") != current_module:
                continue
            if entry.get("outer_class") is not None:
                continue
            package = entry.get("package", "")
            # Look for service-like classes
            if class_name.startswith("B") and "Service" in class_name and entry.get("kind") == "class":
                service_imports[class_name] = package

    return service_imports


def cmd_service_order(base_dir, module_name, as_json=False):
    """Analyze service startup order issues for a module.

    Args:
        base_dir: module-navigator root directory
        module_name: module to analyze (e.g. 'nmodsreflow-rt')
        as_json: if True, emit JSON instead of human-readable output
    """
    mi = _load_method_index(base_dir)
    if not mi:
        print("ERROR: method-index.json not found.")
        return

    ci = _load_class_index(base_dir)
    if not ci:
        print("ERROR: class-index.json not found.")
        return

    classes = ci.get("classes", {})
    source_root = _get_source_root(ci)
    if not source_root:
        print("ERROR: source root not found in class-index metadata.")
        return

    methods_idx = mi.get("methods", {})

    # Step 1: Find all classes in the target module that override serviceStarted()
    service_started_entries = methods_idx.get("serviceStarted", [])
    module_classes_with_ss = []

    for entry in service_started_entries:
        if entry.get("module") != module_name:
            continue
        cname = entry.get("class", "")
        if not cname:
            continue
        module_classes_with_ss.append({
            "class": cname,
            "line": entry.get("line", 0),
            "signature": entry.get("signature", ""),
        })

    # Step 2: Get module imports (service-like classes)
    module_imports = _get_imports_for_module(ci, module_name)

    # Step 3: Analyze each class
    results = []   # list of class findings
    external_warnings = []
    internal_resolves = []
    unknown_resolves = []

    # Progress goes to stderr so stdout stays clean for --json consumers.
    sys.stderr.write("  Scanning...")
    sys.stderr.flush()
    files_scanned = 0

    for cls_info in module_classes_with_ss:
        cname = cls_info["class"]
        ss_line = cls_info["line"]

        # Get source path for this class
        class_entries = classes.get(cname, [])
        if not class_entries:
            continue
        entry = class_entries[0]
        if entry.get("outer_class") is not None:
            continue  # Skip inner classes

        filepath = os.path.join(source_root, entry["path"])
        if not os.path.isfile(filepath):
            continue

        files_scanned += 1
        lines = _read_source_lines(filepath)

        # Find the serviceStarted method body
        body_start, body_end = _find_method_body(lines, "serviceStarted", ss_line)
        if body_start >= body_end:
            body_end = body_start

        # Extract ORDs from serviceStarted body
        ords = _extract_ords_from_method_body(lines, body_start, body_end)

        class_findings = []
        for ord_val in ords:
            slot_name, canonical_class = _extract_service_name_from_ord(ord_val)

            # Try to get more specific class from source context
            inferred_class = _extract_service_class_from_source(
                lines[body_start - 1:body_end], ord_val)
            service_class = inferred_class or canonical_class

            if not service_class:
                classification = "UNKNOWN"
                svc_module = None
            else:
                classification, svc_module = _classify_service_resolution(
                    ord_val, service_class, ci, module_name)

            finding = {
                "ord": ord_val,
                "slot_name": slot_name,
                "service_class": service_class,
                "classification": classification,
                "service_module": svc_module,
            }
            class_findings.append(finding)

            if classification == "EXTERNAL":
                external_warnings.append({
                    "class": cname,
                    "method": "serviceStarted()",
                    "ord": ord_val,
                    "slot_name": slot_name,
                    "service_class": service_class,
                    "service_module": svc_module,
                })
            elif classification == "INTERNAL":
                internal_resolves.append({
                    "class": cname,
                    "ord": ord_val,
                    "service_class": service_class,
                })
            else:
                unknown_resolves.append({
                    "class": cname,
                    "ord": ord_val,
                    "service_class": service_class,
                })

        results.append({
            "class": cname,
            "line": ss_line,
            "findings": class_findings,
        })

    sys.stderr.write(" done ({} files)\n".format(files_scanned))
    sys.stderr.flush()

    # Build module-level service imports summary
    service_imports_list = [
        {"class": cls, "package": pkg}
        for cls, pkg in sorted(module_imports.items())
    ]

    # Build output
    if as_json:
        output = {
            "command": "service-order",
            "module": module_name,
            "summary": {
                "classes_with_service_started": len(results),
                "files_scanned": files_scanned,
                "external_warnings": len(external_warnings),
                "internal_resolves": len(internal_resolves),
                "unknown_resolves": len(unknown_resolves),
            },
            "module_service_imports": service_imports_list,
            "class_results": results,
            "warnings": [
                {
                    "severity": "HIGH",
                    "type": "external_service_in_service_started",
                    "class": w["class"],
                    "method": w["method"],
                    "ord": w["ord"],
                    "slot_name": w["slot_name"],
                    "service_class": w["service_class"],
                    "service_module": w["service_module"],
                    "recommendation": "Replace serviceStarted() → atSteadyState() "
                                      "for dependencies on external services",
                }
                for w in external_warnings
            ],
            "internal_resolves": internal_resolves,
            "unknown_resolves": unknown_resolves,
        }
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    sep = "=" * 70
    print("")
    print("SERVICE ORDER ANALYSIS: {}".format(module_name))
    print(sep)

    if not module_classes_with_ss:
        print("")
        print("  No classes in {} override serviceStarted().".format(module_name))
        print("")
        return

    # Module service imports
    if service_imports_list:
        print("")
        print("  Module service classes (from module's own classes):")
        for si in service_imports_list[:10]:
            print("    {:30s}  ({})".format(si["class"], si["package"]))
        if len(service_imports_list) > 10:
            print("    ... ({} more)".format(len(service_imports_list) - 10))
        print("")

    # Lifecycle analysis per class
    print("  Lifecycle analysis:")
    for res in results:
        cname = res["class"]
        ss_line = res["line"]
        findings = res["findings"]

        print("")
        print("    {}.serviceStarted()  (line {})".format(cname, ss_line))

        for f in findings:
            if f["service_class"]:
                print("      -> ORD: {}".format(f["ord"]))
                print("         Resolves service: {}  [{}]".format(
                    f["service_class"], f["classification"]))
                if f["service_module"]:
                    print("         Service module:   {}".format(f["service_module"]))
            else:
                print("      -> ORD: {}  [unclassified]".format(f["ord"]))

    # WARNINGS section
    print("")
    print(sep)
    print("  WARNINGS:")

    if not external_warnings:
        print("    No external service resolutions found in serviceStarted().")
        print("    No service order issues detected.")
    else:
        for w in external_warnings:
            print("")
            print("    ⚠ {}.serviceStarted() resolves external service {}".format(
                w["class"], w["service_class"]))
            if w["service_module"]:
                print("      (from module: {})".format(w["service_module"]))
            print("      If {} starts BEFORE {} → NPE".format(
                module_name, w["service_module"]))
            print("      SOLUTION: use atSteadyState() instead of serviceStarted()")
            print("                for dependencies on external services")

    # Internal resolves
    if internal_resolves:
        print("")
        print("  INTERNAL SERVICE RESOLVES (no ordering risk):")
        for ir in internal_resolves:
            print("    {}: {}  → {}".format(
                ir["class"], ir["ord"], ir["service_class"]))

    # Summary
    print("")
    print(sep)
    print("  SUMMARY:")
    print("    Classes with serviceStarted(): {}".format(len(results)))
    print("    External service resolves:    {}".format(len(external_warnings)))
    print("    Internal service resolves:    {}".format(len(internal_resolves)))
    print("    Unclassified ORDs:            {}".format(len(unknown_resolves)))

    if external_warnings:
        print("")
        print("    RISK: {} external service(s) resolved in serviceStarted()".format(
            len(external_warnings)))
        print("          If this module starts before the service's module → NPE")
        print("")
        print("    RECOMMENDATION:")
        print("      Replace serviceStarted() → atSteadyState() for external")
        print("      service dependencies (atSteadyState fires after all services are up)")
    else:
        print("")
        print("    STATUS: CLEAN — no service order issues detected")
    print("")
