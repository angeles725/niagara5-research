#!/usr/bin/env bash
# red-green.sh — reproduce the RED/GREEN evidence for every B123 unit (B117-G7).
#
# For each unit commit C (matched by subject prefix below) it creates a throwaway detached worktree
# at C~1 (the code BEFORE the fix), overlays C's tests + fixtures onto it (RED: the new tests must
# fail there), then overlays all of C (GREEN: they must pass). Prints one line per unit:
#   <sha> RED <failed|errors summary> -> GREEN <summary>
# Run from the repo root of a checkout that contains the B123 commits: bash evidence/b123/red-green.sh
set -uo pipefail
repo=$(git rev-parse --show-toplevel)
cd "$repo"
units=(
  "fix(census): reserve exit 1|python"
  "fix(census): isolate per-module|python"
  "fix(census): normalize zip entry|python"
  "fix(census): require the PE signature|python"
  "fix(census): report nested jars|python"
  "feat(lint): add R9|lint"
  "feat(pipeline): fail closed|bats"
  "feat(pipeline): add --verify|bats"
)
run_tests() {  # $1 = kind, $2 = dir
  case "$1" in
    python) (cd "$2/tools/tests" && python3 -m unittest test_n5_extract_census 2>&1 | tail -1) ;;
    lint)   (cd "$2/tools/tests" && python3 -m unittest test_lint_block 2>&1 | tail -1) ;;
    bats)   (cd "$2" && bats -f 'gate:' tools/tests/n5-decompile.bats 2>&1 | awk '/^ok /{o++} /^not ok /{n++} END{printf "bats gate: ok=%d not_ok=%d\n", o, n}') ;;
  esac
}
for u in "${units[@]}"; do
  subj=${u%%|*}; kind=${u##*|}
  sha=$(git log --format='%h' -F --grep="$subj" -1 HEAD)
  [ -n "$sha" ] || { echo "no commit for: $subj"; continue; }
  wt=$(mktemp -d)
  git worktree add -q --detach "$wt" "$sha~1"
  git -C "$wt" checkout -q "$sha" -- tools/tests
  red=$(run_tests "$kind" "$wt")
  git -C "$wt" checkout -q "$sha" -- .
  green=$(run_tests "$kind" "$wt")
  echo "$sha $subj :: RED: $red -> GREEN: $green"
  git worktree remove --force "$wt"
done

# Cumulative check: the FINAL census test file against the PRE-B123 census script (0df8d0a, the merge
# of PR #19) must fail, and against the current script must pass.
base=0df8d0a
head=$(git rev-parse HEAD)
wt=$(mktemp -d)
git worktree add -q --detach "$wt" "$base"
git -C "$wt" checkout -q "$head" -- tools/tests
echo "cumulative census tests vs pre-B123 script ($base): $(run_tests python "$wt")"
git -C "$wt" checkout -q "$head" -- .
echo "cumulative census tests vs current script: $(run_tests python "$wt")"
git worktree remove --force "$wt"
