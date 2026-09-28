# Decompilers used in the bake-off

Jars in this directory are **not** committed (see repo `.gitignore`); this file is the
provenance record. Re-download with the commands below and verify against the sha256sums.

| Tool | Version | Source URL | sha256 |
|---|---|---|---|
| Vineflower | 1.12.0 | https://github.com/Vineflower/vineflower/releases/download/1.12.0/vineflower-1.12.0.jar | `1dfcfe974395734fa467ce620661c7623d05ba83670de0529b1fbd63ff548b9d` |
| Vineflower (pre-existing, kept for regression comparison) | 1.11.1 | local copy at `/home/cristian/modules/Prototipos/Reflow/vineflower.jar` (N4 kit) | not re-verified — external to this repo |
| CFR | 0.152 | https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar | `f686e8f3ded377d7bc87d216a90e9e9512df4156e75b06c655a16648ae8765b2` |
| Procyon | 0.6.0 (latest tagged release; project is effectively unmaintained since 2021) | https://github.com/mstrobel/procyon/releases/download/v0.6.0/procyon-decompiler-0.6.0.jar | `821da96012fc69244fa1ea298c90455ee4e021434bc796d3b9546ab24601b779` |
| JADX (CLI) | 1.5.6 | https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip | `545ea2be9c242511bc145755cf4bda2485ade42966e096f8b4d3da2a230e8974` |
| Fernflower (standalone) | n/a | **not fetched** — no standalone Fernflower jar is published; it only ships bundled inside IntelliJ Community/IDEA. Not "easily available" per task scope, so skipped. Vineflower is Fernflower's actively-maintained fork and supersedes it for this purpose. | — |
| Krakatau (`krak2`, disassembler — last resort) | 2.0.0-alpha, git commit `f5bda74edd2226d510abcb4e0175dc933e6c0300` (2026-09-24) | `cargo install --git https://github.com/Storyyeller/Krakatau --root tools/decompilers/krakatau` | n/a (source build, not a downloaded artifact — cargo pins the exact commit above) |

## Re-download

```bash
cd tools/decompilers
curl -sL -o vineflower-1.12.0.jar   https://github.com/Vineflower/vineflower/releases/download/1.12.0/vineflower-1.12.0.jar
curl -sL -o cfr-0.152.jar           https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar
curl -sL -o procyon-decompiler-0.6.0.jar https://github.com/mstrobel/procyon/releases/download/v0.6.0/procyon-decompiler-0.6.0.jar
curl -sL -o jadx-1.5.6.zip          https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip
unzip -o jadx-1.5.6.zip -d jadx-1.5.6
cargo install --git https://github.com/Storyyeller/Krakatau --root krakatau   # builds bin/krak2
sha256sum ./*.jar ./*.zip
```

## Krakatau (`krak2`) — last-resort fallback

Krakatau is a Rust bytecode assembler/disassembler, not a decompiler: `krak2 dis -o <dir> <class-or-jar>`
produces a `.j` Jasmin-like text form (one-to-one with the bytecode) rather than Java source. It is wired
into the pipeline (`tools/n5-decompile.sh`) as the tool of last resort — used only for a class that every
Java-source decompiler (Vineflower, CFR) fails or times out on, so that class still gets *some* readable,
lossless textual form instead of being silently skipped. It also doubles as ground truth when checking a
Java decompiler's output against the real bytecode (e.g. it is what surfaced that `BNumericPoint`'s
`@Generated` annotation resolves to `niagara.nre.annotations.Generated`, a class that ships in none of the
247 runtime module jars — see `docs/decompiler-bakeoff.md`).

## Why these versions

- **Vineflower 1.12.0**: latest tagged release at bake-off time (2026-09-27); actively
  maintained, explicit Java 21-25 support (records, sealed classes, pattern matching in
  `switch`, `invokedynamic` string concat).
- **CFR 0.152**: latest tagged release; long track record on modern `invokedynamic`
  bytecode (lambdas, string concat) though record/sealed support lags Vineflower.
- **Procyon 0.6.0**: last tagged release (2021); included as a baseline/fallback
  candidate only — project predates Java 17 language features, so records/sealed
  classes are expected to render as plain classes.
- **JADX 1.5.6**: primarily an Android/dex tool, included because it also decompiles
  plain `.jar`/`.class` input and its CLI is exercised as a fourth data point.

See `../../docs/decompiler-bakeoff.md` for the measured comparison.

## `--help` provenance (T19, `--variant v2`)

T19 (`odd/tasks/decompiler-fidelity-audit.md`) read every v2 flag name directly from each
tool's own `--help` output before using it (`--add-external`/`-e`, `--include-runtime`,
`--use-lvt-names`, `--use-method-parameters`, `--decompile-generics`, `--decompile-assert`,
`--rename-members`, `--decompile-complex-constant-dynamic`, `--ignore-invalid-bytecode`,
`--dump-bytecode-on-error`, `--decompiler-comments` for Vineflower 1.12.0; `--extraclasspath`
for CFR 0.152) rather than assume any flag exists. Captured 2026-09-28:

```bash
java -jar vineflower-1.12.0.jar --help > vf-help.txt   # sha256 c26d2d56b7f925b851a3db40909ae9f81a56eadc0c70fdaf1ce4084552d33769
java -jar cfr-0.152.jar --help > cfr-help.txt          # sha256 2c3bef2da5c1c71574d25f45d9ec31366797cc99c6ebfd10d0090dc24d75b043
```

Not committed (`--help` output is regenerable from the pinned jar shas above, not a fixed
artifact) — re-run the two commands above and compare against these sha256sums to confirm the
same flag set before relying on them.
