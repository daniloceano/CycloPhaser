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


The table is the label. The chart is a convenience.
---------------------------------------------------
That ordering is the load-bearing decision in this module, and it was learned
the expensive way: the drag interaction was delivered three times and worked
zero times in a browser, while every check that had been run on it passed.

The reason it never worked was not in the JavaScript, which was correct
throughout. It was one line of Python:

    key=f"lab_chart__{sid}"

`__` is the delimiter Streamlit reserves inside a bidirectional component's
element id, so mounting raised BidiComponentInvalidIdError every single time.
The call sat inside `except Exception:` with a static Plotly picture as the
fallback, so the app quietly drew a chart that could not be dragged and said
nothing. Nobody was ever dragging a broken bar; there was never a bar to drag.

Three things in here follow from that, and none of them is decoration:

1. **The numeric table is the canonical path.** Every field is editable and a
   complete label can be produced without touching the chart at all. When the
   chart fails — and it is a hand-written component talking to a shadow DOM
   across a websocket, so it will fail again — labelling continues.
2. **There is no silent fallback.** A chart that cannot mount says so, in red,
   naming the exception. The old fallback drew a plausible non-interactive
   picture, which is worse than drawing nothing: it made a total failure of the
   component look like a working screen, and that is precisely what hid this bug
   for three rounds.
