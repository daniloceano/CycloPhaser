#!/usr/bin/env python
"""Diagnostic script for "problema A" (index-0 decay opening).

READ-ONLY. Does not modify the cyclophaser package. Calls process_vorticity,
find_peaks_valleys and the individual find_*_period functions exactly as they
are defined in cyclophaser/determine_periods.py and cyclophaser/find_stages.py
(the same sequence get_periods() runs, determine_periods.py:1073-1083), using
the calibration-app config ~/Downloads/cyclophaser_params-9.yaml, unmodified,
on the 51 real tracks in tests/calibration_data/.

The pipeline is re-run step by step (not through the single get_periods() call)
so the periods column can be snapshotted immediately after find_decay_period —
BEFORE find_incipient_period runs. This matters: find_incipient_period, under
this config's incipient_method="plateau", unconditionally overwrites
df.iloc[:boundary] with 'incipient' (cyclophaser/find_stages.py:979-982),
regardless of what find_decay_period assigned there. For the 5 tracks affected
by "problema A" this partially consumes the leading decay block (the first
~8-11 steps become 'incipient') without removing the rest of it. See
idx0_final_stage.csv and REPORT.md for the final-stage picture.

Run:
    ~/miniconda3/envs/south_atlantic_cyclone_extremes/bin/python \
        research/labels/diagnostics/build_idx0_inventory.py

Writes (unversioned, not committed):
    research/labels/diagnostics/idx0_inventory.csv       (Task 1)
    research/labels/diagnostics/idx0_final_stage.csv     (final-output cross-check)
    research/labels/diagnostics/idx0b_prominence.csv     (Task 1b-c)
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"
DIAG_DIR = Path(__file__).resolve().parent
CONFIG_PATH = Path.home() / "Downloads" / "cyclophaser_params-9.yaml"

sys.path.insert(0, str(LABELS_DIR))
sys.path.insert(0, str(REPO_ROOT))
from labels_core import load_real_series, read_split  # noqa: E402

from cyclophaser.determine_periods import (  # noqa: E402
    process_vorticity,
    find_peaks_valleys,
    post_process_periods,
)
from cyclophaser.find_stages import (  # noqa: E402
    find_intensification_period,
    find_decay_period,
    find_mature_stage,
    find_residual_period,
    find_incipient_period,
)
from scipy.signal import peak_prominences  # noqa: E402

# Same key split evaluate_against_labels.py uses to route a calibration-app
# YAML into process_vorticity kwargs vs get_periods kwargs.
PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")


def load_config(path: Path):
    import inspect
    from cyclophaser.determine_periods import get_periods
    doc = yaml.safe_load(path.read_text()) or {}
    gp_accepted = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_accepted}
    return pv, gp, doc


def sign_str(x: float) -> str:
    if x > 0:
        return "+"
    if x < 0:
        return "-"
    return "0"


def leading_run_len(periods: pd.Series, phase: str) -> int:
    """Length in steps of the leading run of `phase` starting at index 0."""
    n = 0
    for v in periods.astype(str):
        if v == phase:
            n += 1
        else:
            break
    return n


def run_pipeline_with_snapshots(values: pd.Series, pv: dict, gp: dict):
    """Reimplements get_periods()'s body (determine_periods.py:1026-1083) with
    an added snapshot of df['periods'] right after find_decay_period.

    Not a modification of the package: every call below invokes the package's
    own functions unchanged, in the same order get_periods() does.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vorticity = process_vorticity(pd.DataFrame({"zeta": values}), **pv)

    z = vorticity.vorticity_smoothed2
    dz = vorticity.dz_dt_smoothed2
    dz2 = vorticity.dz_dt2_smoothed2

    df = z.to_dataframe().rename(columns={"vorticity_smoothed2": "z"})
    df["z_unfil"] = vorticity.zeta.to_dataframe()
    df["dz"] = dz.to_dataframe()
    df["dz2"] = dz2.to_dataframe()

    df["z_peaks_valleys"] = find_peaks_valleys(
        df["z"], prominence=gp.get("prominence"),
        prominence_relative=gp.get("prominence_relative"), distance=gp.get("distance"))
    df["dz_peaks_valleys"] = find_peaks_valleys(df["dz"])
    df["dz2_peaks_valleys"] = find_peaks_valleys(df["dz2"])

    df["periods"] = np.nan
    df["periods"] = df["periods"].astype("object")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = find_intensification_period(df, **gp)
        df = find_decay_period(df, **gp)
        after_decay_period = df["periods"].copy()  # <-- snapshot Task 1 is measured on

        df = find_mature_stage(df, **gp)
        df = find_residual_period(df, **gp)
        df = post_process_periods(df)
        df = find_incipient_period(df, **gp)

    return df, after_decay_period


