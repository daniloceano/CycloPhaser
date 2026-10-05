#!/usr/bin/env python
"""Decisão 1 — the TRAIN re-labels stranded on `feat/label-tab-toplevel`.

    python research/cleanup/passo0/relabel_diff.py

Read-only. Compares `research/labels/manual_labels.yaml` at the tip of
`origin/develop-v2.1` with the same file at the tip of
`origin/feat/label-tab-toplevel` (both read with `git show`, nothing checked
out), restricted to the TRAIN ids of `research/labels/split.yaml` (top-level
`train:` plus every `batches.*.train`). TEST entries are dropped before any
comparison, so no test label is compared or printed; no series is loaded.

Per train id present at both tips it reports, field by field, what differs in
the CONTENT of the label (CONTENT below: phase list, verdict, tolerance_idx,
n_steps, series_sha256). Every other differing key is bookkeeping or schema
(`labeled_at`, `overlays_shown`, the `superseded` history the branch's writer
keeps, `open_/close_unsure` absent on one side) and is only listed by name; an
id whose differences are all of that kind is a re-save without a change of
label. Ids present at one tip only are counted apart. Writes relabel_diff.json
next to it.
"""
import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
DEV = "origin/develop-v2.1"
BRANCH = "origin/feat/label-tab-toplevel"
LABELS = "research/labels/manual_labels.yaml"
CONTENT = {"phases", "verdict", "tolerance_idx", "n_steps", "series_sha256"}


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT, text=True)


def train_ids():
    doc = yaml.safe_load((ROOT / "research/labels/split.yaml").read_text())
    ids = set(doc["train"])
    for blk in (doc.get("batches") or {}).values():
        ids |= set(blk.get("train", []))
    return ids


def labels_at(ref, keep):
    doc = yaml.safe_load(git("show", f"{ref}:{LABELS}"))
    return {str(l["id"]): l for l in doc["labels"] if str(l["id"]) in keep}


def phase_changes(a, b):
    """Phase-by-phase differences, matched by phase name + ordinal."""
    def keyed(phases):
        seen, out = {}, {}
        for p in phases or []:
            n = seen.get(p["phase"], 0)
            seen[p["phase"]] = n + 1
            out[f"{p['phase']}#{n}"] = p
        return out
    ka, kb = keyed(a), keyed(b)
    out = []
    for k in sorted(set(ka) | set(kb)):
        pa, pb = ka.get(k), kb.get(k)
        if pa == pb:
            continue
        if pa is None or pb is None:
            out.append(dict(phase=k.split("#")[0], develop=pa, branch=pb))
            continue
        for f in sorted(set(pa) | set(pb)):
            if pa.get(f) != pb.get(f):
                out.append(dict(phase=k.split("#")[0], field=f, develop=pa.get(f), branch=pb.get(f)))
    return out


def main():
    keep = train_ids()
    dev, br = labels_at(DEV, keep), labels_at(BRANCH, keep)
    rows, resaves = [], []
    only_dev = sorted(set(dev) - set(br))
    only_br = sorted(set(br) - set(dev))
    for sid in sorted(set(dev) & set(br)):
        a, b = dev[sid], br[sid]
        if a == b:
            continue
        diff = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
        content = diff & CONTENT
        if not content:
            resaves.append(dict(id=sid, keys=sorted(diff)))
            continue
        ch = dict(id=sid, fields=sorted(content), other_keys=sorted(diff - CONTENT))
        if "phases" in content:
            ch["phases"] = phase_changes(a.get("phases"), b.get("phases"))
        for f in sorted(content - {"phases"}):
            ch[f] = dict(develop=a.get(f), branch=b.get(f))
        rows.append(ch)
    out = dict(develop=git("rev-parse", "--short", DEV).strip(),
               branch=git("rev-parse", "--short", BRANCH).strip(),
               n_train_ids=len(keep), n_train_labels_develop=len(dev), n_train_labels_branch=len(br),
               only_in_develop=only_dev, only_in_branch=only_br,
               changed=rows, resave_only=resaves)
    (ROOT / "research/cleanup/passo0/relabel_diff.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
