#!/usr/bin/env python
"""Passo 6b — delete exactly the branches Danilo authorised by name (02/10/2026):
the 38 remote and 4 local-only branches of removal_list.md **as committed in
fbeff00**. The list, the tips and the tags are read from that commit, never from
the working tree, so a later edit of those files cannot widen the deletion.

    git fetch --prune --tags origin
    python research/cleanup/passo6/delete_6b.py --check    # writes delete_6b_check.json
    python research/cleanup/passo6/delete_6b.py --delete   # check again, then delete; writes delete_6b.json

Per branch, before deleting:
  * the current tip (on origin for remote rows, refs/heads for local rows) equals
    the full tip recorded in branches.json;
  * group B: the tag archive/<name> exists locally AND on origin, and peels to
    that same tip.
A branch failing any check is NOT deleted and is reported. A remote deletion is
sent with --force-with-lease=<ref>:<recorded tip>, so it is refused by git if the
tip moved between the check and the push.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTH = "fbeff00"
REL = "research/cleanup/passo6"


def git(*a, check=False):
    p = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    if check and p.returncode:
        raise SystemExit(f"git {' '.join(a)} failed: {p.stderr}")
    return p


def at_auth(name):
    return git("show", f"{AUTH}:{REL}/{name}", check=True).stdout


# --- the authorised list, from the committed removal_list.md ---
listing = at_auth("removal_list.md")
rows, section, group = [], None, None
for line in listing.splitlines():
    if line.startswith("## "):
        section = "remote" if line.startswith("## Remote") else "local_only"
        group = re.search(r"— ([AB]) —", line).group(1)
    m = re.match(r"- `([^`]+)`", line)
    if m:
        rows.append(dict(branch=m.group(1), section=section, group=group))
br = json.loads(at_auth("branches.json"))
tips = {(s, r["branch"]): r for s in ("remote", "local_only") for r in br[s]}
tags = {t["branch"]: t for t in json.loads(at_auth("tags.json"))}

remote_heads, remote_tags = {}, {}
for line in git("ls-remote", "origin", check=True).stdout.splitlines():
    h, ref = line.split("\t")
    if ref.startswith("refs/heads/"):
        remote_heads[ref[len("refs/heads/"):]] = h
    elif ref.startswith("refs/tags/") and ref.endswith("^{}"):
        remote_tags[ref[len("refs/tags/"):-3]] = h


def check_rows():
    out = []
    for r in rows:
        rec = tips.get((r["section"], r["branch"]))
        res = dict(r, recorded_tip=rec and rec["tip"], recorded_destination=rec and rec["destination"])
        problems = []
        if rec is None:
            problems.append("not in branches.json")
        elif rec["destination"] != r["group"]:
            problems.append(f"destination {rec['destination']} != list group {r['group']}")
        if r["section"] == "remote":
            now = remote_heads.get(r["branch"])
        else:
            p = git("rev-parse", "--verify", "--quiet", f"refs/heads/{r['branch']}")
            now = p.stdout.strip() or None
        res["current_tip"] = now
        if rec and now != rec["tip"]:
            problems.append(f"tip now {now} != recorded {rec['tip']}")
        if r["group"] == "B":
            t = tags.get(r["branch"])
            if t is None:
                problems.append("no tag in tags.json")
            else:
                loc = git("rev-parse", "--verify", "--quiet", f"refs/tags/{t['tag']}^{{commit}}").stdout.strip() or None
                rem = remote_tags.get(t["tag"])
                res.update(tag=t["tag"], tag_local=loc, tag_origin=rem)
                if not (rec and loc == rem == t["tip"] == rec["tip"]):
                    problems.append(f"tag {t['tag']}: local {loc} origin {rem} tags.json {t['tip']}")
        res["problems"] = problems
        res["ok"] = not problems
        out.append(res)
    return out


checked = check_rows()
n = {s: sum(r["section"] == s for r in checked) for s in ("remote", "local_only")}
summary = dict(authorised_list=f"{AUTH}:{REL}/removal_list.md", counts=n,
               ok=sum(r["ok"] for r in checked), failing=[r for r in checked if not r["ok"]])
print(f"authorised: {n['remote']} remote + {n['local_only']} local; checks OK {summary['ok']}/{len(checked)}")
for r in summary["failing"]:
    print("  NOT OK:", r["branch"], r["problems"])

if sys.argv[1:] == ["--check"]:
    (HERE / "delete_6b_check.json").write_text(json.dumps(dict(summary, rows=checked), indent=1) + "\n")
    sys.exit(0)
if sys.argv[1:] != ["--delete"]:
    raise SystemExit("usage: delete_6b.py --check | --delete")
assert n == {"remote": 38, "local_only": 4}, n

log = []
for r in checked:
    if not r["ok"]:
        log.append(dict(branch=r["branch"], section=r["section"], deleted=False, reason="; ".join(r["problems"])))
        continue
    if r["section"] == "remote":
        ref = f"refs/heads/{r['branch']}"
        p = git("push", f"--force-with-lease={ref}:{r['recorded_tip']}", "origin", f":{ref}")
    else:
        p = git("branch", "-D", r["branch"])
    log.append(dict(branch=r["branch"], section=r["section"], group=r["group"], tip=r["recorded_tip"],
                    deleted=p.returncode == 0, output=(p.stdout + p.stderr).strip()))
    print(("deleted " if p.returncode == 0 else "FAILED  ") + f"{r['section']:10s} {r['branch']}")
(HERE / "delete_6b.json").write_text(json.dumps(dict(summary, log=log), indent=1) + "\n")
print(f"deleted: remote {sum(l['deleted'] for l in log if l['section'] == 'remote')}, "
      f"local {sum(l['deleted'] for l in log if l['section'] == 'local_only')}; "
      f"not deleted: {[l['branch'] for l in log if not l['deleted']]}")
