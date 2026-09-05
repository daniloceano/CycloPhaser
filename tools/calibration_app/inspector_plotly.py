"""Plotly renderer for the single-track layer inspector.

Why Plotly here and matplotlib everywhere else
----------------------------------------------
Clicking a legend entry toggles a trace CLIENT-SIDE — no Streamlit rerun, no
round-trip, no re-render. That is the whole point of the inspector: turning a
layer on and off has to be as cheap as looking at it. With matplotlib +
``st.image`` every toggle would cost a full rerun of the script and a fresh
render of the figure, which is exactly the model this view replaces.

The multi-cyclone grid, the ZIP and the exported PNG stay on matplotlib and are
untouched: 51 Plotly figures on one page lock the browser up, and the exported
PNG has to stay deterministic.

Layer discipline (the distinction the whole view is built on)
--------------------------------------------------------------
* **Series layers** are ALWAYS added as traces. They are ON by default; a
  layer switched off is ``visible="legendonly"``, still in the figure, one
  free client-side click away.
* **Decision overlays** (the ledger, the mature layers, the incipient layers)
  need computation, so the app gates them behind ``st.checkbox`` and only
  passes them in when they are asked for. They are traces too once computed.

Phase shading is the one thing here that is not a trace: a band spanning a
subplot's full height is a layout SHAPE. It is drawn with ``add_vrect`` (the
app's ``PHASE_COLORS``) and is always on — it is the background every other
layer is read against, so there is nothing to gain from switching it off.

Shared y scale
--------------
With every layer on, a panel holds series of genuinely different magnitude
(raw ``zeta`` runs 2-3x wider than the smoothed curve the detector reads). A
twinx is not an option here — it already caused a zorder bug in the app's
``_plot_compact`` — so the panels default to ONE axis with the curves rescaled
to [0, 1] (``layer_inspector.rescaler``). The panel is then read for SHAPE —
where each series turns, and when — which is what the phase rules act on.

The GROUPING is what the package's own ``plot_all_periods`` already gets
right and is reproduced here: raw ``zeta`` is rescaled on its own, while
``filtered_vorticity`` / ``vorticity_smoothed`` / ``vorticity_smoothed2``
share one band (they are one axis of the package's twinx). The raw series
therefore overlays the filtered one — the readable "same track, cleaned up"
picture — while the three pipeline stages stay comparable to EACH OTHER, so
the amplitude every smoothing pass removes is still visible. The derivative
panels follow the same rule: ``*_filt`` and ``*_smoothed2`` share a band.

Every hover still carries the raw value, and the app can switch the rescaling
off to read true units.

Colours
-------
The vorticity panel follows the package's own palette (``cyclophaser/plots.py``,
``plot_didactic``): grey raw ζ, amber ζ_f, navy ζ_fs, red ζ_fs². The derivative
panels follow the package's per-quantity colours from the same file
(``series_colors``: dz red, dz2 amber), with the intermediate ``*_filt`` stage
in a light tint of its panel's colour and the stage detection actually reads in
the full colour at full weight.

Nothing here computes anything about detection: every array it draws comes from
``layer_inspector``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    phase_at_step,
    phase_spans_for_shading,
    rescaler,
)

# Series-layer palette, taken from the package itself so a curve looks the same
# here as it does in cyclophaser's own figures.
#
# Vorticity panel — cyclophaser/plots.py, plot_didactic: raw zeta is grey,
# filtered_vorticity amber, vorticity_smoothed navy, vorticity_smoothed2 red.
# Derivative panels — the same file's `series_colors` gives each QUANTITY a
# colour (dz red, dz2 amber); within a panel the pipeline STAGE is carried by
# weight instead, with the intermediate *_filt in a light tint and the stage
# detection actually reads in the full colour at full weight.
SERIES_COLORS = {
    "zeta":                 "gray",
    "filtered_vorticity":   "#d68c45",
    "vorticity_smoothed":   "#1d3557",
    "vorticity_smoothed2":  "#e63946",
    "dz_dt_filt":           "#eba0a0",
    "dz_dt_smoothed2":      "#d62828",
    "dz_dt2_filt":          "#f6dcaa",
    "dz_dt2_smoothed2":     "#f7b538",
}

C_INT = "#f7b538"
C_DEC = "#7d8c5c"
C_GT = "#00a000"

# Type sizes. The inspector is read at laptop width with a dozen layers on it,
# so these are deliberately larger than Plotly's defaults.
F_TICK = 13
F_AXIS_TITLE = 15
F_LEGEND = 13
F_SUBPLOT_TITLE = 15
F_TITLE = 20
F_HOVER = 13

# Line weights. The detection input of each panel is the thickest line in it:
# with every layer on, "which curve does the algorithm actually read" has to be
# answerable at a glance.
LW_PRIMARY = 4.0
LW_SERIES = 2.6
LW_OVERLAY = 8.0
LW_MARK = 3.0
MARKER_SIZE = 13


def _hover(unit: str, normalize: bool) -> str:
    """Hover text. The RAW value is always first: rescaling is a display
    device for reading shape, never a loss of the number."""
    head = "%{x|%d/%m %Hh}<br>" + unit + " = %{customdata[0]:.4g}"
    if normalize:
        head += "<br>rescaled = %{y:.3f}"
    return head + "<br>phase: %{customdata[1]}<extra>%{fullData.name}</extra>"


def _custom(raw, phases) -> np.ndarray:
    return np.stack([np.asarray(raw, dtype=object),
                     np.asarray(phases, dtype=object)], axis=-1)


def _series_trace(fig, row, x, y, name, colour, phases, unit, scale, normalize,
                  visible=True, width=LW_SERIES, dash=None):
    """One series LAYER: always added, hidden as 'legendonly' when off."""
    raw = np.asarray(y, dtype=float)
    fig.add_trace(
        go.Scatter(
            x=x, y=scale(raw), name=name, mode="lines",
            line=dict(color=colour, width=width, dash=dash),
            customdata=_custom(raw, phases),
            hovertemplate=_hover(unit, normalize),
            visible=True if visible else "legendonly",
            legendgroup=name,
        ),
        row=row, col=1,
    )


def _extrema_trace(fig, row, x, y, labels, name, phases, unit, scale, normalize):
    """A ``*_peaks_valleys`` column as its own layer (peaks ^, valleys v)."""
    raw = np.asarray(y, dtype=float)
    lab = np.asarray(labels, dtype=object)
    sel = np.flatnonzero((lab == "peak") | (lab == "valley"))
    if sel.size == 0:
        return
    symbols = ["triangle-up" if lab[i] == "peak" else "triangle-down" for i in sel]
    colours = [C_ACCEPT_PEAK if lab[i] == "peak" else C_ACCEPT_VALLEY for i in sel]
    fig.add_trace(
        go.Scatter(
            x=np.asarray(x)[sel], y=scale(raw)[sel], name=name, mode="markers",
            marker=dict(symbol=symbols, color=colours, size=MARKER_SIZE,
                        line=dict(width=1.2, color="white")),
            customdata=_custom(raw[sel], np.asarray(phases)[sel]),
            hovertemplate=_hover(unit, normalize),
            visible=True, legendgroup=name,
        ),
        row=row, col=1,
    )


def _vline(fig, rows, x, name, colour, dash="dash", width=LW_MARK, text=""):
    """A vertical marker drawn as a trace (so it is a legend-toggleable layer).

    Plotly's own ``add_vline`` is a shape, which cannot be toggled from the
    legend; a two-point scatter per panel, sharing one ``legendgroup``, gives
    the same picture and one legend click turns it off across every panel.
    """
    for i, (row, lo, hi) in enumerate(rows):
        fig.add_trace(
            go.Scatter(
                x=[x, x], y=[lo, hi], name=name, mode="lines",
                line=dict(color=colour, width=width, dash=dash),
                hovertemplate=(text or name) + "<extra></extra>",
                legendgroup=name, showlegend=(i == 0), visible=True,
            ),
            row=row, col=1,
        )


def _range(*arrays) -> tuple[float, float]:
    vals = np.concatenate([np.asarray(a, dtype=float).ravel() for a in arrays])
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return 0.0, 1.0
    lo, hi = float(vals.min()), float(vals.max())
    pad = (hi - lo) * 0.05 or 1.0
    return lo - pad, hi + pad


def _add_phase_shading(fig, periods_dict) -> None:
    """Phase bands via ``add_vrect``, always on.

    This is the background every other layer is read against — "which phase
    was this stretch given" is the question the whole view serves — so there
    is nothing to gain from switching it off, and the button that used to do
    it sat on top of the figure title.
    """
    if not periods_dict:
        return
    for span in phase_spans_for_shading(periods_dict, None):
        fig.add_vrect(
            x0=span["start"], x1=span["end"],
            fillcolor=PHASE_COLORS.get(span["key"], "#cccccc"),
            opacity=0.28, line_width=0, layer="below",
            row="all", col=1,
        )


def _ledger_traces(fig, row, index, z, scale, ledger, colour, label):
    """Candidate segments of one stage function, accepted vs rejected.

    Both verdicts are drawn on the z panel over the z curve itself, because the
    verdict is about a stretch of z — a peak-to-valley leg for intensification,
    a valley-to-peak leg for decay. Accepted is solid, rejected dotted; each
    segment's hover carries the arithmetic that produced the verdict.
    """
    pos = {ts: i for i, ts in enumerate(index)}
    z = scale(z)
    for accepted, dash, width, opacity in ((True, None, LW_OVERLAY, 0.5),
                                           (False, "dot", 4.5, 0.9)):
        xs, ys, texts = [], [], []
        for rec in ledger["candidates"]:
            if rec["accepted"] != accepted:
                continue
            lo, hi = pos.get(rec["start"]), pos.get(rec["end"])
            if lo is None or hi is None:
                continue
            note = (f"{label} {'ACCEPTED' if accepted else 'REJECTED'}<br>"
                    f"{rec['start']:%d/%m %Hh} → {rec['end']:%d/%m %Hh}<br>"
                    f"duration {_td(rec['duration'])} "
                    f"{'>' if accepted else '≤'} minimum {_td(rec['minimum'])}<br>"
                    f"scale {_td(rec['scale'])}")
            xs.extend(list(index[lo:hi + 1]) + [None])
            ys.extend(list(z[lo:hi + 1]) + [None])
            texts.extend([note] * (hi - lo + 1) + [None])
        if not xs:
            continue
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys, mode="lines",
                name=f"{label}: {'accepted' if accepted else 'rejected'}",
                line=dict(color=colour if accepted else C_REJECT,
                          width=width, dash=dash),
                opacity=opacity, hovertext=texts, hoverinfo="text",
                legendgroup=f"led-{label}-{accepted}", visible=True,
            ),
            row=row, col=1,
        )

    # Gaps: drawn between the z levels of their two endpoints, so a bridged gap
    # reads as the join it is. A gap is FILLED when it is SHORTER than the max.
    xs, ys, texts = [], [], []
    for rec in ledger["gaps"]:
        lo, hi = pos.get(rec["start"]), pos.get(rec["end"])
        if lo is None or hi is None:
            continue
        xs.extend([index[lo], index[hi], None])
        ys.extend([z[lo], z[hi], None])
        note = (f"{label} gap — {'FILLED' if rec['accepted'] else 'LEFT OPEN'}<br>"
                f"{_td(rec['duration'])} {'<' if rec['accepted'] else '≥'} "
                f"maximum {_td(rec['minimum'])}<br>scale {_td(rec['scale'])}")
        texts.extend([note, note, None])
    if xs:
        fig.add_trace(
            go.Scatter(x=xs, y=ys, mode="lines+markers",
                       name=f"{label}: gaps",
                       line=dict(color=C_THRESHOLD, width=LW_MARK, dash="dashdot"),
                       marker=dict(size=10, symbol="x", color=C_THRESHOLD),
                       hovertext=texts, hoverinfo="text", visible=True),
            row=row, col=1,
        )


def _td(value) -> str:
    """Compact rendering of a Timedelta ('1d 06.0h', '9.0h')."""
    td = pd.Timedelta(value)
    total_h = td.total_seconds() / 3600.0
    days, hours = divmod(total_h, 24)
    return f"{int(days)}d {hours:04.1f}h" if days else f"{hours:.1f}h"


def _mature_traces(fig, row, index, z, scale, mature):
    """Mature as LAYERS: the extrema the filter keeps/drops, and the windows
    the strict confirmation threw away without leaving a trace in the output."""
    lens = mature["lens"]
    z = scale(z)
    x = np.asarray(index)

    for kind, accept_colour, symbol in (("peak", C_ACCEPT_PEAK, "triangle-up"),
                                        ("valley", C_ACCEPT_VALLEY, "triangle-down")):
        thr = lens[f"{kind}_threshold"]
        proms = lens[f"{kind}_prominences"]
        for state, colour, filled in (("accepted", accept_colour, True),
                                      ("rejected", C_REJECT, False)):
            idx = lens[f"{state}_{kind}s"]
            if len(idx) == 0:
                continue
            texts = [
                (f"{kind} {'accepted' if filled else 'rejected'}<br>"
                 f"prominence = {proms.get(int(i), float('nan')):.4g}<br>"
                 f"effective threshold = " + (f"{thr:.4g}" if thr is not None else "—"))
                for i in idx
            ]
            fig.add_trace(
                go.Scatter(
                    x=x[idx], y=z[idx], mode="markers",
                    name=f"mature: {kind} {'accepted' if filled else 'rejected'}",
                    marker=dict(symbol=symbol, size=18, color=colour,
                                opacity=1.0 if filled else 0.35,
                                line=dict(width=2.5, color=colour)),
                    hovertext=texts, hoverinfo="text", visible=True,
                ),
                row=row, col=1,
            )

    pos = {ts: i for i, ts in enumerate(index)}
    for confirmed, colour, dash, name in (
            (True, PHASE_COLORS["mature"], None, "mature: window confirmed"),
            (False, C_REJECT, "dot", "mature: window DISCARDED")):
        xs, ys, texts = [], [], []
        for rec in mature["records"]:
            if not rec.get("written") or bool(rec.get("confirmed")) != confirmed:
                continue
            lo = pos.get(rec["start"], int(index.searchsorted(rec["start"])))
            hi = pos.get(rec["end"], int(index.searchsorted(rec["end"], "right")) - 1)
            lo, hi = max(0, min(lo, len(index) - 1)), max(0, min(hi, len(index) - 1))
            note = (f"mature window {'confirmed' if confirmed else 'DISCARDED'}<br>"
                    f"{index[lo]:%d/%m %Hh} → {index[hi]:%d/%m %Hh}<br>"
                    + (f"reason: {rec['reason']}<br>" if rec.get("reason") else "")
                    + f"previous neighbour: {rec.get('prev_label') or '—'} · "
                      f"next: {rec.get('next_label') or '—'}")
            xs.extend(list(index[lo:hi + 1]) + [None])
            ys.extend(list(z[lo:hi + 1]) + [None])
            texts.extend([note] * (hi - lo + 1) + [None])
        if xs:
            fig.add_trace(
                go.Scatter(x=xs, y=ys, mode="lines", name=name,
                           line=dict(color=colour, width=11.0, dash=dash),
                           opacity=0.45, hovertext=texts, hoverinfo="text",
                           visible=True),
                row=row, col=1,
            )
    # Windows rejected before ever being written (empty, or under the duration
    # floor) have no stretch to draw; they are listed in the table instead.


def _incipient_traces(fig, rows, index, dz, dz_scale, normalize, incipient):
    """Incipient as LAYERS over dz / dz2 (+ the rel panel when it exists)."""
    lens = incipient["lens"]
    row_dz, row_dz2, row_rel = rows
    x = np.asarray(index)
    dz = np.asarray(dz, dtype=float)
    plateau = incipient["plateau_active"]

    # The probe's own derivative is d/dt of the SMOOTHED RAW vorticity — a
    # different quantity in different units from the pipeline's dz. No twinx
    # (the app already has one zorder bug from that): when the panel is
    # rescaled it gets the same [0, 1] treatment as everything else in it;
    # when it is not, it is scaled onto dz's own peak so the two are
    # comparable, and the raw value stays in the hover either way.
    if plateau and lens["smoothing_applies"]:
        dz_peak = np.nanmax(np.abs(dz)) or 1.0
        for key, width, dash, tag in (("probe_raw", LW_SERIES, "dot", "raw"),
                                      ("probe_smoothed", LW_PRIMARY, None, "smoothed")):
            probe = np.gradient(np.asarray(lens[key], dtype=float))
            if normalize:
                # A different quantity from dz, so its own band -- the same
                # reasoning that gives raw zeta its own band on the z panel.
                plotted = rescaler([probe], True)(probe)
            else:
                peak = np.nanmax(np.abs(probe))
                plotted = probe * (dz_peak / peak if peak > 0 else 1.0)
            fig.add_trace(
                go.Scatter(x=x, y=plotted, mode="lines",
                           name=f"incipient: {tag} probe d/dt (rescaled)",
                           line=dict(color=C_SMOOTH, width=width, dash=dash),
                           customdata=np.asarray(probe, dtype=object),
                           hovertemplate="%{x|%d/%m %Hh}<br>probe d/dt = "
                                         "%{customdata:.4g}"
                                         "<extra>%{fullData.name}</extra>",
                           visible=True),
                row=row_dz, col=1)

    if plateau and row_rel is not None:
        fig.add_trace(
            go.Scatter(x=x, y=lens["rel_raw"], mode="lines",
                       name="incipient: rel = |dz| / max|dz|",
                       line=dict(color=C_REJECT, width=LW_SERIES),
                       hovertemplate="%{x|%d/%m %Hh}<br>rel = %{y:.3f}"
                                     "<extra>%{fullData.name}</extra>",
                       visible=True),
            row=row_rel, col=1)
        if lens["smoothing_applies"]:
            fig.add_trace(
                go.Scatter(x=x, y=lens["rel_smoothed"], mode="lines",
                           name="incipient: rel (smoothed probe)",
                           line=dict(color=C_REL, width=LW_PRIMARY),
                           hovertemplate="%{x|%d/%m %Hh}<br>rel = %{y:.3f}"
                                         "<extra>%{fullData.name}</extra>",
                           visible=True),
                row=row_rel, col=1)
        tau = float(incipient["tau"])
        fig.add_trace(
            go.Scatter(x=[x[0], x[-1]], y=[tau, tau], mode="lines",
                       name=f"incipient: τ = {tau:.2f}",
                       line=dict(color=C_THRESHOLD, width=LW_MARK, dash="dash"),
                       hoverinfo="skip", visible=True),
            row=row_rel, col=1)


def build_inspector_figure(
    name: str,
    vort,
    df_result,
    periods_dict: dict,
    *,
    gt_boundary_iso: str | None = None,
    ribbon=None,
    ledgers: dict | None = None,
    mature: dict | None = None,
    incipient: dict | None = None,
    normalize: bool = True,
) -> go.Figure:
    """The single-track inspector: stacked panels, one layer per series.

    Args:
        name: track id (figure title).
        vort: the ``process_vorticity`` dataset (source of every series layer).
        df_result: the ``get_periods`` result (phase per timestep, extrema).
        periods_dict: the phase dict, for the shading layer.
        gt_boundary_iso: designed incipient boundary of a synthetic case, or None.
        ribbon: ``layer_inspector.pipeline_ribbon`` output, or None (PIECE 2).
        ledgers: {'intensification': ledger, 'decay': ledger}, or None (PIECE 3).
        mature: {'lens': ..., 'records': ...}, or None (PIECE 4).
        incipient: {'lens': ..., 'boundary': int, 'tau': float,
                    'plateau_active': bool}, or None (PIECE 4).
        normalize: rescale every curve in a panel to [0, 1] by its own min and
            max so they share one axis and can be compared by SHAPE, which is
            what the phase rules act on. Each hover still carries the raw
            value.

    Returns:
        A ``go.Figure`` with every layer visible; a layer switched off from the
        legend stays in the figure as ``legendonly``.
    """
    index = df_result.index
    phases = phase_at_step(df_result["periods"])

    # Bands, grouped the way plots.plot_all_periods groups its two twinx axes:
    # the raw series alone (so it overlays rather than squashes), the pipeline
    # stages together (so the amplitude each pass removes stays visible). See
    # layer_inspector.rescaler.
    raw_scale = rescaler([vort["zeta"].values], normalize)
    z_scale = rescaler([vort["filtered_vorticity"].values,
                        vort["vorticity_smoothed"].values,
                        vort["vorticity_smoothed2"].values], normalize)
    dz_scale = rescaler([vort["dz_dt_filt"].values,
                         vort["dz_dt_smoothed2"].values], normalize)
    dz2_scale = rescaler([vort["dz_dt2_filt"].values,
                          vort["dz_dt2_smoothed2"].values], normalize)
    panel_scale = {"zeta": raw_scale}

    unit_note = " — rescaled 0-1" if normalize else ""
    want_rel = bool(incipient and incipient.get("plateau_active"))
    titles = [f"z — vorticity through the pipeline{unit_note}",
              f"dz — first derivative{unit_note}",
              f"dz2 — second derivative{unit_note}"]
    heights = [0.40, 0.19, 0.19]
    row_rel = None
    if want_rel:
        row_rel = len(titles) + 1
        titles.append("rel = |dz| / max|dz|  (plateau rule)")
        heights.append(0.14)
    row_ribbon = None
    if ribbon:
        row_ribbon = len(titles) + 1
        titles.append("pipeline ribbon — phases after each step")
        heights.append(0.22)
    total = sum(heights)
    heights = [h / total for h in heights]

    fig = make_subplots(rows=len(titles), cols=1, shared_xaxes=True,
                        vertical_spacing=0.05, row_heights=heights,
                        subplot_titles=titles)

    # ── PIECE 1: the series layers (all ON by default) ───────────────────────
    panels = (
        (1, "z", (("zeta", "zeta (raw input)", False),
                  ("filtered_vorticity", "filtered_vorticity (Lanczos)", False),
                  ("vorticity_smoothed", "vorticity_smoothed (Savgol 1)", False),
                  ("vorticity_smoothed2",
                   "vorticity_smoothed2 (what detection reads)", True)), z_scale),
        (2, "dz", (("dz_dt_filt", "dz_dt_filt", False),
                   ("dz_dt_smoothed2",
                    "dz_dt_smoothed2 (what detection reads)", True)), dz_scale),
        (3, "dz2", (("dz_dt2_filt", "dz_dt2_filt", False),
                    ("dz_dt2_smoothed2",
                     "dz_dt2_smoothed2 (what detection reads)", True)), dz2_scale),
    )
    for row, unit, series, default_scale in panels:
        for var, label, primary in series:
            _series_trace(fig, row, index, vort[var].values, label,
                          SERIES_COLORS[var], phases, unit,
                          panel_scale.get(var, default_scale), normalize,
                          width=LW_PRIMARY if primary else LW_SERIES)

    _extrema_trace(fig, 1, index, df_result["z"], df_result["z_peaks_valleys"],
                   "z_peaks_valleys", phases, "z", z_scale, normalize)
    _extrema_trace(fig, 2, index, df_result["dz"], df_result["dz_peaks_valleys"],
                   "dz_peaks_valleys", phases, "dz", dz_scale, normalize)
    _extrema_trace(fig, 3, index, df_result["dz2"], df_result["dz2_peaks_valleys"],
                   "dz2_peaks_valleys", phases, "dz2", dz2_scale, normalize)

    # Vertical markers need each panel's plotted extent, which depends on the
    # rescaling, so it is measured from the plotted arrays rather than assumed.
    span_rows = [
        (1, *_range(z_scale(vort["vorticity_smoothed2"].values),
                    raw_scale(vort["zeta"].values))),
        (2, *_range(dz_scale(vort["dz_dt_smoothed2"].values),
                    dz_scale(vort["dz_dt_filt"].values))),
        (3, *_range(dz2_scale(vort["dz_dt2_smoothed2"].values),
                    dz2_scale(vort["dz_dt2_filt"].values))),
    ]
    if row_rel:
        span_rows.append((row_rel, 0.0, 1.0))

    if gt_boundary_iso:
        _vline(fig, span_rows, pd.Timestamp(gt_boundary_iso),
               "ground-truth Ic boundary", C_GT, dash="dot", width=LW_MARK + 0.5)

    # ── PIECE 3: the candidate ledger ────────────────────────────────────────
    if ledgers:
        if "intensification" in ledgers:
            _ledger_traces(fig, 1, index, df_result["z"], z_scale,
                           ledgers["intensification"], C_INT, "intensification")
        if "decay" in ledgers:
            _ledger_traces(fig, 1, index, df_result["z"], z_scale,
                           ledgers["decay"], C_DEC, "decay")

    # ── PIECE 4: mature and incipient as layers ──────────────────────────────
    if mature:
        _mature_traces(fig, 1, index, df_result["z"], z_scale, mature)
    if incipient:
        _incipient_traces(fig, (2, 3, row_rel), index, df_result["dz"], dz_scale,
                          normalize, incipient)
        knee = int(incipient["lens"]["knee"])
        if 0 <= knee < len(index):
            _vline(fig, span_rows, index[knee],
                   f"incipient: |dz2| knee (step {knee})", C_KNEE,
                   dash="dashdot", width=LW_MARK)
        b = int(incipient.get("boundary") or 0)
        if 0 < b < len(index):
            _vline(fig, span_rows, index[b],
                   f"incipient: boundary produced by the run (step {b})",
                   "#000000", dash="solid", width=LW_MARK)
        if incipient.get("plateau_active"):
            cross = int(incipient["lens"].get("boundary_smoothed")
                        or incipient["lens"].get("boundary_raw") or 0)
            if 0 < cross < len(index) and cross != b:
                _vline(fig, span_rows, index[cross],
                       f"incipient: τ crossing (step {cross})",
                       C_BOUNDARY, dash="dash", width=LW_MARK)

    # ── PIECE 2: the pipeline ribbon ─────────────────────────────────────────
    if ribbon and row_ribbon:
        _add_ribbon(fig, row_ribbon, ribbon)

    # ── phase shading (always on: it is the background, not a layer) ─────────
    _add_phase_shading(fig, periods_dict)

    fig.update_layout(
        title=dict(text=f"Layer inspector — {name}", x=0.01,
                   font=dict(size=F_TITLE)),
        height=320 + 230 * len(titles),
        hovermode="x unified",
        hoverlabel=dict(font_size=F_HOVER),
        font=dict(size=F_TICK),
        legend=dict(orientation="v", x=1.01, y=1.0, font=dict(size=F_LEGEND),
                    groupclick="toggleitem",
                    title=dict(text="Layers — click to toggle",
                               font=dict(size=F_LEGEND + 2))),
        margin=dict(l=80, r=400, t=90, b=50),
        template="plotly_white",
    )
    axis_note = " (rescaled 0-1)" if normalize else ""
    fig.update_yaxes(title_text=f"z{axis_note}", row=1, col=1)
    fig.update_yaxes(title_text=f"dz{axis_note}", row=2, col=1)
    fig.update_yaxes(title_text=f"dz2{axis_note}", row=3, col=1)
    if row_rel:
        fig.update_yaxes(title_text="rel", range=[0, 1.02], row=row_rel, col=1)
    if row_ribbon:
        fig.update_yaxes(
            row=row_ribbon, col=1, range=[-0.5, len(STEP_NAMES) - 0.5],
            tickmode="array",
            tickvals=list(range(len(STEP_NAMES))),
            ticktext=[s for s in reversed(STEP_NAMES)],
            tickfont=dict(size=F_TICK),
        )
    fig.update_xaxes(title_text="time", row=len(titles), col=1)
    fig.update_xaxes(tickfont=dict(size=F_TICK))
    fig.update_yaxes(tickfont=dict(size=F_TICK),
                     title_font=dict(size=F_AXIS_TITLE))
    fig.update_xaxes(title_font=dict(size=F_AXIS_TITLE))
    for ann in fig.layout.annotations:
        ann.font.size = F_SUBPLOT_TITLE
    return fig


def _add_ribbon(fig, row, ribbon) -> None:
    """Six stacked lanes, one per detection step, coloured by the phases in
    force AFTER that step. Reading down a column shows a stretch changing
    hands — which is the only way the fixed call order becomes visible."""
    n = len(ribbon)
    for step_i, (step_name, periods) in enumerate(ribbon):
        lane = n - 1 - step_i          # step 1 at the top
        for run in label_runs(periods):
            label = run["label"]
            colour = PHASE_COLORS.get(label, "#e8e8e8") if label else "#f2f2f2"
            x0, x1 = run["start"], run["end"]
            fig.add_trace(
                go.Scatter(
                    x=[x0, x1, x1, x0, x0],
                    y=[lane - 0.40, lane - 0.40, lane + 0.40, lane + 0.40,
                       lane - 0.40],
                    fill="toself", fillcolor=colour, mode="lines",
                    line=dict(width=0.5, color="white"),
                    opacity=0.95 if label else 0.5,
                    hoveron="fills",
                    hovertext=(f"{step_name}<br>{label or 'unclassified'}"
                               f"<br>{x0:%d/%m %Hh} → {x1:%d/%m %Hh}"
                               f" ({run['i1'] - run['i0'] + 1} steps)"),
                    hoverinfo="text", showlegend=False,
                ),
                row=row, col=1,
            )
