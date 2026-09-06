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

Every colour, band and arrow drawn here comes from the LABELLER'S OWN marks. The
phase palette is the project's standard one (blue incipient, amber
intensification, red mature, olive decay, grey residual) so that a labelled
series reads the same way as every other phase figure in the repo — but it is
painting the human's answer, never the algorithm's.

tests/test_manual_labels.py asserts the absence of those imports and of the
detector-output identifiers by reading this file's source. If you add a
diagnostic layer here, that test fails, and it is right to.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_LABELS_PKG = _REPO_ROOT / "research" / "labels"
if str(_LABELS_PKG) not in sys.path:
    sys.path.insert(0, str(_LABELS_PKG))

import labels_core as lc  # noqa: E402

DEFAULT_TOLERANCE = 5

# Names stamped on the draggable shapes/annotations, and the relayout keys the
# browser reports them under.
_BND, _TOL = "bnd", "tol"
_SHAPE_KEY = re.compile(r"^shapes\[(\d+)\]\.x0$")
_ANN_KEY = re.compile(r"^annotations\[(\d+)\]\.ax$")


# ── the drag bridge ──────────────────────────────────────────────────────────
# st.plotly_chart cannot deliver a drag: its own docs say "Only selection events
# are supported at this time", and a dragged shape arrives as `plotly_relayout`,
# which it does not forward. So a small bidirectional component attaches to the
# chart that st.plotly_chart already rendered — same DOM, components are not
# sandboxed — and forwards just the relayout keys this view cares about.
#
# It adds no visuals and reads nothing: if it fails to bind, or the Streamlit
# version has no components.v2, dragging simply does nothing and the table and
# click paths are untouched. Labelling is never blocked on it.
_DRAG_JS = """
export default function (component) {
  const { setTriggerValue } = component;

  const bind = () => {
    const gds = document.querySelectorAll('.js-plotly-plot');
    let bound = false;
    gds.forEach((gd) => {
      if (typeof gd.on !== 'function') return;
      bound = true;
      if (gd.__cpLabelDragBound) return;
      gd.__cpLabelDragBound = true;
      gd.on('plotly_relayout', (ev) => {
        const out = {};
        for (const k in ev) {
          if (/^shapes\\[\\d+\\]\\.x0$/.test(k) || /^annotations\\[\\d+\\]\\.ax$/.test(k)) {
            out[k] = ev[k];
          }
        }
        if (Object.keys(out).length) setTriggerValue('drag', JSON.stringify(out));
      });
    });
    return bound;
  };

  // The component can mount before Plotly has finished drawing, so retry
  // briefly rather than giving up on the first miss.
  if (!bind()) {
    let tries = 0;
    const t = setInterval(() => { if (bind() || ++tries > 40) clearInterval(t); }, 100);
  }
}
"""


@st.cache_resource(show_spinner=False)
def _drag_component():
    """Registered once per process — re-registering the same name warns."""
    return st.components.v2.component("cyclophaser_label_drag", js=_DRAG_JS)


def _read_drag() -> dict | None:
    """The last drag payload, or None if the bridge is unavailable or idle."""
    try:
        result = _drag_component()(key="lab_drag", on_drag_change=lambda: None,
                                   height=0)
        raw = getattr(result, "drag", None)
        return json.loads(raw) if raw else None
    except Exception:
        # No components.v2, a changed component API, malformed JSON — none of
        # which should cost the labeller their session. Drag is a convenience;
        # the table is the contract.
        return None


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


