#!/usr/bin/env python
"""20190639 — the one track C2's `peak->valley` branch fires on: figure + block table.

The scoring function calls this a loss, because an extra phase makes the
sequence mismatch and `score_phase_sequences` then refuses to pair boundaries at
all. That verdict hides what actually moved, which is why this exists:

    label : incipient[0,25)  intensification@25±5  mature@81±6  decay@106±8
    base  : incipient[0,13)  intensification@13    mature@88    decay@105
    C2    : incipient[0,13)  decay[13,26)  intensification@26  mature@88  decay@105

So C2 does not move the mature or the final decay at all, and it moves the
intensification start from 13 (error 12, outside a ±5 tolerance) to 26 (error 1,
inside it). What it adds is a 13-step `decay` block over [13, 26) — a stretch the
labeller called `incipient`.

Reclassification or regression is a judgement call about that block, and this
script draws it rather than scoring it.

Measurement only; the mirror force lives in `common.py`, never in the package.

Run:
    python research/labels/diagnostics/frontA_idx0_c2/fig_20190639.py \
        --config research/labels/configs/cyclophaser_params-13.yaml \
        --outdir research/labels/diagnostics/frontA_idx0_c2/outputs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import phase_starts, provenance, replay, seq_str, sha256_of  # noqa: E402

from labels_core import PHASE_COLORS, load_real_series, read_labels, series_sha256  # noqa: E402
from evaluate_against_labels import load_config  # noqa: E402

from cyclophaser.find_stages import (  # noqa: E402
    _incipient_plateau_boundary, _incipient_plateau_rel,
)

TRACK = "20190639"


def blocks(starts, n):
    """[(phase, start, end_exclusive), ...] from [(phase, start), ...]."""
    out = []
    for k, (p, i) in enumerate(starts):
        j = starts[k + 1][1] if k + 1 < len(starts) else n
        out.append((p, i, j))
    return out


def label_blocks(rec, n):
    starts = [(p["phase"], int(p["start_idx"])) for p in rec["phases"]]
    return blocks(starts, n)


def ribbon(ax, blks, y, h, label):
    for phase, i, j in blks:
        ax.add_patch(plt_rect(i - 0.5, y, j - i, h,
                              PHASE_COLORS.get(phase, "white")))
    ax.text(-0.012, y + h / 2, label, transform=ax.get_yaxis_transform(),
            ha="right", va="center", fontsize=8)


def plt_rect(x, y, w, h, color):
    import matplotlib.patches as mpatches
    return mpatches.Rectangle((x, y), w, h, facecolor=color, edgecolor="white",
                              lw=0.6, alpha=0.85)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--track", default=TRACK)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    provenance()
    pv, gp = load_config(a.config)
    print(f"config: {a.config}\n  sha256: {sha256_of(a.config)}\n")

    values = load_real_series()[a.track]
    rec = read_labels()[a.track]
    if rec["series_sha256"] != series_sha256(values):
        raise SystemExit("label is stale for this series")
    n = len(values)

    base = replay(values, pv, gp, force="none", verify=True)
    assert base["replay_ok"] is True
    c2 = replay(values, pv, gp, force="all_valley", verify=False)

    rel = _incipient_plateau_rel(base["df"], gp["incipient_plateau_signal"],
                                 gp["incipient_smooth_window"],
                                 gp["incipient_smooth_polyorder"])
    boundary = int(_incipient_plateau_boundary(
        rel, gp["incipient_plateau_tau"], gp["incipient_plateau_crossing"],
        gp["incipient_plateau_k"]))

    lab_b = label_blocks(rec, n)
    base_b = blocks(phase_starts(base["final"]), n)
    c2_b = blocks(phase_starts(c2["final"]), n)

    print(f"track {a.track}, n={n}, incipient boundary (H) = {boundary}")
    print(f"  rotulo : {' '.join(f'{p}[{i},{j})' for p, i, j in lab_b)}")
    print(f"  base   : {' '.join(f'{p}[{i},{j})' for p, i, j in base_b)}")
    print(f"  C2     : {' '.join(f'{p}[{i},{j})' for p, i, j in c2_b)}")

    # per-boundary errors, sequence match or not
    rows = []
    for k, p in enumerate(rec["phases"]):
        if k == 0:
            continue
        lidx, tol = int(p["start_idx"]), int(p["tolerance_idx"])
        det_b = next((i for q, i in phase_starts(base["final"]) if q == p["phase"]), None)
        det_c = next((i for q, i in phase_starts(c2["final"]) if q == p["phase"]), None)
        rows.append({"fase": p["phase"], "rotulo": lidx, "tol": tol,
                     "base": det_b, "erro_base": None if det_b is None else abs(det_b - lidx),
                     "C2": det_c, "erro_C2": None if det_c is None else abs(det_c - lidx),
                     "unsure": bool(p.get("unsure"))})
    tab = pd.DataFrame(rows)
    print()
    print(tab.to_string(index=False))
    print("\n  (first occurrence of each phase name; the sequence metric refuses to")
    print("   pair anything at all once an extra phase appears)")
    out_csv = a.outdir / f"fig_{a.track}_blocks.csv"
    pd.DataFrame([{"fonte": "rotulo", "blocos": " ".join(f"{p}[{i},{j})" for p, i, j in lab_b)},
                  {"fonte": "base", "blocos": " ".join(f"{p}[{i},{j})" for p, i, j in base_b)},
                  {"fonte": "C2", "blocos": " ".join(f"{p}[{i},{j})" for p, i, j in c2_b)}]
                 ).to_csv(out_csv, index=False)
    tab.to_csv(a.outdir / f"fig_{a.track}_boundaries.csv", index=False)
    print(f"\nwrote {out_csv}")

    # ── figure ──────────────────────────────────────────────────────────────
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    z = np.asarray(base["df"]["z"], dtype=float)
    zr = np.asarray(values, dtype=float)

    fig, (ax, axr) = plt.subplots(2, 1, figsize=(12, 7),
                                  gridspec_kw={"height_ratios": [3, 1.15]},
                                  sharex=True)

    ax.plot(range(n), zr, color="0.72", lw=1.0, label="zeta (raw)")
    ax.plot(range(n), z, color="k", lw=1.6, label="z (filtrado)")
    for i, t in enumerate(base["df"]["z_peaks_valleys"]):
        if t == "peak":
            ax.plot(i, z[i], "^", color="tab:blue", ms=7, zorder=5)
        elif t == "valley":
            ax.plot(i, z[i], "v", color="tab:red", ms=7, zorder=5)
    ax.plot([], [], "^", color="tab:blue", ms=7, label="z peak (lista final)")
    ax.plot([], [], "v", color="tab:red", ms=7, label="z valley (lista final)")
    ax.axvline(boundary - 0.5, color="magenta", ls="--", lw=1.2,
               label=f"boundary de H = {boundary}")
    span = z.max() - z.min()
    ax.annotate("indice 0: 'peak'\n(C2 reclassifica para 'valley')",
                xy=(0, z[0]), xytext=(14, z[0] - 0.22 * span),
                fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.9))
    e1 = 25
    ax.annotate(f"E1 = {e1}, 'peak', z[E1] > z[0]\n(o que faz C2 disparar)",
                xy=(e1, z[e1]), xytext=(e1 + 14, z[e1] - 0.14 * span),
                fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.9))
    ax.axvspan(13 - 0.5, 26 - 0.5, color="k", alpha=0.06, lw=0)
    ax.set_ylabel("vorticidade")
    ax.set_title(f"{a.track} — params-13 — o unico disparo do ramo pico->vale de C2",
                 fontsize=11, loc="left", pad=10)
    ax.margins(y=0.08)
    ax.legend(loc="lower right", fontsize=8, ncol=2)

    axr.set_ylim(0, 3)
    axr.set_yticks([])
    for y, (blks, name) in zip((2.05, 1.05, 0.05),
                               ((lab_b, "rotulo"), (base_b, "base"), (c2_b, "C2"))):
        ribbon(axr, blks, y, 0.8, name)
        for phase, i, j in blks:
            if j - i >= 8:
                axr.text((i + j) / 2, y + 0.4, phase, ha="center", va="center",
                         fontsize=7.5)
    axr.axvline(13 - 0.5, color="k", lw=0.8, ls=":")
    axr.axvline(26 - 0.5, color="k", lw=0.8, ls=":")
    axr.set_xlim(-2, n + 1)
    axr.set_xlabel("indice")
    axr.set_title("o bloco em disputa e [13, 26): 'incipient' para o rotulo, "
                  "'decay' para C2. A intensificacao sai de 13 (erro 12) para 26 "
                  "(erro 1, tolerancia ±5).", fontsize=8.5, loc="left")

    fig.tight_layout()
    png = a.outdir / f"fig_{a.track}_c2.png"
    fig.savefig(png, dpi=150)
    print(f"wrote {png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