3. **Nothing here is believed until a real browser has done it.** The checks
   that passed while the feature was broken ran the component's JS against a
   simulated DOM in Node. That harness could not have caught this: the bug was
   in the Python mount call, which it never executed. It has been deleted and
   replaced by tests/test_label_browser.py, which drives Chromium against the
   actual Streamlit app with real pointer events and reads back the values that
   reached Python.


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
import re
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

  // ── reuse before rebuild ───────────────────────────────────────────────────
  // This function runs again on EVERY Streamlit rerender, and a rerender can
  // land in the middle of a gesture (any sidebar widget triggers one). Tearing
  // the SVG down and building a new one would take the listeners and the
  // in-flight drag with it, so the node is kept and its attributes updated
  // whenever the series and the number of phases are unchanged. Only a genuinely
  // different chart is rebuilt.
  const host0 = parentElement.querySelector('#cp-label-chart');
  const S0 = host0 && host0.__cp;
  if (S0 && S0.sid === data.sid && S0.n === data.n &&
      S0.PH.length === data.phases.length) {
    S0.setTrigger = setTriggerValue;   // a fresh closure arrives each rerender
    if (!S0.drag) {                    // never overwrite what is being dragged
      for (let k = 0; k < data.phases.length; k++) {
        S0.PH[k].start_idx = data.phases[k].start_idx;
        S0.PH[k].tolerance_idx = data.phases[k].tolerance_idx;
        S0.PH[k].unsure = !!data.phases[k].unsure;
        S0.PH[k].phase = data.phases[k].phase;
      }
      S0.update();
    }
    return;
  }
  if (S0) S0.teardown();
  if (host0) host0.remove();

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

  const host = document.createElement('div');
  host.id = 'cp-label-chart';
  host.dataset.sid = data.sid;
  parentElement.appendChild(host);

  const svg = el('svg', {
    viewBox: `0 0 ${W} ${H}`, width: '100%',
    preserveAspectRatio: 'xMidYMid meet',
    tabindex: '0',
    // The browser test maps a step index to a viewport pixel through this
    // element's own screen CTM, and needs the step count to do it.
    'data-n': String(N), 'data-sid': data.sid,
    style: 'touch-action:none;user-select:none;display:block;cursor:default;outline:none',
  });
  host.appendChild(svg);
  svg.appendChild(el('rect', { x: 0, y: 0, width: W, height: H, fill: '#ffffff' }));

  // 1. phase bands (below everything)
  const bands = PH.map((p) =>
    svg.appendChild(el('rect', {
      y: MT, height: PH_, fill: COL[p.phase] || '#cccccc', 'fill-opacity': 0.30,
    })));
  const bandText = PH.map(() =>
    svg.appendChild(el('text', {
      y: MT + 15, 'font-size': 12, fill: '#33414f', 'font-family': 'sans-serif',
    })));

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
      y: MT, height: PH_, fill: 'transparent', cursor: 'ew-resize',
      'data-grip': String(k) }));
    hL[k] = svg.appendChild(el('rect', {
      y: MT, height: PH_, fill: 'transparent', cursor: 'col-resize',
      'data-edge': String(k) }));
    hR[k] = svg.appendChild(el('rect', {
      y: MT, height: PH_, fill: 'transparent', cursor: 'col-resize',
      'data-edge': String(k) }));
    tag[k] = svg.appendChild(el('text', {
      y: MT - 8, 'text-anchor': 'middle', 'font-size': 13, fill: c,
      'font-weight': '600', 'font-family': 'sans-serif' }));
  }

  // A failure to reach Python must be VISIBLE. Drawing it inside the chart puts
  // it where the labeller is already looking, at the moment the gesture that
  // failed was made — a console message would be silence.
  const alert = svg.appendChild(el('text', {
    x: ML, y: H - 26, 'font-size': 13, fill: '#c1121f', 'font-weight': '600',
    'font-family': 'sans-serif' }));
  const warn = (msg) => { alert.textContent = msg || ''; };

  function update() {
    for (let k = 0; k < PH.length; k++) {
      const a = sx(PH[k].start_idx);
      const b = k + 1 < PH.length ? sx(PH[k + 1].start_idx) : sx(N - 1);
      bands[k].setAttribute('x', a);
      bands[k].setAttribute('width', Math.max(0, b - a));
      bands[k].setAttribute('fill', COL[PH[k].phase] || '#cccccc');
      bandText[k].setAttribute('x', a + 6);
      bandText[k].textContent = PH[k].phase;
    }
    for (let k = 1; k < PH.length; k++) {
      const c = COL[PH[k].phase] || '#666666';
      const cx = sx(PH[k].start_idx);
      const half = PH[k].tolerance_idx * step;
      const sel = S.sel === k;
      bar[k].setAttribute('x', cx - half);
      bar[k].setAttribute('width', Math.max(0.8, 2 * half));
      bar[k].setAttribute('fill', c);
      bar[k].setAttribute('stroke', c);
      // An unsure boundary is drawn hollow and dashed: it is a mark the labeller
      // made and then declined to stand behind, and evaluation skips it.
      bar[k].setAttribute('fill-opacity', PH[k].unsure ? 0.10 : 0.38);
      bar[k].setAttribute('stroke-dasharray', PH[k].unsure ? '5 4' : 'none');
      line[k].setAttribute('x1', cx);
      line[k].setAttribute('x2', cx);
      line[k].setAttribute('stroke', c);
      line[k].setAttribute('stroke-width', sel ? 4.5 : 2.5);
      line[k].setAttribute('stroke-dasharray', PH[k].unsure ? '6 4' : 'none');
      const inner = Math.max(7, half - 7);
      grip[k].setAttribute('x', cx - inner);
      grip[k].setAttribute('width', 2 * inner);
      const edge = Math.max(half, 11);
      hL[k].setAttribute('x', cx - edge - 6);
      hL[k].setAttribute('width', 12);
      hR[k].setAttribute('x', cx + edge - 6);
      hR[k].setAttribute('width', 12);
      tag[k].setAttribute('x', cx);
      tag[k].setAttribute('fill', c);
      tag[k].setAttribute('font-weight', sel ? '800' : '600');
      tag[k].textContent = PH[k].start_idx + ' ±' + PH[k].tolerance_idx +
        (PH[k].unsure ? ' ?' : '') + (sel ? ' ◂▸' : '');
    }
  }

  // ── the message back to Python ─────────────────────────────────────────────
  // `seq` is a monotonic counter rather than a hash of the positions. Two
  // identical gestures — drag a bar away and back, then away again — describe
  // the same numbers, and a signature over the numbers alone cannot tell the
  // second from a stale replay of the first. The app dedups on the counter, so
  // a repeat is delivered and a replay still is not.
  function emit() {
    const payload = {
      sid: S.sid,
      seq: ++S.seq,
      phases: S.PH.map((p) => ({
        start_idx: p.start_idx, tolerance_idx: p.tolerance_idx })),
    };
    try {
      if (typeof S.setTrigger !== 'function') {
        throw new Error('setTriggerValue is not available');
      }
      S.setTrigger('edit', JSON.stringify(payload));
      warn('');
    } catch (err) {
      warn('⚠ this edit did not reach the app (' + (err && err.message) +
           ') — type it in the table below');
    }
  }

  const at = (e) => {
    const m = svg.getScreenCTM();
    if (!m) return null;
    const p = svg.createSVGPoint();
    p.x = e.clientX;
    p.y = 0;
    return p.matrixTransform(m.inverse()).x;
  };

  const setStart = (k, i) => {
    const min = S.PH[k - 1].start_idx + 1;
    const max = k + 1 < S.PH.length ? S.PH[k + 1].start_idx - 1 : N - 1;
    if (min > max) return false;
    const v = Math.max(min, Math.min(i, max));
    if (v === S.PH[k].start_idx) return false;
    S.PH[k].start_idx = v;
    return true;
  };
  const setTol = (k, t) => {
    const v = Math.max(0, Math.min(t, N - 1));
    if (v === S.PH[k].tolerance_idx) return false;
    S.PH[k].tolerance_idx = v;
    return true;
  };

  const onDown = (k, mode) => (e) => {
    e.preventDefault();
    S.drag = { k: k, mode: mode };
    S.sel = k;
    try { svg.focus({ preventScroll: true }); } catch (_) { /* not focusable */ }
    update();
  };
  for (let k = 1; k < PH.length; k++) {
    grip[k].addEventListener('pointerdown', onDown(k, 'move'));
    hL[k].addEventListener('pointerdown', onDown(k, 'tol'));
    hR[k].addEventListener('pointerdown', onDown(k, 'tol'));
  }

  // ── move/up/cancel live on WINDOW, not on the <svg> ────────────────────────
  // On the SVG they only fire while the pointer is over it. A pointer released
  // outside the plot — past the right edge, over the sidebar, off the window —
  // never delivered pointerup, so the drag never finished and the edit was never
  // sent: the bar snapped back on the next rerender with no error anywhere.
  // setPointerCapture was supposed to cover that, but it was wrapped in a silent
  // try/catch, so when it failed nothing said so. On window the events arrive
  // regardless of where the pointer is, and no capture is needed at all.
  const onMove = (e) => {
    if (!S.drag) return;
    const x = at(e);
    if (x === null) return;
    const i = Math.max(0, Math.min(ix(x), N - 1));
    const k = S.drag.k;
    if (S.drag.mode === 'move') setStart(k, i);
    else setTol(k, Math.abs(i - S.PH[k].start_idx));
    update();
  };
  const onUp = () => {
    if (!S.drag) return;
    S.drag = null;
    update();
    emit();
  };
  window.addEventListener('pointermove', onMove);
  window.addEventListener('pointerup', onUp);
  window.addEventListener('pointercancel', onUp);

  // ── keyboard ───────────────────────────────────────────────────────────────
  // Not an accessibility afterthought. On a 259-step series one index is under
  // four pixels wide, so the last few steps of any boundary cannot be placed
  // with a pointer at all; and when the pointer path fails for any reason, this
  // is the one that still works. Left/right move the boundary, up/down widen and
  // narrow the margin, shift multiplies by five.
  const onKey = (e) => {
    if (S.PH.length < 2) return;
    const big = e.shiftKey ? 5 : 1;
    let k = S.sel;
    if (k < 1 || k >= S.PH.length) k = S.sel = 1;
    let touched = false;
    switch (e.key) {
      case 'ArrowLeft':  touched = setStart(k, S.PH[k].start_idx - big); break;
      case 'ArrowRight': touched = setStart(k, S.PH[k].start_idx + big); break;
      case 'ArrowUp':    touched = setTol(k, S.PH[k].tolerance_idx + big); break;
      case 'ArrowDown':  touched = setTol(k, S.PH[k].tolerance_idx - big); break;
      case 'Tab': {
        e.preventDefault();
        S.sel = e.shiftKey
          ? (k <= 1 ? S.PH.length - 1 : k - 1)
          : (k >= S.PH.length - 1 ? 1 : k + 1);
        update();
        return;
      }
      default: return;
    }
    e.preventDefault();
    if (touched) { update(); emit(); }
  };
  svg.addEventListener('keydown', onKey);

  const S = {
    sid: data.sid, n: N, PH: PH, drag: null, seq: 0, sel: 1,
    setTrigger: setTriggerValue, update: update,
    teardown: () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);
    },
  };
  host.__cp = S;
  update();
}
"""


# A bidirectional component's element id must not contain `__`: Streamlit uses
# that sequence as its own delimiter and raises BidiComponentInvalidIdError on
# mount. The old key was f"lab_chart__{sid}", so the component NEVER mounted, in
# any browser, from the day it was written — and the exception was swallowed by
# the fallback. Every character outside [A-Za-z0-9-] is folded to `-`, which
# makes a doubled underscore unrepresentable rather than merely absent today.
_KEY_SAFE = re.compile(r"[^A-Za-z0-9-]+")


def chart_key(sid: str) -> str:
    """The component key for one series. Never contains `__`; see above."""
    return "labchart-" + _KEY_SAFE.sub("-", str(sid))


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
                    "tolerance_idx": int(p["tolerance_idx"]),
                    "unsure": bool(p.get("unsure", False))} for p in phases],
        "colors": dict(lc.PHASE_COLORS),
        "w": _W, "h": _H, "ml": _ML, "mr": _MR, "mt": _MT, "mb": _MB,
    }


def apply_edit(payload: dict, phases: list[dict], n: int) -> bool:
    """Fold one drag or keystroke result back into the phases. True if changed.

    PURE, and that is the point: whether a browser delivers the gesture is the
    one thing that cannot be tested from here, so everything downstream of the
    message is ordinary Python with ordinary tests.

    The browser clamps as it drags, but the result is re-clamped here anyway. A
    message that arrived stale — from a chart drawn before the table was edited —
    could otherwise write a sequence that is no longer a partition of [0, n).

    `unsure` is NOT read from the message. It is a judgement the chart cannot
    make and does not send; the table owns it, and a drag must never clear it.
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
    """A stable identity for one message from the chart, for the replay guard.

    Keyed on the component's own monotonic `seq` rather than on the positions it
    reports. Hashing the positions cannot tell two identical gestures apart from
    one gesture replayed: drag a bar to 40, back to 30, out to 40 again and the
    third message is byte-identical to the first, so it was DISCARDED and the bar
    appeared to spring back on its own. A counter distinguishes them, and still
    identifies a trigger value that merely outlived its rerun.

    Falls back to the whole payload when there is no counter, so a message from
    an older component build is still deduplicated rather than looping.
    """
    if not isinstance(payload, dict) or not payload:
        return ""
    seq = payload.get("seq")
    if seq is None:
        return json.dumps(payload, sort_keys=True)
    return f"{payload.get('sid')}#{seq}"


