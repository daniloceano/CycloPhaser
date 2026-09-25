# Item 30 — measurement: gate (0) and baseline (1) under params-14

**Measurement only.** No line under `cyclophaser/` changed; no correction is
proposed, no parameter adjusted, nothing relabelled.

The question is whether the plateau overwrite `df.iloc[:boundary] = 'incipient'`
(`find_stages.py:1134`, defect H) is the mechanism that erases an intensification
the pipeline had already detected, when the end of the incipient plateau falls
after the intensity peak.

Predictions: `PREDICTIONS.md`, committed in `f01ca88` before anything was run.
Each is judged below against that text, which is not rewritten.

## Setup

- **Branch.** `research/item30-plateau-overwrite`, from `develop-v2.1` @
  `0f5bef5`. The package code is identical to the current develop tip:
  `git diff 0f5bef5 develop-v2.1 -- cyclophaser/` is empty.
- **Config.** `params-14`, sha256 `acf49853…`, run exactly as the app runs it
  (`benchmark_core.split_config` with `use_filter` True → `'auto'`).
  `params-11` (`24dd7f22…`) is run too, for P1.
- **Environment.** The dedicated `cyclophaser` env: python 3.12.14, numpy 2.5.3,
  scipy 1.18.0, pandas 3.0.5.
- **Code actually loaded.** `cyclophaser.__file__` and `layer_inspector.__file__`
  are asserted in-process to be this checkout (`item30_core.py`). The modules'
  sha256:
  - `determine_periods.py` `dccab392…`
  - `find_stages.py` `a0c65358…`
  - `layer_inspector.py` `89def9d7…`

### Step 0a — are the two configs the same where it matters?

Yes. `filter_params` (including `boundary_padding: edge`) and every
`incipient_*` key are identical between `params-11` and `params-14`. The configs
differ only in `mature_min_depth` 0.8, `intensification_min_depth` 0.05, and
`reclassify_index0` True, which `params-14` states explicitly and is already the
package default.

### The pre-incipient map, and where C2′ runs

- **Stage order.** In `get_periods`, `post_process_periods` (l. 1247) is
  followed directly by `find_incipient_period` (l. 1250); nothing between them
  touches `periods`.
- **Inside `find_incipient_period`.** Between its entry (l. 1038) and line 1134,
  the only write to `periods` is `fillna('incipient')` (l. 1102), which fills NaN
  cells only.
- **The pre-incipient map** is therefore step 5 of
  `layer_inspector.pipeline_ribbon`. Each of its non-NaN labels is exactly what
  line 1134 overwrites.
- **Where C2′ runs.** `reclassify_index0` is applied inside
  `find_peaks_valleys(z)` while the working frame is built (l. 1206–1209). That
  is before all six steps, not in any of them.
- **The args handed to the ribbon.** They are captured from inside
  `get_periods` by wrapping its first stage call, not transcribed. This
  branch's `build_args_periods` predates the item-30a fix and would reject the
  two depth floors, so it is not used. `build_working_frame` and
  `pipeline_ribbon` are identical to develop's.
- **Asserted on every run.** 196 × 2 swell tracks plus 54 train series, 446 runs
  in total, 0 failures:
  1. the ribbon's step 6 equals `get_periods`' `periods` value for value;
  2. every step-6 overwrite lies in `[0, boundary)` and writes `incipient`.

### Definitions (as in exploratory `1faf0c8`)

- **Peak:** `argmin` of the filtered `z`.
- **Plateau end (boundary):** the start of the first run of 5 samples with
  rel ≥ 0.2, computed with the package's own `_incipient_plateau_rel` and
  `_incipient_plateau_boundary`.
- **Signal:** boundary > peak.
- **Symptom:** in the final map, a mature phase with no intensification before
  it.

### Exclusions

- The 16 TEST series of the split, and the batch's 3 TEST series (19930748,
  20111118, 19990549), are excluded from every measurement, table and log.
- In the swell sample, 20203389 (TEST) is excluded as well, leaving a universe of
  **196** tracks: 14 bad and 182 good.
- Labels are read through `item30_core.train_labels`, which drops every non-train
  record by id before any field is read.
- The evaluator's new option drops those records the same way, before its
  checks.

## Step 1 — swell baseline, 196 tracks, params-14

The per-track table is kept outside the repo
(`cyclophaser_swell_tracks_test/diag_item30/swell_baseline_params14.csv`).
Only aggregates are given here.

