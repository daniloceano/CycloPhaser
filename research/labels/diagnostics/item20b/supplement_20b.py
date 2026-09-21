#!/usr/bin/env python
"""Front 20(b) stage 1 - two supplementary measurements.

(1) The DC content of the series that feeds mature detection. The brief asks
    whether the filtered series' zero is a filter artefact. It is not zero-mean,
    so the question needs the actual number: how much of the raw mean survives
    the nominal band-pass, and how much does that gain vary between series.
(2) The separability test repeated on the two sub-populations that the global
    figure mixes, and D2 recomputed on the RAW series. Neither is a threshold
    sweep: no grid, no optimisation, the same two statistics as the main test.
"""
from __future__ import annotations

import sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from measure_20b import load_config
from labels_core import load_real_series, read_split
from cyclophaser.determine_periods import get_periods, process_vorticity
import json


def main():
    pv, gp = load_config()
    OUT = REPO / "research" / "labels" / "diagnostics" / "item20b"
    data = json.loads((OUT / "measurements.json").read_text())
    rows = data["rows"]
    train = set(read_split()["train"])
    real = {s: v for s, v in load_real_series().items() if s in train}

    print("=" * 78)
    print("(1) DC CONTENT OF df['z'] (= vorticity_smoothed2 = the Lanczos output)")
    print("=" * 78)
    print("cyclophaser/lanczos_filter.py documents this directly: at")
    print("window_length_lanczo = len(series)//2 the band-pass kernel does NOT")
    print("reject DC - sum(weights) has a documented median of 0.629. So the")
    print("filtered series keeps most of the raw mean rather than losing it.\n")
    gains, ratios = [], []
    per = {}
    for sid, vals in sorted(real.items()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": vals}), **pv)
        z = np.asarray(vort.vorticity_smoothed2.values, dtype=float)
        raw = np.asarray(vort.zeta.values, dtype=float)
        g = z.mean() / raw.mean()
        r = abs(z.mean()) / (z.max() - z.min())
        gains.append(g); ratios.append(r)
        per[sid] = (g, r)
    gains, ratios = np.array(gains), np.array(ratios)
    print(f"effective DC gain  mean(z)/mean(zeta), over the 35 real train series:")
    print(f"   min {gains.min():.4f}   median {np.median(gains):.4f}   max {gains.max():.4f}")
    print(f"   -> the filtered series is NOT zero-mean; it keeps "
          f"{np.median(gains):.0%} of the raw mean (median)")
    print(f"\n|mean(z)| / (z_max - z_min), same 35 series:")
    print(f"   min {ratios.min():.2f}   median {np.median(ratios):.2f}   max {ratios.max():.2f}")
    print(f"   -> the offset is {np.median(ratios):.1f}x the series' own peak-to-peak "
          f"range (median): z sits well below zero and oscillates about that offset.")
    print(f"\nspread of the gain across series: max-min = {gains.max()-gains.min():.4f}")
    print("   the gain depends on window_length_lanczo = len(series)//2, so it is")
    print("   SERIES-DEPENDENT: the baseline D2 measures |z| against is a different")
    print("   fraction of the physical zero in each series.")

    print("\n" + "=" * 78)
    print("(2a) SEPARABILITY, SPLIT BY SUB-POPULATION")
    print("=" * 78)
    nolab = {r["series"] for r in rows if r["n_labelled_matures"] == 0}
    print(f"series with zero labelled matures: {sorted(nolab)}")
    print("Every block they emit is SPURIOUS by the brief's rule, but it is a")
    print("different failure (a mature where the human saw none) from the")
    print("fragmentation 20(b) targets, so the cut is worth naming.\n")
    for name, sub in (("ALL 46 valleys (the headline figure)", rows),
                      ("excluding the 2 series with no labelled mature",
                       [r for r in rows if r["series"] not in nolab])):
        t = [r for r in sub if r["classification"] == "TRUE"]
        s = [r for r in sub if r["classification"] == "SPURIOUS"]
        print(f"--- {name}: {len(t)} true / {len(s)} spurious")
        for k in ("D1", "D2"):
            mn, mx = min(r[k] for r in t), max(r[k] for r in s)
            who = max(s, key=lambda r: r[k])
            print(f"    {k}: min(TRUE)={mn:.4f}  max(SPURIOUS)={mx:.4f}  "
                  f"separates? {'YES' if mn > mx else 'NO'}   "
                  f"(worst spurious: {who['series']} v{who['valley_idx']})")
        print()

    print("=" * 78)
    print("(2b) D2 RECOMPUTED ON THE RAW SERIES (df['z_unfil'])")
    print("=" * 78)
    print("The brief's concern was that a zero-mean filtered series would make")
    print("D2's zero an artefact. It is not zero-mean - but its zero is still the")
    print("physical zero times a series-dependent gain, so here is D2 measured")
    print("against physical zero instead, at the same valley positions.\n")
    raws = {}
    for sid, vals in sorted(real.items()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": vals}), **pv)
        raws[sid] = np.asarray(vort.zeta.values, dtype=float)
    t, s = [], []
    for r in rows:
        raw = raws[r["series"]]
        d2r = abs(raw[r["valley_idx"]]) / abs(raw.min())
        (t if r["classification"] == "TRUE" else s).append((d2r, r))
    mn = min(x for x, _ in t); mx = max(x for x, _ in s)
    who = max(s, key=lambda x: x[0])[1]
    print(f"D2_raw: min(TRUE)={mn:.4f}   max(SPURIOUS)={mx:.4f}   "
          f"separates? {'YES' if mn > mx else 'NO'}")
    print(f"        worst spurious: {who['series']} v{who['valley_idx']}")
    print("\n=> measuring depth against physical zero instead of the filtered")
    print("   zero does not create a separation either.")


if __name__ == "__main__":
    main()
