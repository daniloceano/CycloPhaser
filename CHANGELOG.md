# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed

**Two filtering defaults moved together (behaviour change)**

| parameter | was | now |
|---|---|---|
| `boundary_padding` | `"zero"` | **`"reflect"`** |
| `replace_endpoints_with_lowpass` | `24` | **`0`** (and deprecated) |

They had to move together: with `boundary_padding="reflect"` and a non-zero
`replace_endpoints_with_lowpass`, both the bandpass and the lowpass carry full
amplitude at the edge instead of both being suppressed toward zero, so the
difference in their gains no longer cancels and the 5 % endpoint splice becomes a
visible **step**. Measured over the 51-track calibration set, the number of tracks
whose detected life cycle *opens* with a spurious `decay` phase:

| configuration | `"zero"` | `"reflect"` |
|---|---|---|
| `replace_endpoints_with_lowpass=24` | 4/51 | **28/51** |
| `replace_endpoints_with_lowpass=0` | 0/51 | **0/51** |

A cyclone track essentially never begins by weakening, so 28/51 is an artifact.
With both new defaults in place: **49/51 tracks open with `incipient`, 2/51 with
`intensification`, 0/51 with `decay`** (old defaults: 46 / 1 / 4).

**`boundary_padding` now defaults to `"reflect"`**

The option added below shipped with `"zero"` as its default so that nothing moved
while it was being validated. It is now `"reflect"` in every entry point:
`lanczos_filter`, `lanczos_bandpass_filter`, `process_vorticity`,
`determine_periods`, and the calibration app.

Rationale: `"zero"` is not a neutral choice, it is the artifact. Convolving via
`scipy.signal.convolve(..., mode="same")` zero-pads the input beyond its own ends,
and because vorticity has a non-zero floor those "missing" samples are a jump to
zero rather than a continuation of the signal. With a kernel about half the series
length, the result is a spurious *deepening* ramp worth a median **74 % of the
cyclone's own peak-to-peak amplitude**, contaminating **~48 % of every series**
(~24 % at each end) and accounting for **≥ 80 % of the slope measured at the first
sample in 51/51 tracks** of the calibration set. Leaving that switched on by
default was judged the larger cost.

Measured effect of the new default (normalised `|dz|` at the first/last sample,
median over the 51-track set, with the Lanczos filter active): **0.95/0.98 →
0.42/0.35**. Raw-signal reference: 0.29.

> **How to reproduce earlier results:** pass `boundary_padding="zero"` **and**
> `replace_endpoints_with_lowpass=24` explicitly. Together these restore the
> previous output byte-for-byte. Note that a parameter set calibrated under one
> padding mode must be re-validated under another — the smoothed signal differs in
> the boundary zone, so this is not a drop-in swap in either direction. On the
> 51-track set, 14/51 detected phase sequences differ between `"zero"` and
> `"reflect"`.

### Deprecated

**`replace_endpoints_with_lowpass`**

Kept, not removed; a non-zero value now emits a `DeprecationWarning`.

It was introduced as a palliative for exactly the artifact `boundary_padding` now
fixes at its source — and it never fixed the cause, because the lowpass estimate it
splices in is produced by `lanczos_filter`, i.e. by the *same* zero-padded
convolution. Measured on the 51-track set, it took the normalised `|dz|` at the
first sample only from a median 0.95 to 0.71, at the cost of 14 % of z's amplitude,
whereas `boundary_padding="reflect"` takes it to 0.42 at no amplitude cost.

With `boundary_padding="reflect"` it is worse than redundant, it is harmful — see
the endpoint-splice step documented under "Changed" above.

### Fixed

**`use_filter=True` silently disabled the Lanczos filter (behaviour change)**

`process_vorticity` selected the Lanczos window with
`if use_filter == 'auto': window = len(zeta)//2 else: window = use_filter`.
Because `bool` is a subclass of `int` in Python, `use_filter=True` fell into the
`else` branch and was read as the integer **1**. A 1-tap Lanczos kernel is a
single scalar multiply (0.0714 for `cutoff_low=168` / `cutoff_high=24`), not a
convolution — so a caller asking for filtering received **none**, and the output
differed from `use_filter=False` only by a constant factor that every downstream
(difference-based) criterion cancels out.

`use_filter=True` is now equivalent to `use_filter='auto'` (window
`len(series)//2`) and emits a `UserWarning` naming the resulting window.
`use_filter=False` still disables filtering; an explicit integer is still a
literal window length, and `use_filter=1` is no longer conflated with `True`
(the bool check runs before the int check).

