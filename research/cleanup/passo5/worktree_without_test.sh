#!/usr/bin/env bash
# Passo 5 — a clean copy of the branch at <commit> from which every TEST track
# file (top-level test split and the batches' test cases, per its split.yaml) is
# deleted, so code run in it cannot open them. Prints the worktree path.
#   bash research/cleanup/passo5/worktree_without_test.sh <commit>
set -eu
ROOT="$(git rev-parse --show-toplevel)"
WT="$(mktemp -d)/wt"
git -C "$ROOT" worktree add -q --detach "$WT" "$1"
"$HOME/miniconda3/envs/cyclophaser/bin/python" - "$WT" <<'PY'
import sys, yaml
from pathlib import Path
wt = Path(sys.argv[1]); split = yaml.safe_load((wt / "research/labels/split.yaml").read_text())
ids = {str(i) for i in split.get("test", [])}
dirs = [wt / "tests/calibration_data"]
for b in (split.get("batches") or {}).values():
    ids |= {str(i) for i in (b.get("test") or [])}
    if b.get("data_dir"): dirs.append(wt / b["data_dir"])
n = 0
for d in dirs:
    for p in d.glob("*.csv"):
        if p.stem in ids: p.unlink(); n += 1
print(f"removed {n} test track files from the copy", file=sys.stderr)
PY
echo "$WT"
