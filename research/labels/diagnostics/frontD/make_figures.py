#!/usr/bin/env python
"""Front D, stage 0 — one figure per C1 series: raw and filtered at the opening.

Marks N_det (detected incipient end), N_lab (the manual label's incipient end,
omitted when the label says there is none) and, for each cut k, the detected
incipient end re-expressed in ABSOLUTE index.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import load_real_series, load_synthetic_series  # noqa: E402
from evaluate_against_labels import load_config  # noqa: E402

CONFIG = REPO / "research/labels/configs/cyclophaser_params-13.yaml"
OUT = Path(__file__).resolve().parent
WINDOW = 30   # steps of the opening to draw


def main() -> int:
    census = {r["id"]: r for r in json.loads((OUT / "census.json").read_text())["rows"]}
    anchors = json.loads((OUT / "anchoring.json").read_text())
    real = load_real_series()
    synth, _ = load_synthetic_series()
    series = {**real, **synth}
    pv, gp = load_config(CONFIG)
    from cyclophaser.determine_periods import process_vorticity

    for a in anchors:
        sid = a["id"]
        s = series[sid]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": s}), **pv)
        raw = vort["zeta"].values
        filt = vort["filtered_vorticity"].values
        n = min(WINDOW, len(raw))
        x = range(n)

        fig, ax = plt.subplots(figsize=(9, 4.6))
        ax.plot(x, raw[:n], color="#888888", lw=1.2, marker="o", ms=3,
                label="raw $\\zeta$")
        ax.plot(x, filt[:n], color="#1f77b4", lw=2.0,
                label="filtered $\\zeta$ (Lanczos, edge padding)")

        ax.axvline(a["L"], color="#d62828", lw=2.0,
                   label=f"$N_{{det}}$ = {a['L']} (detected incipient end)")
        if a["N_lab"] is not None:
            if a["N_lab"] > 0:
                ax.axvline(a["N_lab"], color="#2a9d8f", lw=2.0, ls="--",
                           label=f"$N_{{lab}}$ = {a['N_lab']} (manual label)")
            else:
                ax.plot([], [], " ", label="$N_{lab}$ = 0 — label says NO incipient")

        for c in a["cuts"]:
            if c["abs_end"] is None:
                ax.plot([], [], " ",
                        label=f"cut k={c['k']}: no incipient detected")
                continue
            ax.axvline(c["abs_end"], color="#f7b538", lw=1.4, ls=":",
                       label=f"cut k={c['k']}: end at abs idx {c['abs_end']} "
                             f"(len {c['N_det_cut']})")
            ax.axvspan(-0.5, c["k"] - 0.5, color="#f7b538", alpha=0.10)

        ax.set_xlim(-0.5, n - 0.5)
        ax.set_xlabel("index (original series)")
        ax.set_ylabel("vorticity")
        ax.set_title(f"{sid} ({a['source']}) — opening {n} steps, params-13\n"
                     f"(a) {'PASS' if a['a_pass'] else 'FAIL'} · "
                     f"(b) {a['b']} · verdict: {a['verdict']}", fontsize=10)
        ax.legend(fontsize=7.5, loc="best", framealpha=0.9)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        p = OUT / f"fig_{sid}_opening.png"
        fig.savefig(p, dpi=140)
        plt.close(fig)
        print(f"wrote {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
