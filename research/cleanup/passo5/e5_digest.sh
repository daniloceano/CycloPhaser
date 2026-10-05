#!/usr/bin/env bash
# Passo 5, E5 — the default-behaviour digest before and after correction (d), in one
# session, with the track files each run OPENS recorded (passo5/run_with_open_audit.py).
#   bash research/cleanup/passo5/e5_digest.sh <commit before (d)>
# before: the generator at <commit>, in a clean copy from which the test track files
#         were deleted (so it cannot open them);
# after:  the generator of this working tree.
# The generator appends to its ledger; the ledger is restored afterwards.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
PY="$HOME/miniconda3/envs/cyclophaser/bin/python"
P=research/cleanup/passo5
GEN=research/labels/diagnostics/front_b/default_behaviour_hash.py
LEDGER=research/labels/diagnostics/front_b/default_behaviour_sha256.txt
WT=$(bash $P/worktree_without_test.sh "$1" 2>/dev/null)
( cd "$WT" && PYTHONPATH="$WT" "$PY" -P "$ROOT/$P/run_with_open_audit.py" "$ROOT/$P/e5_before_audit.json" "$GEN" ) > $P/e5_before_raw.txt 2>&1
git worktree remove --force "$WT"
PYTHONPATH="$ROOT" "$PY" -P $P/run_with_open_audit.py $P/e5_after_audit.json "$GEN" > $P/e5_after_raw.txt 2>&1
git checkout -- "$LEDGER"
"$PY" - <<'PY'
import json, re, yaml
from pathlib import Path
P = Path("research/cleanup/passo5")
for n in ("e5_before_raw.txt", "e5_after_raw.txt"):
    t = (P / n).read_text()
    t = re.sub(r"/(Users|home)/[^\s'\"]+", "<path>", t)
    t = re.sub(r"/private/var/folders/[^\s'\"]+|/var/folders/[^\s'\"]+|/tmp/[^\s'\"]+", "<tmp>", t)
    (P / n).write_text(t)
def sha(n): return re.search(r"SHA256\s*=\s*([0-9a-f]{64})", (P / n).read_text()).group(1)
split = yaml.safe_load(open("research/labels/split.yaml"))
test = {str(i) for i in split["test"]}
listed = sorted(Path("tests/calibration_data").glob("*.csv"))
static = dict(csv_in_directory=len(listed), of_which_test_split=sum(1 for p in listed if p.stem in test))
b, a = json.loads((P / "e5_before_audit.json").read_text()), json.loads((P / "e5_after_audit.json").read_text())
b["script"] = a["script"] = "research/labels/diagnostics/front_b/default_behaviour_hash.py"
(P / "e5_before_audit.json").write_text(json.dumps(b, indent=1)); (P / "e5_after_audit.json").write_text(json.dumps(a, indent=1))
res = dict(before_generator_in_normal_tree_by_reading_the_code=static,
           before_run_in_copy_without_test_files=dict(opened=b["csv_opened_under_calibration_data"],
                                                      test=b["of_which_test_split"], sha256=sha("e5_before_raw.txt")),
           after_run_in_working_tree=dict(opened=a["csv_opened_under_calibration_data"],
                                          test=a["of_which_test_split"], sha256=sha("e5_after_raw.txt")))
res["digest_equal"] = res["before_run_in_copy_without_test_files"]["sha256"] == res["after_run_in_working_tree"]["sha256"]
(P / "e5.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
PY
