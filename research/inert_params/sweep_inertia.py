"""FRENTE F(iii) — automated inertia sweep for the calibration app's parameters.

For each (parameter, base_config) pair declared in SWEEP_PLAN, this sweeps the
parameter across its full app.py UI range, over all 51 tracks in
tests/calibration_data, and checks whether `df_result["periods"]` (the
per-timestep phase label array `determine_periods` actually produces) EVER
changes. A parameter is INERT under a base config iff every swept value
produces byte-identical `periods` arrays, on every track, as the base config's
own default value.

This is a MEASUREMENT tool: it calls `process_vorticity` / `get_periods`
directly (the same functions app.py's cached helpers wrap), bypassing
Streamlit entirely. It changes nothing in cyclophaser/ or in the app; it only
reads and reports.

Run: python research/inert_params/sweep_inertia.py
Output: research/inert_params/inertia_matrix.csv (one row per swept value that
produced ANY change, empty per (parameter, base_config) group iff fully inert)
plus a summary printed to stdout and written to
research/inert_params/sweep_summary.txt.
"""
from __future__ import annotations

import csv
import sys
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))

import numpy as np
import pandas as pd

from cyclophaser.determine_periods import get_periods, process_vorticity

CALIB = REPO_ROOT / "tests" / "calibration_data"
TRACKS = sorted(p.stem for p in CALIB.glob("*.csv"))
OUT_DIR = Path(__file__).resolve().parent


def _series(track_id: str) -> pd.Series:
    return pd.read_csv(CALIB / f"{track_id}.csv", sep=";", index_col="time",
                       parse_dates=True)["min_max_zeta_850"]


# ══════════════════════════════════════════════════════════════════════════
# Base configs — named combinations of the "mode" switches (use_filter,
# smoothing on/off, incipient_method, crossing, signal, mature_method, the
# optional-feature enable checkboxes). Everything not listed keeps the
# app.py UI default (see tools/calibration_app/app.py _DEFAULTS).
# ══════════════════════════════════════════════════════════════════════════

PV_DEFAULTS = dict(
    use_filter=True, cutoff_low=168, cutoff_high=48,
    use_smoothing="auto", use_smoothing_twice="auto",
    replace_endpoints_with_lowpass=0, savgol_polynomial=3,
    boundary_padding="reflect",
)

PHASE_DEFAULTS = dict(
    threshold_intensification_length=0.075,
    threshold_intensification_gap=0.075,
    threshold_mature_distance=0.125,
    threshold_mature_length=0.030,
    threshold_decay_length=0.075,
    threshold_decay_gap=0.075,
    threshold_incipient_length=0.400,
    prominence=None,
    prominence_relative=None,
    distance=None,
    length_scale="global",
    mature_method="derivative",
    mature_amplitude_fraction=0.90,
    decay_tail_amplitude_fraction=None,
    incipient_method="geometric",
    incipient_plateau_tau=0.20,
    incipient_plateau_signal="derivative",
    incipient_plateau_crossing="single",
    incipient_plateau_k=3,
    incipient_smooth_window=0,
    incipient_smooth_polyorder=3,
)

BASE_CONFIGS = {
    "default": dict(pv={}, phase={}),
    "nofilter": dict(pv=dict(use_filter=False), phase={}),
    "nosmoothing": dict(pv=dict(use_smoothing=False, use_smoothing_twice=False), phase={}),
    "manual_sm": dict(pv=dict(use_smoothing=17), phase={}),
    "manual_sm2": dict(pv=dict(use_smoothing_twice=17), phase={}),
    "mature_derivative": dict(pv={}, phase=dict(mature_method="derivative")),
    "mature_amplitude": dict(pv={}, phase=dict(mature_method="amplitude")),
    "plateau_single_derivative": dict(pv={}, phase=dict(
        incipient_method="plateau", incipient_plateau_crossing="single",
        incipient_plateau_signal="derivative")),
    "plateau_single_vorticity": dict(pv={}, phase=dict(
        incipient_method="plateau", incipient_plateau_crossing="single",
        incipient_plateau_signal="vorticity")),
    "plateau_sustained_derivative": dict(pv={}, phase=dict(
        incipient_method="plateau", incipient_plateau_crossing="sustained",
        incipient_plateau_signal="derivative")),
    "plateau_sustained_vorticity": dict(pv={}, phase=dict(
        incipient_method="plateau", incipient_plateau_crossing="sustained",
        incipient_plateau_signal="vorticity")),
    "extrema_prominence_on": dict(pv={}, phase=dict(prominence_relative=0.10)),
    "extrema_distance_on": dict(pv={}, phase=dict(distance=3)),
    "decay_tail_on": dict(pv={}, phase=dict(decay_tail_amplitude_fraction=0.05)),
}


