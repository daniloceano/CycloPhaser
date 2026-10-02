#!/usr/bin/env python
"""Passo 6a, step 2 — annotated tags archive/<name> at the tip of every (B) branch of
branches.json. The message names one citation (the first outside research/cleanup/,
else the first). Refuses to move an existing tag. Writes tags.json next to it.

    python research/cleanup/passo6/make_tags.py
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
d = json.loads((HERE / "branches.json").read_text())
out = []
for section in ("remote", "local_only"):
    for r in d[section]:
        if r["destination"] != "B":
            continue
        name, tip = r["branch"], r["tip"]
        where = [w for ws in r["cited_outside"].values() for w in ws]
        cite = next((w for w in where if not w.startswith("research/cleanup/")), where[0] if where else None)
        tag = f"archive/{name}"
        msg = f"Archived branch {name} before the v2.1 clean-up; cited in {cite} or kept as a record."
        exists = subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], cwd=ROOT,
                                capture_output=True, text=True)
        if exists.returncode == 0:
            target = subprocess.check_output(["git", "rev-parse", f"{tag}^{{commit}}"], cwd=ROOT, text=True).strip()
            assert target == tip, f"{tag} exists and points elsewhere"
        else:
            subprocess.check_call(["git", "tag", "-a", tag, tip, "-m", msg], cwd=ROOT)
        out.append(dict(tag=tag, branch=name, section=section, tip=tip, message=msg))
(HERE / "tags.json").write_text(json.dumps(out, indent=1))
for t in out:
    print(f"{t['tag']:48} -> {t['tip'][:7]}  ({t['section']})")
