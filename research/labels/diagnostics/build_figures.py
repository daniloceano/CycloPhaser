#!/usr/bin/env python
"""Before/after figures for the 4 affected TRAIN tracks.

READ-ONLY with respect to the package. Uses the CURRENT (post-fix) code to get
z / z_unfil (unaffected by the fix -- process_vorticity is untouched) and
reads the already-produced fix_state_before.json / fix_state_after.json for
the periods and z_peaks_valleys arrays (before = pre-fix, after = post-fix).
Manual label phases are transcribed from labels_affected.md / manual_labels.yaml
(TRAIN tracks only).

Run:
    ~/miniconda3/envs/south_atlantic_cyclone_extremes/bin/python \
        research/labels/diagnostics/build_figures.py

Writes (unversioned unless the user later commits them):
    research/labels/diagnostics/figures/<track_id>_before_after.png
"""
import json
import sys
import warnings
from pathlib import Path

DIAG_DIR = Path(__file__).resolve().parent
FIG_DIR = DIAG_DIR / "figures"
REPO_ROOT = DIAG_DIR.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS_DIR))
sys.path.insert(0, str(REPO_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from labels_core import load_real_series, read_labels, phase_sequence, PHASE_COLORS  # noqa: E402
from cyclophaser.determine_periods import process_vorticity, get_periods  # noqa: E402

CONFIG_PATH = Path.home() / "Downloads" / "cyclophaser_params-9.yaml"
PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")

TARGETS = ["20180170", "20180608", "20190325", "20191014"]


def load_config(path):
    import inspect
    doc = yaml.safe_load(path.read_text()) or {}
    gp_accepted = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_accepted}
    return pv, gp


def phase_spans(periods):
    spans = []
    cur, start = None, 0
    for i, p in enumerate(periods + [None]):
        if p != cur:
            if cur is not None:
                spans.append((cur, start, i - 1))
            cur, start = p, i
    return spans


def draw_phase_bar(ax, spans, y, height, colors, label_prefix=""):
    for phase, s, e in spans:
        base = phase.split(" ")[0] if phase else phase
        color = colors.get(base, "black") if phase else "white"
        ax.axvspan(s - 0.5, e + 0.5, ymin=y, ymax=y + height,
                   color=color, alpha=0.85, lw=0)


def main():
    pv, gp = load_config(CONFIG_PATH)
    real = load_real_series()
    records = read_labels()

    before = json.loads((DIAG_DIR / "fix_state_before.json").read_text())["tracks"]
    after = json.loads((DIAG_DIR / "fix_state_after.json").read_text())["tracks"]

    for sid in TARGETS:
        values = real[sid]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            df = get_periods(vort, **gp)  # current (post-fix) code; z/z_unfil unaffected by fix
        z = df["z"].values
        n = len(z)
        x = list(range(n))

        periods_before = before[sid]["periods"]
        periods_after = after[sid]["periods"]
        zpv_before = before[sid]["z_peaks_valleys"]
        zpv_after = after[sid]["z_peaks_valleys"]

        rec = records.get(sid)
        label_spans = None
        if rec is not None:
            seq = phase_sequence(rec)  # [(phase, start_idx), ...]
            label_spans = []
            for i, (phase, start) in enumerate(seq):
                end = (seq[i + 1][1] - 1) if i + 1 < len(seq) else n - 1
                label_spans.append((phase, start, end))

        fig, axes = plt.subplots(4, 1, figsize=(11, 9), sharex=True,
                                  gridspec_kw={"height_ratios": [3, 0.5, 0.5, 0.5]})
        ax_z, ax_before, ax_after, ax_label = axes

        ax_z.plot(x, z, color="black", lw=1.2, label="z (filtered vorticity)")
        for i, v in enumerate(zpv_before):
            if v == "peak":
                ax_z.plot(i, z[i], "^", color="tab:orange", ms=7 if i == 0 else 5,
                          mec="black" if i == 0 else None, mew=1.4 if i == 0 else 0,
                          zorder=5)
            elif v == "valley":
                ax_z.plot(i, z[i], "v", color="tab:blue", ms=7 if i == 0 else 5,
                          mec="black" if i == 0 else None, mew=1.4 if i == 0 else 0,
                          zorder=5)
        ax_z.axvline(0, color="red", ls=":", lw=1, alpha=0.6)
        ax_z.annotate("idx 0", xy=(0, z[0]), xytext=(n * 0.03, z[0]),
                      fontsize=8, color="red")
        ax_z.set_ylabel("z")
        ax_z.set_title(f"{sid}  (n={n})  —  idx0: before={zpv_before[0]!r}  after={zpv_after[0]!r}")
        ax_z.legend(loc="upper right", fontsize=8,
                    handles=[
                        plt.Line2D([0], [0], marker="^", color="w", markerfacecolor="tab:orange",
                                   markersize=7, label="peak"),
                        plt.Line2D([0], [0], marker="v", color="w", markerfacecolor="tab:blue",
                                   markersize=7, label="valley"),
                    ])

        draw_phase_bar(ax_before, phase_spans(periods_before), 0, 1, PHASE_COLORS)
        ax_before.set_yticks([])
        ax_before.set_ylabel("before", rotation=0, ha="right", va="center", fontsize=9)

        draw_phase_bar(ax_after, phase_spans(periods_after), 0, 1, PHASE_COLORS)
        ax_after.set_yticks([])
        ax_after.set_ylabel("after", rotation=0, ha="right", va="center", fontsize=9)

        if label_spans is not None:
            draw_phase_bar(ax_label, label_spans, 0, 1, PHASE_COLORS)
        ax_label.set_yticks([])
        ax_label.set_ylabel("rótulo", rotation=0, ha="right", va="center", fontsize=9)
        ax_label.set_xlabel("index (timestep)")

        handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in PHASE_COLORS.values()]
        fig.legend(handles, list(PHASE_COLORS.keys()), loc="lower center", ncol=5,
                   fontsize=8, bbox_to_anchor=(0.5, -0.02))

        fig.tight_layout()
        out_path = FIG_DIR / f"{sid}_before_after.png"
        fig.savefig(out_path, dpi=140, bbox_inches="tight")
        plt.close(fig)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
