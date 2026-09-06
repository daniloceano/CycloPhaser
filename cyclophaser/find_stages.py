import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

# ---------------------------------------------------------------------------
# length_scale: "global" (default) vs "local"
# ---------------------------------------------------------------------------
# Five of the seven detection thresholds (threshold_intensification_length,
# threshold_intensification_gap, threshold_mature_length, threshold_decay_length,
# threshold_decay_gap) are fractions multiplied by a *length* to get an absolute
# minimum/maximum duration. Historically that length was always
# `df.index[-1] - df.index[0]` — the GLOBAL span of the whole input series. The
# other two thresholds (threshold_mature_distance, threshold_incipient_length)
# were already fractions of a LOCAL span (the distance to the neighbouring
# z-extrema, or to the next dz extremum) rather than the global series length.
#
# Investigation on the research/adaptive-thresholds branch found this
# global/local inconsistency causes two related problems: (a) a long
# intensification phase inflates the global denominator, so a legitimately-short
# decay phase elsewhere in the *same* series can fail its own global-fraction
# threshold; (b) in a series containing two life-cycle-sized-differently cycles,
# every global threshold for the smaller cycle is checked against a denominator
# dominated by the larger one, so the smaller cycle's segments are rejected
# wholesale.
#
# `length_scale="local"` (opt-in; default remains "global" for exact backward
# compatibility) makes the five global thresholds behave like the two that were
# already local: each candidate segment is checked against the span of the
# *local* oscillation it belongs to, not the whole series. See
# `_local_cycle_scale` below for the precise definition used by
# find_intensification_period / find_decay_period, and the inline comment in
# find_mature_stage for the (slightly more specific, peak-to-peak) definition
# used there.
def _local_cycle_scale(df, seg_start, seg_end):
    """Local-scale denominator for a candidate segment [seg_start, seg_end].

    Defined as the distance between the nearest z-extremum (peak or valley)
    strictly *before* seg_start and the nearest z-extremum strictly *after*
    seg_end — i.e. the span of "one extremum out" on each side of the segment,
    which brackets the local up/down oscillation the segment is part of. When
    no such extremum exists on one side (segment touches a series boundary),
    that side falls back to the series boundary itself
    (df.index[0] / df.index[-1]).

    This fallback has a useful property: for a series containing a single
    cycle, there are no further extrema beyond the ones bounding that cycle,
    so both sides fall back to the series boundaries and the local scale
    reduces to the *global* series length — i.e. "local" and "global" modes
    agree exactly on a single-cycle series, and only diverge once a series
    contains more structure (multiple cycles, or a segment far from the series
    edges) than the candidate segment itself.

    Args:
        df: DataFrame with a 'z_peaks_valleys' column ('peak'/'valley'/0/NaN).
        seg_start: Start timestamp of the candidate segment (normally itself
            a z-extremum, e.g. the z_peak that starts an intensification leg).
        seg_end: End timestamp of the candidate segment.

    Returns:
        pd.Timedelta: the local cycle scale.
    """
    extrema = df[df['z_peaks_valleys'].isin(['peak', 'valley'])].index
    before = extrema[extrema < seg_start]
    after = extrema[extrema > seg_end]
    left = before[-1] if len(before) else df.index[0]
    right = after[0] if len(after) else df.index[-1]
    return right - left


def _amplitude_mature_bounds(df, previous_z_peak, z_valley, next_z_peak, mature_amplitude_fraction):
    """Amplitude-based mature window around a single z_valley (vorticity extremum).

    Used by find_mature_stage when mature_method="amplitude". Defines the mature
    window as the CONTIGUOUS stretch of z around z_valley that stays within
    ``mature_amplitude_fraction`` of the cycle's amplitude — i.e. "still at least
    X% as intense as the peak" — rather than a fixed proportion of the *time*
    distance to the neighbouring z_peak (that's the "derivative"/default method,
    which anchors on dz extrema and can drift off-centre when the smoothed
    derivative lags the true z minimum; see the mature_method note in
    get_periods).

    Amplitude reference (IMPORTANT — do not use z_valley's absolute value):
    vorticity has a non-zero floor, so "80% of the extreme value" is not a
    meaningful fraction on its own (same reasoning as prominence_relative in
    find_peaks_valleys). Instead the amplitude is measured relative to the
    z_peak that bounds the cycle on each side — the peak-to-valley drop —
    exactly like the previous/next z_peak pair the default method already uses
    to size its window via threshold_mature_distance:

        amplitude_prev = z[previous_z_peak] - z[z_valley]   (intensification side)
        amplitude_next = z[next_z_peak]     - z[z_valley]   (decay side)

    The two sides are treated independently (own amplitude, own level, own
    contiguous walk) rather than pooled into one symmetric amplitude, matching
    the existing per-side treatment of threshold_mature_distance and avoiding
    a single lopsided reference when the two bounding peaks differ in height.

    For each side, the level a timestep's z must stay at or below to still
    count as "mature" is:

        level_prev = z[previous_z_peak] - mature_amplitude_fraction * amplitude_prev
        level_next = z[next_z_peak]     - mature_amplitude_fraction * amplitude_next

    mature_amplitude_fraction -> 1 shrinks the level toward z[z_valley] itself
    (narrow window, only the very peak of intensity); -> 0 widens it toward the
    bounding peak's own value (the whole intensification/decay leg counts).
    The window is walked outward from z_valley and stops at the first timestep
    that violates the level on that side (kept CONTIGUOUS on purpose — a
    momentary z excursion back above the level should not extend the window
    past it), falling back to the bounding peak itself if the whole leg
    qualifies.

    Interaction with length_scale / threshold_mature_length: NONE — this window
    is the final mature window as-is. threshold_mature_length (a MINIMUM
    DURATION check, itself a fraction of length_scale) is a rule for the
    "derivative" method's fixed-time-proportion window and does not apply
    here; the caller (find_mature_stage) skips that check entirely for
    mature_method="amplitude", by design (see the threshold_mature_length /
    mature_method interaction note in find_mature_stage's docstring). The
    window returned here is accepted purely on the strength of its own
    amplitude-based definition — a narrow window is not evidence of a defect
    to filter out, it is a direct, physically meaningful consequence of
    mature_amplitude_fraction.

    Args:
        df: DataFrame with a 'z' column (smoothed vorticity).
        previous_z_peak, next_z_peak: Timestamps of the z_peaks bounding this
            z_valley (already located by the caller).
        z_valley: Timestamp of the candidate mature z_valley.
        mature_amplitude_fraction: float in (0, 1]. Fraction of each side's
            peak-to-valley amplitude that must still be "covered" for a
            timestep to count as mature.

    Returns:
        (mature_start, mature_end): Timestamps bounding the contiguous window.
    """
    z_at_valley = df.at[z_valley, 'z']
    z_at_prev_peak = df.at[previous_z_peak, 'z']
    z_at_next_peak = df.at[next_z_peak, 'z']

    amplitude_prev = z_at_prev_peak - z_at_valley
    amplitude_next = z_at_next_peak - z_at_valley

    level_prev = z_at_prev_peak - mature_amplitude_fraction * amplitude_prev
    level_next = z_at_next_peak - mature_amplitude_fraction * amplitude_next

    # Backward extension (intensification side): walk from z_valley toward
    # previous_z_peak; keep the contiguous run (ending at z_valley) whose z
    # stays at or below level_prev.
    seg_prev = df.loc[previous_z_peak:z_valley, 'z']
    violations_prev = np.where(seg_prev.values > level_prev)[0]
    mature_start = seg_prev.index[violations_prev[-1] + 1] if len(violations_prev) else previous_z_peak

    # Forward extension (decay side): walk from z_valley toward next_z_peak;
    # keep the contiguous run (starting at z_valley) whose z stays at or below
    # level_next.
    seg_next = df.loc[z_valley:next_z_peak, 'z']
    violations_next = np.where(seg_next.values > level_next)[0]
    mature_end = seg_next.index[violations_next[0] - 1] if len(violations_next) else next_z_peak

    return mature_start, mature_end


