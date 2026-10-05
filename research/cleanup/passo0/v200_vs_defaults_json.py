#!/usr/bin/env python
"""Passo 0 — does `research/labels/defaults_2.0.0.json` describe the PUBLISHED 2.0.0?

    python research/cleanup/passo0/v200_vs_defaults_json.py

Read-only, static: parses `cyclophaser/determine_periods.py` at the `v2.0.0` tag
with `ast` (nothing is imported or run from the tag) and compares the signature
defaults of `process_vorticity` and `get_periods` there with the table in
`research/labels/defaults_2.0.0.json` (HEAD). Writes
research/cleanup/passo0/v200_vs_defaults_json.json and prints the differences.
"""
import ast
import json
import subprocess
from pathlib import Path

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
TAG = "v2.0.0"


def sig_defaults(src, fname):
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == fname:
            a = node.args
            pos = a.args[len(a.args) - len(a.defaults):]
            out = {p.arg: ast.literal_eval(d) for p, d in zip(pos, a.defaults)}
            out.update({p.arg: ast.literal_eval(d) for p, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None})
            return out
    raise KeyError(fname)


src = subprocess.check_output(["git", "show", f"{TAG}:cyclophaser/determine_periods.py"], cwd=ROOT, text=True)
tag_commit = subprocess.check_output(["git", "rev-list", "-n", "1", TAG], cwd=ROOT, text=True).strip()
pv = sig_defaults(src, "process_vorticity")
gp = sig_defaults(src, "get_periods")
table = json.loads((ROOT / "research/labels/defaults_2.0.0.json").read_text())

rows = []
for group, sig in (("filter_params", pv), ("phase_params", gp)):
    for k, v in table[group].items():
        if k not in sig:
            rows.append(dict(group=group, param=k, json=v, tag="(parâmetro não existe na tag)"))
        elif sig[k] != v:
            rows.append(dict(group=group, param=k, json=v, tag=sig[k]))
same = sum(1 for g, s in (("filter_params", pv), ("phase_params", gp)) for k, v in table[g].items() if k in s and s[k] == v)
out = dict(tag=TAG, tag_commit=tag_commit, n_keys=sum(len(table[g]) for g in ("filter_params", "phase_params")),
           n_equal=same, differences=rows, json_source=table.get("source"))
(ROOT / "research/cleanup/passo0/v200_vs_defaults_json.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
print(f"{TAG} ({tag_commit[:7]}): {same} of {out['n_keys']} keys equal; {len(rows)} differ")
for r in rows:
    print(f"  {r['group']:14s} {r['param']:42s} json={r['json']!r:14s} tag={r['tag']!r}")
