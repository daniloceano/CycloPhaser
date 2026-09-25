# Item 30 — the swell batch: 10 tracks drawn for manual labelling

The labelled set (51 real + 12 synthetic) has **no case where the incipient
plateau ends after the intensity peak and overwrites the intensification**, so a
fix for that pattern could only be calibrated against visual marks. This folder
records how 10 tracks from the 200-track swell sample were brought into the
labelled set: chosen by a seeded rule and split into train and test **before**
anyone labelled them.

For this part of the front, no detector was run on the 10 and no figure was drawn.
The frozen split (`split.yaml`, seed 20260905, 47/16) is unchanged. The first 146
lines of that file are byte-identical to what they were, and the batch sits after
them as a separate block, `batches: swell_item30`.

| File | What it is |
|---|---|
| `transcribe_groups.py` | Copies the three groups out of the diagnostic's `m1_baseline.csv` (sha256-checked). It runs no detector. |
| `groups_params11.yaml` | The groups R (9), S (10) and C (175), plus Danilo's 15 bad marks. |
| `draw_batch.py` | The seeded draw. It was committed (`659eb5e`, pushed) **before** it was run. |
| `provenance.yaml` | For each file: sha256, original id, number of steps, first and last time, group, split. Also records the base and the conversion. |
| `../split.yaml` → `batches.swell_item30` | The frozen record: seed, rule, overlap exclusions, group sizes, the group of every id, train/test, and file hashes. |
| `tests/calibration_data/swell_item30/*.csv` | The 10 series, copied byte for byte from the standard-format swell files. |

## The batch

| id | group | split |
|---|---|---|
| 19860380 | R | train |
| 19870927 | R | train |
| 19940445 | R | train |
| 20120297 | R | train |
| 19930748 | R | **test** |
| 19790612 | S | train |
| 19810854 | S | train |
| 20111118 | S | **test** |
| 20050893 | C | train |
| 19990549 | C | **test** |

The draw used seed `20260925` and `numpy.random.default_rng`, with one generator
for the whole draw. The groups were drawn in the order R, S, C, and the members of
each group were sorted by id first. Within each group, `rng.choice` picked the
members and `rng.permutation` then split them into train and test:
R 5 (4 train / 1 test), S 3 (2/1), C 2 (1/1). Group sizes after the overlap
exclusion were R 9, S 10 and C 173. `tests/test_swell_batch.py` re-runs the draw
and checks that the committed block is exactly what the seed produces.

## Provenance of the groups (step 0)

**Source.** The maturation diagnostic of 2026-09-24 (not in the repo; its outputs
were in `cyclophaser_swell_tracks_test/diag_maturation/`). The inputs to the
groups are:

- The package code of `develop-v2.1` @ `d45ae49`, run through `baaf595` (item 29).
  `git diff baaf595 0f5bef5 -- cyclophaser/` is empty.
- The repo's `params-11` config (`24dd7f22…`). The three keys it does not set
  took the package defaults: `intensification_min_depth` 0.0,
  `mature_min_depth` 0.0 and `reclassify_index0` **True**.
- Measurement 1 of the diagnostic, `m1_baseline.csv` (sha256 `a1aa5619…`). The
  replay was identical to `get_periods` in 200/200 cases.

The local branch `exp/pre-peak-normalization` (`1faf0c8`, parent `baaf595`)
holds only Measurement 2, the opt-in `incipient_scale`. Its default-off run
reproduces Measurement 1 in 200/200 cases, and its lists are identical.

**Definitions**, as written in `m1_baseline.py`:

- **Intensity peak:** `peak_idx = argmin(z)`, where `z` is the *filtered*
  vorticity.
- **End of the plateau:** `plateau_boundary`, the start of the first run of
  k = 5 consecutive samples with rel ≥ τ = 0.2 (`sustained`). Here
  rel = |d(ζ_raw smoothed, Savitzky–Golay 5/3)/dt| / max.
- **Overwritten intensification:** a mature phase with no intensification before
  it, where the periods in place *before* the incipient step already contained
  intensification. This is `mechanism = int_overwritten_by_plateau`; it holds in
  9/9 flagged cases (7 bad, 2 good).
- **The signal that defines the groups:** `plateau_boundary > peak_idx`. It
  holds in 9 of the 15 bad tracks and 10 of the 185 good ones, leaving 175
  good tracks without it. This is not the same set as the "mature without
  intensification" flag: 3 tracks in R are unflagged (19940445, 19960808,
  20120297), and one flagged bad track (19890443) is not in R.

**The 15 bad marks.** They are in the `evaluation.bad_cases` block of the file the
app exported as `cyclophaser_params-11.yaml` (2026-09-24T22:42Z, sha256
`6df2cc07…`, not in the repo), which also lists all 200 tracks. **That file's
filter and phase parameters are identical to `params-14`**
(`intensification_min_depth` 0.05, `mature_min_depth` 0.80, `reclassify_index0`
true), not to the repo's `params-11`. The diagnostic ran the repo's `params-11`
instead of that file. This does not change the groups, for two reasons:

- The signal reads only `z`, `z_unfil` and the plateau parameters. Those are
  identical in the two configurations, and no stage writes `z` or `z_unfil`.
  The two depth floors act only on the mature and intensification blocks.
  This was established by reading the code, not by running it under `params-14`.
- The bad marks are Danilo's own judgement and are taken as given.

What the discrepancy *does* change is the labelling note below.

## Overlap with the 51 labelled real series (step 0c)

The id schemes are the same (original TRACK ids). Two swell tracks are
**already labelled**. Both were compared by id, start time, length and series,
and both were excluded from every group before the draw:

| id | split in the repo | match |
|---|---|---|
| 20180733 | train | same start, 257 steps, file byte-identical |
| 20203389 | test | same start, 95 steps, file byte-identical (**its label was not read**) |

Other swell tracks overlap real tracks in time (six pairs of 11–88 common steps).
They are concurrent, distinct cyclones: their ids differ and the values do not
match (max|Δ| ≥ 1.5e-5).

## Conversion (step 0d) — measured

The conversion is `min_max_zeta_850 = -1e-5 * vor42`, where vor42 is in
1e-5 s⁻¹ and positive. It was measured on 20180733, the one train overlap:

- Same 257 hourly times, lag 0.
- max|Δ| = 1.36e-20 (max relative difference 1.7e-16, i.e. 1 ulp); 218/257
  values are bit-identical.
- Mean ratio 1.000; all 257 values have the same (negative) sign.
- The standard-format file is byte-identical to
  `tests/calibration_data/20180733.csv`.

## Labelling note — not blind for R

Danilo saw the detector's output on the cases of group R before labelling them,
so their labels are not blind. The configuration on screen was the app export
above, whose parameters equal those of `params-14`. It was **not** the repo's
`params-11`, under which the groups were computed. The whole 200-track sample
went through that same evaluation, so the S and C cases were also seen with the
detection, just without a bad mark.

## Exposure of an already-labelled TEST series

**20203389** is a TEST series of the original split. It was one of the 200 swell
tracks that Danilo evaluated with the detection on screen in the Grid on
2026-09-24. All 63 labels were already on file by then (on `develop-v2.1` the
labels file header reads `updated: '2026-09-14…'`), so its label predates the
exposure. It was excluded from the draw (step 0c), and **its label was not
read** at any point in this front. The series itself, however, has now been
seen with detector output. Any later reading of test results that cites 20203389 should say so.

## Name trap: an export called `params-11` that holds `params-14`

The app export `cyclophaser_params-11.yaml` (sha256 `6df2cc07…`), the file that
holds the 15 bad marks, carries **`params-14`'s values**:
`intensification_min_depth` 0.05, `mature_min_depth` 0.80,
`reclassify_index0` true. Its filter and phase blocks are identical to
`params-14`. The file's name is not its configuration. Before attributing a
result to a configuration, compare the export's parameter blocks with
`research/labels/configs/`; the file name is not evidence.

## Where the batch appears

- **Label tab: yes.** The 10 are appended after the 63, whose order is unchanged.
  The 3 test cases may be saved **once**, while they still have no label; after
  that they are locked like every test case. The 16 test cases of the original
  split stay locked.
- **Decision (Danilo, 2026-09-25):** the save-once exception for the batch's 3
  test cases is accepted. A test case that was drawn before anyone labelled it
  must be labellable once, and it is locked from then on, overwrite included.
- **Nowhere else.** The benchmark, `evaluate_against_labels.py`,
  `load_real_series`, `make_split` and the Grid's "load all test cyclones" all
  glob `tests/calibration_data/*.csv` non-recursively, so they still see 51 real
  series and 63 in total. Split × source is unchanged at 35 train real, 12 train
  synthetic and 16 test real, and so is the population hash.

## Labels recorded (2026-09-25)

`manual_labels.yaml` gained exactly 10 records, the ids of this batch
(`n_labels` 63 → 73). Each of the 63 earlier records is byte-identical to its
block on `develop-v2.1`; the only other change is the header (`updated`,
`n_labels`). For every one of the 10, the record's `series_sha256` equals the
hash of the batch file's values, and that file's own sha256 equals the one in
`split.yaml`. All 10 show as labelled (not stale) in the tab.

For the 7 train records, schema 4 is valid: the phases pass validation and the
stored verdict is the one derived from them. For the 3 test records (19930748,
19990549, 20111118), only presence, hash and lock were checked. The tab (AppTest)
shows each as `[TEST split — locked]`, both save buttons are disabled, and the
blocker says the case is in the TEST split. A batch train case, checked as a
control, stays saveable.
