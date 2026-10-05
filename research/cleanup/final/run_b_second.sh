#!/usr/bin/env bash
# Final gate (b) — SECOND measurement, after the fix of the collection error that
# made the first one FAIL (d44802e). Recorded beside the first, which stands.
# Clean copy (detached worktree at REV); suite -m "not browser" in the dedicated
# env (app tests counted from the same run) and the default digest, one session.
# The pinned-version app run of the first measurement is not repeated: it selects
# the app test files explicitly, so the collection error did not reach it.
#   SCRATCH=<dir outside the repo> bash research/cleanup/final/run_b_second.sh REV
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
REV="$(git rev-parse "$1")"
F=research/cleanup/final; OUT="$ROOT/$F"
PY="$HOME/miniconda3/envs/cyclophaser/bin/python"
WT="$SCRATCH/gate_b2_wt"
git worktree add -q --detach "$WT" "$REV"
cd "$WT"
echo "worktree HEAD: $(git rev-parse HEAD) | changed files: $(git status --porcelain | wc -l | tr -d ' ') | date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$OUT/b2_header.txt"
"$PY" -P research/labels/diagnostics/front_b/default_behaviour_hash.py > "$OUT/b2_digest_raw.txt" 2>&1; echo "EXIT $?" >> "$OUT/b2_digest_raw.txt"
{
  "$PY" - <<'PYEOF'
import os, sys, cyclophaser
root = os.path.realpath(os.getcwd())
assert os.path.basename(sys.prefix) == "cyclophaser", sys.prefix
assert os.path.realpath(cyclophaser.__file__).startswith(root + os.sep), cyclophaser.__file__
print("assert OK: cyclophaser from the worktree | sys.prefix =", sys.prefix)
PYEOF
  "$PY" -m pytest -m "not browser" -q -p no:cacheprovider -rf --junitxml="$SCRATCH/suite2.xml"
  echo "EXIT $?"
} > "$OUT/b2_suite_raw.txt" 2>&1
"$PY" - "$SCRATCH/suite2.xml" "$OUT/b_app_tests.txt" "$OUT/b2_summary.json" <<'PYEOF'
import json, sys, xml.etree.ElementTree as ET
xml, app_list, out = sys.argv[1:4]
mods = [l.strip()[:-3].replace("/", ".") for l in open(app_list) if l.strip()]
def counts(only_app):
    c = dict(passed=0, failed=0, skipped=0, failed_ids=[])
    for tc in ET.parse(xml).getroot().iter("testcase"):
        cl = tc.get("classname", "")
        if only_app and not any(cl == m or cl.startswith(m + ".") for m in mods):
            continue
        k = {x.tag for x in tc}
        if k & {"failure", "error"}: c["failed"] += 1; c["failed_ids"].append(f"{cl}::{tc.get('name')}")
        elif "skipped" in k: c["skipped"] += 1
        else: c["passed"] += 1
    return c
res = dict(suite=counts(False), app_dedicated=counts(True)); json.dump(res, open(out, "w"), indent=1); print(res)
PYEOF
cd "$ROOT"; git worktree remove --force "$WT"
for f in "$OUT"/b2_*; do sed -i '' -e "s#$WT#<wt>#g; s#$SCRATCH#<scratch>#g; s#$HOME#~#g" -e "s#/private/var/folders/[^ '\"]*#<tmp>#g" "$f"; done
grep -h "EXIT\|SHA256" "$OUT"/b2_*raw.txt; tail -3 "$OUT/b2_suite_raw.txt" | head -2
