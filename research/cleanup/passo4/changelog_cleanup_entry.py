#!/usr/bin/env python
"""Passo 4, commit 17 — the CHANGELOG [Unreleased] entry on the repository
clean-up, numbers read from passo3/ outputs and git (never typed). Run once.

    python research/cleanup/passo4/changelog_cleanup_entry.py
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P3 = ROOT / "research/cleanup/passo3"
TAG = "archive/research-diagnostics-pre-cleanup"
T = json.loads((P3 / "tag_and_trace.json").read_text())["R1"]
removed_list = [l for l in (P3 / "removed_files.txt").read_text().splitlines() if l]
tracked = set(subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).split())
restored = [r for r in removed_list if r in tracked]
tag_commit = subprocess.check_output(["git", "rev-parse", "--short", f"{TAG}^{{commit}}"], cwd=ROOT, text=True).strip()
restore_commit = subprocess.check_output(
    ["git", "log", "--format=%h", "-1", "--diff-filter=A", "--", *restored], cwd=ROOT, text=True).strip()
assert T["same_set"] and len(removed_list) == T["listed"]
entry = f"""### Changed — repository clean-up: research diagnostics archived (clean-up front)

Research diagnostics that no live file needs were removed from the tree:
{T['listed']} files, deleted by `{T['removal_commit']}`. Every one of them is kept at
the tag `{TAG}` (`{tag_commit}`) and is read with
`git show {TAG}:<path>`; {len(restored)} of them
(`{restored[0]}`) was restored to the tree by `{restore_commit}`.
Live files that cited a removed path now cite it in that form. The findings the
removed reports supported are consolidated, with their citations, in
`docs/findings.md`. Nothing under `cyclophaser/` changed in this step.

"""
p = ROOT / "CHANGELOG.md"
s = p.read_text()
anchor = "### Changed — calibration app: the sidebar opens with the package defaults"
assert s.count(anchor) == 1
p.write_text(s.replace(anchor, entry + anchor))
print(entry)
