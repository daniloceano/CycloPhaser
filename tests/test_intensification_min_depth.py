# Regression tests for the ``intensification_min_depth`` opt-in parameter.
#
# Background
# ----------
# Until this parameter existed, ``find_intensification_period`` accepted a
# candidate segment (a z_peak and the next z_valley) on DURATION alone:
# ``threshold_intensification_length`` was the only criterion, and nothing
# asked whether the segment actually deepened. A long, essentially flat stretch
# was therefore labelled intensification.
#
# That has a consequence several steps downstream. ``find_residual_period``
# converts an intensification block with no mature phase after it into
# 'residual' all the way to the end of the series. That rule is CORRECT -- it
# implements the project's physical definition of residual: deepening with no
# subsequent mature stage is outside the cyclone's life cycle (a transient
# interaction, or TRACK contamination). But fed a phantom intensification it
# faithfully writes a phantom residual, over a stretch the human label calls
# decay.
#
# ``intensification_min_depth`` (opt-in; default 0.0 reproduces prior behaviour
# exactly) supplies the missing criterion. A raw segment is accepted only when
#
#     D2 = (z[peak] - z[valley]) / (z_max - z_min)   >=  intensification_min_depth
#
# measured on the series' own ``df['z']``. Nothing in find_residual_period is
# touched: the spurious intensification simply stops existing, so the residual
# rule never fires on it, the tail is left unlabelled, and the preceding decay
# extends over it -- which is what the manual label asks for.
#
# Where the floor acts, and why the ORDER matters
# -----------------------------------------------
# The floor is applied PER RAW SEGMENT: after the duration test and BEFORE the
# gap stitching controlled by ``threshold_intensification_gap``. A stitched
# block's endpoints are the FIRST segment's peak and the LAST segment's valley,
# so its D2 is a property of the merged span and can be far smaller than either
# component segment's -- see ``test_floor_is_per_segment_not_per_stitched_block``,
# which builds exactly that configuration. Judging after the stitch would
# measure a different quantity from the one the parameter is defined on.
#
# Measured calibration (research/labels/diagnostics/frontC/)
# ----------------------------------------------------------
# Over the 47 TRAIN series, 75 raw segments clear the duration test. Exactly one
# falls below 0.15 -- 20180733's spurious segment, at D2 = 0.0068 -- and the
# smallest legitimate segment sits at 0.1714. Nothing lies between, so every
# floor in (0.0068, 0.1714] selects the same segments on that split. The
# reference value 0.05 (params-13) sits inside that gap.
#
# NOTE on 20180654: that series is in the FROZEN TEST SPLIT. It is exercised
# here because it is the second series the floor was designed for and Danilo
# authorised measuring and reporting it for this front specifically (a declared
# spend, recorded in docs/future_work.md). The threshold was chosen from the
# train split alone.

import glob
import os
import warnings

import numpy as np
import pandas as pd
import pytest

from cyclophaser.determine_periods import (determine_periods, find_peaks_valleys,
                                           get_periods, process_vorticity)
from cyclophaser.find_stages import find_intensification_period

_CALIBRATION_DATA_DIR = os.path.join(os.path.dirname(__file__), "calibration_data")

# params-13 = params-12 + intensification_min_depth. Kept in sync with
# research/labels/configs/cyclophaser_params-13.yaml by
# test_params13_yaml_matches_this_module.
_FILTER_PARAMS = dict(
    use_filter=True,
    cutoff_low=168,
    cutoff_high=18,
    replace_endpoints_with_lowpass=0,
    use_smoothing=False,
    use_smoothing_twice=False,
    savgol_polynomial=3,
    boundary_padding="edge",
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
    mature_amplitude_fraction=0.9,
    mature_min_depth=0.8,
    decay_tail_amplitude_fraction=0.3,
    incipient_plateau_tau=0.2,
    incipient_plateau_k=5,
    incipient_smooth_window=5.0,
    incipient_smooth_polyorder=3.0,
    length_scale="local",
    mature_method="amplitude",
    incipient_method="plateau",
    incipient_plateau_signal="vorticity",
    incipient_plateau_crossing="sustained",
)

# The params-13 reference value.
X = 0.05

# The two series the floor was designed to fix.
_CONVERT_CASES = ["20180733", "20180654"]

_ALL_TRACK_IDS = sorted(
    os.path.basename(f)[:-4] for f in glob.glob(f"{_CALIBRATION_DATA_DIR}/*.csv")
)