def _frange(lo, hi, step):
    """Inclusive float range on the same grid app.py's st.slider uses."""
    n = round((hi - lo) / step)
    return [round(lo + i * step, 10) for i in range(n + 1)]


# ══════════════════════════════════════════════════════════════════════════
# Swept parameters: name -> (kind, kwarg, values). kind "pv" feeds
# process_vorticity; kind "phase" feeds get_periods. Ranges/steps/defaults are
# copied verbatim from the st.slider/st.number_input/st.radio/st.selectbox
# calls in tools/calibration_app/app.py.
# ══════════════════════════════════════════════════════════════════════════

PARAMS = {
    "cutoff_low":  ("pv", "cutoff_low", list(range(48, 337, 24))),
    "cutoff_high": ("pv", "cutoff_high", list(range(12, 97, 6))),
    "boundary_padding": ("pv", "boundary_padding", ["zero", "reflect", "edge"]),
    # UI range starts at 3, but window=3 with the default savgol_poly=3 is
    # mathematically invalid (scipy requires polyorder < window_length) --
    # not an inertia question, so the sweep starts one step past it.
    "sm_val":  ("pv", "use_smoothing", list(range(5, 62, 2))),
    "sm2_val": ("pv", "use_smoothing_twice", list(range(5, 62, 2))),
    "replace_endpoints": ("pv", "replace_endpoints_with_lowpass", list(range(0, 49, 1))),
    "savgol_poly": ("pv", "savgol_polynomial", [2, 3, 4, 5]),
    "use_filter": ("pv", "use_filter", [True, False]),

    "thr_int_len": ("phase", "threshold_intensification_length", _frange(0.01, 0.30, 0.005)),
    "thr_dec_len": ("phase", "threshold_decay_length", _frange(0.01, 0.30, 0.005)),
    "thr_int_gap": ("phase", "threshold_intensification_gap", _frange(0.01, 0.30, 0.005)),
    "thr_dec_gap": ("phase", "threshold_decay_gap", _frange(0.01, 0.30, 0.005)),
    "thr_mat_len": ("phase", "threshold_mature_length", _frange(0.005, 0.15, 0.005)),
    "thr_mat_dist": ("phase", "threshold_mature_distance", _frange(0.05, 0.30, 0.005)),
    "thr_inc_len": ("phase", "threshold_incipient_length", _frange(0.1, 0.6, 0.01)),
    "mature_amplitude_fraction": ("phase", "mature_amplitude_fraction", _frange(0.05, 1.00, 0.01)),
    "length_scale": ("phase", "length_scale", ["global", "local"]),
    "mature_method": ("phase", "mature_method", ["derivative", "amplitude"]),

    "incipient_plateau_tau": ("phase", "incipient_plateau_tau", _frange(0.01, 0.60, 0.01)),
    "incipient_plateau_signal": ("phase", "incipient_plateau_signal", ["derivative", "vorticity"]),
    "incipient_plateau_crossing": ("phase", "incipient_plateau_crossing", ["single", "sustained"]),
    "incipient_plateau_k": ("phase", "incipient_plateau_k", list(range(1, 26))),
    "incipient_smooth_window": ("phase", "incipient_smooth_window", list(range(0, 22))),
    "incipient_smooth_polyorder": ("phase", "incipient_smooth_polyorder", list(range(1, 8))),

    "extrema_prominence_relative": ("phase", "prominence_relative", _frange(0.00, 0.50, 0.01)),
    "extrema_distance": ("phase", "distance", list(range(2, 31))),
    "decay_tail_amplitude_fraction": ("phase", "decay_tail_amplitude_fraction", _frange(0.01, 0.50, 0.01)),
}

