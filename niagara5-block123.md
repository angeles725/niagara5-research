# Block 123 — Mechanizing the extraction gate: a hardened byte-exactness census, a fail-closed extraction and signature gate in the decompile pipeline, and lint rule R9 for native-binary claims

> Research task for gap **B117-G7** ([Block 117] §117.10 steps 3, 4 and 9 and its child-gap list: "call `n5-extract-census.py sweep` and a `jarsigner -verify -strict` pass from `tools/n5-decompile.sh` (recording `signature_verified` and `byte_exact` in `recon.json`), and add a lint rule that a native claim must carry a sha256, a VA or file offset, and two instrument names", plus "harden n5-extract-census per RDD review-49636f53e9119721"). Answers: (1) which concrete defects `tools/n5-extract-census.py` had, each with a regression test; (2) how the pipeline now refuses to decompile a module whose extraction is not byte-exact or whose signature does not verify; (3) what lint rule R9 checks and what it finds in the existing 122 blocks; (4) what stays unenforced.
>
> Type: evidence (tool work under strict TDD, RED then GREEN per unit, plus one corpus-wide measurement). **Subject version:** Niagara N5 5.0.0.28 (Beta), the 246 Tridium module jars that have `organized/<mod>/recon.json`, read from the sha256-verified local mirror of the config-home `modules/` directory. **Not covered:** §117.10 step 5 (obfuscation and wrong-language detection), step 7 (requiring a second instrument for decompiled claims, only the *naming* of two instruments is now checked), Authenticode of native files ([Block 117] §117.7, B117-G5, already covered), the out-of-pipeline populations (`--extra-tridium`, `--third-party-libinf`, nested `LIB-INF` decompiles) which the gate does not reach (§123.5).
>
> **Numbering note:** the task text calls the new lint rule "R7", but R7 (constant-inlining claims) and R8 (N4-4.15 baseline) already exist in `tools/lint-block.py`; the new rule is therefore **R9**.
>
> **The RDD review text is not in the repository.** `review-49636f53e9119721` is named only in the B117-G7 gap wording, with the parenthetical list (per-module error isolation, exit-code collision, entry-path normalization, sweep tests, MZ check). No file, block or evidence directory contains the review body (`git grep -n 49636f53` matches only `RESEARCH-STATE.md`). Each item was therefore re-derived from the code and reproduced with a failing test, and the defect wording below is this block's, not the review's.
>
> **Repo hygiene:** public repository, no vendor source committed. Evidence is under `evidence/b123/` (small text, no binaries); commands and commit hashes are in §123.7.
>
> **ALREADY-COVERED check (literal queries, 2026-09-29):** `git grep -n "signature_verified\|byte_exact" -- tools ':!tools/tests'` before this block → no hit (the fields did not exist). `rg -il "R9|native claim" niagara5-block*.md` → blocks 63, 87, 116, 117 (all prose uses of the words, none defines a lint rule). `git grep -n "jarsigner" -- tools` before this block → none in `tools/`. Nothing in the corpus already answered the gap.

---

## 123.1 — B117-G7 part 1 CLOSED: six defects in `n5-extract-census.py`, each reproduced by a failing test and fixed `[CERT-hw]`

Every row was RED before its fix and GREEN after, on a throwaway worktree at the parent commit with only the new tests overlaid (`evidence/b123/red-green.sh`, output `evidence/b123/red-green.txt`). Cumulatively, the final census test file fails 12 of 25 tests (7 failures, 5 errors, 1 skipped) against the pre-B123 script (`0df8d0a`) and passes 25/25 minus the 1 install-dependent skip against the current one.