def _load_track(cyclone_id: str) -> pd.Series:
    path = f"{_CALIBRATION_DATA_DIR}/{cyclone_id}.csv"
    df = pd.read_csv(path, sep=";", index_col="time", parse_dates=True)
    return df["min_max_zeta_850"]


def _run(cyclone_id: str, intensification_min_depth=0.0) -> pd.DataFrame:
    series = _load_track(cyclone_id)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return determine_periods(
            series,
            **_FILTER_PARAMS,
            **_PHASE_PARAMS,
            intensification_min_depth=intensification_min_depth,
        )


def _runs(periods) -> list:
    """[(phase, first_idx, last_idx), ...] over a positional phase list."""
    names = [str(x) for x in periods]
    out, prev, start = [], None, 0
    for i, n in enumerate(names):
        if n != prev:
            if prev is not None:
                out.append((prev, start, i - 1))
            prev, start = n, i
    out.append((prev, start, len(names) - 1))
    return out


@pytest.fixture(scope="module")
def calibration_tracks():
    """Pre-computes (default, X=0.05) period DataFrames for every track once."""
    return {cid: (_run(cid, 0.0), _run(cid, X)) for cid in _ALL_TRACK_IDS}


# ── The default is a strict no-op ───────────────────────────────────────────────


def test_default_zero_matches_implicit_default():
    """Passing intensification_min_depth=0.0 explicitly must be byte-identical to
    not passing the parameter at all."""
    series = _load_track(_CONVERT_CASES[0])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_explicit = determine_periods(
            series, **_FILTER_PARAMS, **_PHASE_PARAMS, intensification_min_depth=0.0
        )
        df_implicit = determine_periods(series, **_FILTER_PARAMS, **_PHASE_PARAMS)
    pd.testing.assert_frame_equal(df_explicit, df_implicit)


def test_default_zero_changes_nothing_on_any_calibration_track(calibration_tracks):
    """Across the whole calibration set, the default must reproduce the previous
    behaviour on every track -- not merely on the two this front targets."""
    for cid in _ALL_TRACK_IDS:
        series = _load_track(cid)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            implicit = determine_periods(series, **_FILTER_PARAMS, **_PHASE_PARAMS)
            explicit = determine_periods(
                series, **_FILTER_PARAMS, **_PHASE_PARAMS, intensification_min_depth=0.0
            )
        pd.testing.assert_frame_equal(explicit, implicit, obj=cid)


