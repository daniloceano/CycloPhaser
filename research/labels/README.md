# Manual labels for cyclone phase sequences

Tooling, artefact and evaluation for a human-labelled reference of a cyclone's
**whole phase sequence** — and, as the question that drove the front, of where
the **incipient phase ends**.

## Why this exists

There is no ground truth for the incipient boundary.

* **The synthetic suite's derived boundary is wrong.** `tests/synthetic/cases.py`
  takes the boundary from the length of a leading `Ic` segment, but the shape of
  the *next* segment decides whether the series actually starts flat.
  `_ramp_sine` is a half-period cosine with zero derivative at both endpoints, so
  an `It` or `D` segment opening in `sine` begins flat and creates a real
  incipient plateau that the segment list never mentions. `IcDItMD_noisy` (D in
  sine) and `DItMD_noisy` (D in linear) have the *same segments*, differ only in
  shape, and have different answers. In four cases `expected_starts_idx` puts the
  incipient phase and the phase after it both at index 0 — not a boundary at all.
* **The 51 real tracks carry no label of any kind.**

So the reference has to be built by hand, and this directory is the plumbing
around that. `tests/synthetic/cases.py` is deliberately **not** modified here:
replacing the derived synthetic ground truth is a separate step, and it should
happen after the labels exist, not before.

## Contents

| File | What it is |
|---|---|
| `labels_core.py` | Every pure helper — split, queue, YAML read/write, series hashing, metrics. No Streamlit, so all of it is testable without a browser. |
| `make_split.py` | Draws the frozen train/test split. Writes `split.yaml`. |
| `split.yaml` | **Committed artefact.** The frozen split. |
| `manual_labels.yaml` | **Committed artefact — the deliverable.** Written incrementally by the app. |
| `evaluate_against_labels.py` | Runs the detector, scores it against the labels. |

The labelling UI itself is `tools/calibration_app/label_tab.py`, reached through
the **Label** display mode of the calibration app. Tests are in
`tests/test_manual_labels.py`.

## Workflow

**1 — the split (already done; do not redraw).**

```bash
python research/labels/make_split.py
```

Stratified by series length into three bands (n<60: 10 tracks · 60≤n<120: 22 ·
n≥120: 19), 70/30, seed `20260905` recorded in the output. The bands are not
interchangeable — a 30-step track gives the detector far less to work with than a
259-step one — and an unstratified draw over 51 items can leave a band nearly
empty in the test set. The 12 synthetic cases are not drawn: they all go to
train, tagged `source: synthetic`, because they are a designed population rather
than a sample of anything.

The script **refuses to overwrite an existing `split.yaml`** without `--force`.
That refusal is the point: a split redrawn after results have been seen is not a
test set. Result — **train 47** (35 real + 12 synthetic), **test 16**.

**2 — labelling (pending).**

```bash
streamlit run tools/calibration_app/app.py    # then: Display mode → "Label"
```

63 series in a queue whose order is shuffled with a fixed seed, because the real
track ids are chronological: labelling in id order would align the labeller's
fatigue with the identifier, and any drift in criteria would then look like a
real time-dependent effect. Progress is persisted, so the queue resumes where it
stopped.

Each cyclone is labelled **completely** — every phase, in order — before the
queue moves on, so a track is judged as a whole life cycle rather than as one
boundary in isolation.

**The tab is blind.** It shows the raw input series and nothing else — no
filtered series, no derivatives, no τ, no extrema, no detector boundary. Phases
are shaded in the project's standard palette (blue incipient, amber
intensification, red mature, olive decay, grey residual) so a labelled series
reads like every other phase figure in the repo — but every band, line and arrow
is painting **your** marks, never the algorithm's. A label written while the
detector's answer is on screen is an echo of that answer, not evidence about it,
and anchoring is automatic rather than something care avoids.
`tests/test_manual_labels.py` parses `label_tab.py`'s AST and fails if it imports
the package or names any detector output. Synthetic cases appear under an opaque
hashed id, because names like `IcDItMD_noisy` spell the expected sequence.

**Dragging.** Boundary lines and the ends of the tolerance arrows can be dragged
directly on the chart. `st.plotly_chart` cannot deliver this on its own — its own
docs say *"Only selection events are supported at this time"*, and a dragged
shape arrives as `plotly_relayout`, which it does not forward — so a small
`st.components.v2` bridge attaches to the chart Streamlit already rendered and
forwards just those keys. It draws nothing and reads nothing. If it fails to bind,
or the Streamlit version has no `components.v2`, dragging simply does nothing and
the click and the table are untouched: **labelling is never blocked on it.**
Only movement along the **time axis** counts: a label is an index, so vertical
position means nothing. It cannot be locked at the source — Plotly has no axis
constraint for draggable shapes or annotations, and Streamlit does not expose
`window.Plotly`, so the browser cannot be told to snap it back either. Instead a
vertical drag is forwarded as a redraw signal and the chart is re-rendered from
Python, which puts the line back. The chart's Streamlit key carries a revision
counter for the same reason: re-sending the same figure under the same key would
not fix it, because the frontend diffs against the previous *spec*, not against a
div the user has since dragged. The remount is also what makes a horizontal drag
settle honestly — Plotly leaves the shape where the mouse released it (63.7)
while the label is the rounded index (64).

