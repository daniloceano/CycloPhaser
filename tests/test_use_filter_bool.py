# Tests for the ``use_filter=True`` bug fix.
#
# The bug
# -------
# ``process_vorticity`` picked the Lanczos window with::
#
#     if use_filter == 'auto': window = len(zeta_df) // 2
#     else:                    window = use_filter
#
# ``bool`` is a subclass of ``int`` in Python, so ``use_filter=True`` fell into
# the ``else`` branch and was read as the integer **1**.  ``pass_weights_bandpass``
# returns a single tap for a window of 1, so the "filter" became a scalar
# multiply (0.0714 for cutoff_low=168 / cutoff_high=24) -- no convolution at all.
# A caller asking for filtering silently received NONE, and the output differed
# from ``use_filter=False`` only by a constant factor that every downstream
# (difference-based) criterion cancels out.  This is what the calibration app's
# "Apply Lanczos filter" checkbox sent.
#
# The fix
# -------
# ``True`` now means ``'auto'`` (window ``len(series)//2``) and warns, so the
# user knows the window they got.  ``False`` still disables filtering.  An
# explicit integer is still a literal window length, and ``use_filter=1`` is no
# longer conflated with ``True`` -- the bool check runs BEFORE the int check,
# which is the whole point.
#
# These tests pin the four cases and the warning.  They deliberately assert on
# the WINDOW ACTUALLY USED (via the resulting kernel length / output), not on
# any internal variable, so they keep working if the selection logic is
# restructured.

import warnings

import numpy as np
import pandas as pd
import pytest

from cyclophaser.determine_periods import determine_periods, process_vorticity
from cyclophaser.lanczos_filter import pass_weights_bandpass

_FILTER_KW = dict(
    cutoff_low=168,
    cutoff_high=24,
    replace_endpoints_with_lowpass=0,
    use_smoothing=31,
    use_smoothing_twice=False,
    savgol_polynomial=3,
)


@pytest.fixture(scope="module")
def series() -> pd.Series:
    # 259 points, so len//2 == 129 and the 'auto' window is unambiguous.
    df = pd.read_csv(
        "tests/calibration_data/20160735.csv",
        sep=";",
        index_col="time",
        parse_dates=True,
    )
    return df["min_max_zeta_850"]


def _z(series: pd.Series, use_filter):
    """Smoothed vorticity for a given use_filter, with warnings suppressed."""
    zeta_df = pd.DataFrame({"zeta": series.rename("zeta")})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(zeta_df, use_filter=use_filter, **_FILTER_KW)
    return vort.vorticity_smoothed2.values


# ── The four cases ───────────────────────────────────────────────────────────

def test_true_is_equivalent_to_auto(series):
    """use_filter=True must give the same window as 'auto'."""
    np.testing.assert_array_equal(_z(series, True), _z(series, "auto"))


def test_true_matches_the_explicit_auto_window(series):
    """...and that window is len(series)//2, not some other default."""
    np.testing.assert_array_equal(_z(series, True), _z(series, len(series) // 2))


def test_false_skips_filtering(series):
    """use_filter=False must still bypass the filter entirely."""
    zeta_df = pd.DataFrame({"zeta": series.rename("zeta")})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(zeta_df, use_filter=False, **_FILTER_KW)
    # With filtering off, filtered_vorticity is the raw series verbatim.
    np.testing.assert_array_equal(vort.filtered_vorticity.values, series.values)
    assert not np.array_equal(_z(series, False), _z(series, "auto"))


@pytest.mark.parametrize("window", [5, 31, 64])
def test_integer_is_an_explicit_window_length(series, window):
    """An integer must still mean a literal window length."""
    got = _z(series, window)
    assert not np.array_equal(got, _z(series, "auto"))
    # It really is that window: a different integer gives a different result.
    assert not np.array_equal(got, _z(series, window + 2))


def test_integer_one_is_not_confused_with_true(series):
    """The ambiguous case: 1 and True must now be distinguishable.

    use_filter=1 keeps the literal 1-tap kernel (which is what True used to do
    by accident), while True routes to 'auto'.
    """
    one = _z(series, 1)
    assert not np.array_equal(one, _z(series, True))
    assert not np.array_equal(one, _z(series, "auto"))

    # A 1-tap kernel is a scalar multiply, so use_filter=1 is use_filter=False
    # times a constant -- this is precisely the degenerate behaviour the bug
    # produced, preserved here only for the caller who asks for it explicitly.
    ratio = one / _z(series, False)
    assert np.allclose(ratio, ratio[0], rtol=1e-9)
    assert len(pass_weights_bandpass(1, 1 / 168, 1 / 24)) == 1


# ── The warning ──────────────────────────────────────────────────────────────

def test_true_warns_and_names_the_window(series):
    zeta_df = pd.DataFrame({"zeta": series.rename("zeta")})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        process_vorticity(zeta_df, use_filter=True, **_FILTER_KW)
    msgs = [str(w.message) for w in caught if "use_filter=True" in str(w.message)]
    assert len(msgs) == 1, msgs
    assert str(len(series) // 2) in msgs[0]
    assert "'auto'" in msgs[0]


@pytest.mark.parametrize("use_filter", ["auto", False, 1, 31])
def test_other_values_do_not_warn(series, use_filter):
    zeta_df = pd.DataFrame({"zeta": series.rename("zeta")})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        process_vorticity(zeta_df, use_filter=use_filter, **_FILTER_KW)
    assert not [w for w in caught if "use_filter=True" in str(w.message)]


def test_warning_propagates_through_determine_periods(series):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        determine_periods(series, use_filter=True, **_FILTER_KW)
    assert [w for w in caught if "use_filter=True" in str(w.message)]


def test_end_to_end_true_equals_auto(series):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = determine_periods(series, use_filter=True, **_FILTER_KW)
        b = determine_periods(series, use_filter="auto", **_FILTER_KW)
    pd.testing.assert_frame_equal(a, b)