def is_new_edit(payload: dict, last_signature: str | None) -> bool:
    """Whether this message has already been acted on.

    A trigger value that outlived its rerun would otherwise be re-applied on
    every pass, and each pass reruns — a loop that takes the app down in the
    middle of a labelling session.
    """
    return bool(payload) and edit_signature(payload) != last_signature


def _draw(sid: str, values: pd.Series, phases: list[dict]) -> dict | None:
    """Mount the chart and return its last message, if any.

    Raises rather than returning None on a mount failure: the caller has to be
    able to tell "the labeller has not touched it yet" from "the chart is not
    there", because those two need opposite things on screen.
    """
    result = _chart_component()(
        data=chart_payload(sid, values, phases),
        key=chart_key(sid),
        on_edit_change=lambda: None,
        height=_H + 20,
    )
    raw = getattr(result, "edit", None)
    return json.loads(raw) if raw else None


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
    return [{"phase": p, "start_idx": min(i, n - 1), "tolerance_idx": int(tolerance),
             "unsure": False} for p, i in rows]


# phase · start · margin · not-sure
_TABLE_COLS = [2.2, 1.6, 1.6, 1.4]


def _phase_table(sid: str, phases: list[dict], n: int, rev: int) -> list[dict]:
    """The numeric table: one row per phase, every field editable.

    THE CANONICAL PATH, not a read-out of the chart. A complete label can be
    produced here without the chart existing at all, which is what makes a
    component failure a degraded session rather than a stopped one. Chart and
    table are two views of ONE list in session state — neither keeps a copy —
    so a drag moves these numbers and a number typed here moves the bar.

    Built from individual widgets rather than st.data_editor for two reasons.
    The editor renders to a canvas, so nothing in it can be read or driven by
    the browser test that now has to prove this works; and its state is a diff
    of user edits rather than the table, which made the round trip with the
    chart awkward in exactly the place it must not be.

    `rev` is bumped whenever the chart changes the list, so the widgets are
    rebuilt: a keyed Streamlit widget keeps its own value and ignores a changed
    `value=` argument, so without it a dragged bar would not move the number.
    """
    head = st.columns(_TABLE_COLS)
    head[0].caption("Phase")
    head[1].caption("Starts at step")
    head[2].caption("± margin")
    head[3].caption("Not sure")

    proposed = []
    for k, ph in enumerate(phases):
        c = st.columns(_TABLE_COLS)
        name = c[0].selectbox(
            f"phase, row {k}", options=list(lc.PHASE_ORDER),
            index=(list(lc.PHASE_ORDER).index(ph["phase"])
                   if ph["phase"] in lc.PHASE_ORDER else 0),
            key=f"labphase-{sid}-{k}-{rev}", label_visibility="collapsed")
        # Row 0 is not a boundary: a partition of [0, n) begins at 0, so there is
        # nothing there to move and nothing to be unsure about.
        start = c[1].number_input(
            f"start_idx, row {k}", min_value=0, max_value=max(0, n - 1),
            value=int(ph["start_idx"]), step=1, disabled=(k == 0),
            key=f"labstart-{sid}-{k}-{rev}", label_visibility="collapsed")
        tol = c[2].number_input(
            f"tolerance_idx, row {k}", min_value=0, max_value=max(1, n - 1),
            value=int(ph["tolerance_idx"]), step=1,
            key=f"labtol-{sid}-{k}-{rev}", label_visibility="collapsed")
        unsure = c[3].checkbox(
            f"unsure, row {k}", value=bool(ph.get("unsure", False)),
            disabled=(k == 0), key=f"labunsure-{sid}-{k}-{rev}",
            label_visibility="collapsed")
        proposed.append({"phase": str(name), "start_idx": int(start),
                         "tolerance_idx": int(tol),
                         "unsure": bool(unsure) and k > 0})
    if proposed:
        proposed[0]["start_idx"] = 0
        proposed[0]["unsure"] = False
    return proposed


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
    legacy = bool(existing) and lc.is_legacy_record(existing)
    if existing and not stale and not legacy:
        seq = " → ".join(f"{p['phase']}@{p['start_idx']}" for p in existing["phases"])
        st.info(f"Already labelled — {seq}. Saving again overwrites it.")
    elif stale:
        st.warning("A label exists for this series but was written against "
                   "DIFFERENT data (series_sha256 mismatch). Treat it as void "
                   "and re-label.")
    elif legacy:
        st.warning("A label exists for this series but predates the current "
                   "format and cannot be upgraded — the per-boundary 'not sure' "
                   "marks it never recorded are not recoverable. Re-label it.")

    # The authoritative phase list lives in session state, not in a widget: the
    # chart has to be able to change it before the table is constructed, and the
    # two must read and write ONE list rather than keeping copies that drift.
    key_ph, key_rev = f"_lab_phases__{sid}", f"_lab_rev__{sid}"
    if key_ph not in st.session_state:
        if existing and not stale and not legacy:
            st.session_state[key_ph] = [dict(p) for p in existing["phases"]]
        else:
            st.session_state[key_ph] = default_phases(n, default_tolerance)
        st.session_state[key_rev] = 0
    phases = st.session_state[key_ph]

    st.caption(
        "**Drag a bar** along the time axis to move that phase boundary — the "
        "shading follows it. **Drag a bar's edge** to widen or narrow its "
        "margin: the bar's own thickness *is* the uncertainty. Click a bar and "
        "use **← →** to nudge it one step (**shift** for five) and **↑ ↓** to "
        "change its margin — on a long series one step is under four pixels, so "
        "the keyboard is the only way to place the last few. **The table below "
        "is the label**: every field is editable and a whole cyclone can be "
        "marked there without touching the chart."
    )

    try:
        edit = _draw(sid, values, phases)
    except Exception as exc:
        # Loudly, and naming the exception. The previous version swallowed this
        # and drew a static picture instead, which is how a component that had
        # NEVER mounted looked like a working screen for three rounds.
        edit = None
        st.error(
            f"**The interactive chart could not be mounted** — "
            f"`{type(exc).__name__}: {exc}`. Nothing is lost: the table below is "
            "the label, and every field in it is editable. Please report this "
            "message — a chart that fails silently is the bug this replaced."
        )

    if is_new_edit(edit, st.session_state.get(f"_lab_lastedit__{sid}")):
        st.session_state[f"_lab_lastedit__{sid}"] = edit_signature(edit)
        if apply_edit(edit, phases, n):
            st.session_state[key_rev] += 1
            st.rerun()

    proposed = _phase_table(sid, phases, n, st.session_state[key_rev])
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

    n_unsure = sum(1 for p in phases[1:] if p.get("unsure"))
    if n_unsure:
        st.caption(
            f"{n_unsure} boundary/boundaries marked **not sure** — those are "
            "kept out of the hit rate and the MAE, and the rest of this series "
            "still counts. That is the point of marking them one at a time: one "
            "unreadable transition no longer voids the boundaries you could read."
        )

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

    r1, r2 = st.columns(2)
    if r1.button("＋ Add a phase", use_container_width=True,
                 disabled=bool(phases) and phases[-1]["start_idx"] >= n - 1,
                 help="Appends one more phase after the last, starting one step "
                      "later. The table decides what it is."):
        last = phases[-1]["start_idx"] if phases else -1
        phases.append({"phase": "residual", "start_idx": min(last + 1, n - 1),
                       "tolerance_idx": int(default_tolerance), "unsure": False})
        st.session_state[key_rev] += 1
        st.rerun()
    if r2.button("－ Remove the last phase", use_container_width=True,
                 disabled=len(phases) <= 1,
                 help="Drops the final phase; the one before it runs to the end."):
        phases.pop()
        st.session_state[key_rev] += 1
        st.rerun()

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("💾 Save & next", type="primary", use_container_width=True,
                 disabled=bool(problem)):
        _save(ambiguous=False)
        st.rerun()
    if b2.button("No incipient phase", use_container_width=True,
                 disabled=not (phases and phases[0]["phase"] == "incipient"
                               and len(phases) > 1),
                 help="Drops the leading incipient phase — this series is "
                      "already changing at step 0. The rest of the sequence is kept."):
        rest = [dict(p) for p in phases[1:]]
        if rest:
            rest[0]["start_idx"] = 0
            rest[0]["unsure"] = False
            st.session_state[key_ph] = rest
            st.session_state[key_rev] += 1
        st.rerun()
    if b3.button("Save as ambiguous", use_container_width=True,
                 disabled=bool(problem),
                 help="You cannot decide this cyclone AT ALL. The phases you "
                      "marked are still saved; the incipient verdict is recorded "
                      "as ambiguous. To set aside ONE boundary and keep the rest "
                      "of the series scoring, tick 'Not sure' on its row instead."):
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
