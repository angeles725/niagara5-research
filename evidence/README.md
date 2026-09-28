# evidence/ — durable [CERT-hw]/[CERT-live] artifacts

Session scratch (`/tmp/...`) does not survive the session, so a block citing it as evidence
(§ [Block 106] §106's `okio` probe, [Block 109]'s `n4/n5-Util.class` cmp, [Block 107]'s PKIX probes,
...) leaves nothing reproducible once that scratchpad is gone. `tools/lint-block.py`'s **R3** rule
flags exactly this shape (a `[CERT-hw]`/`[CERT-live]` Self-verify row whose evidence cites only a
`/tmp` path) going forward for blocks >= its `--min-block`. This directory is where the artifact goes
instead.

## Layout

    evidence/b<N>/<short-topic>/...

One subdirectory per block number that cites it, named after the block (`b115`, `b98`, ...); a
descriptive sub-path under that for the specific experiment/probe when a block has more than one.

## What belongs here

Small, non-proprietary reproducibility artifacts for a `[CERT-hw]`/`[CERT-live]` claim: the exact
source file(s) compiled/run this session, captured command output (`javap`, probe scripts, `cmp`/
`sha256sum` output, decompiler output), and short READMEs stating the exact commands and the result
summary.

## What does NOT belong here

- **Binaries and proprietary jars/classes** (Tridium's own, or anyone else's): never commit a
  `.class`/`.jar`/decompiled-from-proprietary-source file here. Cite its **sha256** in the README/
  Self-verify row instead (as the corpus already does for jar/class comparisons), and point back at
  its real location (`organized/...`, `/mnt/c/...` install paths) for anyone re-deriving it.
- **Secrets**: this corpus's existing secrets discipline applies here unchanged — cite structure
  (paths, key names, shapes), never secret values, tokens, or credentials.
- Anything that doesn't fit the size caps below (compress or summarize instead of dumping raw logs).

## Size caps

- <= 512 KiB per individual file.
- <= 5 MiB total per `evidence/b<N>/` directory.

A file at or near these caps is a signal to summarize/trim rather than paste a full raw log; keep the
part that actually proves the claim.

## Citing it from a block

In a Self-verify row, cite the repo-relative path directly (this is what clears **R3**):

    | 7 | `U.class` resolves `K.HOST` via `ldc`, not a field read | [CERT-hw] | `evidence/b115/decompiler-fidelity/constinline/javap-U.txt` |
