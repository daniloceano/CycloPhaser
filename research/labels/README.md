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

**That step has since happened** (`docs/future_work.md` item 17).
`tests/synthetic/test_synthetic_lifecycles.py` now scores phase timing against
`manual_labels.yaml`, and `expected_starts_idx` is read by no test at all — it
is still present in `cases.py`, awaiting its own clean-up front.
`expected_phases` still holds, as the ground truth for the phase *sequence*
test. The decision extends beyond the incipient boundary: for the synthetic set
the manual label is the source of truth for every phase, `mature` included.

## Contents

| File | What it is |
|---|---|
| `labels_core.py` | Every pure helper — split, queue, YAML read/write, series hashing, metrics. No Streamlit, so all of it is testable without a browser. |
| `make_split.py` | Draws the frozen train/test split. Writes `split.yaml`. |
| `split.yaml` | **Committed artefact.** The frozen split. |
| `manual_labels.yaml` | **Committed artefact — the deliverable.** Written incrementally by the app. |
| `evaluate_against_labels.py` | Runs the detector, scores it against the labels. |
| `config_defaults.py`, `defaults_2.0.0.json` | Fills keys a config does not carry with the frozen pre-item-31 defaults (the file name says 2.0.0; see below), and lists them (item 31, decision (a)). |

The labelling UI itself is `tools/calibration_app/label_tab.py`, reached through
the **Developer → Manual labelling** page of the calibration app (only with the
developer key, `CYCLOPHASER_APP_DEV=1`; see `tools/calibration_app/README.md`). Tests are in
`tests/test_manual_labels.py`.

## Calibration configurations

**Since item 31 (2026-09-28), `research/labels/configs/` holds one file:
`cyclophaser_params-track.yaml`, the calibration preset.**

> **Correspondence (2026-09-28).** params-15 foi renomeado para params-track
> (conteúdo idêntico, sha256 `5aa61f2dec710029b46a47668812d14e6d552517b7bca8912a8e00fd130ccf04`); registros anteriores citam o nome antigo.

**params-track = the package defaults except `boundary_padding: edge`** (the
package default is `"reflect"`). Two further differences are of form only:
the file carries `use_filter: true`, which the package treats as `'auto'` (with a
`UserWarning`), and carries no `prominence` key, whose default is `None`
(`research/cleanup/passo1/params_track_vs_defaults.json`, generated). It is
the **only configuration with measured scores**, and every score was measured
under `edge`: those scores belong to params-track, not to the package defaults.
Anyone working with TRACK series who wants the measured behaviour must pass
params-track explicitly.

params-1 to
params-14 were removed by Danilo's decision. They are not lost: each one is
recoverable byte for byte with the command in
`diagnostics/item31/recovery_table.md` (`git show 33ea489358d9:<path>`), and the
records of earlier fronts still cite them by name and hash. **Always identify a
config by its hash, never by its file name**: an app export called
`cyclophaser_params-11.yaml` once held params-14's values
(`swell_item30/README.md`, "Name trap").

| File | sha256 | |
|---|---|---|
| `cyclophaser_params-1.yaml` … `-8.yaml` | see `diagnostics/item31/recovery_table.md` | removed (item 31); historical, added to the repo by front 21 |
| `cyclophaser_params-9.yaml` | `0c3ec55910c45a6dcf9a1787ceca3f3c6796cf25da953be642befa29eaac9f63` | removed (item 31); historical |
| `cyclophaser_params-10.yaml` | `c14755e3ac1c2dcb2da8e652e7eba61ce20b8c45235b18cd7183abac047902d7` | removed (item 31); was `item19_core.CONFIG`, the frozen instrument of items 19/20 |
| `cyclophaser_params-11.yaml` | `24dd7f22b76d98cf0cab0b18ff040e010209604a8485007551095e9622abe420` | removed (item 31); calibration reference from front 20(a) to 2026-09-27 |
| `cyclophaser_params-12.yaml` | `39262f45785eea00d19e4165d6f52b6a77cabfcf56e14514a0cea2e3c67ebec3` | removed (item 31); params-11 + `mature_min_depth` 0.80 (item 22) |
| `cyclophaser_params-13.yaml` | `c1ab8ce02631f1270b3a633cff2ef43fb5caff64dd492642f56cf5a96e483973` | removed (item 31); params-12 + `intensification_min_depth` 0.05 (item 24) |
| `cyclophaser_params-14.yaml` | `acf4985339e8849603711012b2049d8913997e329a3c56d5399f6700e2d1159e` | removed (item 31); params-13 + `reclassify_index0` true (item 28) |
| **`cyclophaser_params-track.yaml`** (was `cyclophaser_params-15.yaml`) | `5aa61f2dec710029b46a47668812d14e6d552517b7bca8912a8e00fd130ccf04` | **the calibration preset** — params-14 + `incipient_plateau_spare_intensification` true (item 30); **adotado sem validação independente** (2026-09-27) |

**Do not normalise or reformat params-track.** Its identity is its file hash: the
Benchmark shows that hash as a column's provenance, and every later record
cites it. It was written by hand from params-14 (plus one line), so its
`metadata` block is params-14's, timestamp included.