def find_mature_stage(df, **args_periods):

    """
    Identifies and marks the mature stage in the cyclone life cycle.

    Two mutually exclusive detection methods are available via 'mature_method':

    - "derivative" (default, unchanged behaviour): the mature window is a fixed
      proportion (threshold_mature_distance) of the *time* distance between the
      z_valley and each neighbouring z_peak. This is the original method.
    - "amplitude" (opt-in): the mature window is the contiguous stretch of z
      around the z_valley that stays within mature_amplitude_fraction of the
      cycle's peak-to-valley amplitude on each side. See
      _amplitude_mature_bounds for the full definition and rationale (fixes a
      forward displacement of the mature window observed with "derivative" on
      some real cyclones, caused by smoothed-derivative phase lag — this method
      anchors on z's own amplitude instead, which does not lag).

    Args:
        df (pd.DataFrame): DataFrame containing vorticity data with columns for
            'z_peaks_valleys' and 'periods'.
        **args_periods: Variable length argument list containing period-specific
            thresholds, including:
            - 'mature_method' (str, optional): "derivative" (default) or
              "amplitude". See above.
            - 'threshold_mature_distance' (float): Factor to calculate mature
              start and end distances from z valleys. Already a LOCAL fraction
              (of the distance to the neighbouring z peaks); unaffected by
              'length_scale'. Only used when mature_method="derivative".
            - 'mature_amplitude_fraction' (float, optional): Fraction (0, 1] of
              each side's peak-to-valley amplitude a timestep's z must still
              reach to count as mature. Default 0.90. Only used when
              mature_method="amplitude".
            - 'threshold_mature_length' (float): Minimum length for a mature
              stage, as a fraction of a length that depends on 'length_scale'.
              Only used when mature_method="derivative" — see the note below.
            - 'length_scale' (str, optional): Only relevant when
              mature_method="derivative" (see note below). 'global' (default)
              measures threshold_mature_length against the whole series length
              (df.index[-1]-df.index[0]), matching all versions prior to this
              option. 'local' measures it against the span between the z_peak
              immediately before and immediately after the candidate mature
              z_valley — i.e. the same previous/next z_peak pair already used
              to size the mature window, so the length check and the window it
              is checking are evaluated on the same local scale.

    threshold_mature_length / mature_method interaction:
        threshold_mature_length is applied ONLY when mature_method="derivative".
        In "amplitude" mode it has NO effect whatsoever — deliberately, not an
        oversight. threshold_mature_length is a minimum-DURATION rule
        calibrated for "derivative"'s fixed time-proportion window; in
        "amplitude" the window's duration is already a direct physical
        consequence of mature_amplitude_fraction (how long z stays within that
        fraction of the cycle's amplitude), so a narrow-but-well-centred window
        is valid on its own terms, not a candidate to discard for being short.
        Reusing a duration floor tuned for the other method was observed
        (20160030, research/adaptive-thresholds branch) to discard a
        well-centred amplitude window for being ~1h short of a
        threshold_mature_length value tuned for "derivative". No replacement
        minimum-duration safeguard (not even a small technical floor) has been
        introduced for "amplitude" — this is intentional, to evaluate the
        method "pure" first; revisit only if calibration surfaces spurious,
        very short amplitude windows. The neighbour-confirmation invariant
        below (mature must be bounded by intensification/decay) is unrelated
        to threshold_mature_length and still applies in both modes.

    Returns:
        pd.DataFrame: Updated DataFrame with 'mature' stages marked in the
        'periods' column where applicable.
    """
    threshold_mature_distance = args_periods['threshold_mature_distance']
    threshold_mature_length = args_periods['threshold_mature_length']
    length_scale = args_periods.get('length_scale', 'global')
    mature_method = args_periods.get('mature_method', 'derivative')
    mature_amplitude_fraction = args_periods.get('mature_amplitude_fraction', 0.90)

    if mature_method not in ('derivative', 'amplitude'):
        raise ValueError(f"mature_method must be 'derivative' or 'amplitude', got {mature_method!r}.")
    if mature_method == 'amplitude' and not (0 < mature_amplitude_fraction <= 1):
        raise ValueError(
            f"mature_amplitude_fraction must be in (0, 1], got {mature_amplitude_fraction!r}."
        )

    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index

    series_length = df.index[-1] - df.index[0]
    dt = df.index[1] - df.index[0]

    # Iterate over z valleys
    for z_valley in z_valleys:

        # Find the previous and next dz valleys relative to the current z valley
        next_z_peak = z_peaks[z_peaks > z_valley]
        previous_z_peak =  z_peaks[z_peaks < z_valley]

        # Check if there is a previous or next z_peak
        if len(previous_z_peak) == 0 or len(next_z_peak) == 0:
            continue

        previous_z_peak = previous_z_peak[-1]
        next_z_peak = next_z_peak[0]

        if mature_method == 'amplitude':
            mature_start, mature_end = _amplitude_mature_bounds(
                df, previous_z_peak, z_valley, next_z_peak, mature_amplitude_fraction)
        else:
            # Calculate the distances between z valley and the previous/next dz valleys
            distance_to_previous_z_peak = z_valley - previous_z_peak
            distance_to_next_z_peak = next_z_peak - z_valley

            # Calculate the mature stage start and end
            mature_distance_previous = distance_to_previous_z_peak * threshold_mature_distance
            mature_distance_next = distance_to_next_z_peak * threshold_mature_distance

            mature_start = z_valley - mature_distance_previous
            mature_end = z_valley + mature_distance_next

        mature_indexes = df.loc[mature_start:mature_end].index

        if len(mature_indexes) == 0:
            continue

        if mature_method == 'amplitude':
            # threshold_mature_length is a minimum-DURATION rule that was
            # calibrated for "derivative"'s time-proportion window. It does
            # not apply here: in "amplitude", the window's extent is already
            # a direct physical consequence of mature_amplitude_fraction (how
            # long z stays within that fraction of the cycle's amplitude), so
            # a narrow-but-well-centred window is a valid result on its own
            # merits, not something to discard for being short. Applying a
            # duration floor calibrated for a different window-sizing method
            # was observed (20160030, research/adaptive-thresholds branch) to
            # discard a well-centred amplitude window for being ~1h too short
            # under threshold_mature_length values tuned for "derivative".
            # Deliberately no replacement minimum here (not even a small
            # technical floor) -- see the mature_method note in
            # determine_periods.get_periods for why, and revisit only if
            # calibration surfaces spurious very-short amplitude windows.
            df.loc[mature_start:mature_end, 'periods'] = 'mature'
        else:
            # Mature stage needs to be at least 3% of the length_scale
            # ('global': whole series; 'local': this valley's own
            # previous_z_peak -> next_z_peak span, i.e. the same pair used
            # above to size the window).
            mature_length_scale = (next_z_peak - previous_z_peak) if length_scale == 'local' else series_length
            if mature_indexes[-1] - mature_indexes[0] > threshold_mature_length * mature_length_scale:
                # Fill the period between mature_start and mature_end with 'mature'
                df.loc[mature_start:mature_end, 'periods'] = 'mature'

    # Check if all mature stages are preceded by an intensification and followed by decay.
    #
    # Both neighbour requirements are intentionally strict, including requiring a
    # literal 'decay' successor (not merely "not intensification"). This is a
    # physical requirement, not an incidental implementation detail: a candidate
    # mature window can only be *confirmed* as mature if the cyclone is
    # subsequently observed to decay. Without that confirmation (e.g. the record
    # ends right after the candidate window, or the following segment is
    # unclassified/NaN), there is no basis to trust that the vorticity plateau was
    # genuinely the storm's peak rather than a transient pause, a filtering
    # artifact, or a life cycle still in progress.
    #
    # Investigated 2026-07 (research/adaptive-thresholds branch): a long
    # intensification phase can inflate the *global* series length that
    # threshold_decay_length is measured against (see find_decay_period), causing
    # a legitimate following decay segment to fail its own threshold and never be
    # labelled 'decay' — which in turn makes this check discard an otherwise
    # locally-valid mature window. Relaxing this check to accept a non-'decay'
    # (e.g. NaN) successor was tried and reverted: it does not actually recover
    # the mature window end-to-end (find_residual_period has its own, separate
    # "mature must be followed by decay" assumption a few steps later in the
    # pipeline, and relaxing only one of the two produces worse output — it can
    # erase the surrounding intensification block too). The correct fix for the
    # underlying cause is to make threshold_decay_length (and the other
    # global-fraction thresholds) scale to the local cycle instead of the total
    # series length, not to loosen this confirmation requirement.
    mature_periods = df[df['periods'] == 'mature'].index
    if len(mature_periods) > 0:
        blocks = np.split(mature_periods, np.where(np.diff(mature_periods) != dt)[0] + 1)
        for block in blocks:
            block_start, block_end = block[0], block[-1]
            prev_idx = block_start - dt
            next_idx = block_end + dt
            # A mature block at the series boundary cannot have required neighbours —
            # treat missing neighbour as "condition not satisfied" and clear the block.
            if prev_idx not in df.index or next_idx not in df.index or \
               df.loc[prev_idx, 'periods'] != 'intensification' or \
               df.loc[next_idx, 'periods'] != 'decay':
                df.loc[block_start:block_end, 'periods'] = np.nan

    return df

