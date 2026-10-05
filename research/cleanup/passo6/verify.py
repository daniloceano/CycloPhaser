#!/usr/bin/env python
"""Passo 6a, step 3 — checks after tagging (read-only).

    git fetch --prune --tags origin
    python research/cleanup/passo6/verify.py      # writes verify.json next to it

1. Every tag of tags.json points, locally AND on origin, to the tip recorded for
   its branch in branches.json (and still equal to the branch's current tip).
2. Simulated removal of every (A) and (B) branch: the refs kept are origin/master,
   origin/develop-v2.1, origin/chore/repo-cleanup and every tag. Every commit
   cited in a tracked file (a 7-40 hex token, not inside a longer hex run, that
   resolves to a commit of this repository) must be reachable from them.
   For comparison, reachability from ALL refs today is measured too.
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEX = re.compile(r"(?<![0-9a-fA-F])([0-9a-f]{7,40})(?![0-9a-fA-F])")


def git(*a, inp=None):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, input=inp).stdout


tags = json.loads((HERE / "tags.json").read_text())
br = json.loads((HERE / "branches.json").read_text())
remote_tags = {}
for line in git("ls-remote", "--tags", "origin", "archive/*").splitlines():
    h, ref = line.split("\t")
    if ref.endswith("^{}"):
        remote_tags[ref[len("refs/tags/"):-3]] = h
tag_rows = []
for t in tags:
    local = git("rev-parse", f"{t['tag']}^{{commit}}").strip()
    ref = f"origin/{t['branch']}" if t["section"] == "remote" else t["branch"]
    current_tip = git("rev-parse", ref).strip()
    ok = local == t["tip"] == remote_tags.get(t["tag"]) == current_tip
    tag_rows.append(dict(tag=t["tag"], tip=t["tip"][:7], local=local[:7], remote=remote_tags.get(t["tag"], "")[:7],
                         branch_tip_now=current_tip[:7], ok=ok))

# cited commits
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
kept_refs = ["origin/master", "origin/develop-v2.1", "origin/chore/repo-cleanup"] + \
            git("for-each-ref", "--format=%(refname)", "refs/tags").split()
kept = set(git("rev-list", *kept_refs).split())
everything = set(git("rev-list", "--all").split())
unreach_after = {t: c for t, c in commits.items() if c not in kept}
unreach_now = {t: c for t, c in commits.items() if c not in everything}
res = dict(tags=tag_rows, tags_ok=all(r["ok"] for r in tag_rows),
           hex_tokens=len(tokens), tokens_resolving_to_commits=len(commits),
           distinct_cited_commits=len(set(commits.values())),
           unreachable_after_simulated_removal=len(set(unreach_after.values())),
           unreachable_after_rows=[dict(token=t, commit=c[:10], first_citation=tokens[t]) for t, c in unreach_after.items()],
           unreachable_from_all_refs_today=len(set(unreach_now.values())),
           kept_refs=kept_refs)
(HERE / "verify.json").write_text(json.dumps(res, indent=1))
print(f"tags: {sum(r['ok'] for r in tag_rows)}/{len(tag_rows)} point to their branch tip (local and origin)")
print(f"cited commits: {res['distinct_cited_commits']} distinct (from {res['tokens_resolving_to_commits']} tokens); "
      f"unreachable after the simulated removal: {res['unreachable_after_simulated_removal']}; "
      f"unreachable from all refs today: {res['unreachable_from_all_refs_today']}")
for r in res["unreachable_after_rows"][:20]:
    print("  ", r)