Everything downstream of the payload is pure Python (`apply_drag`, `drag_map`,
`has_vertical_move`, `is_new_drag`) and tested; whether a given browser emits
those keys on a drag is the one part that has to be confirmed by trying it.

Each boundary's margin is drawn as a shaded band and a **double-headed arrow**
spanning `[start-tol, start+tol]`. The margin is the part of a label that is
easiest to set carelessly: a number in a table gives no sense of how much of the
curve it forgives, and seeing the arrow cover half a ramp is what prompts a
smaller one.

Each save rewrites `manual_labels.yaml` atomically (tmp + `os.replace`), so
closing the tab cannot lose work.

**3 — evaluation.**

```bash
python research/labels/evaluate_against_labels.py --config params.yaml
```

Train only by default; `--test` is explicit and prints a warning, because a test
set is spent the first time a parameter is chosen after looking at it.

## The label format

```yaml
- id: '20150069'
  source: real                # real | synthetic
  series_sha256: 4f3a…        # hash of the RAW values as labelled
  labeled_at: '2026-09-06T00:00:00+00:00'
  n_steps: 133
  phases:                     # an ordered partition of [0, n_steps)
    - {phase: incipient,       start_idx: 0,   tolerance_idx: 0}
    - {phase: intensification, start_idx: 7,   tolerance_idx: 3}
    - {phase: mature,          start_idx: 40,  tolerance_idx: 5}
    - {phase: decay,           start_idx: 60,  tolerance_idx: 4}
  verdict: {kind: boundary, incipient_end_idx: 7}   # DERIVED; incipient is [0, 7)
  tolerance_idx: 3                                  # DERIVED
  notes: clear knee           # optional
```

Phase *i* runs from its own `start_idx` up to the next one's; the last runs to
the end. The first always starts at 0. Repeats are allowed — `residual →
intensification → mature → decay` is a real life cycle — and a phase's **position**
in the list carries the repetition, so the name is never numbered.

`verdict` and the top-level `tolerance_idx` are **derived** from `phases` rather
than asked a second time, so the table and the verdict cannot contradict each
other about the very thing this front exists to settle. `verdict.kind` is
`boundary` (with `incipient_end_idx`), `none` (the sequence does not start with
an incipient phase), or `ambiguous` — the one judgement the table cannot express,
set by the labeller, and recorded alongside the phases rather than instead of
them.

`series_sha256` hashes the raw values only — not the index, not any metadata — so
it answers exactly one question: *is this the data that was looked at?* If a CSV
or the generator changes, the label goes visibly stale instead of silently
pointing at positions in a series that no longer exists.

`tolerance_idx` is the margin accepted **for that boundary**. Per boundary rather
than per series or global, because the subjectivity is not uniform even within
one cyclone: an incipient knee can be unmistakable on a track whose mature→decay
transition is a long gentle roll. One global margin would force the worst case
onto every boundary and hide exactly that difference. The first phase's margin is
unused (its start is 0 by construction).

## What is reported, and why separately

Two blocks, side by side.

**The incipient boundary** — the question the front was commissioned to settle:

* **Hit rate within each label's own margin** — the headline.
* **MAE and worst case, raw**, alongside — a hit rate under a per-boundary
  margin can be inflated by wide margins and says nothing about the size of the
  misses.
* **Refusal, both directions** — the detector agreeing there is no incipient
  phase, and the detector refusing where the label says there is a boundary.
  Refusing is a different failure from being off by *k* steps; averaging the two
  would hide both.
* `ambiguous` verdicts are out of the hit rate and the MAE (there is nothing to
  be near) but stay in the refusal accounting.

**The whole sequence:**

* **Sequence mismatch** — the detector found different phases, or in a different
  order — is counted and set aside, never measured. Pairing the 3rd labelled
  boundary with the 3rd detected one across a mismatch compares two different
  transitions and manufactures a number.
* **Boundary error**, only where the sequences agree, broken out **per phase**,
  each against its own margin. The first phase's start is excluded: it is 0 on
  both sides by construction and would pad every rate with free agreement.

All of it split by train/test and by real/synthetic.
