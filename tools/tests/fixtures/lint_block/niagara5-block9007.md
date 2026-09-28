# Block 9007 — synthetic fixture for R7 constant-inlining-without-evidence

## 9007.1 — positive

The four named constants are simply never referenced at their own real call sites, each shadowed by
an inline literal duplicate `[CERT]`.

## 9007.2 — negative: paired claim, WITH compile-time-constant evidence

The four named constants are simply never referenced at their own real call sites, each shadowed by
a literal duplicate: `javap -c -p` on `U.class` shows `ldc "cloud.example.test"` at the `h()` method
body, confirming javac performed compile-time constant inlining per JLS 4.12.4 `[CERT-hw]`.
