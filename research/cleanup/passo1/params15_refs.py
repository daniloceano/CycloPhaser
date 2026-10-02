#!/usr/bin/env python
"""Passo 1 — "params-15" references after the rename: live must be 0, history intact.

    python research/cleanup/passo1/params15_refs.py [BEFORE_REF]

Same grep and the same VIVA/HISTÓRICA rule as the Passo 0 manifest (section
(c): `git grep -P 'params[-_]?15(?![0-9])'`, research/cleanup/ excluded; the
class table is `passo0/judgements.P15_CLASS`, imported). One more class is
needed after the rename: a line that names params-15 TOGETHER with params-track
— on the line itself or on an adjacent line of the same file, since wrapped
prose splits a sentence — is a correspondence note (the dated note, "renamed
params-track", "then named params-15"), not a stale reference.

History intact = for every HISTÓRICA file, the multiset of its params-15 lines
(text only; correspondence lines set apart) at BEFORE_REF (default d8a19cc, the
commit before the rename) equals the one at HEAD. Writes params15_refs.json.
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/cleanup/passo0"))
from judgements import P15_CLASS  # noqa: E402

BEFORE = sys.argv[1] if len(sys.argv) > 1 else "d8a19cc"
PAT = r"params[-_]?15(?![0-9])"
CORR = re.compile(r"params[-_]track", re.I)


_FILES = {}


def near_track(ref, f, ln):
    """params-track on line ln or an adjacent line of f at ref."""
    if (ref, f) not in _FILES:
        _FILES[(ref, f)] = subprocess.run(["git", "show", f"{ref}:{f}"], cwd=ROOT, capture_output=True,
                                          text=True).stdout.splitlines()
    lines = _FILES[(ref, f)]
    return any(CORR.search(lines[i]) for i in range(max(0, ln - 2), min(len(lines), ln + 1)))


def grep(ref):
    out = subprocess.run(["git", "grep", "-n", "-I", "-P", "-e", PAT, ref, "--", ".",
                          ":(exclude)research/cleanup/"], cwd=ROOT, capture_output=True, text=True).stdout
    hits = []
    for line in out.splitlines():
        _, rest = line.split(":", 1)
        f, ln, text = rest.split(":", 2)
        hits.append((f, int(ln), text, near_track(ref, f, int(ln))))
    return hits


def cls(f):
    for pref, c, _ in P15_CLASS:
        if f.startswith(pref):
            return c.rstrip("*")
    return "?"


def main():
    head = grep("HEAD")
    before = grep(BEFORE)
    rows = []
    for f, ln, text, corr in head:
        c = "CORRESPONDÊNCIA" if corr else cls(f)
        rows.append(dict(file=f, line=ln, cls=c, text=text.strip()[:160]))
    counts = Counter(r["cls"] for r in rows)
    live = [r for r in rows if r["cls"] == "VIVA"]

    def hist_lines(hits):
        return Counter((f, t.strip()) for f, _, t, corr in hits if cls(f) == "HISTÓRICA" and not corr)
    hb, hh = hist_lines(before), hist_lines(head)
    out = dict(before_ref=BEFORE, n_head=len(rows), counts=dict(counts),
               live_remaining=live, hist_before=sum(hb.values()), hist_head=sum(hh.values()),
               hist_identical=hb == hh,
               hist_only_before=[list(k) for k in (hb - hh)], hist_only_head=[list(k) for k in (hh - hb)],
               correspondence=[r for r in rows if r["cls"] == "CORRESPONDÊNCIA"],
               before_counts=dict(Counter(cls(f) for f, _, _, _ in before)))
    Path(__file__).with_name("params15_refs.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"HEAD: {len(rows)} hits — " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"live remaining: {len(live)}")
    print(f"historical: {out['hist_before']} at {BEFORE} -> {out['hist_head']} at HEAD; identical={out['hist_identical']}")
    for r in out["correspondence"]:
        print(f"  correspondence {r['file']}:{r['line']}")


if __name__ == "__main__":
    main()