def main():
    pv, gp, cfg_doc = load_config(CONFIG_PATH)
    print(f"config: {CONFIG_PATH}")
    print(f"process_vorticity kwargs: {pv}")
    print(f"get_periods kwargs: {gp}")

    cyclones_used = cfg_doc.get("metadata", {}).get("cyclones_used")

    split_doc = read_split()
    split_of = {}
    for sid in split_doc.get("train", []):
        split_of[sid] = "treino"
    for sid in split_doc.get("test", []):
        split_of[sid] = "teste"

    series = load_real_series()
    print(f"loaded {len(series)} real tracks from tests/calibration_data")

    if cyclones_used is not None:
        missing = set(cyclones_used) - set(series)
        extra = set(series) - set(cyclones_used)
        if missing or extra:
            print(f"NOTE: cyclones_used in config vs tests/calibration_data differ. "
                  f"missing_from_calib_data={sorted(missing)} extra_in_calib_data={sorted(extra)}")

    rows = []
    final_rows = []
    prom_rows = []

    for sid in sorted(series):
        values = series[sid]
        n_steps = len(values)

        df, after_decay_period = run_pipeline_with_snapshots(values, pv, gp)

        z = df["z"]
        z_unfil = df["z_unfil"]
        idx0_tipo_raw = df["z_peaks_valleys"].iloc[0]
        idx0_tipo = idx0_tipo_raw if isinstance(idx0_tipo_raw, str) else "nenhum"

        sinal_dz_filtrada = sign_str(z.iloc[1] - z.iloc[0])
        sinal_dz_bruta = sign_str(z_unfil.iloc[1] - z_unfil.iloc[0])

        # --- Task 1 columns, measured right after find_decay_period ---
        decai_no_idx0 = bool(str(after_decay_period.iloc[0]) == "decay")
        decai_len = leading_run_len(after_decay_period, "decay") if decai_no_idx0 else 0

        if decai_no_idx0:
            decay_end_idx = decai_len - 1
            z_amp_total = float(z.max() - z.min())
            z_span_decay = float(abs(z.iloc[decay_end_idx] - z.iloc[0]))
            decai_fracao_serie = decai_len / n_steps
            decai_fracao_amplitude = (z_span_decay / z_amp_total) if z_amp_total > 0 else float("nan")
        else:
            decai_fracao_serie = 0.0
            decai_fracao_amplitude = 0.0

        rows.append({
            "track_id": sid,
            "split": split_of.get(sid, "nao_determinado"),
            "idx0_tipo": idx0_tipo,
            "sinal_dz_filtrada": sinal_dz_filtrada,
            "sinal_dz_bruta": sinal_dz_bruta,
            "decai_no_idx0": "sim" if decai_no_idx0 else "nao",
            "decai_comprimento_passos": decai_len,
            "decai_fracao_serie": round(decai_fracao_serie, 4),
            "decai_fracao_amplitude": (round(decai_fracao_amplitude, 4)
                                        if not np.isnan(decai_fracao_amplitude) else ""),
        })

        # --- final-stage cross-check (after find_incipient_period) ---
        final_periods = df["periods"]
        final_idx0 = str(final_periods.iloc[0])
        final_leading_incipient = leading_run_len(final_periods, "incipient")
        first_non_incipient = None
        for v in final_periods.astype(str):
            if v != "incipient":
                first_non_incipient = v
                break
        final_rows.append({
            "track_id": sid,
            "periods_idx0_final": final_idx0,
            "leading_incipient_len_final": final_leading_incipient,
            "first_non_incipient_phase_final": first_non_incipient,
        })

        # ---- Task 1b(c): out-of-band prominence measurement for idx0 valleys ----
        # The package NEVER computes a prominence value for a boundary index
        # (see _refine_extrema, determine_periods.py:181-191: boundary indices
        # are excluded from `interior` before peak_prominences is called, so no
        # prominence is computed for them by the actual code path). This block
        # recomputes it out-of-band, the same way the package computes it for
        # INTERIOR candidates, purely as a diagnostic measurement -- it is not
        # what the shipped code does or uses.
        if idx0_tipo == "valley":
            data = z.values
            N = len(data)
            signed_data = -data  # valleys: package computes prominence on -data
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                idx0_prominence = float(peak_prominences(signed_data, [0])[0][0])

            surviving = df["z_peaks_valleys"].dropna()
            surviving_idx = [df.index.get_loc(i) for i in surviving.index]
            surviving_idx = sorted(i for i in surviving_idx if i != 0)
            dist_to_next = (surviving_idx[0] - 0) if surviving_idx else None

            unfiltered = find_peaks_valleys(z)
            valley_candidates = np.array([df.index.get_loc(i)
                                           for i in unfiltered[unfiltered == "valley"].index])
            peak_candidates = np.array([df.index.get_loc(i)
                                         for i in unfiltered[unfiltered == "peak"].index])
            interior_valleys = np.array([i for i in valley_candidates if i not in (0, N - 1)])
            interior_peaks = np.array([i for i in peak_candidates if i not in (0, N - 1)])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                interior_valley_proms = (peak_prominences(-data, interior_valleys)[0]
                                          if len(interior_valleys) else np.array([]))
                interior_peak_proms = (peak_prominences(data, interior_peaks)[0]
                                        if len(interior_peaks) else np.array([]))
            all_interior_proms = np.concatenate([interior_valley_proms, interior_peak_proms])
            max_interior_prom = float(all_interior_proms.max()) if len(all_interior_proms) else float("nan")
            prominence_relative_cfg = gp.get("prominence_relative")
            would_survive_on_merit = (
                (idx0_prominence >= prominence_relative_cfg * max_interior_prom)
                if (prominence_relative_cfg is not None and not np.isnan(max_interior_prom)
                    and max_interior_prom > 0)
                else None
            )

            prom_rows.append({
                "track_id": sid,
                "idx0_prominence_computed_diagnostically": round(idx0_prominence, 6),
                "max_interior_prominence_z": (round(max_interior_prom, 6)
                                               if not np.isnan(max_interior_prom) else ""),
                "prominence_relative_threshold_cfg": prominence_relative_cfg,
                "would_survive_relative_filter_on_its_own_merit": would_survive_on_merit,
                "steps_to_next_surviving_extremum": dist_to_next,
            })

    inv = pd.DataFrame(rows)
    inv.to_csv(DIAG_DIR / "idx0_inventory.csv", index=False)
    print(f"wrote {DIAG_DIR / 'idx0_inventory.csv'} ({len(inv)} rows)")

    counts = inv["idx0_tipo"].value_counts()
    print("idx0_tipo counts:", dict(counts))
    print("decai_no_idx0 counts (right after find_decay_period):",
          dict(inv["decai_no_idx0"].value_counts()))

    final_df = pd.DataFrame(final_rows)
    final_df.to_csv(DIAG_DIR / "idx0_final_stage.csv", index=False)
    print(f"wrote {DIAG_DIR / 'idx0_final_stage.csv'} ({len(final_df)} rows)")

    prom_df = pd.DataFrame(prom_rows)
    prom_df.to_csv(DIAG_DIR / "idx0b_prominence.csv", index=False)
    print(f"wrote {DIAG_DIR / 'idx0b_prominence.csv'} ({len(prom_df)} rows)")


if __name__ == "__main__":
    main()
