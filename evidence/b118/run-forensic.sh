#!/usr/bin/env bash
set -u
S=/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b118; cd $S
J=/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/java; VF=/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar
MODS=/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules; EXT="/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext"
F=(--remove-synthetic=0 --remove-bridge=0 --hide-default-constructor=0 --prettify-ifs=0 --keep-literals=1 --hide-empty-super=0
   --decompile-complex-constant-dynamic=0 --ignore-invalid-bytecode=0 --decompiler-comments=1 --dump-bytecode-on-error=1
   --use-lvt-names=1 --use-method-parameters=1 --rename-members=0 --include-runtime=/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec
   --bytecode-source-mapping=1 --__dump_original_lines__=1)
for d in ts/*; do rm -rf $d/vf-forensic; $J -jar $VF --log-level=error "${F[@]}" -e=$MODS -e="$EXT" $d/in $d/vf-forensic >/dev/null 2>$d/err-for.txt; done
