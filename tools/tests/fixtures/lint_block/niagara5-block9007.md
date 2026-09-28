# Block 9007 — synthetic fixture for R7 constant-inlining-without-evidence

## 9007.1 — positive

The four named constants are simply never referenced at their own real call sites, each shadowed by
an inline literal duplicate `[CERT]`.

## 9007.2 — negative

`javap -c -p` on `U.class` shows `ldc "cloud.example.test"` at the `h()` method body, confirming
javac performed compile-time constant inlining per JLS 4.12.4; Vineflower's decompile renders the
literal, not `K.HOST` `[CERT-hw]`.
