#!/usr/bin/env python
"""Front C - the D2 distribution over every candidate intensification segment.

Reproduces find_intensification_period's own segment enumeration (z_peak ->
next z_valley, duration test with the params-12 length_scale) and computes

    D2 = (z[peak] - z[valley]) / (z_max - z_min)

for every RAW segment that clears the duration test, on the 47 TRAIN series.
This is the measurement that justifies the 0.05 floor: it says where the gap
between the spurious blocks and the legitimate ones actually is.

Two different populations, deliberately kept apart
-------------------------------------------------
* **75 raw segments** clear the duration test across the 47 train series. This
  is the population the floor actually judges, so every D2 statistic below is
  quoted over it.
* **68 stitched blocks** are what find_intensification_period leaves behind
  after `threshold_intensification_gap` merges neighbours. That is a smaller
  number for the obvious reason, and it is NOT the denominator for D2: a
  stitched block's D2 is a property of the merged span, which is exactly the
  quantity this front declines to judge on.

The enumeration is verified against the detector before it is trusted. The
check is made against the state immediately AFTER find_intensification_period
(captured by patching it), not against the final phase column: steps 2-6
legitimately overwrite intensification, so a raw segment being absent from the
final output proves nothing. 20180733's spurious segment is precisely such a
case - it is accepted at step 1 and then overwritten with residual at step 4.
"""
from __future__ import annotations

import inspect
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import load_real_series, load_synthetic_series, read_split
from cyclophaser.determine_periods import get_periods, process_vorticity
from cyclophaser.find_stages import _local_cycle_scale

OUT = REPO / "research" / "labels" / "diagnostics" / "frontC"
PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")


def load_config(name):
    doc = yaml.safe_load((REPO / "research/labels/configs" / name).read_text()) or {}
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


def segments(df, gp):
    """Enumerate the raw segments exactly as find_intensification_period does."""
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index
    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index
    length = df.index[-1] - df.index[0]
    ls = gp.get("length_scale", "global")
    thr = gp["threshold_intensification_length"]
    z = df['z'].to_numpy(dtype=float)
    z_range = float(np.nanmax(z) - np.nanmin(z))
    pos = {lab: i for i, lab in enumerate(df.index)}

    out = []
    for z_peak in z_peaks:
        nxt = z_valleys[z_valleys > z_peak].min()
        if pd.isna(nxt):
            continue
        scale = _local_cycle_scale(df, z_peak, nxt) if ls == "local" else length
        if nxt - z_peak > scale * thr:
            d2 = (float(df.at[z_peak, 'z']) - float(df.at[nxt, 'z'])) / z_range
            out.append(dict(start=pos[z_peak], end=pos[nxt],
                            n_steps=pos[nxt] - pos[z_peak], D2=d2))
    return out


def main():
    train = set(read_split()["train"])
    real = {s: v for s, v in load_real_series().items() if s in train}
    synth = {s: v for s, v in load_synthetic_series()[0].items() if s in train}
    allser = {**real, **synth}
    pv, gp = load_config("cyclophaser_params-12.yaml")

    rows, mismatched, stitched = [], [], 0
    orig_fip = get_periods.__globals__["find_intensification_period"]
    cap = {}

    def spy(d, **kw):
        cap["entry"] = d.copy()
        out = orig_fip(d, **kw)
        cap["after"] = out.copy()
        return out

    for sid, values in sorted(allser.items()):
        get_periods.__globals__["find_intensification_period"] = spy
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
                df = get_periods(vort, **gp)
        finally:
            get_periods.__globals__["find_intensification_period"] = orig_fip
        entry, after = cap["entry"], cap["after"]
        segs = segments(entry.copy(), gp)

        # --- verify the replay against the detector's own step-1 output ----
        # Captured immediately after find_intensification_period, where the
        # only difference from the raw segments is gap stitching (which can
        # only ADD timesteps). The replay must therefore be a strict subset.
        mask_replay = np.zeros(len(entry), bool)
        for sg in segs:
            mask_replay[sg["start"]:sg["end"] + 1] = True
        mask_det = np.array([str(x) == "intensification" for x in after["periods"]])
        if not np.all(mask_replay <= mask_det):
            mismatched.append(sid)
        det_idx = np.flatnonzero(mask_det)
        if len(det_idx):
            stitched += 1 + int(np.sum(np.diff(det_idx) != 1))

        # how much of each raw segment survives into the FINAL phase column
        final = [str(x) for x in df["periods"]]
        for sg in segs:
            span = final[sg["start"]:sg["end"] + 1]
            sg["pct_intens_final"] = sum(1 for x in span if x == "intensification") / len(span)
            rows.append(dict(series=sid, **sg))

    print(f"train series: {len(allser)}")
    print(f"RAW segments clearing the duration test (what the floor judges): {len(rows)}")
    print(f"STITCHED blocks left by find_intensification_period            : {stitched}")
    print(f"replay verification (raw segments must be a subset of the step-1 mask): "
          f"{'FAIL ' + str(mismatched) if mismatched else 'PASS on all 47 series'}")

    d2 = np.array([r["D2"] for r in rows])
    order = np.argsort(d2)
    print("\n--- the 12 smallest D2 ---")
    print(f"{'series':>12} {'start':>6} {'end':>6} {'steps':>6} {'D2':>10} {'%int.final':>11}")
    for i in order[:12]:
        r = rows[i]
        print(f"{r['series']:>12} {r['start']:>6} {r['end']:>6} {r['n_steps']:>6} "
              f"{r['D2']:>10.4f} {r['pct_intens_final']*100:>10.0f}%")

    for thr in (0.05, 0.10, 0.15, 0.20):
        below = d2[d2 < thr]
        print(f"\nsegments with D2 < {thr:.2f}: {len(below)}  -> {np.sort(below)}")

    below15 = np.sort(d2[d2 < 0.15])
    above15 = np.sort(d2[d2 >= 0.15])
    print(f"\nlargest below 0.15 : {below15[-1] if len(below15) else None}")
    print(f"smallest at/above  : {above15[0] if len(above15) else None}")
    print(f"D2 range overall   : {d2.min():.4f} .. {d2.max():.4f}")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(rows, (OUT / "d2_segments.json").open("w"), indent=1)
    pd.DataFrame(rows).sort_values("D2").to_csv(OUT / "d2_segments.csv", index=False)
    print(f"\nwrote {OUT/'d2_segments.csv'}")


if __name__ == "__main__":
    main()
