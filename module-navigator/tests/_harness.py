"""
Shared test harness for Module Navigator CLI smoke/contract tests.

Zero deps (Python stdlib only), matching the project policy. Tests invoke the
real CLI as a subprocess — these are integration/smoke tests over the actual
indexes, not unit tests of internal functions.

Fixtures (known-valid corpus entities) live here so every test file agrees on
the same targets. If the corpus changes and a fixture disappears, update it
in ONE place.
"""

import os
import subprocess
import sys

# Repo root = parent of tests/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAV = os.path.join(BASE_DIR, "tools", "module_nav.py")

# Generous timeout: some commands load the 143 MB method-index or run every
# audit (module-health). These are smoke tests, not a fast inner loop.
DEFAULT_TIMEOUT = 180

# --- Known-valid fixtures (verified against the live corpus) ----------------
FIXTURE_CLASS = "BAlarmService"        # exists, package javax.baja.alarm
FIXTURE_CLASS2 = "BComponent"          # framework base class
FIXTURE_MODULE = "backup-rt"           # small module with real stream I/O
FIXTURE_MODULE2 = "alarm-rt"           # service module
FIXTURE_FEATURE = "alarms"             # valid feature-brief key
FIXTURE_METHOD = "started"             # method on BComponent
FIXTURE_CLASS_METHOD = "BAlarmService.ackAlarm"  # valid class.method for traces

# Entities guaranteed NOT to exist — for robustness tests.
MISSING_CLASS = "BThisClassDoesNotExistXyz"
MISSING_MODULE = "no-such-module-xyz"


def run_nav(*args, timeout=DEFAULT_TIMEOUT):
    """Run `python module_nav.py <args>` and capture (rc, stdout, stderr).

    stdout and stderr are captured SEPARATELY on purpose: the JSON contract
    requires stdout to be pure JSON, with all progress noise on stderr.
    """
    proc = subprocess.run(
        [sys.executable, NAV, *args],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


# Every subcommand that declares a --json flag, with known-valid args.
# slot-validate is excluded here (it requires --add and is a mutating-style
# validator, covered separately).
JSON_COMMANDS = [
    ("stats", []),
    ("integration-contract", [FIXTURE_CLASS]),
    ("example-mine", [FIXTURE_CLASS]),
    ("virtual-callers", [FIXTURE_CLASS2, FIXTURE_METHOD]),
    ("feature-brief", [FIXTURE_FEATURE]),
    ("slot-collision", []),
    ("ord-validate", [FIXTURE_MODULE]),
    ("resolve-audit", [FIXTURE_MODULE]),
    ("driver-cleanup-audit", [FIXTURE_MODULE]),
    ("resource-leak", [FIXTURE_MODULE]),
    ("service-order", [FIXTURE_MODULE]),
    ("dependency-audit", [FIXTURE_MODULE]),
    ("module-health", [FIXTURE_MODULE]),
    ("full-stack-trace", [FIXTURE_CLASS_METHOD]),
]
