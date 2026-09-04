# Regression tests for ``use_smoothing=False`` disabling the DERIVATIVE smoothing.
#
# The behaviour that changed
# --------------------------
# ``use_smoothing=False`` skipped both Savitzky-Golay passes on the vorticity
# ``z``, but ``process_vorticity`` then reached::
#
#     if not window_length_savgol:
#         window_length_savgol_derivatives = len(zeta_df) // 4 | 1   # or // 2
#
# and applied FOUR Savgol passes to the first and second derivatives with that
# *auto* window -- 15-91 timesteps over the 51-track calibration set, i.e.
# LARGER than any window a calibration ever asked for explicitly.  So a caller
# who switched smoothing off still got the derivatives smoothed twice, with a
# window they never requested.  The block justified itself with "filtering the
# derivatives is not an option because they are too noisy"; measured on TRACK
# (Gramcianinov) vorticity that did not hold -- 1/51 phase sequences change and
# no fragmentation appears, while r(t0) drops from 0.545 to 0.068.  See
# docs/future_work.md, item 4, "Measurement 2026-09-03" and the author's
# decision recorded at the end of that section.
#
# What is pinned here
# -------------------
# 1. With ``use_smoothing=False`` the derivative arrays ``find_stages`` consumes
#    are the UNFILTERED derivatives, exactly (identity, to floating point).
# 2. ``use_smoothing='auto'`` and explicit integer windows still smooth the
#    derivatives -- the change is scoped to the explicit ``False`` case.
# 3. Other falsy values (``0``, ``''``) keep their previous behaviour: the
#    check is ``use_smoothing is False`` by identity, NOT a truthiness test.
# 4. The Savgol passes on ``z`` itself are untouched by this change.

import glob
import os
import warnings

import numpy as np
import pandas as pd
import pytest

from scipy.signal import savgol_filter

from cyclophaser.determine_periods import process_vorticity

_CALIBRATION_DATA_DIR = os.path.join(os.path.dirname(__file__), "calibration_data")
_TRACK = f"{_CALIBRATION_DATA_DIR}/20160735.csv"

# The author's validated calibration (docs/future_work.md item 3c), which is the
# configuration the measurement above was made under.
_PARAMS = dict(
    use_filter=True,
    cutoff_low=168,
    cutoff_high=18,
    replace_endpoints_with_lowpass=0,
    use_smoothing_twice=False,
    savgol_polynomial=3,
    boundary_padding="reflect",
)


@pytest.fixture(scope="module")
def series() -> pd.Series:
    df = pd.read_csv(_TRACK, sep=";", index_col="time", parse_dates=True)
    return df["min_max_zeta_850"]