def find_intensification_period(df, **args_periods):

    """
    Identifies and marks the intensification period in the cyclone life cycle 
    based on the given thresholds for intensification length and gap.

    Args:
        df (pd.DataFrame): DataFrame containing vorticity data with columns
            for 'z_peaks_valleys' and 'periods'.
        **args_periods: Variable length argument list containing period-specific
            thresholds, including:
            - 'threshold_intensification_length' (float): Minimum length for an
              intensification stage, as a fraction of a length that depends on
              'length_scale'.
            - 'threshold_intensification_gap' (float): Maximum gap allowed
              between consecutive intensification periods, as a fraction of a
              length that depends on 'length_scale'.
            - 'length_scale' (str, optional): 'global' (default) measures both
              thresholds above against the whole series length
              (df.index[-1]-df.index[0]), matching all versions prior to this
              option. 'local' measures each candidate segment/gap against
              `_local_cycle_scale`: the span between the nearest z-extremum
              before it and the nearest z-extremum after it (falling back to
              the series boundary where no such extremum exists).

    Returns:
        pd.DataFrame: Updated DataFrame with 'intensification' stages marked in the
        'periods' column where applicable.
    """
    threshold_intensification_length = args_periods['threshold_intensification_length']
    threshold_intensification_gap = args_periods['threshold_intensification_gap']
    length_scale = args_periods.get('length_scale', 'global')

    # Find z peaks and valleys
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index
    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index

    length = df.index[-1] - df.index[0]
    dt = df.index[1] - df.index[0]

    # Find intensification periods between z peaks and valleys
    for z_peak in z_peaks:
        next_z_valley = z_valleys[z_valleys > z_peak].min()
        if not pd.isna(next_z_valley):
            intensification_start = z_peak
            intensification_end = next_z_valley

            # Intensification needs to meet the minimum length threshold
            # (fraction of the series length, or of the local cycle scale).
            scale = (_local_cycle_scale(df, intensification_start, intensification_end)
                     if length_scale == 'local' else length)
            if intensification_end-intensification_start > scale * threshold_intensification_length:
                df.loc[intensification_start:intensification_end, 'periods'] = 'intensification'

    # Check if there are multiple blocks of consecutive intensification periods
    intensefication_periods = df[df['periods'] == 'intensification'].index
    blocks = np.split(intensefication_periods, np.where(np.diff(intensefication_periods) != dt)[0] + 1)

    for i in range(len(blocks) - 1):
        block_end = blocks[i][-1]
        next_block_start = blocks[i+1][0]
        gap = next_block_start - block_end

        # If the gap between blocks is smaller than the threshold, fill with
        # intensification (fraction of the series length, or of the local
        # cycle scale spanning the gap itself).
        gap_scale = (_local_cycle_scale(df, block_end, next_block_start)
                     if length_scale == 'local' else length)
        if gap < gap_scale * threshold_intensification_gap:
            df.loc[block_end:next_block_start, 'periods'] = 'intensification'

    return df

