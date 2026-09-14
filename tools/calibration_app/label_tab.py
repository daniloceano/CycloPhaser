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
# container with preserveAspectRatio, so every coordinate is resolution
# independent.
#
# _H is the DESIGN height and the cap, not the rendered one: the component sizes
# itself to the viewport (see `targetPx` in _CHART_JS) so that the curve and the
# table that is being typed into fit on screen together. Scrolling between the
# shape you are judging and the number you are setting is not a cosmetic
# problem — it means you cannot see both at once, which is the whole job.
_W, _H = 1000, 430
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

  // ── how tall the chart should be ───────────────────────────────────────────
  // Sized to the VIEWPORT, not to a constant. The whole point of this view is to
  // look at one series and mark it, and a chart taller than the window makes you
  // scroll between the curve and the table you are typing into — you cannot see
  // the shape you are judging and the number you are setting at the same time.
  //
  // `data.h` is the design height and the cap; RESERVE is what the rest of the
  // page needs (heading, progress, the four-row table, notes, buttons). The
  // result is a target in CSS pixels, converted to viewBox units against the
  // measured container width so that the scale factor — and therefore the
  // rendered size of every label — stays put however tall the box gets.
  // RESERVE is what the rest of the working area needs below the curve: the
  // four-row table, the notes line, the button row and the two captions. It was
  // measured, not guessed — see tests/test_label_browser.py, which fails if the
  // block from the heading to the buttons stops fitting in the viewport.
  const RESERVE = 400, MIN_PX = 230;
  const targetPx = () => Math.max(
    MIN_PX, Math.min(Math.round((window.innerHeight || 900) - RESERVE), data.h));
  const wantH = (width) => {
    // The width MUST be measured from an element that is already laid out.
    // Falling back to data.w pretends the column is 1000px wide, and on a wide
    // screen that silently scales the chart past its own cap — the first
    // version of this did exactly that and drew a 628px chart with a 430px cap.
    const cw = width || parentElement.clientWidth || data.w;
    return Math.max(200, Math.round(data.w * targetPx() / cw));
  };

  // ── reuse before rebuild ───────────────────────────────────────────────────
  // This function runs again on EVERY Streamlit rerender, and a rerender can
  // land in the middle of a gesture (any sidebar widget triggers one). Tearing
  // the SVG down and building a new one would take the listeners and the
  // in-flight drag with it, so the node is kept and its attributes updated
  // whenever the series, the number of phases, the ACTIVE OVERLAY SET and the
  // height are unchanged. Only a genuinely different chart is rebuilt.
  //
  // The overlay set is part of this comparison because toggling a layer
  // changes which <path> elements must exist, which `update()` does not
  // touch (it only repositions bands/bars from step indices) — so a toggle
  // has to fall through to a full rebuild, same as a changed phase count
  // does. `overlayKey` is a plain string so it can be compared with `===`
  // the same way every other field here is.
  const overlayKey = (data.overlays || []).map((o) => o.name).join('|');
  const host0 = parentElement.querySelector('#cp-label-chart');
  const S0 = host0 && host0.__cp;
  const H0 = host0 ? wantH(host0.clientWidth) : 0;
  if (S0 && S0.sid === data.sid && S0.n === data.n &&
      S0.PH.length === data.phases.length && S0.overlayKey === overlayKey &&
      Math.abs(S0.h - H0) < 10) {
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
  // Carry the marks across a pure resize: the geometry is baked in at build
  // time, so a resize is a rebuild, and a rebuild must not be a way to lose
  // work that has not been through a rerun yet.
  const carried = (S0 && S0.sid === data.sid && S0.n === data.n &&
                   S0.PH.length === data.phases.length)
    ? S0.PH.map((p) => ({ ...p })) : null;
  if (S0) S0.teardown();
  if (host0) host0.remove();
  build(H0, carried);

  // Nested, and a declaration rather than a const, so it is hoisted above the
  // call above and still closes over `data`, `setTriggerValue` and
  // `parentElement`. `H` is a parameter because a resize re-enters here with a
  // different one, and every coordinate below is derived from it.
  function build(hintH, carriedPH) {

  const N = data.n;
  const Y = data.y;
  const OVERLAYS = data.overlays || [];
  const COL = data.colors;
  const PH = (carriedPH || data.phases).map((p) => ({ ...p }));
  const W = data.w;
  const ML = data.ml, MR = data.mr, MT = data.mt, MB = data.mb;

  // Attached BEFORE anything is measured, so `clientWidth` is the real column
  // width rather than zero. Everything below is derived from H, so H has to be
  // settled here and not before.
  const host = document.createElement('div');
  host.id = 'cp-label-chart';
  host.dataset.sid = data.sid;
  host.style.scrollMarginTop = '10px';   // air above the boundary tags
  parentElement.appendChild(host);
  const H = wantH(host.clientWidth) || hintH;
  host.dataset.h = String(H);

  const PW = W - ML - MR, PH_ = H - MT - MB;

  // ONE y-domain for every curve on screen — the raw series AND every active
  // overlay. Deliberately NOT per-curve normalised: a flat overlay is
  // information (it means that processing step did little here), and
  // rescaling it to fill the axis would erase exactly that. If an overlay is
  // visually flat against the raw series' range, that is the honest picture.
  let lo = Infinity, hi = -Infinity;
  const _scan = (arr) => {
    for (let i = 0; i < arr.length; i++) {
      if (arr[i] < lo) lo = arr[i];
      if (arr[i] > hi) hi = arr[i];
    }
  };
  _scan(Y);
  OVERLAYS.forEach((o) => _scan(o.values));
  const pad = (hi - lo) * 0.06 || 1;
  const y0 = lo - pad, y1 = hi + pad;

  const step = N > 1 ? PW / (N - 1) : PW;
  const sx = (i) => ML + (N > 1 ? i / (N - 1) : 0.5) * PW;
  const sy = (v) => MT + (1 - (v - y0) / (y1 - y0)) * PH_;
  const ix = (px) => Math.round(((px - ML) / PW) * (N - 1));

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

  // 3. the raw series — drawn FIRST so every overlay sits visually on top
  //    of it, per the labeller's request: raw in the background, processed
  //    layers above. Never removable: it is the one curve the label is
  //    actually written from.
  const curveD = (arr) => {
    let d = '';
    for (let i = 0; i < arr.length; i++) {
      d += (i ? ' L' : 'M') + sx(i).toFixed(2) + ',' + sy(arr[i]).toFixed(2);
    }
    return d;
  };
  svg.appendChild(el('path', {
    d: curveD(Y), fill: 'none', stroke: '#1f2d3d', 'stroke-width': 1.8,
    'stroke-linejoin': 'round' }));

  // 3b. active overlays — SAME x/y mapping (sx/sy) as the raw series above,
  // so a boundary line drawn later crosses all of them at the identical
  // pixel regardless of which curve it is next to (see the boundary bars
  // below: their position comes ONLY from `sx(step index)`, never from any
  // curve's value, so this ordering cannot change what a drag does).
  // Progressively thinner than the raw line so the raw curve — the one the
  // label is actually written from — reads as the visual anchor even with
  // three lines on screen; color is the primary distinguishing channel.
  OVERLAYS.forEach((o, idx) => {
    svg.appendChild(el('path', {
      d: curveD(o.values), fill: 'none', stroke: o.color,
      'stroke-width': Math.max(0.9, 1.6 - idx * 0.3), 'stroke-linejoin': 'round',
      'stroke-opacity': 0.9,
    }));
  });

  // 3c. legend for the active overlays, top-right so it never collides with
  // the phase-band labels or the alert text (both left-anchored, see below).
  if (OVERLAYS.length) {
    const leg = el('g', {});
    svg.appendChild(leg);
    OVERLAYS.forEach((o, idx) => {
      const ly = MT + 14 + idx * 16;
      leg.appendChild(el('line', {
        x1: ML + PW - 130, x2: ML + PW - 106, y1: ly - 4, y2: ly - 4,
        stroke: o.color, 'stroke-width': Math.max(0.9, 1.6 - idx * 0.3) }));
      const lt = el('text', {
        x: ML + PW - 100, y: ly, 'font-size': 11, fill: '#33414f',
        'font-family': 'sans-serif' });
      lt.textContent = o.name;
      leg.appendChild(lt);
    });
  }

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
    x: ML + 8, y: MT + 36, 'font-size': 13, fill: '#c1121f', 'font-weight': '600',
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

  // ── resize ────────────────────────────────────────────────────────────────
  // The axes, the series path and every margin are baked in at build time from
  // H, so there is nothing to nudge: a size change is a rebuild. Debounced,
  // because a drag of the window edge fires this continuously, and skipped
  // while a gesture is in flight so the rebuild cannot happen under the
  // labeller's own pointer.
  let resizeTimer = null;
  const onResize = () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (S.drag) return;
      const h2 = wantH(host.clientWidth);
      if (Math.abs(h2 - H) < 8) return;
      const keep = S.PH.map((p) => ({ ...p }));
      S.teardown();
      host.remove();
      build(h2, keep);
    }, 180);
  };
  window.addEventListener('resize', onResize);

  const S = {
    sid: data.sid, n: N, h: H, PH: PH, overlayKey: overlayKey,
    drag: null, seq: 0, sel: 1,
    setTrigger: setTriggerValue, update: update,
    teardown: () => {
      clearTimeout(resizeTimer);
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);
      window.removeEventListener('resize', onResize);
    },
  };
  host.__cp = S;
  update();

  // Bring the working area to the top of the window when a NEW series arrives.
  // The app's own header, uploader and mode switch sit above this view and
  // cannot be removed — they belong to Grid and Inspector too — so ~680px of
  // chrome stands between the top of the page and the curve. Left alone, every
  // "Save & next" drops the labeller at the top of the page with the series
  // they are supposed to be reading below the fold. Only on a genuinely new
  // chart: doing it on every rerender would yank the page away mid-edit, and a
  // resize rebuild carries `carriedPH`, which is how that case is told apart.
  if (!carriedPH) {
    try {
      host.scrollIntoView({ block: 'start', behavior: 'instant' });
    } catch (_) { /* older browsers: the page simply stays where it was */ }
  }
  }
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


