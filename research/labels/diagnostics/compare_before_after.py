#!/usr/bin/env python
"""Compare fix_state_before.json vs fix_state_after.json for M1/M2/M6/M7.

READ-ONLY (only reads the two JSON snapshots produced by
capture_pipeline_state.py before/after the idx0 fix). Prints a full report.
"""
import json
import sys
from pathlib import Path

DIAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = DIAG_DIR.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS_DIR))
from labels_core import read_split  # noqa: E402

before = json.loads((DIAG_DIR / "fix_state_before.json").read_text())["tracks"]
after = json.loads((DIAG_DIR / "fix_state_after.json").read_text())["tracks"]

split_doc = read_split()
train = set(split_doc["train"])
test = set(split_doc["test"])

VALLEY_5 = ["20180170", "20180608", "20190325", "20191014", "20206498"]

print("=" * 78)
print("M1 — no-op check on the 46 idx0_tipo=peak real tracks")
print("=" * 78)
real_ids = sorted(k for k, v in before.items() if v.get("source") == "real")
assert len(real_ids) == 51, len(real_ids)
peak46 = [sid for sid in real_ids if sid not in VALLEY_5]
assert len(peak46) == 46, len(peak46)

identical, diffs = [], []
for sid in peak46:
    b, a = before[sid]["periods"], after[sid]["periods"]
    if b == a:
        identical.append(sid)
    else:
        diffs.append(sid)
        # find first differing position
        first = next(i for i, (x, y) in enumerate(zip(b, a)) if x != y)
        print(f"  DIVERGENCE {sid}: first differing position {first}: "
              f"before={b[first]!r} after={a[first]!r}")
print(f"identical: {len(identical)}/46")
print(f"diverging: {len(diffs)}/46  {diffs}")

print()
print("=" * 78)
print("M2 — index 0 present in surviving peaks AFTER prominence/distance filter, 5 valley tracks")
print("=" * 78)
for sid in VALLEY_5:
    zpv_after = after[sid]["z_peaks_valleys"]
    zpv_before = before[sid]["z_peaks_valleys"]
    print(f"  {sid}: before[0]={zpv_before[0]!r}  after[0]={zpv_after[0]!r}")

print()
print("=" * 78)
print("M3 — first non-incipient phase, final output, 4 TRAIN affected tracks")
print("=" * 78)
TRAIN4 = ["20180170", "20180608", "20190325", "20191014"]
def first_non_incipient(periods):
    for p in periods:
        if p != "incipient":
            return p
    return None

for sid in TRAIN4:
    fb = first_non_incipient(before[sid]["periods"])
    fa = first_non_incipient(after[sid]["periods"])
    print(f"  {sid}: before={fb!r} after={fa!r}")

print()
print("=" * 78)
print("M6 — mature phase, 5 valley tracks (no judgement, just report)")
print("=" * 78)
def phase_blocks(periods, phase):
    blocks = []
    start = None
    for i, p in enumerate(periods + [None]):
        if p == phase and start is None:
            start = i
        elif p != phase and start is not None:
            blocks.append((start, i - 1))
            start = None
    return blocks

for sid in VALLEY_5:
    pb = phase_blocks(before[sid]["periods"], "mature")
    pa = phase_blocks(after[sid]["periods"], "mature")
    print(f"  {sid}: n={before[sid]['n_steps']}")
    print(f"    before mature blocks (start,end): {pb}")
    print(f"    after  mature blocks (start,end): {pa}")

print()
print("=" * 78)
print("M7 — synthetic cases (12), full periods array before vs after")
print("=" * 78)
synth_ids = sorted(k for k, v in before.items() if v.get("source") == "synthetic")
assert len(synth_ids) == 12, len(synth_ids)
n_identical = 0
for sid in synth_ids:
    b, a = before[sid]["periods"], after[sid]["periods"]
    same = (b == a)
    n_identical += same
    zb0, za0 = before[sid]["z_peaks_valleys"][0], after[sid]["z_peaks_valleys"][0]
    tag = "SAME" if same else "DIFFERENT"
    print(f"  {sid}: idx0_type before={zb0!r} after={za0!r}  periods {tag}")
    if not same:
        first = next(i for i, (x, y) in enumerate(zip(b, a)) if x != y)
        print(f"      first differing position {first}: before={b[first]!r} after={a[first]!r}")
print(f"identical: {n_identical}/12")
