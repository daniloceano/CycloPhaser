#!/usr/bin/env python
"""Passo 4, commit 17 — mentions of removed paths in CHANGELOG.md [Unreleased],
with the corrected R4 definition of passo3/live_refs.py (any suffix of 2+
components, or the bare name when no file at HEAD carries it; the archived form
`archive/research-diagnostics-pre-cleanup:<path>` does not count).

    python research/cleanup/passo4/changelog_removed_refs.py LABEL   # writes LABEL.json next to it
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research/cleanup/passo3"))
from live_refs import ARCHIVED, mention_patterns, removed  # noqa: E402

label = sys.argv[1]
rem = set(removed())
head = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).split()
pats = mention_patterns(rem, {Path(t).name for t in head})
lines = (ROOT / "CHANGELOG.md").read_text().splitlines()
start = next(i for i, l in enumerate(lines) if l.startswith("## [Unreleased]"))
end = next(i for i, l in enumerate(lines) if l.startswith("## [") and i > start)
refs = []
for i in range(start, end):
    clean = ARCHIVED.sub(" ", lines[i])
    for r in sorted(rem):
        if any(p.search(clean) for p in pats[r]):
            refs.append(dict(line=i + 1, removed=r, text=lines[i].strip()[:160]))
out = dict(section=[start + 1, end], references=len(refs), refs=refs)
(HERE / f"{label}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(f"[Unreleased] lines {start+1}-{end}: {len(refs)} mentions of removed paths")
for r in refs:
    print(f"  CHANGELOG.md:{r['line']} -> {r['removed']}")
