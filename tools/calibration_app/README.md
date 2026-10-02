# CycloPhaser — Calibration App

An interactive tool to calibrate CycloPhaser's filtering, smoothing and
phase-detection parameters on real and synthetic tracks, and to compare
configurations side by side.

## Installation

Run from the `tools/calibration_app/` directory:

```bash
cd tools/calibration_app
pip install -r requirements-app.txt
```

The `-e ../..` line in `requirements-app.txt` installs CycloPhaser in editable
mode from the repository root.

## Running

```bash
streamlit run app.py
```

Open http://localhost:8501 in a browser.

## Track format

Both upload fields (Calibration and Benchmark → Exploration) accept `.csv` and
`.txt`. The format is recognised by **content**, never by extension
(`track_io.py`, the app's only reader).

**Standard format** — a first line with column names separated by `;`,
including:

- `time` — **year-first** dates (`YYYY-MM-DD…`, e.g. `2015-01-27 04:00:00` or
  `2008-08-15-2100`);
- `min_max_zeta_850` — 850 hPa relative vorticity (s⁻¹), Southern-Hemisphere
  convention (cyclonic = negative).

Other columns are ignored. Compatible with `example_file.csv` in
`cyclophaser/example_data/`.

**Custom format** (opt-in, *Custom track format* expander, off by default) —
separator (`auto`, `;`, `,`, tab, whitespace), header line yes/no, date and
vorticity columns (by name, or by 1-based number without a header) and an
optional strftime date format. Dates that do not start with the year need the
explicit format: pandas' inference reads `05/01/2015` as 1 May without warning.
Each file read this way is shown in a preview (first rows, first/last date,
number of points, min/max vorticity, sign and magnitude warnings) and is used
only after it is confirmed. The file is normalised to the standard format; the
rest of the app does not change.

**Validation, on every path** — dates parsed, strictly increasing and without
duplicates; numeric float64 vorticity without NaN; at least 2 points. A file
that fails is refused with the cause, never accepted silently.

## Display modes

The top of the **Calibration** tab has a mode selector: Grid, Inspector and
Label. Grid and Inspector are **pure visualisation**: none of their controls
changes the detection, and none of their state enters the exported YAML. Label
is the manual-labelling tool; see `research/labels/README.md`.

### Grid (default)

The multi-cyclone grid: matplotlib figures rendered to PNG and cached, 1–6
columns, and the same PNG inside the export ZIP. Rendering 51 Plotly figures on
one page freezes the browser, and the exported PNG must stay deterministic —
which is why this mode stays in matplotlib.

### Inspector (one track at a time)

A Plotly figure of stacked panels (`z` / `dz` / `dz2`, shared x axis and
synchronised zoom) for **one** track chosen in the *Track to inspect* select
box. The renderer is the point of the mode: clicking the legend turns a layer
on and off **in the browser**, without a Streamlit rerun.

**The inspector opens with everything on.** Every series layer is visible and
the four decision overlays are checked — the work is per *track* (one selected
cyclone), not for the whole grid, so computing all four is cheap. Unchecking one
removes its cost.

There are two kinds of control, and the difference is deliberate:

- **Series layers** — `zeta`, `filtered_vorticity`, `vorticity_smoothed`,
  `vorticity_smoothed2`, `dz_dt_filt`, `dz_dt_smoothed2`, `dz_dt2_filt`,
  `dz_dt2_smoothed2`, the three `*_peaks_valleys`, and the ground-truth `Ic`
  boundary of the synthetic cases. They are **always** in the figure: hiding one
  is a legend click (it becomes `legendonly` and stays in the figure), at no
  cost. Phase shading is the one exception — a full-height band is a layout
  *shape*, which Plotly does not put in the legend — and it is **always on**: it
  is the background every other layer is read against.

  Colours follow the package's own convention (`cyclophaser/plots.py`,
  `plot_didactic`): raw ζ in grey, `filtered_vorticity` in amber,
  `vorticity_smoothed` in navy and `vorticity_smoothed2` in red. In the
  derivative panels the per-*quantity* colour of the same file applies
  (`series_colors`: dz red, dz2 amber), with the intermediate `*_filt` stage in
  a light tone and the stage the detection reads in full colour and a thicker
  line.
