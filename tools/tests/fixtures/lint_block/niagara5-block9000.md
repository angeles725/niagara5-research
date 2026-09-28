# Block 9000 — synthetic fixture, clean (must not fire any rule)

## 9000.1 — decompiled code quoted for behavior only, no adoption verb

The decompiled source shows `instanceof BFoo f` pattern-match syntax being used to explain what
`handleEvent` does at runtime; this is not a claim about an N4-vs-N5 syntax delta `[CERT]`.

## 9000.2 — absence claim with a real corpus-wide census

`saml.jar` is absent from this OEM package (`unzip -l` swept all 247 module jars under config-home
and bin/ext; zero matches) `[CERT]`.

## 9000.3 — permission claim with a resolved dispatch target

Three call sites invoke `getPermissions(null)`, which is fail-open in shape only: dispatch:
`BRootHistoryFolder.getPermissions(Context)` — `BRootHistoryFolder.java:42` ignores `cx` and fetches
the real session's permissions `[CERT]`.

## 9000.4 — cross-block comparison citing the raw artifact

[Block 55]'s own probe 1 output does not mention the WORKBENCH warning per its §55.2 prose, but the
raw artifact `organized/probes/b55/probe1-output.txt` DOES contain it at line 15.

## 9000.5 — Child gaps opened

- **B9000-G1** — Fully compliant bullet. coverage-check: rg -il "quux" over niagara5-block*.md, no
  matches found. measured-by: `wc -l` over the sweep output, this session.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | Compliant evidence citation | [CERT-hw] | `organized/foo/vineflower/com/foo/Bar.java:42`, this session |
