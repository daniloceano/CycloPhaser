#!/usr/bin/env python
"""Passo 3, R1–R3 — removal count, presence at the archive tag, traceability of S10.

    python research/cleanup/passo3/tag_and_trace.py

R1  number of files in passo3/removed_files.txt, the number actually deleted by
    the removal commit (git diff --name-only --diff-filter=D against its parent),
    and whether the two sets are equal; plus a count per top-level directory.
R2  every path in removed_files.txt exists at the tag (`git cat-file -e`).
R3  every row of the S10 table of docs/findings.md resolves: the file that left
    exists at the tag (a glob row: every match at the tag); every `§Sxx`
    destination is a section of docs/findings.md; every
    `docs/future_work.md:N@<commit>` destination exists at HEAD with the same
    text as at <commit>.
Writes tag_and_trace.json next to it; exit 1 on any failure.
"""
import fnmatch
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TAG = "archive/research-diagnostics-pre-cleanup"
REMOVAL_COMMIT_MSG = "passo 3, commit 12"


def git(*a, check=True):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=check)


def main():
    listed = [l for l in (Path(__file__).with_name("removed_files.txt")).read_text().splitlines() if l]
    commit = git("log", "--format=%H", "-1", f"--grep={REMOVAL_COMMIT_MSG}").stdout.strip()
    deleted = git("diff", "--name-only", "--diff-filter=D", f"{commit}^", commit).stdout.split()
    per_dir = Counter("/".join(p.split("/")[:2]) if p.startswith("research/") else p.split("/")[0] for p in listed)
    per_dir_fine = Counter("/".join(p.split("/")[:4]) if p.startswith("research/labels/diagnostics/")
                           else "/".join(p.split("/")[:2]) for p in listed)
    r1 = dict(listed=len(listed), deleted_by_commit=len(deleted), same_set=set(listed) == set(deleted),
              removal_commit=commit[:7], per_top_dir=dict(sorted(per_dir.items())),
              per_dir=dict(sorted(per_dir_fine.items())))

    missing = [p for p in listed if git("cat-file", "-e", f"{TAG}:{p}", check=False).returncode != 0]
    r2 = dict(checked=len(listed), present_at_tag=len(listed) - len(missing), missing=missing)

    doc = (ROOT / "docs/findings.md").read_text()
    sections = set(re.findall(r"^## (S\d\d)\b", doc, re.M))
    s10 = doc[doc.index("## S10"):doc.index("## S11")]
    tag_files = git("ls-tree", "-r", "--name-only", TAG).stdout.split()
    head_fw = (ROOT / "docs/future_work.md").read_text().splitlines()
    rows, fails = 0, []
    for line in s10.splitlines():
        if not line.startswith("| `"):
            continue
        rows += 1
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        path, dest = cells[0].strip("`"), cells[3]
        matches = [t for t in tag_files if fnmatch.fnmatch(t, path)] if "*" in path else ([path] if path in tag_files else [])
        if not matches:
            fails.append(dict(row=path, kind="not at tag"))
        for s in re.findall(r"§(S\d\d)", dest):
            if s not in sections:
                fails.append(dict(row=path, kind="section missing", section=s))
        for f, n, c in re.findall(r"`(docs/future_work\.md):(\d+)@([0-9a-f]+)`", dest):
            old = git("show", f"{c}:{f}").stdout.splitlines()
            n = int(n)
            if n > len(head_fw) or n > len(old) or head_fw[n - 1] != old[n - 1]:
                fails.append(dict(row=path, kind="future_work line differs at HEAD", line=n))
    r3 = dict(rows=rows, failures=fails)

    out = dict(R1=r1, R2=r2, R3=r3)
    (Path(__file__).with_name("tag_and_trace.json")).write_text(json.dumps(out, indent=1))
    print(f"R1: listed {len(listed)}, deleted by {commit[:7]} {len(deleted)}, same set {r1['same_set']}")
    print(f"    per top-level dir: {r1['per_top_dir']}")
    print(f"R2: {r2['present_at_tag']}/{len(listed)} present at {TAG}")
    print(f"R3: {rows} S10 rows; failures {len(fails)}")
    for f in fails:
        print("   ", f)
    sys.exit(0 if (r1["same_set"] and not missing and not fails) else 1)


if __name__ == "__main__":
    main()