**Incomplete configs** (item 31, decision (a)). A key a config does not carry is
filled with its **pre-item-31 default** from the frozen table
`defaults_2.0.0.json` (generated from item 31's parameter table, never edited by
hand; helper `config_defaults.py`), and the filled keys are always listed —
by `evaluate_against_labels.py` (stderr), by the Benchmark column's provenance
(item 4) and by the app's YAML import (a warning). A key present is never
changed. This keeps an old or hand-trimmed config meaning what it meant when it
was written, whatever the package defaults become.

**What "2.0.0" means in these file names.** `defaults_2.0.0.json`,
`tests/legacy_defaults.py` and `tests/baselines/*_2_0_0.csv` hold the defaults of
the development line **before item 31**, not those of the published 2.0.0
release: the release has no `boundary_padding` (its Lanczos convolution always
zero-pads) and uses `replace_endpoints_with_lowpass=24`, and it has none of the
later phase parameters. The names are historical; `CHANGELOG.md`
([Unreleased], "The pre-item-31 table is not 2.0.0") lists the differences.

**The published 2.0.0 itself** is in `research/snapshots/v2.0.0.json`: the phase
detections produced by running the 2.0.0 wheel from PyPI with its package
defaults over 63 series (51 real + 12 synthetic). Its recorded public
signature matches the `v2.0.0` tag parameter for parameter (`determine_periods` 19, `process_vorticity` 7, `get_periods` 10 defaults;
0 differ), and its sha256 is listed in `research/snapshots/SHA256SUMS`
(checked by `research/cleanup/passo4/snapshot_vs_tag.py`).

**`item19_core.py` no longer has a default config.** `pair_by_overlap` and
`MARGIN`, which the Benchmark imports, are unchanged. `load_config()` without a
path raises and names the recovery commit. The item 19/20 scripts, and every
other closed-front script that loads a removed config, are listed in
`archive/research-diagnostics-pre-cleanup:research/labels/diagnostics/item31/stale_scripts.md` and reproduce from `33ea489358d9`.

Two instruments score matures and they are **not** interchangeable:
`evaluate_against_labels.py` / `score_phase_sequences` scores only series whose
whole phase sequence matches, compares phase **starts**, and uses each label's
own `tolerance_idx`; `item19_core.pair_by_overlap` scores **all** series,
compares **both ends**, and uses a fixed margin of 6. Which one governs which
quantity is open debt — see item 20(a) in `docs/future_work.md`.

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

**2 — labelling (done: all 63 series are labelled).**

```bash
CYCLOPHASER_APP_DEV=1 streamlit run tools/calibration_app/app.py    # then: Developer → Manual labelling
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

**The chart is hand-drawn SVG**, not a Plotly figure, and the reason is the
interaction. This view needs a bar that slides along time and drags its phase
shading with it. Plotly can make a shape draggable but only in two dimensions —
there is no axis constraint for shapes or annotations anywhere in its schema — so
a boundary could be pulled off the time axis, where it means nothing, taking the
shading with it. That could not be corrected in the browser either, because
Streamlit's bundle does not expose `window.Plotly`.

Drawn by hand in a `st.components.v2` surface, the problem disappears instead of
being repaired: the drag handler reads `clientX` and nothing else, so a bar
cannot leave the time axis — not because it is pushed back, but because nothing
ever moves it there.

- **The table is the label.** Every field is editable, and a whole cyclone can be
  marked without touching the chart. This is the canonical path; the chart is a
  convenience on top of it. Chart and table are two views of one list in session
  state, so a drag moves the numbers and a typed number moves the bar.
- **Drag a bar** to move that boundary. The phase bands are recomputed from the
  bar positions on every frame, so the shading follows for free.
- **Drag a bar's edge** to widen or narrow its margin. The bar's own **thickness
  is the uncertainty**, so the margin travels with the boundary by construction
  instead of being a second object that has to be kept in sync.
- **Click a bar and use the arrow keys**: ← → move the boundary one step (shift,
  five), ↑ ↓ change its margin. On a 259-step track one index is under four
  pixels, so the keyboard is the only way to place the last few — and it is the
  path that still works when the pointer path does not.
- **A chart that cannot mount says so, in red, naming the exception.** There is
  no static fallback any more. There was one, and it is the reason this took four
  rounds: `key=f"lab_chart__{sid}"` contained `__`, which Streamlit reserves
  inside a bidirectional component's id, so the mount raised on *every* render
  from the day it was written. `except Exception` caught it and drew a plausible
  non-interactive picture, so a total failure of the component looked like a
  working screen. A drawing nobody can use is worse than an error message.

### Verified in a browser, not in a stub

`tests/test_label_browser.py` starts `streamlit run tools/calibration_app/app.py`
on a free port, drives Chromium at it with **real pointer events**, and reads
every assertion back from the values that reached **Python** — the phase table —
never from a pixel. It covers the four gestures that were broken or unprovable:
dragging a bar there and back, dragging a tolerance handle wider and narrower,
releasing the pointer *outside* the chart mid-drag, and dragging *through* a
Streamlit rerender. Plus the keyboard, and the table→chart direction.

It replaces `tests/js/`, which ran the component's JS against a hand-written DOM
stub under Node. That spec passed while the feature worked in nobody's browser,
three times, because the fault was in the Python that mounts the component and
the stub never executed a mount. Keeping both would have duplicated the
maintenance and preserved the false confidence.

    pip install playwright && python -m playwright install chromium
    pytest tests/test_label_browser.py

Both are test-only; every test skips when they are absent, and neither reaches
the package's requirements or its CI.

Everything downstream of the drag is pure Python (`chart_payload`, `apply_edit`,
`is_new_edit`) and tested. `chart_payload` is the only channel from the app to
the drawing surface, and its keys are pinned by a test: the raw values, the
labeller's own marks, and the palette. Nothing else can reach the screen.


Each save rewrites `manual_labels.yaml` atomically (tmp + `os.replace`), so
closing the tab cannot lose work.

**2b — the item-30 swell batch (drawn, not yet labelled).** Ten swell tracks
were drawn by a seeded rule (seed `20260925`) into a separate, frozen block,
`batches: swell_item30`, appended to `split.yaml` (7 train, 3 test). The 47/16
split above it is unchanged. Their series are in
`tests/calibration_data/swell_item30/`, deliberately **below** the 51 so that no
existing reader sees them. The Label tab queues them after the 63. See
`swell_item30/README.md` for the rule, the provenance and why these labels are
not blind.

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
    - {phase: incipient,       start_idx: 0,   tolerance_idx: 0, unsure: false}
    - {phase: intensification, start_idx: 7,   tolerance_idx: 3, unsure: false}
    - {phase: mature,          start_idx: 40,  tolerance_idx: 5, unsure: false}
    - {phase: decay,           start_idx: 60,  tolerance_idx: 4, unsure: true}
  verdict: {kind: boundary, incipient_end_idx: 7}   # DERIVED; incipient is [0, 7)
  tolerance_idx: 3                                  # DERIVED
  notes: clear knee           # optional
  open_unsure: false          # schema 4 — uncertainty before phase 0
  close_unsure: false         # schema 4 — uncertainty after the last phase
  overlays_shown: []          # schema 4 — empty or absent means blind
  superseded: [...]           # schema 4 — prior versions, oldest first
```

