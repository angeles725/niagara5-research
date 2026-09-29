# evidence/b120 — pattern-switch decompile fidelity (B116-G5)

Everything here is a script, a table, or a normalized-bytecode comparison result. **No decompiled or reconstructed
Tridium source is committed** (repo is public): full decompiles, patched trees and reconstructed method text live in
`/home/cristian/niagara5-research/organized/_evidence/b120/` (gitignored), identified by sha256 in `artifacts.sha256`.

Run order (all read-only on `organized/`; scratch dir = any writable path):

    python3 census_switch.py                         # census-switch.json / .out   (21,751 classes; `javap -c -p -v`)
    python3 census_switch.py <organized>/_lib-inf-3p --out /dev/null   # 33,713 classes, 0 sites (census-switch-3p.out)
    python3 census_switch.py <organized>/_etc-m2     --out /dev/null   # 945 classes, 0 sites   (census-switch-etcm2.out)
    python3 site_labels.py census-switch.json > site-labels.tsv        # BSM label list + guard-loop flag per site
    python3 matchexc_kinds.py census-switch.json > matchexc-kinds.tsv  # record-deconstruction vs exhaustive-default
    python3 grade_sites.py --scratch $S --jobs 6 --out grades.json     # javac-25 recompile of 5 trees x 39 units (~15 min)
    python3 reconstruct.py --scratch $S                                # recon-results.json (needs patch-blocks.json, out of git)
    python3 site_table.py grades.json recon-results.json site-labels.tsv > site-table.tsv 2> tally.txt
    python3 pseudo_labels.py census-switch.json site-labels.tsv $S > pseudo-labels.tsv
    ./tree_pseudo_census.sh > tree-pseudo-census.out

`grade_sites.py` imports `tools/n5-fidelity.py` (`parse_javap_verbose`, `build_classpath`; unmodified). Its normalizer drops
constant-pool indices, so the case-label list (BootstrapMethods arguments) is injected into each `invokedynamic` line first;
without that step label order would be invisible to the comparison. CFR 0.152 and Procyon 0.6.0 are run by the script on
the shipped top-level class. Classpath = jar-mirror `modules` + `bin-ext` (+ its subdirectories, which n5-fidelity's glob
misses: bouncycastle) + nested LIB-INF. Two mechanical helpers keep unrelated defects from hiding a switch verdict:
an overload-pinning shim for the `SecurityUtil.doPrivileged(<lambda>) is ambiguous` family (B116 §116.5) and
`javac --system <Niagara jre>` for the JavaFX imports of `BWbProfile`. Neither touches a switch method.

Verdict codes (site-table.tsv): X identical normalized bytecode; S same labels, same effect sequence or effect multiset,
different branch layout; U only difference is an extra `checkcast` for an unused binding (shipped uses `case T _`);
D effects differ (reviewed by hand); PSEUDO javac rejects the file and it prints SwitchBootstraps pseudo-Java;
NC javac rejects the file for a reason outside the switch; EMPTY decompiler wrote an empty file.

Files: `grades.json` (per unit/tree/method verdict + normalized-bytecode first difference), `recon-results.json`,
`site-table.tsv` (49 rows: 27 typeSwitch, 15 MatchException, 7 enumSwitch), `tally.txt`, `pseudo-labels.tsv`,
`census-*.{json,out}`, `site-labels.tsv`, `matchexc-kinds.tsv`, `tree-pseudo-census.out`, `recon.out`.
No unit tests: these are one-shot evidence scripts, not `tools/` code.