def _draw(sid: str, values: pd.Series, phases: list[dict],
         overlays: list[dict] | None = None) -> dict | None:
    """Mount the chart and return its last message, if any.

    Raises rather than returning None on a mount failure: the caller has to be
    able to tell "the labeller has not touched it yet" from "the chart is not
    there", because those two need opposite things on screen.

    `overlays`, when non-empty, draws those layers in the SAME chart, on the
    SAME y-axis as the raw series (see the chart JS: the y-domain is the union
    of the raw series and every active overlay, never normalised per curve).
    Merged into the wire payload HERE rather than inside `chart_payload`
    itself: that function's return keys are pinned by
    tests/test_manual_labels.py to the raw-series-only contract, and `render`
    only ever passes a non-empty list here from INSPECTION mode (see
    `_overlay_controls`) — LABELLING mode always calls this with `overlays`
    left at its default, so the wire payload it produces is byte-for-byte
    what it always was.
    """
    # height="content": the component decides its own height from the viewport,
    # so a fixed number here would either crop it or reserve space it does not
    # use.
    payload = chart_payload(sid, values, phases)
    payload["overlays"] = overlays or []
    result = _chart_component()(
        data=payload,
        key=chart_key(sid),
        on_edit_change=lambda: None,
        height="content",
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


# phase · start · margin · start-unsure · end-unsure · remove
_TABLE_COLS = [2.0, 1.4, 1.4, 1.2, 1.2, 0.9]


def _compact_layout() -> None:
    """Tighten the vertical rhythm of the main column for this view only.

    Streamlit's default 1rem gap between blocks is right for a page you read and
    wrong for one you work in: across a heading, a progress bar, an expander, the
    chart, four table rows, a notes box and six buttons it adds up to more than
    the chart itself, and pushes the curve off screen. Halving it is what lets
    the series and the table it describes be visible at the same time.

    Scoped to the main area, so the sidebar keeps its normal spacing, and
    written defensively: if the selector stops matching a future Streamlit, the
    layout is merely roomy again — nothing breaks.
    """
    st.markdown(
        """<style>
        [data-testid="stMain"] [data-testid="stVerticalBlock"] { gap: 0.45rem; }
        [data-testid="stMain"] [data-testid="stElementContainer"] { margin: 0; }
        [data-testid="stMain"] .stProgress > div { margin-bottom: 0; }
        </style>""",
        unsafe_allow_html=True,
    )


def _phase_table(sid: str, phases: list[dict], n: int, rev: int,
                 open_unsure: bool, close_unsure: bool
                 ) -> tuple[list[dict], list[int], bool, bool]:
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

    Returns `(proposed_phases, marked_for_removal, open_unsure, close_unsure)`.
    The removal checkbox is a separate return value rather than a field on the
    phase dict: removal is an action on the ROW, not a property of the phase
    it currently holds.

    Two boundary checkboxes per row, not two independent flags
    -------------------------------------------------------------
    A phase sequence of N phases has N+1 EDGES: before phase 0, between every
    pair of adjacent phases, and after phase N-1. Storage still has exactly
    one value per edge — `open_unsure` (edge 0), `phases[k]['unsure']` for
    k=1..N-1 (edge k, the phase that STARTS there), `close_unsure` (edge N) —
    unchanged from schema 4. What changes here is that every row now shows
    BOTH of ITS OWN two edges: row k's "start unsure" is edge k, row k's "end
    unsure" is edge k+1. Row k's "end" and row (k+1)'s "start" are therefore
    two on-screen checkboxes for the identical stored value.

    Because they are two different Streamlit widgets, ticking one does not by
    itself change what the other shows — a keyed widget keeps its own value
    regardless of what `value=` says on the next render (the same fact this
    module already works around for the chart/table split, see `rev` above).
    So this function reads BOTH raw checkbox results for every internal edge
    and reconciles them AFTER the loop: whichever of the two disagrees with
    the edge's OLD stored value is the one that was just clicked, and that
    becomes the new value for the edge — which both checkboxes then render
    from, via a bumped `rev`, on the very next rerun. They cannot be left
    showing different states for more than the one rerun it takes Streamlit
    to redraw both from the single reconciled value.
    """
    head = st.columns(_TABLE_COLS)
    head[0].caption("Phase")
    head[1].caption("Starts at step")
    head[2].caption("± margin")
    head[3].caption("Start unsure")
    head[4].caption("End unsure")
    head[5].caption("Remove")

    n_phases = len(phases)
    proposed, to_remove = [], []
    row_start_unsure, row_end_unsure = [], []
    for k, ph in enumerate(phases):
        c = st.columns(_TABLE_COLS)
        name = c[0].selectbox(
            f"phase, row {k}", options=list(lc.PHASE_ORDER),
            index=(list(lc.PHASE_ORDER).index(ph["phase"])
                   if ph["phase"] in lc.PHASE_ORDER else 0),
            key=f"labphase-{sid}-{k}-{rev}", label_visibility="collapsed")
        # Row 0's start_idx is not a boundary: a partition of [0, n) begins at
        # 0, so there is nothing there to move — but there IS something to be
        # unsure about (edge 0, i.e. `open_unsure`; see the docstring).
        start = c[1].number_input(
            f"start_idx, row {k}", min_value=0, max_value=max(0, n - 1),
            value=int(ph["start_idx"]), step=1, disabled=(k == 0),
            key=f"labstart-{sid}-{k}-{rev}", label_visibility="collapsed")
        tol = c[2].number_input(
            f"tolerance_idx, row {k}", min_value=0, max_value=max(1, n - 1),
            value=int(ph["tolerance_idx"]), step=1,
            key=f"labtol-{sid}-{k}-{rev}", label_visibility="collapsed")
        start_default = open_unsure if k == 0 else bool(ph.get("unsure", False))
        su = c[3].checkbox(
            f"unsure, row {k}", value=start_default,
            key=f"labunsure-{sid}-{k}-{rev}", label_visibility="collapsed")
        end_default = (bool(phases[k + 1].get("unsure", False))
                       if k + 1 < n_phases else close_unsure)
        eu = c[4].checkbox(
            f"end unsure, row {k}", value=end_default,
            key=f"labendunsure-{sid}-{k}-{rev}", label_visibility="collapsed")
        remove = c[5].checkbox(
            f"remove, row {k}", value=False,
            key=f"labremove-{sid}-{k}-{rev}", label_visibility="collapsed")
        row_start_unsure.append(bool(su))
        row_end_unsure.append(bool(eu))
        proposed.append({"phase": str(name), "start_idx": int(start),
                         "tolerance_idx": int(tol), "unsure": False})
        if remove:
            to_remove.append(k)

    new_open = row_start_unsure[0] if n_phases else open_unsure
    new_close = row_end_unsure[-1] if n_phases else close_unsure
    for i in range(1, n_phases):
        old = bool(phases[i].get("unsure", False))
        end_of_prev, start_of_this = row_end_unsure[i - 1], row_start_unsure[i]
        if end_of_prev != old:
            proposed[i]["unsure"] = end_of_prev
        elif start_of_this != old:
            proposed[i]["unsure"] = start_of_this
        else:
            proposed[i]["unsure"] = old
    if proposed:
        proposed[0]["start_idx"] = 0
        proposed[0]["unsure"] = False   # structural: edge 0 is `open_unsure`, not this
    return proposed, to_remove, new_open, new_close


@st.cache_data(show_spinner=False)
def _load_synthetic_names() -> dict[str, str]:
    """{opaque_id: case_name} — for the navigation list in INSPECTION only.

    The opaque id is what the labeller sees while labelling (see
    `lc.opaque_synthetic_id`'s own docstring on why: the case name spells the
    expected phase sequence). Showing the name too is fine ONLY in Inspection,
    which this whole front already treats as a mode where the label is not
    blind — see `_overlay_controls` and `_mode_switch`.
    """
    _series, names = lc.load_synthetic_series()
    return names


@st.cache_data(show_spinner=False)
def _read_split():
    """(split_doc, error). `error` is a message, not an exception: a failure to
    read the split must not crash the tab, but it also must not be silently
    treated as "no test cases exist" — see the fail-closed use in `render`."""
    try:
        return lc.read_split(), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


_STATUS_ICON = {"labeled": "✅", "stale": "⚠️", "unlabeled": "⬜"}


def _case_status(values: pd.Series, rec: dict | None) -> str:
    """One of the three states the navigation list shows per case."""
    if not rec:
        return "unlabeled"
    if lc.is_legacy_record(rec) or rec.get("series_sha256") != lc.series_sha256(values):
        return "stale"
    return "labeled"


def _case_navigation(queue: list[str], records: dict, series: dict,
                     sources: dict, synth_names: dict[str, str],
                     test_ids: set, mode: str, pos: int) -> int:
    """The case picker: a dropdown to jump to ANY of the 63 cases directly,
    with status/split/frozen indicators, plus a filter for "not yet labelled".

    In the MAIN content area, at the very top of the Label tab, deliberately
    — not in the sidebar. A control this central to actually using the tab
    (open a specific case for a second look) has to be the first thing on
    screen, not one more widget mixed in among the Grid/Inspector filter
    controls the sidebar already carries.

    Keyed on `pos` itself (the pattern `_phase_table` already uses via `rev`):
    whenever `pos` changes for ANY reason — this selector, Save & next, Previous/Next —
    the key changes and the widget is rebuilt fresh from the new `pos`, so it
    can never show a stale selection left over from a previous case.
    """
    def _option_text(i: int) -> str:
        sid = queue[i]
        status = _case_status(series[sid], records.get(sid))
        tag = ""
        if sid in test_ids:
            tag += "  [TEST split — locked]"
        if sources[sid] == "synthetic":
            tag += "  [frozen synthetic]"
            if mode == "inspect":
                tag += f"  ({synth_names.get(sid, '?')})"
        return f"{_STATUS_ICON[status]} #{i + 1}/{len(queue)}  {sid}{tag}"

    nav_col, filter_col = st.columns([3, 1.4])
    only_unlabeled = filter_col.checkbox(
        "Show only not-yet-labelled", value=False, key="lab_nav_only_unlabeled")

    options = [i for i, sid in enumerate(queue)
              if not only_unlabeled
              or _case_status(series[sid], records.get(sid)) != "labeled"]
    if not options:
        st.success("Every case is labelled.")
        options = list(range(len(queue)))

    default_i = pos if pos in options else options[0]
    chosen = nav_col.selectbox(
        "Jump to case", options=options, index=options.index(default_i),
        format_func=_option_text, key=f"lab_case_select__{pos}__{only_unlabeled}")
    if chosen != pos:
        st.session_state["lab_pos"] = chosen
        st.rerun()
    return pos


def _mode_switch(sid: str) -> str:
    """INSPECTION / LABELLING toggle, opening always on INSPECTION.

    INSPECTION allows overlays and disables saving; LABELLING allows saving and
    never offers an overlay at all (see `_overlay_controls`). Switching FROM
    inspection TO labelling is the direction that matters — it means this
    case's label, from this point in the session, is no longer blind — so it
    needs an explicit confirmation naming the case, separate from the toggle
    itself. Switching back to Inspection is always free: it only restricts
    what can be saved, it never reveals anything.
    """
    mode = st.session_state.setdefault("_lab_mode", "inspect")
    gen = st.session_state.setdefault("_lab_mode_gen", 0)
    st.sidebar.markdown("### Mode")
    if st.session_state.get("_lab_mode_pending"):
        st.sidebar.warning(
            f"Switching to LABELLING now makes labelling **{sid}** "
            "NOT BLIND from this point in the session onward. Confirm?")
        c1, c2 = st.sidebar.columns(2)
        if c1.button("Confirm", key="lab_mode_confirm", use_container_width=True):
            st.session_state["_lab_mode"] = "label"
            st.session_state["_lab_mode_pending"] = False
            st.rerun()
        if c2.button("Cancel", key="lab_mode_cancel", use_container_width=True):
            st.session_state["_lab_mode_pending"] = False
            st.session_state["_lab_mode_gen"] = gen + 1
            st.rerun()
        return mode
    choice = st.sidebar.radio(
        "Mode", ["Inspection", "Labelling"], index=0 if mode == "inspect" else 1,
        key=f"lab_mode_radio__{gen}")
    wanted = "inspect" if choice == "Inspection" else "label"
    if wanted != mode:
        if wanted == "label":
            st.session_state["_lab_mode_pending"] = True
        else:
            st.session_state["_lab_mode"] = "inspect"
        st.rerun()
    return mode


def _overlay_controls(sid: str, values: pd.Series, mode: str,
                      overlay_provider) -> list[dict]:
    """INSPECTION-only controls for drawing the package's own filtered/smoothed
    series IN THE SAME interactive chart as the raw one (see `_draw`).

    Returns the list of ACTIVE layers, each `{"name", "label", "color",
    "values"}` — everything the chart component needs, and nothing chart_payload
    itself carries (that function's return keys are pinned exactly to the raw
    series by tests/test_manual_labels.py's blindness tests; this list is
    merged in separately by `_draw`, only when non-empty).

    Gated twice over: the master checkbox is OFF by default and its own label
    names no package internals, so neither the overlay computation nor any
    package vocabulary reaches the page until the labeller opts in — and this
    function returns `[]` immediately in LABELLING mode (see `render`), so
    there is no path from here back into what the RAW-ONLY chart draws while
    a label is actually being written.

    Every name/label/color/value that could name a package internal is DATA
    handed back by `overlay_provider` (app.py, which is allowed to import
    cyclophaser) — never a Python identifier in this module, which is what
    keeps this file's own AST free of them (see the module docstring and
    tests/test_manual_labels.py's FORBIDDEN_NAMES check). `values` is only
    ever passed to `overlay_provider`, never filtered here.

    Whatever layer is actually switched on here is recorded into
    `_lab_overlays_seen__{sid}`, which never resets for the rest of the
    session — that accumulator is what `render` reads at save time into the
    schema-4 `overlays_shown` provenance field.
    """
    if mode != "inspect" or overlay_provider is None:
        return []
    seen = st.session_state.setdefault(f"_lab_overlays_seen__{sid}", set())
    show = st.checkbox(
        "Show filtered/smoothed overlays, in the SAME chart (Inspection "
        "only — never offered while Labelling)",
        value=False, key=f"lab_overlay_master__{sid}")
    if not show:
        return []
    try:
        layers = overlay_provider(values) or {}
    except Exception as exc:
        st.error(f"Could not compute overlays — {type(exc).__name__}: {exc}")
        return []
    if not layers:
        st.caption("No overlay available for this series.")
        return []
    active = []
    cols = st.columns(len(layers))
    for col, (name, info) in zip(cols, layers.items()):
        label = info.get("label", name) if isinstance(info, dict) else name
        on = col.checkbox(label, value=False, key=f"lab_overlay__{sid}__{name}")
        if on:
            seen.add(name)
            active.append({
                "name": name, "label": label,
                "color": info.get("color", "#666666"),
                "values": list(info.get("values", [])),
            })
    return active


def render(default_tolerance: int = DEFAULT_TOLERANCE, overlay_provider=None) -> None:
    """Draw the Label mode. Called from app.py's Calibration tab.

    `overlay_provider`, if given, is a `values -> {layer_name: [float, ...]}`
    callable that app.py defines using cyclophaser directly (this module still
    imports nothing from the package — see the module docstring). It is only
    ever invoked from `_overlay_controls`, which only ever runs in INSPECTION
    mode behind its own opt-in checkbox: the raw-series-only chart that the
    label is actually written from (`_draw`, below) never receives it and
    never changes shape depending on it.
    """
    series, sources = _load_population()
    if not series:
        st.error("No series found to label "
                 "(tests/calibration_data/ and tests/synthetic/cases.py are both empty).")
        return

    queue = lc.build_queue(series.keys())
    records = lc.read_labels()
    n_total = len(queue)
    split_doc, split_error = _read_split()
    test_ids = set(split_doc.get("test", [])) if split_doc else set()
    synth_names = _load_synthetic_names()

    # Resume where the last session stopped. Stored in session state after the
    # first computation so Previous/Next can move off it without the next
    # rerun snapping back to the first unlabelled item.
    if "lab_pos" not in st.session_state:
        st.session_state["lab_pos"] = min(lc.queue_position(queue, records), n_total - 1)
    pos = int(st.session_state["lab_pos"]) % n_total

    pos = _case_navigation(queue, records, series, sources, synth_names,
                          test_ids, st.session_state.get("_lab_mode", "inspect"), pos)
    sid = queue[pos]
    mode = _mode_switch(sid)
    values = series[sid]
    n = len(values)
    is_synthetic = sources[sid] == "synthetic"
    is_test_case = sid in test_ids

    if split_error:
        st.error(f"Cannot read {lc.SPLIT_PATH.name} ({split_error}) — ALL saving "
                 "is locked until this is fixed: a case's train/test membership "
                 "cannot be verified, and the test split must never be trained "
                 "on by accident.")

    # The authoritative phase list lives in session state, not in a widget: the
    # chart has to be able to change it before the table is constructed, and the
    # two must read and write ONE list rather than keeping copies that drift.
    key_ph, key_rev = f"_lab_phases__{sid}", f"_lab_rev__{sid}"
    key_open, key_close = f"_lab_open__{sid}", f"_lab_close__{sid}"

    existing = records.get(sid)
    stale = bool(existing) and existing.get("series_sha256") != lc.series_sha256(values)
    legacy = bool(existing) and lc.is_legacy_record(existing)
    usable_existing = existing if (existing and not stale and not legacy) else None
    disk_phases = ([dict(p) for p in usable_existing["phases"]] if usable_existing
                   else default_phases(n, default_tolerance))
    disk_open = bool(usable_existing.get("open_unsure", False)) if usable_existing else False
    disk_close = bool(usable_existing.get("close_unsure", False)) if usable_existing else False

    # Switching case — via the top selector, Save & next, or Previous/Next —
    # must reload from the file, not silently keep showing whatever this session
    # happened to have in memory for the new sid from an earlier, unsaved visit.
    # Session state that disagrees with the file is orphaned state, and it gets
    # named as such rather than displayed as if it were the file's content.
    if st.session_state.get("_lab_last_sid") != sid:
        if key_ph in st.session_state and (
                st.session_state[key_ph] != disk_phases
                or st.session_state.get(key_open, False) != disk_open
                or st.session_state.get(key_close, False) != disk_close):
            st.session_state[f"_lab_conflict__{sid}"] = True
        st.session_state["_lab_last_sid"] = sid

    if st.session_state.get(f"_lab_conflict__{sid}"):
        st.warning(
            f"There is an unsaved edit from earlier in this session for "
            f"**{sid}** that differs from what is currently on file. Choose one:")
        cc1, cc2 = st.columns(2)
        if cc1.button("Discard my edit, reload from file",
                      key=f"lab_conflict_discard__{sid}", use_container_width=True):
            st.session_state[key_ph] = [dict(p) for p in disk_phases]
            st.session_state[key_open] = disk_open
            st.session_state[key_close] = disk_close
            st.session_state[key_rev] = st.session_state.get(key_rev, 0) + 1
            st.session_state[f"_lab_conflict__{sid}"] = False
            st.rerun()
        if cc2.button("Keep my edit, ignore the file",
                      key=f"lab_conflict_keep__{sid}", use_container_width=True):
            st.session_state[f"_lab_conflict__{sid}"] = False
            st.rerun()
        return

    # Everything explanatory is collapsed. It is all still here — it is why the
    # labels are worth anything — but it is read once and then re-read only on
    # purpose, whereas the vertical space it costs is paid on all 63 series. The
    # curve and the table have to be on screen together; the prose does not.
    _compact_layout()
    st.markdown("#### Manual labelling — the **raw input series only**")
    st.caption(
        f"Mode: **{'Inspection' if mode == 'inspect' else 'Labelling'}**"
        + ("  ·  🔒 TEST split — saving locked" if is_test_case else "")
        + ("  ·  ❄️ frozen synthetic — saving needs double confirmation"
           if is_synthetic else "")
    )

    n_done = len(records)
    st.progress(n_done / n_total, text=f"{n_done} of {n_total} labelled "
                                       f"· now showing #{pos + 1} in the queue")

    if existing and not stale and not legacy:
        seq = " → ".join(f"{p['phase']}@{p['start_idx']}" for p in existing["phases"])
        st.info(f"Already labelled — {seq}. Saving again preserves this version "
               "in 'superseded' rather than erasing it — see the overwrite "
               "confirmation near the buttons below.")
    elif stale:
        st.warning("A label exists for this series but was written against "
                   "DIFFERENT data (series_sha256 mismatch). Treat it as void "
                   "and re-label.")
    elif legacy:
        st.warning("A label exists for this series but predates the current "
                   "format and cannot be upgraded — the per-boundary 'not sure' "
                   "marks it never recorded are not recoverable. Re-label it.")

    if key_ph not in st.session_state:
        st.session_state[key_ph] = [dict(p) for p in disk_phases]
        st.session_state[key_rev] = 0
    if key_open not in st.session_state:
        st.session_state[key_open] = disk_open
    if key_close not in st.session_state:
        st.session_state[key_close] = disk_close
    phases = st.session_state[key_ph]

    with st.expander("How to mark a series, and why it is blind", expanded=False):
        st.markdown(
            "You are looking at the **raw input series only**. No filtering, no "
            "derivatives, and nothing the detector produced — that is "
            "deliberate, and it is what makes these labels usable as evidence. "
            "A label written while the algorithm's answer is on screen is an "
            "echo of that answer, not evidence about it. Every bar and band is "
            "drawn from *your* marks; the colours are the project's standard "
            "phase palette only so the figure reads like every other one in the "
            "repo.\n\n"
            "* **Drag a bar** along the time axis to move that phase boundary — "
            "the shading follows it.\n"
            "* **Drag a bar's edge** to widen or narrow its margin: the bar's "
            "own thickness *is* the uncertainty.\n"
            "* **Click a bar, then ← →** to nudge it one step (**shift** for "
            "five), **↑ ↓** for its margin. On a 259-step track one step is "
            "under four pixels, so the keyboard is the only way to place the "
            "last few — and it is the path that still works if the pointer one "
            "does not.\n"
            "* **The table is the label.** Every field is editable and a whole "
            "cyclone can be marked there without touching the chart.\n"
            "* **Start unsure / End unsure** set one EDGE aside from the "
            "scoring — a phase sequence of N phases has N+1 edges (before "
            "the first, between every pair, after the last), and every row "
            "shows both of its own two. A row's 'End unsure' and the next "
            "row's 'Start unsure' are the SAME edge shown twice — ticking "
            "either one ticks both, on the next redraw. The rest of the "
            "series keeps counting regardless of which edges are set aside.\n\n"
            f"Queue order is shuffled with a fixed seed ({lc.QUEUE_SEED}) rather "
            "than sorted by id: the real track ids are chronological, so "
            "labelling them in order would align fatigue with the identifier "
            "and any drift in your criteria would look like a real "
            "time-dependent effect. Labels are written to "
            f"`{lc.LABELS_PATH.relative_to(_REPO_ROOT)}` the moment you press a "
            "button, each save rewriting the file atomically — closing the tab "
            "cannot lose work.\n\n"
            "**Inspection vs. Labelling.** The tab opens in Inspection: you can "
            "browse any case and reveal the package's own filtered/smoothed "
            "overlays, but saving is off. Switching to Labelling turns saving on "
            "and removes the overlays entirely — and switching a given case FROM "
            "Inspection TO Labelling needs a confirmation, because that case's "
            "label is no longer blind from that point on."
        )

    overlay_layers = _overlay_controls(sid, values, mode, overlay_provider)

    try:
        edit = _draw(sid, values, phases, overlays=overlay_layers)
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

    proposed, to_remove, new_open, new_close = _phase_table(
        sid, phases, n, st.session_state[key_rev],
        st.session_state[key_open], st.session_state[key_close])
    if (proposed != phases or new_open != st.session_state[key_open]
            or new_close != st.session_state[key_close]):
        st.session_state[key_ph] = proposed
        st.session_state[key_open] = new_open
        st.session_state[key_close] = new_close
        # Bumped unconditionally, not just for the edge case: a plain
        # start_idx/tolerance edit does not need it (that widget already
        # shows what the user typed), but the paired start/end-unsure
        # checkboxes on TWO DIFFERENT rows do — see _phase_table's docstring.
        # Bumping here too, rather than only on that path, keeps this one
        # rule instead of two.
        st.session_state[key_rev] += 1
        st.rerun()
    open_unsure, close_unsure = st.session_state[key_open], st.session_state[key_close]

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
    # Carries the queue position as well as the boundary. The progress bar above
    # the chart scrolls out of view once the working area is brought to the top
    # of the window, and "which of the 63 am I on" is worth keeping in sight.
    st.caption(
        (f"Incipient phase = steps 0–{inc_end - 1} (ends at {inc_end}, "
         f"{values.index[inc_end]})" if inc_end is not None else
         "No incipient phase — this series is already changing at step 0")
        + f" · series length {n} steps"
        + f" · #{pos + 1} of {n_total} in the queue, {n_done} labelled"
    )

    # Backed by its own session_state entry, not just the widget's key, for
    # the same reason the confirmation checkboxes below are: an earlier
    # widget's rerun (the mode switch, case navigation) can skip this one for
    # a pass and reset it to the `value=` given, which must therefore be
    # "whatever was last typed", not always "whatever is on disk".
    key_notes = f"_lab_notes__{sid}"
    if key_notes not in st.session_state:
        st.session_state[key_notes] = (existing or {}).get("notes", "")
    notes = st.text_input("Notes (optional)",
                          value=st.session_state[key_notes],
                          key=f"lab_notes_widget__{sid}",
                          placeholder="anything that made this one hard to read",
                          label_visibility="collapsed")
    st.session_state[key_notes] = notes

    # ── save gates ────────────────────────────────────────────────────────────
    # Every gate here is a HARD block on the buttons themselves (`disabled=`),
    # not a warning a click can walk past. They stack: a synthetic case that
    # already has a label needs the overwrite checkbox AND both synthetic
    # checkboxes; a TEST-split case cannot be saved no matter what is ticked.
    #
    # Each checkbox's `value=` is read from ITS OWN backing session_state
    # entry, not left to the widget's own key-based memory — because that
    # memory does not reliably survive a rerun that an EARLIER widget in this
    # same script triggers before this point is reached (the mode-switch
    # radio's Confirm/Cancel flow does exactly this: it calls `st.rerun()`
    # from higher up in `render`, which skips these checkboxes for that one
    # pass, and Streamlit does not treat that as "still checked" on the next
    # one). `_phase_table`'s own checkboxes were never vulnerable to this
    # because they already read every `value=` from the phases/open/close
    # backing store rather than from widget memory; these three are the same
    # fix applied to the confirmation checkboxes, which previously trusted
    # widget memory alone and could silently reset to unticked.
    overwrite_needed = bool(existing) and not stale and not legacy
    overwrite_ok = True
    if overwrite_needed:
        key_ow = f"_lab_overwrite_confirm__{sid}"
        overwrite_ok = st.checkbox(
            "Overwrite the existing label for this case (the previous version "
            "is kept under 'superseded', not erased)",
            value=st.session_state.get(key_ow, False),
            key=f"lab_overwrite_confirm_widget__{sid}")
        st.session_state[key_ow] = overwrite_ok

    synthetic_ok = True
    if is_synthetic:
        st.warning("This is one of the 12 FROZEN synthetic cases — saving "
                   "needs two separate confirmations.")
        key_sc1 = f"_lab_synth_confirm1__{sid}"
        key_sc2 = f"_lab_synth_confirm2__{sid}"
        sc1 = st.checkbox("I understand this is a frozen synthetic case",
                          value=st.session_state.get(key_sc1, False),
                          key=f"lab_synth_confirm1_widget__{sid}")
        st.session_state[key_sc1] = sc1
        sc2 = st.checkbox("I still want to save a label for it",
                          value=st.session_state.get(key_sc2, False),
                          key=f"lab_synth_confirm2_widget__{sid}")
        st.session_state[key_sc2] = sc2
        synthetic_ok = sc1 and sc2

    if is_test_case:
        st.error("This case is in the TEST split (research/labels/split.yaml) "
                 "— saving is BLOCKED, not just discouraged.")

    # Named explicitly, not just left as a greyed-out button: a labeller who
    # has ticked every confirmation on screen and still cannot save has no
    # way to tell why unless the ONE remaining reason is spelled out — the
    # mode gate in particular is easy to satisfy every OTHER condition for
    # and still miss, because it lives in the sidebar, away from these
    # checkboxes and buttons.
    blockers = []
    if mode != "label":
        blockers.append("switch to **Labelling** mode in the sidebar — "
                        "saving is off while Inspecting")
    if split_error:
        blockers.append(f"{lc.SPLIT_PATH.name} could not be read; saving is "
                        "locked repo-wide until this is fixed")
    elif is_test_case:
        blockers.append("this case is in the TEST split — saving is blocked, "
                        "not just discouraged")
    if problem:
        blockers.append("fix the phase sequence above first")
    if overwrite_needed and not overwrite_ok:
        blockers.append("tick the overwrite-confirmation checkbox above")
    if is_synthetic and not synthetic_ok:
        blockers.append("tick BOTH frozen-synthetic checkboxes above")

    can_save = not blockers
    if blockers:
        st.caption("Cannot save yet — " + "; ".join(blockers) + ".")

    def _save(ambiguous: bool) -> None:
        rec = lc.make_label_record(
            sid, sources[sid], values, phases, notes=notes or None,
            ambiguous=ambiguous, open_unsure=open_unsure, close_unsure=close_unsure,
            overlays_shown=st.session_state.get(f"_lab_overlays_seen__{sid}"))
        lc.upsert_label(rec)
        st.session_state["lab_pos"] = (pos + 1) % n_total

    # "Remove last" and "No incipient" are gone: both were special cases of
    # the general per-row 'Remove' checkbox + 'Remove selected' button above
    # (tick the last row, or row 0, and remove it — row 0's removal already
    # re-pins the new first phase to start at 0, same as "No incipient" did).
    # "← Back" is gone too, replaced by a Previous/Next pair that ONLY moves
    # through the queue and never saves — the case-navigation dropdown at the
    # top of the tab covers "jump to any case"; these cover "step through the
    # ones next to it", which matters most in INSPECTION mode, where nothing
    # here can save at all.
    r1, r2, b1, b2, p1, p2 = st.columns([1.3, 1.6, 1.3, 1.4, 1.0, 1.0])
    if r1.button("＋ Add a phase", use_container_width=True,
                 disabled=bool(phases) and phases[-1]["start_idx"] >= n - 1,
                 help="Appends one more phase after the last, starting one step "
                      "later. The table decides what it is."):
        last = phases[-1]["start_idx"] if phases else -1
        phases.append({"phase": "residual", "start_idx": min(last + 1, n - 1),
                       "tolerance_idx": int(default_tolerance), "unsure": False})
        st.session_state[key_rev] += 1
        st.rerun()
    if r2.button(f"🗑 Remove selected ({len(to_remove)})", use_container_width=True,
                 disabled=not to_remove or len(to_remove) >= len(phases),
                 help="Removes every phase whose 'Remove' box is ticked, all at "
                      "once. The first remaining phase is re-pinned to start at "
                      "0."):
        remaining = [dict(p) for i, p in enumerate(phases) if i not in to_remove]
        remaining[0]["start_idx"] = 0
        remaining[0]["unsure"] = False
        st.session_state[key_ph] = remaining
        st.session_state[key_rev] += 1
        st.rerun()
    if b1.button("💾 Save & next", type="primary", use_container_width=True,
                 disabled=not can_save):
        _save(ambiguous=False)
        st.rerun()
    if b2.button("Save ambiguous", use_container_width=True,
                 disabled=not can_save,
                 help="You cannot decide this cyclone AT ALL. The phases you "
                      "marked are still saved; the incipient verdict is recorded "
                      "as ambiguous. To set aside ONE boundary and keep the rest "
                      "of the series scoring, tick 'Not sure' on its row instead."):
        _save(ambiguous=True)
        st.rerun()
    if p1.button("◂ Previous", use_container_width=True,
                 help="Move to the previous case in the queue. Never saves."):
        st.session_state["lab_pos"] = (pos - 1) % n_total
        st.rerun()
    if p2.button("Next ▸", use_container_width=True,
                 help="Move to the next case in the queue. Never saves."):
        st.session_state["lab_pos"] = (pos + 1) % n_total
        st.rerun()

