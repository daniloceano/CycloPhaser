#!/usr/bin/env python
"""Front 20(b) stage 2 - before/after figures for 20160735 and 20205386.

Each cyclone gets two stacked panels, params-11 (before) over params-12
(after, mature_min_depth=0.80), sharing the x axis. Phase blocks are shaded,
the human-labelled mature span is drawn as a hatched band, and every surviving
valley is annotated with its D1 so the floor can be read off the figure.
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

from gate_stage2 import load_config, run_one
from labels_core import load_real_series, read_labels

OUT = REPO / "research" / "labels" / "diagnostics" / "item20b"

PHASE_COLOUR = {
    "incipient":       "#cfd8dc",
    "intensification": "#90caf9",
    "mature":          "#ef5350",
    "decay":           "#a5d6a7",
    "residual":        "#ffe082",
}


def panel(ax, f, z, title, floor):
    n = len(z)
    for p, a, b in f["runs"]:
        if p in PHASE_COLOUR:
            ax.axvspan(a - 0.5, b + 0.5, color=PHASE_COLOUR[p], alpha=0.55, lw=0)
    for (la, lb, _u) in f["lab_matures"]:
        ax.axvspan(la - 0.5, lb + 0.5, facecolor="none", edgecolor="black",
                   hatch="///", lw=1.4, zorder=3)
    ax.plot(np.arange(n), z, color="#212121", lw=1.3, zorder=4)

    for v in f["valleys"]:
        i, d1 = v["idx"], v["D1"]
        kept = v["block"] is not None
        ax.plot(i, z[i], marker="v", ms=8, zorder=6,
                color="#1b5e20" if kept else "#b71c1c",
                markeredgecolor="white", markeredgewidth=0.8)
        ax.annotate(f"D1={d1:.3f}", (i, z[i]), textcoords="offset points",
                    xytext=(0, -16), ha="center", fontsize=7.5, zorder=6,
                    color="#1b5e20" if kept else "#b71c1c",
                    fontweight="bold" if kept else "normal")
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_ylabel("z  (filtered ζ, s⁻¹)", fontsize=8)
    ax.tick_params(labelsize=8)
    ax.margins(x=0.01)
    ax.text(0.995, 0.06, f"mature blocks: {f['det'] if f['det'] else 'none'}",
            transform=ax.transAxes, ha="right", fontsize=8,
            bbox=dict(fc="white", ec="#9e9e9e", alpha=0.9, boxstyle="round,pad=0.3"))


def main():
    labels = read_labels()
    real = load_real_series()
    pv, gp11 = load_config("cyclophaser_params-11.yaml")
    _, gp12 = load_config("cyclophaser_params-12.yaml")
    floor = gp12["mature_min_depth"]

    for sid in ("20160735", "20205386"):
        vals = real[sid]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            before = run_one(sid, vals, labels.get(sid), pv, gp11)
            after = run_one(sid, vals, labels.get(sid), pv, gp12)
        from cyclophaser.determine_periods import process_vorticity
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            z = np.asarray(process_vorticity(pd.DataFrame({"zeta": vals}), **pv)
                           .vorticity_smoothed2.values, dtype=float)

        fig, axes = plt.subplots(2, 1, figsize=(11, 6.4), sharex=True)
        panel(axes[0], before, z, f"{sid} — BEFORE: params-11 (no depth floor)", floor)
        panel(axes[1], after, z, f"{sid} — AFTER: params-12, mature_min_depth = {floor}", floor)
        axes[1].set_xlabel("timestep index", fontsize=9)

        handles = [mpatches.Patch(color=c, label=p, alpha=0.55)
                   for p, c in PHASE_COLOUR.items()]
        handles += [
            mpatches.Patch(facecolor="none", edgecolor="black", hatch="///",
                           label="labelled mature (human)"),
            plt.Line2D([], [], marker="v", ls="", color="#1b5e20",
                       markeredgecolor="white", label="valley → generates a block"),
            plt.Line2D([], [], marker="v", ls="", color="#b71c1c",
                       markeredgecolor="white", label="valley → no block"),
        ]
        fig.legend(handles=handles, loc="upper center", ncol=5, fontsize=8,
                   frameon=False, bbox_to_anchor=(0.5, 1.005))
        fig.suptitle("", y=1)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        p = OUT / f"fig_{sid}_before_after.png"
        fig.savefig(p, dpi=160, bbox_inches="tight")
        plt.close(fig)
        print(f"wrote {p}")
        print(f"   before blocks {before['det']}  ->  after {after['det']}")


if __name__ == "__main__":
    main()
