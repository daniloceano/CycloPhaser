#!/usr/bin/env python
"""Front 20(b) stage 1 - depth of the valleys that generate mature blocks.

MEASUREMENT ONLY. No package code is modified and none is needed: every number
below comes from calling the detector as shipped and reading its output.

Scope: the 35 REAL series of the TRAIN split, under params-11.
`read_split()["test"]` is never read. The 12 synthetics are read only for
measurement C, whose published denominator (38) is a 47-series number.

This is a NEW driver. research/labels/diagnostics/item19/item19_core.py is a
frozen instrument pinned to params-10 and is neither imported nor edited here;
the few helpers it also has (extrema prominence, phase runs) are re-derived
below straight from determine_periods, so this file stands alone.
"""
from __future__ import annotations

import csv
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

from labels_core import (load_real_series, load_synthetic_series, normalize_phase,
                         read_labels, read_split, series_sha256)
from cyclophaser.determine_periods import get_periods, process_vorticity, _collapse_plateaux
from cyclophaser.find_stages import _amplitude_mature_bounds
from scipy.signal import argrelextrema, peak_prominences

CONFIG = REPO / "research" / "labels" / "configs" / "cyclophaser_params-11.yaml"
OUT = REPO / "research" / "labels" / "diagnostics" / "item20b"

PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")

MARGIN = 6      # item 17(d): the asserted boundary margin is a fixed 6


def load_config(path=CONFIG):
    doc = yaml.safe_load(Path(path).read_text()) or {}
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


# --------------------------------------------------------------------------- #
# extrema, with the exact relative prominence the detector compares against
# --------------------------------------------------------------------------- #
def valley_facts(z):
    """Per-valley prominence facts, mirroring find_peaks_valleys/_refine_extrema.

    Returns {idx: dict(rel, prom, drop_left, drop_right)} over the VALLEY
    candidates, before the prominence filter. `rel` is prom / max(interior prom)
    - the quantity `prominence_relative` is compared to - and is None for the
    boundary indices 0 and N-1, which _refine_extrema exempts from filtering.

    drop_left / drop_right are scipy's own two climbs out of the valley, in z
    units: z[left_base] - z[valley] and z[right_base] - z[valley]. scipy keeps
    only their MINIMUM as the prominence, so their difference is the discarded
    information (future_work.md item 20(e)(iii)).
    """
    data = np.asarray(z, dtype=float)
    N = len(data)
    peaks = _collapse_plateaux(argrelextrema(data, np.greater_equal)[0])
    valleys = _collapse_plateaux(argrelextrema(data, np.less_equal)[0])
    overlap = np.intersect1d(peaks, valleys)
    if len(overlap):
        peaks = peaks[~np.isin(peaks, overlap)]

    boundary = {int(i) for i in (0, N - 1) if i in set(valleys.tolist())}
    interior = np.array([int(i) for i in valleys if i not in boundary], dtype=int)

    out = {i: dict(rel=None, prom=None, drop_left=None, drop_right=None) for i in boundary}
    if len(interior):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prom, lb, rb = peak_prominences(-data, interior)
        mx = prom.max() if len(prom) else 0.0
        for i, p, l, r in zip(interior, prom, lb, rb):
            out[int(i)] = dict(
                rel=(float(p) / mx) if mx > 0.0 else None,
                prom=float(p),
                drop_left=float(data[int(l)] - data[int(i)]),
                drop_right=float(data[int(r)] - data[int(i)]),
            )
    return out


# --------------------------------------------------------------------------- #
# phase bookkeeping
# --------------------------------------------------------------------------- #
def runs_of(names):
    out, prev, start = [], None, 0
    for i, n in enumerate(names):
        if n != prev:
            if prev is not None:
                out.append((prev, start, i - 1))
            prev, start = n, i
    out.append((prev, start, len(names) - 1))
    return out


def label_runs(record):
    ph, n = record["phases"], record["n_steps"]
    out = []
    for k, p in enumerate(ph):
        s = p["start_idx"]
        e = (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph) else n - 1
        out.append((normalize_phase(p["phase"]), s, e, bool(p.get("unsure"))))
    return out


def overlaps(a, b):
    """Steps shared by two inclusive index ranges."""
    return max(0, min(a[1], b[1]) - max(a[0], b[0]) + 1)