| # | Defect (derived from the code) | Before | After | Test (`tools/tests/test_n5_extract_census.py`) | Commit |
|---|---|---|---|---|---|
| D1 | **Exit-code collision.** `2` meant "usage/read error", the same value argparse uses for bad usage; and only `OSError`/`BadZipFile` were caught, so any other exception was an uncaught traceback that exits `1`, the code for "census found a mismatch". An entry flagged encrypted (`RuntimeError`) reproduced it: exit 1 with a traceback. | crash reads as a finding; missing jar and bad usage both exit 2 | 0 clean, 1 mismatch, 2 usage only, 3 read/internal error (every exception); no traceback | `ExitCodeTest.test_missing_jar_is_exit_3`, `test_corrupt_jar_is_exit_3`, `test_bad_crc_is_exit_3`, `test_non_zip_exception_is_exit_3_not_1`, `test_usage_error_is_exit_2` | `bf02b02`, `test(census)` follow-up |
| D2 | **No per-module error isolation in `sweep`.** One unreadable jar raised out of the loop; `main` turned it into exit 2 and every other module's result was discarded. Jars without `recon.json` were skipped silently, indistinguishable from "checked and clean". | first bad jar aborts the sweep | bad module goes to `errored_modules` and the sweep continues; skipped jars are listed in `skipped_no_recon`; exit 3 unless a real mismatch (1) is also present | `SweepTest.test_one_corrupt_jar_does_not_abort_the_sweep`, `test_jar_without_recon_is_reported_skipped_not_silently_dropped`, `test_cli_sweep_exit_codes` | `fdf4591` |
| D3 | **No sweep tests.** `sweep()` and its aggregation had no unit test at all (only `census_module` and the CLI `module` path did). | untested | aggregation, unclean-module listing, skip and error paths, CLI exit codes all pinned | `SweepTest.test_aggregates_and_lists_unclean_modules` and the three above | `fdf4591` |
| D4 | **Entry-path normalization.** `os.path.join(extracted, entry_name)` was used unnormalized: an entry named `../../x` read a file *outside* the module directory, and a byte-equal decoy there reported a bogus byte-exact match; `a/./b` and `a//b` were looked up under names the extractor does not create. | traversal entry "matches" an outside file | `safe_entry_path()` normalizes; absolute, `..`-escaping, backslash and NUL names go to `unsafe_entries` and make the module unclean | `EntryPathTest.test_safe_entry_path_normalizes_and_rejects_escapes`, `test_traversal_entry_is_unsafe_and_never_read_outside_moddir` | `3a034a8` |
| D5 | **MZ check.** `native_format` called any file starting with the two ASCII letters `MZ` a PE, and the callers passed only `data[:8]`, so the PE signature behind `e_lfanew` could not even be examined. A text or CSV resource starting with `MZ` was reported as a native payload. | 2-byte magic | `MZ` plus `e_lfanew` (u32 at 0x3c) pointing at `PE\0\0` inside the data; callers pass the whole entry | `PayloadClassifierTest.test_mz_alone_is_not_a_pe`, `test_census_does_not_report_mz_text_resource_as_native` (and `test_native_magic` now uses a real minimal PE header) | `84e721b` |
| D6 | **Unreadable nested jar silently dropped.** A nested `PK` entry that failed to open hit `except BadZipFile: continue`, so it vanished from the nested counts. | dropped | listed in `nested_unreadable` with its sha256 and the error | `NestedUnreadableTest.test_corrupt_nested_jar_is_reported_not_silently_skipped` | `96661ed` |

**Real-corpus check (no false positives, nothing newly found).** The old (`0df8d0a`) and the hardened script give the same aggregate on the real tree: 246 modules, 20,723 classes and 20,481 non-class resources byte-exact (0 mismatched, 0 missing), 103 nested jars (34,605 classes) with 0 unreadable, 0 unsafe entries, 23 native payloads, 2,560 JS files of which 234 minified (`evidence/b123/sweep-aggregate.json`, `evidence/b123/sweep-aggregate-old.json`; `docSource` is the only jar skipped for lack of `recon.json`). The six fixes are therefore defensive: they do not change today's numbers, they stop a future bad input from being read as clean or as a crash. The old 23 natives equal the new 23, so no resource in the corpus was being misread as a PE by the two-letter check.

## 123.2 — B117-G7 part 2 CLOSED: the pipeline refuses to decompile a module whose extraction is not byte-exact or whose signature does not verify `[CERT-hw]`

**Where.** `decompile_module` in `tools/n5-decompile.sh` (the v1 path used for `modules/` and, through the same function, for `bin/ext`) calls `verify_extraction` right after `extracted/` and `resources/` are written and *before* Vineflower runs. v2/cons reuse the `extracted/` tree through the `.jar_sha256` marker and are not re-gated.

**What the gate does.**

