# Block 9003 — synthetic fixture for R3 ephemeral evidence

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | Positive: only a /tmp path | [CERT-hw] | `/tmp/claude-1000/scratchpad/b9003/out/Foo.kt`, this session |
| 2 | Negative: organized/ path cited | [CERT-hw] | `organized/foo/vineflower/com/foo/Bar.java:42`, this session |
| 3 | Negative: evidence/ path cited | [CERT-live] | `evidence/b9003/probe1-output.txt`, this session |
| 4 | Negative: not CERT-hw/live | [CERT] | `/tmp/claude-1000/scratchpad/b9003/out/Foo.kt` |