def _process(series: pd.Series, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return process_vorticity(
            pd.DataFrame({"zeta": series.rename("zeta")}), **kwargs
        )


def _raw_derivatives(vort):
    """The derivatives as taken straight off ``vorticity_smoothed2``, i.e. with
    no Savgol applied to them at all."""
    dz_dt = vort.vorticity_smoothed2.differentiate("time", datetime_unit="h")
    dz_dt2 = dz_dt.differentiate("time", datetime_unit="h")
    return dz_dt.values, dz_dt2.values


def test_use_smoothing_false_leaves_derivatives_unfiltered(series):
    """The arrays find_stages consumes must be the unfiltered derivatives."""
    vort = _process(series, use_smoothing=False, **_PARAMS)
    dz_dt, dz_dt2 = _raw_derivatives(vort)

    # dz_dt_smoothed2 / dz_dt2_smoothed2 are what find_stages actually reads.
    np.testing.assert_allclose(vort.dz_dt_smoothed2.values, dz_dt, rtol=0, atol=0)
    np.testing.assert_allclose(vort.dz_dt2_smoothed2.values, dz_dt2, rtol=0, atol=0)

    # The single-pass arrays must be the same series, i.e. no second pass either.
    np.testing.assert_allclose(vort.dz_dt_filt.values, dz_dt, rtol=0, atol=0)
    np.testing.assert_allclose(vort.dz_dt2_filt.values, dz_dt2, rtol=0, atol=0)


def test_use_smoothing_false_still_skips_savgol_on_z(series):
    """Unchanged by this fix: False also means no smoothing of z itself."""
    vort = _process(series, use_smoothing=False, **_PARAMS)
    np.testing.assert_allclose(
        vort.vorticity_smoothed2.values, vort.filtered_vorticity.values, rtol=0, atol=0
    )


def test_edge_artifact_matches_the_documented_measurement():
    """Pins the headline numbers of docs/future_work.md item 4,
    "Measurement 2026-09-03", over the full 51-track calibration set.

    r(t0) = |dz_dt_smoothed2[0]| / max|dz_dt_smoothed2|, median over the set,
    under the author's validated calibration:

        auto window (15-91 steps, the old behaviour) : 0.545
        derivatives untouched (the new behaviour)    : 0.068

    The "old" column is reconstructed here by re-applying the two Savgol passes
    the previous code applied, rather than hard-coded, so the ~8x gap stays
    meaningful if the upstream filtering stage ever changes.  Both medians are
    asserted to two decimals; a single track's ratio is far noisier than the
    median and is not a useful pin (on 20160735 the gap is only 1.7x).
    """
    poly = _PARAMS["savgol_polynomial"]
    new_r0, old_r0 = [], []

    for path in sorted(glob.glob(f"{_CALIBRATION_DATA_DIR}/*.csv")):
        series = pd.read_csv(path, sep=";", index_col="time", parse_dates=True)[
            "min_max_zeta_850"
        ]
        vort = _process(series, use_smoothing=False, **_PARAMS)
        raw = vort.dz_dt_smoothed2.values

        # The window the old code picked when `not window_length_savgol` held.
        n = len(series)
        span = pd.Timedelta(series.index[-1] - series.index[0])
        window = (n // 4 | 1) if span > pd.Timedelta("8D") else (n // 2 | 1)
        smoothed = savgol_filter(raw, window, poly, mode="nearest")
        smoothed = savgol_filter(smoothed, window, poly, mode="nearest")

        new_r0.append(np.abs(raw)[0] / np.abs(raw).max())
        old_r0.append(np.abs(smoothed)[0] / np.abs(smoothed).max())

    assert len(new_r0) == 51
    assert round(float(np.median(new_r0)), 2) == 0.07   # documented 0.068
    assert round(float(np.median(old_r0)), 2) == 0.55   # documented 0.545


@pytest.mark.parametrize("use_smoothing", ["auto", 31])
def test_explicit_windows_and_auto_still_smooth_the_derivatives(series, use_smoothing):
    """The change is scoped to ``use_smoothing is False``; nothing else moves."""
    vort = _process(series, use_smoothing=use_smoothing, **_PARAMS)
    dz_dt, _ = _raw_derivatives(vort)
    assert not np.allclose(vort.dz_dt_smoothed2.values, dz_dt)


def test_other_falsy_values_are_not_treated_as_false(series):
    """The check is ``use_smoothing is False`` by identity, not truthiness.

    Two falsy-but-not-``False`` values, both pinned at their PRE-EXISTING
    behaviour (neither is endorsed as a sensible thing to pass -- they are here
    so that a future rewrite of the check as ``if not use_smoothing:`` fails
    loudly):

    * ``''`` -- never coerced to an int, so ``not window_length_savgol`` still
      holds and the derivatives are still smoothed with the *auto* window.
    * ``0`` -- coerced to a window of 1, then raised to ``savgol_polynomial``,
      which leaves ``savgol_filter(x, 3, 3)`` and a scipy ``ValueError``.
    """
    vort = _process(series, use_smoothing="", **_PARAMS)
    dz_dt, _ = _raw_derivatives(vort)
    assert not np.allclose(vort.dz_dt_smoothed2.values, dz_dt)

    with pytest.raises(ValueError, match="polyorder must be less than window_length"):
        _process(series, use_smoothing=0, **_PARAMS)
