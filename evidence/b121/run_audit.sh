#!/bin/bash
# B121 audit runner. Usage: run_audit.sh <outdir>
set -e
J=/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin
EXT="/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext"
M2="/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository/com/tridium/tools"
HERE="$(cd "$(dirname "$0")" && pwd)"
CP="$EXT/asm-9.10.1.jar:$EXT/asm-tree-9.10.1.jar:$EXT/kotlin-stdlib-2.4.10.jar:$HERE/kotlin-metadata-jvm-2.4.10.jar:$HERE/classes"
OUT="$1"; shift
"$J/java" -cp "$CP" KotlinAudit "$OUT" \
  "$M2/n-plugin/5.0.54.9.2/n-plugin-5.0.54.9.2.jar" \
  "$M2/n-conv-plugin/5.0.54.9.2/n-conv-plugin-5.0.54.9.2.jar" \
  "$M2/settings/5.0.9.8.14/settings-5.0.9.8.14.jar" \
  "$M2/utils/5.0.7.8.14/utils-5.0.7.8.14.jar" "$@"
