#!/usr/bin/env python
"""Item 19/20 part 1 - shared read-only machinery. No package code is modified.

Everything downstream (stage 1 description, stage 2 grid) goes through
`facts_for_config`, so the reference run and every grid cell are produced by
literally the same code path and differ only in the parameter dict.

TRAIN SPLIT ONLY. `read_split()["test"]` is never read by this module.
"""
from __future__ import annotations

import inspect
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
from cyclophaser.determine_periods import (get_periods, process_vorticity,
                                           _collapse_plateaux)
from scipy.signal import argrelextrema, peak_prominences

CONFIG = REPO / "research" / "labels" / "configs" / "cyclophaser_params-10.yaml"
OUT = REPO / "research" / "labels" / "diagnostics" / "item19"

PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")

MARGIN = 6            # item 17(d): the asserted boundary margin is a fixed 6


def load_config(path=CONFIG):
    doc = yaml.safe_load(Path(path).read_text()) or {}
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


# --------------------------------------------------------------------------- #
# extrema, with the relative prominence the detector actually compares
# --------------------------------------------------------------------------- #
def extrema_with_prominence(z):
    """z extrema before the prominence filter, each with its RELATIVE prominence.

    Mirrors determine_periods.find_peaks_valleys / _refine_extrema:
      * candidates from argrelextrema with plateau collapse, valleys win overlaps
        (determine_periods.py:110-131)
      * prominence from scipy.signal.peak_prominences on `data` for peaks and
        `-data` for valleys - two SEPARATE populations (determine_periods.py:135-136,
        :188)
      * relative = prom / max(prom over the interior candidates of that type)
        (determine_periods.py:203-208)
      * indices 0 and N-1 are exempt from filtering (determine_periods.py:180-181)
        and get rel = None.
    Returns {'peak': {idx: rel_or_None}, 'valley': {idx: rel_or_None}}.
    """
    data = np.asarray(z, dtype=float)
    N = len(data)
    peaks = _collapse_plateaux(argrelextrema(data, np.greater_equal)[0])
    valleys = _collapse_plateaux(argrelextrema(data, np.less_equal)[0])
    overlap = np.intersect1d(peaks, valleys)
    if len(overlap):
        peaks = peaks[~np.isin(peaks, overlap)]

    out = {}
    for kind, cand, signed in (("peak", peaks, data), ("valley", valleys, -data)):
        boundary = {int(i) for i in (0, N - 1) if i in set(cand.tolist())}
        interior = np.array([int(i) for i in cand if i not in boundary], dtype=int)
        rel = {i: None for i in boundary}
        if len(interior):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                prom = peak_prominences(signed, interior)[0]
            mx = prom.max() if len(prom) else 0.0
            for i, p in zip(interior, prom):
                rel[int(i)] = (float(p) / mx) if mx > 0.0 else None
        out[kind] = rel
    return out


def surviving(rel_map, prominence_relative):
    """Indices that survive the relative filter, for one extremum type."""
    return sorted(i for i, r in rel_map.items()
                  if r is None or r >= prominence_relative)


# --------------------------------------------------------------------------- #
# phase bookkeeping
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
    ph, n = record["phases"], record["n_steps"]
    out = []
    for k, p in enumerate(ph):
        s = p["start_idx"]
        e = (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph) else n - 1
        out.append((normalize_phase(p["phase"]), s, e,
                    p.get("tolerance_idx"), bool(p.get("unsure"))))
    return out


def leading_incipient(runs):
    """Detector's incipient boundary: the phase is [0, N). None if step 0 is not
    incipient - same reading as evaluate_against_labels.py."""
    return runs[0][2] + 1 if runs and runs[0][0] == "incipient" else None


def pair_by_overlap(det_matures, lab_mature):
    """Pick the detected mature block with the largest overlap with the label.

    Overlap pairing (not order pairing): across a sequence mismatch, pairing the
    k-th detected mature with the k-th labelled one compares two different
    transitions. Falls back to the nearest block by midpoint when nothing
    overlaps, so a Delta is still reported rather than silently dropped.
    """
    if not det_matures or lab_mature is None:
        return None, None
    ls, le = lab_mature
    best, best_ov = None, -1
    for (ds, de) in det_matures:
        ov = min(de, le) - max(ds, ls) + 1
        if ov > best_ov:
            best, best_ov = (ds, de), ov
    if best_ov <= 0:                       # no overlap: nearest midpoint
        mid = (ls + le) / 2
        best = min(det_matures, key=lambda b: abs((b[0] + b[1]) / 2 - mid))
    return best, max(best_ov, 0)


# --------------------------------------------------------------------------- #
def load_train_series():
    split = read_split()
    train = set(split["train"])
    real = {s: v for s, v in load_real_series().items() if s in train}
    synth = {s: v for s, v in load_synthetic_series()[0].items() if s in train}
    return real, synth


def facts_for_config(series, labels, pv, gp, want_z=False):
    """Run the detector on every series and reduce to the facts the gate needs."""
    facts = {}
    for sid, values in series.items():
        rec = labels.get(sid)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
                res = get_periods(vort, **gp)
        except Exception as exc:
            # The detector itself raised. Recorded, never swallowed: a cell that
            # cannot be computed on all 47 series cannot satisfy a gate defined
            # over all 47, so it is carried through as a total failure and named
            # in the report. See mature_amplitude_fraction=1.00.
            facts[sid] = dict(id=sid, n=len(values), error=f"{type(exc).__name__}: {exc}",
                              det_seq=[], lab_seq=[], det_matures=[], n_det_mature=0,
                              lab_mature=None, paired=None, overlap=None,
                              incip_end="ERROR", sha_ok=None, seq_match=False,
                              d_start=None, d_end=None, abs_sum=None,
                              matches_label=False)
            continue
        runs = phase_runs(res["periods"])
        det_mat = [(a, b) for p, a, b in runs if p == "mature"]
        lab = label_runs(rec) if rec else []
        lab_mat = [(a, b) for p, a, b, _, _ in lab if p == "mature"]
        first_lab = lab_mat[0] if lab_mat else None
        paired, ov = pair_by_overlap(det_mat, first_lab)

        f = dict(
            id=sid,
            n=len(values),
            det_seq=[p for p, _, _ in runs],
            lab_seq=[p for p, _, _, _, _ in lab],
            det_matures=det_mat,
            n_det_mature=len(det_mat),
            lab_mature=first_lab,
            paired=paired,
            overlap=ov,
            incip_end=leading_incipient(runs),
            sha_ok=(series_sha256(values) == rec["series_sha256"]) if rec else None,
            error=None,
        )
        f["seq_match"] = (f["det_seq"] == f["lab_seq"])
        if paired and first_lab:
            f["d_start"] = paired[0] - first_lab[0]
            f["d_end"] = paired[1] - first_lab[1]
            f["abs_sum"] = abs(f["d_start"]) + abs(f["d_end"])
            f["matches_label"] = (abs(f["d_start"]) <= MARGIN and abs(f["d_end"]) <= MARGIN)
        else:
            f["d_start"] = f["d_end"] = f["abs_sum"] = None
            f["matches_label"] = False
        if want_z:
            f["z"] = np.asarray(vort.vorticity_smoothed2.values, dtype=float)
            f["z_unfil"] = np.asarray(vort.zeta.values, dtype=float)
            f["periods"] = [normalize_phase(str(x)) for x in res["periods"]]
            f["lab_runs"] = lab
        facts[sid] = f
    return facts
