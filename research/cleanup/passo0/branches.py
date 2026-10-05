#!/usr/bin/env python
"""Passo 0.3 — remote-branch inventory (read-only: nothing is deleted or moved).

    python research/cleanup/passo0/branches.py

For every `origin/*` branch: tip (hash, date, subject), whether it is already
contained in origin/develop-v2.1 (`git merge-base --is-ancestor`), commits
ahead/behind develop-v2.1, the files it changes relative to their merge base
(to summarise its content), and every committed mention of the branch name in
the tree at HEAD (`git grep -n -F`, research/cleanup/ excluded).
Also lists local branches that have no remote counterpart.
Writes research/cleanup/passo0/branches.json.

Passo 1 correction: `in_develop` (ancestry) is kept, and a second, separate
fact is recorded — `patch_equivalent`: the branch is NOT an ancestor of develop
but every commit it has beyond the merge base has a patch-equivalent commit in
develop (`git cherry develop <branch>` prints only '-' lines). A
patch-equivalent branch is not contained in develop: its own hashes stop
resolving if the ref is deleted, so it is never lumped with the ancestors.
Run `git fetch origin` first; this script reads remote-tracking refs as they are.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
DEV = "origin/develop-v2.1"


def git(*a, check=False):
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    return r if check else r.stdout


def main():
    remotes = [b for b in git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").split()
               if b not in ("origin/HEAD", "origin")]
    rows = []
    for b in remotes:
        name = b[len("origin/"):]
        h, d, subj = git("log", "-1", "--format=%h%x09%cs%x09%s", b).strip().split("\t", 2)
        merged = git("merge-base", "--is-ancestor", b, DEV, check=True).returncode == 0
        cherry = [l[:1] for l in git("cherry", DEV, b).splitlines() if l.strip()]
        patch_eq = (not merged) and bool(cherry) and all(c == "-" for c in cherry)
        behind, ahead = git("rev-list", "--left-right", "--count", f"{DEV}...{b}").split()
        mb = git("merge-base", DEV, b).strip()
        changed = git("diff", "--name-only", mb, b).split()
        top = sorted({"/".join(p.split("/")[:3]) for p in changed})
        mentions = []
        for line in git("grep", "-n", "-F", "-e", name, "HEAD", "--", ".",
                        ":(exclude)research/cleanup/").splitlines():
            _, path, ln, _ = line.split(":", 3)
            mentions.append(f"{path}:{ln}")
        # Citations of the branch's OWN commits (those not in develop) by short
        # hash: a record can cite a commit without naming its branch.
        hash_mentions = []
        if not merged:
            for c in git("rev-list", f"{DEV}..{b}").split():
                for line in git("grep", "-n", "-F", "-e", c[:7], "HEAD", "--", ".",
                                ":(exclude)research/cleanup/").splitlines():
                    _, path, ln, _ = line.split(":", 3)
                    hash_mentions.append(f"{path}:{ln} ({c[:7]})")
        rows.append(dict(branch=name, hash_mentions=hash_mentions, tip=h, date=d, subject=subj, in_develop=merged,
                         patch_equivalent=patch_eq, cherry_minus=cherry.count("-"),
                         cherry_plus=cherry.count("+"),
                         ahead=int(ahead), behind=int(behind), merge_base=mb[:7],
                         n_files_changed=len(changed), dirs_changed=top[:12],
                         mentions=mentions))
    local = git("for-each-ref", "--format=%(refname:short)", "refs/heads").split()
    local_only = [b for b in local if f"origin/{b}" not in remotes]
    out = dict(develop_tip=git("rev-parse", "--short", DEV).strip(), n_remote=len(rows),
               remote=rows, local_without_remote=local_only)
    (ROOT / "research/cleanup/passo0/branches.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for r in rows:
        print(f"{r['branch']:50s} {r['tip']} {r['date']} merged={r['in_develop']!s:5s} patch_eq={r['patch_equivalent']!s:5s} "
              f"+{r['ahead']}/-{r['behind']} files={r['n_files_changed']} mentions={len(r['mentions'])} "
              f"hash_mentions={len(r['hash_mentions'])}")
    print("local without remote:", local_only)


if __name__ == "__main__":
    main()