def pair_by_overlap(det_matures, lab_mature):
    """item19_core's rule, reproduced so measurement C counts the same cases.

    Largest-overlap pairing, falling back to nearest midpoint when nothing
    overlaps so a Delta is still reported rather than silently dropped.
    """
    if not det_matures or lab_mature is None:
        return None, None
    ls, le = lab_mature
    best, best_ov = None, -1
    for (ds, de) in det_matures:
        ov = min(de, le) - max(ds, ls) + 1
        if ov > best_ov:
            best, best_ov = (ds, de), ov
    if best_ov <= 0:
        mid = (ls + le) / 2
        best = min(det_matures, key=lambda b: abs((b[0] + b[1]) / 2 - mid))
    return best, max(best_ov, 0)


# --------------------------------------------------------------------------- #
def analyse(sid, values, record, pv, gp):
    """Run the detector once and reduce the series to the facts stage 1 needs."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        df = get_periods(vort, **gp)

    z = np.asarray(df["z"].values, dtype=float)
    N = len(z)
    z_min, z_max = float(z.min()), float(z.max())
    idx = df.index
    pos = {lab: i for i, lab in enumerate(idx)}

    periods = [normalize_phase(str(x)) for x in df["periods"]]
    det_blocks = [(a, b) for p, a, b in runs_of(periods) if p == "mature"]
    lab = label_runs(record) if record else []
    lab_matures = [(a, b, u) for p, a, b, u in lab if p == "mature"]

    vfacts = valley_facts(z)

    # The valleys and peaks that SURVIVED the prominence filter - exactly the
    # ones find_mature_stage iterates over.
    surv_valleys = [lab_ for lab_ in idx[df["z_peaks_valleys"] == "valley"]]
    surv_peaks = [lab_ for lab_ in idx[df["z_peaks_valleys"] == "peak"]]

    rows, defects = [], []
    for v_lab in surv_valleys:
        vi = pos[v_lab]
        prev_p = [p for p in surv_peaks if p < v_lab]
        next_p = [p for p in surv_peaks if p > v_lab]
        if not prev_p or not next_p:
            continue                       # find_mature_stage skips these
        prev_p, next_p = prev_p[-1], next_p[0]

        z_v = float(df.at[v_lab, "z"])
        amp_prev = float(df.at[prev_p, "z"]) - z_v
        amp_next = float(df.at[next_p, "z"]) - z_v
        maf = gp["mature_amplitude_fraction"]
        level_prev = float(df.at[prev_p, "z"]) - maf * amp_prev
        level_next = float(df.at[next_p, "z"]) - maf * amp_next

        # ---- ACTIVE check of the two latent defects of _amplitude_mature_bounds.
        # Not "did it raise?": the :159/:160 one never raises. Both are tested by
        # recomputing the condition that would trigger them.
        #   :152  violations_prev[-1] + 1 == len(seg_prev)  -> IndexError (loud)
        #         <=> the valley itself violates level_prev <=> amp_prev < 0
        #   :159  violations_next[0] - 1 == -1 -> index[-1], i.e. mature_end is
        #         silently set to next_z_peak (a maximally wrong window)
        #         <=> the valley itself violates level_next <=> amp_next < 0
        if z_v > level_prev:
            defects.append(dict(series=sid, valley=vi, defect="152", amp=amp_prev))
        if z_v > level_next:
            defects.append(dict(series=sid, valley=vi, defect="160", amp=amp_next))

        m_start, m_end = _amplitude_mature_bounds(df, prev_p, v_lab, next_p, maf)
        win = (pos[m_start], pos[m_end])

        # Which FINAL mature block, if any, this valley's window produced.
        hits = [(b, overlaps(win, b)) for b in det_blocks if overlaps(win, b) > 0]
        if not hits:
            continue                       # window cleared downstream: no block
        block, _ = max(hits, key=lambda t: t[1])

        lab_ov = max((overlaps(block, (a, b)) for a, b, _ in lab_matures), default=0)
        vf = vfacts.get(vi, dict(rel=None, prom=None, drop_left=None, drop_right=None))
        rng = z_max - z_min
        rows.append(dict(
            series=sid,
            valley_idx=vi,
            z_valley=z_v,
            z_min=z_min,
            z_max=z_max,
            D1=(z_max - z_v) / rng if rng > 0 else float("nan"),
            D2=(abs(z_v) / abs(z_min)) if z_min != 0 else float("nan"),
            prominence_relative=vf["rel"],
            prominence_abs=vf["prom"],
            drop_left=vf["drop_left"],
            drop_right=vf["drop_right"],
            drop_asymmetry=(None if vf["drop_left"] is None
                            else vf["drop_left"] - vf["drop_right"]),
            amp_prev_peak=amp_prev,
            amp_next_peak=amp_next,
            window_start=win[0],
            window_end=win[1],
            block_start=block[0],
            block_end=block[1],
            block_len=block[1] - block[0] + 1,
            label_overlap=lab_ov,
            classification="TRUE" if lab_ov >= 1 else "SPURIOUS",
            n_blocks_in_series=len(det_blocks),
            n_labelled_matures=len(lab_matures),
        ))

    # --- measurement C bookkeeping: is the generating valley the deepest one?
    first_lab = (lab_matures[0][0], lab_matures[0][1]) if lab_matures else None
    paired, _ = pair_by_overlap(det_blocks, first_lab)
    matches_label = False
    d_start = d_end = None
    if paired and first_lab:
        d_start, d_end = paired[0] - first_lab[0], paired[1] - first_lab[1]
        matches_label = abs(d_start) <= MARGIN and abs(d_end) <= MARGIN

    gen_for_paired = None
    if paired:
        cands = [r for r in rows if (r["block_start"], r["block_end"]) == paired]
        if cands:
            gen_for_paired = min(cands, key=lambda r: r["z_valley"])

    all_valley_pos = sorted(vfacts)
    deepest_all = min(all_valley_pos, key=lambda i: z[i]) if all_valley_pos else None
    surv_pos = [pos[v] for v in surv_valleys]
    deepest_surv = min(surv_pos, key=lambda i: z[i]) if surv_pos else None
    argmin_series = int(np.argmin(z))

    return dict(
        series=sid, n=N, rows=rows, defects=defects,
        z_min=z_min, z_max=z_max, z_mean=float(z.mean()),
        z_unfil_mean=float(np.asarray(df["z_unfil"].values, dtype=float).mean()),
        det_blocks=det_blocks, lab_matures=lab_matures,
        sha_ok=(series_sha256(values) == record["series_sha256"]) if record else None,
        matches_label=matches_label, paired=paired, d_start=d_start, d_end=d_end,
        gen_for_paired=gen_for_paired,
        deepest_valley_all=deepest_all, deepest_valley_surviving=deepest_surv,
        argmin_series=argmin_series,
        n_valleys_no_neighbour=len(surv_valleys) - len(
            [v for v in surv_valleys
             if any(p < v for p in surv_peaks) and any(p > v for p in surv_peaks)]),
    )


# --------------------------------------------------------------------------- #
def main():
    import hashlib
    import scipy

    pv, gp = load_config()
    sha = hashlib.sha256(CONFIG.read_bytes()).hexdigest()
    split = read_split()
    train = set(split["train"])
    labels = read_labels()

    real = {s: v for s, v in load_real_series().items() if s in train}
    synth = {s: v for s, v in load_synthetic_series()[0].items() if s in train}

    print(f"numpy {np.__version__}  scipy {scipy.__version__}  pandas {pd.__version__}")
    print(f"params-11 sha256 {sha}")
    print(f"real train {len(real)}   synthetic train {len(synth)}")
    print(f"mature_amplitude_fraction = {gp['mature_amplitude_fraction']}")

    res_real = {s: analyse(s, v, labels.get(s), pv, gp) for s, v in sorted(real.items())}
    res_syn = {s: analyse(s, v, labels.get(s), pv, gp) for s, v in sorted(synth.items())}

    OUT.mkdir(parents=True, exist_ok=True)
    rows = [r for f in res_real.values() for r in f["rows"]]
    cols = list(rows[0].keys())
    with (OUT / "depth_table.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    payload = dict(
        numpy=np.__version__, scipy=scipy.__version__, pandas=pd.__version__,
        config_sha256=sha,
        real_train=sorted(real), synthetic_train=sorted(synth),
        series={s: {k: v for k, v in f.items() if k not in ("rows", "gen_for_paired")}
                for s, f in {**res_real, **res_syn}.items()},
        rows=rows,
    )
    (OUT / "measurements.json").write_text(json.dumps(payload, indent=1, default=str))
    print(f"\nwrote {OUT/'depth_table.csv'} ({len(rows)} generating valleys)")
    return res_real, res_syn, rows, pv, gp, sha


if __name__ == "__main__":
    main()
