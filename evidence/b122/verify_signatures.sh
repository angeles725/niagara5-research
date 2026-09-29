#!/usr/bin/env bash
# B122: Authenticode verification of the 14 .NET files (xprotect.jar!nativeLib) and the 8 FFmpeg files with osslsigncode.
# Independent of pelib's own image hash (clr_dump.py): here osslsigncode recomputes the digest and validates the chain
# against the system CA bundle. Usage: verify_signatures.sh <organized-root> > authenticode-verify.tsv
set -uo pipefail
ORG="${1:?organized root}"
printf 'file\tdigest_alg\tdigest_match\tverified_signatures\tresult\tsigner\tsigned_at\tfailure_reason\n'
for f in "$ORG"/xprotect/resources/nativeLib/*.dll "$ORG"/xprotect/resources/nativeLib/*.exe "$ORG"/ffmpeg/resources/nativeLib/x86_64/*.dll; do
  o="$(osslsigncode verify -in "$f" 2>&1)"; rc=$?
  alg="$(grep -m1 'Message digest algorithm' <<<"$o" | awk '{print $NF}')"
  cur="$(grep -m1 'Current message digest' <<<"$o" | awk '{print $NF}')"
  cal="$(grep -m1 'Calculated message digest' <<<"$o" | awk '{print $NF}')"
  subj="$(grep -m1 'Subject:' <<<"$o" | sed 's/.*Subject: //')"
  ts="$(grep -m1 'Timestamp time' <<<"$o" | sed 's/.*: //')"
  why="$(grep -m1 -oE 'Verify error: [A-Za-z -]+(certificate in certificate chain|certificate)?' <<<"$o" | head -1)"
  nver="$(grep -m1 'Number of verified signatures' <<<"$o" | awk '{print $NF}')"
  last="$(tail -1 <<<"$o")"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(basename "$f")" "$alg" "$([ "$cur" = "$cal" ] && echo yes || echo NO)" \
    "${nver:-0}" "${last:-?}" "$subj" "$ts" "${why:--}"
done
