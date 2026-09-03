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
"local", because "local" cannot differ from "global" there at all
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

Separately: the author confirmed against the real cyclone track database
(TRACK/Gramcianinov) that this input shape -- a decay this abrupt (D=14)
immediately after an intensification this long (It=280) -- does not occur in
real cyclones. Real declines are always at least moderately gradual; real
asymmetric cyclones (decay shorter than intensification, or the reverse) are
already detected correctly by the existing pipeline. So case (a) remains a
synthetic stress probe for `_local_cycle_scale`'s mathematics, not a data
pattern the method needs to support.

This test is therefore a SENTINEL for the global == local invariant, not a
target-behaviour check on the phases themselves. If 'global' and 'local' ever
diverge on this single-cycle input, `_local_cycle_scale`'s single-cycle
fallback changed and needs investigation.

UPDATE 2026-09 (branch research/boundary-artifacts) -- the 'mature' assertion
was inverted, with cause
--------------------------------------------------------------------------------
Until then this sentinel also locked in that 'mature' is ABSENT in both modes,
and read that absence as physical: the decay being too abrupt for the
mature/decay neighbour-confirmation invariant in `find_stages.find_mature_stage`
to confirm the mature window. That reading was wrong.

The absence was an ARTEFACT of ``replace_endpoints_with_lowpass``, which
overwrote the last 5 % of the series with a lowpass estimate. Here n=301, so
5 % is **15 timesteps** -- longer than the entire **14-timestep** decay segment.
The endpoint splice consumed the whole decay, and mature was then discarded for
lack of a successor 'decay' that was present in the original signal all along.
With ``replace_endpoints_with_lowpass=0`` (the new default; the parameter is
deprecated) the decay survives and 'mature' is correctly detected. Attribution
is unambiguous -- ``boundary_padding="zero"`` with
``replace_endpoints_with_lowpass=0`` already produces the full
incipient/intensification/mature/decay sequence, so ``boundary_padding`` is not
what changed this.

Detecting 'mature' here is NOT a claim that the D=14-after-It=280 shape is
physical. It only means nothing in the pipeline is destroying its decay before
the detection logic can see it. The mature/decay neighbour-confirmation
invariant itself is unchanged, and the global == local invariant held in all
four (boundary_padding x replace_endpoints_with_lowpass) combinations tested.
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
# NOTE: the comment below predates the 2026-09 finding that
# replace_endpoints_with_lowpass (5 % of n=301 = 15 steps) was consuming this
# case's entire 14-step decay segment. 'mature' IS now detected here; see the
# UPDATE block in the module docstring and in the test's own docstring.
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


def test_case_a_single_cycle_local_matches_global():
    """SENTINEL for `_local_cycle_scale`'s single-cycle fallback -- see module
    docstring.

    What this test guards, and has always guarded, is that 'local' and 'global'
    AGREE on a single-cycle series. 'local' cannot behave differently here in
    principle: with only one life cycle in the series, `_local_cycle_scale` has
    no other extremum to anchor to and falls back to the series boundary on both
    sides, so it numerically equals the 'global' series length. If the two ever
    diverge on this input, `_local_cycle_scale`'s single-cycle fallback changed
    and needs investigation.

    HISTORY -- why the 'mature' assertion was inverted (2026-09, branch
    research/boundary-artifacts)
    ---------------------------------------------------------------------------
    This sentinel originally asserted that 'mature' is ABSENT in both modes, and
    read that absence as a physical property: the D=14 decay is so abrupt after
    an It=280 intensification that the 'decay must literally follow mature'
    invariant in `find_stages.find_mature_stage` never confirms the mature
    window. The docstring warned against simply flipping the assertion.

    A later investigation showed the absence was an ARTEFACT of
    ``replace_endpoints_with_lowpass``, not a physical property. That option
    overwrote the last 5 % of the series with a lowpass estimate; for this case
    n=301, so 5 % is **15 timesteps** -- longer than the entire **14-timestep**
    decay segment. The endpoint splice therefore consumed the whole decay, and
    the mature window was then discarded by the mature/decay neighbour invariant
    for lack of a successor 'decay' that was present in the original signal all
    along.

    With ``replace_endpoints_with_lowpass=0`` (the new default; the parameter is
    now deprecated) the decay survives and 'mature' is correctly detected.
    Attribution is unambiguous: the change is driven by that option alone, not by
    ``boundary_padding`` -- ``boundary_padding="zero"`` with
    ``replace_endpoints_with_lowpass=0`` already yields the full
    incipient/intensification/mature/decay sequence.

    So the 'mature' assertion is inverted here deliberately and with cause. The
    global == local invariant below is unchanged and still locked: it held in all
    four (boundary_padding x replace_endpoints_with_lowpass) combinations tested,
    and it remains the point of this sentinel.

    NOTE on the module docstring's framing: the D=14-after-It=280 shape is still
    a synthetic stress probe that does not occur in real TRACK/Gramcianinov
    cyclones. Detecting 'mature' on it is not a claim that the shape is physical
    -- only that nothing in the pipeline is now destroying its decay before the
    detection logic can see it.
    """
    d_global = _run(_series_case_a, "global")
    d_local = _run(_series_case_a, "local")

    assert any(k.split()[0] == "mature" for k in d_global), (
        "'global' no longer detects mature on case A. Since "
        "replace_endpoints_with_lowpass went to 0 this segment's decay survives "
        "and mature should be confirmed; if it is absent again, something is "
        f"consuming the 14-step decay segment: {list(d_global.keys())}"
    )
    assert any(k.split()[0] == "mature" for k in d_local), (
        f"'local' no longer detects mature on case A: {list(d_local.keys())}"
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
