#!/usr/bin/env bash
# Release v2.1, part B, passo 2 — item 7: the new build_test job, run locally.
#   SCRATCH=<dir outside the repo> bash research/release_v21/parteB_passo2/run_ci_steps.sh REV
# A detached, clean worktree of REV and a NEW python3.12 venv; then the job's own
# commands, verbatim from .circleci/config.yml @ REV, in the worktree root:
#   pip install --upgrade pip build; python -m build; pip install dist/*.whl;
#   pip install pytest pyyaml;
#   CYCLOPHASER_REQUIRE_INSTALLED=1 pytest --import-mode=append -m "not source_tree" --junitxml=test-reports/results.xml
#   python -m pytest -m source_tree --junitxml=test-reports/results-source-tree.xml
# Counts come from the junit files; __file__ from the line tests/conftest.py prints.
# Then two controls that are NOT part of the job (after both steps, outputs elsewhere):
#   C1 the lock refuses the source: CYCLOPHASER_REQUIRE_INSTALLED=1 python -m pytest
#   C2 the end-of-session check catches a late swap to the source.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
REV="$(git rev-parse "$1")"
OUT="$ROOT/research/release_v21/parteB_passo2"
WT="$SCRATCH/pb2_wt"; VENV="$SCRATCH/pb2_venv"; RAW="$SCRATCH/pb2_raw"
rm -rf "$WT" "$VENV" "$RAW"; mkdir -p "$RAW"
git worktree add -q --detach "$WT" "$REV"
cd "$WT"
LOG="$OUT/07_ci_steps_raw.txt"
step() {  # name, command...
  local name="$1"; shift
  echo; echo "=== $name"; echo "\$ $*"
  "$@" > "$RAW/$name.log" 2>&1; local rc=$?
  echo "exit $rc"
  grep -E "^collected|cyclophaser.__file__|CYCLOPHASER_REQUIRE_INSTALLED|^=+ .*(passed|failed|error|skipped|deselected).* =+$|^[0-9]+ (passed|failed)|^(FAILED|ERROR)|Successfully (built|installed)" "$RAW/$name.log" | head -20
}
{
  echo "worktree HEAD: $(git rev-parse HEAD) | changed files: $(git status --porcelain | wc -l | tr -d ' ') | date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  /opt/homebrew/bin/python3.12 -m venv "$VENV"
  . "$VENV/bin/activate"
  echo "python: $(python --version 2>&1) at $(which python) | venv: new"
  step install_build_tools pip install --upgrade pip build
  step build python -m build
  step install_wheel bash -c 'pip install dist/*.whl'
  step install_test_deps pip install pytest pyyaml
  echo; echo "worktree after build (untracked/ignored): $(git status --porcelain --ignored | tr '\n' ' ')"
  echo "tracked files changed: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')"
  echo "playwright importable: $(python -c 'import playwright' 2>/dev/null && echo yes || echo no)"
  echo "dist: $(ls dist | tr '\n' ' ')"
  echo "wheel LICENSE entries: $(unzip -l dist/*.whl | awk '/[Ll][Ii][Cc][Ee][Nn][Ss][Ee]/{print $4}' | tr '\n' ' ')"
  echo "wheel sha256: $(shasum -a 256 dist/*.whl | cut -c1-16)…"
  echo "installed: $(pip list --format=freeze 2>/dev/null | tr '\n' ' ')"
  step main_wheel env CYCLOPHASER_REQUIRE_INSTALLED=1 pytest --import-mode=append -m "not source_tree" --junitxml=test-reports/results.xml
  step source_tree python -m pytest -m source_tree --junitxml=test-reports/results-source-tree.xml
  # controls (not CI steps)
  step C1_lock_refuses_source env CYCLOPHASER_REQUIRE_INSTALLED=1 python -m pytest -p no:cacheprovider tests/test_track_io.py
  mkdir -p "$RAW/c2"; cat > tests/test_zz_c2_late_swap.py <<'PYEOF'
import importlib, sys
def test_swap_to_source():
    for n in [m for m in sys.modules if m == "cyclophaser" or m.startswith("cyclophaser.")]:
        del sys.modules[n]
    sys.path.insert(0, ".")
    import cyclophaser
    assert "site-packages" not in cyclophaser.__file__
PYEOF
  step C2_late_swap_caught env CYCLOPHASER_REQUIRE_INSTALLED=1 pytest --import-mode=append -p no:cacheprovider tests/test_zz_c2_late_swap.py
  rm -f tests/test_zz_c2_late_swap.py
  deactivate
} > "$LOG" 2>&1

python3 - "$WT/test-reports" "$OUT/07_ci_steps_summary.json" <<'PYEOF'
import json, sys, os, xml.etree.ElementTree as ET
rep, out = sys.argv[1:]
res = {}
for f in ("results.xml", "results-source-tree.xml"):
    c = dict(passed=0, failed=0, skipped=0, failed_ids=[], skipped_ids=[])
    for tc in ET.parse(os.path.join(rep, f)).getroot().iter("testcase"):
        k = {x.tag for x in tc}
        if k & {"failure", "error"}:
            c["failed"] += 1; c["failed_ids"].append(f"{tc.get('classname')}::{tc.get('name')}")
        elif "skipped" in k:
            c["skipped"] += 1; c["skipped_ids"].append(f"{tc.get('classname')}::{tc.get('name')}")
        else:
            c["passed"] += 1
    res[f] = c
a, b = (set(res[f]["skipped_ids"]) for f in ("results.xml", "results-source-tree.xml"))
res["source_tree_skips_subset_of_main_skips"] = b <= a
res["union_of_skips"] = len(a | b)
s = json.dumps(res, indent=1)
open(out, "w").write(s + "\n")
print(s)
PYEOF

cd "$ROOT"; git worktree remove --force "$WT"
sed -i '' -e "s#$VENV#<venv>#g; s#$WT#<wt>#g; s#$SCRATCH#<scratch>#g; s#$HOME#~#g" -e "s#/private/var/folders/[^ '\"]*#<tmp>#g" "$LOG"
