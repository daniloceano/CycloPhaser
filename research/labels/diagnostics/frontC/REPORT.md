# Front C — `intensification_min_depth`

**Branch** `research/frontC-intensification-depth`, from `develop-v2.1` @ `17dc21f`.
**Status: implemented and measured. NOT merged, NOT a PR. Awaiting Danilo's approval.**

Environment: numpy 2.5.3 / scipy 1.18.0 / pandas 3.0.5, conda env `cyclophaser`
(`sys.prefix` asserted). **The brief specified numpy 2.4.4 / scipy 1.17.1 /
pandas 3.0.2 — this machine no longer has those versions.** One expected number
depends on that difference; see "Divergences".

---

## What was built

`find_intensification_period` accepted a candidate segment on **duration alone**
(`threshold_intensification_length`). Nothing asked whether it deepened, so a
long flat stretch became intensification; `find_residual_period` then converted
that phantom intensification — having no mature after it — into `residual` to
the end of the series.

`intensification_min_depth` (default `0.0`, off) requires

    D2 = (z[peak] - z[valley]) / (z_max - z_min)  >=  intensification_min_depth

per **raw segment**, after the duration test and **before** gap stitching.
`find_residual_period`, `decay_tail_amplitude_fraction`, `mature_min_depth` and
`tests/test_decay_tail_amplitude_fraction.py` were **not** touched.

Files changed:

| file | change |
|---|---|
| `cyclophaser/find_stages.py` | the floor, its guard, its validation, its rationale |
| `cyclophaser/determine_periods.py` | parameter on both public signatures + docstrings |
| `research/labels/configs/cyclophaser_params-13.yaml` | params-12 + `intensification_min_depth: 0.05` (params-12 untouched) |
| `tools/calibration_app/app.py` | slider 0.00–0.50 step 0.01, default 0.00; YAML import/export; optional-key handling |
| `tests/test_intensification_min_depth.py` | new, 24 tests |
| `CHANGELOG.md`, `docs/future_work.md` | entry; findings under item 22 |
| `research/labels/diagnostics/frontC/` | the drivers, figures, measurements |

## Measured — TRAIN split (35 real + 12 synthetic), params-12 → params-13

All 47 `series_sha256` verified before comparing anything.

| metric | params-12 | params-13 | expected |
|---|---|---|---|
| sequence | 31/47 | **31/47** | 31/47 ✓ |
| mature within ±6 | 38/44 | **38/44** | 38/44 ✓ |
| synthetic sequence | 12/12 | **12/12** | 12/12 ✓ |
| incipient boundary identical | — | **47/47** | identical ✓ |
| series changed | — | **1** (`20180733`) | see below |
| non-residual phase lost | — | **none** | none ✓ |

`20180733` (train) — residual gone, decay extended, exactly as predicted:

```
before: … decay 147–189, residual 190–256
after : … decay 147–256
```

`20180654` (**test split, authorised**) — likewise:

```
before: intens 0–70, mature 71–82, decay 83–108, residual 109–148
after : intens 0–70, mature 71–82, decay 83–148
```

Only two series change in total, as predicted. Figures:
`fig_20180733_before_after.png`, `fig_20180654_before_after.png`.

## Default equivalence

| configuration | sha256 of the whole `periods` column, 47 series |
|---|---|
| package defaults, this branch | `b01b16b6…752f` |
| package defaults, **unmodified `develop-v2.1`, same env** | `b01b16b6…752f` — **identical** |
| package defaults + `intensification_min_depth=0.0` explicit | `b01b16b6…752f` — identical |
| params-12 (key absent) | `ee9541d3…3b59` |
| params-12 + `0.0` explicit | `ee9541d3…3b59` — identical |
| params-13 (`0.05`) | `8e752ecf…e101a` — differs, as it must |

## Divergences from the brief's expected numbers

1. ~~**The default-behaviour sha256 is `b01b16b6…`, not `b500d2e0…c4a5`** —
   the CHANGELOG value is environment-dependent.~~ **RETRACTED 2026-09-22 —
   this was my error.** I compared the canonical digest against one produced by
   a second generator I had written with a different blob layout
   (`default_equivalence.py`: `sid` + `"|".join(periods)`, no separators; the
   canonical `front_b/default_behaviour_hash.py`: `"<id>:<periods>"` lines
   joined by `\n`). Different blobs, identical behaviour, different numbers —
   and I blamed the libraries. Run with the canonical generator in this same
   environment the digest is `b500d2e0…c4a5` at `17dc21f` **and** `7a87a10`:
   the constant is not environment-dependent, and front C's default-neutrality
   is confirmed by the canonical instrument. See `docs/future_work.md` item 24.

