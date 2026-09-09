#!/usr/bin/env python
"""Investigate the M5 divergence: predicted +2 (18/35 -> 20/35) on TRAIN·real
sequence match, measured +1 (18/35 -> 19/35).

READ-ONLY. Reads fix_state_before.json / fix_state_after.json (already
produced) plus manual_labels.yaml (TRAIN real records only -- no test track is
read) to find, per track, whether sequence-match status flipped, and in which
direction, individually -- not just the net count.
"""
import json
import sys
from pathlib import Path

DIAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = DIAG_DIR.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS_DIR))
from labels_core import (  # noqa: E402
    read_labels, read_split, is_legacy_record, series_sha256, load_real_series,
    normalize_phase, phase_sequence,
)

before = json.loads((DIAG_DIR / "fix_state_before.json").read_text())["tracks"]
after = json.loads((DIAG_DIR / "fix_state_after.json").read_text())["tracks"]

records = read_labels()
split_doc = read_split()
train = set(split_doc["train"])
real_series = load_real_series()


def detected_sequence(periods_list):
    out = []
    prev = None
    for i, lab in enumerate(periods_list):
        name = normalize_phase(lab)
        if name != prev:
            out.append((name, i))
            prev = name
    return out


usable_train_real = {}
for sid, rec in records.items():
    if sid not in train:
        continue
    if sid not in real_series:
        continue
    if is_legacy_record(rec):
        continue
    if rec.get("series_sha256") != series_sha256(real_series[sid]):
        continue
    usable_train_real[sid] = rec

print(f"usable TRAIN real labelled tracks: {len(usable_train_real)}")

flips_to_match, flips_to_mismatch, unchanged_match, unchanged_mismatch = [], [], [], []

for sid, rec in sorted(usable_train_real.items()):
    lab_seq = [p for p, _ in phase_sequence(rec)]

    det_before = [normalize_phase(p) for p, _ in detected_sequence(before[sid]["periods"])]
    det_after = [normalize_phase(p) for p, _ in detected_sequence(after[sid]["periods"])]

    match_before = (det_before == lab_seq)
    match_after = (det_after == lab_seq)

    if match_before and not match_after:
        flips_to_mismatch.append((sid, lab_seq, det_before, det_after))
    elif not match_before and match_after:
        flips_to_match.append((sid, lab_seq, det_before, det_after))
    elif match_before and match_after:
        unchanged_match.append(sid)
    else:
        unchanged_mismatch.append((sid, lab_seq, det_before, det_after))

print(f"\nmatch before: {sum(1 for s in usable_train_real if [normalize_phase(p) for p,_ in detected_sequence(before[s]['periods'])] == [p for p,_ in phase_sequence(usable_train_real[s])])}")
print(f"match after:  {sum(1 for s in usable_train_real if [normalize_phase(p) for p,_ in detected_sequence(after[s]['periods'])] == [p for p,_ in phase_sequence(usable_train_real[s])])}")

print(f"\nflips mismatch->match ({len(flips_to_match)}):")
for sid, lab_seq, db, da in flips_to_match:
    print(f"  {sid}: label={lab_seq}\n         before={db}\n         after ={da}")

print(f"\nflips match->mismatch ({len(flips_to_mismatch)}) -- REGRESSIONS:")
for sid, lab_seq, db, da in flips_to_mismatch:
    print(f"  {sid}: label={lab_seq}\n         before={db}\n         after ={da}")

print(f"\nunchanged, still mismatched, among the 4 affected tracks (20180170/20180608/20190325/20191014):")
affected = {"20180170", "20180608", "20190325", "20191014"}
for sid, lab_seq, db, da in unchanged_mismatch:
    if sid in affected:
        print(f"  {sid}: label={lab_seq}\n         before={db}\n         after ={da}")
