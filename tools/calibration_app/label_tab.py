"""BLIND manual labelling of a cyclone's whole phase sequence.

    THIS MODULE MUST NEVER SHOW DETECTOR OUTPUT.

That is the whole point of it, so it is worth being explicit about what "blind"
means here and why the constraint is absolute.

There is no ground truth for the incipient boundary. The synthetic suite derives
one from the segment list and that derivation is wrong — `shape="sine"` is a
half-period cosine with zero derivative at both ends, so an It or D segment
opening in sine starts FLAT and creates a real incipient plateau the segment list
does not express (compare IcDItMD_noisy, D in sine, with DItMD_noisy, D in
linear: same segments, different answers). Four cases place the incipient phase
and the phase after it both at index 0, which is not a boundary at all. The 51
real tracks have no label of any kind.

So the labels have to come from a human looking at the raw series. If that human
can see where the detector put its boundaries, the label stops being independent
evidence and becomes an echo of the thing it is supposed to judge — and the whole
artefact is worthless, silently. Anchoring is not a risk that careful labelling
avoids; it is automatic.

Concretely, this module:

  * plots the RAW input series and nothing else — no filtered series, no dz, no
    dz2, no smoothing, no normalisation;
  * does not import cyclophaser, layer_inspector, inspector_plotly, or anything
    else that could produce a phase, an extremum, a tau, or a rel profile;
  * does not read the app's filter/phase parameter widgets, so no sidebar
    setting can change what is on screen;
  * loads its own series straight from tests/calibration_data/ and
    tests/synthetic/cases.py, independently of whatever the rest of the app has
    loaded, so the queue is always the same 63 series.

Every bar and band drawn here comes from the LABELLER'S OWN marks. The phase
palette is the project's standard one (blue incipient, amber intensification,
red mature, olive decay, grey residual) so a labelled series reads the same way
as every other phase figure in the repo — but it is painting the human's answer,
never the algorithm's.


Why the chart is hand-drawn instead of a Plotly figure
------------------------------------------------------
It was a Plotly figure, twice, and both attempts failed on the same wall.

The interaction this view needs is: grab the bar that marks a phase boundary,
slide it along time, and have the shading follow. Plotly can make a shape
draggable, but only in two dimensions — there is no axis constraint for shapes
or annotations anywhere in its schema. So a boundary could be dragged off the
time axis, where it means nothing, and it dragged the phase shading with it.

That could not be corrected in the browser either: Streamlit's bundle does not
expose `window.Plotly` (only `PlotlyGeoAssets` and `PlotlyLocales`), so there is
no handle to call `relayout` on. Correcting it server-side meant a round trip and
a remount for every stray vertical nudge, which is what made dragging work only
"mais ou menos".

Drawn by hand, the problem disappears rather than being repaired: the drag
handler reads `clientX` and NOTHING ELSE. There is no vertical coordinate in the
code path at all, so a boundary cannot leave the time axis — not because it is
pushed back, but because nothing ever moves it there. The uncertainty is the
BAR'S OWN WIDTH, so it travels with the boundary by construction instead of being
a second object that has to be kept in sync, and the phase bands are recomputed
from the bar positions on every frame, so the shading follows for free.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_LABELS_PKG = _REPO_ROOT / "research" / "labels"
if str(_LABELS_PKG) not in sys.path:
    sys.path.insert(0, str(_LABELS_PKG))

import labels_core as lc  # noqa: E402

DEFAULT_TOLERANCE = 5

# The component's drawing surface, in viewBox units. The SVG scales to the
# container with preserveAspectRatio, so every coordinate below is resolution
# independent and nothing has to be recomputed when the window is resized.
_W, _H = 1000, 520
_ML, _MR, _MT, _MB = 74, 22, 26, 44


# ── the chart component ──────────────────────────────────────────────────────
# Reads clientX and nothing else. See the module docstring for why that is the
# whole point rather than an implementation detail.
_CHART_JS = """
export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  if (!data || !data.n) return;

  const NS = 'http://www.w3.org/2000/svg';
  const el = (t, a) => {
    const e = document.createElementNS(NS, t);
    for (const k in a) e.setAttribute(k, a[k]);
    return e;
  };

  const N = data.n;
  const Y = data.y;
  const COL = data.colors;
  const PH = data.phases.map((p) => ({ ...p }));
  const W = data.w, H = data.h;
  const ML = data.ml, MR = data.mr, MT = data.mt, MB = data.mb;
  const PW = W - ML - MR, PH_ = H - MT - MB;

  let lo = Infinity, hi = -Infinity;
  for (let i = 0; i < N; i++) { if (Y[i] < lo) lo = Y[i]; if (Y[i] > hi) hi = Y[i]; }
  const pad = (hi - lo) * 0.06 || 1;
  const y0 = lo - pad, y1 = hi + pad;

  const step = N > 1 ? PW / (N - 1) : PW;
  const sx = (i) => ML + (N > 1 ? i / (N - 1) : 0.5) * PW;
  const sy = (v) => MT + (1 - (v - y0) / (y1 - y0)) * PH_;
  const ix = (px) => Math.round(((px - ML) / PW) * (N - 1));

  // Replace rather than append: this runs again on every rerender, and
  // appending would stack a new chart under the old one each time.
  const prev = parentElement.querySelector('#cp-label-chart');
  if (prev) prev.remove();
  const host = document.createElement('div');
  host.id = 'cp-label-chart';
  parentElement.appendChild(host);

  const svg = el('svg', {
    viewBox: `0 0 ${W} ${H}`, width: '100%',
    preserveAspectRatio: 'xMidYMid meet',
    style: 'touch-action:none;user-select:none;display:block;cursor:default',
  });
  host.appendChild(svg);
  svg.appendChild(el('rect', { x: 0, y: 0, width: W, height: H, fill: '#ffffff' }));

  // 1. phase bands (below everything)
  const bands = PH.map((p) =>
    svg.appendChild(el('rect', {
      y: MT, height: PH_, fill: COL[p.phase] || '#cccccc', 'fill-opacity': 0.30,
    })));
  const bandText = PH.map((p) =>
    svg.appendChild(el('text', {
      y: MT + 15, 'font-size': 12, fill: '#33414f', 'font-family': 'sans-serif',
    })));
  bandText.forEach((t, k) => { t.textContent = PH[k].phase; });

  // 2. axes
  const axis = el('g', {});
  svg.appendChild(axis);
  const nx = 6;
  for (let j = 0; j <= nx; j++) {
    const i = Math.round((j / nx) * (N - 1));
    const x = sx(i);
    axis.appendChild(el('line', {
      x1: x, x2: x, y1: MT, y2: MT + PH_, stroke: '#e6eaef', 'stroke-width': 1 }));
    const t = el('text', {
      x: x, y: MT + PH_ + 20, 'text-anchor': 'middle', 'font-size': 12,
      fill: '#5b6773', 'font-family': 'sans-serif' });
    t.textContent = String(i);
    axis.appendChild(t);
  }
  for (let j = 0; j <= 4; j++) {
    const v = y0 + (j / 4) * (y1 - y0);
    const y = sy(v);
    axis.appendChild(el('line', {
      x1: ML, x2: ML + PW, y1: y, y2: y, stroke: '#eceff3', 'stroke-width': 1 }));
    const t = el('text', {
      x: ML - 8, y: y + 4, 'text-anchor': 'end', 'font-size': 11,
      fill: '#5b6773', 'font-family': 'sans-serif' });
    t.textContent = v.toExponential(2);
    axis.appendChild(t);
  }
  const xlab = el('text', {
    x: ML + PW / 2, y: H - 8, 'text-anchor': 'middle', 'font-size': 12,
    fill: '#33414f', 'font-family': 'sans-serif' });
  xlab.textContent = 'step index';
  svg.appendChild(xlab);

  // 3. the raw series
  let d = '';
  for (let i = 0; i < N; i++) d += (i ? ' L' : 'M') + sx(i).toFixed(2) + ',' + sy(Y[i]).toFixed(2);
  svg.appendChild(el('path', {
    d: d, fill: 'none', stroke: '#1f2d3d', 'stroke-width': 1.8,
    'stroke-linejoin': 'round' }));

  // 4. boundary bars. The bar's WIDTH is the tolerance, so the uncertainty
  //    travels with the boundary instead of being a second object to keep in
  //    sync. Index 0 is not a boundary: it is 0 by construction.
  const bar = [], line = [], grip = [], hL = [], hR = [], tag = [];
  for (let k = 1; k < PH.length; k++) {
    const c = COL[PH[k].phase] || '#666666';
    bar[k] = svg.appendChild(el('rect', {
      y: MT, height: PH_, fill: c, 'fill-opacity': 0.38,
      stroke: c, 'stroke-opacity': 0.65, 'stroke-width': 1 }));
    line[k] = svg.appendChild(el('line', {
      y1: MT, y2: MT + PH_, stroke: c, 'stroke-width': 2.5 }));
    // Transparent hit areas, appended after the visuals so they receive the
    // pointer. The edge grips come last so they win where they overlap the body.
    grip[k] = svg.appendChild(el('rect', {
      y: MT, height: PH_, fill: 'transparent', cursor: 'ew-resize' }));
    hL[k] = svg.appendChild(el('rect', {
      y: MT, height: PH_, fill: 'transparent', cursor: 'col-resize' }));
    hR[k] = svg.appendChild(el('rect', {
      y: MT, height: PH_, fill: 'transparent', cursor: 'col-resize' }));
    tag[k] = svg.appendChild(el('text', {
      y: MT - 8, 'text-anchor': 'middle', 'font-size': 13, fill: c,
      'font-weight': '600', 'font-family': 'sans-serif' }));
  }

  function update() {
    for (let k = 0; k < PH.length; k++) {
      const a = sx(PH[k].start_idx);
      const b = k + 1 < PH.length ? sx(PH[k + 1].start_idx) : sx(N - 1);
      bands[k].setAttribute('x', a);
      bands[k].setAttribute('width', Math.max(0, b - a));
      bandText[k].setAttribute('x', a + 6);
    }
    for (let k = 1; k < PH.length; k++) {
      const cx = sx(PH[k].start_idx);
      const half = PH[k].tolerance_idx * step;
      bar[k].setAttribute('x', cx - half);
      bar[k].setAttribute('width', Math.max(0.8, 2 * half));
      line[k].setAttribute('x1', cx);
      line[k].setAttribute('x2', cx);
      const inner = Math.max(7, half - 7);
      grip[k].setAttribute('x', cx - inner);
      grip[k].setAttribute('width', 2 * inner);
      const edge = Math.max(half, 11);
      hL[k].setAttribute('x', cx - edge - 6);
      hL[k].setAttribute('width', 12);
      hR[k].setAttribute('x', cx + edge - 6);
      hR[k].setAttribute('width', 12);
      tag[k].setAttribute('x', cx);
      tag[k].textContent = PH[k].start_idx + ' \\u00b1' + PH[k].tolerance_idx;
    }
  }
  update();

  // 5. dragging. ONLY clientX is ever read: there is no vertical coordinate in
  //    this code path, so a boundary cannot leave the time axis.
  let drag = null;
  const at = (e) => {
    const m = svg.getScreenCTM();
    if (!m) return null;
    const p = svg.createSVGPoint();
    p.x = e.clientX;
    p.y = 0;
    return p.matrixTransform(m.inverse()).x;
  };
  const begin = (k, mode) => (e) => {
    e.preventDefault();
    drag = { k: k, mode: mode };
    try { svg.setPointerCapture(e.pointerId); } catch (_) {}
  };
  for (let k = 1; k < PH.length; k++) {
    grip[k].addEventListener('pointerdown', begin(k, 'move'));
    hL[k].addEventListener('pointerdown', begin(k, 'tol'));
    hR[k].addEventListener('pointerdown', begin(k, 'tol'));
  }
  svg.addEventListener('pointermove', (e) => {
    if (!drag) return;
    const x = at(e);
    if (x === null) return;
    const i = Math.max(0, Math.min(ix(x), N - 1));
    const k = drag.k;
    if (drag.mode === 'move') {
      const min = PH[k - 1].start_idx + 1;
      const max = k + 1 < PH.length ? PH[k + 1].start_idx - 1 : N - 1;
      if (min <= max) PH[k].start_idx = Math.max(min, Math.min(i, max));
    } else {
      PH[k].tolerance_idx = Math.max(0, Math.min(Math.abs(i - PH[k].start_idx), N - 1));
    }
    update();
  });
  const finish = (e) => {
    if (!drag) return;
    drag = null;
    try { svg.releasePointerCapture(e.pointerId); } catch (_) {}
    setTriggerValue('edit', JSON.stringify({
      sid: data.sid,
      phases: PH.map((p) => ({
        start_idx: p.start_idx, tolerance_idx: p.tolerance_idx })),
    }));
  };
  svg.addEventListener('pointerup', finish);
  svg.addEventListener('pointercancel', finish);
}
"""


@st.cache_resource(show_spinner=False)
def _chart_component():
    """Registered once per process — re-registering the same name warns."""
    return st.components.v2.component("cyclophaser_label_chart", js=_CHART_JS)


def chart_payload(sid: str, values: pd.Series, phases: list[dict]) -> dict:
    """Everything the chart is allowed to know.

    Pure, and deliberately narrow: this is the only channel from the app to the
    drawing surface, so keeping it to the raw values, the labeller's own marks
    and the palette is what makes the blindness checkable rather than asserted.
    tests/test_manual_labels.py pins these keys exactly.
    """
    return {
        "sid": str(sid),
        "n": int(len(values)),
        "y": [float(v) for v in values.to_numpy()],
        "phases": [{"phase": p["phase"], "start_idx": int(p["start_idx"]),
                    "tolerance_idx": int(p["tolerance_idx"])} for p in phases],
        "colors": dict(lc.PHASE_COLORS),
        "w": _W, "h": _H, "ml": _ML, "mr": _MR, "mt": _MT, "mb": _MB,
    }


def apply_edit(payload: dict, phases: list[dict], n: int) -> bool:
    """Fold one drag result back into the phases. True if anything changed.

    PURE, and that is the point: whether a browser delivers the gesture is the
    one thing that cannot be tested from here, so everything downstream of the
    message is ordinary Python with ordinary tests.

    The browser clamps as it drags, but the result is re-clamped here anyway. A
    message that arrived stale — from a chart drawn before the table was edited —
    could otherwise write a sequence that is no longer a partition of [0, n).
    """
    incoming = (payload or {}).get("phases")
    if not isinstance(incoming, list) or len(incoming) != len(phases):
        return False
    changed = False
    for k, item in enumerate(incoming):
        if not isinstance(item, dict):
            return False
        try:
            start = int(item["start_idx"])
            tol = int(item["tolerance_idx"])
        except (KeyError, TypeError, ValueError):
            return False
        if k == 0:
            start = 0                      # structural: a partition begins at 0
        else:
            low = phases[k - 1]["start_idx"] + 1
            high = phases[k + 1]["start_idx"] - 1 if k + 1 < len(phases) else n - 1
            if low > high:
                continue
            start = max(low, min(start, high))
        tol = max(0, min(tol, n - 1))
        if start != phases[k]["start_idx"] or tol != phases[k]["tolerance_idx"]:
            phases[k]["start_idx"] = start
            phases[k]["tolerance_idx"] = tol
            changed = True
    return changed


def edit_signature(payload: dict) -> str:
    """A stable identity for one drag result, for the replay guard."""
    return json.dumps(payload, sort_keys=True)


def is_new_edit(payload: dict, last_signature: str | None) -> bool:
    """Whether this message has already been acted on.

    A trigger value that outlived its rerun would otherwise be re-applied on
    every pass, and each pass reruns — a loop that takes the app down in the
    middle of a labelling session. Re-sending an identical result is a no-op
    anyway, since it describes the same positions.
    """
    return bool(payload) and edit_signature(payload) != last_signature


def _draw(sid: str, values: pd.Series, phases: list[dict]) -> dict | None:
    """Render the chart and return the last drag result, if any.

    Returns None when the component is unavailable, which the caller treats as
    "draw the fallback instead" rather than as an error.
    """
    result = _chart_component()(
        data=chart_payload(sid, values, phases),
        key=f"lab_chart__{sid}",
        on_edit_change=lambda: None,
        height=_H + 20,
    )
    raw = getattr(result, "edit", None)
    return json.loads(raw) if raw else None


def _fallback_chart(sid: str, values: pd.Series, phases: list[dict]) -> None:
    """A static picture of the same thing, for when the component cannot run.

    Not interactive — no drag, no click. It exists so that an older Streamlit,
    or a browser where the component fails, still shows the series and leaves
    the table usable. Labelling is degraded, never blocked.
    """
    import plotly.graph_objects as go

    n = len(values)
    fig = go.Figure()
    for k, ph in enumerate(phases):
        x1 = phases[k + 1]["start_idx"] if k + 1 < len(phases) else n - 1
        fig.add_vrect(x0=ph["start_idx"], x1=x1, layer="below", line_width=0,
                      fillcolor=lc.PHASE_COLORS.get(ph["phase"], "#cccccc"),
                      opacity=0.30, annotation_text=ph["phase"],
                      annotation_position="top left")
    fig.add_trace(go.Scatter(x=list(range(n)), y=values.to_numpy(), mode="lines",
                             line=dict(color="#1f2d3d", width=2), name="series"))
    for k, ph in enumerate(phases):
        if k == 0:
            continue
        colour = lc.PHASE_COLORS.get(ph["phase"], "#666666")
        tol = int(ph["tolerance_idx"])
        if tol > 0:
            fig.add_vrect(x0=ph["start_idx"] - tol, x1=ph["start_idx"] + tol,
                          layer="below", line_width=0, fillcolor=colour,
                          opacity=0.38)
        fig.add_vline(x=ph["start_idx"], line=dict(color=colour, width=2.5))
    fig.update_layout(height=_H, margin=dict(l=60, r=20, t=30, b=45),
                      showlegend=False, plot_bgcolor="white", dragmode=False,
                      title=dict(text=f"series {sid}", font=dict(size=15)),
                      xaxis=dict(title="step index", range=[-1, n]),
                      yaxis=dict(title="raw input value"))
    st.plotly_chart(fig, key=f"lab_fallback__{sid}",
                    config={"displayModeBar": False})
    st.caption("Interactive chart unavailable — the table below is fully usable.")


@st.cache_data(show_spinner=False)
def _load_population():
    """Every series to be labelled, as ({id: Series}, {id: source}).

    Cached because it re-reads 51 CSVs and re-generates 12 synthetic series;
    nothing here depends on any app parameter, so one load per session is right.
    """
    real = lc.load_real_series()
    synth, _names = lc.load_synthetic_series()
    series = {**real, **synth}
    sources = ({k: "real" for k in real} | {k: "synthetic" for k in synth})
    return series, sources


def default_phases(n: int, tolerance: int) -> list[dict]:
    """The scaffold a fresh series opens on: the canonical four phases, evenly spaced.

    Arbitrary on purpose, and visibly so — quarters of the record are not a
    proposal about this cyclone, they are somewhere to start dragging from. The
    anchoring this whole front exists to avoid is anchoring to the DETECTOR;
    a geometric scaffold carries none of its information. Labelling 63 cyclones
    four boundaries at a time from an empty table would be the bigger cost.
    """
    span = max(1, n // 4)
    rows = [("incipient", 0), ("intensification", span),
            ("mature", 2 * span), ("decay", 3 * span)]
    return [{"phase": p, "start_idx": min(i, n - 1), "tolerance_idx": int(tolerance)}
            for p, i in rows]


def render(default_tolerance: int = DEFAULT_TOLERANCE) -> None:
    """Draw the Label mode. Called from app.py's Calibration tab."""
    series, sources = _load_population()
    if not series:
        st.error("No series found to label "
                 "(tests/calibration_data/ and tests/synthetic/cases.py are both empty).")
        return

    queue = lc.build_queue(series.keys())
    records = lc.read_labels()
    n_total = len(queue)

    # Resume where the last session stopped. Stored in session state after the
    # first computation so the Back button can move off it without the next
    # rerun snapping back to the first unlabelled item.
    if "lab_pos" not in st.session_state:
        st.session_state["lab_pos"] = min(lc.queue_position(queue, records), n_total - 1)
    pos = int(st.session_state["lab_pos"]) % n_total
    sid = queue[pos]
    values = series[sid]
    n = len(values)

    st.markdown(
        "#### Manual labelling — mark every phase of this cyclone\n"
        "You are looking at the **raw input series only**. No filtering, no "
        "derivatives, and nothing the detector produced — that is deliberate, "
        "and it is what makes these labels usable as evidence. Every bar and "
        "band below is drawn from *your* marks."
    )

    n_done = len(records)
    st.progress(n_done / n_total, text=f"{n_done} of {n_total} labelled "
                                       f"· now showing #{pos + 1} in the queue")

    existing = records.get(sid)
    stale = bool(existing) and existing.get("series_sha256") != lc.series_sha256(values)
    if existing and not stale:
        seq = " → ".join(f"{p['phase']}@{p['start_idx']}" for p in existing["phases"])
        st.info(f"Already labelled — {seq}. Saving again overwrites it.")
    elif stale:
        st.warning("A label exists for this series but was written against "
                   "DIFFERENT data (series_sha256 mismatch). Treat it as void "
                   "and re-label.")

    # The authoritative phase list lives in session state, not in a widget: the
    # chart has to be able to change it before the editor is constructed, and a
    # data_editor's own state is a diff of user edits rather than the table.
    key_ph, key_rev = f"_lab_phases__{sid}", f"_lab_rev__{sid}"
    if key_ph not in st.session_state:
        if existing and not stale:
            st.session_state[key_ph] = [dict(p) for p in existing["phases"]]
        else:
            st.session_state[key_ph] = default_phases(n, default_tolerance)
        st.session_state[key_rev] = 0
    phases = st.session_state[key_ph]

    st.caption(
        "**Drag a bar** along the time axis to move that phase boundary — the "
        "shading follows it. **Drag a bar's edge** to widen or narrow its "
        "margin: the bar's own thickness *is* the uncertainty. Bars cannot "
        "leave the time axis, because vertical position means nothing here. "
        "The table below is the exact path and always works."
    )

    try:
        edit = _draw(sid, values, phases)
    except Exception:
        # No components.v2, a changed component API, malformed JSON — none of
        # which should cost the labeller their session.
        edit = None
        _fallback_chart(sid, values, phases)

    if is_new_edit(edit, st.session_state.get(f"_lab_lastedit__{sid}")):
        st.session_state[f"_lab_lastedit__{sid}"] = edit_signature(edit)
        if apply_edit(edit, phases, n):
            st.session_state[key_rev] += 1
            st.rerun()

    edited = st.data_editor(
        pd.DataFrame(phases, columns=["phase", "start_idx", "tolerance_idx"]),
        key=f"lab_tbl__{sid}__{st.session_state[key_rev]}",
        num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={
            "phase": st.column_config.SelectboxColumn(
                "Phase", options=list(lc.PHASE_ORDER), required=True, width="medium"),
            "start_idx": st.column_config.NumberColumn(
                "Starts at step", min_value=0, max_value=max(0, n - 1), step=1,
                required=True, width="small"),
            "tolerance_idx": st.column_config.NumberColumn(
                "± steps", min_value=0, max_value=max(1, n - 1), step=1,
                required=True, width="small",
                help="The margin evaluation will allow on THIS boundary, drawn "
                     "as the bar's thickness. Per boundary, not per cyclone: an "
                     "unmistakable incipient knee and a long gentle mature→decay "
                     "roll do not deserve the same forgiveness."),
        },
    )

    proposed = []
    for row in edited.to_dict("records"):
        if row.get("phase") is None or pd.isna(row.get("start_idx")):
            continue
        proposed.append({"phase": str(row["phase"]),
                         "start_idx": int(row["start_idx"]),
                         "tolerance_idx": int(row.get("tolerance_idx") or 0)})
    # The first phase starts at 0 structurally — a partition of [0, n) has to
    # begin at 0 — so it is coerced rather than reported as the labeller's error.
    if proposed:
        proposed[0]["start_idx"] = 0
    if proposed != phases:
        st.session_state[key_ph] = proposed
        st.rerun()

    problem = None
    try:
        lc.validate_phases(phases, n_steps=n)
    except (ValueError, KeyError, TypeError) as exc:
        problem = str(exc)
    if problem:
        st.error(f"Not saveable yet — {problem}")

    first = phases[0]["phase"] if phases else None
    inc_end = phases[1]["start_idx"] if (first == "incipient" and len(phases) > 1) else None
    st.caption(
        (f"Incipient phase = steps 0–{inc_end - 1} (ends at {inc_end}, "
         f"{values.index[inc_end]})" if inc_end is not None else
         "No incipient phase — this series is already changing at step 0")
        + f" · series length {n} steps"
    )

    notes = st.text_area("Notes (optional)",
                         value=(existing or {}).get("notes", ""),
                         key=f"lab_notes__{sid}", height=68)

    def _save(ambiguous: bool) -> None:
        rec = lc.make_label_record(sid, sources[sid], values, phases,
                                   notes=notes or None, ambiguous=ambiguous)
        lc.upsert_label(rec)
        st.session_state["lab_pos"] = (pos + 1) % n_total

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("💾 Save & next", type="primary", use_container_width=True,
                 disabled=bool(problem)):
        _save(ambiguous=False)
        st.rerun()
    if b2.button("No incipient phase", use_container_width=True,
                 disabled=not (phases and phases[0]["phase"] == "incipient"),
                 help="Drops the leading incipient phase — this series is "
                      "already changing at step 0. The rest of the sequence is kept."):
        rest = [dict(p) for p in phases[1:]]
        if rest:
            rest[0]["start_idx"] = 0
            st.session_state[key_ph] = rest
            st.session_state[key_rev] += 1
        st.rerun()
    if b3.button("Save as ambiguous", use_container_width=True,
                 disabled=bool(problem),
                 help="You cannot decide the incipient boundary. The phases you "
                      "marked are still saved; the incipient verdict is recorded "
                      "as ambiguous and kept out of the hit rate and the MAE."):
        _save(ambiguous=True)
        st.rerun()
    if b4.button("← Back", use_container_width=True,
                 help="Re-label the previous series in the queue."):
        st.session_state["lab_pos"] = (pos - 1) % n_total
        st.rerun()

    st.caption(
        f"Queue order is shuffled with a fixed seed ({lc.QUEUE_SEED}) rather than "
        "sorted by id: the real track ids are chronological, so labelling them in "
        "order would align fatigue with the identifier and any drift in your "
        "criteria would look like a real time-dependent effect. "
        f"Labels are written to `{lc.LABELS_PATH.relative_to(_REPO_ROOT)}` the "
        "moment you press a button, each save rewriting the file atomically — "
        "closing the tab cannot lose work."
    )
