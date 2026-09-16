#!/usr/bin/env python
"""Front B part 1b - sweep `distance` over ALL 47 TRAIN series.

Part 1 swept `distance` on the two target tracks only and reported a global
minimum surviving gap (14, on 20170760) measured on a different series. This
script closes that gap: it runs the sweep on every training series and reports,
per distance value, how many z extrema the distance criterion removes and how
many series change their `periods` column relative to the reference config.

Read-only. TRAIN split only; the 16 test series are never loaded.

    python research/labels/diagnostics/front_b/sweep_distance.py
"""
from __future__ import annotations

import inspect
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.signal import argrelextrema, peak_prominences

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import load_real_series, load_synthetic_series, read_split
from cyclophaser.determine_periods import (_collapse_plateaux, get_periods,
                                           process_vorticity)

CONFIG = REPO / "research" / "labels" / "configs" / "cyclophaser_params-9.yaml"
OUT = Path(__file__).resolve().parent
PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")
SWEEP = [None, 1, 2, 3, 5, 8, 10, 12, 14, 15, 16, 18, 20, 25, 30, 40]


# ---------------------------------------------------------------------------
# HISTORICAL — does not run against the current package, by design.
#
# This script sweeps `distance`, the extrema filter that front B measured and
# that was REMOVED as a result (it was redundant with `prominence_relative`
# throughout the calibrated range). Against the current package every call
# below raises TypeError, which is the intended post-removal behaviour: there
# is no compatibility shim.
#
# It is kept as the evidence that justified the removal. Its frozen output
# alongside this file was produced on the pre-removal code
# (develop-v2.1 @ ab7f244, diagnostics commit 491a5d0) in the conda
# `cyclophaser` environment. To re-run it, check out that commit.
# ---------------------------------------------------------------------------
import sys as _sys


def _refuse_if_distance_is_gone():
    import inspect

    from cyclophaser.determine_periods import get_periods
    if "distance" not in inspect.signature(get_periods).parameters:
        _sys.exit(
            "HISTORICAL SCRIPT: `distance` was removed from cyclophaser, so this "
            "sweep cannot run against the current package. Its frozen output is "
            "next to this file; re-run it against develop-v2.1 @ ab7f244 if you "
            "need to reproduce it. See research/inert_params/REPORT_inertia_sweep.md."
        )


def load_config():
    doc = yaml.safe_load(CONFIG.read_text()) or {}
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


def candidates(data):
    """Raw collapsed peak/valley candidate indices, as find_peaks_valleys builds them."""
    peaks = _collapse_plateaux(argrelextrema(data, np.greater_equal)[0])
    valleys = _collapse_plateaux(argrelextrema(data, np.less_equal)[0])
    overlap = np.intersect1d(peaks, valleys)
    if len(overlap):
        peaks = peaks[~np.isin(peaks, overlap)]
    return peaks, valleys


def n_removed_by_distance(data, signed_data, cand, prominence_relative, distance):
    """How many interior candidates the DISTANCE criterion drops, post-prominence."""
    if distance is None or len(cand) == 0:
        return 0
    N = len(data)
    boundary = {i for i in (0, N - 1) if i in set(cand)}
    interior = np.array([i for i in cand if i not in boundary], dtype=int)
    if len(interior):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prom = peak_prominences(signed_data, interior)[0]
    else:
        prom = np.zeros(0)
    if prominence_relative is not None and len(interior):
        mx = prom.max() if len(prom) else 0.0
        if mx > 0.0:
            mask = prom >= prominence_relative * mx
            interior, prom = interior[mask], prom[mask]
    kept, dropped = list(boundary), 0
    for rank in np.argsort(-prom) if len(interior) else []:
        idx = int(interior[rank])
        if all(abs(idx - k) >= distance for k in kept):
            kept.append(idx)
        else:
            dropped += 1
    return dropped


def min_surviving_gap(data, signed_data, cand, prominence_relative):
    """Smallest same-type gap AFTER prominence, BEFORE distance (boundaries included)."""
    N = len(data)
    boundary = {i for i in (0, N - 1) if i in set(cand)}
    interior = np.array([i for i in cand if i not in boundary], dtype=int)
    if len(interior):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prom = peak_prominences(signed_data, interior)[0]
        if prominence_relative is not None:
            mx = prom.max() if len(prom) else 0.0
            if mx > 0.0:
                interior = interior[prom >= prominence_relative * mx]
    surv = sorted(boundary | set(interior.tolist()))
    gaps = [b - a for a, b in zip(surv, surv[1:])]
    return min(gaps) if gaps else None


