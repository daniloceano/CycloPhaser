#!/usr/bin/env python
"""Stage 1 — one figure per refused series.

Three stacked panels per series:
  top     raw zeta and the filtered/smoothed curve the detector consumes, with
          the manual label's incipient boundary and the detector's phase opening;
  middle  the same, zoomed to the first 3*max(N_lab, k) steps, where the decision
          is actually made;
  bottom  the plateau probe rel(t) with tau, the k-window at index 0 whose
          minimum is the decisive statistic, and every sustained run.

The series are re-run through the detector here rather than reading arrays back
from refusal.json, and the boundary is asserted against the value diagnose.py
recorded, so the figure cannot drift from the table.
"""
from __future__ import annotations

import importlib
import json
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import load_real_series, read_labels, read_split  # noqa: E402
from evaluate_against_labels import load_config  # noqa: E402

OUT = Path(__file__).resolve().parent
CONFIG = REPO / "research/labels/configs/cyclophaser_params-13.yaml"
ROWS = {r["id"]: r for r in json.loads((OUT / "refusal.json").read_text())["rows"]}
SIX = ["20160587", "20160735", "20171179", "20180628", "20181046", "20202023"]


def main() -> int:
    split = read_split()
    assert not (set(SIX) & set(split["test"])), "test-split id in the figure list"
    records = read_labels()
    real = load_real_series()
    pv, gp = load_config(CONFIG)
    dp = importlib.import_module("cyclophaser.determine_periods")
    from cyclophaser.find_stages import (
        _incipient_plateau_boundary, _incipient_plateau_rel,
    )

    tau = float(gp["incipient_plateau_tau"])
    k = int(gp["incipient_plateau_k"])

    for sid in SIX:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = dp.process_vorticity(pd.DataFrame({"zeta": real[sid]}), **pv)
            res = dp.get_periods(vort, **gp)
        raw = np.asarray(vort["zeta"].values, dtype=float)
        filt = np.asarray(vort["vorticity_smoothed2"].values, dtype=float)
        df = pd.DataFrame({"dz": np.asarray(vort["dz_dt_smoothed2"].values, float),
                           "z_unfil": raw})
        rel = _incipient_plateau_rel(df, gp["incipient_plateau_signal"],
                                     gp["incipient_smooth_window"],
                                     gp["incipient_smooth_polyorder"])
        boundary = int(_incipient_plateau_boundary(
            rel, tau, gp["incipient_plateau_crossing"], k))
        assert boundary == ROWS[sid]["boundary"], f"{sid}: figure/table disagree"

        n_lab = int(records[sid]["verdict"]["incipient_end_idx"])
        tol = int(records[sid]["tolerance_idx"])
        head_min = float(np.min(rel[:k]))
        periods = list(res["periods"].astype(str))
        first_phase = periods[0]
        # the first index at which the detected phase changes
        chg = next((i for i, p in enumerate(periods) if p != first_phase), len(periods))

        above = rel >= tau
        run = np.convolve(above.astype(int), np.ones(k, int), mode="valid")
        runs = np.flatnonzero(run == k)

        zoom = min(len(raw), max(2 * max(n_lab, k) + 5, 20))
        fig, axes = plt.subplots(3, 1, figsize=(11, 9.5))
        fig.suptitle(
            f"{sid} — plateau incipient REFUSED under params-13  "
            f"(path R1: min(rel[0:{k}]) = {head_min:.4f} $\\geq$ "
            f"$\\tau$ = {tau})\n"
            f"label: incipient = [0, {n_lab}), tolerance $\\pm${tol}   |   "
            f"detector: no incipient, opens with '{first_phase}'   |   "
            f"n = {len(raw)} steps",
            fontsize=10.5)

        for ax, hi, tag in ((axes[0], len(raw), "full series"),
                            (axes[1], zoom, f"first {zoom} steps (where it is decided)")):
            x = np.arange(hi)
            ax.plot(x, raw[:hi], color="0.6", lw=1.0, label=r"raw $\zeta$")
            ax.plot(x, filt[:hi], color="tab:blue", lw=1.6,
                    label=r"filtered $\zeta$ (what the detector reads)")
            ax.axvspan(0, max(n_lab - 1, 0), color="tab:green", alpha=0.13,
                       label=f"label: incipient [0, {n_lab})")
            ax.axvline(n_lab, color="tab:green", ls="--", lw=1.6,
                       label=f"label boundary = {n_lab}")
            if chg < hi:
                ax.axvline(chg, color="tab:red", ls=":", lw=1.6,
                           label=f"detector's first phase change = {chg}")
            ax.axvspan(0, k - 1, color="tab:orange", alpha=0.18,
                       label=f"the k={k} window the criterion reads")
            ax.set_ylabel(r"$\zeta$  (s$^{-1}$)")
            ax.set_title(tag, fontsize=9, loc="left")
            ax.grid(alpha=0.25)
        axes[0].legend(fontsize=7.5, loc="best", ncol=2)

        ax = axes[2]
        x = np.arange(len(rel))
        ax.plot(x, rel, color="tab:purple", lw=1.3,
                label=r"rel$(t)=|d\zeta_{raw}/dt|\,/\,\max$  (probe, savgol w=5)")
        ax.axhline(tau, color="k", ls="--", lw=1.4, label=fr"$\tau$ = {tau}")
        ax.axvspan(0, k - 1, color="tab:orange", alpha=0.25,
                   label=fr"rel[0:{k}], min = {head_min:.4f}  $\geq\tau$  $\Rightarrow$ "
                         fr"run starts at 0  $\Rightarrow$ boundary = 0")
        ax.plot(np.arange(k), rel[:k], "o", color="tab:orange", ms=5)
        for j, s in enumerate(runs):
            ax.axvspan(s, s + k - 1, color="tab:red", alpha=0.10,
                       label="sustained runs ($k$ consecutive $\\geq\\tau$)" if j == 0 else None)
        ax.axvline(n_lab, color="tab:green", ls="--", lw=1.6,
                   label=f"label boundary = {n_lab}")
        ax.set_xlim(0, min(len(rel), max(zoom, 40)))
        ax.set_ylim(0, 1.02)
        ax.set_xlabel("index")
        ax.set_ylabel("rel")
        ax.set_title("where the plateau criterion is evaluated", fontsize=9, loc="left")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=7.5, loc="upper right")

        fig.tight_layout(rect=(0, 0, 1, 0.94))
        p = OUT / f"fig_{sid}_refusal.png"
        fig.savefig(p, dpi=130)
        plt.close(fig)
        print(f"wrote {p.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
