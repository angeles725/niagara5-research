#!/usr/bin/env bash
# B122 dynamic check of the static JNI mismatch (jni-match.tsv). Local only, no network, no station.
# Needs: javac (any >= 21), the N5 Windows JRE (java.exe via WSL interop), and the 8 DLLs from ffmpeg.jar!nativeLib/x86_64.
# Usage: run.sh <dir-with-the-8-DLLs> ; copies DLLs + classes to C:\Users\Public\b122probe, runs, removes the copy.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DLLS="${1:?dir with the FFmpeg DLLs}"
JAVA="/mnt/c/Program Files/Niagara/5.0.0.28/jre/bin/java.exe"
W=/mnt/c/Users/Public/b122probe
out="$(mktemp -d)"
javac --release 21 -d "$out" "$HERE/org/baja/ffmpeg/libavcodec/FfmpegAvCodecUtil.java" "$HERE/Probe.java"
mkdir -p "$W" && cp "$DLLS"/*.dll "$W"/ && rm -rf "$W/classes" && cp -r "$out" "$W/classes"
"$JAVA" --enable-native-access=ALL-UNNAMED -cp 'C:\Users\Public\b122probe\classes' Probe 'C:\Users\Public\b122probe'
rm -rf "$W" "$out"