> **Impact — read this before reusing old results.** Any series processed with
> `use_filter=True` on version 2.0.0 or earlier was effectively **unfiltered**.
> This includes the calibration app's "Apply Lanczos filter" checkbox, which
> sends a bool. Parameter sets calibrated under that setting were calibrated on
> an unfiltered signal and **must be re-validated** — the filter now actually
> runs, which changes the smoothed series, its derivatives, and the detected
> phases.

### Added

**`boundary_padding` — opt-in fix for the Lanczos zero-padding edge artifact**

`lanczos_filter` and `lanczos_bandpass_filter` convolve via
`scipy.signal.convolve(..., mode="same")`, which implicitly zero-pads the input
beyond its own ends. Vorticity has a non-zero floor (order -5e-5), so those
"missing" samples are a jump to zero rather than a neutral continuation, and two
properties of this configuration amplify the damage: the kernel is about half the
series length (measured kernel/series ratio median 0.494 over the 51-track
calibration set), and the bandpass kernel does not actually reject DC at these
window lengths (`sum(weights)` median 0.629).

The result is a step between the boundary value and the interior worth a median
**74 % of the cyclone's own peak-to-peak amplitude**, spread as a ramp over ~24 %
of the series at each end and carrying the sign of a spurious *deepening*. On the
calibration set that ramp alone accounts for **≥ 80 % of the slope measured at t0
in 51/51 tracks**.

`boundary_padding` accepts `"reflect"`, `"edge"` and `"zero"` (the latter
byte-for-byte the pre-fix behaviour). Measured on the 51 tracks with
`use_filter='auto'` (normalised `|dz|` at the first/last sample, median):
`"zero"` 0.95/0.98, `"reflect"` 0.42/0.35, `"edge"` 0.50/0.38 — against a
raw-signal reference of 0.29. It shipped with `"zero"` as the default and that
default has since been changed to `"reflect"` (see "Changed" above).

The Lanczos kernels themselves are unchanged; the correction is purely a boundary
condition, and the pad widths reproduce scipy's `"same"` alignment exactly, so no
time shift is introduced. Exposed in the calibration app (selectbox + YAML
import/export; pre-existing YAMLs fall back to the default without warning).

`replace_endpoints_with_lowpass` was introduced as a palliative for this same
artifact and itself calls `lanczos_filter`, i.e. it replaces zero-padded bandpass
endpoints with zero-padded lowpass endpoints. It is unchanged here and is a
candidate for future deprecation.

### Notes

**New validated calibration with the Lanczos filter active.** With the two changes
above in place, the author re-validated the 51-track calibration set and reached
0/51 bad cases with `use_filter=true`, `cutoff_high=18`, `boundary_padding=reflect`
and **Savitzky-Golay smoothing of `z` switched off entirely**
(`use_smoothing=false`, `use_smoothing_twice=false`). See
`docs/future_work.md` § 3c for the full parameter set, the measurements, and the
caveat that `use_smoothing=false` disables Savgol on `z` but leaves the
*derivative* smoothing running with an auto window.

---

## [2.0.0] - 2026-06-14

This release consolidates a comprehensive bug-fix and hardening pass on the core
phase-detection pipeline (`fix/core-bugs` branch), a new synthetic test suite,
an interactive calibration tool, and packaging / documentation cleanup.
No public API defaults were changed; the fixes are behavioural corrections to
previously silent or erroneous logic.

### Fixed

**Phase detection — core bugs**
- `find_intensification_period`: wrong dict key caused `threshold_intensification_gap`
  to be silently ignored (gap-merging was never applied).
- `post_process_periods`: singleton-phase detection used `type(…) == int` which
  never matched a pandas Timedelta; single-timestep phases were therefore never
  absorbed by their neighbour.
- `find_residual_period`: three related bugs corrected —
  correct last-block selection (was always selecting first block),
  working residual fill (fill loop was a no-op),
  and consistent consecutive-block detection.
- `find_residual_period`: guard against `NameError` when neither `decay` nor
  `mature` is present in `unique_phases` (early return instead of crash).
- `periods_to_dict`: suffix counter for 3+ repeated phase names was broken
  (`len()` of a 2-tuple is always 2, so the third block always overwrote
  `"name 2"`); now counts all matching existing keys for a unique suffix.
- `find_mature_stage`: `df.loc[block_start - dt]` and `df.loc[block_end + dt]`
  raised `KeyError` when a mature block touched the series boundary; explicit
  boundary check added, out-of-bounds treated as "required neighbour absent"
  → block cleared to `NaN`.
- `find_peaks_valleys`: plateau runs (consecutive equal extrema) collapsed to a
  single representative midpoint, preventing duplicate / overlapping peak-valley
  labels that caused downstream detection failures.