- **Decision overlays** — they need server-side computation, so they are
  `st.checkbox` controls:
  - **Pipeline ribbon** — six bands, one per step, coloured by the phases in
    force *after* that step. The six functions run in a fixed order and
    overwrite one another; reading a column from top to bottom shows a stretch
    changing owner.
  - **Candidate ledger** — every segment `find_intensification_period` and
    `find_decay_period` consider, with the scale used, the required minimum, the
    verdict under the current sliders, the gaps and the fill-in test, and
    (crossed with the ribbon) whether an accepted candidate was overwritten by a
    later step.
  - **Mature layers** — accepted and rejected `z` peaks/valleys under the
    effective prominence threshold, and the mature windows, **including those
    the strict confirmation discarded** — which otherwise vanish without a trace
    in the result.
  - **Incipient layers** — the smoothed probe, the profile `rel = |dz|/max|dz|`
    against τ, the `|dz2|` knee, and the incipient boundary the run produced
    (read from `df['periods']`, not recomputed). Outside
    `incipient_method="plateau"` the rel/τ/probe layers do not exist and are
    omitted with a notice; raw `dz` and `dz2` remain.

**Shared scale (`Shared y scale`, on by default).** The curves are rescaled to a
**0–1** band, in the **same groups** the Grid figure puts on its two axes
(`plots.plot_all_periods` uses `twinx`: raw `zeta` on one axis,
`filtered_vorticity` + `vorticity_smoothed` + `vorticity_smoothed2` together on
the other). The derivative panels follow the same rule: `*_filt` and
`*_smoothed2` share a band.

Both halves of the grouping matter:

- giving **raw its own band** is what lets it **overlay** the filtered series
  instead of crushing it — it has 2–3× more amplitude, and on a common scale it
  would flatten the others against the axis;
- keeping **the pipeline stages together** is what preserves the amplitude each
  smoothing pass removed. Scaling each stage on its own makes every stage fill
  the whole height and all of them look identical — measured on 20190325 with
  the package defaults of the time, `filtered_vorticity` has 1.25× the amplitude
  of `vorticity_smoothed2`, and per-series scaling erased that.

The panel is then read by **shape** — where each series turns, and when —,
which is the only thing the phase rules act on. Magnitude leaves the axis, but
**every hover still shows the raw value**. Side effect: zero sits at a different
height in each band, so the zero line of the dz/dz2 panels is not drawn in this
mode. Uncheck it to read true units and a real zero.

(A real `twinx` stays out of the inspector: it caused the zorder bug in the
grid's compact figure. What is reproduced here is the *grouping* the package's
`twinx` produces, on a single axis.)

**Fidelity.** All computation lives in pure functions (`layer_inspector.py`,
no Streamlit and no plotting library) that only *call* the package's own
functions — the ribbon runs the six functions in sequence on a copy of the
frame, and the ledger is compared, in a test, with the mask the package function
produces on its own (`tests/test_layer_inspector.py`). The same helpers feed the
app's Plotly renderer and the static matplotlib check render in
`research/app_layer_inspector/gen_inspector_figures.py`.

## Benchmark tab

Compares N configurations side by side, over the cyclones you choose, aligned by
cyclone. A column is created from the current sidebar state, an uploaded YAML, a
file in `research/labels/configs/` (since item 31 only params-15, renamed params-track in the cleanup front; params-1..14
are recoverable, see `research/labels/diagnostics/item31/recovery_table.md`) or a frozen published-version
snapshot, and stays editable in the tab itself.

**Each column's header** — one identity line (source hash · running commit), the
pre-filter-fix warning when it applies, and a `Provenance` drop-down holding all
five mandatory items:

1. sha256 of the source YAML, or `edited in session` if it was changed;
2. the commit of the code actually running (`git rev-parse HEAD`). **Not**
   `metadata.cyclophaser_version`: it reads `2.0.0` in every calibration file and
   distinguishes nothing;
3. keys present in the YAML and ignored by the current signature (`distance`);
4. keys absent from the YAML and filled by the current default, with the value;
5. the **"pre-filter-fix config"** warning when `boundary_padding` is missing.
   This is not cosmetic: the v1–v5 YAMLs carry `use_filter: true`, and in the
   code of that period `True` was read as the integer window 1 (bool is a
   subclass of int), so the Lanczos filter was **never** applied. The same line
   applies the filter today. Without the warning the column shows a result
   nobody saw at the time and presents it as history.

**Both measurements** are always shown, each named by its instrument: the phase
sequence from `evaluate_against_labels.py / score_phase_sequences` (starts only,
`tolerance_idx` per label, refuses to pair when the sequence does not match) and
the mature pairing from `item19_core.pair_by_overlap` (largest overlap, both
ends, fixed margin 6). They are different instruments and are never summed.

**`evaluation.bad_cases_count` is not a score.** It appears only as a labelled
historical annotation under `Provenance`: these were visual marks made at
different times with different knowledge of the problem (v5 and v6 record 0; v9
records 6).

