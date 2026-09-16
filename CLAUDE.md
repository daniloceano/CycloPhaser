# CLAUDE.md

Working notes for AI agents in this repository. Deliberately short and stable:
durable rules and settled decisions only. The record of individual work fronts —
what was measured, what was decided, what is still open — lives in
`docs/future_work.md`. Read it for context, and update it when a front closes.

## Fixed rules

- **Run the suite only in the dedicated `cyclophaser` conda environment, never
  the base one.** Confirm with `which python` before trusting a result. A plain
  `import cyclophaser` outside that environment can silently resolve to a
  separately installed release of this package instead of the working tree, so a
  run in the wrong environment measures the wrong code without erroring.
- **Never open a pull request.** Merging into a development branch happens only
  with the maintainer's explicit authorization, per front. Pushing a feature
  branch is free.
- **`research/labels/split.yaml` is frozen.** Do not redraw it. A split redrawn
  after results have been seen is not a test set.
- **Do not run the browser tests** (`tests/test_label_browser.py`) and do not
  make claims about their outcome. They drive a real Chromium and are run by
  hand.
- **State suite predictions as passed and failed only** — never the
  skipped/deselected split. See the last section for why.

## Ground truth for the synthetic suite

- `research/labels/manual_labels.yaml` — the maintainer's manual labels — is the
  source of truth for phase **timing**.
  `tests/synthetic/test_synthetic_lifecycles.py` compares each detected boundary
  with the label by position, running on the frozen series in
  `tests/synthetic/data/` and verifying that label's `series_sha256` before
  comparing anything.
- `expected_starts_idx` in `tests/synthetic/cases.py` is **not** ground truth and
  is no longer read by any test. It is still in the file; removing it is a future
  clean-up front.
- `expected_phases` **is** still the ground truth for the phase *sequence* test.
- **`mature` follows the human label**, not the short plateau the segment lists
  were designed around: labelled mature runs 7–16 steps across 13 phases in 11
  cases. The mechanical reason is that the neighbouring sine phases arrive at and
  leave the plateau with **zero derivative**, so the visually flat region is far
  larger than the designed plateau — and that flat region belongs to `mature`
  itself. The label therefore marks `mature` starting *before* and ending *after*
  the designed boundaries.
- Separately, and about the **incipient** phase rather than `mature`: a segment
  opening in `sine` begins flat, which creates a genuine incipient plateau the
  segment lists never designed for. That is why the labels exist at all; see
  `research/labels/README.md`.

## The asserted margin is a fixed 6

The synthetic timing test asserts against the case `tolerance` (6), not against
each label's own `tolerance_idx`. `max(6, tolerance_idx)` was considered and
rejected: it would change nothing today — `tolerance_idx` runs 1–4 on the
synthetic boundaries, so the expression yields 6 at 45 of 45 — and it would mix
the detector's error margin with the labeller's uncertainty, which are two
different quantities.

The demanding, per-boundary metric is the job of
`research/labels/evaluate_against_labels.py`, not of pytest.

## Suite counts depend on the environment

`tests/test_label_browser.py` skips whole at collection through a module-level
`importorskip`. The same commit therefore reports two different shapes under
`-m "not browser"`:

| playwright | reported |
|---|---|
| installed | its 29 tests are collected, then deselected by the marker |
| absent | the module counts as a single skip; its tests are never collected |

`passed` is identical either way. So a gate should predict `passed` and `failed`
and nothing else — a predicted skipped/deselected split reports on the machine
rather than on the code.
