#!/usr/bin/env bash
# krak2 -r round-trip over every .class in a jar; prints module total identical differ
set -u
K=/home/cristian/niagara5-research/tools/decompilers/krakatau/bin/krak2
jar="$1"; m=$(basename "$jar" .jar); w="$2/$m"; rm -rf "$w"; mkdir -p "$w/orig" "$w/j" "$w/re"
(cd "$w/orig" && unzip -q -o "$jar" '*.class' 2>/dev/null)
$K dis -r -o "$w/j" "$jar" >/dev/null 2>"$w/dis.err"
find "$w/j" -name "*.j" -print0 | xargs -0 cat > "$w/all.j"; $K asm -o "$w/re.jar" "$w/all.j" >/dev/null 2>"$w/asm.err"; (cd "$w/re" && unzip -q -o ../re.jar)
tot=0; same=0; diff=0; miss=0
while IFS= read -r f; do
  rel=${f#$w/orig/}; tot=$((tot+1))
  if [ -f "$w/re/$rel" ]; then cmp -s "$f" "$w/re/$rel" && same=$((same+1)) || { diff=$((diff+1)); echo "$rel" >> "$w/differ.txt"; }
  else miss=$((miss+1)); echo "$rel" >> "$w/missing.txt"; fi
done < <(find "$w/orig" -name '*.class')
printf "%s\t%d\t%d\t%d\t%d\n" "$m" "$tot" "$same" "$diff" "$miss"
rm -rf "$w/orig" "$w/re" "$w/re.jar" "$w/j" "$w/all.j"
