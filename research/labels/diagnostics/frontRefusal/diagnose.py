#!/usr/bin/env python
"""Front "incipient refusal", stage 1 — why the plateau rule refuses, on TRAIN.

Diagnostic only. Nothing under `cyclophaser/` or `tests/` is written, no
parameter is changed, and the TEST split is never loaded into the detector
(`_assert_train_only` raises before any detection runs).

How the statistics are obtained
-------------------------------
Everything decisive is read out of the REAL run, not recomputed from a
reimplementation of the pipeline. `find_incipient_period` is wrapped for the
duration of the run: the wrapper records the `periods` column exactly as the
detector handed it over (i.e. BEFORE the unconditional `fillna('incipient')`
inside that function), then delegates to the untouched package function. The
plateau profile `rel` and the boundary are then computed by calling the
package's own `_incipient_plateau_rel` / `_incipient_plateau_boundary` on that
same captured frame with the same kwargs, and the result is ASSERTED against
what `get_periods` actually returned before any attribution is printed.

Why the pre-fillna `periods[0]` matters
---------------------------------------
`find_incipient_period` fills every NaN in `periods` with 'incipient' before the
plateau rule runs. So a boundary of 0 — the plateau rule declining — does not by
itself mean the output has no incipient phase: if the frame arrived with a
leading run of NaN, that run is labelled 'incipient' by the fillna and the
evaluator counts it. A REFUSAL is therefore `boundary == 0` AND `periods[0]`
non-NaN on arrival. The two are separated here.
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

from labels_core import (  # noqa: E402
    load_real_series, load_synthetic_series, read_labels, read_split,
    series_sha256,
)
from evaluate_against_labels import (  # noqa: E402
    detected_incipient_end, detected_phase_starts, load_config,
)

CONFIG = REPO / "research/labels/configs/cyclophaser_params-13.yaml"
OUT = Path(__file__).resolve().parent

# The six refusals front D's stage-0 census named (item 25). Re-derived here,
# not trusted: the derived set is asserted against this list.
FRONT_D_C2 = ["20160587", "20160735", "20171179", "20180628", "20181046", "20202023"]


def _assert_train_only(ids, split) -> None:
    test = set(split["test"])
    leaked = sorted(set(ids) & test)
    if leaked:
        raise SystemExit(f"REFUSING TO RUN: test-split ids reached the detector: {leaked}")


def run_one(values: pd.Series, pv: dict, gp: dict) -> dict:
    """One series through the real detector, with the plateau decision read back."""
    # `cyclophaser/__init__.py` rebinds the name `determine_periods` to a
    # FUNCTION, so `import cyclophaser.determine_periods as dp` resolves to
    # that function, not the module. Go through sys.modules instead.
    import importlib
    dp = importlib.import_module("cyclophaser.determine_periods")
    from cyclophaser.find_stages import (
        _incipient_plateau_boundary, _incipient_plateau_rel, find_incipient_period,
    )

    captured = {}

    def spy(df, **args):
        # pre-fillna snapshot; .copy() because the real function mutates in place
        captured["periods_in"] = df["periods"].copy()
        captured["df"] = df.copy()
        captured["args"] = dict(args)
        return find_incipient_period(df, **args)

    real_fn = dp.find_incipient_period
    dp.find_incipient_period = spy
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = dp.process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            res = dp.get_periods(vort, **gp)
    finally:
        dp.find_incipient_period = real_fn

    args = captured["args"]
    signal = args.get("incipient_plateau_signal", "derivative")
    tau = float(args.get("incipient_plateau_tau", 0.20))
    crossing = args.get("incipient_plateau_crossing", "single")
    k = int(args.get("incipient_plateau_k", 3))

    rel = _incipient_plateau_rel(
        captured["df"], signal,
        args.get("incipient_smooth_window", 0),
        args.get("incipient_smooth_polyorder", 3))
    boundary = int(_incipient_plateau_boundary(rel, tau, crossing, k))

    n_det = detected_incipient_end(res["periods"])
    n_det = 0 if n_det is None else int(n_det)

    periods_in = captured["periods_in"]
    p0_in = periods_in.iloc[0]
    p0_isna = bool(pd.isna(p0_in))
    lead_nan = 0
    for v in periods_in:
        if pd.isna(v):
            lead_nan += 1
        else:
            break

    # --- the replay must agree with what the detector actually produced ---
    if boundary > 0:
        replay_ok = (n_det == boundary)
    elif p0_isna:
        replay_ok = (n_det == lead_nan)          # the fillna path, not the plateau
    else:
        replay_ok = (n_det == 0)                 # a genuine refusal
    if not replay_ok:
        raise AssertionError(
            f"replay disagrees with get_periods: boundary={boundary} "
            f"p0_isna={p0_isna} lead_nan={lead_nan} n_det={n_det}")

    # --- the decisive statistics, per candidate refusal path ---
    above = rel >= tau
    n = int(above.size)
    # R1: is the first sustained run at index 0? -> min(rel[0:k]) >= tau
    head_min = float(np.min(rel[:k])) if n >= k else None
    # R2: is there a sustained run anywhere? -> max_i min(rel[i:i+k])
    if n >= k:
        wins = np.lib.stride_tricks.sliding_window_view(rel, k)
        win_min = wins.min(axis=1)
        best_run = float(win_min.max())
        best_run_at = int(win_min.argmax())
    else:
        best_run = best_run_at = None
    amax_abs = float(np.nanmax(np.abs(
        np.asarray(captured["df"]["dz"], dtype=float) if signal == "derivative"
        else np.gradient(np.asarray(captured["df"]["z_unfil"], dtype=float)))))

    raw = vort["zeta"].values
    filt = vort["filtered_vorticity"].values
    d_raw = float(raw[1] - raw[0])
    d_filt = float(filt[1] - filt[0])
    dz_t0 = float(np.asarray(captured["df"]["dz"], dtype=float)[0])
    flip = (d_raw > 0) != (d_filt > 0) if (d_raw != 0 and d_filt != 0) else None

    return {
        "n_steps": n,
        "N_det": n_det,
        "boundary": boundary,
        "tau": tau, "k": k, "crossing": crossing, "signal": signal,
        "periods_in_0": None if p0_isna else str(p0_in),
        "leading_nan_in": lead_nan,
        "refusal": bool(boundary == 0 and not p0_isna),
        "fillna_incipient": bool(boundary == 0 and p0_isna),
        "head_min": head_min,
        "best_run": best_run, "best_run_at": best_run_at,
        "rel_head": [float(x) for x in rel[:12]],
        "probe_amax": amax_abs,
        "d_raw_t0": d_raw, "d_filt_t0": d_filt, "dz_t0": dz_t0,
        "defect_I": flip,
        "detected_sequence": [[p, int(i)] for p, i in detected_phase_starts(res["periods"])],
        "rel": [float(x) for x in rel],
    }


def refusal_path(r: dict) -> str:
    """R1 / R2 / R3 / R4, or '-' when the rule did not refuse."""
    if r["boundary"] > 0:
        return "-"
    if r["n_steps"] < r["k"]:
        return "R3"
    if r["probe_amax"] <= 0 or not np.isfinite(r["probe_amax"]):
        return "R4"
    if r["head_min"] is not None and r["head_min"] >= r["tau"]:
        return "R1"
    return "R2"


def label_incipient(rec):
    kind = rec["verdict"]["kind"]
    if kind == "boundary":
        return int(rec["verdict"]["incipient_end_idx"]), int(rec["tolerance_idx"]), kind
    if kind == "none":
        return 0, int(rec["tolerance_idx"]), kind
    return None, int(rec["tolerance_idx"]), kind


def main() -> int:
    split = read_split()
    train = list(split["train"])
    sources = split["source"]
    records = read_labels()
    real = load_real_series()
    synth, _ = load_synthetic_series()
    series = {**real, **synth}

    _assert_train_only(train, split)

    print(f"config: research/labels/configs/{CONFIG.name}")
    import hashlib
    print(f"config sha256: {hashlib.sha256(CONFIG.read_bytes()).hexdigest()}")
    pv, gp = load_config(CONFIG)
    print(f"process_vorticity kwargs: {pv}")
    print(f"get_periods kwargs: {gp}\n")

    # every scored series verified against the hash its label was written against
    bad = [sid for sid in sorted(train)
           if records[sid].get("series_sha256") != series_sha256(series[sid])]
    if bad:
        raise SystemExit(f"series_sha256 mismatch on {bad}")
    print(f"series_sha256 verified: {len(train)}/{len(train)} train labels match\n")

    rows = []
    for sid in sorted(train):
        if sources[sid] != "real":
            continue                      # this front is about the real tracks
        r = run_one(series[sid], pv, gp)
        n_lab, tol, kind = label_incipient(records[sid])
        r.update(id=sid, N_lab=n_lab, tolerance_idx=tol, label_kind=kind,
                 R=refusal_path(r))
        rows.append(r)
    print(f"replay verified against get_periods on all {len(rows)} real train series\n")

    def cell(r):
        if r["label_kind"] == "ambiguous":
            return "AMB"
        lab_yes = r["N_lab"] > 0
        det_yes = r["N_det"] > 0
        return {(True, True): "TP", (False, True): "FP",
                (True, False): "REFUSAL", (False, False): "TN"}[(lab_yes, det_yes)]

    for r in rows:
        r["cell"] = cell(r)
    groups = {c: [r for r in rows if r["cell"] == c]
              for c in ("TP", "FP", "REFUSAL", "TN", "AMB")}

    print("=" * 96)
    print("2x2 on the 33 non-ambiguous real TRAIN series (+ 2 ambiguous)")
    print("=" * 96)
    for c in ("TP", "FP", "REFUSAL", "TN", "AMB"):
        print(f"  {c:<8} {len(groups[c]):>3}  {[r['id'] for r in groups[c]]}")

    derived = sorted(r["id"] for r in groups["REFUSAL"])
    assert derived == sorted(FRONT_D_C2), f"refusal set moved: {derived}"
    print(f"\n  refusal set matches front D's C2 exactly: {derived}\n")

    hdr = (f"{'id':<11} {'cell':<8} {'n':>4} {'N_det':>6} {'N_lab':>6} {'tol':>4} "
           f"{'R':>3} {'bnd':>4} {'head_min':>9} {'best_run':>9} {'p_in[0]':<16} "
           f"{'lead_nan':>8} {'defI':>5}")
    print("=" * 120)
    print("PER-SERIES — real TRAIN, params-13")
    print("=" * 120)
    print(hdr)
    for r in sorted(rows, key=lambda x: (x["cell"] != "REFUSAL", x["id"])):
        hm = "—" if r["head_min"] is None else f"{r['head_min']:.6f}"
        br = "—" if r["best_run"] is None else f"{r['best_run']:.6f}"
        di = {True: "yes", False: "no", None: "n/a"}[r["defect_I"]]
        print(f"{r['id']:<11} {r['cell']:<8} {r['n_steps']:>4} {r['N_det']:>6} "
              f"{str('amb' if r['N_lab'] is None else r['N_lab']):>6} "
              f"{r['tolerance_idx']:>4} {r['R']:>3} {r['boundary']:>4} {hm:>9} "
              f"{br:>9} {str(r['periods_in_0']):<16} {r['leading_nan_in']:>8} {di:>5}")

    (OUT / "refusal.json").write_text(json.dumps(
        {"config": CONFIG.name, "rows": rows}, indent=2))
    # repo-relative: a committed .txt must not embed an absolute local path
    print(f"\nwrote {(OUT / 'refusal.json').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
