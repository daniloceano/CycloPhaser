#!/usr/bin/env python
"""Passo 6a — the nominal list proposed for removal in 6b, from branches.json and
tags.json (nothing deleted here). Writes removal_list.md next to it.

    python research/cleanup/passo6/removal_list.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
d = json.loads((HERE / "branches.json").read_text())
tags = {t["branch"]: t["tag"] for t in json.loads((HERE / "tags.json").read_text())}
out = ["# Branches proposed for removal in 6b — for Danilo's nominal authorisation (generated)\n",
       "Nothing is deleted before an explicit, per-branch authorisation.\n"]
for section, title in (("remote", "Remote (`git push origin --delete <name>`)"),
                       ("local_only", "Local only (`git branch -D <name>`)")):
    rows = d[section]
    for dest, label in (("A", "A — delete (contained in develop-v2.1, nothing cited outside it)"),
                        ("B", "B — delete after the archive tag (tag already created and pushed)")):
        sel = [r for r in rows if r["destination"] == dest]
        if not sel:
            continue
        out += [f"## {title} — {label}: {len(sel)}\n"]
        out += [f"- `{r['branch']}`" + (f" → kept as `{tags[r['branch']]}`" if dest == "B" else "") for r in sel]
        out.append("")
(HERE / "removal_list.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
