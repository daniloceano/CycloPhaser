#!/usr/bin/env python
"""Front C - the two TEST-split series, measured with explicit authorisation.

*** THIS SCRIPT READS THE FROZEN TEST SPLIT. ***

20180654 is in the test split. Danilo authorised measuring and reporting it for
this front specifically, because it is the second series the depth floor was
designed to fix and the front cannot be judged without it. That authorisation
is a declared spend of the test set, recorded in docs/future_work.md - it is
not a precedent and it does not extend to any other series or any other front.

Nothing here is used to CHOOSE the threshold. 0.05 was selected from the train
split alone (see d2_separation.py); this script only reports what that already
fixed choice does to the authorised series.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "research/labels/diagnostics/frontC"))

from labels_core import load_real_series, normalize_phase, read_labels, read_split
from cyclophaser.determine_periods import get_periods, process_vorticity
from d2_separation import load_config, segments
from measure_frontC import runs_of

AUTHORISED = ["20180654"]


def main():
    split = read_split()
    labels = read_labels()
    series = load_real_series()
    pv, gp12 = load_config("cyclophaser_params-12.yaml")
    _, gp13 = load_config("cyclophaser_params-13.yaml")

    print("TEST-SPLIT MEASUREMENT - authorised series only:", AUTHORISED)
    print(f"(test split holds {len(split['test'])} series; only the authorised "
          f"one(s) above are read)\n")

    for sid in AUTHORISED:
        assert sid in split["test"], f"{sid} is not in the test split"
        values = series[sid]
        out = {}
        for tag, gp in (("params-12", gp12), ("params-13", gp13)):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
                df = get_periods(vort, **gp)
            periods = [normalize_phase(str(x)) for x in df["periods"]]
            out[tag] = (periods, runs_of(periods))

        print(f"=== {sid}  (n={len(values)}) ===")
        for tag in ("params-12", "params-13"):
            print(f"  {tag}: {out[tag][1]}")
        print(f"  changed: {out['params-12'][0] != out['params-13'][0]}")

        rec = labels.get(sid)
        if rec:
            ph, n = rec["phases"], rec["n_steps"]
            lab = [(normalize_phase(p["phase"]), p["start_idx"],
                    (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph) else n - 1)
                   for k, p in enumerate(ph)]
            print(f"  manual label: {lab}")

        # the D2 of the raw segments in this series
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            df12 = get_periods(vort, **gp12)
        for sg in segments(df12.copy(), gp12):
            flag = "  <- REJECTED by the 0.05 floor" if sg["D2"] < 0.05 else ""
            print(f"    raw segment {sg['start']:>4}-{sg['end']:<4} "
                  f"steps {sg['n_steps']:>3}  D2 {sg['D2']:>8.4f}{flag}")
        print()


if __name__ == "__main__":
    main()
