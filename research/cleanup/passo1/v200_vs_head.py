#!/usr/bin/env python
"""Passo 1 — signature defaults of the REAL v2.0.0 tag against this working tree.

    python research/cleanup/passo1/v200_vs_head.py

Static, read-only: parses `cyclophaser/determine_periods.py` at tag `v2.0.0`
(`git show`) and in the working tree with `ast` — nothing is imported or run —
and compares the signature defaults of `process_vorticity`, `get_periods` and
`determine_periods`. `sig_defaults` is the same parser as
passo0/v200_vs_defaults_json.py (that module writes on import, so it is not
imported). Asserts that `determine_periods` carries, for every detection
parameter, the same default as `process_vorticity`/`get_periods` at each end,
so one table per group is the whole story. Writes v200_vs_head.json and prints
the CHANGELOG table rows (markdown), which the CHANGELOG entry reproduces.
"""
import ast
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TAG = "v2.0.0"
SRC = "cyclophaser/determine_periods.py"
NON_DETECTION = {"series", "x", "plot", "plot_steps", "export_dict", "hemisphere"}


def sig_defaults(src, fname):
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == fname:
            a = node.args
            pos = a.args[len(a.args) - len(a.defaults):]
            out = {p.arg: ast.literal_eval(d) for p, d in zip(pos, a.defaults)}
            out.update({p.arg: ast.literal_eval(d) for p, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None})
            return out
    raise KeyError(fname)


def fmt(v):
    return "—" if v is ABSENT else f"`{v!r}`".replace("'", '"') if isinstance(v, str) else f"`{v!r}`"


ABSENT = object()
tag_src = subprocess.check_output(["git", "show", f"{TAG}:{SRC}"], cwd=ROOT, text=True)
tag_commit = subprocess.check_output(["git", "rev-list", "-n", "1", TAG], cwd=ROOT, text=True).strip()
head_src = (ROOT / SRC).read_text()

ends = {}
for name, src in (("tag", tag_src), ("head", head_src)):
    pv, gp, dpf = (sig_defaults(src, f) for f in ("process_vorticity", "get_periods", "determine_periods"))
    for k, v in dpf.items():
        if k in NON_DETECTION:
            continue
        ref = pv.get(k, gp.get(k, ABSENT))
        assert ref is not ABSENT and ref == v, f"{name}: determine_periods.{k}={v!r} vs {ref!r}"
    ends[name] = dict(filter=pv, phase=gp)

rows = {}
for group in ("filter", "phase"):
    keys = list(ends["head"][group]) + [k for k in ends["tag"][group] if k not in ends["head"][group]]
    rows[group] = []
    for k in keys:
        if k in ("zeta_df", "vorticity") or k in NON_DETECTION:
            continue
        t, h = ends["tag"][group].get(k, ABSENT), ends["head"][group].get(k, ABSENT)
        rows[group].append(dict(param=k, tag=None if t is ABSENT else t, head=None if h is ABSENT else h,
                                in_tag=t is not ABSENT, in_head=h is not ABSENT,
                                changed=(t is ABSENT) or (h is ABSENT) or t != h,
                                tag_fmt=fmt(t), head_fmt=fmt(h)))

out = dict(tag=TAG, tag_commit=tag_commit, rows=rows)
(Path(__file__).with_name("v200_vs_head.json")).write_text(json.dumps(out, indent=1, default=str))
for group, title in (("filter", "process_vorticity"), ("phase", "get_periods")):
    ch = [r for r in rows[group] if r["changed"]]
    same = [r for r in rows[group] if not r["changed"]]
    print(f"\n{title}: {len(ch)} changed or new, {len(same)} unchanged")
    print("| parameter | 2.0.0 (tag) | now |\n|---|---|---|")
    for r in ch:
        print(f"| `{r['param']}` | {r['tag_fmt']} | {r['head_fmt']} |")
    if same:
        print("| " + ", ".join(f"`{r['param']}`" for r in same) + " | unchanged ("
              + ", ".join(r["tag_fmt"] for r in same) + ") | unchanged |")
