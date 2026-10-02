#!/usr/bin/env python
"""Passo 5, (b) — literal track ids of the TEST split in the app's and the tests'
code (read-only). Prints and writes COUNTS and file:line only, never an id.

    python research/cleanup/passo5/test_ids_in_code.py LABEL   # writes LABEL.json next to it

Scans every tracked .py under tools/calibration_app/ and tests/ for quoted
8-digit literals and intersects them with every `test:` list of
research/labels/split.yaml (the top-level split and the batches).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
split = yaml.safe_load((ROOT / "research/labels/split.yaml").read_text())
test_ids = {str(i) for i in split.get("test", [])}
for b in (split.get("batches") or {}).values():
    test_ids |= {str(i) for i in (b.get("test") or [])}
files = [f for f in subprocess.check_output(["git", "ls-files", "tools/calibration_app", "tests"], cwd=ROOT,
                                            text=True).split() if f.endswith(".py")]
LIT = re.compile(r"""["'](\d{8})["']""")
hits = []
for f in files:
    for n, line in enumerate((ROOT / f).read_text().splitlines(), 1):
        k = sum(1 for m in LIT.finditer(line) if m.group(1) in test_ids)
        if k:
            hits.append(dict(where=f"{f}:{n}", n_test_ids=k))
out = dict(label=sys.argv[1], files_scanned=len(files), lines_with_test_ids=len(hits),
           test_id_literals=sum(h["n_test_ids"] for h in hits), where=hits)
(Path(__file__).with_name(f"{sys.argv[1]}.json")).write_text(json.dumps(out, indent=1))
print(f"{len(files)} files; test-split id literals: {out['test_id_literals']} on {len(hits)} line(s)")
for h in hits:
    print(f"  {h['where']}  ({h['n_test_ids']})")
