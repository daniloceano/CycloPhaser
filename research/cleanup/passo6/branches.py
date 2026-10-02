#!/usr/bin/env python
"""Passo 6a — the branch table: one row per branch, regenerated from the refs (read-only).

    git fetch --prune origin
    python research/cleanup/passo6/branches.py      # writes branches.json and branches.md next to it

Remote branches come from refs/remotes/origin/*; branches that exist only locally
(refs/heads/* with no origin counterpart) are listed in a separate section.

Per branch:
* tip: hash, date, subject;
* contained in origin/develop-v2.1 (`git merge-base --is-ancestor`), or only
  patch-equivalent (every commit outside develop has an equivalent there, `git
  cherry`), or neither;
* commits outside develop (`git rev-list origin/develop-v2.1..<branch>`): count,
  and which of them are CITED in a tracked file of this working tree (any hex
  token of 7-40 characters that is a prefix of the commit hash), with file:line;
* proposed destination:
    (C) keep            master, develop-v2.1, chore/repo-cleanup;
    (B) tag + delete    a commit outside develop is cited, or the branch is a
                        record by a Passo 0 decision ("tag de arquivo" in
                        research/cleanup/MANIFEST.md, section 0.3);
    (A) delete          contained in develop, or only patch-equivalent, and no
                        commit outside develop cited;
    decide with Danilo  anything else, with the reason.
"""
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEVELOP = "origin/develop-v2.1"
KEEP = {"master", "develop-v2.1", "chore/repo-cleanup"}


def git(*a, check=True):
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(r.stderr)
    return r.stdout.strip()


def passo0_records():
    """Branches whose Passo 0 destination is 'tag de arquivo' (MANIFEST section 0.3)."""
    text = (ROOT / "research/cleanup/MANIFEST.md").read_text()
    sec = text[text.index("## 0.3 Manifesto de branches"):text.index("## 0.4 ")]
    out = {}
    for line in sec.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 9 and cells[1].startswith("`"):
            name = cells[1].strip("`")
            if "tag de arquivo" in cells[9]:
                out[name] = cells[9].replace("*", "")
    return out


HEX = re.compile(r"(?<![0-9a-fA-F])([0-9a-f]{7,40})(?![0-9a-fA-F])")


def citation_index():
    """{first 7 hex chars: [(token, 'file:line'), ...]} over every tracked text file of
    the working tree. A token is 7-40 lowercase hex characters not inside a longer
    hex run (so a sha256 is not read as a commit citation)."""
    idx = defaultdict(list)
    for f in git("ls-files").splitlines():
        p = ROOT / f
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if b"\x00" in data[:4096]:
            continue
        for n, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            for m in HEX.finditer(line):
                idx[m.group(1)[:7]].append((m.group(1), f"{f}:{n}"))
    return idx


def cited(h, idx):
    return sorted({where for tok, where in idx.get(h[:7], []) if h.startswith(tok)})


def row(ref, name, idx, records):
    tip = git("log", "-1", "--format=%H%x09%cs%x09%s", ref).split("\t")
    contained = subprocess.run(["git", "merge-base", "--is-ancestor", ref, DEVELOP], cwd=ROOT).returncode == 0
    outside = git("rev-list", f"{DEVELOP}..{ref}").split()
    cherry = git("cherry", DEVELOP, ref).splitlines()
    not_equiv = [l[2:] for l in cherry if l.startswith("+ ")]
    cit = {h: cited(h, idx) for h in outside}
    cit = {h: w for h, w in cit.items() if w}
    patch_equiv_only = bool(outside) and not not_equiv
    if name in KEEP:
        dest, why = "C", "keep (fixed list)"
    elif cit:
        dest, why = "B", f"{len(cit)} commit(s) outside develop cited"
    elif name in records:
        dest, why = "B", f"record by the Passo 0 decision ({records[name]})"
    elif contained or patch_equiv_only:
        dest, why = "A", "contained in develop" if contained else "only patch-equivalent to develop"
    else:
        dest, why = "decide", (f"{len(not_equiv)} commit(s) outside develop with no equivalent there, none cited, "
                               "not a Passo 0 record")
    return dict(branch=name, tip=tip[0], tip_date=tip[1], tip_subject=tip[2], contained=contained,
                patch_equivalent_only=patch_equiv_only, outside=len(outside), outside_not_equivalent=len(not_equiv),
                cited_outside={h[:7]: w for h, w in cit.items()}, destination=dest, reason=why,
                passo0=records.get(name))


def main():
    idx = citation_index()
    records = passo0_records()
    remote = [r for r in git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").split()
              if r not in ("origin", "origin/HEAD")]
    rows = [row(r, r[len("origin/"):], idx, records) for r in sorted(remote)]
    remote_names = {r["branch"] for r in rows}
    local_only = [b for b in git("for-each-ref", "--format=%(refname:short)", "refs/heads").split()
                  if b not in remote_names]
    lrows = [row(b, b, idx, records) for b in sorted(local_only)]
    res = dict(develop=git("rev-parse", "--short", DEVELOP), remote=rows, local_only=lrows,
               passo0_records=sorted(records))
    (HERE / "branches.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))

    def table(rs):
        t = ["| branch | tip | contained / patch-equiv. | outside develop (not equiv.) | cited (outside develop) | "
             "destination | reason |", "|---|---|---|---|---|---|---|"]
        for r in rs:
            c = "; ".join(f"`{h}` → " + ", ".join(f"`{w}`" for w in ws[:3]) + (f" (+{len(ws) - 3})" if len(ws) > 3 else "")
                          for h, ws in r["cited_outside"].items()) or "—"
            cont = "contained" if r["contained"] else ("patch-equiv." if r["patch_equivalent_only"] else "no")
            subj = r["tip_subject"].replace("|", "\\|")[:60]
            t.append(f"| `{r['branch']}` | `{r['tip'][:7]}` {r['tip_date']} {subj} | {cont} | "
                     f"{r['outside']} ({r['outside_not_equivalent']}) | {c} | **{r['destination']}** | {r['reason']} |")
        return t

    def counts(rs):
        k = defaultdict(int)
        for r in rs:
            k[r["destination"]] += 1
        return dict(sorted(k.items()))

    md = ["# Branches — table (generated by branches.py; nothing deleted)\n",
          f"Reference: `{DEVELOP}` at `{res['develop']}`. Remote branches: **{len(rows)}**, by destination "
          f"{counts(rows)}. Local-only branches: **{len(lrows)}**, by destination {counts(lrows)}.\n",
          "Destinations: **A** delete; **B** annotated tag `archive/<name>` at the tip, then delete; **C** keep; "
          "**decide** with Danilo. Citations are hex tokens of 7-40 characters in tracked files of the "
          "working tree that are a prefix of the commit.\n",
          "## Remote\n"] + table(rows) + ["", "## Local only\n"] + table(lrows)
    (HERE / "branches.md").write_text("\n".join(md) + "\n")
    print(md[1])
    for r in rows + lrows:
        print(f"  {r['destination']:7} {r['branch']:45} out={r['outside']:3} cited={len(r['cited_outside'])} {r['reason']}")


if __name__ == "__main__":
    main()