def _fig(sid: str, values: pd.Series, phases: list[dict]) -> go.Figure:
    """The raw series, the labeller's phases, and their tolerance bands.

    x is the STEP INDEX, not the timestamp: a label is an index, so plotting
    against the index removes a conversion between what is clicked and what is
    stored. The timestamp is still on hover and printed under the chart.

    Phases are shaded in the project's standard palette and each boundary gets a
    translucent band plus a double-headed arrow spanning [start-tol, start+tol],
    because the margin is the part of a label that is easiest to set carelessly:
    a number in a table gives no sense of how much of the curve it actually
    forgives, and seeing the arrow cover half a ramp is what prompts a smaller one.
    """
    n = len(values)
    x = list(range(n))
    y = values.to_numpy()
    lo, hi = float(y.min()), float(y.max())
    span = (hi - lo) or 1.0
    # Headroom above the curve for the tolerance arrows, so they never sit on
    # top of the data they are describing.
    y_arrow = hi + 0.13 * span
    y_top = hi + 0.26 * span

    fig = go.Figure()

    # Phase shading — the labeller's own partition of [0, n).
    for k, ph in enumerate(phases):
        x0 = ph["start_idx"]
        x1 = phases[k + 1]["start_idx"] if k + 1 < len(phases) else n - 1
        fig.add_vrect(x0=x0, x1=x1, layer="below", line_width=0, editable=False,
                      fillcolor=lc.PHASE_COLORS.get(ph["phase"], "#cccccc"),
                      opacity=0.30,
                      annotation_text=ph["phase"], annotation_position="top left",
                      annotation=dict(font=dict(size=11, color="#33414f")))

    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines+markers",
        line=dict(color="#1f2d3d", width=2),
        # Markers are the click targets, so every step must have one; they are
        # kept small so the eye still reads a curve rather than a dot plot.
        marker=dict(size=5, color="#1f2d3d"),
        name="series",
        customdata=[str(t) for t in values.index],
        hovertemplate="step %{x}<br>%{customdata}<br>%{y:.3e}<extra></extra>",
    ))

    # Boundaries and their tolerance. Index 0 is skipped: it is 0 by
    # construction, not a judgement, and has no margin to show.
    for k, ph in enumerate(phases):
        if k == 0:
            continue
        idx = ph["start_idx"]
        tol = int(ph["tolerance_idx"])
        colour = lc.PHASE_COLORS.get(ph["phase"], "#666666")
        # `name` is what makes the drag round-trip robust: Plotly reports a drag
        # as `shapes[i].x0`, by POSITION in layout.shapes, and the positions
        # depend on the order these helpers happen to append in. Naming the
        # draggable ones and looking their indices back up (see `drag_map`)
        # survives any reordering of this function.
        fig.add_vline(x=idx, line=dict(color=colour, width=3),
                      name=f"{_BND}{k}", editable=True)
        if tol > 0:
            a, b = max(0, idx - tol), min(n - 1, idx + tol)
            fig.add_vrect(x0=a, x1=b, layer="below", line_width=0, editable=False,
                          fillcolor=colour, opacity=0.22)
            fig.add_annotation(
                x=b, y=y_arrow, ax=a, ay=y_arrow,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=1.8,
                arrowcolor=colour, arrowside="end+start", text="",
                name=f"{_TOL}{k}")
        fig.add_annotation(
            x=idx, y=y_arrow, xref="x", yref="y", showarrow=False,
            text=f"<b>{idx}</b> ±{tol}", yshift=13,
            font=dict(size=11, color=colour),
            bgcolor="rgba(255,255,255,0.75)")

    fig.update_layout(
        height=560, margin=dict(l=60, r=20, t=30, b=45),
        showlegend=False, hovermode="closest",
        title=dict(text=f"series {sid}", font=dict(size=15)),
        xaxis=dict(title="step index", showgrid=True, gridcolor="#eceff3",
                   range=[-1, n]),
        yaxis=dict(title="raw input value", showgrid=True, gridcolor="#eceff3",
                   range=[lo - 0.06 * span, y_top]),
        plot_bgcolor="white",
        dragmode=False,
    )
    return fig


def drag_map(fig) -> dict[str, dict[int, int]]:
    """Which layout index belongs to which boundary.

    Plotly reports a drag positionally — `shapes[7].x0`, `annotations[2].ax` —
    so the browser's message is meaningless without this. Built by reading the
    names back off the figure rather than by counting the calls that made it, so
    adding a decoration to `_fig` cannot silently misroute a drag onto the wrong
    boundary.
    """
    shapes = {i: int(sh.name[len(_BND):])
              for i, sh in enumerate(fig.layout.shapes or ())
              if sh.name and sh.name.startswith(_BND)}
    anns = {i: int(an.name[len(_TOL):])
            for i, an in enumerate(fig.layout.annotations or ())
            if an.name and an.name.startswith(_TOL)}
    return {"shapes": shapes, "annotations": anns}