def find_decay_period(df, **args_periods):

    """
    Identifies and marks the decay stage in the cyclone life cycle based on the 
    given thresholds for decay length and gap.

    Args:
        df (pd.DataFrame): DataFrame containing vorticity data with columns for
            'z_peaks_valleys' and 'periods'.
        **args_periods: Variable length argument list containing period-specific
            thresholds, including:
            - 'threshold_decay_length' (float): Minimum decay length, as a
              fraction of a length that depends on 'length_scale'.
            - 'threshold_decay_gap' (float): Maximum gap in decay periods, as a
              fraction of a length that depends on 'length_scale'.
            - 'length_scale' (str, optional): 'global' (default) measures both
              thresholds above against the whole series length
              (df.index[-1]-df.index[0]), matching all versions prior to this
              option. 'local' measures each candidate segment/gap against
              `_local_cycle_scale`: the span between the nearest z-extremum
              before it and the nearest z-extremum after it (falling back to
              the series boundary where no such extremum exists).

    Returns:
        pd.DataFrame: Updated DataFrame with 'decay' stages marked in the
        'periods' column where applicable.
    """
    threshold_decay_length = args_periods['threshold_decay_length']
    threshold_decay_gap = args_periods['threshold_decay_gap']
    length_scale = args_periods.get('length_scale', 'global')

    # Find z peaks and valleys
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index
    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index

    length = df.index[-1] - df.index[0]
    dt = df.index[1] - df.index[0]

    # Find decay periods between z valleys and peaks
    for z_valley in z_valleys:
        next_z_peak = z_peaks[z_peaks > z_valley].min()
        if not pd.isna(next_z_peak):
            decay_start = z_valley
            decay_end = next_z_peak
        else:
            decay_start = z_valley
            decay_end = df.index[-1]  # Last index of the DataFrame

        # Decay needs to meet the minimum length threshold (fraction of the
        # series length, or of the local cycle scale).
        scale = (_local_cycle_scale(df, decay_start, decay_end)
                 if length_scale == 'local' else length)
        if decay_end - decay_start > scale * threshold_decay_length:
            df.loc[decay_start:decay_end, 'periods'] = 'decay'

    # Check if there are multiple blocks of consecutive decay periods
    decay_periods = df[df['periods'] == 'decay'].index
    blocks = np.split(decay_periods, np.where(np.diff(decay_periods) != dt)[0] + 1)

    for i in range(len(blocks) - 1):
        block_end = blocks[i][-1]
        next_block_start = blocks[i+1][0]
        gap = next_block_start - block_end

        # If the gap between blocks is smaller than the threshold, fill with
        # decay (fraction of the series length, or of the local cycle scale
        # spanning the gap itself).
        gap_scale = (_local_cycle_scale(df, block_end, next_block_start)
                     if length_scale == 'local' else length)
        if gap < gap_scale * threshold_decay_gap:
            df.loc[block_end:next_block_start, 'periods'] = 'decay'

    return df

