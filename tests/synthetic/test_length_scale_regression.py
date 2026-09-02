"""Regression tests for the ``length_scale`` opt-in parameter ("global" vs "local").

Background
----------
Five of the seven phase-detection thresholds (threshold_intensification_length,
threshold_intensification_gap, threshold_mature_length, threshold_decay_length,
threshold_decay_gap) are fractions of a *length*. With the default
``length_scale="global"`` that length is the whole input series
(df.index[-1] - df.index[0]) -- unchanged from all versions prior to this
option. With ``length_scale="local"`` each candidate segment is instead
checked against the span of the local oscillation it belongs to (see
``cyclophaser.find_stages._local_cycle_scale``).

This module documents two investigated scenarios and what "local" does and
does not fix for each. Both are permanent regression cases: they lock in the
*current* behaviour of both modes so a future change to either the threshold
logic or the smoothing pipeline is caught if it silently shifts these results.

Case (b) -- asymmetric two-cycle track -- IS fixed by "local"
---------------------------------------------------------------
A long first life cycle followed by a much shorter second one. Under "global",
every global-fraction threshold for cycle 2 is checked against a denominator
dominated by cycle 1, so cycle 2's intensification/mature/decay are all
rejected and the whole tail collapses into a single 'residual' block. Under
"local", each cycle is checked against its own span, and cycle 2's phases are
recovered.

Case (a) -- long intensification, short decay, SINGLE cycle -- is NOT fixed by
"local", and is NOT a target for correction at all
--------------------------------------------------------------------------------
This was the original motivating scenario for "local" mode (see the
research/adaptive-thresholds branch diagnostic history), but investigating it
with the real 'auto' smoothing pipeline (rather than the non-default manual
smoothing window used in an earlier ad-hoc diagnostic) revealed an important
mathematical property of `_local_cycle_scale`: for a series containing a
*single* life cycle, there is no other extremum beyond the ones bounding that
one cycle, so the "local" scale falls back to (and numerically equals) the
"global" series length. Local and global therefore agree exactly on a
single-cycle series, by construction -- "local" mode can only diverge from
"global" once a series has more structure than the one segment being checked.
It is fundamentally a fix for problem (b)-shaped scenarios (heterogeneity
*between* cycles), not for a disproportionate decay *within* a single cycle.

Separately, and decisively: the author confirmed against the real cyclone
track database (TRACK/Gramcianinov) that this input shape -- a decay this
abrupt (D=14) immediately after an intensification this long (It=280) -- does
not occur in real cyclones. Real declines are always at least moderately
gradual; real asymmetric cyclones (decay shorter than intensification, or the
reverse) are already detected correctly by the existing pipeline. So this
case is not a data pattern the method needs to support, and the absent
'mature' here is not a failure mode being tracked for a future fix -- with or
without "local" mode.

This test is therefore a SENTINEL, not a target-behaviour check: it locks in
that 'global' and 'local' currently agree exactly (mature absent, identical
period sequence) on this non-physical input. If it starts failing -- either
mode starts detecting 'mature', or the two modes diverge -- that signals an
unrelated change to `_local_cycle_scale` (find_stages.py) or to the
mature/decay neighbour-confirmation invariant (see the comment on that check
in `find_mature_stage`, find_stages.py: mature is only ever confirmed once a
'decay' is observed after it -- a physical requirement, not an incidental
implementation detail) worth investigating on its own terms. It does not mean
this test's assertions should simply be flipped to expect 'mature'.
"""

import warnings

import pandas as pd
import pytest

from cyclophaser.determine_periods import determine_periods, periods_to_dict

from .generators import make_lifecycle_series


def _run(series, length_scale):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = determine_periods(series, x=series.index, length_scale=length_scale)
    return periods_to_dict(df)


# ── Case (a): single-cycle long-intensification / short-decay -- NON-PHYSICAL ──
# Ic(3) It(280) M(4,plateau) D(14) -> 301 steps. Chosen (in an earlier diagnostic
# pass) to be structurally "clean": exactly 2 z_peaks / 2 z_valleys under the
# real default smoothing pipeline (no spurious extrema from the long-series
# 'auto' Savgol window), isolating the length_scale question from the
# unrelated, out-of-scope smoothing-artifact investigation.
#
# IMPORTANT: this D=14-after-It=280 shape (a decay that abrupt right after an
# intensification that long) does not occur in real cyclones in the TRACK/
# Gramcianinov database -- confirmed against real tracks, not just asserted.
# It exists here purely as a synthetic stress probe for length_scale's
# mathematical behaviour, not as a data pattern the method is expected to
# handle. See the module docstring for the full reasoning.
_SEG_CASE_A = [
    {"type": "Ic", "n": 3,   "shape": "plateau"},
    {"type": "It", "n": 280, "shape": "sine"},
    {"type": "M",  "n": 4,   "shape": "plateau"},
    {"type": "D",  "n": 14,  "shape": "sine"},
]
_series_case_a = make_lifecycle_series(_SEG_CASE_A, noise_frac=0.0)