def apply_drag(payload: dict, phases: list[dict], dmap: dict, n: int) -> bool:
    """Fold a Plotly relayout payload into the phases. True if anything moved.

    PURE, and deliberately so: whether the browser emits these keys on a drag is
    the one part of this feature that cannot be tested from here, so everything
    downstream of the payload is ordinary Python with ordinary tests.

    Boundaries are applied before tolerances, because a tolerance arrives as the
    absolute position of the arrow's tail and only becomes a ± once it is
    measured against the boundary it belongs to — which may have moved in the
    same gesture.
    """
    moved = False
    for key, value in sorted(payload.items()):
        m = _SHAPE_KEY.match(key)
        if not m:
            continue
        k = dmap["shapes"].get(int(m.group(1)))
        if k is None or not (1 <= k < len(phases)):
            continue
        low = phases[k - 1]["start_idx"] + 1
        high = phases[k + 1]["start_idx"] - 1 if k + 1 < len(phases) else n - 1
        if low > high:
            continue
        new = max(low, min(int(round(float(value))), high))
        if new != phases[k]["start_idx"]:
            phases[k]["start_idx"] = new
            moved = True

    for key, value in sorted(payload.items()):
        m = _ANN_KEY.match(key)
        if not m:
            continue
        k = dmap["annotations"].get(int(m.group(1)))
        if k is None or not (0 <= k < len(phases)):
            continue
        # The arrow is drawn symmetric, so the tail is one half of it: the margin
        # is its distance from the boundary, whichever side it was dragged to.
        tol = abs(int(round(float(value))) - phases[k]["start_idx"])
        tol = max(0, min(tol, n - 1))
        if tol != phases[k]["tolerance_idx"]:
            phases[k]["tolerance_idx"] = tol
            moved = True
    return moved


def _apply_click(sid: str, event, target: int, phases: list[dict], n: int) -> bool:
    """Fold a Plotly click into the selected boundary. True if anything moved.

    The selection persists across reruns, so the raw event cannot be used
    directly — it would re-apply itself on every rerun and pin the boundary,
    making the table unusable. Only a click at a DIFFERENT step than the one last
    applied counts as new.
    """
    try:
        pts = (event or {}).get("selection", {}).get("points", [])
    except AttributeError:
        pts = []
    if not pts or target < 1 or target >= len(phases):
        return False
    clicked = max(1, min(int(pts[-1].get("x", 0)), n - 1))
    seen_key = f"_lab_lastclick__{sid}"
    if st.session_state.get(seen_key) == (target, clicked):
        return False
    st.session_state[seen_key] = (target, clicked)
    # A click that would cross a neighbouring boundary is clamped rather than
    # rejected: silently doing nothing on a click reads as a broken chart.
    low = phases[target - 1]["start_idx"] + 1
    high = (phases[target + 1]["start_idx"] - 1
            if target + 1 < len(phases) else n - 1)
    if low > high:
        return False
    phases[target]["start_idx"] = max(low, min(clicked, high))
    return True


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
        "and it is what makes these labels usable as evidence. Every band and "
        "arrow below is drawn from *your* marks."
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

    # The authoritative phase list lives in session state, not in the editor
    # widget: a chart click has to be able to change it BEFORE the editor is
    # constructed, and a data_editor's own state is a diff of user edits rather
    # than the table itself.
    key_ph, key_rev = f"_lab_phases__{sid}", f"_lab_rev__{sid}"
    if key_ph not in st.session_state:
        if existing and not stale:
            st.session_state[key_ph] = [dict(p) for p in existing["phases"]]
        else:
            st.session_state[key_ph] = default_phases(n, default_tolerance)
        st.session_state[key_rev] = 0
    phases = st.session_state[key_ph]

    labels = [f"{k} · {p['phase']} @ {p['start_idx']}"
              for k, p in enumerate(phases) if k >= 1]
    target_label = st.selectbox(
        "Chart click moves this boundary", options=labels or ["(no boundary yet)"],
        key=f"lab_target__{sid}",
        help="Clicking the chart is the fast path; the table below is the exact "
             "one. The first phase always starts at step 0, so it is not listed.")
    st.caption(
        "**Drag** a boundary line to move it, or the end of a tolerance arrow to "
        "widen or narrow that margin. If dragging does nothing in your browser, "
        "nothing is broken — use the click above or the table below, which are "
        "the paths that do not depend on it.")
    target = (labels.index(target_label) + 1) if labels and target_label in labels else 0

    fig = _fig(sid, values, phases)
    event = st.plotly_chart(
        fig,
        key=f"lab_chart__{sid}",
        on_select="rerun", selection_mode="points",
        config={"displayModeBar": False,
                # Only the boundary lines carry editable=True; every band is
                # pinned editable=False, so these two switches cannot make the
                # phase shading draggable by accident.
                "edits": {"shapePosition": True, "annotationTail": True}},
    )

    payload = _read_drag()
    if payload and apply_drag(payload, phases, drag_map(fig), n):
        st.session_state[key_rev] += 1
        st.rerun()

    if _apply_click(sid, event, target, phases, n):
        st.session_state[key_rev] += 1
        st.rerun()

    # The editor is re-seeded (via a changing key) whenever a click mutates the
    # list, so the table and the chart can never disagree about what is labelled.
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
                help="The margin evaluation will allow on THIS boundary. Per "
                     "boundary, not per cyclone: an unmistakable incipient knee "
                     "and a long gentle mature→decay roll do not deserve the "
                     "same forgiveness."),
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