def find_residual_period(df, **args_periods):
    """
    Identifies and fills the 'residual' period in the cyclone life cycle stages where applicable.

    This function analyzes the 'periods' column in the provided DataFrame and marks
    the NaN values with 'residual' in specific conditions. If there is only one unique
    phase present, it fills NaNs after the last block of this phase with 'residual'.
    For multiple phases, it checks the sequence of phases and determines where 'residual'
    should be applied, particularly after mature and intensification stages if no subsequent
    decay or mature stages are detected.

    'decay_tail_amplitude_fraction' note (opt-in, default None: no effect)
    ------------------------------------------------------------------------
    The catch-all rule that fills the NaN tail after the last 'decay' block with
    'residual' (below) can be triggered by an artifact rather than a genuine
    re-intensification: on a single-cycle series, ``find_peaks_valleys``'
    prominence filter computes peaks and valleys as two SEPARATE populations,
    each normalised by its own maximum. The largest interior PEAK therefore
    always scores a relative prominence of 1.0 BY CONSTRUCTION (it is the max
    of its own population) and survives ``prominence_relative`` filtering no
    matter how small its prominence is in absolute terms — while the VALLEY of
    that same ripple, normalised against the population containing the
    cycle's genuine, large main valley, is correctly rejected as
    insignificant. The result is an "orphan" interior peak with no
    surviving valley after it. ``find_decay_period`` marks decay only up to
    the next surviving z_peak, so this orphan peak truncates an otherwise
    continuous decay right there, and everything after it becomes a NaN tail
    that the catch-all rule below then labels 'residual' — even though
    nothing about the vorticity itself indicates a genuine re-intensification.
    Observed concretely on 20170409 (research/adaptive-thresholds branch): the
    catch-all declared the cyclone 'residual' with 89.5% of its peak intensity
    still present, contradicting the published decay definition ("the decrease
    in vorticity after the mature phase until the system dissipates").

    When ``decay_tail_amplitude_fraction`` is not None, this function checks —
    immediately before the catch-all rule, and ONLY when that NaN tail
    directly follows an existing 'decay' block — whether the tail contains a
    genuine re-deepening: the largest drop below the tail's running-maximum z
    (i.e. the deepest dip below any level already reached while walking
    forward through the tail), as a FRACTION OF THE CYCLE'S OWN
    peak-to-valley AMPLITUDE (``z.max() - z.min()`` over the whole series —
    same non-zero-floor reasoning as ``prominence_relative`` in
    ``find_peaks_valleys`` and ``mature_amplitude_fraction`` in
    ``_amplitude_mature_bounds``: an absolute threshold would not be
    meaningful across cyclones of different intensity). If that drop is
    SMALLER than ``decay_tail_amplitude_fraction`` (i.e. the tail is a flat
    plateau or a ripple, not a real re-deepening), the tail is labelled
    'decay' — extending the existing decay block to the end of that run —
    instead of being left for the catch-all to mark 'residual'. If the drop
    is at or above the fraction, nothing changes here and the catch-all rule
    still applies exactly as before.

    This only ever ADDS 'decay' to already-NaN timesteps; it never removes or
    relabels any other phase, and it does not touch ``z_peaks_valleys`` or
    any other extrema, so it cannot alter the mature window computed by
    ``find_mature_stage`` (which has already run by the time this function is
    called — see the fixed pipeline order in ``get_periods``). It also never
    fires when the tail follows only a 'mature' block with no 'decay' at all
    (the "else 'mature' in unique_phases" branch below): the mechanism is
    specifically about a decay run truncated by an orphan peak, so there must
    be an existing decay block to extend. A validated calibration
    (research/adaptive-thresholds branch, 51-track calibration set) found
    ``decay_tail_amplitude_fraction=0.05`` sits in the middle of a confirmed
    safe window (0.0356, 0.0651]: correctly converts 20170409, 20150561,
    20160030, 20180759, 20180654, 20203373, 20207822 from residual-tailed to
    fully decayed, while leaving 20180628, 20190325, 20191014 (genuine
    re-intensifications) — and every other one of the 51 tracks — untouched.

    Args:
        df (pd.DataFrame): DataFrame containing vorticity data with a 'periods'
            column and a 'z' column (smoothed vorticity).
        **args_periods: Variable length argument list containing period-specific
            thresholds, including:
            - 'decay_tail_amplitude_fraction' (float, optional): Fraction (0, 1]
              of the cycle's peak-to-valley amplitude. See the note above.
              Default None disables this check entirely, reproducing the exact
              behaviour of all versions prior to this option.

    Returns:
        pd.DataFrame: Updated DataFrame with 'residual' stages marked in the 'periods'
        column where applicable.

    Raises:
        ValueError: If 'decay_tail_amplitude_fraction' is not None and not in (0, 1].
    """
    decay_tail_amplitude_fraction = args_periods.get('decay_tail_amplitude_fraction', None)
    if decay_tail_amplitude_fraction is not None and not (0 < decay_tail_amplitude_fraction <= 1):
        raise ValueError(
            "decay_tail_amplitude_fraction must be None or in (0, 1], "
            f"got {decay_tail_amplitude_fraction!r}."
        )

    unique_phases = [item for item in df['periods'].unique() if pd.notnull(item)]
    num_unique_phases = len(unique_phases)

    dt = df.index[1] - df.index[0]

    # If there's only one phase, fills with 'residual' the NaNs after the last block of it.
    if num_unique_phases == 1:
        phase_to_fill = unique_phases[0]

        # Find consecutive blocks of the same phase.
        # B5 fix: split on the phase index itself (np.diff of the DatetimeIndex), not on
        # a boolean mask diff — the boolean-mask approach produced split positions relative
        # to the full DataFrame length, causing misaligned blocks when the phase does not
        # start at row 0.
        phase_idx = df[df['periods'] == phase_to_fill].index
        phase_blocks = np.split(phase_idx, np.where(np.diff(phase_idx) != dt)[0] + 1)

        # B3 fix: break on the first non-empty block encountered in reverse order, which is
        # the last non-empty block in forward order.  Without break the loop continued
        # overwriting last_phase_block and ended up with the *first* block instead.
        for index in reversed(phase_blocks):
            if not index.empty:
                last_phase_block = index
                break

        # Find the index right after the last block
        if len(last_phase_block) > 0:
            last_phase_block_end = last_phase_block[-1]
            df.loc[last_phase_block_end + dt:, 'periods'] = df.loc[last_phase_block_end + dt:, 'periods'].fillna('residual')
        else:
            # B4 fix: fillna with inplace=True on a slice is a no-op in pandas; use
            # assignment instead.
            last_phase_block_end = phase_blocks[-2][-1]
            df.loc[last_phase_block_end + dt:, 'periods'] = df.loc[last_phase_block_end + dt:, 'periods'].fillna('residual')

    else:
        mature_periods = df[df['periods'] == 'mature'].index
        decay_periods = df[df['periods'] == 'decay'].index
        intensification_periods = df[df['periods'] == 'intensification'].index

        # Check if 'mature' is the last stage before the end of the series
        last_phase_end = df.index[-1]

        # Find residual periods where there is no decay stage after the mature stage.
        # The loop iterates over individual timesteps rather than over contiguous blocks,
        # but the result is equivalent to a block-based check: all timesteps within the
        # same mature block share the same next_decay_period, so either every timestep
        # in that block fires the conversion or none does.  Writes from later timesteps
        # in the same block are harmless redundant overwrites of 'residual'.
        for mature_period in mature_periods:
            if len(unique_phases) > 2:
                next_decay_period = decay_periods[decay_periods > mature_period].min()
                if pd.isna(next_decay_period) and mature_period != last_phase_end:
                    df.loc[mature_period:, 'periods'] = 'residual'
                    
        # Update mature periods
        mature_periods = df[df['periods'] == 'mature'].index

        # Fills with residual period intensification stage if there isn't a mature stage after it
        # but only if there's more than two periods
        if len(unique_phases) > 2:
            for intensification_period in intensification_periods:
                next_mature_period = mature_periods[mature_periods > intensification_period].min()
                if pd.isna(next_mature_period):
                    df.loc[intensification_period:, 'periods'] = 'residual'

        # Fill NaNs after decay with residual if there is a decay, else, fill the NaNs after mature.
        # If neither is present (e.g. only intensification detected), there is no anchor point
        # from which to extend residual — skip to avoid NameError on last_decay_index.
        if 'decay' in unique_phases:
            last_decay_index = df[df['periods'] == 'decay'].index[-1]

            # decay_tail_amplitude_fraction (opt-in, see docstring above): if the NaN
            # tail right after this decay block is not a genuine re-deepening, extend
            # decay over it instead of letting the catch-all below mark it residual.
            if decay_tail_amplitude_fraction is not None:
                tail = df.loc[last_decay_index + dt:]
                if len(tail) > 0 and tail['periods'].isna().all():
                    tail_z = df.loc[last_decay_index:, 'z']
                    drawdown = (tail_z.cummax() - tail_z).max()
                    cycle_amplitude = df['z'].max() - df['z'].min()
                    if drawdown < decay_tail_amplitude_fraction * cycle_amplitude:
                        df.loc[last_decay_index + dt:, 'periods'] = 'decay'
        elif 'mature' in unique_phases:
            last_decay_index = df[df['periods'] == 'mature'].index[-1]
        else:
            return df
        dt = df.index[1] - df.index[0]
        df.loc[last_decay_index + dt:, 'periods'] = df.loc[last_decay_index + dt:, 'periods'].fillna('residual')

    return df

