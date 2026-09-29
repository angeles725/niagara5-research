# Block 9011 — synthetic fixture for R9 native-claim anchors

## 9011.1 — positive: native claim with no sha256, anchor or instrument

The `vendor.dll` export table lists 12 functions `[CERT-hw]`.

## 9011.2 — positive: sha256 and VA present, only one instrument

`vendor.dll` (sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef) checks the token at VA 0x180001000, read with objdump `[CERT-hw]`.

## 9011.3 — positive: two instruments and a VA, but no sha256 of the binary

`libagent.so.1` calls the verifier at VA 0x4010a0 (readelf and objdump agree) `[CERT]`.

## 9011.4 — positive: ELF wording with no .so filename, in a table row

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | The ELF loader stub is stripped | [CERT-hw] | `evidence/b1/stub.txt` |
| 2 | `agent.exe` is a PE32+ image built by Go | [CERT] | sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef, VA 0x140001000, `debug/pe` and `rabin2` |

## 9011.5 — negative: complete claim (sha256, VA, two instruments)

`vendor.dll` (sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef) checks the token at VA 0x180001000, disassembled by objdump and
radare2 `[CERT-hw]`.

## 9011.6 — negative: waiver with a reason

`vendor.dll` was not retained after the session `[CERT-hw]` <!-- lint-ok: R9 binary not retained; claim taken from the vendor readme -->

## 9011.7 — negative: no native context (Java class evidence)

The `com/tridium/Foo.class` constant pool holds the URL `[CERT]`.

## 9011.8 — negative: native context but the marker is not CERT/CERT-hw

`vendor.dll` looks packed `[INFER]`, and its help page says so `[CERT-doc]`.

## 9011.9 — negative: the word "strings" and "elf" in ordinary prose

The Java strings in `com/tridium/Foo.class` decode to a shelf label `[CERT]`.
