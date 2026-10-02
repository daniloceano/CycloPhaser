#!/usr/bin/env python
"""Passo 6b, after the deletion — read-only. Writes post_6b.json next to it.

    git fetch --prune --tags origin
    python research/cleanup/passo6/post_6b.py

1. The branches on origin now (git ls-remote, not the local remote-tracking refs).
2. Remote branches deleted = (remote branches of branches.json @ fbeff00) minus
   (branches on origin now); compared with the authorised remote list of
   removal_list.md @ fbeff00 — must be equal as sets.
3. Every tag of tags.json @ fbeff00 still exists on origin, at its tip.
4. Reachability of every commit cited in a tracked file (same token rule as
   verify.py) from the refs that exist ON ORIGIN now (heads + tags) — what a fresh
   clone sees — and, for comparison, from all local refs.
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTH = "fbeff00"
REL = "research/cleanup/passo6"
HEX = re.compile(r"(?<![0-9a-fA-F])([0-9a-f]{7,40})(?![0-9a-fA-F])")


def git(*a, inp=None):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, input=inp).stdout


heads, tag_peeled, tag_objs = {}, {}, {}
for line in git("ls-remote", "origin").splitlines():
    h, ref = line.split("\t")
    if ref.startswith("refs/heads/"):
        heads[ref[len("refs/heads/"):]] = h
    elif ref.startswith("refs/tags/"):
        name = ref[len("refs/tags/"):]
        if name.endswith("^{}"):
            tag_peeled[name[:-3]] = h
        else:
            tag_objs[name] = h
tag_commits = {t: tag_peeled.get(t, h) for t, h in tag_objs.items()}

before = {r["branch"] for r in json.loads(git("show", f"{AUTH}:{REL}/branches.json"))["remote"]}
listing = git("show", f"{AUTH}:{REL}/removal_list.md")
authorised_remote = set()
in_remote = False
for line in listing.splitlines():
    if line.startswith("## "):
        in_remote = line.startswith("## Remote")
    m = re.match(r"- `([^`]+)`", line)
    if m and in_remote:
        authorised_remote.add(m.group(1))
deleted = before - set(heads)
tags = json.loads(git("show", f"{AUTH}:{REL}/tags.json"))
tag_rows = [dict(tag=t["tag"], tip=t["tip"][:7], origin=(tag_commits.get(t["tag"]) or "")[:7],
                 ok=tag_commits.get(t["tag"]) == t["tip"]) for t in tags]

tokens = {}
for f in git("ls-files").splitlines():
    try:
        data = (ROOT / f).read_bytes()
    except OSError:
        continue
    if b"\x00" in data[:4096]:
        continue
    for n, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
        for m in HEX.finditer(line):
            tokens.setdefault(m.group(1), f"{f}:{n}")
check = git("cat-file", "--batch-check=%(objectname) %(objecttype)", inp="\n".join(tokens) + "\n").splitlines()
commits = {}
for tok, res in zip(tokens, check):
    parts = res.split()
    if len(parts) == 2 and parts[1] == "commit":
        commits[tok] = parts[0]
origin_tips = sorted(set(heads.values()) | set(tag_commits.values()))
on_origin = set(git("rev-list", *origin_tips).split())
local_all = set(git("rev-list", "--all").split())
unreach = {t: c for t, c in commits.items() if c not in on_origin}
res = dict(
    remote_branches_now=sorted(heads), remote_branch_tips={b: h[:7] for b, h in sorted(heads.items())},
    remote_branches_before=len(before), deleted_remote=sorted(deleted),
    deleted_equals_authorised=deleted == authorised_remote,
    deleted_not_authorised=sorted(deleted - authorised_remote),
    authorised_not_deleted=sorted(authorised_remote - deleted),
    new_remote_branches_since_6a=sorted(set(heads) - before),
    local_branches_now=git("for-each-ref", "--format=%(refname:short)", "refs/heads").split(),
    tags=tag_rows, tags_ok=all(r["ok"] for r in tag_rows), tags_on_origin=sorted(tag_commits),
    hex_tokens=len(tokens), tokens_resolving_to_commits=len(commits),
    distinct_cited_commits=len(set(commits.values())),
    unreachable_from_origin=len(set(unreach.values())),
    unreachable_rows=[dict(token=t, commit=c[:10], first_citation=tokens[t]) for t, c in unreach.items()],
    unreachable_from_all_local_refs=len({c for c in commits.values() if c not in local_all}),
)
(HERE / "post_6b.json").write_text(json.dumps(res, indent=1) + "\n")
print("remote branches now:", res["remote_branches_now"])
print(f"deleted on origin: {len(deleted)} (before {len(before)}); equals the authorised list: "
      f"{res['deleted_equals_authorised']}; new since 6a: {res['new_remote_branches_since_6a']}")
print(f"archive tags on origin at their tips: {sum(r['ok'] for r in tag_rows)}/{len(tag_rows)}")
print(f"cited commits: {res['distinct_cited_commits']} distinct; unreachable from origin: "
      f"{res['unreachable_from_origin']}; from all local refs: {res['unreachable_from_all_local_refs']}")
for r in res["unreachable_rows"][:20]:
    print("  ", r)
