#!/usr/bin/env bash
# Criterion (b) with the CI sequence (research/cleanup/final/PREVISOES_ci.md).
#   SCRATCH=<dir outside the repo> bash research/cleanup/final/run_b_ci.sh LABEL REV
# In ONE session, on a clean copy (detached worktree at REV):
#   (b-ci)    the steps of build_test in .circleci/config.yml, in a NEW venv
#             (python3.12 -m venv): pip install --upgrade pip build; python -m build;
#             pip install dist/*.whl; pip install pytest pyyaml;
#             python -m pytest --junitxml=... at the root, no marker filter
#   (b-conda) python -m pytest -m "not browser" in the conda env `cyclophaser`
#   digest    the canonical default-behaviour generator, conda env
# Outputs (masked) in research/cleanup/final/: LABEL_header.txt, LABEL_ci_raw.txt,
# LABEL_conda_raw.txt, LABEL_digest_raw.txt, LABEL_summary.json.
set -u
LABEL="$1"
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
REV="$(git rev-parse "$2")"
OUT="$ROOT/research/cleanup/final"
PY="$HOME/miniconda3/envs/cyclophaser/bin/python"
WT="$SCRATCH/${LABEL}_wt"; VENV="$SCRATCH/${LABEL}_ci_venv"
git worktree add -q --detach "$WT" "$REV"
cd "$WT"
echo "worktree HEAD: $(git rev-parse HEAD) | changed files: $(git status --porcelain | wc -l | tr -d ' ') | date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$OUT/${LABEL}_header.txt"

# (b-ci)
{
  /opt/homebrew/bin/python3.12 -m venv "$VENV"
  . "$VENV/bin/activate"
  echo "python: $(python --version 2>&1) | venv: new"
  echo '$ pip install --upgrade pip build'; pip install -q --upgrade pip build; echo "exit $?"
  echo '$ python -m build'; python -m build > "$SCRATCH/${LABEL}_build.log" 2>&1; echo "exit $?"; tail -1 "$SCRATCH/${LABEL}_build.log"
  echo '$ pip install dist/*.whl'; pip install -q dist/*.whl; echo "exit $?"
  echo '$ pip install pytest pyyaml'; pip install -q pytest pyyaml; echo "exit $?"
  echo "installed: $(pip list --format=freeze 2>/dev/null | tr '\n' ' ')"
  echo "streamlit importable: $(python -c 'import streamlit' 2>/dev/null && echo yes || echo no)"
  echo '$ python -m pytest --junitxml=<scratch>/ci.xml'
  python -m pytest -p no:cacheprovider -rfE --junitxml="$SCRATCH/${LABEL}_ci.xml"
  echo "EXIT $?"
  deactivate
} > "$OUT/${LABEL}_ci_raw.txt" 2>&1
rm -rf dist build ./*.egg-info

# digest (same session)
"$PY" -P research/labels/diagnostics/front_b/default_behaviour_hash.py > "$OUT/${LABEL}_digest_raw.txt" 2>&1
echo "EXIT $?" >> "$OUT/${LABEL}_digest_raw.txt"

# (b-conda)
{
  "$PY" - <<'PYEOF'
import os, sys, cyclophaser
root = os.path.realpath(os.getcwd())
assert os.path.basename(sys.prefix) == "cyclophaser", sys.prefix
assert os.path.realpath(cyclophaser.__file__).startswith(root + os.sep), cyclophaser.__file__
print("assert OK: cyclophaser from the worktree | sys.prefix =", sys.prefix)
PYEOF
  "$PY" -m pytest -m "not browser" -q -p no:cacheprovider -rfE --junitxml="$SCRATCH/${LABEL}_conda.xml"
  echo "EXIT $?"
} > "$OUT/${LABEL}_conda_raw.txt" 2>&1

"$PY" - "$SCRATCH/${LABEL}_ci.xml" "$SCRATCH/${LABEL}_conda.xml" "$OUT/${LABEL}_summary.json" <<'PYEOF'
import json, sys, collections, xml.etree.ElementTree as ET
def counts(xml):
    c = dict(passed=0, failed=0, skipped=0, failed_ids=[])
    for tc in ET.parse(xml).getroot().iter("testcase"):
        k = {x.tag for x in tc}
        if k & {"failure", "error"}:
            c["failed"] += 1; c["failed_ids"].append(f"{tc.get('classname')}::{tc.get('name')}")
        elif "skipped" in k:
            c["skipped"] += 1
        else:
            c["passed"] += 1
    c["failed_by_module"] = dict(collections.Counter(i.split("::")[0].rsplit(".", 1)[0] if i.count(".") > 1 else i.split("::")[0]
                                                     for i in c["failed_ids"]))
    return c
res = dict(ci=counts(sys.argv[1]), conda=counts(sys.argv[2]))
json.dump(res, open(sys.argv[3], "w"), indent=1)
print(json.dumps({k: {a: b for a, b in v.items() if a != "failed_ids"} for k, v in res.items()}))
PYEOF

cd "$ROOT"; git worktree remove --force "$WT"
for f in "$OUT/${LABEL}"_*; do
  sed -i '' -e "s#$VENV#<ci-venv>#g; s#$WT#<wt>#g; s#$SCRATCH#<scratch>#g; s#$HOME#~#g" -e "s#/private/var/folders/[^ '\"]*#<tmp>#g" "$f"
done
grep -h "EXIT\|SHA256" "$OUT/${LABEL}"_*raw.txt
