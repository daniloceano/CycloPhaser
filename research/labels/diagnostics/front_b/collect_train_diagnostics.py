#!/usr/bin/env python
"""FRONT B part 1 - read-only diagnostic. No detector code is modified.

Reproduces the reference configuration (cyclophaser_params-9.yaml) on the TRAIN
split only, and reports, per series:
  * the detected mature window vs the manual label's mature window
  * the z extrema before and after the prominence/distance refinement, with
    each removal attributed to the criterion that removed it
"""
from __future__ import annotations

import json, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import (load_real_series, load_synthetic_series, normalize_phase,
                         read_labels, read_split, series_sha256)
from cyclophaser.determine_periods import (get_periods, process_vorticity,
                                           _collapse_plateaux)
from scipy.signal import argrelextrema, peak_prominences

CONFIG = Path.home() / "Downloads" / "cyclophaser_params-9.yaml"
OUT = REPO / "research" / "labels" / "diagnostics" / "front_b"
OUT.mkdir(parents=True, exist_ok=True)

PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")


def load_config(path):
    import inspect
    doc = yaml.safe_load(Path(path).read_text()) or {}
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


# --------------------------------------------------------------------------- #
# extremum bookkeeping - mirrors determine_periods._refine_extrema exactly,
# but records WHICH filter dropped each candidate instead of only the survivors
# --------------------------------------------------------------------------- #
def trace_extrema(data, signed_data, prominence_relative, distance):
    N = len(data)
    if signed_data is data:
        cand = argrelextrema(data, np.greater_equal)[0]
    else:
        cand = argrelextrema(data, np.less_equal)[0]
    cand = _collapse_plateaux(cand)
    return cand, N


def refine_traced(data, signed_data, candidates, prominence_relative, distance, N):
    """Returns (survivors, {idx: 'prominence'|'distance'}) - attribution per drop."""
    dropped = {}
    if len(candidates) == 0:
        return candidates, dropped
    boundary = {i for i in (0, N - 1) if i in set(candidates)}
    interior = np.array([i for i in candidates if i not in boundary], dtype=int)
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
            for i in interior[~mask]:
                dropped[int(i)] = "prominence"
            interior, prom = interior[mask], prom[mask]

    if distance is not None:
        order = np.argsort(-prom) if len(interior) else np.array([], dtype=int)
        kept = list(boundary)
        for rank in order:
            idx = int(interior[rank])
            if all(abs(idx - k) >= distance for k in kept):
                kept.append(idx)
            else:
                dropped[idx] = "distance"
        surviving = np.array([i for i in interior if i in set(kept)], dtype=int)
    else:
        surviving = interior
    return np.array(sorted(boundary | set(surviving.tolist())), dtype=int), dropped


def extrema_report(z_values, prominence_relative, distance):
    """Raw vs refined peaks/valleys on z, with per-drop attribution."""
    data = np.asarray(z_values, dtype=float)
    N = len(data)
    peaks = _collapse_plateaux(argrelextrema(data, np.greater_equal)[0])
    valleys = _collapse_plateaux(argrelextrema(data, np.less_equal)[0])
    overlap = np.intersect1d(peaks, valleys)
    if len(overlap):
        peaks = peaks[~np.isin(peaks, overlap)]

    p_keep, p_drop = refine_traced(data, data, peaks, prominence_relative, distance, N)
    v_keep, v_drop = refine_traced(data, -data, valleys, prominence_relative, distance, N)

    # counterfactual: distance disabled, prominence only
    p_keep_np, _ = refine_traced(data, data, peaks, prominence_relative, None, N)
    v_keep_np, _ = refine_traced(data, -data, valleys, prominence_relative, None, N)
    return dict(
        raw_peaks=peaks.tolist(), raw_valleys=valleys.tolist(),
        kept_peaks=p_keep.tolist(), kept_valleys=v_keep.tolist(),
        dropped_peaks=p_drop, dropped_valleys=v_drop,
        kept_peaks_no_distance=p_keep_np.tolist(),
        kept_valleys_no_distance=v_keep_np.tolist(),
    )


# --------------------------------------------------------------------------- #
def phase_runs(periods):
    """[(phase, start, end_inclusive), ...] over normalised phase names."""
    out, prev, start = [], None, 0
    names = [normalize_phase(str(x)) for x in periods]
    for i, n in enumerate(names):
        if n != prev:
            if prev is not None:
                out.append((prev, start, i - 1))
            prev, start = n, i
    out.append((prev, start, len(names) - 1))
    return out


def label_runs(record):
    ph = record["phases"]
    n = record["n_steps"]
    out = []
    for k, p in enumerate(ph):
        s = p["start_idx"]
        e = (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph) else n - 1
        out.append((normalize_phase(p["phase"]), s, e, p.get("tolerance_idx"),
                    bool(p.get("unsure"))))
    return out


def main():
    pv, gp = load_config(CONFIG)
    prom_rel = gp.get("prominence_relative")
    dist = gp.get("distance")
    print(f"config       : {CONFIG}")
    print(f"prominence_relative={prom_rel}   distance={dist}   "
          f"length_scale={gp.get('length_scale')}   mature_method={gp.get('mature_method')}")

    split = read_split()
    train = list(split["train"])
    labels = read_labels()

    real = {sid: s for sid, s in load_real_series().items() if sid in train}
    synth = {sid: s for sid, s in load_synthetic_series()[0].items() if sid in train}
    series = {**real, **synth}
    print(f"train series : {len(real)} real + {len(synth)} synthetic = {len(series)}")

    rows = []
    for sid, values in series.items():
        rec = labels.get(sid)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            res = get_periods(vort, **gp)
        z = vort.vorticity_smoothed2.values
        ex = extrema_report(z, prom_rel, dist)

        det = phase_runs(res["periods"])
        det_mat = [r for r in det if r[0] == "mature"]
        lab = label_runs(rec) if rec else []
        lab_mat = [r for r in lab if r[0] == "mature"]

        # z valleys with both bounding peaks == candidate cycles
        kp, kv = ex["kept_peaks"], ex["kept_valleys"]
        cycles = sum(1 for v in kv if any(p < v for p in kp) and any(p > v for p in kp))

        rows.append(dict(
            id=sid, source=("real" if sid in real else "synthetic"),
            n=len(values), sha_ok=(series_sha256(values) == rec["series_sha256"]) if rec else None,
            det_mature=[(a, b) for _, a, b in det_mat],
            lab_mature=[(a, b, t, u) for _, a, b, t, u in lab_mat],
            det_seq=[r[0] for r in det],
            lab_seq=[r[0] for r in lab],
            cycles=cycles,
            n_raw_ext=len(ex["raw_peaks"]) + len(ex["raw_valleys"]),
            n_kept_ext=len(ex["kept_peaks"]) + len(ex["kept_valleys"]),
            n_drop_prom=sum(1 for v in list(ex["dropped_peaks"].values()) + list(ex["dropped_valleys"].values()) if v == "prominence"),
            n_drop_dist=sum(1 for v in list(ex["dropped_peaks"].values()) + list(ex["dropped_valleys"].values()) if v == "distance"),
            ex=ex,
        ))

    with open(OUT / "train_raw.json", "w") as f:
        json.dump(rows, f, indent=1, default=str)
    print(f"wrote {OUT/'train_raw.json'}  ({len(rows)} series)")
    bad = [r["id"] for r in rows if r["sha_ok"] is False]
    print("sha256 mismatches:", bad or "none")


if __name__ == "__main__":
    main()
