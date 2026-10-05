#!/usr/bin/env bash
# I1 gate (c), CI recipe — the CircleCI build_test job, run locally on the
# UNCOMMITTED working tree (nothing may be committed before Danilo approves (d)).
#
#   SCRATCH=<dir outside the repo> bash research/app_redesign/i1/run_ci_recipe.sh
#
# A clean detached worktree of HEAD, plus the working tree's tracked changes
# (`git diff HEAD`, binary-safe) and its new untracked, non-ignored files; then a
# NEW python3.12 venv and the job's commands, verbatim from .circleci/config.yml:
#   pip install --upgrade pip build; python -m build; pip install dist/*.whl;
#   pip install pytest pyyaml;
#   CYCLOPHASER_REQUIRE_INSTALLED=1 pytest --import-mode=append -m "not source_tree"
#   python -m pytest -m source_tree
# Counts come from the junit files. Output: ci_recipe_raw.txt, ci_recipe_summary.json
# next to this script. Adapted from research/release_v21/parteB_passo2/run_ci_steps.sh.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
OUT="$ROOT/research/app_redesign/i1"
WT="$SCRATCH/i1_ci_wt"; VENV="$SCRATCH/i1_ci_venv"; RAW="$SCRATCH/i1_ci_raw"
rm -rf "$WT" "$VENV" "$RAW"; mkdir -p "$RAW"
git worktree add -q --detach "$WT" HEAD
git diff --binary HEAD > "$RAW/working_tree.patch"
( cd "$WT" && git apply --whitespace=nowarn "$RAW/working_tree.patch" )
git ls-files --others --exclude-standard -z | while IFS= read -r -d '' f; do
  mkdir -p "$WT/$(dirname "$f")"; cp "$f" "$WT/$f"
done
LOG="$OUT/ci_recipe_raw.txt"
step() {  # name, command...
  local name="$1"; shift
  echo; echo "=== $name"; echo "\$ $*"
  "$@" > "$RAW/$name.log" 2>&1; local rc=$?
  echo "exit $rc"
  grep -E "^collected|cyclophaser.__file__|^=+ .*(passed|failed|error|skipped|deselected).* =+$|^(FAILED|ERROR)|Successfully (built|installed)" "$RAW/$name.log" | head -20
}
{
  echo "base HEAD: $(git rev-parse HEAD) | working-tree patch: $(wc -l < "$RAW/working_tree.patch" | tr -d ' ') lines, sha256 $(shasum -a 256 "$RAW/working_tree.patch" | cut -c1-16)… | untracked files copied: $(git ls-files --others --exclude-standard | wc -l | tr -d ' ') | date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd "$WT"
  echo "worktree: tracked files differing from HEAD: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')"
  /opt/homebrew/bin/python3.12 -m venv "$VENV"
  . "$VENV/bin/activate"
  echo "python: $(python --version 2>&1) | venv: new"
  step install_build_tools pip install --upgrade pip build
  step build python -m build
  step install_wheel bash -c 'pip install dist/*.whl'
  step install_test_deps pip install pytest pyyaml
  echo "streamlit importable: $(python -c 'import streamlit' 2>/dev/null && echo yes || echo no)"
  echo "playwright importable: $(python -c 'import playwright' 2>/dev/null && echo yes || echo no)"
  step main_wheel env CYCLOPHASER_REQUIRE_INSTALLED=1 pytest --import-mode=append -m "not source_tree" --junitxml=test-reports/results.xml
  step source_tree python -m pytest -m source_tree --junitxml=test-reports/results-source-tree.xml
  deactivate
} > "$LOG" 2>&1

python3 - "$WT/test-reports" "$OUT/ci_recipe_summary.json" <<'PYEOF'
import json, sys, os, xml.etree.ElementTree as ET
rep, out = sys.argv[1:]
res = {}
for f in ("results.xml", "results-source-tree.xml"):
    c = dict(passed=0, failed=0, failed_ids=[])
    for tc in ET.parse(os.path.join(rep, f)).getroot().iter("testcase"):
        k = {x.tag for x in tc}
        if k & {"failure", "error"}:
            c["failed"] += 1; c["failed_ids"].append(f"{tc.get('classname')}::{tc.get('name')}")
        elif "skipped" not in k:
            c["passed"] += 1
    res[f] = c
s = json.dumps(res, indent=1)
open(out, "w").write(s + "\n")
print(s)
PYEOF

cd "$ROOT"; git worktree remove --force "$WT"
sed -i '' -e "s#$VENV#<venv>#g; s#$WT#<wt>#g; s#$SCRATCH#<scratch>#g; s#$HOME#~#g" -e "s#/private/var/folders/[^ '\"]*#<tmp>#g" "$LOG"