def test_case_a_single_cycle_local_does_not_fix_and_matches_global():
    """SENTINEL, not a target-behaviour check -- see module docstring.

    This input (single life cycle, decay disproportionately short relative to
    a very long intensification) is a non-physical shape that does not occur
    in real cyclone tracks (confirmed against TRACK/Gramcianinov), so the
    absent 'mature' here is not a bug and not something either length_scale
    mode is expected to fix. 'local' cannot fix it in principle: with only one
    life cycle in the series, `_local_cycle_scale` has no other extremum to
    anchor to and falls back to the series boundary on both sides, so it
    numerically equals the 'global' series length -- local and global are
    mathematically forced to agree here.

    What this test guards is that mature stays absent (in both modes) *because
    decay never gets confirmed*, per the intentional, physically-motivated
    'decay must literally follow mature' check documented in
    find_mature_stage (find_stages.py) -- not because of some accidental
    global/local disagreement. If this test starts failing -- either mode
    starts detecting 'mature', or 'global' and 'local' diverge on this
    input -- treat it as a signal that `_local_cycle_scale`'s single-cycle
    fallback or the mature/decay neighbour check changed, and go find out why.
    Do not "fix" this test by just flipping the assertions to expect mature:
    that would mean the method started accepting a decay shape that real
    cyclones don't exhibit.
    """
    d_global = _run(_series_case_a, "global")
    d_local = _run(_series_case_a, "local")

    assert not any(k.split()[0] == "mature" for k in d_global), (
        f"'global' unexpectedly detected mature on a non-physical decay shape: "
        f"{list(d_global.keys())}"
    )
    assert not any(k.split()[0] == "mature" for k in d_local), (
        f"'local' unexpectedly detected mature -- local-scale normalization "
        f"cannot distinguish this from 'global' on a single-cycle series (see "
        f"docstring); if this now passes, _local_cycle_scale's single-cycle "
        f"fallback changed and needs investigation: {list(d_local.keys())}"
    )
    assert list(d_global.keys()) == list(d_local.keys()), (
        "global and local diverged on a single-cycle series, which should be "
        "mathematically impossible given _local_cycle_scale's single-cycle "
        f"fallback to the series boundary.\n  global: {list(d_global.keys())}\n"
        f"  local:  {list(d_local.keys())}"
    )


# ── Case (b): asymmetric two-cycle track ────────────────────────────────────────
# Cycle 1 (It=80, M=8, D=80) much larger than cycle 2 (It=20, M=3, D=20).
# 214 steps total. Both cycles individually survive the real default 'auto'
# smoothing window (unlike smaller variants tried during the diagnostic scan,
# where cycle 2 was smoothed away before any threshold logic even ran).
_SEG_CASE_B = [
    {"type": "Ic", "n": 3,   "shape": "plateau"},
    {"type": "It", "n": 80,  "shape": "sine"},
    {"type": "M",  "n": 8,   "shape": "plateau"},
    {"type": "D",  "n": 80,  "shape": "sine"},
    {"type": "It", "n": 20,  "shape": "sine"},
    {"type": "M",  "n": 3,   "shape": "plateau"},
    {"type": "D",  "n": 20,  "shape": "sine"},
]
_series_case_b = make_lifecycle_series(_SEG_CASE_B, noise_frac=0.02, seed=7)


def test_case_b_global_collapses_second_cycle():
    """'global' (default): cycle 2 has no surviving phases; it collapses into 'residual'."""
    d_global = _run(_series_case_b, "global")
    assert not any(k.startswith("intensification 2") for k in d_global)
    assert not any(k.startswith("mature 2") for k in d_global)
    assert not any(k.startswith("decay 2") for k in d_global)
    assert "residual" in d_global, (
        f"expected the swallowed cycle-2 tail to surface as 'residual': {list(d_global.keys())}"
    )


def test_case_b_local_recovers_second_cycle():
    """'local': all three cycle-2 phases are recovered instead of collapsing to residual."""
    d_local = _run(_series_case_b, "local")
    assert any(k.startswith("intensification 2") for k in d_local), list(d_local.keys())
    assert any(k.startswith("mature 2") for k in d_local), list(d_local.keys())
    assert any(k.startswith("decay 2") for k in d_local), list(d_local.keys())

    # Sanity: cycle-2 phases must be ordered and occur strictly after cycle 1's decay.
    decay1_end = d_local["decay"][1]
    it2_start = d_local["intensification 2"][0]
    m2_start = d_local["mature 2"][0]
    d2_start = d_local["decay 2"][0]
    assert decay1_end < it2_start < m2_start < d2_start, (
        f"cycle-2 phases out of order relative to cycle 1: "
        f"decay1_end={decay1_end} it2={it2_start} m2={m2_start} d2={d2_start}"
    )


def test_case_b_global_mode_unaffected_by_length_scale_option_existing():
    """Adding the length_scale parameter must not change 'global' output vs.
    calling determine_periods() without specifying it at all (implicit default)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_explicit = determine_periods(_series_case_b, x=_series_case_b.index, length_scale="global")
        df_implicit = determine_periods(_series_case_b, x=_series_case_b.index)
    pd.testing.assert_frame_equal(df_explicit, df_implicit)
