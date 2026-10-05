#!/usr/bin/env python
"""Methodology figure of the documentation (docs/generated/methodology.png).

    python docs/figures/make_methodology_figure.py

Deterministic: an analytic synthetic vorticity series with seeded noise, run
through the package with its defaults. Every panel is read from the package's
own output or from its public functions; nothing of the package's logic is
reimplemented here:

  A  raw series                    get_periods(...)['z_unfil']
  B  filtered series               process_vorticity(...)['filtered_vorticity'] (defaults)
  C  smoothing (optional, off by   process_vorticity(..., use_smoothing='auto')['vorticity_smoothed']
     default)
  D  series used for detection     get_periods(...)['z']
  E  extrema                       get_periods(...)['z_peaks_valleys'], and the extrema that
                                   find_peaks_valleys finds without the prominence filter but the
                                   defaults discard (crossed out: one weak oscillation, a valley
                                   and a peak, inside the decay)
  F-J what each stage assigns      the public stage functions of cyclophaser.find_stages replayed
                                   in get_periods' order on the returned frame (intensification,
                                   decay, mature, residual, then incipient); the script asserts
                                   that the replay reproduces get_periods' `periods`
  K  final phases                  get_periods(...)['periods']

The layout, colours and legend follow the 2024 figure (de Souza et al., 2024).
The colours were sampled from its legend
(research/cleanup/passo4/old_figure_colors.json in the repository). No
threshold and no number is drawn. The fraction of the series each phase takes is written next to
the figure (methodology_phase_fractions.csv).
"""
import importlib
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

importlib.import_module("cyclophaser.determine_periods")
DP = sys.modules["cyclophaser.determine_periods"]       # the module (the package re-exports the function)
FS = importlib.import_module("cyclophaser.find_stages")

OUT = Path(__file__).resolve().parents[1] / "generated" / "methodology.png"

# colours of the 2024 figure (sampled from its legend; see the docstring)
PHASE_COLORS = {"incipient": "#8aa5f6", "intensification": "#eeeb78", "mature": "#e67d77",
                "decay": "#cee3a8", "residual": "#c0c0c0"}
LINE_COLORS = {"zeta_850": "#717171", "zeta_f": "#ef706a", "zeta_s": "#6889f4", "zeta_s2": "#030408"}


# --- the synthetic series ------------------------------------------------------------------
def synthetic_series():
    """Hourly analytic vorticity (Southern-Hemisphere sign: deeper = more negative):
    a short flat start, a deepening, a longer recovery with a weak ripple, and a
    short re-deepening at the end, plus seeded high-frequency noise (random-phase
    sinusoids with periods of 2.5-8 h, below the filter's high cutoff).

    Design targets, not thresholds (Danilo, round 1): decay the longest phase,
    near half of the series; intensification near a quarter; incipient, mature and
    residual about a tenth or less each; the weak oscillation the prominence
    filter discards lies inside the decay. The shape and the seed were chosen by
    research/cleanup/passo4/methodology_series_search.py in the repository;
    main() asserts the structure and reports the fractions."""
    n = 240
    t = np.arange(n, dtype=float)

    def halfcos(a, b):                       # 0 before a, 1 after b, half-cosine between
        x = np.clip((t - a) / (b - a), 0, 1)
        return 0.5 - 0.5 * np.cos(np.pi * x)

    t0 = 0.05 * n                            # start of the deepening
    tv = t0 + 0.30 * n                       # the deepest point
    t3 = min(tv + 0.62 * n, n - 1)           # end of the recovery
    zeta = (-1e-5
            - 6e-5 * halfcos(t0, tv) * (1 - halfcos(tv, t3))                     # deepening and recovery
            + 0.5e-5 * np.exp(-((t - (tv + 0.55 * (t3 - tv))) / (0.05 * n)) ** 2)  # a weak ripple
            - 1.5e-5 * halfcos(t3, n + 5)                                        # re-deepening at the end
            + 0.3e-5 * np.exp(-((t - t0) / (0.04 * n)) ** 2))                    # the onset peak
    rng = np.random.default_rng(24)
    periods, phases, amps = rng.uniform(2.5, 8.0, 40), rng.uniform(0, 2 * np.pi, 40), rng.standard_normal(40)
    noise = (amps[:, None] * np.sin(2 * np.pi * t[None, :] / periods[:, None] + phases[:, None])).sum(0)
    zeta += 0.6e-5 * noise / noise.std()
    return pd.Series(zeta, index=pd.date_range("2000-01-01", periods=n, freq="h"))