# ---------------------------------------------------------------------------
# incipient_method: "geometric" (default) vs "plateau"
# ---------------------------------------------------------------------------
# The historical ("geometric") incipient rule places the incipient/next-phase
# boundary at a fixed FRACTION OF A DISTANCE: `threshold_incipient_length`
# (default 0.4) of the span between the start of the series and the next dz
# extremum. It therefore carries no information about how fast the cyclone is
# actually deepening at the point where it puts the boundary.
#
# Measured on the 51-track calibration set at 01c4492 (see
# research/incipient_plateau/REPORT_incipient_characterisation.md): at the
# moment the geometric rule ends the incipient phase, |dz| has already reached
# a median 58 % (author's calibration) / 77 % (package defaults) of its own
# maximum. The boundary is not sitting on a low-slope start.
#
# `incipient_method="plateau"` (opt-in; default remains "geometric", which is
# byte-identical to every prior version) replaces that with a direct slope
# criterion: the incipient phase is the leading stretch over which the
# normalised slope stays below `incipient_plateau_tau`, i.e. the initial
# "plateau" before the cyclone starts deepening in earnest.
#
# IMPORTANT MEASURED CAVEAT: this criterion is only DEFINABLE when the boundary
# artifact at t0 has been dealt with. Under bare package defaults the very
# first sample already exceeds every tau up to 0.30 on 35-50 of the 51 tracks
# (r(t0) median 0.526), so the rule degenerates to "no incipient phase". Under
# the author's validated calibration (r(t0) median 0.068) a plateau exists, but
# it is short - a median of 1-3 timesteps depending on tau. See section 3 of the
# report. This is why the method is opt-in and why tau is exposed rather than
# hard-coded.
#
# Unlike the geometric rule, the plateau rule is SELF-CONTAINED: it scans from
# t0 and depends only on the signal, not on the phases_order dispatch (cases A
# / B / C) or on the position of the next dz extremum relative to `mature`. It
# therefore applies uniformly to all three cases. The only condition under which
# it declines to create an incipient phase is a plateau of length zero -
# rel(0) >= tau - which is a property of the data and of tau, and is the knob
# that replaces the case A/B/C gating as the false-positive guard.
#
# `threshold_incipient_length` is IGNORED when incipient_method="plateau", in
# the same way `threshold_mature_length` is ignored under
# mature_method="amplitude".


# ---------------------------------------------------------------------------
# Dedicated smoothing for the INCIPIENT PROBE (plateau mode, signal="vorticity")
# ---------------------------------------------------------------------------
# `incipient_plateau_signal="vorticity"` reads d(zeta_raw)/dt on the UNFILTERED
# input. That is what makes it immune to the Lanczos/Savgol edge artifacts the
# "derivative" path inherits — and it is also what exposes it to raw noise:
# measured on the 2 %-noise synthetic cases, the normalised raw gradient at t0
# is already 0.25-0.57, above any usable tau, so the rate trips the criterion in
# a spasm and no incipient phase is found at all.
#
# The fix is NOT to re-enable pipeline smoothing (`use_smoothing` stays off by
# the author's decision, docs/future_work.md item 4) and NOT to lean on a large
# `incipient_plateau_k` as a crutch — a high k papers over an unreliable rate by
# demanding it stay tripped, which delays the boundary instead of measuring it
# better. Instead the probe gets its own light denoising, applied to the raw
# vorticity before differentiating it, and applied ONLY here: `df['z']` and
# `df['dz']` are untouched, so every other phase sees exactly what it saw
# before, and `incipient_smooth_window=0` (the default) reproduces the previous
# behaviour byte for byte.
#
# The goal is denoising towards the underlying sinusoid, NOT smoothing the
# phase. GOLDILOCKS CAVEAT: too wide a window flattens the very rise being
# measured and displaces the knee later in the series, so this is meant to stay
# light — sweep it (research/incipient_plateau/measure_incipient_smoothing.py)
# rather than assuming bigger is better.
#
# `incipient_smooth_window` / `incipient_smooth_polyorder` are IGNORED outside
# `incipient_method="plateau"` with `incipient_plateau_signal="vorticity"`, in
# the same way `threshold_incipient_length` is ignored under "plateau" and
# `threshold_mature_length` under `mature_method="amplitude"`.


def _smooth_incipient_probe(x, window, polyorder):
    """Light denoising of the curve the incipient probe measures its rate on.

    This exists ONLY to make the rate reliable; it is not a phase-smoothing
    stage and never touches ``df['z']`` / ``df['dz']``, so no other phase sees
    it (see the block comment above ``_incipient_plateau_rel``).

    Savitzky-Golay rather than a moving average: a boxcar both attenuates a
    sinusoid's amplitude and smears its curvature, and curvature is precisely
    what the incipient probe reads — the rate's rise out of the flat start, and
    (in the measurement scripts) the knee in ``|d2z|``. Savgol fits a local
    polynomial instead, so it removes noise while keeping the position and
    shape of that turn far better than a boxcar of the same width.

    All clamping is silent and conservative — the function returns ``x``
    unchanged rather than raising, because this is a probe-side convenience and
    a bad window should degrade to "no smoothing", not break phase detection:

      * ``window <= 0`` disables it (the default);
      * an even window is rounded up to odd (``| 1``), as ``savgol_filter``
        requires, matching the ``len // 4 | 1`` idiom used elsewhere;
      * a window longer than the series is clamped to the longest odd length
        that fits;
      * a window that ends up ``<= polyorder`` cannot define the fit and is
        skipped.
    """
    w = int(window)
    if w <= 0 or x.size < 3:
        return x
    w |= 1
    longest_odd = x.size if x.size % 2 else x.size - 1
    w = min(w, longest_odd)
    if w <= int(polyorder):
        return x
    return savgol_filter(x, w, int(polyorder), mode="nearest")