def main():
    _refuse_if_distance_is_gone()
    pv, gp = load_config()
    prom_rel = gp.get("prominence_relative")
    split = read_split()
    train = set(split["train"])
    real = {k: v for k, v in load_real_series().items() if k in train}
    syn = {k: v for k, v in load_synthetic_series()[0].items() if k in train}
    series = {**real, **syn}

    lines = []

    def P(s=""):
        print(s)
        lines.append(s)

    P("FRONT B part 1b - `distance` sweep over all 47 TRAIN series")
    P("=" * 94)
    P(f"config: {CONFIG.name}   prominence_relative={prom_rel}   "
      f"reference distance={gp.get('distance')}")
    P(f"series: {len(real)} real + {len(syn)} synthetic = {len(series)}")
    P()

    # cache z and candidates once per series
    z_cache, ref_periods = {}, {}
    for sid, values in sorted(series.items()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            res = get_periods(vort, **gp)
        z = np.asarray(vort.vorticity_smoothed2.values, dtype=float)
        z_cache[sid] = z
        ref_periods[sid] = list(res["periods"].astype(str))

    # --- per-series minimum surviving gap (post-prominence, pre-distance) ----
    P("Minimum same-type gap among POST-PROMINENCE survivors, per series")
    P("(this is the quantity `distance` compares against; boundary indices included)")
    gaps = []
    for sid in sorted(series):
        z = z_cache[sid]
        pk, vl = candidates(z)
        g = [x for x in (min_surviving_gap(z, z, pk, prom_rel),
                         min_surviving_gap(z, -z, vl, prom_rel)) if x is not None]
        gaps.append((min(g), sid))
    gaps.sort()
    P("   smallest 10:")
    for g, sid in gaps[:10]:
        P(f"      {g:4d}   {sid}")
    P(f"   global minimum = {gaps[0][0]}  ({gaps[0][1]})")
    P()

    # --- the sweep ----------------------------------------------------------
    P("Sweep: per `distance` value, extrema removed BY DISTANCE and series whose")
    P("`periods` column differs from the reference run (distance=5).")
    P()
    P(f"   {'distance':>9} | {'extrema removed':>15} | {'series w/ removal':>17} | "
      f"{'series w/ PHASE change':>22}")
    P("   " + "-" * 74)
    table = []
    for d in SWEEP:
        tot_removed, series_removed, changed = 0, 0, []
        for sid, values in sorted(series.items()):
            z = z_cache[sid]
            pk, vl = candidates(z)
            r = (n_removed_by_distance(z, z, pk, prom_rel, d)
                 + n_removed_by_distance(z, -z, vl, prom_rel, d))
            tot_removed += r
            series_removed += 1 if r else 0
            if r:  # only re-run the detector where the extremum set actually moved
                g2 = dict(gp)
                g2["distance"] = d
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    res = get_periods(
                        process_vorticity(pd.DataFrame({"zeta": values}), **pv), **g2)
                if list(res["periods"].astype(str)) != ref_periods[sid]:
                    changed.append(sid)
        label = "None" if d is None else str(d)
        P(f"   {label:>9} | {tot_removed:>15} | {series_removed:>17} | "
          f"{len(changed):>22}")
        table.append((label, tot_removed, series_removed, changed))
    P()
    P("Series whose phases change, by distance value:")
    for label, tot, nser, changed in table:
        if changed:
            P(f"   distance={label:>4}: {changed}")
    P()
    lo = [t for t in table if t[1] == 0]
    P(f"=> `distance` removes NOTHING for values {', '.join(t[0] for t in lo)}.")
    first = next((t for t in table if t[1] > 0), None)
    if first:
        P(f"=> first value with any effect: distance={first[0]} "
          f"({first[1]} extrema, {first[2]} series, {len(first[3])} with phase changes)")

    (OUT / "distance_sweep.txt").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {OUT / 'distance_sweep.txt'}")


if __name__ == "__main__":
    main()