def replay(df):
    """get_periods' stage sequence (intensification, decay, mature, residual,
    post_process_periods, incipient) replayed with the PUBLIC functions on the
    frame get_periods returned, `periods` cleared; returns the frame after
    each step. args_periods is rebuilt from get_periods' own signature defaults."""
    import inspect
    sig = {k: v.default for k, v in inspect.signature(DP.get_periods).parameters.items()
           if v.default is not inspect.Parameter.empty}
    args = {k: v for k, v in sig.items() if k not in ("plot", "plot_steps", "export_dict", "prominence",
                                                      "prominence_relative", "reclassify_index0")}
    d = df.copy()
    d["periods"] = np.nan
    d["periods"] = d["periods"].astype("object")
    steps = {}
    for name, fn in (("intensification", FS.find_intensification_period),
                     ("decay", FS.find_decay_period),
                     ("mature", FS.find_mature_stage),
                     ("residual", FS.find_residual_period),
                     ("post_process", lambda x, **_: DP.post_process_periods(x)),
                     ("incipient", FS.find_incipient_period)):
        d = fn(d.copy(), **args)
        steps[name] = d["periods"].copy()
    return steps


# --- drawing helpers -----------------------------------------------------------------------
def bare_axes(ax, letter, xlabel=True, ylabel=False):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.plot(1, 0, ">k", transform=ax.transAxes, clip_on=False, markersize=4)
    ax.plot(0, 1, "^k", transform=ax.transAxes, clip_on=False, markersize=4)
    ax.text(-0.02, 1.08, f"({letter})", transform=ax.transAxes, fontsize=15, fontweight="bold")
    if xlabel:
        ax.set_xlabel("Time", fontsize=13)
    if ylabel:
        ax.set_ylabel("Vorticity", fontsize=13)


def line(ax, x, y, key, lw=3.5):
    ax.plot(x, y, color=LINE_COLORS[key], lw=lw, solid_capstyle="round")


def extrema(ax, x, z, labels):
    pk = np.flatnonzero(labels == "peak")
    vl = np.flatnonzero(labels == "valley")
    ax.scatter(x[pk], z[pk], s=150, color="k", zorder=5)
    ax.scatter(x[vl], z[vl], s=150, facecolors="white", edgecolors="k", linewidths=2.5, zorder=5)


def shade(ax, x, z, mask, color, top):
    """Fill from the curve up to the top of the panel where `mask` holds, like the 2024 figure."""
    ax.fill_between(x, z, top, where=mask, color=color, step=None, interpolate=False, linewidth=0, zorder=1)


