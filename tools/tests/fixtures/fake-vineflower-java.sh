#!/usr/bin/env bash
# fake-vineflower-java.sh — T24 test double for $N5_JAVA (see the "T24"
# section of tools/tests/n5-decompile.bats: isolating classes that hang
# Vineflower instead of losing the whole module to CFR).
#
# n5-decompile.sh always invokes Vineflower AND CFR the same way:
# "$N5_JAVA" -jar "$SOME_TOOL_JAR" <args...>. This wrapper recognizes the ONE
# case a T24 test needs faked — a -jar target equal to $FAKE_VINEFLOWER_JAR
# (a path the test points N5_VINEFLOWER at; its bytes are never read, so it
# does not need to be a real jar) — and hands that invocation to
# fake-vineflower.py instead of a real Vineflower, which can be made to hang
# on command (a real Vineflower's actual bajaui hang cannot be reproduced
# quickly or deterministically in a unit test). Every OTHER -jar target
# (every real CFR invocation the script makes, including T24's per-hung-class
# fallback and the whole-module fallback path) is passed straight through to
# $REAL_JAVA, so CFR fallback is genuinely exercised against real compiled
# .class bytes in these tests, never mocked.
set -euo pipefail
if [[ "${1:-}" == "-jar" && "${2:-}" == "${FAKE_VINEFLOWER_JAR:-}" ]]; then
  shift 2
  exec python3 "$FAKE_VINEFLOWER_PY" "$@"
fi
exec "$REAL_JAVA" "$@"
