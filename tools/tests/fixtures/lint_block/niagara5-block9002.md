# Block 9002 — synthetic fixture for R2 absence-without-census

## 9002.1 — positive: single named-jar lookup

This OEM package does **not** ship `saml.jar` at all (`unzip -l "$BASE/modules/saml.jar"` -> file
not found; `ls "$BASE/modules" | grep -i saml` -> no matches).

## 9002.2 — negative: across-all-jars census

`saml.jar` is absent from this OEM package (`unzip -l` swept all 247 module jars under config-home
and bin/ext; zero matches).

## 9002.3 — negative: ships normally, nothing to census

`saml.jar` ships three per-layer jars in this OEM package.

## 9002.4 — negative: one row of a settings diff table

| Key | N4 | N5 | Note |
|---|---|---|---|
| `niagara.ipv6Enabled` | `false` (active) | **absent, no trace** | schema-level drop |
