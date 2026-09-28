# Block 9001 — synthetic fixture for R1 syntax-adoption-without-evidence

## 9001.1 — positive: adoption claim with no bytecode evidence

N5 rewrites N4's `if`/`instanceof` cause-dispatch chain as a Java-21 pattern-matching `switch`
statement `[CERT]`.

## 9001.2 — negative: same feature term, no adoption verb

The decompiled source shows `instanceof BFoo f` pattern-match syntax when explaining runtime
behavior, not an N4-vs-N5 delta `[CERT]`.

## 9001.3 — negative: adoption verb with bytecode evidence

`javap -c -p` on both class files shows 12 `typeSwitch` bootstrap calls, confirming N5 rewrites the
dispatch as a pattern-matching switch `[CERT-hw]`.

## 9001.4 — positive table row

| Class | Diff | Verdict |
|---|---|---|
| `BFoo` | `instanceof BNumericPoint np` pattern-match (Java 21) replaces N4's cast | CLEAN |