2. **75 raw segments, not 68.** Both numbers are real and they count different
   things: **75** raw segments clear the duration test (the population the
   floor judges); **68** is the count of *stitched* blocks left after the gap
   merge. The D2 figures the brief quotes are per-segment, so 75 is their
   denominator. The docstrings say 75 and explain the 68. The D2 values
   themselves reproduce **exactly**: only one segment below 0.15, at
   `D2 = 0.0068`; smallest legitimate `D2 = 0.1714`; nothing between, so any
   floor in `(0.0068, 0.1714]` behaves identically on train.

3. **`20180654`'s block has D2 = +0.0025 (+0.25%), not −0.02%, and it is not
   stitched.** Under `params-12` neither series stitches at all: the raw
   segments and the blocks `find_intensification_period` leaves are identical
   on both. So the brief's empirical justification for judging before the
   stitch — "the stitched block of 20180654 has a negative D2 because of the
   merge" — **does not reproduce under params-12**. The pre-stitch ordering was
   implemented as specified anyway: it is the correct choice on principle (a
   merged block's D2 is a property of the merged span, not of the segments the
   parameter is defined on), and `test_floor_is_per_segment_not_per_stitched_block`
   demonstrates the difference on a purpose-built synthetic series, with a
   positive control. But no real series currently exercises it.

## Verification discipline

* The segment enumeration used for every D2 number is **verified against the
  detector** before being trusted: captured immediately after
  `find_intensification_period` and asserted to be a subset of its own mask on
  all 47 series. Checking against the *final* phase column would have been
  wrong — later steps legitimately overwrite intensification, which is exactly
  what happens to `20180733`'s spurious segment.
* The mature metric is the same instrument as front 20(b) stage 2
  (`item20b/gate_stage2.py`): best-overlap pairing of the first labelled mature
  run, margin a fixed 6. Reproduced in `measure_frontC.py` so the number is
  traceable to the code that made it.
* The per-segment ordering test ships with a **positive control** (a floor above
  both segments must reject both), so "the block survived" cannot be confused
  with "the parameter was never wired in".

### Epistemic standing of this gate — read before citing it

This gate is **not** of the same kind as those in items 19–23.

1. **Only the D2 distribution test was predictive**: "at most 3 segments fall in
   `(0.02, 0.15]`", declared before the measurement; result **0 of 75**.
2. **The gate metrics were not.** Sequence, mature, incipient, synthetics and
   the changed-series set were re-read from a floor sweep measured *before* the
   topological criterion for residual existed. Retrospective validation, not a
   passed prediction.
3. **Two earlier interventions failed first, the second on a mis-specified
   criterion** — it demanded "fixing" `20160735` and `20170342`, which are
   *correct* under the topological definition. A gate that fails on the wrong
   criterion is not evidence against what it rejected.
4. **The "destructive overwrite at `find_stages.py:726`, sibling of defect H"
   diagnosis is WITHDRAWN.** Line 726 is inside `find_residual_period`; the
   rule implements the physical definition and is correct.
5. **`0.05` was chosen after the result was known.** Nothing predictive backs
   that point inside `(0.0068, 0.1714]`; what is predictive is the window's
   existence and width.

## Drivers

| script | what it does |
|---|---|
| `measure_frontC.py` | TRAIN metrics, changed series, phase-existence check |
| `d2_separation.py` | the D2 distribution + the verified replay |
| `default_equivalence.py` | the sha256 table above |
| `report_test_series.py` | the authorised `20180654` measurement |
| `make_figures.py` | the two before/after figures |

## Open for Danilo

1. Merge or not — **not merged, no PR, per repo rule**.
2. Whether `0.05` stays the params-13 value. Any value in `(0.0068, 0.1714]` is
   equivalent on train; 0.05 was chosen from train alone.
3. Whether the unreproducible CHANGELOG hash should be re-recorded with its
   library versions, or dropped as a portability claim it cannot support.
4. The `decay_tail_amplitude_fraction` recalibration remains an open front
   (see item 22).
