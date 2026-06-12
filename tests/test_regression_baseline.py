# Regression baselines — visually approved pre-bugfix (branch fix/core-bugs).
#
# Two cases are covered here:
#   - baseline_default:   determine_periods with all-default parameters.
#   - baseline_smoothing: use_filter=False, use_smoothing=11,
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
    result = _run_and_dict(series, x,
                           use_filter=False,
                           use_smoothing=11,
                           use_smoothing_twice=False)
    expected = _load_baseline("baseline_smoothing")
    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        expected.reset_index(drop=True),
        check_like=False,
    )
