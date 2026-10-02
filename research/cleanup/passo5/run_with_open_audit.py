#!/usr/bin/env python
"""Passo 5 — run a script and record which track files it OPENS (sys.addaudithook,
event "open"), without changing the script.

    <python> -P research/cleanup/passo5/run_with_open_audit.py AUDIT_JSON SCRIPT [ARGS...]

Writes AUDIT_JSON with COUNTS only: files opened under tests/calibration_data/
(top level and batch folders), and how many of them belong to a TEST list of
research/labels/split.yaml (top-level test split or a batch's test cases). No
id is written or printed. Run from the root of the tree to measure; the tree's
own split.yaml decides membership.
"""
import json
import os
import runpy
import sys
from pathlib import Path

import yaml

audit_out, script, *args = sys.argv[1:]
root = Path.cwd().resolve()
split = yaml.safe_load((root / "research/labels/split.yaml").read_text())
test_ids = {str(i) for i in split.get("test", [])}
for b in (split.get("batches") or {}).values():
    test_ids |= {str(i) for i in (b.get("test") or [])}
calib = (root / "tests" / "calibration_data").resolve()
opened = set()


def hook(event, a):
    if event == "open" and a and isinstance(a[0], (str, bytes, os.PathLike)):
        try:
            p = Path(os.fsdecode(a[0])).resolve()
        except Exception:
            return
        if p.suffix == ".csv" and calib in p.parents:
            opened.add(p)


sys.addaudithook(hook)
sys.argv = [script, *args]
sys.path.insert(0, str(root))
code = 0
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as e:
    code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
res = dict(script=script, args=args, exit=code, csv_opened_under_calibration_data=len(opened),
           of_which_test_split=sum(1 for p in opened if p.stem in test_ids))
Path(audit_out).write_text(json.dumps(res, indent=1))
print(f"[audit] {res['csv_opened_under_calibration_data']} track files opened, "
      f"{res['of_which_test_split']} of them in a test list", file=sys.stderr)
sys.exit(code)
