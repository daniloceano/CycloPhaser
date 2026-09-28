# Regression baselines — visually approved pre-bugfix (branch fix/core-bugs).
#
# Two cases are covered here:
#   - baseline_default:   determine_periods with all-default parameters.
#   - baseline_smoothing: use_filter=False, use_smoothing=10,
#                         use_smoothing_twice=False.
#
# NOT covered here on purpose:
#   threshold_intensification_gap — this parameter is affected by bug #1
#   (find_stages.py:103 reads 'threshold_decay_length' instead of
#   'threshold_intensification_gap'), so any variation produces results
#   identical to the default right now.  A dedicated before/after visual
#   checkpoint will be run as part of the bug #1 fix, and its regression
#   baseline will be added at that point.

import warnings
import pandas as pd
import pytest

from cyclophaser import example_file
from cyclophaser.determine_periods import determine_periods, periods_to_dict

BASELINES_DIR = "tests/baselines"


def _load_baseline(name: str) -> pd.DataFrame:
    return pd.read_csv(f"{BASELINES_DIR}/{name}.csv")


def _run_and_dict(series, x, **kwargs) -> pd.DataFrame:
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        df = determine_periods(series, x=x, **kwargs)
    d = periods_to_dict(df)
    rows = [(ph, str(st), str(en)) for ph, (st, en) in d.items()]
    return pd.DataFrame(rows, columns=["phase", "start", "end"])


@pytest.fixture(scope="module")
def series_and_index():
    track = pd.read_csv(example_file, parse_dates=[0], delimiter=";", index_col=[0])
    return track["min_max_zeta_850"], track.index


def test_baseline_default(series_and_index):
    series, x = series_and_index
    result = _run_and_dict(series, x)
    expected = _load_baseline("baseline_default")
    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        expected.reset_index(drop=True),
        check_like=False,
    )


def test_baseline_smoothing(series_and_index):
    series, x = series_and_index
    kwargs = dict(use_filter=False, use_smoothing=10, use_smoothing_twice=False)

    # Verify that the window-coercion warning fires (use_smoothing=10 -> 11).
    # Call determine_periods directly so warnings aren't swallowed by _run_and_dict's inner context.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from cyclophaser.determine_periods import determine_periods
        determine_periods(series, x=x, **kwargs)
    adjustment_warnings = [w for w in caught if "adjusted" in str(w.message)]
    assert adjustment_warnings, "Expected UserWarning about window adjustment for use_smoothing=10"

    result = _run_and_dict(series, x, **kwargs)
    expected = _load_baseline("baseline_smoothing")
    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        expected.reset_index(drop=True),
        check_like=False,
    )


# ── Item 31: the 2.0.0 path, kept as a cross-version check ─────────────────────
# The package defaults moved to params-15 (item 31), so baseline_default /
# baseline_smoothing were regenerated under the new defaults. The 2.0.0 CSVs are
# kept as *_2_0_0.csv, and the 2.0.0 defaults — passed explicitly, from the
# frozen table — must still reproduce them.

import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from legacy_defaults import ALL_2_0_0  # noqa: E402


def test_baseline_default_2_0_0_path(series_and_index):
    series, x = series_and_index
    result = _run_and_dict(series, x, **ALL_2_0_0)
    expected = _load_baseline("baseline_default_2_0_0")
    pd.testing.assert_frame_equal(result.reset_index(drop=True),
                                  expected.reset_index(drop=True), check_like=False)


def test_baseline_smoothing_2_0_0_path(series_and_index):
    series, x = series_and_index
    kwargs = {**ALL_2_0_0, "use_filter": False, "use_smoothing": 10,
              "use_smoothing_twice": False}
    result = _run_and_dict(series, x, **kwargs)
    expected = _load_baseline("baseline_smoothing_2_0_0")
    pd.testing.assert_frame_equal(result.reset_index(drop=True),
                                  expected.reset_index(drop=True), check_like=False)
