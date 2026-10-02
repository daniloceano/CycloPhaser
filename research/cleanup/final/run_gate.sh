#!/usr/bin/env bash
# Final gate of the clean-up front — measured ONCE, in a clean copy of the branch
# (a detached git worktree at REV), never in the working tree.
#   SCRATCH=<dir outside the repo> bash research/cleanup/final/run_gate.sh [REV]
# Outputs (paths masked) land in research/cleanup/final/ of the main working tree;
# RELATORIO_FINAL.md is rendered from them by final/make_report.py.
#   (a) final/gate_a.py                         -> gate_a.json, gate_a_output.txt
#   (b) default digest (canonical generator), suite -m "not browser" (dedicated env),
#       app tests (passo5/app_tests.py list) in the dedicated env (from the suite run)
#       and in a fresh venv with tools/calibration_app/requirements-app.txt
#                                               -> b_*.txt, b_summary.json
#   (c) passo3/tag_and_trace.py (S10 = R3), passo2/verify_citations.py -> c_*
#   (d) passo4/check_documented_defaults.py     -> d_defaults.{json,md}
#   (e) final/d2_head.py                        -> e_d2.{json,md}
#   (f) passo6/post_6b.py (git ls-remote)       -> f_post_6b.json
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
REV="$(git rev-parse "${1:-HEAD}")"
F=research/cleanup/final
PY="$HOME/miniconda3/envs/cyclophaser/bin/python"
WT="$SCRATCH/gate_wt"; VENV="$SCRATCH/pinned_venv"
OUT="$ROOT/$F"
git fetch -q --prune --tags origin
git worktree add -q --detach "$WT" "$REV"
cd "$WT"
{
  echo "worktree HEAD: $(git rev-parse HEAD) | changed files: $(git status --porcelain | wc -l | tr -d ' ')"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ) | dedicated env: $("$PY" -c 'import sys; print(sys.prefix.rsplit("/",1)[-1], sys.version.split()[0])')"
} > "$OUT/gate_header.txt"

# (a)
"$PY" $F/gate_a.py > "$OUT/gate_a_output.txt" 2>&1; echo "EXIT $?" >> "$OUT/gate_a_output.txt"
cp $F/gate_a.json "$OUT/gate_a.json"

# (b) digest — same session as the suite
"$PY" -P research/labels/diagnostics/front_b/default_behaviour_hash.py > "$OUT/b_digest_raw.txt" 2>&1
echo "EXIT $?" >> "$OUT/b_digest_raw.txt"
# (b) suite, dedicated env; the package must come from this worktree
{
  "$PY" - <<'PYEOF'
import os, sys, cyclophaser
root = os.path.realpath(os.getcwd())
assert os.path.basename(sys.prefix) == "cyclophaser", sys.prefix
assert os.path.realpath(cyclophaser.__file__).startswith(root + os.sep), cyclophaser.__file__
print("assert OK: cyclophaser from the worktree | sys.prefix =", sys.prefix)
PYEOF
  "$PY" -m pytest -m "not browser" -q -p no:cacheprovider -rf --junitxml="$SCRATCH/suite.xml"
  echo "EXIT $?"
} > "$OUT/b_suite_raw.txt" 2>&1
"$PY" research/cleanup/passo5/app_tests.py > /dev/null && cp research/cleanup/passo5/app_tests.txt "$OUT/b_app_tests.txt"
# (b) app tests, pinned versions, fresh venv
{
  /opt/homebrew/bin/python3.12 -m venv "$VENV"
  ( cd tools/calibration_app && "$VENV/bin/pip" install -q -r requirements-app.txt pytest ) && echo "pinned venv installed"
  "$VENV/bin/python" -c "import streamlit, pandas, numpy, cyclophaser, sys, os; print('python', sys.version.split()[0], '| streamlit', streamlit.__version__, '| pandas', pandas.__version__, '| numpy', numpy.__version__); print('cyclophaser from the worktree:', os.path.realpath(cyclophaser.__file__).startswith(os.path.realpath(os.getcwd()) + os.sep))"
  "$VENV/bin/python" -m pytest -m "not browser" -q -p no:cacheprovider -rf --junitxml="$SCRATCH/pinned.xml" $(cat research/cleanup/passo5/app_tests.txt)
  echo "EXIT $?"
} > "$OUT/b_app_pinned_raw.txt" 2>&1

