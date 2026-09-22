#!/usr/bin/env python
"""Front C - before/after figures for 20180733 and 20180654.

Each cyclone gets two stacked panels sharing the x axis: params-12 (before)
over params-13 (after, intensification_min_depth=0.05). Phase blocks are
shaded, the manual label's phase sequence is drawn as a strip beneath, and
every raw intensification segment is annotated with its D2 so the floor can be
read straight off the figure.

20180654 is in the frozen TEST split; it is plotted here under the explicit
authorisation recorded in report_test_series.py and docs/future_work.md.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import load_real_series, normalize_phase, read_labels
from cyclophaser.determine_periods import get_periods, process_vorticity
from d2_separation import load_config, segments
from measure_frontC import runs_of

OUT = REPO / "research" / "labels" / "diagnostics" / "frontC"

PHASE_COLOUR = {
    "incipient":       "#cfd8dc",
    "intensification": "#90caf9",
    "mature":          "#ef5350",
    "decay":           "#a5d6a7",
    "residual":        "#ffe082",
}


def run(values, pv, gp):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        df = get_periods(vort, **gp)
    periods = [normalize_phase(str(x)) for x in df["periods"]]
    return df, periods, runs_of(periods)


def panel(ax, z, runs, segs, title, floor):
    for p, a, b in runs:
        if p in PHASE_COLOUR:
            ax.axvspan(a - 0.5, b + 0.5, color=PHASE_COLOUR[p], alpha=0.55, lw=0)
    ax.plot(np.arange(len(z)), z, color="0.15", lw=1.4, zorder=5)

    for sg in segs:
        rejected = floor is not None and sg["D2"] < floor
        ax.annotate(
            f"D2={sg['D2']:.4f}" + ("\nREJECTED" if rejected else ""),
            xy=((sg["start"] + sg["end"]) / 2, ax.get_ylim()[1]),
            xytext=(0, -12), textcoords="offset points",
            ha="center", va="top", fontsize=7.5, zorder=6,
            color="#b71c1c" if rejected else "#1a237e",
            fontweight="bold" if rejected else "normal",
        )
        ax.plot([sg["start"], sg["end"]],
                [z[sg["start"]], z[sg["end"]]],
                ls="--", lw=1.0, color="#b71c1c" if rejected else "#1a237e", zorder=6)

    ax.set_title(title, fontsize=10, loc="left")
    ax.set_ylabel("z (filtered vorticity)", fontsize=8)
    ax.tick_params(labelsize=8)


def label_strip(ax, rec, n):
    if not rec:
        ax.set_visible(False)
        return
    ph = rec["phases"]
    for k, p in enumerate(ph):
        s = p["start_idx"]
        e = (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph) else rec["n_steps"] - 1
        name = normalize_phase(p["phase"])
        ax.axvspan(s - 0.5, e + 0.5, color=PHASE_COLOUR.get(name, "0.8"), alpha=0.85, lw=0)
        ax.text((s + e) / 2, 0.5, name[:6], ha="center", va="center", fontsize=7)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_yticks([])
    ax.set_ylabel("manual\nlabel", fontsize=8, rotation=0, ha="right", va="center")
    ax.tick_params(labelsize=8)


def main():
    pv, gp12 = load_config("cyclophaser_params-12.yaml")
    _, gp13 = load_config("cyclophaser_params-13.yaml")
    floor = gp13["intensification_min_depth"]
    labels = read_labels()
    series = load_real_series()

    for sid in ("20180733", "20180654"):
        values = series[sid]
        df12, p12, r12 = run(values, pv, gp12)
        _, p13, r13 = run(values, pv, gp13)
        z = df12["z"].to_numpy(float)
        segs = segments(df12.copy(), gp12)

        fig, axes = plt.subplots(
            3, 1, figsize=(11, 7), sharex=True,
            gridspec_kw={"height_ratios": [1, 1, 0.16], "hspace": 0.28})
        panel(axes[0], z, r12, segs,
              f"{sid} — BEFORE  (params-12, no intensification floor)", None)
        panel(axes[1], z, r13, segs,
              f"{sid} — AFTER  (params-13, intensification_min_depth={floor})", floor)
        label_strip(axes[2], labels.get(sid), len(z))
        axes[2].set_xlabel("time step index", fontsize=9)

        handles = [mpatches.Patch(color=c, label=p, alpha=0.55)
                   for p, c in PHASE_COLOUR.items()]
        axes[0].legend(handles=handles, ncol=5, fontsize=8, loc="lower left",
                       frameon=False, bbox_to_anchor=(0, 1.12))

        note = ("TEST split — plotted under explicit authorisation"
                if sid == "20180654" else "TRAIN split")
        fig.text(0.995, 0.005, note, ha="right", va="bottom", fontsize=7.5, color="0.35")

        out = OUT / f"fig_{sid}_before_after.png"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"wrote {out}")
        print(f"  before: {r12}")
        print(f"  after : {r13}")


if __name__ == "__main__":
    main()
