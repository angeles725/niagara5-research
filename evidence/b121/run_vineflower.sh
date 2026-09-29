#!/bin/bash
# B121 step 3b: run Vineflower 1.12.0 with and without its bundled Kotlin plugin over the four Kotlin-compiled Tridium jars.
# Usage: run_vineflower.sh <outroot>   (creates <outroot>/vf-kt/<jar>, <outroot>/vf-java/<jar>)
set -u
J=/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/java
VF=/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar
M2="/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository/com/tridium/tools"
LIBS=$(ls /home/cristian/niagara5-research/organized/_v2-libcache/*.jar | paste -sd, -)
OUT="$1"
declare -A JARS=(
 [n-plugin]="$M2/n-plugin/5.0.54.9.2/n-plugin-5.0.54.9.2.jar"
 [n-conv-plugin]="$M2/n-conv-plugin/5.0.54.9.2/n-conv-plugin-5.0.54.9.2.jar"
 [settings]="$M2/settings/5.0.9.8.14/settings-5.0.9.8.14.jar"
 [utils]="$M2/utils/5.0.7.8.14/utils-5.0.7.8.14.jar")
for n in "${!JARS[@]}"; do
  for mode in kt java; do
    d="$OUT/vf-$mode/$n"; rm -rf "$d"; mkdir -p "$d"
    flag=true; [ $mode = java ] && flag=false
    s=$(date +%s)
    "$J" -jar "$VF" --log-level=error --kt-enable=$flag --use-lvt-names=true --use-method-parameters=true --decompile-generics=true -e="$LIBS" "${JARS[$n]}" "$d" > "$d.log" 2>&1
    echo "$n $mode exit=$? secs=$(( $(date +%s)-s ))"
  done
done
