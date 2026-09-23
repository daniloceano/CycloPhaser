"""Rule C2' — the type of the extremum at index 0 (``reclassify_index0``).

Index 0 is always an extremum: ``argrelextrema`` runs with ``mode='clip'`` and
non-strict comparators, so it compares ``data[0]`` against itself. Its type used
to come from the single difference ``data[1] - data[0]``. The rule replaces that
with a comparison against E1, the next extremum still standing in the final list
— taken whatever E1's own type is.

A structural fact that shapes every test here, and that is worth stating because
it is not obvious: **the rule can only fire when something has already removed
the extremum that would otherwise sit between index 0 and E1.** Raw
``argrelextrema`` output alternates, so the extremum right after a valley at
index 0 is a peak the series rose to, which cannot be below index 0; the
symmetric argument holds for a peak. The configurations the rule acts on are
therefore made by the prominence filter, and the firing tests below set them up
with ``prominence_relative`` rather than by hand. That is also what happens on
the real tracks: on ``20190639`` the filter deletes the valley at index 9 and
leaves two consecutive peaks.

Defaults are asymmetric on purpose and pinned here: ``find_peaks_valleys``
defaults to False (a direct caller keeps the historical behaviour),
``get_periods`` and ``determine_periods`` default to True (the pipeline applies
the rule). See front A / item 28 —
``research/labels/diagnostics/frontA_idx0_c2/REPORT.md``.
"""

import inspect
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cyclophaser.determine_periods import (
    _reclassify_index0, determine_periods, find_peaks_valleys, get_periods,
    process_vorticity,
)

_CALIB = Path(__file__).parent / "calibration_data"

# A valley at index 0 whose next SURVIVING extremum is a peak lying BELOW it:
# the series rises into a low-prominence bump, the filter removes that bump, and
# what remains after index 0 is the peak at index 3 (9.5 < 10.0). This is the
# shape of track 20180170 — and the case rule C2 (same front, stage 1) could not
# reach, because it demanded E1 share index 0's type.
VALLEY_THEN_LOWER_PEAK = [10.0, 10.1, 9.0, 9.5, 8.0, 9.0, 11.0]

# The mirror: a peak at index 0 whose next surviving extremum is a valley ABOVE
# it. This is 20190639's shape.
PEAK_THEN_HIGHER_VALLEY = [10.0, 9.9, 11.0, 10.5, 12.0, 11.0, 9.0]

# Nothing is removed here, so index 0's neighbour is the extremum it fell to.
PLAIN_ALTERNATION = [10.0, 9.0, 8.0, 7.0, 6.0, 8.0, 10.0]

FILTER = {"prominence_relative": 0.3}


def _types(series_values, **kwargs):
    """{position: 'peak'|'valley'} for a list of values."""
    out = find_peaks_valleys(pd.Series(np.asarray(series_values, dtype=float)),
                             **kwargs)
    return {i: t for i, t in enumerate(list(out)) if isinstance(t, str)}


# ── it fires, on both branches ───────────────────────────────────────────────

def test_valley_becomes_peak_when_the_next_extremum_is_strictly_deeper():
    before = _types(VALLEY_THEN_LOWER_PEAK, **FILTER)
    after = _types(VALLEY_THEN_LOWER_PEAK, reclassify_index0=True, **FILTER)

    assert before[0] == "valley"
    # E1 is a PEAK, and it is deeper than index 0 — the case C2 missed.
    e1 = min(i for i in before if i > 0)
    assert before[e1] == "peak"
    assert VALLEY_THEN_LOWER_PEAK[e1] < VALLEY_THEN_LOWER_PEAK[0]

    assert after[0] == "peak"


def test_peak_becomes_valley_when_the_next_extremum_is_strictly_higher():
    before = _types(PEAK_THEN_HIGHER_VALLEY, **FILTER)
    after = _types(PEAK_THEN_HIGHER_VALLEY, reclassify_index0=True, **FILTER)

    assert before[0] == "peak"
    e1 = min(i for i in before if i > 0)
    assert before[e1] == "valley"
    assert PEAK_THEN_HIGHER_VALLEY[e1] > PEAK_THEN_HIGHER_VALLEY[0]

    assert after[0] == "valley"


def test_only_index_zero_is_touched():
    """Every other extremum keeps its position and its type."""
    for values in (VALLEY_THEN_LOWER_PEAK, PEAK_THEN_HIGHER_VALLEY):
        before = _types(values, **FILTER)
        after = _types(values, reclassify_index0=True, **FILTER)
        assert set(before) == set(after), "an extremum was created or removed"
        assert {i: t for i, t in before.items() if i != 0} == \
               {i: t for i, t in after.items() if i != 0}


# ── it declines ──────────────────────────────────────────────────────────────

def test_does_not_fire_on_plain_alternation():
    """A peak at index 0 followed by the valley it fell to: nothing to fix."""
    before = _types(PLAIN_ALTERNATION, **FILTER)
    after = _types(PLAIN_ALTERNATION, reclassify_index0=True, **FILTER)
    assert before[0] == "peak"
    assert before == after


