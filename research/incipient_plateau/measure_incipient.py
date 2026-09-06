"""Characterisation of the incipient phase under the CURRENT pipeline defaults.

MEASUREMENT ONLY — this script never modifies ``cyclophaser/``.  All
instrumentation is done by monkeypatching ``find_incipient_period`` in the
``determine_periods`` namespace with a *tracing wrapper* that diagnoses which
code path fires and then delegates to the untouched original for the real
result.  A per-call consistency check verifies the replica's predicted
boundary against what the genuine function actually produced.

Pinned provenance
-----------------
Base commit : 01c44923cc6d9e9ae70c48c0fc717fd126546390  (develop-v2.1)
Branch      : research/incipient-plateau
Environment : python 3.13.5, scipy 1.17.1, numpy 2.1.2, pandas 2.3.3
Track set   : the 51 tracks in tests/calibration_data/ + tests/synthetic/ CASES

Why re-measure
--------------
The earlier incipient investigation ran on a pipeline that was contaminated by
three defects since fixed on develop-v2.1: Lanczos zero-padding, an inert
``use_filter=True`` (bool read as the integer 1), and an unrequested Savitzky-
Golay pass on the derivatives.  Its numbers do not carry over.

Pinned metrics (docs/future_work.md §4 fixes these definitions; the earlier
note failed to pin its script and produced a 0.571 vs 0.545 discrepancy)
-----------------------------------------------------------------------
    r(t0)      = |dz_dt_smoothed2[0]|  / max|dz_dt_smoothed2|
    r(t_final) = |dz_dt_smoothed2[-1]| / max|dz_dt_smoothed2|
    reported as the median over the 51 real tracks.
``dz_dt_smoothed2`` is the array ``find_stages`` actually consumes.

Run from the repo root:
    python research/incipient_plateau/measure_incipient.py
    python research/incipient_plateau/measure_incipient.py --no-figures
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# NOTE: cyclophaser/__init__.py re-exports the *function* determine_periods,
# which shadows the submodule of the same name; import it explicitly.
import importlib
dp_mod = importlib.import_module("cyclophaser.determine_periods")
from cyclophaser.determine_periods import (
    find_peaks_valleys, get_periods, periods_to_dict, process_vorticity,
)

OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figures"
CALIB_DIR = REPO_ROOT / "tests" / "calibration_data"

TAUS = [0.05, 0.10, 0.15, 0.20, 0.30]

# ── The two configurations under test ────────────────────────────────────────
# (a) the author's validated §3c calibration (0/51 bad cases), PRIMARY
# (b) bare package defaults: determine_periods(series)
CONFIG_AUTHOR = {
    "pv": dict(
        use_filter=True,                 # == 'auto'; window = len(series)//2
        cutoff_low=168,
        cutoff_high=18,
        boundary_padding="reflect",
        replace_endpoints_with_lowpass=0,
        use_smoothing=False,
        use_smoothing_twice=False,
        savgol_polynomial=3,
    ),
    "gp": dict(
        prominence_relative=0.3,
        distance=3,
        mature_method="amplitude",
        mature_amplitude_fraction=0.95,
        decay_tail_amplitude_fraction=0.05,
        length_scale="local",
        threshold_mature_distance=0.18,
    ),
}
CONFIG_DEFAULTS = {"pv": {}, "gp": {}}

CONFIGS = {"author": CONFIG_AUTHOR, "defaults": CONFIG_DEFAULTS}


# ═════════════════════════════════════════════════════════════════════════════
# Instrumentation: which of the four paths of find_incipient_period fires
# ═════════════════════════════════════════════════════════════════════════════
_ORIG_FIND_INCIPIENT = dp_mod.find_incipient_period
_TRACE: list[dict] = []


def _phases_order(periods: pd.Series) -> list[str]:
    """Verbatim replica of the phases_order accumulation in find_incipient_period.

    NOTE: the original binds ``periods = df['periods']`` *before* the fillna and
    then rebinds the column, so ``periods`` keeps the pre-fillna values (NaNs
    still present).  This replica is fed the same pre-fillna series.
    """
    order, current = [], None
    for phase in periods:
        if pd.notnull(phase) and phase != "residual":
            if phase != current:
                order.append(phase)
                current = phase
    return order


def _diagnose(df_pre: pd.DataFrame, threshold_incipient_length: float) -> dict:
    """Replicate the branch decision of find_incipient_period without mutating."""
    periods_pre = df_pre["periods"]
    order = _phases_order(periods_pre)

    df = df_pre.copy()
    df["periods"] = df["periods"].fillna("incipient")

    # How much of the incipient phase the catch-all fillna could produce on its
    # own: the leading run of NaN in the PRE-fillna periods column.
    isna = periods_pre.isna().to_numpy()
    leading_nan = int(np.argmin(isna)) if (isna.any() and isna[0]) else 0
    if isna.all():
        leading_nan = len(isna)

    info = {
        "leading_nan_len": leading_nan,
        "total_nan": int(isna.sum()),
        "n_phases_order": len(order),
        "phases_order": " > ".join(order),
        "via": "catch_all_only",
        "via_fired": False,
        "predicted_time_range": pd.NaT,
    }

    if len(order) <= 2:
        info["via"] = "i_catch_all_only"
        return info

    if order[:3] == ["intensification", "decay", "intensification"]:
        info["via"] = "ii_caseA_ItDIt"
        start_time = df[df["periods"] == "intensification"].index.min()
        decay_blocks = np.split(
            df[df["periods"] == "decay"].index,
            np.where(np.diff(df["periods"] == "decay") != 0)[0] + 1,
        )
        end_time = decay_blocks[0].max()
        if not pd.isna(end_time):
            info["via_fired"] = True
            info["predicted_time_range"] = start_time + (
                (end_time - start_time) * threshold_incipient_length)

    elif order[0] == "intensification":
        info["via"] = "iii_caseB_startsIt"
        start_time = df[df["periods"] == "intensification"].index.min()
        next_dz_valley = df[1:][df[1:]["dz_peaks_valleys"] == "valley"].index.min()
        next_mature = df[periods_pre == "mature"].index.min()
        if next_dz_valley < next_mature:
            info["via_fired"] = True
            info["predicted_time_range"] = start_time + (
                (next_dz_valley - start_time) * threshold_incipient_length)

    elif order[0] == "decay":
        info["via"] = "iv_caseC_startsD"
        start_time = df[df["periods"] == "decay"].index.min()
        next_dz_peak = df[1:][df[1:]["dz_peaks_valleys"] == "peak"].index.min()
        next_mature = df[periods_pre == "mature"].index.min()
        if next_dz_peak < next_mature:
            info["via_fired"] = True
            info["predicted_time_range"] = start_time + (
                (next_dz_peak - start_time) * threshold_incipient_length)
    else:
        # >2 phases but the first is neither intensification nor decay
        # (e.g. the series opens on 'mature'): no branch applies.
        info["via"] = "i_catch_all_only_no_branch"

    return info


def _traced_find_incipient_period(df, **args_periods):
    """Diagnose on a copy, then delegate to the untouched original."""
    df_pre = df.copy(deep=True)
    info = _diagnose(df_pre, args_periods["threshold_incipient_length"])

    out = _ORIG_FIND_INCIPIENT(df, **args_periods)

    # consistency self-check: reproduce the boundary the genuine call produced
    is_inc = (out["periods"] == "incipient").to_numpy()
    if is_inc.any() and is_inc[0]:
        lead = int(np.argmin(is_inc)) if not is_inc.all() else len(is_inc)
    else:
        lead = 0
    info["incipient_lead_len"] = lead

    if info["via_fired"]:
        tr = info["predicted_time_range"]
        expected_lead = int((out.index <= tr).sum())
        # the catch-all fillna may extend the leading run beyond time_range
        info["replica_consistent"] = bool(lead >= expected_lead)
        info["expected_lead_from_replica"] = expected_lead
    else:
        info["replica_consistent"] = True
        info["expected_lead_from_replica"] = -1

    _TRACE.append(info)
    return out


# ═════════════════════════════════════════════════════════════════════════════
# Per-series measurement
# ═════════════════════════════════════════════════════════════════════════════
def measure_series(series: pd.Series, config: dict) -> dict:
    """Run the full pipeline on one series under one config and measure."""
    zeta_df = pd.DataFrame({"zeta": series})

    _TRACE.clear()
    dp_mod.find_incipient_period = _traced_find_incipient_period
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(zeta_df.copy(), **config["pv"])
            df = get_periods(vort, **config["gp"])
    finally:
        dp_mod.find_incipient_period = _ORIG_FIND_INCIPIENT

    assert len(_TRACE) == 1, f"expected 1 traced call, got {len(_TRACE)}"
    trace = dict(_TRACE[0])

    n = len(series)
    dz = np.asarray(vort["dz_dt_smoothed2"].values, dtype=float)
    amax = np.nanmax(np.abs(dz))
    rel = np.abs(dz) / amax if amax > 0 else np.zeros_like(dz)

    rec = {
        "n": n,
        "r_t0": float(rel[0]),
        "r_tfinal": float(rel[-1]),
        "via": trace["via"],
        "via_fired": trace["via_fired"],
        "leading_nan_len": trace["leading_nan_len"],
        "total_nan": trace["total_nan"],
        "n_phases_order": trace["n_phases_order"],
        "phases_order": trace["phases_order"],
        "replica_consistent": trace["replica_consistent"],
    }

    # ── current incipient boundary ───────────────────────────────────────────
    lead = trace["incipient_lead_len"]
    rec["has_incipient"] = bool((df["periods"] == "incipient").any())
    rec["boundary_idx"] = lead if lead > 0 else -1          # first non-incipient step
    rec["boundary_frac"] = (lead / n) if lead > 0 else np.nan
    rec["boundary_hours"] = (
        (series.index[lead] - series.index[0]).total_seconds() / 3600.0
        if 0 < lead < n else np.nan)
    rec["rel_at_boundary"] = float(rel[lead]) if 0 < lead < n else np.nan

    # ── slope profile / plateau descriptors ──────────────────────────────────
    rec["rel_mean_first10pct"] = float(np.mean(rel[: max(1, n // 10)]))
    rec["rel_argmax_idx"] = int(np.argmax(np.abs(dz)))

    # tau sweep: first step where the relative slope reaches tau
    for tau in TAUS:
        hits = np.flatnonzero(rel >= tau)
        idx = int(hits[0]) if hits.size else -1
        key = f"{tau:.2f}"
        rec[f"tau{key}_idx"] = idx
        rec[f"tau{key}_frac"] = (idx / n) if idx >= 0 else np.nan
        rec[f"tau{key}_hours"] = (
            (series.index[idx] - series.index[0]).total_seconds() / 3600.0
            if idx >= 0 else np.nan)
        rec[f"tau{key}_minus_current"] = (
            idx - lead if (idx >= 0 and lead > 0) else np.nan)

    phases = periods_to_dict(df)
    rec["phase_seq"] = " > ".join(
        dict.fromkeys(k.rstrip(" 0123456789").strip() for k in phases))
    rec["_rel"] = rel
    rec["_df"] = df
    rec["_vort"] = vort
    rec["_phases"] = phases
    return rec


# ═════════════════════════════════════════════════════════════════════════════
# Data loading
# ═════════════════════════════════════════════════════════════════════════════
def load_real_tracks() -> dict[str, pd.Series]:
    out = {}
    for csv in sorted(CALIB_DIR.glob("*.csv")):
        d = pd.read_csv(csv, sep=";", index_col="time", parse_dates=True)
        out[csv.stem] = d["min_max_zeta_850"].rename("zeta")
    return out


def load_synthetic() -> dict[str, dict]:
    from tests.synthetic.cases import CASES
    return CASES


def synthetic_ground_truth(name: str, case: dict) -> dict:
    """Ground truth for the incipient boundary of one synthetic case.

    Three kinds:
      designed_Ic  — the segment list opens with a literal 'Ic' segment; the
                     ground-truth boundary is its length.
      expected_Ic  — the case asserts an 'incipient' phase but has no Ic
                     segment (it is derived from a leading D); the designed
                     boundary is degenerate (incipient and the next phase share
                     start 0), so no boundary target is checkable.
      no_Ic        — the case asserts no incipient at all: any incipient the
                     catch-all produces is spurious.
    """
    segs = case["segments"]
    types = [s["type"] for s in segs]
    exp = case.get("expected_phases")
    if types and types[0] == "Ic":
        return {"kind": "designed_Ic", "gt_boundary": segs[0]["n"],
                "tolerance": case.get("tolerance", 6)}
    if exp is not None and "incipient" in exp:
        starts = case.get("expected_starts_idx") or {}
        nxt = exp[1] if len(exp) > 1 else None
        gt = starts.get(nxt) if nxt else None
        if gt:
            return {"kind": "expected_Ic", "gt_boundary": gt,
                    "tolerance": case.get("tolerance", 6)}
        return {"kind": "expected_Ic", "gt_boundary": np.nan,
                "tolerance": case.get("tolerance", 6)}
    return {"kind": "no_Ic", "gt_boundary": np.nan,
            "tolerance": case.get("tolerance", 6)}


# ═════════════════════════════════════════════════════════════════════════════
# Figures — style reused from tests/calibration_data/gen_real_before_after.py
# ═════════════════════════════════════════════════════════════════════════════
PHASE_COLORS = {
    "incipient":       "#65a1e6",
    "intensification": "#f7b538",
    "mature":          "#d62828",
    "decay":           "#9aa981",
    "residual":        "#999999",
}
ALL_PHASES = ["incipient", "intensification", "mature", "decay", "residual"]
C_Z, C_DZ, C_DZ2 = "#1d3557", "#457b9d", "#e63946"
_BLUE, _RED = "#2171b5", "#cb181d"
MK_PEAK = dict(marker="^", s=60, zorder=5, clip_on=False)
MK_VALLEY = dict(marker="v", s=60, zorder=5, clip_on=False)
TAU_COLORS = {0.05: "#4d004b", 0.10: "#810f7c", 0.15: "#8856a7",
              0.20: "#8c96c6", 0.30: "#b3cde3"}


def _normalize(name):
    return name.rstrip(" 0123456789").strip()


def _draw_phases(ax, phases_dict, ts_to_idx, n):
    items = list(phases_dict.items())
    for i, (ph, (st, en)) in enumerate(items):
        right_ts = items[i + 1][1][0] if i + 1 < len(items) else en
        left_i = ts_to_idx.get(st, 0)
        right_i = ts_to_idx.get(right_ts, n - 1)
        ax.axvspan(left_i, right_i, alpha=0.28,
                   color=PHASE_COLORS.get(_normalize(ph), "#cccccc"), lw=0)


def make_figure(track_id, series, recs, out_path, gt_boundary=None):
    """Two columns: (a) author's §3c calibration | (b) package defaults."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.gridspec as gridspec
    import matplotlib.lines as mlines
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    n = len(series)
    times = list(series.index)
    t_vals = np.arange(n)
    ts_to_idx = {t: i for i, t in enumerate(times)}
    dur_days = (series.index[-1] - series.index[0]).total_seconds() / 86400
    date_str = (f"{series.index[0].strftime('%Y-%m-%d')} -> "
                f"{series.index[-1].strftime('%Y-%m-%d')}")

    col_keys = ["author", "defaults"]
    col_titles = []
    for ck in col_keys:
        r = recs[ck]
        lab = ("(a) calibracao do autor §3c" if ck == "author"
               else "(b) defaults do pacote")
        col_titles.append(
            f"{lab}\n{r['phase_seq']}\n"
            f"via={r['via']} fired={r['via_fired']}  ·  "
            f"r(t0)={r['r_t0']:.3f}  r(tf)={r['r_tfinal']:.3f}")

    fig = plt.figure(figsize=(17, 13))
    fig.suptitle(
        f"Ciclone {track_id}  ·  {n} pts  ·  {date_str}  ·  {dur_days:.1f} dias\n"
        f"Fronteira incipiente atual (linha preta) vs varredura de tau "
        f"(linhas tracejadas)  ·  fase incipiente sob as duas configuracoes",
        fontsize=11, fontweight="bold", y=0.99)
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.52, wspace=0.10,
                           top=0.90, bottom=0.15)

    for ci, ck in enumerate(col_keys):
        rec = recs[ck]
        vort = rec["_vort"]
        z = pd.Series(vort["vorticity_smoothed2"].values, index=series.index)
        dz = pd.Series(vort["dz_dt_smoothed2"].values, index=series.index)
        dz2 = pd.Series(vort["dz_dt2_smoothed2"].values, index=series.index)
        z_raw = pd.Series(vort["zeta"].values, index=series.index)
        rel = rec["_rel"]

        panel_cfg = [
            ("z", z, C_Z, "z  (vorticidade suavizada)", find_peaks_valleys(z)),
            ("dz", dz, C_DZ, "dz/dt  (1a derivada)", find_peaks_valleys(dz)),
            ("rel", pd.Series(rel, index=series.index), C_DZ2,
             "|dz| / max|dz|  (perfil de slope)", None),
        ]

        for ri, (key, ser, color, ser_label, extr) in enumerate(panel_cfg):
            ax = fig.add_subplot(gs[ri, ci])
            _draw_phases(ax, rec["_phases"], ts_to_idx, n)

            ax2 = ax.twinx()
            ax2.plot(t_vals, z_raw.values, color="#888888", lw=1.4,
                     alpha=0.65, zorder=1)
            ax2.tick_params(axis="y", labelsize=6, colors="#888888", length=3)
            ax2.set_ylabel("original", fontsize=6, color="#888888")
            ax2.set_xlim(-0.5, n - 0.5)

            ax.set_zorder(ax2.get_zorder() + 1)
            ax.patch.set_visible(False)
            ax.axhline(0, color="gray", lw=0.5, ls="--")
            ax.plot(t_vals, ser.values, color=color, lw=1.8, zorder=3)

            npk = nvl = 0
            if extr is not None:
                peaks = [i for i, t in enumerate(times) if extr[t] == "peak"]
                valleys = [i for i, t in enumerate(times) if extr[t] == "valley"]
                npk, nvl = len(peaks), len(valleys)
                if peaks:
                    ax.scatter(peaks, [ser.values[i] for i in peaks],
                               color=_BLUE, **MK_PEAK)
                if valleys:
                    ax.scatter(valleys, [ser.values[i] for i in valleys],
                               color=_RED, **MK_VALLEY)

            # current incipient boundary
            b = rec["boundary_idx"]
            if b > 0:
                ax.axvline(b, color="black", lw=2.0, zorder=6)
            # ground truth (synthetic only)
            if gt_boundary is not None and not pd.isna(gt_boundary):
                ax.axvline(gt_boundary, color="#00a000", lw=2.0, ls=":", zorder=6)
            # tau crossings
            for tau in TAUS:
                idx = rec[f"tau{tau:.2f}_idx"]
                if idx >= 0:
                    ax.axvline(idx, color=TAU_COLORS[tau], lw=1.1, ls="--",
                               alpha=0.9, zorder=4)
            if key == "rel":
                for tau in TAUS:
                    ax.axhline(tau, color=TAU_COLORS[tau], lw=0.7, ls=":",
                               alpha=0.7)
                ax.set_ylim(0, 1.02)

            if ri == 0:
                ax.set_title(col_titles[ci], fontsize=8.5, pad=6)
            suffix = f"\n({npk}p / {nvl}v)" if extr is not None else ""
            ax.set_ylabel(ser_label + suffix, fontsize=7.5)
            ax.tick_params(labelsize=7)
            ax.set_xlim(-0.5, n - 0.5)
            step = max(1, n // 8)
            tick_pos = list(range(0, n, step))
            ax.set_xticks(tick_pos)
            ax.set_xticklabels(
                [times[i].strftime("%m/%d\n%Hh") for i in tick_pos], fontsize=6)
            if ri == 2:
                ax.set_xlabel("Data/hora", fontsize=8)

    handles = [mpatches.Patch(color=PHASE_COLORS[p], alpha=0.6,
                              label=p.capitalize()) for p in ALL_PHASES]
    handles += [
        mlines.Line2D([], [], color="#888888", lw=1.4, alpha=0.8,
                      label="serie original (eixo dir.)"),
        mlines.Line2D([], [], color="black", lw=2.0,
                      label="fronteira incipiente ATUAL (0.4x)"),
        mlines.Line2D([], [], color="#00a000", lw=2.0, ls=":",
                      label="ground truth Ic (sinteticos)"),
    ]
    handles += [mlines.Line2D([], [], color=TAU_COLORS[t], lw=1.1, ls="--",
                              label=f"tau={t:.2f}") for t in TAUS]
    fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=8,
               frameon=False, bbox_to_anchor=(0.5, 0.015))
    fig.savefig(out_path, dpi=110, bbox_inches="tight")
    plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args()

    real = load_real_tracks()
    synth = load_synthetic()
    print(f"loaded {len(real)} real tracks, {len(synth)} synthetic cases")

    rows = []
    fig_dir_real = FIG_DIR / "real"
    fig_dir_syn = FIG_DIR / "synthetic"
    if not args.no_figures:
        fig_dir_real.mkdir(parents=True, exist_ok=True)
        fig_dir_syn.mkdir(parents=True, exist_ok=True)

    # ── real tracks ──────────────────────────────────────────────────────────
    for tid, series in real.items():
        recs = {}
        for cname, cfg in CONFIGS.items():
            rec = measure_series(series, cfg)
            recs[cname] = rec
            rows.append({"dataset": "real", "track": tid, "config": cname,
                         "gt_kind": "", "gt_boundary": np.nan,
                         **{k: v for k, v in rec.items()
                            if not k.startswith("_")}})
        if not args.no_figures:
            make_figure(tid, series, recs, fig_dir_real / f"{tid}.png")
        print(f"  real {tid}: "
              f"a via={recs['author']['via']}/{recs['author']['via_fired']} "
              f"b via={recs['defaults']['via']}/{recs['defaults']['via_fired']}")

    # ── synthetic ────────────────────────────────────────────────────────────
    for name, case in synth.items():
        series = case["series"]
        gt = synthetic_ground_truth(name, case)
        recs = {}
        for cname, cfg in CONFIGS.items():
            rec = measure_series(series, cfg)
            recs[cname] = rec
            row = {"dataset": "synthetic", "track": name, "config": cname,
                   "gt_kind": gt["kind"], "gt_boundary": gt["gt_boundary"],
                   **{k: v for k, v in rec.items() if not k.startswith("_")}}
            row["boundary_err"] = (row["boundary_idx"] - gt["gt_boundary"]
                                   if (not pd.isna(gt["gt_boundary"])
                                       and row["boundary_idx"] > 0) else np.nan)
            for tau in TAUS:
                row[f"tau{tau:.2f}_err"] = (
                    row[f"tau{tau:.2f}_idx"] - gt["gt_boundary"]
                    if (not pd.isna(gt["gt_boundary"])
                        and row[f"tau{tau:.2f}_idx"] >= 0) else np.nan)
            rows.append(row)
        if not args.no_figures:
            make_figure(name, series, recs, fig_dir_syn / f"{name}.png",
                        gt_boundary=gt["gt_boundary"])
        print(f"  synth {name} [{gt['kind']}]: "
              f"a b={recs['author']['boundary_idx']} "
              f"b b={recs['defaults']['boundary_idx']} gt={gt['gt_boundary']}")

    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "incipient_measurements.csv", index=False)
    print(f"\nwrote {OUT_DIR / 'incipient_measurements.csv'}  ({len(out)} rows)")

    bad = out[~out["replica_consistent"].astype(bool)]
    if len(bad):
        print(f"!! replica inconsistency on {len(bad)} rows:\n"
              f"{bad[['dataset', 'track', 'config', 'via']]}")
    else:
        print("replica self-check: OK on all rows")

    summarise(out)