**Leakage.** Every aggregate is computed over the train split. Aggregates
involving the 16 real cyclones of the frozen test split appear in a separate,
labelled block and are never added into the train one. Manual labels are opt-in.

Frozen reference columns come from `research/snapshots/` (see that directory's
README): the tab **reads files** and never runs a published version live.

### Modes, reference column and Run

**Reading order.** A one-line status bar (configs · cyclones · ground-truth
badge · reference column), then four numbered sections, each an expander:
**1 Mode → 2 Data → 3 Configurations → 4 Results**. Each section owns everything
it governs — the configuration cards render inside section 3, so collapsing the
section hides them.

**Mode is not independent state.** `Validation` and `Exploration` filter what is
selectable and what is emphasised; they never decide whether a number is
produced. That is decided per cyclone by whether it carries a manual label, in
`benchmark_core.scoreable`. A row with no label yields no scoring number in
either mode.

* **Validation** — only labelled sources selectable (51 real + 12 synthetic);
  scoring panel visible. Switching back from Exploration drops any uploaded
  track from the selection rather than carrying it into a scored run.
* **Exploration** — every source selectable, cyclone uploads included; scoring
  panel collapsed. If labelled rows are in the selection, a note offers to score
  those rows only.

**Without ground truth**, each column is measured against the **reference
column**, never against truth, and the block is labelled `relative to reference`.
Four measures: cyclones whose phase sequence changed; boundary displacement in
timesteps (median and max) for those whose sequence matches; phases that
appeared or disappeared, per type; and cyclones that refused an incipient phase.
Boundary displacement is computed only where the sequence matches — pairing
boundaries across a mismatch would compare two different transitions.

**Reference column** is chosen explicitly. It defaults to the manual label when
one exists, otherwise the first configuration column. The manual label has no
parameters, so the card diffs fall back to the first configuration column as
their parameter baseline, and the card says so.

**A card shows only the parameters that DIFFER from the reference.** Calibration
YAMLs share roughly fifteen identical parameters; listing all of them hides the
two or three that separate one configuration from another. The full
configuration sits behind the card's `Provenance` drop-down.

**Nothing recomputes on edit.** Results come from an explicit **Run**. A
fingerprint of (columns × selection × reference) is stored with them; when it
stops matching, the results are flagged **out of date** instead of being
silently replaced.

**Figures** come in two arrangements over the same data: `Side by side`
(default) and `Stacked`, which puts the panels on a shared x axis and a shared y
scale so a boundary that moved is read straight down the figure. The choice is
kept in session state.

## Sidebar order

The controls are grouped by the order in which the detector actually **executes**,
not by phase name:

| group | step | function |
|---|---|---|
| 1 Lanczos Filter | 1 | `process_vorticity` |
| 2 Savitzky-Golay Smoothing | 2 | `process_vorticity` |
| 3 Extrema Filtering | 3 | `find_peaks_valleys(z)` |
| 4 Intensification | 4 | `find_intensification_period` |
| 5 Decay | 5 | `find_decay_period` |
| 6 Mature | 6 | `find_mature_stage` |
| 7 Residual | 7 | `find_residual_period` |
| 8 Incipient | 9 | `find_incipient_period` |

Step 8, `post_process_periods`, takes no parameter.

Two consequences of reading the real order instead of assuming it: **extrema
filtering is step 3** — it runs before every stage, and the extrema that survive
there are the ones all of them see — and `decay_tail_amplitude_fraction` is read
by `find_residual_period` (`find_stages.py:588`), not by `find_decay_period`,
which is why it sits under Residual.

Two parameters span groups and carry a note in their own widget: `length_scale`
(scales the intensification and decay duration thresholds,
`find_stages.py:387`, and changes detected phases on 20160735, 20191014 and
20203947 under params-9) and `boundary_padding` (a filter parameter that can
govern the incipient phase: with `incipient_plateau_signal="derivative"` no
series refuses an incipient phase under `reflect`, 0/51, against 33/51 under
`edge`; with the default `incipient_plateau_signal="vorticity"` the probe reads
the raw series and refusals do not change, 28/54 training series under both —
`research/cleanup/passo1/RELATORIO.md`).

This layout's coverage is verified by an automatic test, not by eye:
`tests/test_sidebar_coverage.py` enumerates the package's public signature and
requires every parameter to have a control and no widget key to repeat.

## Scope

The app covers the whole detection pipeline: track upload (standard or custom
format), every filter, smoothing and phase-detection parameter of the package in
the sidebar, the Grid, Inspector and Label display modes, the Benchmark tab, and
export of the parameters (YAML) with the figures and phase tables.