- `plot_all_periods`, `generate_figures.py`: spurious white gaps between adjacent
  phase bands eliminated by extending each phase's right boundary to the start of
  the following phase (root cause: `periods_to_dict` returns `end` = last timestamp,
  so `axvspan`/`fill_between` stopped one `dt` short of the next phase start).

**Pandas compatibility**
- Removed deprecated `inplace=True` patterns (`find_incipient_period`) replaced
  with direct assignment, compatible with pandas Copy-on-Write (pandas ≥ 2.0).
- `is` / `is not pd.NaT` identity comparisons replaced with `pd.isna()` throughout.

**Savgol smoothing**
- Integer `use_smoothing` / `use_smoothing_twice` values are now coerced to the
  nearest odd integer and clamped to the series length, with a `UserWarning`;
  previously they were passed through silently and could cause Savgol errors.

**Input validation**
- `process_vorticity` now raises a clear `ValueError` when the input is a
  `list` or `ndarray` and `x` (the time index) is `None`, instead of letting
  an obscure downstream error surface.

**Plotting**
- `plot_all_periods` legend moved from `bbox_to_anchor=(1.5, 1)` (far right of
  axes, causing excessive whitespace in exported PNGs) to centred below the axes.

### Changed

- `plot_all_periods` and `plot_didactic` now always return a
  `matplotlib.figure.Figure` object (previously returned `None`). Callers that
  discard the return value are unaffected.
- `plot_didactic`: `output_directory` parameter is now optional (default `None`);
  when `None`, no file is written. Previously `None` caused a crash.
- `find_stages.py` / `find_intensification_period`: stale inline comment hardcoded
  "12.5%" replaced with a generic description referencing the threshold parameter
  (actual configurable default is 7.5%).

### Added

**Tests**
- Synthetic test suite (`tests/synthetic/`) covering 12 life-cycle patterns
  (clean and noisy variants of ItMD, IcItMD, IcDItMD, DItMD, IcItMD×2, ItMD×2,
  IcIt observational, quase_ItD, IcItMD residual); tests check both phase
  sequence and approximate phase timing.
- Regression baselines (`test_baseline_default`, `test_baseline_smoothing`)
  updated to reflect corrected behaviour.
- Unit tests for `find_peaks_valleys` plateau behaviour (4 cases).
- Unit test for `determine_periods` with non-default options.

**Calibration tool** (`tools/calibration_app/` — not distributed in the wheel)
- Interactive Streamlit app for tuning filter, smoothing, and phase-detection
  parameters against one or more cyclone CSV files simultaneously.
- Multi-cyclone grid view (1–6 columns); compact twin-axis figure for dense grids.
- YAML export / import of full parameter configuration.
- Export all results as ZIP (per-cyclone `_periods.csv` + full-resolution
  `_periods.png` + `parameters.yaml`).
- In-app Documentation tab with method overview, parameter reference, and
  methodological notes (detection order, precedence, ~15–18 h detection lag).

**Documentation**
- `get_periods` docstring: phase detection pipeline order, function-call precedence
  (later functions can overwrite earlier labels), and detection-lag note
  (~15–18 h at 3-hourly resolution, most pronounced for `residual`).
- `find_peaks_valleys` docstring: boundary-index artefact documented.
- `docs/future_work.md`: 7 methodological improvement directions for
  post-2.0 releases (adaptive thresholds, `find_peaks` replacement,
  derivative smoothing, low-confidence boundary zone, and more).
- Cross-reference comments in `plots.py` and `generate_figures.py` linking
  the two copies of the gap-fix logic.

### Packaging / Documentation

- **License**: unified to `GPL-3.0-or-later` (SPDX); `setup.py` was incorrectly
  set to `MIT`. `LICENSE` file already contained the full GPLv3 text.
- **Version**: `1.9.4` → `2.0.0`.
- **Dependencies**: `pytest` moved from `install_requires` to
  `extras_require['test']` (test dependency, not runtime).
- **Project URLs**: Documentation and Issue Tracker URLs corrected to
  `cyclophaser.readthedocs.io/en/latest/` and
  `github.com/daniloceano/CycloPhaser/issues`.
- **README**: JOSS citation updated from "(under review)" to published form
  (de Souza et al., 2025, *JOSS*, 10(108), 7363,
  https://doi.org/10.21105/joss.07363); double-parenthesis markdown link bug
  fixed; unclosed code fence closed.
- `process_vorticity` docstring: removed orphaned `filter_derivatives` parameter
  entry (parameter does not exist in the function signature).

---

## [1.9.4] - 2025-01-01

*(Previous release — see git history for details.)*

[2.0.0]: https://github.com/daniloceano/CycloPhaser/compare/v1.9.4...v2.0.0
[1.9.4]: https://github.com/daniloceano/CycloPhaser/releases/tag/v1.9.4