The document carries `schema: 4`. Records written against schema **1 or 2** are
**refused**, not upgraded, and named so the series goes back in the queue: a
schema-1 record never stored the phase sequence, and a schema-2 record never
stored `unsure`. Defaulting a missing `unsure` to `false` would put a claim in
the labeller's mouth — *they were confident* — and that claim is exactly what
decides whether a boundary counts against the detector. Those two bumps were
free because `manual_labels.yaml` was still empty each time; refusal is detected
structurally, per record, rather than from the document's version number,
because a working copy can hold a mix.

The 3 → 4 bump cost no re-labelling, which is why it could happen with the queue
already labelled. None of its three additions — `open_unsure`/`close_unsure`,
`overlays_shown`, `superseded` — touches `phases`, `verdict` or `tolerance_idx`,
so a schema-3 record still derives the identical verdict and stays valid. A
schema-3 file is read and left exactly as it is; none of the three fields is
invented on a record that was not itself re-saved. `open_unsure` and
`close_unsure` carry uncertainty on the two edges a phase sequence cannot
express (before phase 0, which is pinned at `start_idx` 0, and after the last
phase, which has no boundary to flag); `overlays_shown` records which
smoothed/filtered overlays were on screen before the save, so a non-blind label
says so; `superseded` preserves the record a re-label replaced instead of
erasing it.

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

`unsure` says *I cannot place this boundary* — and it is per boundary for the
same reason the margin is. Ambiguity used to be a property of the whole series,
so being unable to read one long mature→decay roll discarded the incipient knee
four phases away from it: throwing away the evidence you have in order to
register the one you lack. Marked here, that boundary drops out of the hit rate
and the MAE while the rest of the series keeps scoring, and the count of
exclusions is printed — a phase that is routinely unreadable is a finding about
the phase, not noise. The whole-series `ambiguous` verdict still exists as a
shortcut for a cyclone you cannot read at all. The first phase's flag is always
false: its start is 0 by construction, so there is no boundary there to doubt.

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
  be near) but stay in the refusal accounting. An `unsure` incipient boundary
  arrives here as `ambiguous`, so the two spellings of the same judgement cannot
  disagree.

**The whole sequence:**

* **Sequence mismatch** — the detector found different phases, or in a different
  order — is counted and set aside, never measured. Pairing the 3rd labelled
  boundary with the 3rd detected one across a mismatch compares two different
  transitions and manufactures a number.
* **Boundary error**, only where the sequences agree, broken out **per phase**,
  each against its own margin. The first phase's start is excluded: it is 0 on
  both sides by construction and would pad every rate with free agreement.
* Boundaries marked `unsure` are excluded in **both** directions and counted
  separately — including when the detector happens to land on one, since
  counting that agreement would inflate the rate with a coin flip.

All of it split by train/test and by real/synthetic.
