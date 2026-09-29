#!/bin/bash
# B125 step 1: Java-mode Vineflower 1.12.0 (--kt-enable=false) over the four Kotlin-compiled Tridium jars.
# Same flags and library context as evidence/b121/run_vineflower.sh, java mode only.
# Usage: run_java_mode.sh [outroot]   (default organized/_evidence/b125/java-mode; creates <outroot>/<jar>)
set -u
ORG=${N5_CORPUS:-/home/cristian/niagara5-research}/organized
J=${JAVA:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/java}
VF=${N5_CORPUS:-/home/cristian/niagara5-research}/tools/decompilers/vineflower-1.12.0.jar
M2="/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository/com/tridium/tools"
LIBS=$(ls "$ORG"/_v2-libcache/*.jar | paste -sd, -)
OUT=${1:-$ORG/_evidence/b125/java-mode}
declare -A JARS=(
 [n-plugin]="$M2/n-plugin/5.0.54.9.2/n-plugin-5.0.54.9.2.jar"
 [n-conv-plugin]="$M2/n-conv-plugin/5.0.54.9.2/n-conv-plugin-5.0.54.9.2.jar"
 [settings]="$M2/settings/5.0.9.8.14/settings-5.0.9.8.14.jar"
 [utils]="$M2/utils/5.0.7.8.14/utils-5.0.7.8.14.jar")
for n in n-plugin n-conv-plugin settings utils; do
  d="$OUT/$n"; rm -rf "$d"; mkdir -p "$d"
  s=$(date +%s)
  "$J" -jar "$VF" --log-level=error --kt-enable=false --use-lvt-names=true --use-method-parameters=true \
    --decompile-generics=true -e="$LIBS" "${JARS[$n]}" "$d" > "$d.log" 2>&1
  echo "$n exit=$? secs=$(( $(date +%s)-s )) sha256=$(sha256sum "${JARS[$n]}" | cut -d' ' -f1)"
done