def main():
    warnings.simplefilter("ignore")
    s = synthetic_series()
    zeta_df = pd.DataFrame({"zeta": s.values}, index=s.index)
    vort = DP.process_vorticity(zeta_df)                                # package defaults
    vort_smoothed = DP.process_vorticity(zeta_df, use_smoothing="auto")  # C: the optional smoothing
    df = DP.get_periods(vort)
    assert df.equals(DP.determine_periods(s)), "get_periods on process_vorticity != determine_periods"

    steps = replay(df)
    assert steps["incipient"].equals(df["periods"]), "the replay does not reproduce get_periods' periods"

    # E: the extrema the prominence filter discards
    unfiltered = DP.find_peaks_valleys(df["z"], prominence=None, prominence_relative=None, reclassify_index0=False)
    kept_pos = set(np.flatnonzero(df["z_peaks_valleys"].notna()))
    all_pos = sorted(np.flatnonzero(unfiltered.notna()))
    dropped = sorted(set(all_pos) - kept_pos)
    # designed for: one weak oscillation (a valley and the peak next to it) discarded inside
    # the decay, one full cycle, a flat start and a residual tail
    assert len(dropped) == 2 and all_pos.index(dropped[1]) == all_pos.index(dropped[0]) + 1, dropped
    assert all(df["periods"].iloc[i] == "decay" for i in dropped), dropped
    seq = [p for i, p in enumerate(df["periods"]) if i == 0 or p != df["periods"].iloc[i - 1]]
    assert seq == ["incipient", "intensification", "mature", "decay", "residual"], seq
    fractions = {p: float((df["periods"] == p).mean()) for p in PHASE_COLORS}

    x = np.arange(len(df))
    z = df["z"].values
    labels = df["z_peaks_valleys"].values
    top = z.max() + 0.15 * (z.max() - z.min())
    bottom = z.min() - 0.08 * (z.max() - z.min())

    fig = plt.figure(figsize=(17.5, 12.4))
    gs = fig.add_gridspec(3, 4, hspace=0.42, wspace=0.18, left=0.04, right=0.99, top=0.95, bottom=0.05)
    ax = {k: fig.add_subplot(gs[r, c]) for k, (r, c) in zip("ABCDEFGHIJK", [(r, c) for r in range(3) for c in range(4)])}

    # A-D: the series
    line(ax["A"], x, df["z_unfil"].values, "zeta_850", lw=3)
    line(ax["B"], x, vort["filtered_vorticity"].values, "zeta_f")
    line(ax["C"], x, vort_smoothed["vorticity_smoothed"].values, "zeta_s")
    ax["C"].text(0.97, 0.06, "optional", transform=ax["C"].transAxes, ha="right", fontsize=13, style="italic")
    line(ax["D"], x, z, "zeta_s2")

    # E: extrema, with the discarded one crossed out
    line(ax["E"], x, z, "zeta_s2")
    extrema(ax["E"], x, z, labels)
    for i in dropped:
        ax["E"].scatter(x[i], z[i], s=150, facecolors="white", edgecolors="0.55", linewidths=2, zorder=5)
        ax["E"].scatter(x[i], z[i], s=260, marker="x", color="k", linewidths=2.5, zorder=6)

    # F-J: what each stage assigns (the replay, in get_periods' order)
    order = [("F", "intensification", "intensification"), ("G", "decay", "decay"),
             ("H", "mature", "mature"), ("I", "residual", None), ("J", "incipient", None)]
    prev = None
    names = list(steps)
    for letter, step, phase in order:
        cur = steps[step]
        if phase is not None:                    # the cells this stage's phase holds after it ran
            mask = (cur == phase).values
            color_of = {phase: PHASE_COLORS[phase]}
        else:                                    # the cells this stage changed, by their new phase
            before = steps[names[names.index(step) - 1]]
            mask = (cur.fillna("") != before.fillna("")).values
            color_of = {p: PHASE_COLORS[p] for p in pd.unique(cur[mask])}
        for p, c in color_of.items():
            shade(ax[letter], x, z, mask & (cur == p).values, c, top)
        line(ax[letter], x, z, "zeta_s2")
        extrema(ax[letter], x, z, labels)

    # K: final phases, with the raw series over them
    for p, c in PHASE_COLORS.items():
        shade(ax["K"], x, z, (df["periods"] == p).values, c, top)
    line(ax["K"], x, z, "zeta_s2")
    twin = ax["K"].twinx()
    twin.plot(x, df["z_unfil"].values, color=LINE_COLORS["zeta_850"], lw=2.5, alpha=0.9)
    twin.set_yticks([])
    for side in ("top", "right"):
        twin.spines[side].set_visible(False)

    for k, a in ax.items():
        if k not in "ABCD":
            a.set_ylim(bottom, top)
        bare_axes(a, k, ylabel=k in "AEI")

    # legend in the last cell
    leg = fig.add_subplot(gs[2, 3])
    leg.axis("off")
    phase_handles = [Patch(color=PHASE_COLORS[p], label=p.capitalize()) for p in PHASE_COLORS]
    line_handles = [Line2D([], [], color=LINE_COLORS[k], lw=4, label=lab) for k, lab in
                    [("zeta_850", r"$\zeta_{850}$"), ("zeta_f", r"$\zeta_{f}$"), ("zeta_s", r"$\zeta_{s}$"),
                     ("zeta_s2", r"$\zeta_{s^2}$")]]
    marker_handles = [Line2D([], [], marker="o", color="k", ls="", markersize=11, label="Peak"),
                      Line2D([], [], marker="o", markerfacecolor="white", markeredgecolor="k", markeredgewidth=2,
                             ls="", markersize=11, label="Valley"),
                      Line2D([], [], marker="x", color="k", ls="", markersize=12, markeredgewidth=2.5,
                             label="Discarded (weak)")]
    first = leg.legend(handles=phase_handles, loc="upper left", fontsize=14, frameon=False, handlelength=2.4,
                       handleheight=1.2, bbox_to_anchor=(-0.02, 1.0))
    leg.add_artist(first)
    leg.legend(handles=line_handles, loc="upper left", fontsize=14, frameon=False, handlelength=2.0,
               bbox_to_anchor=(0.62, 1.0))
    leg.add_artist(leg.get_legend())
    leg.legend(handles=marker_handles, loc="upper left", fontsize=14, frameon=False, handlelength=1.5,
               bbox_to_anchor=(-0.02, 0.38))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=100, metadata={"Software": None})
    OUT.with_name("methodology_phase_fractions.csv").write_text(
        "phase,fraction of the series\n" + "".join(f"{p},{f:.3f}\n" for p, f in fractions.items()))
    print(f"written {OUT.name}; replay reproduces periods: True; discarded extrema: {len(dropped)} "
          f"(one oscillation, inside the decay); fractions: "
          + ", ".join(f"{p} {f:.3f}" for p, f in fractions.items()))


if __name__ == "__main__":
    main()