# (parameter, [base_config names]) — which base configs each parameter is
# swept under. See PREDICTION.md for the declared expectation of each pair.
SWEEP_PLAN = [
    ("cutoff_low", ["default", "nofilter"]),
    ("cutoff_high", ["default", "nofilter"]),
    ("boundary_padding", ["default", "nofilter"]),
    ("sm_val", ["manual_sm"]),
    ("sm2_val", ["manual_sm2"]),
    ("replace_endpoints", ["default"]),
    ("savgol_poly", ["default", "nosmoothing"]),
    ("use_filter", ["default"]),

    ("thr_int_len", ["default"]),
    ("thr_dec_len", ["default"]),
    ("thr_int_gap", ["default"]),
    ("thr_dec_gap", ["default"]),
    ("thr_mat_len", ["mature_derivative", "mature_amplitude"]),
    ("thr_mat_dist", ["mature_derivative", "mature_amplitude"]),
    ("thr_inc_len", ["default", "plateau_single_derivative"]),
    ("mature_amplitude_fraction", ["mature_amplitude", "mature_derivative"]),
    ("length_scale", ["default"]),
    ("mature_method", ["default"]),

    ("incipient_plateau_tau", ["default", "plateau_single_derivative"]),
    ("incipient_plateau_signal", ["default", "plateau_single_derivative"]),
    ("incipient_plateau_crossing", ["default", "plateau_single_derivative"]),
    ("incipient_plateau_k", [
        "default", "plateau_single_derivative", "plateau_single_vorticity",
        "plateau_sustained_derivative", "plateau_sustained_vorticity",
    ]),
    ("incipient_smooth_window", [
        "default", "plateau_single_derivative", "plateau_single_vorticity",
    ]),
    ("incipient_smooth_polyorder", [
        "default", "plateau_single_derivative", "plateau_single_vorticity",
    ]),

    ("extrema_prominence_relative", ["extrema_prominence_on"]),
    ("extrema_distance", ["extrema_distance_on"]),
    ("decay_tail_amplitude_fraction", ["decay_tail_on"]),
]

# The 5 cases gate (a) requires the sweep to self-rediscover as INERT.
KNOWN_INERT_CASES = [
    ("incipient_plateau_tau", "default"),
    ("incipient_plateau_signal", "default"),
    ("incipient_plateau_crossing", "default"),
    ("incipient_plateau_k", "default"),
    ("incipient_smooth_window", "default"),
    ("incipient_smooth_polyorder", "default"),
    ("incipient_plateau_k", "plateau_single_derivative"),
    ("incipient_plateau_k", "plateau_single_vorticity"),
    ("incipient_smooth_window", "plateau_single_derivative"),
    ("incipient_smooth_polyorder", "plateau_single_derivative"),
    ("thr_inc_len", "plateau_single_derivative"),
    ("thr_mat_len", "mature_amplitude"),
    ("thr_mat_dist", "mature_amplitude"),
]


_VORT_CACHE: dict = {}


def _get_vort(track_id: str, pv_kwargs: dict):
    """process_vorticity is ~3x cheaper than get_periods but still the
    dominant fixed cost when the same pv_kwargs recur across many sweep
    entries (every "phase"-kind sweep under the same base config shares one
    vorticity dataset per track) -- cached globally across the whole run."""
    key = (track_id, tuple(sorted(pv_kwargs.items())))
    if key not in _VORT_CACHE:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _VORT_CACHE[key] = process_vorticity(
                pd.DataFrame({"zeta": _series(track_id)}), **pv_kwargs)
    return _VORT_CACHE[key]


def _run(track_id: str, pv_kwargs: dict, phase_kwargs: dict):
    """Returns (ok, result). A raised exception (e.g. an out-of-range
    savgol_poly/window combination the UI sliders can independently produce,
    unrelated to this front's inertia question) is reported as "not
    evaluable" for that single (track, value) point rather than crashing the
    whole sweep -- it is neither evidence of inertia nor of an effect."""
    try:
        vort = _get_vort(track_id, pv_kwargs)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = get_periods(vorticity=vort, plot=False, plot_steps=False, **phase_kwargs)
        return True, tuple(df["periods"].astype(str))
    except Exception as exc:  # noqa: BLE001 -- a measurement tool, not the package
        return False, str(exc)


