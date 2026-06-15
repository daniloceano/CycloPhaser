# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
