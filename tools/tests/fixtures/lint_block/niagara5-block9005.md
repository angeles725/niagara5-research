# Block 9005 — synthetic fixture for R5 dispatch

## 9005.1 — positive

Three call sites invoke `getPermissions(null)`, which fails open because the base implementation
returns full permissions when `cx` is null `[CERT]`.

## 9005.2 — negative

Three call sites invoke `getPermissions(null)`, which is fail-open in shape only: dispatch:
`BRootHistoryFolder.getPermissions(Context)` — `BRootHistoryFolder.java:42` ignores `cx` and fetches
the real session's permissions `[CERT]`.

## 9005.3 — negative: unrelated Gradle build-flag wording

The `-PignoreRuntimeProfileCheck` Gradle property bypasses the runtime-profile validation task so a
CI job can build faster `[CERT]`.
