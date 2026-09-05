"""Plotly renderer for the single-track layer inspector.

Why Plotly here and matplotlib everywhere else
----------------------------------------------
Clicking a legend entry toggles a trace CLIENT-SIDE — no Streamlit rerun, no
round-trip, no re-render. That is the whole point of the inspector: turning a
series on and off has to be as cheap as looking at it. With matplotlib +
``st.image`` every toggle would cost a full rerun of the script and a fresh
render of the figure, which is exactly the model this view replaces.

The multi-cyclone grid, the ZIP and the exported PNG stay on matplotlib and are
untouched: 51 Plotly figures on one page lock the browser up, and the exported
PNG has to stay deterministic.

Layer discipline (the distinction the whole view is built on)
--------------------------------------------------------------
* **Series layers** are ALWAYS added as traces, with ``visible="legendonly"``
  when off. Toggling one is a legend click — free, and it never re-runs
  anything on the server.
* **Decision overlays** (the ledger, the mature layers, the incipient layers)
  need computation, so the app gates them behind ``st.checkbox`` and only
  passes them in when they are asked for. They are traces too once computed.

Phase shading is the one exception to "everything is a trace": a shaded band
spanning a subplot's full height is a layout SHAPE, and shapes cannot be legend
items in Plotly. It is drawn with ``add_vrect`` (the app's ``PHASE_COLORS``) and
made toggleable by an ``updatemenus`` button, which relayouts client-side — the
same no-rerun property as a legend click.

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
)

# Series-layer palette. Deliberately distinct from the phase palette so a
# pipeline stage can never be mistaken for a phase.
SERIES_COLORS = {
    "zeta":                 "#8d8d8d",
    "filtered_vorticity":   "#7fb3d5",
    "vorticity_smoothed":   "#2e86c1",
    "vorticity_smoothed2":  "#1d3557",
    "dz_dt_filt":           "#9ec5d8",
    "dz_dt_smoothed2":      "#457b9d",
    "dz_dt2_filt":          "#c3b5e0",
    "dz_dt2_smoothed2":     "#6a51a3",
}

C_INT = "#f7b538"
C_DEC = "#7d8c5c"
C_GT = "#00a000"


def _hover(unit: str) -> str:
    return ("%{x|%d/%m %Hh}<br>" + unit + " = %{y:.4g}<br>fase: %{customdata}"
            "<extra>%{fullData.name}</extra>")


def _series_trace(fig, row, x, y, name, colour, phases, unit,
                  visible=False, width=1.6, dash=None):
    """One series LAYER: always added, hidden as 'legendonly' when off."""
    fig.add_trace(
        go.Scatter(
            x=x, y=np.asarray(y, dtype=float), name=name, mode="lines",
            line=dict(color=colour, width=width, dash=dash),
            customdata=phases, hovertemplate=_hover(unit),
            visible=True if visible else "legendonly",
            legendgroup=name,
        ),
        row=row, col=1,
    )


def _extrema_trace(fig, row, x, y, labels, name, phases, unit):
    """A ``*_peaks_valleys`` column as its own layer (peaks ^, valleys v)."""
    y = np.asarray(y, dtype=float)
    lab = np.asarray(labels, dtype=object)
    sel = np.flatnonzero((lab == "peak") | (lab == "valley"))
    if sel.size == 0:
        return
    symbols = ["triangle-up" if lab[i] == "peak" else "triangle-down" for i in sel]
    colours = [C_ACCEPT_PEAK if lab[i] == "peak" else C_ACCEPT_VALLEY for i in sel]
    fig.add_trace(
        go.Scatter(
            x=np.asarray(x)[sel], y=y[sel], name=name, mode="markers",
            marker=dict(symbol=symbols, color=colours, size=9,
                        line=dict(width=0.8, color="white")),
            customdata=np.asarray(phases)[sel],
            hovertemplate=_hover(unit),
            visible="legendonly", legendgroup=name,
        ),
        row=row, col=1,
    )


def _vline(fig, rows, x, name, colour, dash="dash", width=2.0, text=""):
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
                legendgroup=name, showlegend=(i == 0), visible="legendonly",
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


def _add_phase_shading(fig, periods_dict, n_rows) -> list[dict]:
    """Phase bands via ``add_vrect``, returned so a button can toggle them."""
    if not periods_dict:
        return []
    for span in phase_spans_for_shading(periods_dict, None):
        fig.add_vrect(
            x0=span["start"], x1=span["end"],
            fillcolor=PHASE_COLORS.get(span["key"], "#cccccc"),
            opacity=0.28, line_width=0, layer="below",
            row="all", col=1,
        )
    return list(fig.layout.shapes)


def _ledger_traces(fig, row, index, z, ledger, colour, label, phases):
    """Candidate segments of one stage function, accepted vs rejected.

    Both verdicts are drawn on the z panel over the z curve itself, because the
    verdict is about a stretch of z — a peak-to-valley leg for intensification,
    a valley-to-peak leg for decay. Accepted is solid, rejected dashed; each
    segment's hover carries the arithmetic that produced the verdict.
    """
    pos = {ts: i for i, ts in enumerate(index)}
    z = np.asarray(z, dtype=float)
    for accepted, dash, width, opacity in ((True, None, 5.0, 0.55),
                                           (False, "dot", 3.0, 0.9)):
        xs, ys, texts = [], [], []
        for rec in ledger["candidates"]:
            if rec["accepted"] != accepted:
                continue
            lo, hi = pos.get(rec["start"]), pos.get(rec["end"])
            if lo is None or hi is None:
                continue
            note = (f"{label} {'ACEITO' if accepted else 'REJEITADO'}<br>"
                    f"{rec['start']:%d/%m %Hh} → {rec['end']:%d/%m %Hh}<br>"
                    f"duração {_td(rec['duration'])} "
                    f"{'>' if accepted else '≤'} mínimo {_td(rec['minimum'])}<br>"
                    f"escala {_td(rec['scale'])}")
            xs.extend(list(index[lo:hi + 1]) + [None])
            ys.extend(list(z[lo:hi + 1]) + [None])
            texts.extend([note] * (hi - lo + 1) + [None])
        if not xs:
            continue
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys, mode="lines",
                name=f"{label}: {'aceitos' if accepted else 'rejeitados'}",
                line=dict(color=colour if accepted else C_REJECT,
                          width=width, dash=dash),
                opacity=opacity, hovertext=texts, hoverinfo="text",
                legendgroup=f"led-{label}-{accepted}", visible=True,
            ),
            row=row, col=1,
        )

    # Gaps: drawn at the z level of their two endpoints, so a bridged gap reads
    # as the join it is. A gap is FILLED when it is SHORTER than the maximum.
    xs, ys, texts, colours = [], [], [], []
    for rec in ledger["gaps"]:
        lo, hi = pos.get(rec["start"]), pos.get(rec["end"])
        if lo is None or hi is None:
            continue
        xs.extend([index[lo], index[hi], None])
        ys.extend([z[lo], z[hi], None])
        note = (f"gap {label} — {'PREENCHIDO' if rec['accepted'] else 'MANTIDO'}<br>"
                f"{_td(rec['duration'])} {'<' if rec['accepted'] else '≥'} "
                f"máximo {_td(rec['minimum'])}<br>escala {_td(rec['scale'])}")
        texts.extend([note, note, None])
    if xs:
        fig.add_trace(
            go.Scatter(x=xs, y=ys, mode="lines+markers",
                       name=f"{label}: gaps",
                       line=dict(color=C_THRESHOLD, width=2.5, dash="dashdot"),
                       marker=dict(size=7, symbol="x", color=C_THRESHOLD),
                       hovertext=texts, hoverinfo="text",
                       visible="legendonly"),
            row=row, col=1,
        )


def _td(value) -> str:
    """Compact rendering of a Timedelta ('1d 06h', '9h')."""
    td = pd.Timedelta(value)
    total_h = td.total_seconds() / 3600.0
    days, hours = divmod(total_h, 24)
    return f"{int(days)}d {hours:04.1f}h" if days else f"{hours:.1f}h"


def _mature_traces(fig, row, index, z, mature, phases):
    """Mature as LAYERS: the extrema the filter keeps/drops, and the windows
    the strict confirmation threw away without leaving a trace in the output."""
    lens = mature["lens"]
    z = np.asarray(z, dtype=float)
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
                (f"{kind} {'aceito' if filled else 'rejeitado'}<br>"
                 f"proeminência = "
                 f"{proms.get(int(i), float('nan')):.4g}<br>"
                 f"limiar efetivo = " + (f"{thr:.4g}" if thr is not None else "—"))
                for i in idx
            ]
            fig.add_trace(
                go.Scatter(
                    x=x[idx], y=z[idx], mode="markers",
                    name=f"mature: {kind} {'aceito' if filled else 'rejeitado'}",
                    marker=dict(symbol=symbol, size=13, color=colour,
                                opacity=1.0 if filled else 0.35,
                                line=dict(width=2, color=colour)),
                    hovertext=texts, hoverinfo="text", visible=True,
                ),
                row=row, col=1,
            )

    # Discarded mature windows: the reason is the payload here.
    pos = {ts: i for i, ts in enumerate(index)}
    for confirmed, colour, dash, name in (
            (True, PHASE_COLORS["mature"], None, "mature: janela confirmada"),
            (False, C_REJECT, "dot", "mature: janela descartada")):
        xs, ys, texts = [], [], []
        for rec in mature["records"]:
            if not rec.get("written") or bool(rec.get("confirmed")) != confirmed:
                continue
            lo = pos.get(rec["start"], int(index.searchsorted(rec["start"])))
            hi = pos.get(rec["end"], int(index.searchsorted(rec["end"], "right")) - 1)
            lo, hi = max(0, min(lo, len(index) - 1)), max(0, min(hi, len(index) - 1))
            note = (f"janela madura {'confirmada' if confirmed else 'DESCARTADA'}<br>"
                    f"{index[lo]:%d/%m %Hh} → {index[hi]:%d/%m %Hh}<br>"
                    + (f"motivo: {rec['reason']}<br>" if rec.get("reason") else "")
                    + f"vizinho anterior: {rec.get('prev_label') or '—'} · "
                      f"posterior: {rec.get('next_label') or '—'}")
            xs.extend(list(index[lo:hi + 1]) + [None])
            ys.extend(list(z[lo:hi + 1]) + [None])
            texts.extend([note] * (hi - lo + 1) + [None])
        if xs:
            fig.add_trace(
                go.Scatter(x=xs, y=ys, mode="lines", name=name,
                           line=dict(color=colour, width=7.0, dash=dash),
                           opacity=0.5, hovertext=texts, hoverinfo="text",
                           visible=True),
                row=row, col=1,
            )
    # Windows rejected before ever being written (empty, or under the duration
    # floor) have no stretch to draw; they are listed in the table instead.


def _incipient_traces(fig, rows, index, dz, dz2, incipient):
    """Incipient as LAYERS over dz / dz2 (+ the rel panel when it exists)."""
    lens = incipient["lens"]
    row_dz, row_dz2, row_rel = rows
    x = np.asarray(index)
    dz = np.asarray(dz, dtype=float)
    dz2 = np.asarray(dz2, dtype=float)
    plateau = incipient["plateau_active"]

    # The probe's own derivative is d/dt of the SMOOTHED RAW vorticity — a
    # different quantity in different units from the pipeline's dz. No twinx
    # (the app already has one zorder bug from that): it is normalised onto
    # dz's scale and the legend entry says so.
    if plateau and lens["smoothing_applies"]:
        for key, colour, width, tag in (("probe_raw", C_SMOOTH, 1.2, "crua"),
                                        ("probe_smoothed", C_SMOOTH, 2.2, "suavizada")):
            probe = np.gradient(np.asarray(lens[key], dtype=float))
            scale = (np.nanmax(np.abs(dz)) / np.nanmax(np.abs(probe))
                     if np.nanmax(np.abs(probe)) > 0 else 1.0)
            fig.add_trace(
                go.Scatter(x=x, y=probe * scale, mode="lines",
                           name=f"incipiente: sondagem {tag} d/dt (×{scale:.3g})",
                           line=dict(color=colour, width=width,
                                     dash=None if tag == "suavizada" else "dot"),
                           hovertemplate="%{x|%d/%m %Hh}<br>sondagem d/dt "
                                         "(reescalada) = %{y:.4g}<extra></extra>",
                           visible=True),
                row=row_dz, col=1)

    if plateau and row_rel is not None:
        fig.add_trace(
            go.Scatter(x=x, y=lens["rel_raw"], mode="lines",
                       name="incipiente: rel = |dz|/max|dz|",
                       line=dict(color=C_REJECT, width=1.6),
                       hovertemplate="%{x|%d/%m %Hh}<br>rel = %{y:.3f}<extra></extra>",
                       visible=True),
            row=row_rel, col=1)
        if lens["smoothing_applies"]:
            fig.add_trace(
                go.Scatter(x=x, y=lens["rel_smoothed"], mode="lines",
                           name="incipiente: rel (sondagem suavizada)",
                           line=dict(color=C_REL, width=2.2),
                           hovertemplate="%{x|%d/%m %Hh}<br>rel = %{y:.3f}"
                                         "<extra></extra>",
                           visible=True),
                row=row_rel, col=1)
        tau = float(incipient["tau"])
        fig.add_trace(
            go.Scatter(x=[x[0], x[-1]], y=[tau, tau], mode="lines",
                       name=f"incipiente: τ = {tau:.2f}",
                       line=dict(color=C_THRESHOLD, width=1.6, dash="dash"),
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
) -> go.Figure:
    """The single-track inspector: three stacked panels, one layer per series.

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

    Returns:
        A ``go.Figure`` whose default visible layers reproduce the phase figure
        of the Grid mode: ``vorticity_smoothed2`` plus the phase shading.
        Everything else is present as ``legendonly`` and one click away.
    """
    index = df_result.index
    phases = phase_at_step(df_result["periods"])

    want_rel = bool(incipient and incipient.get("plateau_active"))
    titles = ["z — vorticidade e estágios do pipeline",
              "dz — primeira derivada",
              "dz2 — segunda derivada"]
    heights = [0.40, 0.19, 0.19]
    row_rel = None
    if want_rel:
        row_rel = len(titles) + 1
        titles.append("rel = |dz| / max|dz| (regra do platô)")
        heights.append(0.14)
    row_ribbon = None
    if ribbon:
        row_ribbon = len(titles) + 1
        titles.append("fita do pipeline — fases após cada etapa")
        heights.append(0.22)
    total = sum(heights)
    heights = [h / total for h in heights]

    fig = make_subplots(rows=len(titles), cols=1, shared_xaxes=True,
                        vertical_spacing=0.045, row_heights=heights,
                        subplot_titles=titles)

    # ── PIECE 1: the series layers ───────────────────────────────────────────
    z_series = [
        ("zeta", "zeta (entrada crua)", False),
        ("filtered_vorticity", "filtered_vorticity (Lanczos)", False),
        ("vorticity_smoothed", "vorticity_smoothed (Savgol 1)", False),
        ("vorticity_smoothed2", "vorticity_smoothed2 (o que a detecção lê)", True),
    ]
    for var, label, on in z_series:
        _series_trace(fig, 1, index, vort[var].values, label,
                      SERIES_COLORS[var], phases, "z", visible=on,
                      width=2.2 if on else 1.5)
    for var, label in (("dz_dt_filt", "dz_dt_filt"),
                       ("dz_dt_smoothed2", "dz_dt_smoothed2 (o que a detecção lê)")):
        _series_trace(fig, 2, index, vort[var].values, label,
                      SERIES_COLORS[var], phases, "dz")
    for var, label in (("dz_dt2_filt", "dz_dt2_filt"),
                       ("dz_dt2_smoothed2", "dz_dt2_smoothed2 (o que a detecção lê)")):
        _series_trace(fig, 3, index, vort[var].values, label,
                      SERIES_COLORS[var], phases, "dz2")

    _extrema_trace(fig, 1, index, df_result["z"], df_result["z_peaks_valleys"],
                   "z_peaks_valleys", phases, "z")
    _extrema_trace(fig, 2, index, df_result["dz"], df_result["dz_peaks_valleys"],
                   "dz_peaks_valleys", phases, "dz")
    _extrema_trace(fig, 3, index, df_result["dz2"], df_result["dz2_peaks_valleys"],
                   "dz2_peaks_valleys", phases, "dz2")

    z_lo, z_hi = _range(vort["vorticity_smoothed2"].values, vort["zeta"].values)
    dz_lo, dz_hi = _range(vort["dz_dt_smoothed2"].values, vort["dz_dt_filt"].values)
    dz2_lo, dz2_hi = _range(vort["dz_dt2_smoothed2"].values, vort["dz_dt2_filt"].values)
    span_rows = [(1, z_lo, z_hi), (2, dz_lo, dz_hi), (3, dz2_lo, dz2_hi)]
    if row_rel:
        span_rows.append((row_rel, 0.0, 1.0))

    if gt_boundary_iso:
        _vline(fig, span_rows, pd.Timestamp(gt_boundary_iso),
               "fronteira Ic (ground truth)", C_GT, dash="dot", width=2.4)

    # ── PIECE 3: the candidate ledger ────────────────────────────────────────
    if ledgers:
        if "intensification" in ledgers:
            _ledger_traces(fig, 1, index, df_result["z"],
                           ledgers["intensification"], C_INT,
                           "intensificação", phases)
        if "decay" in ledgers:
            _ledger_traces(fig, 1, index, df_result["z"], ledgers["decay"],
                           C_DEC, "decaimento", phases)

    # ── PIECE 4: mature and incipient as layers ──────────────────────────────
    if mature:
        _mature_traces(fig, 1, index, df_result["z"], mature, phases)
    if incipient:
        _incipient_traces(fig, (2, 3, row_rel), index, df_result["dz"],
                          df_result["dz2"], incipient)
        knee = int(incipient["lens"]["knee"])
        if 0 <= knee < len(index):
            _vline(fig, span_rows, index[knee],
                   f"incipiente: joelho |dz2| (passo {knee})", C_KNEE,
                   dash="dashdot", width=2.0)
        b = int(incipient.get("boundary") or 0)
        if 0 < b < len(index):
            _vline(fig, span_rows, index[b],
                   f"incipiente: fronteira do run (passo {b})", "#000000",
                   dash="solid", width=2.0)
        if incipient.get("plateau_active"):
            cross = int(incipient["lens"].get("boundary_smoothed")
                        or incipient["lens"].get("boundary_raw") or 0)
            if 0 < cross < len(index) and cross != b:
                _vline(fig, span_rows, index[cross],
                       f"incipiente: cruzamento de τ (passo {cross})",
                       C_BOUNDARY, dash="dash", width=2.0)

    # ── PIECE 2: the pipeline ribbon ─────────────────────────────────────────
    if ribbon and row_ribbon:
        _add_ribbon(fig, row_ribbon, ribbon)

    # ── phase shading (shapes + a client-side toggle button) ─────────────────
    shapes = _add_phase_shading(fig, periods_dict, len(titles))

    fig.update_layout(
        title=dict(text=f"Inspetor de camadas — {name}", x=0.01,
                   font=dict(size=15)),
        height=280 + 190 * len(titles),
        hovermode="x unified",
        legend=dict(orientation="v", x=1.01, y=1.0, font=dict(size=10),
                    groupclick="toggleitem",
                    title=dict(text="camadas (clique para ligar/desligar)",
                               font=dict(size=11))),
        margin=dict(l=60, r=330, t=90, b=40),
        template="plotly_white",
        updatemenus=[dict(
            type="buttons", direction="right", x=0.0, y=1.10,
            xanchor="left", yanchor="bottom", showactive=False,
            buttons=[
                dict(label="fases: ligado", method="relayout",
                     args=[{"shapes": shapes}]),
                dict(label="fases: desligado", method="relayout",
                     args=[{"shapes": []}]),
            ],
        )] if shapes else [],
    )
    fig.update_yaxes(title_text="z", row=1, col=1)
    fig.update_yaxes(title_text="dz", row=2, col=1)
    fig.update_yaxes(title_text="dz2", row=3, col=1)
    if row_rel:
        fig.update_yaxes(title_text="rel", range=[0, 1.02], row=row_rel, col=1)
    if row_ribbon:
        fig.update_yaxes(
            row=row_ribbon, col=1, range=[-0.5, len(STEP_NAMES) - 0.5],
            tickmode="array",
            tickvals=list(range(len(STEP_NAMES))),
            ticktext=[s for s in reversed(STEP_NAMES)],
            tickfont=dict(size=9),
        )
    fig.update_xaxes(title_text="tempo", row=len(titles), col=1)
    for ann in fig.layout.annotations:
        ann.font.size = 11
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
                    y=[lane - 0.38, lane - 0.38, lane + 0.38, lane + 0.38,
                       lane - 0.38],
                    fill="toself", fillcolor=colour, mode="lines",
                    line=dict(width=0.5, color="white"),
                    opacity=0.95 if label else 0.5,
                    hoveron="fills",
                    hovertext=(f"{step_name}<br>{label or 'não classificado'}"
                               f"<br>{x0:%d/%m %Hh} → {x1:%d/%m %Hh}"
                               f" ({run['i1'] - run['i0'] + 1} passos)"),
                    hoverinfo="text", showlegend=False,
                ),
                row=row, col=1,
            )
