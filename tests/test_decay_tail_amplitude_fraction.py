# Regression tests for the ``decay_tail_amplitude_fraction`` opt-in parameter.
#
# Background
# ----------
# On a single-cycle series, ``find_peaks_valleys``' prominence filter computes
# peaks and valleys as two SEPARATE populations, each normalised by its own
# maximum. The largest interior PEAK therefore always scores a relative
# prominence of 1.0 BY CONSTRUCTION and survives ``prominence_relative``
# filtering no matter how small its prominence is in absolute terms, while the
# VALLEY of the same ripple -- normalised against the population containing the
# cycle's genuine, large main valley -- is correctly rejected. The result is an
# "orphan" interior z_peak with no surviving z_valley after it.
# ``find_decay_period`` marks decay only up to the next surviving z_peak, so
# this orphan peak truncates an otherwise continuous decay, and the remaining
# NaN tail is then labelled 'residual' by find_residual_period's catch-all rule
# -- even though nothing about the vorticity itself indicates a genuine
# re-intensification (research/adaptive-thresholds branch diagnostic; observed
# concretely on 20170409, declared 'residual' with 89.5% of peak intensity
# still present).
#
# ``decay_tail_amplitude_fraction`` (opt-in; default None reproduces prior
# behaviour exactly) fixes this WITHOUT touching ``z_peaks_valleys`` or any
# extrema detection: find_residual_period checks whether the NaN tail after
# the last decay block contains a genuine re-deepening (a drop below the
# tail's running-maximum z larger than this fraction of the cycle's own
# peak-to-valley amplitude) and, if not, extends 'decay' over the tail instead
# of leaving it for the catch-all to mark 'residual'. See
# ``cyclophaser.find_stages.find_residual_period`` for the full mechanism.
#
# This module locks in the author's validated calibration on the 51-track
# calibration set (tests/calibration_data/): decay_tail_amplitude_fraction=0.05
# sits in the middle of a confirmed safe window (0.0356, 0.0651] --
#   - CONVERTS residual-tailed to fully decayed: 20170409, 20150561, 20160030,
#     20180759, 20180654, 20203373, 20207822 (7 cases, all with a spurious
#     orphan-peak-truncated decay)
#   - PRESERVES residual (byte-identical to the default): 20180628, 20190325,
#     20191014 (genuine re-intensifications, not orphan-peak artifacts)
#   - touches NONE of the other 41 tracks in the set
#   - leaves the 'mature' phase byte-identical in every one of the 7 converted
#     cases -- the central guarantee of this approach over the discarded
#     alternative (dropping the orphan peak from z_peaks_valleys, which shifted
#     the mature window's amplitude reference and inflated its duration in all
#     7 cases; see the research/adaptive-thresholds branch diagnostic history).
#
# A future change to the smoothing pipeline, the prominence filter, or the
# residual/decay logic that shifts any of these results should fail this
# suite -- that is the point of locking them in here.

import glob
import os
import warnings

import pandas as pd
import pytest

from cyclophaser.determine_periods import determine_periods, periods_to_dict

_CALIBRATION_DATA_DIR = os.path.join(os.path.dirname(__file__), "calibration_data")

# Author's calibration (docs/future_work.md, "Amplitude-based mature-stage
# detection", 2026-09 entry): 7.8% bad cases (4/51) before this fix.
_FILTER_PARAMS = dict(
    use_filter=True,
    cutoff_low=168,
    cutoff_high=24,
    replace_endpoints_with_lowpass=0,
    use_smoothing=31,
    use_smoothing_twice=False,
    savgol_polynomial=3,
)
_PHASE_PARAMS = dict(
    threshold_intensification_length=0.075,
    threshold_intensification_gap=0.075,
    threshold_mature_distance=0.18,
    threshold_mature_length=0.15,
    threshold_decay_length=0.075,
    threshold_decay_gap=0.075,
    threshold_incipient_length=0.4,
    prominence_relative=0.3,
    distance=3,
    mature_amplitude_fraction=0.95,
    length_scale="local",
    mature_method="amplitude",
)

# Validated reference value: middle of the confirmed safe window (0.0356, 0.0651].
X = 0.05

_CONVERT_CASES = [
    "20170409",
    "20150561",
    "20160030",
    "20180759",
    "20180654",
    "20203373",
    "20207822",
]
_PRESERVE_CASES = ["20180628", "20190325", "20191014"]

_ALL_TRACK_IDS = sorted(
    os.path.basename(f)[:-4] for f in glob.glob(f"{_CALIBRATION_DATA_DIR}/*.csv")
)


def _load_track(cyclone_id: str) -> pd.Series:
    path = f"{_CALIBRATION_DATA_DIR}/{cyclone_id}.csv"
    df = pd.read_csv(path, sep=";", index_col="time", parse_dates=True)
    return df["min_max_zeta_850"]


def _run(cyclone_id: str, decay_tail_amplitude_fraction=None) -> pd.DataFrame:
    series = _load_track(cyclone_id)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return determine_periods(
            series,
            **_FILTER_PARAMS,
            **_PHASE_PARAMS,
            decay_tail_amplitude_fraction=decay_tail_amplitude_fraction,
        )


@pytest.fixture(scope="module")
def calibration_tracks():
    """Pre-computes (default, X=0.05) period DataFrames for every track once."""
    return {
        cid: (_run(cid, None), _run(cid, X))
        for cid in _ALL_TRACK_IDS
    }


# ── Default (None) is a strict no-op ────────────────────────────────────────────


