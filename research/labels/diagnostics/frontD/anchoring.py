#!/usr/bin/env python
"""Front D, stage 0, step 2 — artefact vs real-phase test on the C1 series only.

For each C1 series (short detected incipient), with L = N_det:
  (a) label agreement: |N_det - N_lab| <= 6, the fixed margin. The label's own
      tolerance_idx is printed beside it as information only; the verdict uses 6.
  (b) temporal anchoring: for k = 1, 2, 3 with k < L, drop the first k steps of
      the RAW series, re-run the detector under params-13, and record the new
      incipient end in ABSOLUTE (original) index = k + N_det_cut.

The decision rule is the one frozen in the brief, applied as written:
  ARTEFACT        = (a) fails AND (b) edge-anchored
  REAL SHORT PHASE= (a) passes AND (b) time-anchored
  INCONCLUSIVE    = anything else, including L = 1 and "mixed"

Known limitation, recorded per cut: removing the first k steps can remove the
global min or the global max of the filtered series, which changes the
normalisation every relative threshold is measured against. Whether the removed
chunk held either extremum is reported for every cut.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import load_real_series, load_synthetic_series, read_split  # noqa: E402
from evaluate_against_labels import detected_incipient_end, load_config  # noqa: E402

CONFIG = REPO / "research/labels/configs/cyclophaser_params-13.yaml"
OUT = Path(__file__).resolve().parent
MARGIN = 6


def detect(values: pd.Series, pv, gp):
    from cyclophaser.determine_periods import get_periods, process_vorticity
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        res = get_periods(vort, **gp)
    end = detected_incipient_end(res["periods"])
    return (None if end is None else int(end)), vort


def main() -> int:
    census = json.loads((OUT / "census.json").read_text())
    rows = {r["id"]: r for r in census["rows"]}
    split = read_split()
    test = set(split["test"])
    real = load_real_series()
    synth, _ = load_synthetic_series()
    series = {**real, **synth}
    pv, gp = load_config(CONFIG)

    c1 = [r for r in census["rows"] if r["class"] == "C1"]
    assert not (set(r["id"] for r in c1) & test), "a test id reached step 2"

    results = []
    for r in c1:
        sid = r["id"]
        s = series[sid]
        L = r["N_det"]
        n_lab, tol = r["N_lab"], r["tolerance_idx"]

        # (a) — fixed margin 6; tolerance_idx reported alongside, not used
        a_pass = (n_lab is not None) and abs(L - n_lab) <= MARGIN

        # the filtered series' global extrema, on the FULL series
        _, vort_full = detect(s, pv, gp)
        filt = np.asarray(vort_full["filtered_vorticity"].values, dtype="float64")
        i_min, i_max = int(np.argmin(filt)), int(np.argmax(filt))

        cuts = []
        for k in (1, 2, 3):
            if k >= L:
                continue
            end_cut, _ = detect(s.iloc[k:], pv, gp)
            abs_end = None if end_cut is None else k + end_cut
            cuts.append({
                "k": k,
                "N_det_cut": end_cut,
                "abs_end": abs_end,
                "duration": end_cut,
                "time_anchored": (abs_end is not None and abs(abs_end - L) <= 1),
                "edge_anchored": (end_cut is None or abs(end_cut - L) <= 1),
                "removed_holds_global_min": i_min < k,
                "removed_holds_global_max": i_max < k,
            })

        if L == 1 or not cuts:
            b = "n/a (L=1)"
        elif all(c["time_anchored"] for c in cuts) and all(c["edge_anchored"] for c in cuts):
            # both readings true at once: with L small the two criteria are not
            # distinguishable, which is a property of the test, not of the series
            b = "indistinguishable (both)"
        elif all(c["time_anchored"] for c in cuts):
            b = "time-anchored"
        elif all(c["edge_anchored"] for c in cuts):
            b = "edge-anchored"
        else:
            b = "mixed"

        if (not a_pass) and b == "edge-anchored":
            verdict = "ARTEFACT"
        elif a_pass and b == "time-anchored":
            verdict = "REAL SHORT PHASE"
        else:
            verdict = "INCONCLUSIVE"

        results.append({"id": sid, "source": r["source"], "L": L, "N_lab": n_lab,
                        "tolerance_idx": tol, "a_pass": a_pass, "b": b,
                        "verdict": verdict, "cuts": cuts,
                        "filt_argmin": i_min, "filt_argmax": i_max})

    print("=" * 92)
    print(f"STEP 2 — anchoring test on C1 only   (margin fixed at {MARGIN})")
    print("=" * 92)
    for r in results:
        print(f"\n{r['id']}  ({r['source']})   L = N_det = {r['L']}   "
              f"N_lab = {r['N_lab']}   tolerance_idx = {r['tolerance_idx']} (info only)")
        print(f"  (a) |N_det - N_lab| = "
              f"{'—' if r['N_lab'] is None else abs(r['L'] - r['N_lab'])} "
              f"<= {MARGIN} ?  {'PASS' if r['a_pass'] else 'FAIL'}")
        if not r["cuts"]:
            print("  (b) not applicable: L = 1, no valid k")
        else:
            print(f"  (b) filtered-series global min at idx {r['filt_argmin']}, "
                  f"max at idx {r['filt_argmax']}")
            print(f"      {'k':>2} {'N_det_cut':>10} {'abs_end':>8} {'time?':>6} "
                  f"{'edge?':>6}  removed chunk holds")
            for c in r["cuts"]:
                holds = ", ".join(
                    x for x, y in (("global min", c["removed_holds_global_min"]),
                                   ("global max", c["removed_holds_global_max"])) if y
                ) or "neither extremum"
                print(f"      {c['k']:>2} {str(c['N_det_cut']):>10} "
                      f"{str(c['abs_end']):>8} {str(c['time_anchored']):>6} "
                      f"{str(c['edge_anchored']):>6}  {holds}")
        print(f"  (b) reading: {r['b']}")
        print(f"  VERDICT: {r['verdict']}")

    from collections import Counter
    for src in ("real", "synthetic"):
        sel = [r for r in results if r["source"] == src]
        if sel:
            print(f"\n{src.upper()} C1 verdicts: {dict(Counter(r['verdict'] for r in sel))}")

    (OUT / "anchoring.json").write_text(json.dumps(results, indent=2))
    print(f"\nwrote {OUT / 'anchoring.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
