# Manual labels for the incipient-phase boundary

Tooling, artefact and evaluation for a human-labelled reference of where the
**incipient phase ends** in a cyclone vorticity series.

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

**The tab is blind.** It shows the raw input series and nothing else — no
filtered series, no derivatives, no phases, no shading, no τ, no extrema, no
detector boundary. A label written while the detector's answer is on screen is an
echo of that answer, not evidence about it, and anchoring is automatic rather
than something care avoids. `tests/test_manual_labels.py` parses
`label_tab.py`'s AST and fails if it imports the package or names any detector
output. Synthetic cases appear under an opaque hashed id, because names like
`IcDItMD_noisy` spell the expected sequence.

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
  verdict: {kind: boundary, incipient_end_idx: 7}   # incipient phase is [0, 7)
  tolerance_idx: 3
  notes: clear knee           # optional
```

`verdict.kind` is one of `boundary` (with `incipient_end_idx`), `none` (no
incipient phase), or `ambiguous` (undecidable).

`series_sha256` hashes the raw values only — not the index, not any metadata — so
it answers exactly one question: *is this the data that was looked at?* If a CSV
or the generator changes, the label goes visibly stale instead of silently
pointing at positions in a series that no longer exists.

`tolerance_idx` is the margin accepted **for that label**, always present and
ignored for `kind: none`. Per-label rather than global because the subjectivity
is not uniform: some knees are unmistakable and worth ±1, some ramps are gentle
enough that any of ten indices would be defensible. One global margin would force
the worst case onto every series and hide exactly that difference.

## What is reported, and why separately

* **Hit rate within each label's own margin** — the headline.
* **MAE and worst case, raw**, alongside — a hit rate under a per-label margin
  can be inflated by wide margins and says nothing about the size of the misses.
* **Refusal, both directions** — the detector agreeing there is no incipient
  phase, and the detector refusing where the label says there is a boundary.
  Refusing is a different failure from being off by *k* steps; averaging the two
  would hide both.
* `ambiguous` verdicts are out of the hit rate and the MAE (there is nothing to
  be near) but stay in the refusal accounting.

All of it split by train/test and by real/synthetic.
