#!/usr/bin/env python
"""Passo 6a, commit 21 — a TRAINING series on which the incipient probe's rel(t0)
is not monotone in the smoothing window (replaces the test-split series the
calibration app's help text cited). Read-only.

    <cyclophaser env python> -P research/cleanup/passo6/rel_t0_window.py   # writes rel_t0_window.json

rel(t0) is the first value of the package's own probe profile,
find_stages._incipient_plateau_rel(df, "vorticity", w, 3): |d(zeta_raw)/dt| after
a Savitzky-Golay pass of window w (0 = none), normalised by its maximum. The
signal "vorticity" reads the RAW series, so the filter settings do not enter.
Series: the training ids of research/labels/split.yaml (the split and the
swell batch's train cases); only their files are opened.
"""
import importlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research" / "labels"))
from labels_core import load_batch_series, load_real_series, read_split  # noqa: E402

FS = importlib.import_module("cyclophaser.find_stages")
WINDOWS = [0, 3, 5, 7, 9]

split = read_split()
train = {str(i) for i in split["train"]}
batch = split["batches"]["swell_item30"]
batch_train = {str(i) for i in batch["train"]}
series = load_real_series(ids=train)
series.update(load_batch_series("swell_item30", ids=batch_train))
rows = {}
for sid, s in sorted(series.items()):
    df = pd.DataFrame({"z_unfil": s.values})
    rows[sid] = {w: float(FS._incipient_plateau_rel(df, "vorticity", w, 3)[0]) for w in WINDOWS}
nonmono = {sid: r for sid, r in rows.items() if r[5] > r[0] and r[7] < r[5]}
ranked = sorted(nonmono, key=lambda sid: -min(rows[sid][5] - rows[sid][0], rows[sid][5] - rows[sid][7]))
out = dict(windows=WINDOWS, n_series=len(rows), n_rise_then_fall=len(nonmono),
           ranked_rise_then_fall=[dict(id=sid, rel_t0={str(w): round(rows[sid][w], 2) for w in WINDOWS})
                                  for sid in ranked])
(Path(__file__).with_name("rel_t0_window.json")).write_text(json.dumps(out, indent=1))
print(f"{len(rows)} training series; rise at w=5 then fall at w=7: {len(nonmono)}")
for r in out["ranked_rise_then_fall"][:5]:
    print(" ", r["id"], r["rel_t0"])
