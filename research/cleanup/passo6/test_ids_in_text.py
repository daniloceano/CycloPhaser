#!/usr/bin/env python
"""Passo 6a, commit 21 — the passo-5 scanner widened: ANY occurrence of a test-split
track id (word-bounded, inside text, comments, strings or code), not only a quoted
literal. Read-only; counts and file:line only, never an id.

    python research/cleanup/passo6/test_ids_in_text.py LABEL [REV] [PATHS...]
        REV: a git revision to read the files from (default: the working tree)
        PATHS: default tools/calibration_app docs

Test ids: every `test:` list of research/labels/split.yaml (top-level and batches).
Files: every tracked text file under PATHS (binary files skipped).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
label = sys.argv[1]
rev = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "WORKTREE" else None
paths = sys.argv[3:] or ["tools/calibration_app", "docs"]


def read(f):
    if rev:
        return subprocess.run(["git", "show", f"{rev}:{f}"], cwd=ROOT, capture_output=True).stdout
    return (ROOT / f).read_bytes()


split = yaml.safe_load((ROOT / "research/labels/split.yaml").read_text())
test_ids = {str(i) for i in split.get("test", [])}
for b in (split.get("batches") or {}).values():
    test_ids |= {str(i) for i in (b.get("test") or [])}
ls = ["git", "ls-tree", "-r", "--name-only", rev, "--", *paths] if rev else ["git", "ls-files", "--", *paths]
files = subprocess.check_output(ls, cwd=ROOT, text=True).split()
ID = re.compile(r"(?<![0-9A-Za-z_])(\d{8})(?![0-9A-Za-z_])")
hits, scanned = [], 0
for f in files:
    data = read(f)
    if b"\x00" in data[:4096]:
        continue
    scanned += 1
    for n, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
        k = sum(1 for m in ID.finditer(line) if m.group(1) in test_ids)
        if k:
            hits.append(dict(where=f"{f}:{n}", n_test_ids=k))
out = dict(label=label, rev=rev or "working tree", paths=paths, text_files_scanned=scanned,
           occurrences=sum(h["n_test_ids"] for h in hits), lines=len(hits), where=hits)
(Path(__file__).with_name(f"{label}.json")).write_text(json.dumps(out, indent=1))
print(f"{label} ({out['rev']}): {scanned} text files; test-split ids: {out['occurrences']} on {len(hits)} line(s)")
for h in hits:
    print(f"  {h['where']}  ({h['n_test_ids']})")