@pytest.mark.parametrize("kind", ["valley", "peak"])
def test_does_not_fire_on_a_tie(kind):
    """``data[E1] == data[0]`` is exactly what the boundary difference cannot
    resolve either; inventing an answer there would be the defect this rule
    exists to remove.

    Exercised on the rule itself rather than through ``find_peaks_valleys``: an
    exact tie between index 0 and its successor is easy to state and awkward to
    manufacture through the filter, and the filter is not what is under test."""
    data = np.array([10.0, 9.0, 8.0, 10.0, 7.0])  # data[3] == data[0]
    if kind == "valley":
        peaks, valleys = np.array([3]), np.array([0, 4])
    else:
        peaks, valleys = np.array([0, 3]), np.array([4])
    out_peaks, out_valleys = _reclassify_index0(data, peaks, valleys)
    np.testing.assert_array_equal(out_peaks, peaks)
    np.testing.assert_array_equal(out_valleys, valleys)


def test_does_not_fire_when_index_zero_has_no_successor():
    data = np.array([10.0, 9.0, 8.0])
    peaks, valleys = np.array([], dtype=int), np.array([0])
    out_peaks, out_valleys = _reclassify_index0(data, peaks, valleys)
    np.testing.assert_array_equal(out_peaks, peaks)
    np.testing.assert_array_equal(out_valleys, valleys)


def test_does_not_fire_when_index_zero_is_not_an_extremum():
    """A flat opening plateau collapses to its midpoint, so index 0 is absent
    from both lists and there is nothing to retype."""
    flat = [5.0, 5.0, 5.0, 5.0]
    assert _types(flat) == _types(flat, reclassify_index0=True)


def test_single_sample_series_is_left_alone():
    peaks, valleys = np.array([0]), np.array([0])
    out_peaks, out_valleys = _reclassify_index0(np.array([1.0]), peaks, valleys)
    np.testing.assert_array_equal(out_peaks, peaks)
    np.testing.assert_array_equal(out_valleys, valleys)


# ── the switch, and the defaults ─────────────────────────────────────────────

def test_false_reproduces_the_previous_behaviour_exactly():
    for values in (VALLEY_THEN_LOWER_PEAK, PEAK_THEN_HIGHER_VALLEY,
                   PLAIN_ALTERNATION):
        s = pd.Series(np.asarray(values, dtype=float))
        pd.testing.assert_series_equal(
            find_peaks_valleys(s, reclassify_index0=False, **FILTER),
            find_peaks_valleys(s, **FILTER))


def test_declared_defaults():
    """The asymmetry is the API decision of front A / item 28, not an accident."""
    assert inspect.signature(find_peaks_valleys).parameters[
        "reclassify_index0"].default is False
    assert inspect.signature(get_periods).parameters[
        "reclassify_index0"].default is True
    assert inspect.signature(determine_periods).parameters[
        "reclassify_index0"].default is True


# ── through the pipeline, on a real track ────────────────────────────────────

def _track(track_id):
    d = pd.read_csv(_CALIB / f"{track_id}.csv", sep=";", index_col="time",
                    parse_dates=True)
    return d["min_max_zeta_850"].astype("float64")


def _sequence(periods):
    seq, prev = [], None
    for v in periods.astype(str):
        if v != prev:
            seq.append(v)
            prev = v
    return seq


# params-13 — the calibration reference this rule was measured under.
PARAMS_13_PV = {"use_filter": True, "cutoff_low": 168, "cutoff_high": 18,
                "replace_endpoints_with_lowpass": 0, "use_smoothing": False,
                "use_smoothing_twice": False, "savgol_polynomial": 3,
                "boundary_padding": "edge"}
PARAMS_13_GP = {"threshold_intensification_length": 0.075,
                "threshold_intensification_gap": 0.075,
                "threshold_mature_distance": 0.18, "threshold_mature_length": 0.15,
                "threshold_decay_length": 0.075, "threshold_decay_gap": 0.075,
                "threshold_incipient_length": 0.4, "prominence_relative": 0.3,
                "mature_amplitude_fraction": 0.9, "mature_min_depth": 0.8,
                "intensification_min_depth": 0.05,
                "decay_tail_amplitude_fraction": 0.3,
                "incipient_plateau_tau": 0.2, "incipient_plateau_k": 5,
                "incipient_smooth_window": 5, "incipient_smooth_polyorder": 3,
                "length_scale": "local", "mature_method": "amplitude",
                "incipient_method": "plateau",
                "incipient_plateau_signal": "vorticity",
                "incipient_plateau_crossing": "sustained"}


def _run(track_id, **extra):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": _track(track_id)}),
                                 **PARAMS_13_PV)
        return get_periods(vort, **{**PARAMS_13_GP, **extra})


def test_20180170_loses_its_opening_decay_under_the_rule():
    """The measured anchor of the whole front: index 0 typed `valley` opened
    this life cycle with a `decay` the vorticity does not support."""
    off = _sequence(_run("20180170", reclassify_index0=False)["periods"])
    on = _sequence(_run("20180170", reclassify_index0=True)["periods"])
    assert off == ["incipient", "decay", "intensification", "mature", "decay"]
    assert on == ["incipient", "intensification", "mature", "decay"]


def test_the_rule_is_on_by_default_in_the_pipeline():
    default = _run("20180170")["periods"].astype(str).tolist()
    explicit = _run("20180170", reclassify_index0=True)["periods"].astype(str).tolist()
    assert default == explicit


def test_derivative_extrema_are_never_reclassified():
    """The rule is applied to z alone: no stage function reads index 0's type in
    dz or dz2, so retyping them would change only what the plots draw."""
    res = _run("20180170", reclassify_index0=True)
    for col, src in (("dz_peaks_valleys", "dz"), ("dz2_peaks_valleys", "dz2")):
        pd.testing.assert_series_equal(
            res[col], find_peaks_valleys(res[src]), check_names=False)
