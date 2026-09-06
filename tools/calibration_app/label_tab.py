"""BLIND manual labelling of the incipient boundary.

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
can see where the detector put the boundary, the label stops being independent
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

tests/test_manual_labels.py asserts the absence of those imports and of the
detector-output identifiers by reading this file's source. If you add a
diagnostic layer here, that test fails, and it is right to.
"""

from __future__ import annotations

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


def _fig(sid: str, values: pd.Series, boundary: int | None) -> go.Figure:
    """The raw series, a click target, and the candidate boundary. Nothing else.

    x is the STEP INDEX, not the timestamp: the label is an index (the incipient
    phase is [0, N)), so plotting against the index removes a conversion between
    what is clicked and what is stored. The timestamp is still available on hover
    and is printed under the chart.
    """
    x = list(range(len(values)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=values.to_numpy(),
        mode="lines+markers",
        line=dict(color="#1f2d3d", width=2),
        # Markers are the click targets, so every step must have one; they are
        # kept small so the eye still reads a curve rather than a dot plot.
        marker=dict(size=5, color="#1f2d3d"),
        name="series",
        customdata=[str(t) for t in values.index],
        hovertemplate="step %{x}<br>%{customdata}<br>%{y:.3e}<extra></extra>",
    ))
    if boundary is not None:
        fig.add_vline(x=boundary, line=dict(color="#c1121f", width=3, dash="solid"))
        fig.add_vrect(x0=0, x1=boundary, fillcolor="#c1121f", opacity=0.08,
                      line_width=0)
    fig.update_layout(
        height=520, margin=dict(l=60, r=20, t=30, b=45),
        showlegend=False, hovermode="closest",
        title=dict(text=f"series {sid}", font=dict(size=15)),
        xaxis=dict(title="step index", showgrid=True, gridcolor="#eceff3"),
        yaxis=dict(title="raw input value", showgrid=True, gridcolor="#eceff3"),
        plot_bgcolor="white",
        dragmode=False,
    )
    return fig


def _apply_click(sid: str, event, n: int) -> None:
    """Fold a Plotly click into the index widget's state.

    Runs BEFORE the number_input is constructed, because Streamlit reads a
    widget's session_state value at construction time; writing it afterwards
    would not take effect until the following rerun and the marker would appear
    to lag one click behind.

    The selection persists across reruns, so the raw event cannot be used
    directly — it would re-apply itself and pin the widget, making the manual
    input unusable. Only a click at a DIFFERENT step than the one last applied
    counts as new.
    """
    try:
        pts = (event or {}).get("selection", {}).get("points", [])
    except AttributeError:
        pts = []
    if not pts:
        return
    clicked = int(pts[-1].get("x", 0))
    clicked = max(1, min(clicked, n - 1))
    seen_key = f"_lab_lastclick__{sid}"
    if st.session_state.get(seen_key) == clicked:
        return
    st.session_state[seen_key] = clicked
    st.session_state[f"lab_idx__{sid}"] = clicked


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
        "#### Manual labelling — where does the incipient phase end?\n"
        "You are looking at the **raw input series only**. No filtering, no "
        "derivatives, and nothing the detector produced — that is deliberate, "
        "and it is what makes these labels usable as evidence."
    )

    n_done = len(records)
    st.progress(n_done / n_total, text=f"{n_done} of {n_total} labelled "
                                       f"· now showing #{pos + 1} in the queue")

    existing = records.get(sid)
    stale = bool(existing) and existing.get("series_sha256") != lc.series_sha256(values)
    if existing and not stale:
        v = existing["verdict"]
        detail = (f"boundary at {v['incipient_end_idx']}" if v["kind"] == "boundary"
                  else v["kind"])
        st.info(f"Already labelled — **{detail}**, ±{existing['tolerance_idx']} steps. "
                "Saving again overwrites it.")
    elif stale:
        st.warning("A label exists for this series but was written against "
                   "DIFFERENT data (series_sha256 mismatch). Treat it as void "
                   "and re-label.")

    # Seed the index widget before it is built: mid-series is a neutral starting
    # point that does not suggest an answer, and a stored label re-opens on itself.
    key_idx, key_tol = f"lab_idx__{sid}", f"lab_tol__{sid}"
    if key_idx not in st.session_state:
        if existing and not stale and existing["verdict"]["kind"] == "boundary":
            st.session_state[key_idx] = int(existing["verdict"]["incipient_end_idx"])
        else:
            st.session_state[key_idx] = max(1, n // 2)
    if key_tol not in st.session_state:
        st.session_state[key_tol] = int(existing["tolerance_idx"]) if existing \
            else int(default_tolerance)

    event = st.plotly_chart(
        _fig(sid, values, int(st.session_state[key_idx])),
        key=f"lab_chart__{sid}",
        on_select="rerun", selection_mode="points",
        config={"displayModeBar": False},
    )
    _apply_click(sid, event, n)

    col_a, col_b = st.columns([3, 2])
    with col_a:
        # The slider is the guaranteed path. Clicking the chart is faster, but it
        # depends on Plotly selection events surviving the browser and the
        # Streamlit version; the label must be settable without them.
        st.slider("Incipient ends at step (the incipient phase is [0, N))",
                  min_value=1, max_value=max(1, n - 1), key=key_idx)
    with col_b:
        st.number_input("± steps you accept for THIS series", min_value=0,
                        max_value=max(1, n - 1), step=1, key=key_tol,
                        help="The margin evaluation will allow on this label. "
                             "Per-series because some knees are obvious and some "
                             "ramps are gentle enough that ten indices would do.")

    idx = int(st.session_state[key_idx])
    st.caption(f"**Boundary at step {idx}** · {values.index[idx]} · "
               f"series length {n} steps · incipient phase would be steps 0–{idx - 1}")

    notes = st.text_area("Notes (optional)",
                         value=(existing or {}).get("notes", ""),
                         key=f"lab_notes__{sid}", height=68)

    def _save(verdict: dict) -> None:
        rec = lc.make_label_record(sid, sources[sid], values, verdict,
                                   int(st.session_state[key_tol]),
                                   notes=notes or None)
        lc.upsert_label(rec)
        st.session_state["lab_pos"] = (pos + 1) % n_total

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("💾 Save & next", type="primary", use_container_width=True):
        _save({"kind": "boundary", "incipient_end_idx": idx})
        st.rerun()
    if b2.button("No incipient phase", use_container_width=True,
                 help="This series never starts flat — it is already changing at step 0."):
        _save({"kind": "none"})
        st.rerun()
    if b3.button("Ambiguous", use_container_width=True,
                 help="You cannot decide. Kept out of the hit rate and the MAE, "
                      "counted in the refusal accounting."):
        _save({"kind": "ambiguous"})
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
