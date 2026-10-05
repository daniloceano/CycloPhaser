#!/usr/bin/env python
"""Passo 4 — what research/snapshots/v2.0.0.json is, checked against the v2.0.0 tag.

    python research/cleanup/passo4/snapshot_vs_tag.py

Static and read-only. Reads the snapshot's own header (label, version,
generator, parameters) and its recorded `public_signature`, parses
`cyclophaser/determine_periods.py` at tag v2.0.0 with `ast` (nothing imported
or run), and compares every recorded default with the tag's, per function.
Also compares the file's sha256 with research/snapshots/SHA256SUMS. Writes
snapshot_vs_tag.json next to it.
"""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SNAP = ROOT / "research/snapshots/v2.0.0.json"
TAG = "v2.0.0"

doc = json.loads(SNAP.read_text())
head = doc["snapshot"]
src = subprocess.check_output(["git", "show", f"{TAG}:cyclophaser/determine_periods.py"], cwd=ROOT, text=True)
tree = ast.parse(src)


def tag_sig(name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            a = n.args
            pos = a.args[len(a.args) - len(a.defaults):]
            out = {p.arg: ast.get_source_segment(src, d) for p, d in zip(pos, a.defaults)}
            out.update({p.arg: ast.get_source_segment(src, d) for p, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None})
            return out
    return None


def norm(v):
    try:
        return repr(ast.literal_eval(v))
    except (ValueError, SyntaxError):
        return v


cmp = {}
for fn, rec in head["public_signature"].items():
    t = tag_sig(fn)
    if t is None:
        cmp[fn] = dict(in_tag=False)
        continue
    rec_d = {k: v for k, v in rec.items() if v is not None}
    keys = sorted(set(rec_d) | set(t))
    diffs = {k: dict(snapshot=rec_d.get(k), tag=t.get(k)) for k in keys
             if norm(str(rec_d.get(k))) != norm(str(t.get(k)))}
    cmp[fn] = dict(in_tag=True, params_with_default=len(keys), differing=diffs)
sha = hashlib.sha256(SNAP.read_bytes()).hexdigest()
sums = (ROOT / "research/snapshots/SHA256SUMS").read_text()
out = dict(file="research/snapshots/v2.0.0.json", label=head.get("label"), version=head.get("cyclophaser_version"),
           generator=head.get("generator"), parameters=head.get("parameters"),
           n_series=len(doc["records"]), counts=doc.get("counts"),
           tag=TAG, tag_commit=subprocess.check_output(["git", "rev-list", "-n", "1", TAG], cwd=ROOT, text=True).strip()[:7],
           signature_vs_tag=cmp, sha256=sha, sha256_in_SHA256SUMS=sha in sums)
Path(__file__).with_name("snapshot_vs_tag.json").write_text(json.dumps(out, indent=1))
print(f"{out['label']} — version {out['version']}, generator {out['generator']}")
print(f"parameters: {out['parameters']}; series: {out['n_series']}")
for fn, c in cmp.items():
    print(f"  {fn}: in tag {c['in_tag']}; params with default {c.get('params_with_default')}; differing {len(c.get('differing', {}))}")
print(f"sha256 listed in SHA256SUMS: {out['sha256_in_SHA256SUMS']}")
