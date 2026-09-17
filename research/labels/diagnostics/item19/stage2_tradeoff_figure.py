#!/usr/bin/env python
"""Item 19/20 stage 2 - the trade-off, drawn. TRAIN split only.

No cell passes the gate, so step 3.4's "before/after for a PASS cell" has nothing
to draw. This draws the closest thing that exists: the only two cells that satisfy
criterion (b) at all (prominence_relative=0.60, mature_amplitude_fraction 0.85 and
0.90), side by side with params-10, for `20160735` - the case (b) is about - and
for the two series that pay for it by losing their mature entirely.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import item19_core as C
from item19_core import OUT
from labels_core import read_labels

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CELL = dict(prominence_relative=0.60, mature_amplitude_fraction=0.90)
SHOW = ["20160735", "20191014", "scfcf1387"]


def main():
    pv, gp0 = C.load_config()
    real, synth = C.load_train_series()
    series = {**real, **synth}
    labels = read_labels()
    sub = {s: series[s] for s in SHOW}

    ref = C.facts_for_config(sub, labels, pv, gp0, want_z=True)
    new = C.facts_for_config(sub, labels, pv, dict(gp0, **CELL), want_z=True)

    fig, axes = plt.subplots(len(SHOW), 2, figsize=(13, 3.1 * len(SHOW)))
    for r, sid in enumerate(SHOW):
        for c, (facts, title) in enumerate((
                (ref, f"params-10  (pr={gp0['prominence_relative']}, "
                      f"maf={gp0['mature_amplitude_fraction']})"),
                (new, f"pr={CELL['prominence_relative']}, "
                      f"maf={CELL['mature_amplitude_fraction']}"))):
            f = facts[sid]
            ax = axes[r, c]
            ax.plot(f["z_unfil"], color="0.75", lw=.8)
            ax.plot(f["z"], color="k", lw=1.3)
            rel = C.extrema_with_prominence(f["z"])
            pr = (gp0 if c == 0 else dict(gp0, **CELL))["prominence_relative"]
            for v in C.surviving(rel["valley"], pr):
                ax.plot(v, f["z"][v], "v", color="#d95f0e", ms=5)
            for k in C.surviving(rel["peak"], pr):
                ax.plot(k, f["z"][k], "^", color="#2c7fb8", ms=5)
            if f["lab_mature"]:
                ax.axvspan(*f["lab_mature"], color="#31a354", alpha=.18)
            for a, b in f["det_matures"]:
                ax.axvspan(a, b, color="#de2d26", alpha=.32)
            ax.set_title(f"{sid} - {title}   ({f['n_det_mature']} mature block(s))",
                         fontsize=9)
            ax.tick_params(labelsize=7)
    axes[0, 0].plot([], [], "v", color="#d95f0e", ms=5, label="surviving z valleys")
    axes[0, 0].plot([], [], "^", color="#2c7fb8", ms=5, label="surviving z peaks")
    axes[0, 0].axvspan(0, 0, color="#31a354", alpha=.18, label="labelled mature")
    axes[0, 0].axvspan(0, 0, color="#de2d26", alpha=.32, label="detected mature")
    axes[0, 0].legend(fontsize=6, loc="lower left")
    fig.suptitle("Stage 2 - the only cells that satisfy criterion (b) break other series",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, .97])
    fig.savefig(OUT / "fig_tradeoff_pr060_maf090.png", dpi=150)
    print("wrote fig_tradeoff_pr060_maf090.png")
    for sid in SHOW:
        print(f"  {sid:12s} params-10 {ref[sid]['n_det_mature']} block(s) "
              f"-> cell {new[sid]['n_det_mature']} block(s)")


if __name__ == "__main__":
    main()