def _incipient_plateau_rel(df, signal, smooth_window=0, smooth_polyorder=3):
    """Normalised slope profile rel(t) used by the plateau incipient rule.

    Args:
        df (pd.DataFrame): the working frame built by ``get_periods``; must
            carry ``'dz'`` (``dz_dt_smoothed2``) and ``'z_unfil'`` (the raw
            input vorticity, before any filtering or smoothing).
        signal (str): ``"derivative"`` uses ``|dz_dt_smoothed2|`` — the array
            ``find_stages`` itself consumes, so the criterion is measured on
            exactly the curve the phase detection sees. ``"vorticity"`` uses
            ``|d(zeta_raw)/dt|`` via ``np.gradient`` on the UNFILTERED input,
            which is immune to Lanczos/Savgol edge artifacts but noisier.
        smooth_window (int): Savitzky-Golay window applied to the raw vorticity
            BEFORE differentiating it. 0 (default) disables it, reproducing the
            previous behaviour exactly. **Only used when
            ``signal="vorticity"``** — the ``"derivative"`` path already reads a
            curve the pipeline has filtered, so smoothing it again here would be
            a second, hidden pass over the same signal.
        smooth_polyorder (int): polynomial order for that Savitzky-Golay pass.
            Default 3.

    Returns:
        np.ndarray: ``|v| / max|v|`` in [0, 1]; all-zeros if the signal is flat.
    """
    if signal == "derivative":
        v = np.asarray(df['dz'], dtype=float)
    elif signal == "vorticity":
        v = np.gradient(_smooth_incipient_probe(
            np.asarray(df['z_unfil'], dtype=float),
            smooth_window, smooth_polyorder))
    else:
        raise ValueError(
            f"incipient_plateau_signal must be 'derivative' or 'vorticity', got {signal!r}.")

    a = np.abs(v)
    amax = np.nanmax(a) if a.size else 0.0
    if not np.isfinite(amax) or amax <= 0:
        return np.zeros_like(a)
    return a / amax


def _incipient_plateau_boundary(rel, tau, crossing, k):
    """First index at which the initial low-slope plateau ends.

    The incipient phase is the half-open range ``[0, boundary)``; a boundary of
    0 means no incipient phase is created.

    Args:
        rel (np.ndarray): normalised slope profile from ``_incipient_plateau_rel``.
        tau (float): plateau threshold; the plateau is where ``rel < tau``.
        crossing (str): ``"single"`` ends the plateau at the first sample with
            ``rel >= tau``. ``"sustained"`` requires ``k`` consecutive samples
            at or above ``tau`` and ends the plateau at the start of that run,
            which is robust to a single noise spike inside the plateau.
        k (int): run length for ``"sustained"``; ignored for ``"single"``.

    Returns:
        int: the boundary index.
    """
    above = rel >= tau

    if crossing == "single":
        hits = np.flatnonzero(above)
        return int(hits[0]) if hits.size else 0

    if crossing != "sustained":
        raise ValueError(
            f"incipient_plateau_crossing must be 'single' or 'sustained', got {crossing!r}.")

    k = int(k)
    if k < 1:
        raise ValueError(f"incipient_plateau_k must be >= 1, got {k}.")

    n = above.size
    if k > n:
        # A run of k cannot exist: no boundary is defined, so no incipient
        # phase (same conservative outcome as a zero-length plateau).
        return 0
    # Sliding all-True window of width k, without a Python loop.
    run = np.convolve(above.astype(int), np.ones(k, dtype=int), mode="valid")
    hits = np.flatnonzero(run == k)
    # No sustained run anywhere: the criterion is undefined for this series, so
    # decline rather than fall back to the single-crossing rule (silently
    # swapping criteria would make the toggle unreadable in validation).
    return int(hits[0]) if hits.size else 0