| | bad (14) | good (182) |
|---|---|---|
| signal, params-14 | **8** | **9** |
| signal, params-11 (m1) | 8 | 9 |
| symptom, params-14 | 6 | **0** |
| symptom, params-11 (m1) | 6 | 2 |

**Entries and exits, track by track against `m1_baseline.csv`:**

- **Signal:** no entries or exits, bad or good. The sets are identical.
- **Symptom:** no change among the bad. Among the good, 19880329 and 19940213
  **left**, and none entered. Under params-11 both had a mature with no
  intensification before it. Under params-14 neither has a mature:
  - 19880329 becomes `incipient > decay`;
  - 19940213 becomes `incipient > decay > intensification > decay`.

  The two depth floors are the only parameters that differ between the runs.
  Which of the two floors causes this was not measured.

m1's symptom column was also recomputed under params-11 and agrees 196/196.

The signal sets are:

- **8 bad with the signal:** 19860380, 19870927, 19900808, 19940445, 19940737,
  19960808, 20000821, 20120297.
- **9 good with the signal:** 19790612, 19810854, 19830376, 19840325, 19861089,
  19880329, 19910227, 20030213, 20204384.

## Step 2 — gate (0a)/(0b)

Per-track details are outside the repo (`diag_item30/gate_params14.json`).

**The 8 bad tracks with the signal**

- **(0a):** intensification is present in the pre-incipient map before the
  boundary in **8/8**. In 7/8 it opens the series at index 0. It ends 2 to 8
  steps **before the peak**; the step-5 mature window covers the peak.
- **After step 6:** no intensification is left before the boundary in **8/8**.
  The step-5 intensification samples in `[0, boundary)` are exactly the ones
  step 6 erases, again **8/8**. The intensification survives steps 1–5 and is
  lost only at step 6.
- **(0b):** step 6 erases **intensification in 8/8** and **mature in 8/8**,
  and decay in 3/8. Counted as blocks, that is 9 intensification, 9 mature and
  4 decay; 19870927 contributes two of each.
- **The phase that opens the final map at the boundary:** `mature` in 5/8 and
  `decay` in 3/8. In those 3 (19940445, 19960808, 20120297), step 6 erased the
  whole mature, and the final map reads `incipient > decay`.

**The 9 good tracks with the signal**

- **In 7/9 the peak is at index 0 or 1.** The series opens at its most intense
  point, the pre-incipient map starts with `decay`, and there is no
  intensification before the peak. The signal fires only because boundary > 0.
  Step 6 erases `decay` only.
- **In 2/9 (19810854, 19861089)** step 6 erases the whole leading
  intensification, the mature and part of the decay. The final map reads
  `incipient > decay`, although both were marked good.
- **Final map at the boundary:** `decay` in 9/9.

### Predictions P1–P5

**P1 — CONFIRMED.** The plateau boundary is identical under params-11 and
params-14 in **196/196** tracks, both against the m1 CSV and against a fresh
params-11 run. The peak is also identical in 196/196.

**P2 — CONFIRMED.** The signal fires in **8/14 bad and 9/182 good** tracks,
exactly.

**P3 — CONFIRMED, 8/8.** In every one of the 8 bad tracks with the pattern,
intensification is present in the pre-incipient map before the boundary and is
absent after the incipient step. Mechanism H accounts for the loss in full: the
erased samples are exactly the step-5 intensification in `[0, boundary)`.

**P4 — REFUTED: 5/8, not 8/8.** The symptom persists in 19860380, 19870927,
19900808, 19940737 and 20000821. In 19940445, 19960808 and 20120297 the overwrite
also erased the **whole** mature, so the final map has no mature for the symptom
to fire on. The damage there is larger, not smaller. Under params-11 the result
is the same 5/8.

**P5 — REFUTED: 2/9, not 9/9.** Per the prediction's own dichotomy, H is not
described wrongly: in the bad tracks it does exactly what was described. The
premise fails instead: **the intensification does not end at the global
minimum.**

- In 7/9 good tracks no intensification exists before the peak at all, because
  the peak is at index 0 or 1 and step 6 erases decay only.
- In the 2/9 where an intensification leads to the peak, it ends 8 to 14 steps
  before it, with the mature in between. That block does vanish.

The signal `boundary > peak` therefore groups two different situations:

1. a peak near index 0, where there is nothing to erase but decay;
2. an intensification → mature that the plateau swallows whole.

## Step 3 — train census: 42 real + 12 synthetic, params-14

### 3a — evaluator option

