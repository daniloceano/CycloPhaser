"""The per-cyclone phase figures of the Benchmark and Compare pages — no Streamlit.

Moved out of benchmark_tab.py unchanged (benchmark review, I1) so the Compare
page draws exactly what the Benchmark draws. The only addition is the `colors`
argument: the Benchmark passes its own copy of the phase palette, as before, and
the Compare page passes the app's single source (`layer_inspector.PHASE_COLORS`).
The two are the same values (tests/test_phase_colors.py), and
tests/test_compare_apptest.py checks that the Benchmark's PNGs are byte-identical
to the ones the code produced before the move.

The Grid's compact convention (app.py `_plot_compact`), item 30c: the raw series
and `vorticity_smoothed2` — the series detection runs on — each on a y axis of
its own (twinx), raw drawn in front. The raw series spans 2-3x the smoothed one,
so one shared axis would flatten the curve that explains the bands. The smoothed
curve is the COLUMN's own (computed with that column's filter_params); a column
without one draws raw only. A PNG has no hover; the left axis carries the raw
values.
"""

from __future__ import annotations

import io

import matplotlib
import matplotlib.pyplot as plt

RAW_COLOR = "dimgray"
FILTERED_COLOR = "#e63946"
TOLERANCE_COLOR = "#222222"


def draw_tolerances(ax, spans) -> None:
    """The label's tolerance at each boundary, on `ax`.

    `spans` is ((lo, hi, start, unsure), ...): a hatched band over [lo, hi] (the
    detected boundaries the sequence instrument accepts, start_idx ±
    tolerance_idx, clipped to the series) and a thin line at the label's start.
    A boundary the labeller marked unsure is excluded from that instrument, so
    it gets a dashed line and no band.
    """
    for lo, hi, start, unsure in spans:
        if unsure:
            ax.axvline(start, color=TOLERANCE_COLOR, lw=0.8, ls=(0, (2, 2)),
                       zorder=1)
            continue
        ax.axvspan(lo, hi, facecolor="none", edgecolor=TOLERANCE_COLOR,
                   hatch="////", lw=0, zorder=1)
        ax.axvline(start, color=TOLERANCE_COLOR, lw=0.8, zorder=1)


def draw_panel(ax, values_tuple, runs, z_tuple, colors, z_lim=None,
               tolerances=None) -> None:
    x = range(len(values_tuple))
    back = ax
    if z_tuple is not None:
        back = ax.twinx()
        back.plot(x, z_tuple, color=FILTERED_COLOR, lw=1.2)
        back.tick_params(right=False, labelright=False)
        if z_lim is not None:
            back.set_ylim(*z_lim)
        ax.patch.set_visible(False)
        ax.set_zorder(back.get_zorder() + 1)
    # Bands on the back axis, so neither curve is tinted by them.
    for phase, a, b in runs:
        back.axvspan(a, b + 0.999, color=colors.get(phase, "white"),
                     alpha=0.45, lw=0, zorder=0)
    if tolerances:
        draw_tolerances(back, tolerances)
    ax.plot(x, values_tuple, color=RAW_COLOR, lw=1.0, alpha=0.9)


def padded(lo: float, hi: float) -> tuple[float, float]:
    pad = 0.05 * (hi - lo or 1.0)
    return lo - pad, hi + pad


def png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    return buf.getvalue()


def cell_figure(values_tuple: tuple, runs_tuple: tuple, title: str,
                z_tuple: tuple | None, colors, tolerances=None):
    """Raw series, the column's smoothed series and its phases as bands; with
    `tolerances`, also the label's tolerance spans (see `draw_tolerances`)."""
    matplotlib.use("Agg")
    fig, ax = plt.subplots(figsize=(3.6, 1.7))
    draw_panel(ax, values_tuple, runs_tuple, z_tuple, colors,
               tolerances=tolerances)
    ax.set_title(title, fontsize=7)
    ax.tick_params(labelsize=6)
    ax.set_xlim(0, max(1, len(values_tuple) - 1))
    fig.tight_layout(pad=0.3)
    return fig


def stacked_figure(values_tuple: tuple, panels: tuple, colors, tolerances=None):
    """All columns stacked vertically on a SHARED x axis and a shared y scale.

    The point of this arrangement is that a boundary that moved between two
    configurations is read straight down the figure. That only works if the two
    axes are actually the same, so `sharex=True` and one y range for every panel
    are the arrangement, not decoration. The same holds for the smoothed curve:
    each panel draws its own column's, and all of them share one range on the
    twin axis, so a column that smoothed harder shows a flatter curve.

    `panels` is ((title, runs, z_tuple or None), ...). `tolerances`, when
    given, is aligned with `panels`: the spans for each panel, or None.
    """
    matplotlib.use("Agg")
    n = len(panels)
    fig, axes = plt.subplots(n, 1, figsize=(7.2, 1.35 * n + 0.4),
                             sharex=True, sharey=True, squeeze=False)
    lim = padded(min(values_tuple), max(values_tuple))
    zs = [v for _, _, z in panels if z is not None for v in z if v == v]
    z_lim = padded(min(zs), max(zs)) if zs else None
    tols = tolerances or (None,) * n
    for ax, (title, runs, z), tol in zip(axes[:, 0], panels, tols):
        draw_panel(ax, values_tuple, runs, z, colors, z_lim, tolerances=tol)
        ax.set_ylabel(title, fontsize=7, rotation=0, ha="right", va="center")
        ax.tick_params(labelsize=6)
        ax.set_ylim(*lim)
    axes[-1, 0].set_xlim(0, max(1, len(values_tuple) - 1))
    fig.tight_layout(pad=0.3)
    return fig
