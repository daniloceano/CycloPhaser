"""Static (matplotlib) equivalent of the layer inspector — no Streamlit.

The inspector is UI: its whole point is that a layer is one legend click away.
That makes it awkward to review without starting Streamlit, so this module
renders the same layers as a flat PNG — everything switched ON at once, since a
static figure has no switches (which is also the app's default state).

It consumes the SAME pure helpers as the Plotly renderer
(``layer_inspector``), including the shared-axis normalisation, so a
disagreement between the two is impossible by construction: they differ only in
how they draw, never in what they compute. Used by
``research/app_layer_inspector/gen_inspector_figures.py``.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from layer_inspector import (
    C_ABOVE_TAU,
    C_ACCEPT_PEAK,
    C_ACCEPT_VALLEY,
    C_BOUNDARY,
    C_FILTERED,
    C_KNEE,
    C_RAW,
    C_REJECT,
    C_REL,
    C_SMOOTH,
    C_SMOOTHED,
    C_SMOOTHED_LIGHT,
    C_THRESHOLD,
    PHASE_COLORS,
    REFUSAL_REASON_TEXT,
    STEP_NAMES,
    label_runs,
    phase_spans_for_shading,
    requirement_text,
    rescaler,
)

C_INT = "#f7b538"
C_DEC = "#7d8c5c"
C_GT = "#00a000"

# Type sizes and line weights, matching the Plotly renderer's intent: the raw
# curve is always the thickest line in its panel (stands out under every other
# layer); the stage detection actually reads is next; intermediate stages stay
# thin.
F_TICK = 11
F_AXIS = 13
F_LEGEND = 10
F_TITLE = 15
LW_RAW = 4.6
LW_PRIMARY = 3.2
LW_SERIES = 2.0
LW_OVERLAY = 9.0
LW_MARK = 2.6

# Palette -- see layer_inspector's C_RAW/C_FILTERED/C_SMOOTHED for the
# role-based convention (grey=raw, yellow=post-filter, red=post-smoothing,
# raw always the thickest line via LW_RAW below).
_SERIES_Z = [
    ("zeta", "zeta (raw input)", C_RAW, LW_RAW),
    ("filtered_vorticity", "filtered_vorticity (Lanczos)", C_FILTERED, LW_SERIES),
    ("vorticity_smoothed", "vorticity_smoothed (Savgol 1)", C_SMOOTHED_LIGHT, LW_SERIES),
    ("vorticity_smoothed2", "vorticity_smoothed2 (what detection reads)",
     C_SMOOTHED, LW_PRIMARY),
]
_SERIES_D = {
    "dz":  {"filt": C_FILTERED, "smoothed": C_SMOOTHED},
    "dz2": {"filt": C_FILTERED, "smoothed": C_SMOOTHED},
}


def _shade(ax, periods_dict) -> None:
    for span in phase_spans_for_shading(periods_dict, None):
        ax.axvspan(span["start"], span["end"], alpha=0.25, lw=0,
                   color=PHASE_COLORS.get(span["key"], "#cccccc"))


def render_static_inspector(name, vort, df_result, periods_dict, *,
                            ribbon=None, ledgers=None, mature=None,
                            incipient=None, gt_boundary_iso=None,
                            normalize=True, title_suffix=""):
    """One page per track: z / dz / dz2 (+ rel) panels, plus the pipeline ribbon.

    Args mirror ``inspector_plotly.build_inspector_figure`` exactly — including
    ``normalize``, which rescales the curves to [0, 1] in the same groups
    ``plots.plot_all_periods`` puts on its two twinx axes. See there for what
    each overlay dict must carry.
    """
    index = df_result.index
    want_rel = bool(incipient and incipient.get("plateau_active"))
    n_rows = 3 + int(want_rel) + int(bool(ribbon))
    ratios = [2.6, 1.3, 1.3] + ([1.1] if want_rel else []) + ([1.5] if ribbon else [])

    # Bands grouped the way plots.plot_all_periods groups its two twinx axes:
    # the raw series alone, the pipeline stages together. See
    # layer_inspector.rescaler for why.
    raw_scale = rescaler([vort["zeta"].values], normalize)
    z_scale = rescaler([vort["filtered_vorticity"].values,
                        vort["vorticity_smoothed"].values,
                        vort["vorticity_smoothed2"].values], normalize)
    dz_scale = rescaler([vort["dz_dt_filt"].values,
                         vort["dz_dt_smoothed2"].values], normalize)
    dz2_scale = rescaler([vort["dz_dt2_filt"].values,
                          vort["dz_dt2_smoothed2"].values], normalize)

    fig, axes = plt.subplots(n_rows, 1, figsize=(17, 3.0 * n_rows), sharex=True,
                             gridspec_kw={"height_ratios": ratios})
    ax_z, ax_dz, ax_dz2 = axes[0], axes[1], axes[2]
    ax_rel = axes[3] if want_rel else None
    ax_rib = axes[-1] if ribbon else None
    suffix = " (rescaled 0-1)" if normalize else ""

    # ── panel z: every pipeline series + the extrema the detector consumes ──
    _shade(ax_z, periods_dict)
    for var, label, colour, lw in _SERIES_Z:
        values = np.asarray(vort[var].values, dtype=float)
        scale = raw_scale if var == "zeta" else z_scale
        ax_z.plot(index, scale(values), color=colour, lw=lw, label=label,
                  zorder=3)
    _extrema(ax_z, index, df_result["z"], df_result["z_peaks_valleys"], z_scale)
    ax_z.set_ylabel(f"z{suffix}", fontsize=F_AXIS)

    if gt_boundary_iso:
        for ax in (axes[:-1] if ribbon else axes):
            ax.axvline(pd.Timestamp(gt_boundary_iso), color=C_GT, lw=LW_MARK,
                       ls=":", zorder=6)
        ax_z.plot([], [], color=C_GT, lw=LW_MARK, ls=":",
                  label="ground-truth Ic boundary")

    if ledgers:
        _draw_ledger(ax_z, index, df_result["z"], z_scale, ledgers)
    if mature:
        _draw_mature(ax_z, index, df_result["z"], z_scale, mature)

    # ── panels dz / dz2 ─────────────────────────────────────────────────────
    for ax, base, filt, smooth, sm_scale in (
            (ax_dz, "dz", "dz_dt_filt", "dz_dt_smoothed2", dz_scale),
            (ax_dz2, "dz2", "dz_dt2_filt", "dz_dt2_smoothed2", dz2_scale)):
        raw = np.asarray(vort[filt].values, dtype=float)
        ax.plot(index, sm_scale(raw), color=_SERIES_D[base]["filt"],
                lw=LW_SERIES, label=filt)
        smoothed = np.asarray(vort[smooth].values, dtype=float)
        ax.plot(index, sm_scale(smoothed), color=_SERIES_D[base]["smoothed"],
                lw=LW_PRIMARY, label=f"{smooth} (what detection reads)")
        _extrema(ax, index, df_result[base], df_result[f"{base}_peaks_valleys"],
                 sm_scale)
        ax.set_ylabel(f"{base}{suffix}", fontsize=F_AXIS)
        # Only meaningful in true units: once each series is rescaled by its
        # own min/max, zero sits at a different height for each of them, so a
        # single zero line would be a line through nothing.
        if not normalize:
            ax.axhline(0.0, color="#888888", lw=0.9)

    if incipient:
        _draw_incipient(ax_dz, ax_dz2, ax_rel, index, dz_scale, normalize,
                        np.asarray(df_result["dz"], dtype=float), incipient)

    # One legend per panel, pinned just outside its OWN right edge -- not one
    # combined legend, and not overlapping the data inside the panel either.
    for ax in (axes[:-1] if ribbon else axes):
        ax.legend(fontsize=F_LEGEND, loc="upper left", bbox_to_anchor=(1.01, 1.0),
                  ncol=1, framealpha=0.92, borderaxespad=0.0)
        ax.tick_params(labelsize=F_TICK)

    if ax_rib is not None:
        _draw_ribbon(ax_rib, ribbon)

    fig.suptitle(f"Layer inspector — {name}{title_suffix}",
                 fontsize=F_TITLE, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 0.80, 0.98))
    return fig


def _extrema(ax, index, values, labels, scale) -> None:
    values = scale(values)
    lab = np.asarray(labels, dtype=object)
    for kind, marker, colour in (("peak", "^", C_ACCEPT_PEAK),
                                 ("valley", "v", C_ACCEPT_VALLEY)):
        sel = np.flatnonzero(lab == kind)
        if sel.size:
            ax.scatter(np.asarray(index)[sel], values[sel], marker=marker, s=70,
                       color=colour, zorder=7, label=f"{kind}s")


def _draw_ledger(ax, index, z, scale, ledgers) -> None:
    """Candidate segments over z, coloured by the verdict under the current
    threshold; gaps drawn as the dash-dot bridges they either are or are not."""
    z = scale(z)
    pos = {ts: i for i, ts in enumerate(index)}
    for kind, colour, label in (("intensification", C_INT, "intensification"),
                                ("decay", C_DEC, "decay")):
        ledger = ledgers.get(kind)
        if not ledger:
            continue
        for tag, accepted, ls, lw, alpha in (("accepted", True, "-", LW_OVERLAY, 0.45),
                                             ("rejected", False, ":", 4.0, 0.9)):
            first = True
            for rec in ledger["candidates"]:
                if rec["accepted"] != accepted:
                    continue
                lo, hi = pos[rec["start"]], pos[rec["end"]]
                ax.plot(index[lo:hi + 1], z[lo:hi + 1],
                        color=colour if accepted else C_REJECT, lw=lw, ls=ls,
                        alpha=alpha, zorder=4,
                        label=f"{label}: {tag}" if first else None)
                first = False
        first = True
        for rec in ledger["gaps"]:
            lo, hi = pos[rec["start"]], pos[rec["end"]]
            ax.plot([index[lo], index[hi]], [z[lo], z[hi]], color=C_THRESHOLD,
                    lw=LW_MARK, ls="-." if rec["accepted"] else "--", marker="x",
                    ms=9, zorder=5,
                    label=(f"{label}: gap "
                           f"{'filled' if rec['accepted'] else 'left open'}")
                    if first else None)
            first = False


def _draw_mature(ax, index, z, scale, mature) -> None:
    """Accepted vs rejected z extrema under the effective prominence cut, and
    the mature windows — including the ones the strict confirmation erased."""
    lens = mature["lens"]
    z = scale(z)
    x = np.asarray(index)
    for kind, colour, marker in (("peak", C_ACCEPT_PEAK, "^"),
                                 ("valley", C_ACCEPT_VALLEY, "v")):
        for state, filled in (("accepted", True), ("rejected", False)):
            idx = lens[f"{state}_{kind}s"]
            if len(idx) == 0:
                continue
            ax.scatter(x[idx], z[idx], marker=marker, s=170, zorder=8,
                       facecolors=colour if filled else "none",
                       edgecolors=colour, linewidths=2.2,
                       label=f"mature {kind} {state}")
    pos = {ts: i for i, ts in enumerate(index)}
    for confirmed, colour, ls, tag in (
            (True, PHASE_COLORS["mature"], "-", "confirmed"),
            (False, C_REJECT, ":", "DISCARDED")):
        first = True
        for rec in mature["records"]:
            if not rec.get("written") or bool(rec.get("confirmed")) != confirmed:
                continue
            lo = pos.get(rec["start"], int(index.searchsorted(rec["start"])))
            hi = pos.get(rec["end"], int(index.searchsorted(rec["end"], "right")) - 1)
            lo, hi = max(0, min(lo, len(index) - 1)), max(0, min(hi, len(index) - 1))
            ax.plot(index[lo:hi + 1], z[lo:hi + 1], color=colour, lw=12.0, ls=ls,
                    alpha=0.4, zorder=2,
                    label=f"mature window {tag}" if first else None)
            if not confirmed and rec.get("reason"):
                ax.annotate(rec["reason"], (index[(lo + hi) // 2], z[(lo + hi) // 2]),
                            textcoords="offset points", xytext=(0, 20),
                            ha="center", fontsize=F_LEGEND, color="#333333",
                            bbox=dict(fc="white", ec=C_REJECT, lw=0.8, alpha=0.9))
            first = False


def _draw_incipient(ax_dz, ax_dz2, ax_rel, index, dz_scale, normalize, dz,
                    incipient) -> None:
    lens = incipient["lens"]
    x = np.asarray(index)
    plateau = incipient["plateau_active"]

    if plateau and lens["smoothing_applies"]:
        # The probe is d/dt of the smoothed RAW vorticity: a different quantity
        # in different units from the pipeline's dz. No twinx (that is what
        # produced the zorder bug in the app's _plot_compact) -- when the panel
        # is rescaled the probe gets the same treatment as everything in it;
        # when it is not, it is put on dz's own peak so the two are comparable.
        dz_peak = np.nanmax(np.abs(dz)) or 1.0
        for key, lw, ls, tag in (("probe_raw", LW_SERIES, ":", "raw"),
                                 ("probe_smoothed", LW_PRIMARY, "-", "smoothed")):
            probe = np.gradient(np.asarray(lens[key], dtype=float))
            if normalize:
                # A different quantity from dz, so its own band -- the same
                # reasoning that gives raw zeta its own band on the z panel.
                plotted = rescaler([probe], True)(probe)
            else:
                peak = np.nanmax(np.abs(probe))
                plotted = probe * (dz_peak / peak if peak > 0 else 1.0)
            ax_dz.plot(x, plotted, color=C_SMOOTH, lw=lw, ls=ls,
                       label=f"{tag} probe d/dt (rescaled)")

    knee = int(lens["knee"])
    if 0 <= knee < len(index):
        ax_dz2.axvline(index[knee], color=C_KNEE, lw=LW_MARK, ls="-.",
                       label=f"|dz2| knee (step {knee})", zorder=8)

    axes = [ax for ax in (ax_dz, ax_dz2, ax_rel) if ax is not None]
    b = int(incipient.get("boundary") or 0)
    if 0 < b < len(index):
        for i, ax in enumerate(axes):
            ax.axvline(index[b], color="#000000", lw=LW_MARK, zorder=7,
                       label=f"boundary produced by the run (step {b})"
                       if i == 0 else None)

    if not plateau or ax_rel is None:
        return
    tau = float(incipient["tau"])
    rel_label_short = lens["rel_label_short"]
    ax_rel.plot(x, lens["rel_raw"], color=C_REJECT, lw=LW_SERIES,
                label=f"{rel_label_short} (probe smoothing off)")
    rel_active = np.asarray(lens["rel_smoothed"], dtype=float)
    if lens["smoothing_applies"]:
        ax_rel.plot(x, rel_active, color=C_REL, lw=LW_PRIMARY,
                    label=f"{rel_label_short} (probe smoothing on)")
    ax_rel.axhline(tau, color=C_THRESHOLD, lw=LW_MARK, ls="--",
                   label=f"τ = {tau:.2f}")

    # Requirement evidence: which samples clear tau, which runs the
    # crossing/k rule rejected as too short, and the accepted run's start.
    above = np.asarray(lens["above"], dtype=bool)
    if above.any():
        ax_rel.scatter(x[above], rel_active[above], color=C_ABOVE_TAU, s=70,
                       edgecolors="#0b4a26", linewidths=1.0,
                       zorder=6, label="rel ≥ τ samples")
    k_eff = int(lens["k_effective"])
    first_rejected = True
    for start, length, accepted in lens["runs"]:
        if lens["crossing"] == "sustained" and not accepted and length < k_eff:
            hi = min(start + length - 1, len(index) - 1)
            ax_rel.plot(x[start:hi + 1], rel_active[start:hi + 1],
                       color=C_REJECT, lw=LW_MARK + 1.5, ls="--", zorder=5,
                       label="run rejected (too short)" if first_rejected else None)
            ax_rel.annotate(f"len={length}<k={k_eff}", (x[start], rel_active[start]),
                            textcoords="offset points", xytext=(0, -14),
                            ha="left", fontsize=F_LEGEND - 1, color="#555555")
            first_rejected = False
        if accepted:
            ax_rel.scatter([x[start]], [rel_active[start]], color=C_BOUNDARY,
                           marker="D", s=90, zorder=8, edgecolors="black",
                           linewidths=1.2,
                           label=f"accepted run starts (step {start})")

    ax_rel.text(0.01, 0.94, requirement_text(lens["crossing"], k_eff),
               transform=ax_rel.transAxes, fontsize=F_LEGEND, color="#222222",
               va="top",
               bbox=dict(fc="white", ec="none", alpha=0.75))

    cross = int(lens["boundary_smoothed"])
    if 0 < cross < len(index):
        ax_rel.axvline(index[cross], color=C_BOUNDARY, lw=LW_MARK, ls="--",
                       label=f"τ crossing (step {cross})")
    reason = lens.get("refusal_reason")
    if reason:
        ax_rel.text(0.01, 0.08, REFUSAL_REASON_TEXT.get(reason, reason),
                    transform=ax_rel.transAxes, fontsize=F_LEGEND,
                    color="#8b0000",
                    bbox=dict(fc="white", ec=C_REJECT, lw=0.8, alpha=0.9))
    ax_rel.set_ylim(0, 1.02)
    ax_rel.set_ylabel(rel_label_short, fontsize=F_AXIS)


def _draw_ribbon(ax, ribbon) -> None:
    """Six lanes, one per step, coloured by the phases in force AFTER it."""
    n = len(ribbon)
    for step_i, (step_name, periods) in enumerate(ribbon):
        lane = n - 1 - step_i
        for run in label_runs(periods):
            colour = (PHASE_COLORS.get(run["label"], "#e0e0e0")
                      if run["label"] else "#f4f4f4")
            ax.fill_betweenx([lane - 0.40, lane + 0.40],
                             run["start"], run["end"], color=colour,
                             lw=0.4, edgecolor="white")
    ax.set_ylim(-0.5, n - 0.5)
    ax.set_yticks(range(n))
    ax.set_yticklabels(list(reversed(STEP_NAMES)), fontsize=F_TICK)
    ax.set_xlabel("time", fontsize=F_AXIS)
    ax.tick_params(labelsize=F_TICK)
    ax.set_title("pipeline ribbon — phases after each step (fixed order; later "
                 "steps overwrite earlier ones)", fontsize=F_AXIS, loc="left")
