"""Static (matplotlib) equivalent of the layer inspector — no Streamlit.

The inspector is UI: its whole point is that a layer is one legend click away.
That makes it awkward to review without starting Streamlit, so this module
renders the same layers as a flat PNG — everything switched ON at once, since a
static figure has no switches.

It consumes the SAME pure helpers as the Plotly renderer
(``layer_inspector``), so a disagreement between the two is impossible by
construction: they differ only in how they draw, never in what they compute.
Used by ``research/app_layer_inspector/gen_inspector_figures.py``.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from layer_inspector import (
    C_ACCEPT_PEAK,
    C_ACCEPT_VALLEY,
    C_BOUNDARY,
    C_KNEE,
    C_REJECT,
    C_REL,
    C_SMOOTH,
    C_THRESHOLD,
    PHASE_COLORS,
    STEP_NAMES,
    label_runs,
    phase_spans_for_shading,
)

C_INT = "#f7b538"
C_DEC = "#7d8c5c"
C_GT = "#00a000"

_SERIES_Z = [
    ("zeta", "zeta (entrada crua)", "#8d8d8d", 1.0),
    ("filtered_vorticity", "filtered_vorticity", "#7fb3d5", 1.2),
    ("vorticity_smoothed", "vorticity_smoothed", "#2e86c1", 1.2),
    ("vorticity_smoothed2", "vorticity_smoothed2", "#1d3557", 2.0),
]


def _shade(ax, periods_dict) -> None:
    for span in phase_spans_for_shading(periods_dict, None):
        ax.axvspan(span["start"], span["end"], alpha=0.25, lw=0,
                   color=PHASE_COLORS.get(span["key"], "#cccccc"))


def render_static_inspector(name, vort, df_result, periods_dict, *,
                            ribbon=None, ledgers=None, mature=None,
                            incipient=None, gt_boundary_iso=None,
                            title_suffix=""):
    """One page per track: z / dz / dz2 (+ rel) panels, plus the pipeline ribbon.

    Args mirror ``inspector_plotly.build_inspector_figure`` exactly; see there
    for what each overlay dict must carry.
    """
    index = df_result.index
    want_rel = bool(incipient and incipient.get("plateau_active"))
    n_rows = 3 + int(want_rel) + int(bool(ribbon))
    ratios = [2.6, 1.2, 1.2] + ([1.0] if want_rel else []) + ([1.4] if ribbon else [])

    fig, axes = plt.subplots(n_rows, 1, figsize=(15, 2.6 * n_rows), sharex=True,
                             gridspec_kw={"height_ratios": ratios})
    ax_z, ax_dz, ax_dz2 = axes[0], axes[1], axes[2]
    ax_rel = axes[3] if want_rel else None
    ax_rib = axes[-1] if ribbon else None

    # ── panel z: every pipeline series + the extrema the detector consumes ──
    _shade(ax_z, periods_dict)
    for var, label, colour, lw in _SERIES_Z:
        ax_z.plot(index, vort[var].values, color=colour, lw=lw, label=label,
                  zorder=3)
    _extrema(ax_z, index, df_result["z"], df_result["z_peaks_valleys"])
    ax_z.set_ylabel("z", fontsize=9)

    if gt_boundary_iso:
        for ax in axes[:-1] if ribbon else axes:
            ax.axvline(pd.Timestamp(gt_boundary_iso), color=C_GT, lw=2.0,
                       ls=":", zorder=6)
        ax_z.plot([], [], color=C_GT, lw=2.0, ls=":", label="fronteira Ic (GT)")

    if ledgers:
        _draw_ledger(ax_z, index, df_result["z"], ledgers)
    if mature:
        _draw_mature(ax_z, index, df_result["z"], mature)

    # ── panels dz / dz2 ─────────────────────────────────────────────────────
    for ax, base, filt, smooth, lbl in (
            (ax_dz, "dz", "dz_dt_filt", "dz_dt_smoothed2", "dz"),
            (ax_dz2, "dz2", "dz_dt2_filt", "dz_dt2_smoothed2", "dz2")):
        ax.plot(index, vort[filt].values, color="#bdbdbd", lw=1.1, label=filt)
        ax.plot(index, vort[smooth].values, color="#457b9d", lw=1.8, label=smooth)
        _extrema(ax, index, df_result[base], df_result[f"{base}_peaks_valleys"])
        ax.set_ylabel(lbl, fontsize=9)
        ax.axhline(0.0, color="#888888", lw=0.7)

    if incipient:
        _draw_incipient(ax_dz, ax_dz2, ax_rel, index, incipient)

    for ax in axes[:-1] if ribbon else axes:
        ax.legend(fontsize=7, loc="best", ncol=2, framealpha=0.85)
        ax.tick_params(labelsize=8)

    if ax_rib is not None:
        _draw_ribbon(ax_rib, ribbon)

    fig.suptitle(f"Inspetor de camadas — {name}{title_suffix}",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    return fig


def _extrema(ax, index, values, labels) -> None:
    values = np.asarray(values, dtype=float)
    lab = np.asarray(labels, dtype=object)
    for kind, marker, colour in (("peak", "^", C_ACCEPT_PEAK),
                                 ("valley", "v", C_ACCEPT_VALLEY)):
        sel = np.flatnonzero(lab == kind)
        if sel.size:
            ax.scatter(np.asarray(index)[sel], values[sel], marker=marker, s=45,
                       color=colour, zorder=7, label=f"{kind}s")


def _draw_ledger(ax, index, z, ledgers) -> None:
    """Candidate segments over z, coloured by the verdict under the current
    threshold; gaps drawn as the dash-dot bridges they either are or are not."""
    z = np.asarray(z, dtype=float)
    pos = {ts: i for i, ts in enumerate(index)}
    for kind, colour, label in (("intensification", C_INT, "intensificação"),
                                ("decay", C_DEC, "decaimento")):
        ledger = ledgers.get(kind)
        if not ledger:
            continue
        for tag, accepted, ls, lw, alpha in (("aceito", True, "-", 5.5, 0.5),
                                             ("rejeitado", False, ":", 3.0, 0.9)):
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
                    lw=2.0, ls="-." if rec["accepted"] else "--", marker="x",
                    ms=6, zorder=5,
                    label=(f"{label}: gap "
                           f"{'preenchido' if rec['accepted'] else 'mantido'}")
                    if first else None)
            first = False


def _draw_mature(ax, index, z, mature) -> None:
    """Accepted vs rejected z extrema under the effective prominence cut, and
    the mature windows — including the ones the strict confirmation erased."""
    lens = mature["lens"]
    z = np.asarray(z, dtype=float)
    x = np.asarray(index)
    for kind, colour, marker in (("peak", C_ACCEPT_PEAK, "^"),
                                 ("valley", C_ACCEPT_VALLEY, "v")):
        for state, filled in (("accepted", True), ("rejected", False)):
            idx = lens[f"{state}_{kind}s"]
            if len(idx) == 0:
                continue
            ax.scatter(x[idx], z[idx], marker=marker, s=110, zorder=8,
                       facecolors=colour if filled else "none",
                       edgecolors=colour, linewidths=1.8,
                       label=f"mature {kind} {'aceito' if filled else 'rejeitado'}")
    pos = {ts: i for i, ts in enumerate(index)}
    for confirmed, colour, ls, tag in (
            (True, PHASE_COLORS["mature"], "-", "confirmada"),
            (False, C_REJECT, ":", "DESCARTADA")):
        first = True
        for rec in mature["records"]:
            if not rec.get("written") or bool(rec.get("confirmed")) != confirmed:
                continue
            lo = pos.get(rec["start"], int(index.searchsorted(rec["start"])))
            hi = pos.get(rec["end"], int(index.searchsorted(rec["end"], "right")) - 1)
            lo, hi = max(0, min(lo, len(index) - 1)), max(0, min(hi, len(index) - 1))
            ax.plot(index[lo:hi + 1], z[lo:hi + 1], color=colour, lw=8.0, ls=ls,
                    alpha=0.45, zorder=2,
                    label=f"janela madura {tag}" if first else None)
            if not confirmed and rec.get("reason"):
                ax.annotate(rec["reason"], (index[(lo + hi) // 2], z[(lo + hi) // 2]),
                            textcoords="offset points", xytext=(0, 16),
                            ha="center", fontsize=7, color="#444444",
                            bbox=dict(fc="white", ec=C_REJECT, lw=0.6, alpha=0.85))
            first = False


def _draw_incipient(ax_dz, ax_dz2, ax_rel, index, incipient) -> None:
    lens = incipient["lens"]
    x = np.asarray(index)
    plateau = incipient["plateau_active"]

    if plateau and lens["smoothing_applies"]:
        # Explicitly rescaled onto dz, and labelled with the factor: the probe
        # is d/dt of the smoothed RAW vorticity, a different quantity in
        # different units. No twinx (that is what produced the zorder bug in
        # _plot_compact) -- one axis, one stated normalisation.
        dz_ref = np.nanmax(np.abs(np.asarray(ax_dz.lines[1].get_ydata(), float)))
        for key, lw, ls, tag in (("probe_raw", 1.0, ":", "crua"),
                                 ("probe_smoothed", 2.0, "-", "suavizada")):
            probe = np.gradient(np.asarray(lens[key], dtype=float))
            peak = np.nanmax(np.abs(probe))
            scale = dz_ref / peak if peak > 0 else 1.0
            ax_dz.plot(x, probe * scale, color=C_SMOOTH, lw=lw, ls=ls,
                       label=f"sondagem {tag} d/dt (×{scale:.3g})")

    knee = int(lens["knee"])
    if 0 <= knee < len(index):
        ax_dz2.axvline(index[knee], color=C_KNEE, lw=1.8, ls="-.",
                       label=f"joelho |dz2| (passo {knee})", zorder=8)

    axes = [ax for ax in (ax_dz, ax_dz2, ax_rel) if ax is not None]
    b = int(incipient.get("boundary") or 0)
    if 0 < b < len(index):
        for i, ax in enumerate(axes):
            ax.axvline(index[b], color="#000000", lw=1.8, zorder=7,
                       label=f"fronteira do run (passo {b})" if i == 0 else None)

    if not plateau or ax_rel is None:
        return
    tau = float(incipient["tau"])
    ax_rel.plot(x, lens["rel_raw"], color=C_REJECT, lw=1.3,
                label="rel sem suavização")
    if lens["smoothing_applies"]:
        ax_rel.plot(x, lens["rel_smoothed"], color=C_REL, lw=2.0,
                    label="rel com suavização")
    ax_rel.axhline(tau, color=C_THRESHOLD, lw=1.5, ls="--", label=f"τ = {tau:.2f}")
    cross = int(lens.get("boundary_smoothed") or lens.get("boundary_raw") or 0)
    if 0 < cross < len(index):
        ax_rel.axvline(index[cross], color=C_BOUNDARY, lw=1.8, ls="--",
                       label=f"cruzamento de τ (passo {cross})")
    else:
        ax_rel.text(0.01, 0.08,
                    "sem cruzamento (rel(t0) ≥ τ ou nenhuma corrida sustentada)",
                    transform=ax_rel.transAxes, fontsize=7.5, color="#555555")
    ax_rel.set_ylim(0, 1.02)
    ax_rel.set_ylabel("rel", fontsize=9)


def _draw_ribbon(ax, ribbon) -> None:
    """Six lanes, one per step, coloured by the phases in force AFTER it."""
    n = len(ribbon)
    for step_i, (step_name, periods) in enumerate(ribbon):
        lane = n - 1 - step_i
        for run in label_runs(periods):
            colour = (PHASE_COLORS.get(run["label"], "#e0e0e0")
                      if run["label"] else "#f4f4f4")
            ax.axhspan(lane - 0.38, lane + 0.38,
                       xmin=0, xmax=1, color="none")   # keeps autoscale sane
            ax.fill_betweenx([lane - 0.38, lane + 0.38],
                             run["start"], run["end"], color=colour,
                             lw=0.4, edgecolor="white")
    ax.set_ylim(-0.5, n - 0.5)
    ax.set_yticks(range(n))
    ax.set_yticklabels(list(reversed(STEP_NAMES)), fontsize=8)
    ax.set_xlabel("tempo", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title("fita do pipeline — fases após cada etapa (ordem fixa; "
                 "etapas posteriores sobrescrevem as anteriores)",
                 fontsize=9, loc="left")
