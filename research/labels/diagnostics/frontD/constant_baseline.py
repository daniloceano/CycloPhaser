#!/usr/bin/env python
"""Front D, stage 0 — the constant baseline for the incipient-end question, TRAIN.

ATTRIBUTION, read before citing any number from here: this is NOT a line of
`evaluate_against_labels.py`. That script computes no baseline of any kind
(checked at f901b76). The "constant modal-sequence baseline" quoted in
docs/future_work.md item 19 is a different quantity, about the whole phase
SEQUENCE, produced by that front's own diagnostics. The numbers below come from
this file and nowhere else.

What is scored: the strategy "ignore the series, always answer N" — including
N = "no incipient phase" — against the same train labels, read the same way
score_labels reads them (per-label tolerance_idx for the hit rate; raw distance
for MAE), so the baseline and the detector are measured on one ruler.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))

from labels_core import read_labels, read_split, score_labels  # noqa: E402

OUT = Path(__file__).resolve().parent


def fnum(x, spec=".2f"):
    return "—" if x is None else format(x, spec)


def main() -> int:
    records = read_labels()
    split = read_split()
    train = set(split["train"])
    sources = split["source"]
    census = {r["id"]: r for r in json.loads((OUT / "census.json").read_text())["rows"]}

    out = {}
    for src in ("real", "synthetic", "all"):
        sel = [r for sid, r in sorted(records.items())
               if sid in train and (src == "all" or sources.get(sid) == src)]
        print("=" * 78)
        print(f"TRAIN · {src}   ({len(sel)} labels)")
        print("=" * 78)
        print(f"  {'constant':>12}  {'n_bdry':>6} {'hit':>4} {'hit rate':>9} "
              f"{'MAE':>7} {'worst':>6}   {'none agreed':>11}")
        best = None
        for const in [None] + list(range(0, 41)):
            det = {sid: const for sid in train}
            m = score_labels(sel, det)
            label = "no incipient" if const is None else str(const)
            print(f"  {label:>12}  {m['n_boundary']:>6} {m['n_hit']:>4} "
                  f"{fnum(None if m['hit_rate'] is None else 100 * m['hit_rate'], '8.1f')}% "
                  f"{fnum(m['mae'], '7.2f')} {str(m['worst']):>6}   "
                  f"{m['n_none_agreed']}/{m['n_none']}")
            key = (m["n_hit"], -(m["mae"] if m["mae"] is not None else 1e9))
            if best is None or key > (best[1]["n_hit"],
                                      -(best[1]["mae"] if best[1]["mae"] is not None else 1e9)):
                best = (const, m)
        b_const, b = best
        print(f"\n  BEST constant: {'no incipient' if b_const is None else b_const}"
              f"  ->  {b['n_hit']}/{b['n_boundary']} within each label's own margin "
              f"({fnum(None if b['hit_rate'] is None else 100 * b['hit_rate'], '.1f')}%), "
              f"MAE {fnum(b['mae'])}, worst {b['worst']}\n")
        out[src] = {"best_constant": b_const, "n_boundary": b["n_boundary"],
                    "n_hit": b["n_hit"], "hit_rate": b["hit_rate"],
                    "mae": b["mae"], "worst": b["worst"]}

    print("=" * 78)
    print("the detector under params-13, on the SAME ruler, for comparison")
    print("=" * 78)
    for src in ("real", "synthetic", "all"):
        sel = [r for sid, r in sorted(records.items())
               if sid in train and (src == "all" or sources.get(sid) == src)]
        det = {sid: (None if census[sid]["N_det"] == 0 else census[sid]["N_det"])
               for sid in train}
        m = score_labels(sel, det)
        out[src]["detector"] = {"n_hit": m["n_hit"], "n_boundary": m["n_boundary"],
                                "hit_rate": m["hit_rate"], "mae": m["mae"],
                                "worst": m["worst"]}
        print(f"  TRAIN·{src:<10} {m['n_hit']:>3}/{m['n_boundary']:<3} "
              f"({fnum(None if m['hit_rate'] is None else 100 * m['hit_rate'], '.1f')}%), "
              f"MAE {fnum(m['mae'])}, worst {m['worst']}")

    (OUT / "constant_baseline.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT / 'constant_baseline.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