# ── Validation ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("bad", [-0.1, -1e-9, 1.0000001, 1.5, 2.0])
def test_out_of_range_raises(bad):
    series = _load_track(_CONVERT_CASES[0])
    with pytest.raises(ValueError, match="intensification_min_depth"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            determine_periods(
                series, **_FILTER_PARAMS, **_PHASE_PARAMS,
                intensification_min_depth=bad,
            )


@pytest.mark.parametrize("ok", [0.0, 0.05, 0.5, 1.0])
def test_in_range_accepted(ok):
    """The endpoints of [0, 1] are valid -- a floor of exactly 1.0 is meaningful
    (only a segment spanning the entire z range qualifies)."""
    series = _load_track(_CONVERT_CASES[0])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        determine_periods(
            series, **_FILTER_PARAMS, **_PHASE_PARAMS, intensification_min_depth=ok
        )


# ── The two series the floor was designed for ──────────────────────────────────


@pytest.mark.parametrize("cyclone_id", _CONVERT_CASES)
def test_convert_cases_lose_spurious_residual(calibration_tracks, cyclone_id):
    """Under params-13 the phantom residual tail is gone and the series ends in
    'decay' -- the behaviour the manual label asks for."""
    before, after = calibration_tracks[cyclone_id]
    assert "residual" in set(before["periods"].astype(str)), (
        f"{cyclone_id} is supposed to HAVE a spurious residual at the default; "
        "if this fails the premise of the front has moved, not the fix"
    )
    assert "residual" not in set(after["periods"].astype(str))
    assert str(after["periods"].iloc[-1]) == "decay"


@pytest.mark.parametrize("cyclone_id", _CONVERT_CASES)
def test_convert_cases_only_the_residual_tail_becomes_decay(calibration_tracks, cyclone_id):
    """Every timestep that changes must be one that was 'residual' before and is
    'decay' after. Nothing else in the series may move -- in particular not the
    mature phase, which is the guarantee that the floor did not disturb the
    cycle it was not aimed at."""
    before, after = calibration_tracks[cyclone_id]
    b = before["periods"].astype(str).to_numpy()
    a = after["periods"].astype(str).to_numpy()
    changed = np.flatnonzero(b != a)
    assert len(changed) > 0
    assert set(b[changed]) == {"residual"}, set(b[changed])
    assert set(a[changed]) == {"decay"}, set(a[changed])
    # the mature block is untouched
    assert [i for i, x in enumerate(b) if x == "mature"] == \
           [i for i, x in enumerate(a) if x == "mature"]


def test_no_other_calibration_track_changes(calibration_tracks):
    """The floor at 0.05 must touch ONLY the two designed cases across the whole
    calibration set."""
    changed = [cid for cid in _ALL_TRACK_IDS
               if not calibration_tracks[cid][0]["periods"].astype(str)
                      .equals(calibration_tracks[cid][1]["periods"].astype(str))]
    assert sorted(changed) == sorted(_CONVERT_CASES), changed


def test_no_phase_loses_its_existence(calibration_tracks):
    """No track may lose a phase it previously had, except the spurious residual
    on the two designed cases. A floor that silently deleted a mature or an
    intensification phase elsewhere would be a regression the counts above
    could hide."""
    for cid in _ALL_TRACK_IDS:
        before, after = calibration_tracks[cid]
        lost = set(before["periods"].astype(str)) - set(after["periods"].astype(str))
        lost.discard("nan")
        if cid in _CONVERT_CASES:
            assert lost == {"residual"}, (cid, lost)
        else:
            assert not lost, (cid, lost)


# ── The floor acts per segment, not per stitched block ─────────────────────────


def _stitching_series():
    """A series whose STITCHED block has a far smaller D2 than either segment.

    Layout (index: z), built so that z is passed through unfiltered:

        10  peak    6.0  ┐ segment A: D2 = (6.0 - 1.0) / 10 = 0.50
        40  valley  1.0  ┘
                          gap of 5 steps -> stitched (< 0.075 * 119)
        45  peak   11.0  ┐ segment B: D2 = (11.0 - 5.5) / 10 = 0.55
        75  valley  5.5  ┘

    z range is 11.0 - 1.0 = 10.0, so the STITCHED block [10, 75] has
    D2 = (z[10] - z[75]) / 10 = (6.0 - 5.5) / 10 = 0.05 -- an order of magnitude
    below either segment. A floor of 0.20 therefore discriminates: applied per
    segment it accepts both (0.50, 0.55 >= 0.20); applied to the stitched block
    it would reject everything (0.05 < 0.20).

    No value is exactly 0: find_peaks_valleys marks zeros with the integer 0,
    which would overwrite the 'valley' marker at that index.
    """
    def ramp(a, b, n):
        return list(np.linspace(a, b, n, endpoint=False))

    vals = (ramp(3, 6, 10) + ramp(6, 1, 30) + ramp(1, 11, 5) +
            ramp(11, 5.5, 30) + ramp(5.5, 7, 44) + [7.0])
    idx = pd.date_range("2020-01-01", periods=len(vals), freq="1h", name="time")
    return pd.Series(vals, index=idx)


def _prepare(series):
    """Build the DataFrame find_intensification_period expects, the same way
    get_periods does, with filtering and smoothing off so z is the raw input."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": series}), use_filter=False,
                                 use_smoothing=False, use_smoothing_twice=False)
    df = vort.vorticity_smoothed2.to_dataframe().rename(
        columns={"vorticity_smoothed2": "z"})
    df["z_peaks_valleys"] = find_peaks_valleys(df["z"])
    df["periods"] = np.nan
    df["periods"] = df["periods"].astype("object")
    return df


def _intensification_blocks(df):
    mask = np.array([str(x) == "intensification" for x in df["periods"]])
    idx = np.flatnonzero(mask)
    if not len(idx):
        return []
    return [(int(b[0]), int(b[-1]))
            for b in np.split(idx, np.where(np.diff(idx) != 1)[0] + 1)]


def test_stitching_fixture_has_the_intended_geometry():
    """Guards the discriminating test below: if the extrema or the stitch move,
    that test stops testing what it claims to."""
    df = _prepare(_stitching_series())
    pos = {lab: i for i, lab in enumerate(df.index)}
    ext = [(pos[i], df.at[i, "z_peaks_valleys"], round(float(df.at[i, "z"]), 6))
           for i in df.index if df.at[i, "z_peaks_valleys"] in ("peak", "valley")]
    assert ext == [(0, "valley", 3.0), (10, "peak", 6.0), (40, "valley", 1.0),
                   (45, "peak", 11.0), (75, "valley", 5.5), (119, "peak", 7.0)], ext

    z = df["z"].to_numpy(float)
    z_range = z.max() - z.min()
    assert z_range == pytest.approx(10.0)
    assert (z[10] - z[40]) / z_range == pytest.approx(0.50)   # segment A
    assert (z[45] - z[75]) / z_range == pytest.approx(0.55)   # segment B
    assert (z[10] - z[75]) / z_range == pytest.approx(0.05)   # stitched block

    # the two segments really are stitched into one block at the default
    out = find_intensification_period(
        df.copy(), threshold_intensification_length=0.075,
        threshold_intensification_gap=0.075)
    assert _intensification_blocks(out) == [(10, 75)]


def test_floor_is_per_segment_not_per_stitched_block():
    """The discriminating test. With a floor of 0.20 both raw segments clear it
    (0.50, 0.55) while the stitched block does not (0.05). The block must
    survive -- proving the floor judged the segments, before the merge."""
    df = _prepare(_stitching_series())
    out = find_intensification_period(
        df.copy(), threshold_intensification_length=0.075,
        threshold_intensification_gap=0.075, intensification_min_depth=0.20)
    assert _intensification_blocks(out) == [(10, 75)]


def test_floor_is_per_segment_positive_control():
    """The control for the test above: a floor ABOVE both segments' D2 must
    reject them both. Without this, 'the block survived' could equally mean the
    parameter was never wired in."""
    df = _prepare(_stitching_series())
    out = find_intensification_period(
        df.copy(), threshold_intensification_length=0.075,
        threshold_intensification_gap=0.075, intensification_min_depth=0.60)
    assert _intensification_blocks(out) == []


def test_stitching_series_through_the_full_pipeline():
    """The same discrimination, end to end through get_periods rather than on
    find_intensification_period alone."""
    series = _stitching_series()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": series}), use_filter=False,
                                 use_smoothing=False, use_smoothing_twice=False)
        at_0 = get_periods(vort.copy(deep=True), intensification_min_depth=0.0)
        at_20 = get_periods(vort.copy(deep=True), intensification_min_depth=0.20)
        at_60 = get_periods(vort.copy(deep=True), intensification_min_depth=0.60)

    p0 = at_0["periods"].astype(str).to_numpy()
    p20 = at_20["periods"].astype(str).to_numpy()
    p60 = at_60["periods"].astype(str).to_numpy()
    # 0.20 leaves the merged block intact -> identical to the default
    assert (p0 == p20).all(), _runs(p20)
    # 0.60 rejects both segments -> intensification disappears entirely
    assert "intensification" in set(p0)
    assert "intensification" not in set(p60)


# ── Degenerate series ──────────────────────────────────────────────────────────


def test_zero_amplitude_series_warns_and_does_not_crash():
    """A flat series has no depth scale, so D2 is undefined. The floor must be
    skipped with a UserWarning rather than dividing by zero or silently
    ignoring the request."""
    idx = pd.date_range("2020-01-01", periods=60, freq="1h", name="time")
    flat = pd.Series(np.full(60, 3.0), index=idx)
    df = _prepare(flat)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = find_intensification_period(
            df.copy(), threshold_intensification_length=0.075,
            threshold_intensification_gap=0.075, intensification_min_depth=0.30)
    msgs = [str(w.message) for w in caught
            if issubclass(w.category, UserWarning)
            and "intensification_min_depth" in str(w.message)]
    assert msgs, [str(w.message) for w in caught]
    assert "NOT applied" in msgs[0]
    assert out is not None


def test_zero_amplitude_series_is_not_warned_about_at_the_default():
    """The warning is about a REQUESTED floor being skipped. At the default
    there is no request, so a flat series must stay silent."""
    idx = pd.date_range("2020-01-01", periods=60, freq="1h", name="time")
    flat = pd.Series(np.full(60, 3.0), index=idx)
    df = _prepare(flat)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        find_intensification_period(
            df.copy(), threshold_intensification_length=0.075,
            threshold_intensification_gap=0.075)
    assert not [w for w in caught if "intensification_min_depth" in str(w.message)]


# ── The config on disk agrees with this module ─────────────────────────────────


def test_params13_yaml_matches_this_module():
    """params-13 is the calibration reference for this parameter; if it drifts
    from the values exercised here, these tests stop describing it."""
    import yaml
    path = os.path.join(os.path.dirname(__file__), os.pardir, "research", "labels",
                        "configs", "cyclophaser_params-13.yaml")
    doc = yaml.safe_load(open(path))
    assert doc["phase_params"]["intensification_min_depth"] == X
    for key, value in _PHASE_PARAMS.items():
        assert doc["phase_params"][key] == value, key
    for key, value in _FILTER_PARAMS.items():
        assert doc["filter_params"][key] == value, key