def summarise(out: pd.DataFrame):
    """Print the aggregate tables that go into the report."""
    real = out[out.dataset == "real"]
    lines = []
    A = lines.append

    A("\n" + "=" * 78)
    A("TABLE 1 — pinned edge metrics, 51 real tracks (median [q25-q75])")
    A("=" * 78)
    A(f"{'config':<12}{'r(t0)':<24}{'r(t_final)':<24}")
    for c in ("author", "defaults"):
        s = real[real.config == c]
        r0, rf = s.r_t0, s.r_tfinal
        A(f"{c:<12}"
          f"{r0.median():.3f} [{r0.quantile(.25):.3f}-{r0.quantile(.75):.3f}]   "
          f"{rf.median():.3f} [{rf.quantile(.25):.3f}-{rf.quantile(.75):.3f}]")

    A("\n" + "=" * 78)
    A("TABLE 2 — which of the four paths of find_incipient_period fires (51 real)")
    A("=" * 78)
    piv = (real.groupby(["config", "via", "via_fired"]).size()
           .unstack(fill_value=0))
    A(piv.to_string())
    A("")
    A("tracks with len(phases_order) <= 2: " + str(
        real[real.n_phases_order <= 2].groupby("config").size().to_dict()))
    A("tracks with an incipient phase: " + str(
        real[real.has_incipient].groupby("config").size().to_dict()))

    A("\n" + "=" * 78)
    A("TABLE 3 — current incipient boundary (51 real)")
    A("=" * 78)
    A(f"{'config':<12}{'n_with_inc':<12}{'idx med':<10}{'frac med':<11}{'hours med':<11}{'rel@bound med':<14}")
    for c in ("author", "defaults"):
        s = real[(real.config == c) & (real.boundary_idx > 0)]
        A(f"{c:<12}{len(s):<12}{s.boundary_idx.median():<10.1f}"
          f"{s.boundary_frac.median():<11.3f}{s.boundary_hours.median():<11.1f}"
          f"{s.rel_at_boundary.median():<14.3f}")

    A("\n" + "=" * 78)
    A("TABLE 4 — tau sweep vs the current boundary (51 real), in timesteps")
    A("=" * 78)
    for c in ("author", "defaults"):
        s = real[real.config == c]
        A(f"\n-- config {c} --  (current boundary median idx = "
          f"{s[s.boundary_idx > 0].boundary_idx.median():.1f})")
        A(f"{'tau':<8}{'idx med':<10}{'frac med':<11}{'hours med':<11}"
          f"{'delta vs current (med)':<24}{'n reached':<10}")
        for tau in TAUS:
            k = f"tau{tau:.2f}"
            sub = s[s[f"{k}_idx"] >= 0]
            A(f"{tau:<8.2f}{sub[f'{k}_idx'].median():<10.1f}"
              f"{sub[f'{k}_frac'].median():<11.3f}"
              f"{sub[f'{k}_hours'].median():<11.1f}"
              f"{s[f'{k}_minus_current'].median():<24.1f}{len(sub):<10}")

    A("\n" + "=" * 78)
    A("TABLE 5 — does an initial low-slope plateau exist at all? (51 real)")
    A("=" * 78)
    A("A 'plateau' of length L at tau means rel(t) < tau for the first L steps,")
    A("i.e. L == the tau-crossing index.  L == 0 means the very first sample")
    A("already exceeds tau: no plateau exists and no tau-based criterion can")
    A("place a boundary there.")
    A(f"{'config':<12}{'tau':<8}{'n L==0':<10}{'n L>=1':<10}{'n L>=3':<10}"
      f"{'n L>=6':<10}{'L med':<8}{'L q75':<8}")
    for c in ("author", "defaults"):
        s = real[real.config == c]
        for tau in TAUS:
            L = s[f"tau{tau:.2f}_idx"].clip(lower=0)
            A(f"{c:<12}{tau:<8.2f}{int((L == 0).sum()):<10}"
              f"{int((L >= 1).sum()):<10}{int((L >= 3).sum()):<10}"
              f"{int((L >= 6).sum()):<10}{L.median():<8.1f}"
              f"{L.quantile(.75):<8.1f}")

    A("\n" + "=" * 78)
    A("TABLE 6 — pure catch-all incipient (no via fired) (51 real)")
    A("=" * 78)
    A(f"{'config':<12}{'no via fired':<15}{'  of which WITH incipient':<28}"
      f"{'via fired':<12}")
    for c in ("author", "defaults"):
        s = real[real.config == c]
        nf = s[~s.via_fired.astype(bool)]
        A(f"{c:<12}{len(nf):<15}{int(nf.has_incipient.sum()):<28}"
          f"{int(s.via_fired.astype(bool).sum()):<12}")
    A("")
    A("What the catch-all fillna could contribute on its own — the leading run")
    A("of NaN in the periods column BEFORE the fillna (post_process_periods has")
    A("already run at this point):")
    A(f"{'config':<12}{'n leading_nan>0':<18}{'leading_nan med':<18}"
      f"{'n any NaN':<12}")
    for c in ("author", "defaults"):
        s = real[real.config == c]
        A(f"{c:<12}{int((s.leading_nan_len > 0).sum()):<18}"
          f"{s.leading_nan_len.median():<18.1f}"
          f"{int((s.total_nan > 0).sum()):<12}")
    A("")
    A("per-track detail for the tracks where no via fired:")
    nf = real[~real.via_fired.astype(bool)]
    A(nf[["track", "config", "via", "n_phases_order", "phases_order",
          "has_incipient", "boundary_idx", "phase_seq"]].to_string(index=False))

    A("\n" + "=" * 78)
    A("TABLE 7 — synthetic ground truth")
    A("=" * 78)
    syn = out[out.dataset == "synthetic"]
    cols = (["track", "config", "gt_kind", "gt_boundary", "boundary_idx",
             "boundary_err"] + [f"tau{t:.2f}_idx" for t in TAUS]
            + ["phase_seq", "via", "via_fired"])
    A(syn[cols].to_string(index=False))

    A("\n" + "=" * 78)
    A("TABLE 8 — synthetic accuracy vs the known Ic boundary (designed_Ic only)")
    A("=" * 78)
    dz = syn[(syn.gt_kind == "designed_Ic")]
    A(f"{'config':<12}{'criterion':<14}{'n scored':<10}{'MAE (steps)':<14}"
      f"{'signed med':<13}{'misses':<8}")
    for c in ("author", "defaults"):
        s2 = dz[dz.config == c]
        e = s2["boundary_err"].dropna()
        A(f"{c:<12}{'current 0.4x':<14}{len(e):<10}{e.abs().mean():<14.2f}"
          f"{e.median():<13.1f}{int(s2.boundary_err.isna().sum()):<8}")
        for tau in TAUS:
            e = s2[f"tau{tau:.2f}_err"].dropna()
            A(f"{c:<12}{'tau=' + f'{tau:.2f}':<14}{len(e):<10}"
              f"{e.abs().mean():<14.2f}{e.median():<13.1f}"
              f"{int(s2[f'tau{tau:.2f}_err'].isna().sum()):<8}")
    A("")
    A("spurious incipient on cases that designed NO incipient (gt_kind=no_Ic):")
    A(syn[syn.gt_kind == "no_Ic"][
        ["track", "config", "has_incipient", "boundary_idx", "via",
         "via_fired", "phase_seq"]].to_string(index=False))

    text = "\n".join(lines)
    print(text)
    (OUT_DIR / "summary_tables.txt").write_text(text)
    print(f"\nwrote {OUT_DIR / 'summary_tables.txt'}")


if __name__ == "__main__":
    main()
