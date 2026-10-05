#!/usr/bin/env bash
# Release v2.1, part A, passo 2 — the full suite by the CI recipe (build_test in
# .circleci/config.yml), adapted from research/cleanup/final/run_b_ci.sh (b-ci only).
#   SCRATCH=<dir outside the repo> bash research/release_v21/passo2/run_suite_ci.sh REV
# On a clean copy (detached worktree at REV), in a NEW venv (python3.12 -m venv):
#   pip install --upgrade pip build; python -m build; pip install dist/*.whl;
#   pip install pytest pyyaml; python -m pytest --junitxml=... at the root, no marker filter.
# Outputs (machine paths masked) in research/release_v21/passo2/: suite_ci_raw.txt,
# suite_ci_summary.json. Nothing is fixed if something fails; it is only reported.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
REV="$(git rev-parse "$1")"
OUT="$ROOT/research/release_v21/passo2"
WT="$SCRATCH/suite_wt"; VENV="$SCRATCH/suite_ci_venv"
git worktree add -q --detach "$WT" "$REV"
cd "$WT"
{
  echo "worktree HEAD: $(git rev-parse HEAD) | changed files: $(git status --porcelain | wc -l | tr -d ' ') | date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  /opt/homebrew/bin/python3.12 -m venv "$VENV"
  . "$VENV/bin/activate"
  echo "python: $(python --version 2>&1) | venv: new"
  echo '$ pip install --upgrade pip build'; pip install -q --upgrade pip build; echo "exit $?"
  echo '$ python -m build'; python -m build > "$SCRATCH/suite_build.log" 2>&1; echo "exit $?"; tail -1 "$SCRATCH/suite_build.log"
  echo '$ pip install dist/*.whl'; pip install -q dist/*.whl; echo "exit $?"
  echo '$ pip install pytest pyyaml'; pip install -q pytest pyyaml; echo "exit $?"
  echo "installed: $(pip list --format=freeze 2>/dev/null | tr '\n' ' ')"
  echo "playwright importable: $(python -c 'import playwright' 2>/dev/null && echo yes || echo no)"
  echo '$ python -m pytest --junitxml=<scratch>/suite_ci.xml'
  python -m pytest -p no:cacheprovider -rfE --junitxml="$SCRATCH/suite_ci.xml"
  echo "EXIT $?"
  deactivate
} > "$OUT/suite_ci_raw.txt" 2>&1

python3 - "$SCRATCH/suite_ci.xml" "$OUT/suite_ci_summary.json" <<'PYEOF'
import json, sys, xml.etree.ElementTree as ET
c = dict(passed=0, failed=0, failed_ids=[])
for tc in ET.parse(sys.argv[1]).getroot().iter("testcase"):
    k = {x.tag for x in tc}
    if k & {"failure", "error"}:
        c["failed"] += 1; c["failed_ids"].append(f"{tc.get('classname')}::{tc.get('name')}")
    elif "skipped" not in k:
        c["passed"] += 1
json.dump(c, open(sys.argv[2], "w"), indent=1)
print(json.dumps(c))
PYEOF

cd "$ROOT"; git worktree remove --force "$WT"
for f in "$OUT"/suite_ci_raw.txt; do
  sed -i '' -e "s#$VENV#<ci-venv>#g; s#$WT#<wt>#g; s#$SCRATCH#<scratch>#g; s#$HOME#~#g" -e "s#/private/var/folders/[^ '\"]*#<tmp>#g" "$f"
done
grep -h "EXIT\|passed\|failed" "$OUT/suite_ci_raw.txt" | tail -3