1. `python3 tools/n5-extract-census.py module <jar> <moddir> --json`: exit 0 is byte-exact (§117.10 step 4). Any other exit (1 mismatch, 3 error, per D1) is a failure.
2. `jarsigner -verify -strict <jar>` (step 3), resolved as `N5_JARSIGNER`, else the `jarsigner` beside `N5_JAVA`, else `PATH`. `classify_jarsigner` maps result to a status: exit 0 with `jar verified` = `verified`; exit 0 with `jar is unsigned` = `unsigned`; exit in {2,4,6} with `jar verified` = `verified-with-signer-warnings` (Tridium's chain is not in the JDK trust store, so exit 4 is the *expected* result, [Block 117] §117.6); anything else, or any output containing `digest error`, `SecurityException`, `unsigned entries`, `verification failed` or `invalid SHA`, = `failed`.
3. Success records four fields in `recon.json`: `byte_exact` (bool), `signature_verified` (bool, true only for the two verified statuses), `signature_status`, `jarsigner_exit`.

**Failure modes and what the gate does (each is a `gate:` bats test).**

| Situation | Result | Test |
|---|---|---|
| exit 4, output `jar verified, with signer errors.` | accepted, `verified-with-signer-warnings`, `jarsigner_exit` 4 | `gate: a verified jar records byte_exact and signature_*` |
| exit 0, `jar verified.` | accepted, `verified` | `gate: exit 0 'jar verified.' is status verified` |
| digest error (exit 1, `SecurityException`) | fail closed: non-zero exit, `recon.json` removed, `GATE FAILED` logged | `gate: a digest error fails closed` |
| exit 4 but output lacks `jar verified` | fail closed | `gate: exit 4 whose output does not say 'jar verified' is rejected` |
| unsigned jar | recorded `signature_verified=false`, `unsigned`; fails only with `N5_REQUIRE_SIGNED=1` | `gate: an unsigned jar is recorded ...` |
| no jarsigner anywhere | fail closed; `N5_JARSIGNER_SKIP=1` records `skipped` instead | `gate: a missing jarsigner fails closed ...` |
| extraction differs from the jar (torn or partial copy) | fail closed even with a good signature | `gate: a non-byte-exact extraction fails closed ...` |
| one module fails in a multi-module run | the others still run; `finish_gate` exits 1 at the end | `gate: one failing module does not stop the others ...` |

**Design decision worth recording.** The failure is signalled through a global counter (`N5_GATE_FAILURES`) turned into an exit status by `finish_gate`, not through `return 1`. The script runs under `set -e`; a caller that wrote `decompile_module ... || handle` would disable errexit for the whole body of the function, so every other failing step (extraction, copy) would be silently ignored: a fail-open regression introduced by the fail-closed gate. A separate lesson came from the first full run of the existing bats file with the gate in place: the T24 tests (at least numbers 67-71 failed; the head of that output was not captured) stub `N5_JAVA` with a directory that holds no `jarsigner`, so a path derived only from `dirname $N5_JAVA` failed closed. `resolve_jarsigner` therefore falls back to `PATH`; the full file was then re-run in a snapshot copy with the real Vineflower and CFR jars: 91 of 91 `ok` (the 83 pre-existing tests plus the 8 gate tests then present), exit 0 (`evidence/b123/bats-full-summary.txt`; the three `--verify` tests were added afterwards and pass in the filtered run). On failure the module's `recon.json` is deleted, so the sha256 idempotency check cannot treat the module as up to date on the next run.

**`--verify [<module>]` and `make census`.** `tools/n5-decompile.sh --verify` re-runs the gate over already-decompiled modules (those with a `recon.json`), touches no decompile tree, and merges the four fields (a failure records `byte_exact=false`, `signature_status=failed`). `make census` runs it; `make census-sweep` runs the read-only aggregate `n5-extract-census.py sweep`. Neither is in `make check` or CI: CI has no corpus, and still runs only `make test`, `tools/lint-block.py` and `tools/check-gap-drift.py`. Tests: `gate: --verify backfills ...`, `--verify exits 1 and records byte_exact=false ...`, `--verify skips modules with no recon.json and non-Tridium vendors`.

**Measured on the real corpus** (`--verify` over a scratch view of the 246 module directories so the shared `organized/` was not written): `verify: ok=246 failed=0` (wall 18 min 31 s, jarsigner from JDK 26). All 246 `recon.json` gained `byte_exact=true` and `signature_verified=true`; `signature_status` is `verified-with-signer-warnings` and `jarsigner_exit` is `4` for **246 of 246** (`evidence/b123/verify-real-summary.txt`). That is exactly the profile [Block 117] §117.6 measured by hand (chain not in the JDK trust store, no digest error, no unsigned entry), now produced by the pipeline's own code. The shared `organized/` was not written (B123-G1).

## 123.3 — B117-G7 part 3 CLOSED: lint rule R9, native-binary claims must carry a sha256, an address anchor and two named instruments `[CERT-hw]`

**Trigger (per clause).** An evidence marker `[CERT]`, `[CERT-hw]` or `[CERT-live]` and native-binary context in the same clause. Native context is a file name ending in `dll`, `so` (optionally with version digits), `exe` or `dylib`, or (case-sensitive) the words PE32, ELF, Mach-O, "PE binary/file/image/header/section", Authenticode. `[CERT-doc]`, `[CERT-web]` and `[INFER]` make no byte claim and never trigger it.

**Requirement (per paragraph or table row, like R6, because the three items of one claim routinely sit in neighbouring sentences or cells).** All of: the binary's full sha256 (64 hex characters); an address anchor (`0x` followed by 3 or more hex digits, or VA/RVA/offset followed by hex); and two distinct instruments from the documented allowlist `R9_INSTRUMENTS` in `tools/lint-block.py` (readelf, objdump, r2, radare2, rabin2, ghidra, pefile, pelib, osslsigncode, ilspycmd, ilspy, diec, dumpbin, otool, ldd, gdb, lldb, capstone, xxd, hexdump, binwalk, debug/pe, debug/elf, debug/gosym, gosym; `nm` and `strings` count only inside a backtick code span because they are ordinary words and units). A finding names which of the three is missing. Waiver: `<!-- lint-ok: R9 <reason> -->` with a non-empty reason (an empty one is an R0 finding, as for R1-R8).

**Enforcement.** A new per-rule floor `RULE_MIN_BLOCK = {"R9": 123}`: in enforced mode R9 gates only blocks numbered 123 or higher; `--audit` reports it for every block. The floor is needed because the existing enforced range starts at block 115 and blocks 117 and 122 already carry R9 findings; without it CI would fail on merged history.

**Tests (`tools/tests/test_lint_block.py::TestR9NativeClaimAnchors`, fixtures `niagara5-block9011.md`, `niagara5-block122.md`, `niagara5-block123.md`).** The four incomplete claims fire (no evidence at all; sha256 and VA but one instrument; two instruments and a VA but no sha256; a table row with ELF wording and no `.so` name); a complete claim, a waived claim, a Java-class claim, an `[INFER]`/`[CERT-doc]` claim and ordinary prose using "strings" and "elf" do not; block 123 fails enforced, block 122 passes enforced and reports under `--audit` (`R9=1`). Two false positives were found and fixed against the real corpus while tuning: `.sys` and `.ocx` were dropped from the extension list because `javax.baja.sys` and `com.tridium.sys.module` are Java package names, and a file-name match is rejected when followed by `.` and a letter.

**Audit of the existing blocks (report only, nothing edited).** `python3 tools/lint-block.py --audit niagara5-block*.md` reports `R9=113` findings in 30 of the 122 blocks (total across all rules 834 before this block): 102 lack the sha256, 95 lack an anchor, 94 name fewer than two instruments (a finding can lack several). 11 of the 113 are in blocks 115 and up (block 117: 5, block 122: 6). Per-block counts: `evidence/b123/r9-audit-by-block.tsv`. These are heuristic findings, not verified errors: many are correct-by-intent (an older block cites a native library's behaviour from a live disassembly with the address in a neighbouring cell), and some are false positives of the file-name trigger. They are a to-do list for anyone re-auditing a native claim, not a defect count.

## 123.4 — What R9 does not check

R9 is a presence check on three kinds of token. It does not check that the sha256 belongs to the binary under discussion (any 64-hex string in the unit satisfies it), that the address exists in that binary, that the two instruments were run, that they are independent (two front-ends of one engine still count as two names; the independence rule of [Block 117] §117.10 is prose only), or that the claim is true. It cannot see a native claim phrased without a file name or the format words (for example "the launcher" or "the agent"). A claim in a Self-verify row that points to a side file for its hash fails by design; the waiver is the intended escape when the binary was not retained. Java-only evidence and decompiled-source claims are out of scope (R1, R7 and the fidelity rule cover those).

## 123.5 — What remains unenforced after this block

| Item | State | Why |
|---|---|---|
| Gate on `--extra-tridium`, `--third-party-libinf`, nested `LIB-INF` decompiles, v2/cons re-extraction | not gated | those paths do not call `verify_extraction`; they extract from cached or nested jars whose signature is not the vendor's (B123-G2) |
| `recon.json` fields on the shared `organized/` | not yet written | this session verified a scratch view; `make census` on the main checkout writes the fields into the 246 files (B123-G1) |
| §117.10 step 5 (obfuscation, wrong language) | manual | untouched |
| §117.10 step 7 (a second instrument actually run) | manual; only the naming is linted | R9 checks names, not runs |
| Authenticode digest for native PE files in the pipeline | manual (B117-G5 did it once, 20 of 20 `bin/` files) | `osslsigncode` is not called from any script |
| `jarsigner` result for nested `LIB-INF` jars | not checked | the gate verifies the outer jar only |
| CI | unit tests, lint and gap-drift only | CI has no corpus; the bats gate tests are hermetic but bats is not in the CI workflow |

## 123.6 — Corrections to earlier blocks

- [Block 117] §117.10 table rows 3, 4 and 9 (statuses "no", "tool exists, not called by the pipeline or CI", "no rule for the native anchor yet") are superseded: row 3 and row 4 are now mechanized in `tools/n5-decompile.sh` for the modules and `bin/ext` path (not CI); row 9 has lint rule R9 (presence check, blocks 123 and up).
- [Block 117] B117-G7 `measured-by` said "`recon.json` files carrying both fields = 252": the module tree has 246 `recon.json` files (plus 6 under `_bin-ext`), not 252; 252 is not a count of anything in `organized/` today.

## 123.7 — Reproduction and commits

Commits on branch `feat/n5-wave19` (base `0df8d0a`): `bf02b02` D1, `fdf4591` D2+D3, `3a034a8` D4, `84e721b` D5, `96661ed` D6, a `test(census)` follow-up for the non-zip crash case, `8c64db8` R9, `4fca335` the gate, `637ca82` `--verify` and `make census`, then the block, state and docs commits. Reproduce RED/GREEN with `bash evidence/b123/red-green.sh` from a checkout containing them. Unit tests: `cd tools/tests && python3 -m unittest test_n5_extract_census test_lint_block`; bats: `bats -f 'gate:' tools/tests/n5-decompile.bats`.

## 123.8 — Connections

- [Block 117] §117.10 is the specification this block mechanizes; §117.5–§117.6 fix the jarsigner exit-code interpretation used by `classify_jarsigner`.
- [Block 116] and [Block 115] set the fidelity rules whose lint counterparts (R1, R7) R9 extends to native binaries.
- [Block 122] is the first block written after R9 was designed and already contains native claims that R9 reports in `--audit` (6 findings).
- Kit: METHODOLOGY §3 (markers), §4 (anatomy), §11 and §11b (verify the verifier: every rule has a RED fixture).

## 123.9 — Child gaps opened

- **B123-G1** (high) — Run `make census` on the main checkout so the 246 module `recon.json` files carry `byte_exact`, `signature_verified`, `signature_status` and `jarsigner_exit`, and record the per-status counts. Investigable (needs write access to the shared `organized/`). coverage-check: `git grep -n "signature_status" -- tools` (only `tools/n5-decompile.sh` and tests) and `python3 -c` over `organized/*/recon.json` for the key (absent today). measured-by: `recon.json` files carrying all four fields, target 246 of 246.
- **B123-G2** (medium) — Extend the gate to the populations it does not reach: `--extra-tridium` jars (`_etc-m2`, `_lib`), the Tridium-owned nested `LIB-INF` jars, `--third-party-libinf` (jarsigner is meaningless for those; a byte-exactness and sha256-vs-upstream check is not). Investigable read-only. coverage-check: `rg -n "verify_extraction" tools/n5-decompile.sh` shows the single call site in `decompile_module`. measured-by: populations calling the gate, target every path that writes an `extracted/` tree.
- **B123-G3** (medium) — Call `osslsigncode verify` from a script for the native PE files (B117-G5's 20 of 20 was run by hand) and record the result in the same recon-style fields. Investigable. coverage-check: `git grep -n osslsigncode -- tools` returns nothing; B117-G5 covered in `RESEARCH-STATE.md`. measured-by: PE files with a recorded digest result.
- **B123-G4** (low) — Reduce R9's false positives in the 113 audit findings (classify each as true gap, waiver-worthy, or trigger error) and decide whether to widen the floor to 115. Investigable read-only. coverage-check: `evidence/b123/r9-audit-by-block.tsv`. measured-by: findings triaged as true, waiver or false-positive out of 113.
- **B123-G5** (low) — Add the bats gate tests (hermetic, no corpus) to CI by installing bats in the workflow; today only `make test` runs. Investigable. coverage-check: `.github/workflows/ci.yml` runs `make test`, lint, gap-drift and shellcheck only. measured-by: CI job list includes the `gate:` tests.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | D1: a crash (encrypted-entry `RuntimeError`) exited 1 with a traceback in the pre-B123 script, and now exits 3 | [CERT-hw] | `tools/tests/test_n5_extract_census.py` `test_non_zip_exception_is_exit_3_not_1`; `evidence/b123/red-green.txt` (cumulative line, 12 of 25 fail on `0df8d0a`) |
| 2 | Each of D1, D2+D3, D4, D5, D6 is RED at the parent commit and GREEN at the fix | [CERT-hw] | `evidence/b123/red-green.txt` (`bf02b02`, `fdf4591`, `3a034a8`, `84e721b`, `96661ed`) |
| 3 | The old and hardened census give identical aggregates on the 246-module real tree (0 mismatches, 23 natives) | [CERT-hw] | `evidence/b123/sweep-aggregate.json`, `evidence/b123/sweep-aggregate-old.json` |
| 4 | The gate fails closed on a digest error, a bad `jarsigner` result, a missing `jarsigner` and a non-byte-exact extraction, and removes `recon.json`; the whole existing bats file still passes with it (91 of 91) | [CERT-hw] | `tools/tests/n5-decompile.bats` tests `gate:` 1-8; `evidence/b123/red-green.txt` (`4fca335`: 0 of 8 before, 8 of 8 after); `evidence/b123/bats-full-summary.txt` |
| 5 | Exit 4 (untrusted chain) is accepted only when the output says `jar verified` | [CERT-hw] | `tools/n5-decompile.sh:370` (`classify_jarsigner`); bats `gate: exit 4 whose output does not say 'jar verified' is rejected` |
| 6 | `--verify` backfills the four fields without touching decompile trees and records failure as `byte_exact=false` | [CERT-hw] | bats `gate:` 9-11; `evidence/b123/red-green.txt` (`637ca82`: 8 of 11 before, 11 of 11 after) |
| 7 | `--verify` over the real 246 modules: 246 of 246 `byte_exact=true`, 246 of 246 `verified-with-signer-warnings` with `jarsigner_exit` 4, 0 failed | [CERT-hw] | `evidence/b123/verify-real-summary.txt` |
| 8 | R9 has 4 firing fixtures, 5 non-firing, an audit-only floor below block 123, and yields 113 findings in 30 old blocks (11 in blocks 115 and up) | [CERT-hw] | `tools/tests/test_lint_block.py` `TestR9NativeClaimAnchors`; `evidence/b123/r9-audit-by-block.tsv`; `evidence/b123/red-green.txt` (`8c64db8`) |
| 9 | `.sys`/`.ocx` are excluded from the R9 trigger because `javax.baja.sys` and `com.tridium.sys.module` are Java package names | [CERT] | `tools/lint-block.py:526` (`R9_NATIVE_RE`) and the comment above it; `tools/tests/test_lint_block.py` |
| 10 | The RDD review body is not in the repository, so the D1-D6 wording is derived from code | [CERT] | `git grep -n 49636f53` matches only `RESEARCH-STATE.md` |
| 11 | R7 and R8 already exist, so the new rule is R9 | [CERT] | `tools/lint-block.py:22` (R7) and `tools/lint-block.py:24` (R8) in the module docstring |
| 12 | The gate covers the `decompile_module` path only; extra-tridium, third-party LIB-INF and v2/cons are not gated | [CERT] | `tools/n5-decompile.sh:396` (`verify_extraction`) and its single call site inside `decompile_module` (`git grep -n 'verify_extraction' tools/n5-decompile.sh`) |
| 13 | R9 does not verify that the sha256 belongs to the binary, that the address exists, or that instruments were run | [INFER] | `tools/lint-block.py:556` (`rule_r9`) checks token presence only; not tested against adversarial input |
| 14 | Many R9 audit findings are correct-by-intent or trigger false positives rather than true errors | [INFER] | sampled by eye (12 of the 113 lines were read); B123-G4 measures it |

**Tally:** `[CERT-hw]` 7 rows · `[CERT]` 4 rows · `[INFER]` 2 rows · `[INFER]`/`[CERT*]` = 2/11 = 0.18.

**Artifacts:** `evidence/b123/` (`red-green.sh`, `red-green.txt`, `bats-full-summary.txt`, `sweep-aggregate.json`, `sweep-aggregate-old.json`, `verify-real-summary.txt`, `r9-audit-by-block.tsv`); code in `tools/n5-extract-census.py`, `tools/n5-decompile.sh`, `tools/lint-block.py`, `Makefile`, tests under `tools/tests/`. No binaries, no vendor source.