def find_incipient_period(df, **args_periods):

    """
    Identifies and marks the incipient period in the cyclone life cycle.

    Two methods are available, selected by ``incipient_method``:

    ``"geometric"`` (default, unchanged from every prior version)
        The incipient phase runs from the start of the first intensification or
        decay segment to ``threshold_incipient_length`` of the way to the next
        dz valley/peak, dispatched through three cases on the phase order
        (see the case A/B/C branches below).

    ``"plateau"`` (opt-in)
        The incipient phase is the leading stretch over which the normalised
        slope stays below ``incipient_plateau_tau``. Self-contained: it scans
        from t0 and does not use the case A/B/C dispatch or
        ``threshold_incipient_length``. See the block comment above
        ``_incipient_plateau_rel`` for the rationale and the measured caveats.

    Args:
        df (pd.DataFrame): DataFrame containing vorticity data with columns for
            'periods', 'dz_peaks_valleys', and — for the plateau method — 'dz'
            and 'z_unfil'.
        **args_periods: Variable length argument list containing period-specific
            thresholds, including:
            - 'threshold_incipient_length' (float): Fraction of the time range
              between the start of intensification or decay and the next dz
              valley/peak to be marked as incipient. **Ignored when**
              ``incipient_method="plateau"``, in the same way
              ``threshold_mature_length`` is ignored under
              ``mature_method="amplitude"``.
            - 'incipient_method' (str): "geometric" (default) or "plateau".
            - 'incipient_plateau_tau' (float): plateau threshold on the
              normalised slope. Default 0.20. Only used when method="plateau".
            - 'incipient_plateau_signal' (str): "derivative" (default) or
              "vorticity". Only used when method="plateau".
            - 'incipient_plateau_crossing' (str): "single" (default) or
              "sustained". Only used when method="plateau".
            - 'incipient_plateau_k' (int): consecutive steps required by
              "sustained". Default 3. Only used when crossing="sustained".
            - 'incipient_smooth_window' (int): Savitzky-Golay window applied to
              the raw vorticity before the incipient probe differentiates it.
              Default 0 (disabled). Only used when method="plateau" AND
              signal="vorticity".
            - 'incipient_smooth_polyorder' (int): polynomial order for that
              pass. Default 3.

    Returns:
        pd.DataFrame: Updated DataFrame with 'incipient' stages marked in the
        'periods' column where applicable.
    """
    threshold_incipient_length = args_periods['threshold_incipient_length']
    # .get() with defaults: keeps the function callable with the partial
    # args dict that predates these parameters (and that the tests use).
    incipient_method = args_periods.get('incipient_method', 'geometric')
    if incipient_method not in ('geometric', 'plateau'):
        raise ValueError(
            f"incipient_method must be 'geometric' or 'plateau', got {incipient_method!r}.")

    periods = df['periods']
    
    # inplace=True on a column accessor is a no-op under pandas CoW (pandas 3.0+);
    # use explicit assignment to guarantee the fill propagates back to the DataFrame.
    df['periods'] = df['periods'].fillna('incipient')

    phases_order = []
    current_phase = None

    for phase in periods:
        if pd.notnull(phase) and phase != 'residual':
            if phase != current_phase:
                phases_order.append(phase)
                current_phase = phase

    if incipient_method == 'plateau':
        # Self-contained slope rule: the incipient phase is the leading run over
        # which the normalised slope stays below tau. No dependence on
        # phases_order, on the next dz extremum, or on
        # threshold_incipient_length. A boundary of 0 (rel(0) already >= tau,
        # i.e. a zero-length plateau) means no incipient phase is created here —
        # the catch-all fillna above still applies, exactly as in the geometric
        # path.
        rel = _incipient_plateau_rel(
            df, args_periods.get('incipient_plateau_signal', 'derivative'),
            args_periods.get('incipient_smooth_window', 0),
            args_periods.get('incipient_smooth_polyorder', 3))
        boundary = _incipient_plateau_boundary(
            rel,
            args_periods.get('incipient_plateau_tau', 0.20),
            args_periods.get('incipient_plateau_crossing', 'single'),
            args_periods.get('incipient_plateau_k', 3),
        )
        if boundary > 0:
            # [t0, boundary) — half-open, hence .iloc and not the label-based
            # (inclusive) .loc slicing the geometric branches use.
            df.iloc[:boundary, df.columns.get_loc('periods')] = 'incipient'
        return df

    # If there's more than 2 unique phases other than residual, and the life cycle
    # begins with intensification or decay, incipient phase will be from the beginning
    # of it until 40% to the next dz_valley/dz_peak
    # If there is a cycle of intensification and decay before the next mature stage it
    #  will cganged to incipient
    if len(phases_order) > 2:
        if phases_order[:3] == ['intensification', 'decay', 'intensification']:
            start_time = df[df['periods'] == "intensification"].index.min()
            decay_blocks = np.split(df[df['periods'] == "decay"].index,
                                np.where(np.diff(df['periods'] == "decay") != 0)[0] + 1)
            end_time = decay_blocks[0].max()
            if not pd.isna(end_time):
                time_range = start_time + ((end_time - start_time) * threshold_incipient_length)
                df.loc[start_time:time_range, 'periods'] = 'incipient'

        elif phases_order[0] == 'intensification':
            start_time = df[df['periods'] == 'intensification'].index.min()
            # Check if there's a dz valley before the next mature stage
            next_dz_valley = df[1:][df[1:]['dz_peaks_valleys'] == 'valley'].index.min()
            next_mature = df[periods == 'mature'].index.min()
            if next_dz_valley < next_mature:
                time_range = start_time + ((next_dz_valley - start_time) * threshold_incipient_length)
                df.loc[start_time:time_range, 'periods'] = 'incipient'

        elif phases_order[0] == 'decay':
            start_time = df[df['periods'] == 'decay'].index.min()
            # Check if there's a dz peak before the next mature stage
            next_dz_peak = df[1:][df[1:]['dz_peaks_valleys'] == 'peak'].index.min()
            next_mature = df[periods == 'mature'].index.min()
            if next_dz_peak < next_mature:
                time_range = start_time + ((next_dz_peak - start_time) * threshold_incipient_length)
                df.loc[start_time:time_range, 'periods'] = 'incipient'  
                
    return df

if __name__ == '__main__':

    import determine_periods as det

    track_file = "../tests/test.csv"
    track = pd.read_csv(track_file, parse_dates=[0], delimiter=';', index_col=[0])

    # Extract the series of vorticity values and the temporal range
    series = track['min_zeta_850'].tolist()
    x = track.index.tolist()

    # Testing
    options = {
        "plot": False,
        "plot_steps": False,
        "export_dict": False,
        "process_vorticity_args": {
            "use_filter": False,
            "use_smoothing_twice": len(track)// 4 | 1}
    }

    args = [options["plot"], options["plot_steps"], options["export_dict"]]
    
    zeta_df = pd.DataFrame(track["min_zeta_850"].rename('zeta'))

    # Modify the array_vorticity_args if provided, otherwise use defaults
    vorticity = det.process_vorticity(zeta_df.copy(), **options["process_vorticity_args"])

    z = vorticity.vorticity_smoothed2
    dz = vorticity.dz_dt_smoothed2
    dz2 = vorticity.dz_dt2_smoothed2

    df = z.to_dataframe().rename(columns={'vorticity_smoothed2':'z'})
    df['z_unfil'] = vorticity.zeta.to_dataframe()
    df['dz'] = dz.to_dataframe()
    df['dz2'] = dz2.to_dataframe()

    df['z_peaks_valleys'] = det.find_peaks_valleys(df['z'])
    df['dz_peaks_valleys'] = det.find_peaks_valleys(df['dz'])
    df['dz2_peaks_valleys'] = det.find_peaks_valleys(df['dz2'])

    df['periods'] = np.nan
    df['periods'] = df['periods'].astype('object')

    df = find_intensification_period(df)

    df = find_decay_period(df)

    df = find_mature_stage(df)

    df = find_residual_period(df)

    # 1) Fill consecutive intensification or decay periods that have NaNs between them
    # 2) Remove periods that are too short and fill with the previous period
    # (or the next one if there is no previous period)
    df = det.post_process_periods(df)

    df = find_incipient_period(df)

