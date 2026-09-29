#!/usr/bin/env bash
# B120: whole-tree count of decompiled files holding pseudo-Java switch bootstrap calls, per tree.
# Scope = per-module trees under organized/*/<tree> and organized/_bin-ext/*/<tree> (same module scope as the class census).
set -eu
O=${1:-/home/cristian/niagara5-research/organized}
cd "$O"
for t in vineflower vineflower2 vineflower-cons; do
  n=$(grep -rlE 'typeSwitch<|enumSwitch<|SwitchBootstraps' --include='*.java' $(ls -d */$t _bin-ext/*/$t 2>/dev/null | tr '\n' ' ') | wc -l)
  echo "$t files-with-switch-bootstrap-pseudo-java $n"
  grep -rlE 'typeSwitch<|enumSwitch<|SwitchBootstraps' --include='*.java' $(ls -d */$t _bin-ext/*/$t 2>/dev/null | tr '\n' ' ') | head -3 | sed 's/^/  e.g. /'
done