# (c)
"$PY" research/cleanup/passo3/tag_and_trace.py > "$OUT/c_tag_and_trace_output.txt" 2>&1; echo "EXIT $?" >> "$OUT/c_tag_and_trace_output.txt"
cp research/cleanup/passo3/tag_and_trace.json "$OUT/c_tag_and_trace.json"
"$PY" research/cleanup/passo2/verify_citations.py > "$OUT/c_verify_citations_output.txt" 2>&1; echo "EXIT $?" >> "$OUT/c_verify_citations_output.txt"
cp research/cleanup/passo2/verify_citations.json "$OUT/c_verify_citations.json"
cp research/cleanup/passo2/weak_citations.txt "$OUT/c_weak_citations.txt"

# (d)
"$PY" -P research/cleanup/passo4/check_documented_defaults.py d_defaults > "$OUT/d_defaults_output.txt" 2>&1; echo "EXIT $?" >> "$OUT/d_defaults_output.txt"
cp research/cleanup/passo4/d_defaults.json research/cleanup/passo4/d_defaults.md "$OUT/"

# (e)
"$PY" $F/d2_head.py e_d2 > "$OUT/e_d2_output.txt" 2>&1; echo "EXIT $?" >> "$OUT/e_d2_output.txt"
cp $F/e_d2.json $F/e_d2.md "$OUT/"

# (f)
"$PY" research/cleanup/passo6/post_6b.py > "$OUT/f_post_6b_output.txt" 2>&1; echo "EXIT $?" >> "$OUT/f_post_6b_output.txt"
cp research/cleanup/passo6/post_6b.json "$OUT/f_post_6b.json"

# junit -> counts (no hostnames or paths kept)
"$PY" - "$SCRATCH/suite.xml" "$SCRATCH/pinned.xml" "$OUT/b_app_tests.txt" "$OUT/b_summary.json" <<'PYEOF'
import json, sys, xml.etree.ElementTree as ET
suite, pinned, app_list, out = sys.argv[1:5]
app_mods = [l.strip()[:-3].replace("/", ".") for l in open(app_list) if l.strip()]
def counts(xml, only_app):
    c = dict(passed=0, failed=0, skipped=0, failed_ids=[])
    for tc in ET.parse(xml).getroot().iter("testcase"):
        cl = tc.get("classname", "")
        if only_app and not any(cl == m or cl.startswith(m + ".") for m in app_mods):
            continue
        kids = {k.tag for k in tc}
        if kids & {"failure", "error"}:
            c["failed"] += 1; c["failed_ids"].append(f"{cl}::{tc.get('name')}")
        elif "skipped" in kids:
            c["skipped"] += 1
        else:
            c["passed"] += 1
    return c
res = dict(app_test_files=len(app_mods), suite=counts(suite, False), app_dedicated=counts(suite, True),
           app_pinned=counts(pinned, True))
json.dump(res, open(out, "w"), indent=1); print(json.dumps({k: v if not isinstance(v, dict) else {a: b for a, b in v.items() if a != "failed_ids"} for k, v in res.items()}))
PYEOF

cd "$ROOT"
git worktree remove --force "$WT"
# mask machine paths in everything written
for f in "$OUT"/gate_header.txt "$OUT"/*_output.txt "$OUT"/*_raw.txt "$OUT"/*.json "$OUT"/*.md; do
  [ -f "$f" ] || continue
  sed -i '' -e "s#$VENV#<pinned-venv>#g; s#$WT#<wt>#g; s#$SCRATCH#<scratch>#g; s#$HOME#~#g" -e "s#/private/var/folders/[^ '\"]*#<tmp>#g" "$f"
done
grep -h "EXIT" "$OUT"/*_output.txt "$OUT"/*_raw.txt
