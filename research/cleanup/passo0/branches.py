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
        behind, ahead = git("rev-list", "--left-right", "--count", f"{DEV}...{b}").split()
        mb = git("merge-base", DEV, b).strip()
        changed = git("diff", "--name-only", mb, b).split()
        top = sorted({"/".join(p.split("/")[:3]) for p in changed})
        mentions = []
        for line in git("grep", "-n", "-F", "-e", name, "HEAD", "--", ".",
                        ":(exclude)research/cleanup/", ":(exclude).pypirc").splitlines():
            _, path, ln, _ = line.split(":", 3)
            mentions.append(f"{path}:{ln}")
        rows.append(dict(branch=name, tip=h, date=d, subject=subj, in_develop=merged,
                         ahead=int(ahead), behind=int(behind), merge_base=mb[:7],
                         n_files_changed=len(changed), dirs_changed=top[:12],
                         mentions=mentions))
    local = git("for-each-ref", "--format=%(refname:short)", "refs/heads").split()
    local_only = [b for b in local if f"origin/{b}" not in remotes]
    out = dict(develop_tip=git("rev-parse", "--short", DEV).strip(), n_remote=len(rows),
               remote=rows, local_without_remote=local_only)
    (ROOT / "research/cleanup/passo0/branches.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for r in rows:
        print(f"{r['branch']:50s} {r['tip']} {r['date']} merged={r['in_develop']!s:5s} "
              f"+{r['ahead']}/-{r['behind']} files={r['n_files_changed']} mentions={len(r['mentions'])}")
    print("local without remote:", local_only)


if __name__ == "__main__":
    main()
