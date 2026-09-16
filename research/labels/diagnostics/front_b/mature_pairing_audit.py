#!/usr/bin/env python
"""Front B part 1b - exact accounting behind the "n=45" mature deviation table.

Part 1 reported start/end/duration deviations over "n=45" without saying what
the unit was. The unit is a LABELLED MATURE WINDOW (not a series, not a
boundary), paired with the detected mature window it overlaps most. This script
enumerates every labelled mature window in the TRAIN split and states, for each,
whether it entered the table and why.

Read-only. TRAIN split only.

    python research/labels/diagnostics/front_b/mature_pairing_audit.py
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

OUT = Path(__file__).resolve().parent
rows = json.load(open(OUT / "train_raw.json"))

lines = []


def P(s=""):
    print(s)
    lines.append(s)


def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]) + 1)


P("FRONT B part 1b - what 'n=45' counts, and what was excluded")
P("=" * 94)
P()

n_series = len(rows)
series_with_label_mature = sum(1 for r in rows if r["lab_mature"])
total_label_mature = sum(len(r["lab_mature"]) for r in rows)
total_det_mature = sum(len(r["det_mature"]) for r in rows)

P(f"train series                                  : {n_series}")
P(f"series with >=1 LABELLED mature               : {series_with_label_mature}")
P(f"series with NO labelled mature                : "
  f"{n_series - series_with_label_mature}  "
  f"{[r['id'] for r in rows if not r['lab_mature']]}")
P(f"TOTAL labelled mature windows (the population): {total_label_mature}")
P(f"total DETECTED mature windows                 : {total_det_mature}")
P()
P("The unit of the deviation table is one LABELLED MATURE WINDOW.")
P("Each is paired with the detected mature window it overlaps most (>0 steps).")
P()

paired, unpaired = [], []
for r in rows:
    for (la, lb, lt, lu) in r["lab_mature"]:
        best, bo = None, 0
        for (da, db) in r["det_mature"]:
            o = overlap((da, db), (la, lb))
            if o > bo:
                best, bo = (da, db), o
        if best is None:
            unpaired.append((r["id"], r["source"], la, lb, lu, r["det_mature"]))
        else:
            paired.append((r["id"], r["source"], la, lb, lt, lu, best, bo))

P(f"paired   : {len(paired)}   <- this is the n=45")
P(f"unpaired : {len(unpaired)}")
P(f"check    : {len(paired)} + {len(unpaired)} = {len(paired)+len(unpaired)} "
  f"== {total_label_mature} labelled mature windows  "
  f"{'OK' if len(paired)+len(unpaired)==total_label_mature else 'MISMATCH'}")
P()
P("EXCLUDED - labelled mature windows with zero overlap with any detected mature:")
for sid, src, la, lb, lu, det in unpaired:
    P(f"   {sid} [{src}]  label mature [{la},{lb}] (len {lb-la+1}, unsure={lu})")
    P(f"      detected matures in this series: {det}  -> no overlap with the label")
P()
nu = sum(1 for p in paired if p[5])
unsure_ids = [f"{p[0]}[{p[2]},{p[3]}]" for p in paired if p[5]]
P("NOT excluded, for the record:")
P(f"   * `unsure` labelled matures ARE included ({nu} of them: "
  f"{', '.join(unsure_ids)}).")
P("   * series whose detected SEQUENCE differs from the label ARE included -")
P("     pairing is by overlap, not by position, precisely so a sequence")
P("     mismatch does not manufacture a deviation.")
P()

devs = [(p[6][1] - p[6][0] + 1) - (p[3] - p[2] + 1) for p in paired]
ds = [p[6][0] - p[2] for p in paired]
de = [p[6][1] - p[3] for p in paired]


def stat(name, v):
    P(f"   {name:<22} n={len(v):3d}  median={statistics.median(v):+6.1f}  "
      f"min={min(v):+4d}  max={max(v):+4d}  mean={statistics.mean(v):+6.2f}")


P("Recomputed from this audit (must match the part-1 table):")
stat("duration (det-label)", devs)
stat("start    (det-label)", ds)
stat("end      (det-label)", de)

(OUT / "mature_pairing_audit.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT / 'mature_pairing_audit.txt'}")
