"""Visual checkpoint: incipient_method="geometric" vs "plateau", side by side.

MEASUREMENT/VISUALISATION ONLY. Reuses the figure style of
`measure_incipient.py` (itself modelled on
tests/calibration_data/gen_real_before_after.py and
tests/synthetic/gen_extrema_before_after.py): a 3-row x 2-column grid with
phase shading, the raw series on a secondary axis, and marker conventions
unchanged.

Left column  = geometric (the current, default rule).
Right column = plateau   (the opt-in rule under test).

Overlays
    black solid   the incipient boundary the column's own method produced
    magenta solid the plateau boundary (shown in BOTH columns for comparison)
    green dotted  the designed ground-truth Ic boundary (synthetic cases only)
    coloured dash the tau sweep crossings on the rel(t) panel

Configurations
    real tracks : the author's validated section-3c calibration, which is the
                  regime where a plateau is definable at all (r(t0) median
                  0.068). Under package defaults the first sample already
                  exceeds every usable tau on most tracks — see section 4 of
                  REPORT_incipient_characterisation.md.
    synthetic   : the preset appropriate to each case — SYNTHETIC_CLEAN_PRESET
                  for the four noise-free cases, SYNTHETIC_NOISY_PRESET for the
                  eight 2 %-noise ones (they need different pre-processing; see
                  the presets' block comment in tests/synthetic/cases.py).

Run from the repo root:
    python research/incipient_plateau/gen_geometric_vs_plateau.py
    python research/incipient_plateau/gen_geometric_vs_plateau.py --tau 0.15
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import importlib
dp_mod = importlib.import_module("cyclophaser.determine_periods")
from cyclophaser.determine_periods import (
    find_peaks_valleys, get_periods, periods_to_dict, process_vorticity,
)
from cyclophaser.find_stages import _incipient_plateau_rel
from tests.synthetic.cases import CASES, NOISY_CASE_IDS, preset_for

OUT = Path(__file__).resolve().parent / "figures" / "geometric_vs_plateau"
CALIB = REPO_ROOT / "tests" / "calibration_data"

# The six real tracks flagged for the visual checkpoint: 20190325 and 20206498
# take case C under the author's calibration (and 20206498's via does not fire);
# 20150377 is a plain case-B track; 20190639 is the one track in the set with
# any leading NaN before the catch-all; 20203373 and 20203947 have a high
# r(t0) under defaults, so they show the regime where the plateau collapses.
REAL_TRACKS = ["20150377", "20190325", "20190639", "20203373", "20203947", "20206498"]

TAUS = [0.05, 0.10, 0.15, 0.20, 0.30]
TAU_COLORS = {0.05: "#4d004b", 0.10: "#810f7c", 0.15: "#8856a7",
              0.20: "#8c96c6", 0.30: "#b3cde3"}

# ── section 3c calibration (author's validated set) ──────────────────────────
AUTHOR_PV = dict(use_filter=True, cutoff_low=168, cutoff_high=18,
                 boundary_padding="reflect", replace_endpoints_with_lowpass=0,
                 use_smoothing=False, use_smoothing_twice=False,
                 savgol_polynomial=3)
AUTHOR_GP = dict(prominence_relative=0.3, distance=3, mature_method="amplitude",
                 mature_amplitude_fraction=0.95,
                 decay_tail_amplitude_fraction=0.05, length_scale="local",
                 threshold_mature_distance=0.18)

PRESET_GP: dict = {}

PHASE_COLORS = {"incipient": "#65a1e6", "intensification": "#f7b538",
                "mature": "#d62828", "decay": "#9aa981", "residual": "#999999"}
ALL_PHASES = ["incipient", "intensification", "mature", "decay", "residual"]
C_Z, C_DZ, C_REL = "#1d3557", "#457b9d", "#e63946"
_BLUE, _RED = "#2171b5", "#cb181d"
C_PLATEAU = "#d000d0"
MK_PEAK = dict(marker="^", s=60, zorder=5, clip_on=False)
MK_VALLEY = dict(marker="v", s=60, zorder=5, clip_on=False)


def _normalize(n):
    return n.rstrip(" 0123456789").strip()


def _draw_phases(ax, phases, ts_to_idx, n):
    items = list(phases.items())
    for i, (ph, (st, en)) in enumerate(items):
        right = items[i + 1][1][0] if i + 1 < len(items) else en
        ax.axvspan(ts_to_idx.get(st, 0), ts_to_idx.get(right, n - 1),
                   alpha=0.28, color=PHASE_COLORS.get(_normalize(ph), "#ccc"), lw=0)


def _lead(df):
    inc = (df["periods"] == "incipient").to_numpy()
    if not inc.any() or not inc[0]:
        return 0
    return int(np.argmin(inc)) if not inc.all() else len(inc)


def run_one(series, pv, gp, tau, **plateau_kw):
    zeta_df = pd.DataFrame({"zeta": series})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(zeta_df.copy(), **pv)
        geo = get_periods(vort, **gp)
        plat = get_periods(vort, **gp, incipient_method="plateau",
                           incipient_plateau_tau=tau, **plateau_kw)
    return vort, geo, plat


def make_figure(name, series, vort, geo, plat, tau, out_path, gt=None,
                config_label=""):
    n = len(series)
    times = list(series.index)
    t = np.arange(n)
    ts_to_idx = {x: i for i, x in enumerate(times)}

    z = pd.Series(vort["vorticity_smoothed2"].values, index=series.index)
    dz = pd.Series(vort["dz_dt_smoothed2"].values, index=series.index)
    z_raw = pd.Series(vort["zeta"].values, index=series.index)
    rel = _incipient_plateau_rel(geo, "derivative")

    b_geo, b_plat = _lead(geo), _lead(plat)
    seq = lambda d: " > ".join(dict.fromkeys(
        _normalize(k) for k in periods_to_dict(d)))

    dur = (series.index[-1] - series.index[0]).total_seconds() / 86400
    fig = plt.figure(figsize=(17, 13))
    fig.suptitle(
        f"{name}  ·  {n} pts  ·  {dur:.1f} dias  ·  {config_label}\n"
        f"incipient_method: geometric (esq.) vs plateau tau={tau:.2f} (dir.)  ·  "
        f"fronteira {b_geo} -> {b_plat} passos"
        + (f"  ·  ground truth Ic = {gt}" if gt is not None else ""),
        fontsize=11, fontweight="bold", y=0.99)
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.52, wspace=0.10,
                           top=0.90, bottom=0.15)

    cols = [("geometric", geo, b_geo), (f"plateau (tau={tau:.2f})", plat, b_plat)]
    for ci, (label, dfc, bnd) in enumerate(cols):
        panels = [
            ("z", z, C_Z, "z  (vorticidade suavizada)", find_peaks_valleys(z)),
            ("dz", dz, C_DZ, "dz/dt  (1a derivada)", find_peaks_valleys(dz)),
            ("rel", pd.Series(rel, index=series.index), C_REL,
             "|dz| / max|dz|  (perfil de slope)", None),
        ]
        for ri, (key, ser, color, ylab, extr) in enumerate(panels):
            ax = fig.add_subplot(gs[ri, ci])
            _draw_phases(ax, periods_to_dict(dfc), ts_to_idx, n)

            ax2 = ax.twinx()
            ax2.plot(t, z_raw.values, color="#888888", lw=1.4, alpha=0.65, zorder=1)
            ax2.tick_params(axis="y", labelsize=6, colors="#888888", length=3)
            ax2.set_ylabel("original", fontsize=6, color="#888888")
            ax2.set_xlim(-0.5, n - 0.5)

            ax.set_zorder(ax2.get_zorder() + 1)
            ax.patch.set_visible(False)
            ax.axhline(0, color="gray", lw=0.5, ls="--")
            ax.plot(t, ser.values, color=color, lw=1.8, zorder=3)

            npk = nvl = 0
            if extr is not None:
                pk = [i for i, x in enumerate(times) if extr[x] == "peak"]
                vl = [i for i, x in enumerate(times) if extr[x] == "valley"]
                npk, nvl = len(pk), len(vl)
                if pk:
                    ax.scatter(pk, [ser.values[i] for i in pk], color=_BLUE, **MK_PEAK)
                if vl:
                    ax.scatter(vl, [ser.values[i] for i in vl], color=_RED, **MK_VALLEY)

            if bnd > 0:
                ax.axvline(bnd, color="black", lw=2.0, zorder=7)
            if b_plat > 0:
                ax.axvline(b_plat, color=C_PLATEAU, lw=1.6, ls="-", alpha=0.9, zorder=6)
            if gt is not None:
                ax.axvline(gt, color="#00a000", lw=2.0, ls=":", zorder=6)
            for tv in TAUS:
                hits = np.flatnonzero(rel >= tv)
                if hits.size:
                    ax.axvline(int(hits[0]), color=TAU_COLORS[tv], lw=1.0,
                               ls="--", alpha=0.75, zorder=4)
            if key == "rel":
                for tv in TAUS:
                    ax.axhline(tv, color=TAU_COLORS[tv], lw=0.7, ls=":", alpha=0.7)
                ax.axhline(tau, color=C_PLATEAU, lw=1.4, ls="-", alpha=0.9)
                ax.set_ylim(0, 1.02)

            if ri == 0:
                ax.set_title(f"{label}\n{seq(dfc)}\nfronteira = {bnd} passos",
                             fontsize=8.5, pad=6)
            ax.set_ylabel(ylab + (f"\n({npk}p / {nvl}v)" if extr is not None else ""),
                          fontsize=7.5)
            ax.tick_params(labelsize=7)
            ax.set_xlim(-0.5, n - 0.5)
            step = max(1, n // 8)
            tp = list(range(0, n, step))
            ax.set_xticks(tp)
            ax.set_xticklabels([times[i].strftime("%m/%d\n%Hh") for i in tp], fontsize=6)
            if ri == 2:
                ax.set_xlabel("Data/hora", fontsize=8)

    handles = [mpatches.Patch(color=PHASE_COLORS[p], alpha=0.6, label=p.capitalize())
               for p in ALL_PHASES]
    handles += [
        mlines.Line2D([], [], color="#888888", lw=1.4, label="serie original (eixo dir.)"),
        mlines.Line2D([], [], color="black", lw=2.0, label="fronteira do metodo da coluna"),
        mlines.Line2D([], [], color=C_PLATEAU, lw=1.6, label="fronteira plateau (ambas colunas)"),
        mlines.Line2D([], [], color="#00a000", lw=2.0, ls=":", label="ground truth Ic"),
    ]
    handles += [mlines.Line2D([], [], color=TAU_COLORS[x], lw=1.0, ls="--",
                              label=f"tau={x:.2f}") for x in TAUS]
    fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=8,
               frameon=False, bbox_to_anchor=(0.5, 0.015))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tau", type=float, default=0.20)
    args = ap.parse_args()
    tau = args.tau

    rows = []
    print(f"tau = {tau}\n--- real tracks (author's 3c calibration) ---")
    for tid in REAL_TRACKS:
        d = pd.read_csv(CALIB / f"{tid}.csv", sep=";", index_col="time",
                        parse_dates=True)
        s = d["min_max_zeta_850"].rename("zeta")
        vort, geo, plat = run_one(s, AUTHOR_PV, AUTHOR_GP, tau)
        make_figure(tid, s, vort, geo, plat, tau, OUT / "real" / f"{tid}.png",
                    config_label="calibracao do autor (3c)")
        rows.append({"set": "real", "name": tid, "geo": _lead(geo),
                     "plateau": _lead(plat), "gt": None})
        print(f"  {tid}: geometric={_lead(geo)} plateau={_lead(plat)}")

    print("--- synthetic (per-case clean/noisy preset) ---")
    for name, case in CASES.items():
        s = case["series"]
        segs = case["segments"]
        gt = segs[0]["n"] if segs and segs[0]["type"] == "Ic" else None
        grp = "noisy" if name in NOISY_CASE_IDS else "clean"
        vort, geo, plat = run_one(s, preset_for(name), PRESET_GP, tau)
        make_figure(name, s, vort, geo, plat, tau,
                    OUT / "synthetic" / f"{name}.png", gt=gt,
                    config_label=f"SYNTHETIC_{grp.upper()}_PRESET")
        rows.append({"set": "synthetic", "name": name, "geo": _lead(geo),
                     "plateau": _lead(plat), "gt": gt})
        err = (f" err={_lead(plat) - gt:+d}" if gt is not None else "")
        print(f"  {name}: geometric={_lead(geo)} plateau={_lead(plat)} "
              f"gt={gt}{err}")

    t = pd.DataFrame(rows)
    t.to_csv(Path(__file__).resolve().parent / "geometric_vs_plateau.csv", index=False)
    print(f"\nfigures -> {OUT}")
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