`evaluate_against_labels.py --batch-train swell_item30` adds the batch's TRAIN
part as its own block. It is never pooled into `TRAIN · ALL`, and it refuses
`--test`. Every non-train label is dropped by id right after reading.

- **Default path unchanged.** `prove_evaluator_default.py` runs the evaluator of
  `f01ca88` (before the option) and the current one on the same train-only
  input, with `--config params-14` and with package defaults.
  - Population hash is identical (`b39338fd…`) in both.
  - Printed output is identical, character for character, in both.
- **The 47-series blocks** are also identical with and without `--batch-train`.
- **Exclusion test.** `tests/test_evaluate_batch_train.py` stubs the detector
  and checks that no TEST id, of the split or of the batch, reaches:
  - the detector;
  - any scoring aggregate;
  - even the legacy-record check.

### 3b — baseline score, params-14

Output in `evaluate_params14_train_batch.txt`.

| block | full sequence match | incipient boundary within margin |
|---|---|---|
| **47 original** (35 real + 12 synthetic) | **31/47** (66.0%) | **17/27** (63.0%), MAE 3.00, worst 26 |
| … of which real (35) | 19/35 | 8/17 |
| … of which synthetic (12) | 12/12 | 9/10 |
| **7 batch train** | **1/7** (14.3%) | **3/7** (42.9%), MAE 17.17, worst 59; 1 refusal |

### 3c — census

Per series in `census_train_params14.csv` (training series only).

- **Signal:** 6/42 real train series, **all six from the batch**: 4 R and 2 S.
  The batch's C case, 20050893, has boundary 0. The split's 35 real series
  show it in **0/35**, and the 12 synthetic in 0/12. This confirms the premise
  that motivated the batch: the original labelled set had no case of this kind.
- **H erases a non-incipient block** in 20/42 real series (14/35 in the split,
  6/7 in the batch) and in 10/12 synthetic. It erases intensification
  specifically in 18/42 real (13/35 + 5/7) and 8/12 synthetic.
- **Outside the signal, the erasure is the leading part of an intensification**,
  with boundary < peak in all 35 split series. Here the labels mostly agree with
  the detector. In the 13 split series, label incipient end − boundary is
  −1, 0, 0, 0, 1, 1, 2 (7 within ±2), then −4, 6, 26; one label is ambiguous and
  two say "no incipient". In the 8 synthetic series it is within ±1 in 7, and +4
  in the eighth.

**P6 — REFUTED: 2/4.**

- For 19940445 and 20120297, the label's intensification starts at 8 and 2,
  before the boundary (38 and 10).
- **19860380 and 19870927 are labelled `incipient > decay`**, with no
  intensification and no mature. Their labelled incipient end (14 and 64) is
  within 2 steps of the plateau boundary (12 and 66).
- In these two, the label does not support "an intensification was erased".
  What the detector adds that the label rejects is the **mature**.

**P7 — no prediction.** The data for the 42 real train series is given above.
For the 2 S train series:

- **19790612.** Peak at 0. Step 6 erases decay `[0, 14]`, and the final map is
  `incipient > decay`. The label is `incipient > decay` with incipient end 13
  (boundary 15), so the full sequence matches.
- **19810854.** Step 6 erases intensification `[0, 48]`, mature `[49, 60]` and
  decay `[61]`, and the final map is `incipient > decay`. The label is
  `incipient > intensification > mature > decay` with incipient end 3, 59 steps
  before the boundary. Here H erases a labelled intensification and a labelled
  mature.

## What this establishes, and what it does not

- **H is the mechanism of the erasure.** In all 8 bad tracks with the pattern,
  and in the batch's R and S cases, the intensification detected by steps 1–5 is
  erased at line 1134 and nowhere else.
- **Whether that erasure is wrong has two answers** in the labelled training
  data:
  - 19810854, 19940445 and 20120297: yes, the label has the intensification.
  - 19860380 and 19870927: no. The label has no intensification; the error is
    the mature.
- **The signal is not a clean criterion.** On the good tracks it mostly flags a
  peak at index 0, where nothing but decay is erased.

## Files

- **`item30_core.py`** — the pipeline per series (ribbon, boundary, peak,
  erasures), both assertions, and the population and label guards.
- **`swell_baseline_gate.py`** — steps 1 and 2. It takes the swell folder and
  the m1 CSV (sha256-checked) as arguments and writes per-track tables outside
  the repo.
- **`census_train.py`** — step 3c.
- **`prove_evaluator_default.py`** — step 3a.
- **`evaluate_params14_train_batch.txt`**, **`census_train_params14.csv`** —
  the outputs.