def sweep_one(param_name: str, base_name: str) -> dict:
    kind, kwarg, values = PARAMS[param_name]
    base = BASE_CONFIGS[base_name]
    pv_base = {**PV_DEFAULTS, **base["pv"]}
    phase_base = {**PHASE_DEFAULTS, **base["phase"]}

    changed_tracks = set()
    n_changed_values = 0
    n_skipped = 0
    per_track_baseline = {}
    unevaluable_tracks = set()
    for track_id in TRACKS:
        pv_kwargs = dict(pv_base)
        phase_kwargs = dict(phase_base)
        if kind == "pv":
            pv_kwargs[kwarg] = values[0]
        else:
            phase_kwargs[kwarg] = values[0]
        ok, result = _run(track_id, pv_kwargs, phase_kwargs)
        if ok:
            per_track_baseline[track_id] = result
        else:
            unevaluable_tracks.add(track_id)

    for value in values[1:]:
        for track_id in TRACKS:
            if track_id in unevaluable_tracks:
                continue
            pv_kwargs = dict(pv_base)
            phase_kwargs = dict(phase_base)
            if kind == "pv":
                pv_kwargs[kwarg] = value
            else:
                phase_kwargs[kwarg] = value
            ok, result = _run(track_id, pv_kwargs, phase_kwargs)
            if not ok:
                n_skipped += 1
                continue
            if result != per_track_baseline[track_id]:
                changed_tracks.add(track_id)
                n_changed_values += 1

    # A parameter with EVERY track unevaluable at baseline has no evidence
    # either way -- reporting that as "inert" would be vacuously true, not a
    # measurement. Surfaced as inert=None so it cannot silently pass gate (a)
    # or be mistaken for a real finding in gate (b).
    if len(unevaluable_tracks) == len(TRACKS):
        inert = None
    else:
        inert = len(changed_tracks) == 0
    return {
        "parameter": param_name,
        "base_config": base_name,
        "kwarg": kwarg,
        "n_values_swept": len(values),
        "n_skipped_observations": n_skipped,
        "n_unevaluable_tracks": len(unevaluable_tracks),
        "inert": inert,
        "n_tracks_changed": len(changed_tracks),
        "changed_tracks": sorted(changed_tracks),
        "n_changed_observations": n_changed_values,
    }


def main():
    rows = []
    for param_name, base_names in SWEEP_PLAN:
        for base_name in base_names:
            print(f"sweeping {param_name!r} under base={base_name!r} "
                 f"({len(PARAMS[param_name][2])} values x {len(TRACKS)} tracks)...",
                 flush=True)
            result = sweep_one(param_name, base_name)
            rows.append(result)
            if result["inert"] is None:
                verdict = "UNEVALUABLE (every track errored at baseline)"
            else:
                verdict = "INERT" if result["inert"] else "not inert"
            print(f"  -> {verdict} "
                 f"(tracks changed: {result['n_tracks_changed']}/{len(TRACKS)})")

    csv_path = OUT_DIR / "inertia_matrix.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "base_config", "kwarg", "n_values_swept",
                         "inert", "n_tracks_changed", "n_changed_observations",
                         "n_skipped_observations", "n_unevaluable_tracks",
                         "changed_tracks"])
        for r in rows:
            writer.writerow([r["parameter"], r["base_config"], r["kwarg"],
                            r["n_values_swept"], r["inert"], r["n_tracks_changed"],
                            r["n_changed_observations"], r["n_skipped_observations"],
                            r["n_unevaluable_tracks"],
                            ";".join(r["changed_tracks"])])
    print(f"\nwrote {csv_path}")

    # Gate (a): self-test against the 5 known cases.
    lookup = {(r["parameter"], r["base_config"]): r["inert"] for r in rows}
    gate_a_failures = []
    for param_name, base_name in KNOWN_INERT_CASES:
        found_inert = lookup.get((param_name, base_name))
        if found_inert is not True:
            gate_a_failures.append((param_name, base_name, found_inert))

    summary_path = OUT_DIR / "sweep_summary.txt"
    with open(summary_path, "w") as f:
        f.write(f"Swept {len(rows)} (parameter, base_config) pairs over "
               f"{len(TRACKS)} tracks.\n\n")
        f.write("GATE (a) — known-inert self-test:\n")
        if gate_a_failures:
            f.write("  FAILED. The sweep did not detect inertia for:\n")
            for p, b, found in gate_a_failures:
                f.write(f"    {p} / {b}: found inert={found}\n")
        else:
            f.write("  PASSED — all 5 known cases "
                   f"({len(KNOWN_INERT_CASES)} (parameter, base) pairs) "
                   "correctly flagged inert.\n")
        f.write("\nFull matrix:\n")
        for r in rows:
            if r["inert"] is None:
                verdict = "UNEVALUABLE"
            else:
                verdict = "INERT" if r["inert"] else "not inert"
            f.write(f"  {r['parameter']:32s} / {r['base_config']:28s} -> "
                   f"{verdict:11s} "
                   f"(changed {r['n_tracks_changed']}/{len(TRACKS)} tracks, "
                   f"unevaluable {r['n_unevaluable_tracks']}/{len(TRACKS)})\n")
    print(f"wrote {summary_path}")
    print()
    print(open(summary_path).read())


if __name__ == "__main__":
    main()
