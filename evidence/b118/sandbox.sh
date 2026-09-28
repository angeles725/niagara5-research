#!/usr/bin/env bash
# Read-only-root, no-network sandbox for M3/M4 probes. Only $S/m3 (and $S/m4) writable. No NIAGARA_* env.
S=/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b118
exec bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --bind "$S" "$S" --unshare-all --die-with-parent \
  --clearenv --setenv HOME "$S/m3/home" --setenv PATH /usr/bin:/bin --chdir "$S/m3" "$@"