def test_default_none_matches_implicit_default():
    """Passing decay_tail_amplitude_fraction=None explicitly must be byte-identical
    to not passing the parameter at all (implicit default)."""
    series = _load_track(_CONVERT_CASES[0])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_explicit = determine_periods(
            series, **_FILTER_PARAMS, **_PHASE_PARAMS, decay_tail_amplitude_fraction=None
        )
        df_implicit = determine_periods(series, **_FILTER_PARAMS, **_PHASE_PARAMS)
    pd.testing.assert_frame_equal(df_explicit, df_implicit)


def test_invalid_fraction_raises():
    series = _load_track(_CONVERT_CASES[0])
    for bad in (0.0, -0.1, 1.5):
        with pytest.raises(ValueError, match="decay_tail_amplitude_fraction"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                determine_periods(
                    series, **_FILTER_PARAMS, **_PHASE_PARAMS,
                    decay_tail_amplitude_fraction=bad,
                )


# ── The 7 cases with a spurious orphan-peak-truncated decay ────────────────────


@pytest.mark.parametrize("cyclone_id", _CONVERT_CASES)
def test_convert_cases_lose_residual_tail(calibration_tracks, cyclone_id):
    """With X=0.05, the spurious residual tail is absorbed into 'decay' --
    confirming both that 'residual' was present before, and gone after."""
    df_default, df_x = calibration_tracks[cyclone_id]

    d_default = periods_to_dict(df_default)
    d_x = periods_to_dict(df_x)

    assert "residual" in d_default, (
        f"{cyclone_id}: expected 'residual' in the default-parameter baseline "
        f"(regenerate this fixture if the upstream calibration changed): "
        f"{list(d_default.keys())}"
    )
    assert "residual" not in d_x, (
        f"{cyclone_id}: decay_tail_amplitude_fraction={X} should have absorbed "
        f"the residual tail into 'decay': {list(d_x.keys())}"
    )
    assert "decay" in d_x

    # The decay block must now run all the way to the series end.
    decay_end = d_x["decay"][1]
    assert decay_end == df_x.index[-1], (
        f"{cyclone_id}: expected decay to extend to the series end "
        f"({df_x.index[-1]}), got {decay_end}"
    )


@pytest.mark.parametrize("cyclone_id", _CONVERT_CASES)
def test_convert_cases_mature_phase_unchanged(calibration_tracks, cyclone_id):
    """Central guarantee of this approach: decay_tail_amplitude_fraction never
    touches z_peaks_valleys, so the 'mature' window (already computed before
    find_residual_period runs) must be byte-identical to the default -- unlike
    the discarded alternative of dropping the orphan peak from z_peaks_valleys,
    which shifted _amplitude_mature_bounds' decay-side amplitude reference and
    inflated the mature window's duration in all 7 of these cases."""
    df_default, df_x = calibration_tracks[cyclone_id]

    mature_default = df_default.loc[df_default["periods"] == "mature", "periods"]
    mature_x = df_x.loc[df_x["periods"] == "mature", "periods"]

    assert list(mature_default.index) == list(mature_x.index), (
        f"{cyclone_id}: mature phase shifted under decay_tail_amplitude_fraction="
        f"{X} -- expected byte-identical timestamps.\n"
        f"  default: {mature_default.index[0]} -> {mature_default.index[-1]}\n"
        f"  X={X}:    {mature_x.index[0] if len(mature_x) else None} -> "
        f"{mature_x.index[-1] if len(mature_x) else None}"
    )


@pytest.mark.parametrize("cyclone_id", _CONVERT_CASES)
def test_convert_cases_only_nan_tail_becomes_decay(calibration_tracks, cyclone_id):
    """Every OTHER phase (incipient, intensification, mature, and the decay
    block up to its original end) stays byte-identical -- only the trailing
    NaN/residual run changes to 'decay'."""
    df_default, df_x = calibration_tracks[cyclone_id]

    diff_mask = df_default["periods"] != df_x["periods"]
    changed_timestamps = df_default.index[diff_mask]

    # Every changed timestamp must have been 'residual' before and 'decay' after.
    assert (df_default.loc[changed_timestamps, "periods"] == "residual").all(), (
        f"{cyclone_id}: a non-residual timestep changed unexpectedly: "
        f"{df_default.loc[changed_timestamps, 'periods'].unique()}"
    )
    assert (df_x.loc[changed_timestamps, "periods"] == "decay").all(), (
        f"{cyclone_id}: a changed timestep did not become 'decay': "
        f"{df_x.loc[changed_timestamps, 'periods'].unique()}"
    )


# ── The 3 cases with a genuine re-intensification: must stay untouched ─────────


@pytest.mark.parametrize("cyclone_id", _PRESERVE_CASES)
def test_preserve_cases_byte_identical(calibration_tracks, cyclone_id):
    """These are genuine re-intensifications (not orphan-peak artifacts) and
    must remain classified as 'residual', byte-identical to the default."""
    df_default, df_x = calibration_tracks[cyclone_id]
    pd.testing.assert_series_equal(
        df_default["periods"], df_x["periods"],
        obj=f"{cyclone_id} periods (default vs decay_tail_amplitude_fraction={X})",
    )


# ── None of the other 51 tracks is touched ──────────────────────────────────────


def test_only_the_seven_convert_cases_change(calibration_tracks):
    """Across the full 51-track calibration set, decay_tail_amplitude_fraction=
    0.05 must change ONLY the 7 documented convert cases -- every other track
    (including the 3 explicit preserve cases) stays byte-identical."""
    changed = [
        cid
        for cid, (df_default, df_x) in calibration_tracks.items()
        if not df_default["periods"].equals(df_x["periods"])
    ]
    assert sorted(changed) == sorted(_CONVERT_CASES), (
        f"expected exactly {sorted(_CONVERT_CASES)} to change, got {sorted(changed)}"
    )
