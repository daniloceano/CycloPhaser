"""Layer inspector for the calibration app — PURE computation, no Streamlit.

PURE VISUALISATION. Nothing in this module changes phase detection. Every
quantity it reports is either read straight back from the package (by calling
``find_intensification_period``, ``find_decay_period``, ``find_mature_stage``,
``find_residual_period``, ``post_process_periods``, ``find_incipient_period``,
``find_peaks_valleys``, ``_local_cycle_scale``, ``_amplitude_mature_bounds``,
``_incipient_plateau_rel`` / ``_incipient_plateau_boundary`` /
``_smooth_incipient_probe``), or a diagnostic computed on top of what those
returned. The module deliberately imports neither ``streamlit`` nor a plotting
library, so the same helpers feed the Plotly inspector in the app AND the
offline matplotlib render in ``research/app_layer_inspector/``.

What lives here
---------------
``build_working_frame``
    The frame ``get_periods`` builds internally, reproduced field for field so
    the package's stage functions can be called on it directly. This is what
    makes the pipeline ribbon and the ledgers faithful BY CONSTRUCTION rather
    than by resemblance.

``pipeline_ribbon``
    ``df['periods']`` after each of the six detection steps, obtained by
    calling the six package functions in the pipeline's fixed order. Step 6 of
    the ribbon is required (and tested) to equal ``get_periods``' own result.

``intensification_ledger`` / ``decay_ledger``
    Every candidate segment the two functions consider, the scale each one is
    measured against, the minimum duration it had to clear, and the verdict —
    plus the inter-block gaps and their fill test. The union of the accepted
    candidates (and filled gaps) is required (and tested) to be identical to
    the mask the package function itself produces.

``mature_ledger``
    The candidate mature windows, whether each was written, and — for the ones
    that were written and then discarded — WHY the strict neighbour
    confirmation in ``find_mature_stage`` rejected them. Today a discarded
    mature window vanishes without trace; this is the only part of the module
    that reconstructs a criterion the package does not expose as a callable,
    and it is pinned by a fidelity test against ``find_mature_stage`` itself.

``mature_lens`` / ``incipient_lens`` / ``knee_index`` / ``_effective_threshold``
    Carried over unchanged from the pure half of the abandoned
    ``research/app-phase-focus`` branch's ``phase_focus.py`` (only the drawing
    code and the focus UI were dropped). They answer "which extrema does the
    detector actually consume" and "what does the plateau probe see".
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.signal import peak_prominences

from cyclophaser.determine_periods import find_peaks_valleys, post_process_periods
from cyclophaser.find_stages import (
    _amplitude_mature_bounds,
    _incipient_plateau_boundary,
    _incipient_plateau_rel,
    _local_cycle_scale,
    _smooth_incipient_probe,
    find_decay_period,
    find_incipient_period,
    find_intensification_period,
    find_mature_stage,
    find_residual_period,
)

# Phase palette — the app's PHASE_COLORS, duplicated here (not imported) so this
# module stays importable without Streamlit; app.py and the offline figure
# script both read it from here.
PHASE_COLORS = {
    "incipient":       "#65a1e6",
    "intensification": "#f7b538",
    "mature":          "#d62828",
    "decay":           "#9aa981",
    "residual":        "gray",
}

# Marker / colour conventions, shared with the research figures in
# research/incipient_plateau/ so the two read the same way.
C_ACCEPT_PEAK = "#2171b5"
C_ACCEPT_VALLEY = "#cb181d"
C_REJECT = "#9e9e9e"
C_THRESHOLD = "#8856a7"
C_Z = "#1d3557"
C_DZ = "#457b9d"
C_DZ2 = "#6a51a3"
C_REL = "#e63946"
C_SMOOTH = "#e07b00"
C_BOUNDARY = "#d000d0"
C_KNEE = "#00a000"

# The six detection steps, in the fixed order get_periods calls them.
STEP_NAMES = (
    "1 find_intensification_period",
    "2 find_decay_period",
    "3 find_mature_stage",
    "4 find_residual_period",
    "5 post_process_periods",
    "6 find_incipient_period",
)

# Every keyword get_periods forwards to the stage functions, with the package's
# own defaults. build_args_periods() below fills this in, so a caller only has
# to name what it wants to change — and so a new package parameter shows up
# here as one entry rather than as a divergence between app and package.
_ARGS_PERIODS_DEFAULTS = {
    "threshold_intensification_length": 0.075,
    "threshold_intensification_gap": 0.075,
    "threshold_mature_distance": 0.125,
    "threshold_mature_length": 0.03,
    "threshold_decay_length": 0.075,
    "threshold_decay_gap": 0.075,
    "threshold_incipient_length": 0.4,
    "length_scale": "global",
    "mature_method": "derivative",
    "mature_amplitude_fraction": 0.90,
    "decay_tail_amplitude_fraction": None,
    "incipient_method": "geometric",
    "incipient_plateau_tau": 0.20,
    "incipient_plateau_signal": "derivative",
    "incipient_plateau_crossing": "single",
    "incipient_plateau_k": 3,
    "incipient_smooth_window": 0,
    "incipient_smooth_polyorder": 3,
}


def build_args_periods(**overrides) -> dict:
    """The ``args_periods`` dict ``get_periods`` hands to every stage function.

    Unknown keys are rejected rather than silently ignored: a typo'd threshold
    that quietly fell back to the package default would make the ribbon and the
    ledgers disagree with the run they are supposed to be explaining, which is
    the one failure mode this module cannot afford.
    """
    unknown = set(overrides) - set(_ARGS_PERIODS_DEFAULTS)
    if unknown:
        raise KeyError(f"not stage-detection parameters: {sorted(unknown)}")
    args = dict(_ARGS_PERIODS_DEFAULTS)
    args.update({k: v for k, v in overrides.items() if v is not None})
    return args


# ══════════════════════════════════════════════════════════════════════════════
# The working frame — exactly what get_periods builds before step 1
# ══════════════════════════════════════════════════════════════════════════════

def build_working_frame(vorticity,
                        prominence=None,
                        prominence_relative=None,
                        distance=None) -> pd.DataFrame:
    """Reproduce ``get_periods``' internal frame, field for field.

    This is a TRANSCRIPTION of the block in
    ``determine_periods.get_periods`` between "Extract smoothed vorticity and
    derivatives" and "Detect different stages of cyclone lifecycle" — same
    columns, same source arrays, same ``find_peaks_valleys`` arguments (the
    prominence/distance filters applied to ``z`` only, never to ``dz``/``dz2``),
    same ``object``-dtype NaN ``periods`` column.

    It is transcribed rather than imported because ``get_periods`` does not
    expose it: the frame only exists inside that function, and it is the input
    every stage function reads. Any divergence here would make the pipeline
    ribbon and the ledgers describe a run that never happened, which is why
    ``tests/test_layer_inspector.py`` pins step 6 of the ribbon against
    ``get_periods``' own output on real tracks.

    Args:
        vorticity: the ``process_vorticity`` dataset (needs ``zeta``,
            ``vorticity_smoothed2``, ``dz_dt_smoothed2``, ``dz_dt2_smoothed2``).
        prominence, prominence_relative, distance: the z-extrema filter
            settings, forwarded to ``find_peaks_valleys`` verbatim.

    Returns:
        pd.DataFrame indexed by time with columns z, z_unfil, dz, dz2,
        z_peaks_valleys, dz_peaks_valleys, dz2_peaks_valleys, periods.
    """
    z = vorticity.vorticity_smoothed2
    dz = vorticity.dz_dt_smoothed2
    dz2 = vorticity.dz_dt2_smoothed2

    df = z.to_dataframe().rename(columns={'vorticity_smoothed2': 'z'})
    df['z_unfil'] = vorticity.zeta.to_dataframe()
    df['dz'] = dz.to_dataframe()
    df['dz2'] = dz2.to_dataframe()

    df['z_peaks_valleys'] = find_peaks_valleys(df['z'],
                                               prominence=prominence,
                                               prominence_relative=prominence_relative,
                                               distance=distance)
    df['dz_peaks_valleys'] = find_peaks_valleys(df['dz'])
    df['dz2_peaks_valleys'] = find_peaks_valleys(df['dz2'])

    df['periods'] = np.nan
    df['periods'] = df['periods'].astype('object')
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PIECE 2 — the pipeline ribbon: what the phases look like after each step
# ══════════════════════════════════════════════════════════════════════════════

def pipeline_ribbon(df: pd.DataFrame, **args_periods) -> list[tuple[str, pd.Series]]:
    """``df['periods']`` after each of the six detection steps.

    Fidelity is BY CONSTRUCTION: the package's own six functions are called, in
    the package's own order, on a copy of the working frame, and the periods
    column is snapshotted after each. Nothing is re-implemented, so the ribbon
    cannot drift from the pipeline — the only thing that could be wrong is the
    frame handed in, which is why ``build_working_frame`` transcribes
    ``get_periods``' construction and why step 6 is tested against
    ``get_periods``' own result.

    Args:
        df: a fresh frame from ``build_working_frame`` (copied here, not mutated).
        **args_periods: the stage-detection parameters, as built by
            ``build_args_periods``.

    Returns:
        list of (step name, periods Series) in pipeline order, length 6.
    """
    work = df.copy(deep=True)
    steps = []
    for name, fn in (
        (STEP_NAMES[0], lambda d: find_intensification_period(d, **args_periods)),
        (STEP_NAMES[1], lambda d: find_decay_period(d, **args_periods)),
        (STEP_NAMES[2], lambda d: find_mature_stage(d, **args_periods)),
        (STEP_NAMES[3], lambda d: find_residual_period(d, **args_periods)),
        # post_process_periods is the one step that takes no thresholds.
        (STEP_NAMES[4], lambda d: post_process_periods(d)),
        (STEP_NAMES[5], lambda d: find_incipient_period(d, **args_periods)),
    ):
        work = fn(work)
        steps.append((name, work['periods'].copy()))
    return steps


def ribbon_overwrites(steps: list[tuple[str, pd.Series]]) -> list[dict]:
    """Where each step overwrote a label a previous step had already written.

    Returns one record per (step, contiguous run) with the label before, the
    label after, and the run's time bounds — i.e. the answer to "who took this
    stretch away from whom", which is the whole reason the six functions'
    fixed order matters.
    """
    out = []
    for i in range(1, len(steps)):
        prev = steps[i - 1][1]
        cur = steps[i][1]
        changed = ((prev.notna()) & (prev != cur)).to_numpy()
        prev_v = prev.to_numpy(dtype=object)
        cur_v = cur.to_numpy(dtype=object)
        for lo, hi in _runs(changed):
            # Split the run wherever the (from, to) pair itself changes: a
            # single step can overwrite an intensification block and the decay
            # block next to it in one contiguous stretch (find_mature_stage
            # routinely does exactly that), and reporting only the first pair
            # would hide half of what the step did.
            seg_lo = lo
            for j in range(lo, hi + 2):
                same = (j <= hi
                        and _same_label(prev_v[j], prev_v[seg_lo])
                        and _same_label(cur_v[j], cur_v[seg_lo]))
                if same:
                    continue
                out.append({
                    "step": steps[i][0],
                    "start": prev.index[seg_lo],
                    "end": prev.index[j - 1],
                    "n": j - seg_lo,
                    "from": str(prev_v[seg_lo]),
                    "to": "—" if pd.isna(cur_v[seg_lo]) else str(cur_v[seg_lo]),
                })
                seg_lo = j
    return out


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous True runs of a boolean mask as [start, end] positional pairs."""
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return []
    starts, ends, in_run = [], [], False
    for i, v in enumerate(mask):
        if v and not in_run:
            starts.append(i); in_run = True
        elif not v and in_run:
            ends.append(i - 1); in_run = False
    if in_run:
        ends.append(len(mask) - 1)
    return list(zip(starts, ends))


def label_runs(periods: pd.Series) -> list[dict]:
    """Contiguous runs of the same label in a periods column (NaN included).

    Unlike ``periods_to_dict``, NaN runs are kept and reported as label None,
    because "still unclassified after this step" is exactly what the ribbon
    needs to show.
    """
    values = periods.to_numpy(dtype=object)
    out = []
    if values.size == 0:
        return out
    start = 0
    for i in range(1, values.size + 1):
        if i == values.size or not _same_label(values[i], values[start]):
            lbl = values[start]
            out.append({
                "label": None if pd.isna(lbl) else str(lbl),
                "i0": start, "i1": i - 1,
                "start": periods.index[start], "end": periods.index[i - 1],
            })
            start = i
    return out


def _same_label(a, b) -> bool:
    a_na, b_na = pd.isna(a), pd.isna(b)
    if a_na or b_na:
        return a_na and b_na
    return a == b


def phase_spans_for_shading(periods_dict: dict, index: pd.DatetimeIndex) -> list[dict]:
    """Shading spans matching the app's existing phase figure exactly.

    Mirrors ``app._plot_compact``: each phase is shaded from its own start to
    the START of the next phase (not to its own end), so consecutive phases
    tile the axis with no seam. Keeping this identical is what makes the
    inspector's default layer set reproduce the figure the Grid mode draws.
    """
    items = list(periods_dict.items())
    spans = []
    for i, (phase, (start, end)) in enumerate(items):
        right = items[i + 1][1][0] if i + 1 < len(items) else end
        spans.append({
            "phase": phase,
            "key": str(phase).rstrip(" 0123456789").strip(),
            "start": start,
            "end": right,
        })
    return spans


def normalise_series(y):
    """Rescale a series to [0, 1] using its own minimum and maximum.

    The panels stack series of genuinely different magnitude — raw ``zeta``
    runs 2-3x wider than the smoothed curve the detector reads. A twinx was
    ruled out for the inspector (it already produced a zorder bug in the app's
    ``_plot_compact``), so instead every curve is rescaled to fill the same
    band and the panel is read for SHAPE: where each series turns, and when.
    That is what the phase rules act on — the y magnitude is not what is being
    judged here, so spending the axis on it buys nothing.

    Consequence worth knowing: after this, zero is at a different height for
    each series, so the dz/dz2 panels' zero line is no longer common and is
    not drawn. Switch the rescaling off (the app's "Shared y scale" checkbox)
    to read true units and a real zero.

    Returns:
        (scaled, lo, hi). A flat series (lo == hi) has no range to spread over
        and is returned as a constant 0.5, centred in the band, rather than
        dividing by zero.
    """
    return _rescale(np.asarray(y, dtype=float), *_span([y]))


def _span(reference) -> tuple[float, float]:
    """(lo, hi) over one series or over a GROUP of them, pooled.

    A bare array/Series is accepted as a group of one, so a caller that does
    not care about grouping cannot silently get a per-element band.
    """
    if isinstance(reference, (np.ndarray, pd.Series)) or not isinstance(reference, (list, tuple)):
        reference = [reference]
    values = np.concatenate([np.asarray(r, dtype=float).ravel() for r in reference])
    values = values[np.isfinite(values)]
    if values.size == 0:
        return 0.0, 1.0
    return float(values.min()), float(values.max())


def _rescale(a, lo, hi):
    if hi <= lo:
        return np.full_like(a, 0.5), lo, hi
    return (a - lo) / (hi - lo), lo, hi


def rescaler(reference, normalize: bool):
    """A transform mapping values onto ``reference``'s rescaled band.

    ``reference`` is a LIST of series that share one band — which is the whole
    point, and the thing the package's own figures already get right. In
    ``plots.plot_all_periods`` the raw ``zeta`` is drawn on one axis and
    ``filtered_vorticity`` / ``vorticity_smoothed`` / ``vorticity_smoothed2``
    together on a second (``twinx``, autoscaled over all three at once). That
    grouping is not incidental:

      * the raw series has 2-3x the amplitude of the filtered ones, so giving
        it its own band is what makes it overlay the filtered curve instead of
        squashing it — the readable "same track, cleaned up" picture;
      * the three pipeline stages share ONE band, so the amplitude each
        smoothing pass removes stays visible. Scaling them separately would
        force every stage to span the full height and make them look
        identical, which is exactly the information the panel exists to show
        (measured on 20190325 under package defaults: filtered_vorticity spans
        1.25x vorticity_smoothed2 — a difference a per-series scaling erases).

    Overlays get the scaler of the series they annotate, so a ledger segment
    drawn over ``z`` lands on the ``z`` line rather than floating above it.
    The same function is used by the Plotly and matplotlib renderers, so the
    two cannot disagree about where a layer sits.

    ``normalize=False`` returns the identity: the series in their own units.
    """
    if not normalize:
        return lambda v: np.asarray(v, dtype=float)
    lo, hi = _span(reference)
    span = (hi - lo) or 1.0
    return lambda v: (np.asarray(v, dtype=float) - lo) / span


def phase_at_step(periods: pd.Series) -> np.ndarray:
    """Per-timestep phase label as strings ('—' for unclassified), for hover."""
    return np.array(["—" if pd.isna(v) else str(v) for v in periods.to_numpy(dtype=object)])


# ══════════════════════════════════════════════════════════════════════════════
# PIECE 3 — the candidate ledger for intensification and decay
# ══════════════════════════════════════════════════════════════════════════════

def _positional_slice(index: pd.DatetimeIndex, start, end) -> slice:
    """Positional equivalent of ``df.loc[start:end]`` (both ends inclusive)."""
    lo = int(index.searchsorted(start, side="left"))
    hi = int(index.searchsorted(end, side="right"))
    return slice(lo, hi)


def _segment_ledger(df: pd.DataFrame, kind: str,
                    threshold_length: float, threshold_gap: float,
                    length_scale: str) -> dict:
    """Shared body of ``intensification_ledger`` / ``decay_ledger``.

    Reconstructs, on the app side, the candidate loop of
    ``find_intensification_period`` (each z_peak -> the next z_valley) or
    ``find_decay_period`` (each z_valley -> the next z_peak, plus the
    last-valley-runs-to-the-end rule), with the SAME scale computation: the
    global series length, or ``_local_cycle_scale`` — imported from the
    package, never rewritten — under ``length_scale='local'``.

    The reconstruction is the risk in this module, so it is pinned by
    ``tests/test_layer_inspector.py``: the union of the accepted candidates and
    the filled gaps must equal, bit for bit, the mask the package function
    itself writes on a fresh frame, over 20+ tracks x several prominence
    settings.

    Returns:
        dict with ``candidates`` (list of records), ``gaps`` (list of records)
        and ``mask`` (bool array over df.index, the union of everything
        accepted — the same thing the package function marks).
    """
    index = df.index
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index
    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index
    length = index[-1] - index[0]
    dt = index[1] - index[0]

    mask = np.zeros(len(index), dtype=bool)
    candidates = []

    if kind == "intensification":
        anchors, targets = z_peaks, z_valleys
    else:
        anchors, targets = z_valleys, z_peaks

    for anchor in anchors:
        nxt = targets[targets > anchor].min()
        if pd.isna(nxt):
            if kind == "intensification":
                # find_intensification_period simply skips a peak with no
                # valley after it — there is no candidate at all, so it is not
                # a rejection either and does not belong in the ledger.
                continue
            # find_decay_period instead runs the last valley to the end of the
            # series; that IS a candidate and still faces the length test.
            seg_start, seg_end, to_series_end = anchor, index[-1], True
        else:
            seg_start, seg_end, to_series_end = anchor, nxt, False

        scale = (_local_cycle_scale(df, seg_start, seg_end)
                 if length_scale == 'local' else length)
        minimum = scale * threshold_length
        duration = seg_end - seg_start
        accepted = bool(duration > minimum)
        if accepted:
            mask[_positional_slice(index, seg_start, seg_end)] = True
        candidates.append({
            "kind": kind,
            "type": "candidate",
            "start": seg_start,
            "end": seg_end,
            "duration": duration,
            "scale": scale,
            "minimum": minimum,
            "accepted": accepted,
            "to_series_end": to_series_end,
        })

    # ── gaps between accepted blocks, and the gap-fill test ──────────────────
    # The package computes the block list ONCE, from the marks the candidate
    # loop left, and then fills; blocks are not recomputed as filling proceeds.
    # Same here, or a chain of three near blocks would merge differently.
    gaps = []
    marked = index[mask]
    blocks = np.split(marked, np.where(np.diff(marked) != dt)[0] + 1)
    for i in range(len(blocks) - 1):
        block_end = blocks[i][-1]
        next_block_start = blocks[i + 1][0]
        gap = next_block_start - block_end
        gap_scale = (_local_cycle_scale(df, block_end, next_block_start)
                     if length_scale == 'local' else length)
        maximum = gap_scale * threshold_gap
        filled = bool(gap < maximum)
        if filled:
            mask[_positional_slice(index, block_end, next_block_start)] = True
        gaps.append({
            "kind": kind,
            "type": "gap",
            "start": block_end,
            "end": next_block_start,
            "duration": gap,
            "scale": gap_scale,
            "minimum": maximum,   # here a MAXIMUM: the gap is filled if below it
            "accepted": filled,
            "to_series_end": False,
        })

    return {"candidates": candidates, "gaps": gaps, "mask": mask}


def intensification_ledger(df, threshold_intensification_length=0.075,
                           threshold_intensification_gap=0.075,
                           length_scale="global", **_ignored) -> dict:
    """Candidate ledger for ``find_intensification_period`` (see ``_segment_ledger``)."""
    return _segment_ledger(df, "intensification",
                           threshold_intensification_length,
                           threshold_intensification_gap, length_scale)


def decay_ledger(df, threshold_decay_length=0.075, threshold_decay_gap=0.075,
                 length_scale="global", **_ignored) -> dict:
    """Candidate ledger for ``find_decay_period`` (see ``_segment_ledger``)."""
    return _segment_ledger(df, "decay",
                           threshold_decay_length, threshold_decay_gap,
                           length_scale)


def ledger_reference_mask(df: pd.DataFrame, kind: str, **args_periods) -> np.ndarray:
    """The mask the PACKAGE writes for `kind`, run in isolation on a fresh frame.

    The oracle the ledger's fidelity test compares against — and the reason the
    ledger can be trusted to be showing the real criterion rather than a
    plausible-looking parallel one.
    """
    work = df.copy(deep=True)
    fn = find_intensification_period if kind == "intensification" else find_decay_period
    work = fn(work, **args_periods)
    return (work['periods'] == kind).to_numpy()


def fate_of_segment(steps: list[tuple[str, pd.Series]], start, end) -> dict:
    """What became of an accepted candidate by the end of the pipeline.

    Crosses the ledger (PIECE 3) with the ribbon (PIECE 2): a candidate can be
    accepted by its own function and then be overwritten wholesale by a later
    step — that is the single most confusing thing about calibrating these
    thresholds, and it is invisible in the final figure.

    Returns:
        dict with ``final`` (the labels present over the segment in step 6, with
        their counts) and ``overwritten`` (how many timesteps no longer carry
        the label the candidate's own function gave them).
    """
    final = steps[-1][1]
    sl = _positional_slice(final.index, start, end)
    values = final.iloc[sl].to_numpy(dtype=object)
    counts: dict[str, int] = {}
    for v in values:
        key = "—" if pd.isna(v) else str(v)
        counts[key] = counts.get(key, 0) + 1
    return {"final": counts, "n": int(values.size)}


# ══════════════════════════════════════════════════════════════════════════════
# PIECE 4a — mature: the extrema lens, plus the strict-confirmation verdict
# ══════════════════════════════════════════════════════════════════════════════

def _label_positions(labels: pd.Series, kind: str) -> np.ndarray:
    """Positional indices carrying `kind` ('peak'/'valley') in a labels Series."""
    return np.flatnonzero((labels == kind).to_numpy())


def _effective_threshold(signed_data: np.ndarray,
                         interior: np.ndarray,
                         prominence,
                         prominence_relative):
    """Prominences of `interior` and the prominence threshold actually applied.

    Replicates ``determine_periods._refine_extrema``'s bookkeeping exactly so
    the horizontal line a layer draws is the line the filter used, not an
    approximation of it:

      * prominences are computed once, with ``peak_prominences`` on
        ``signed_data`` (``data`` for peaks, ``-data`` for valleys);
      * absolute filtering runs first;
      * the relative denominator is the max prominence of the set that SURVIVED
        the absolute step, not of the original set.

    Both filters are ``prom >= threshold`` tests on the same prominence values,
    so a single number — ``max(absolute, relative x denominator)`` — describes
    the combined cut and can be drawn as one line.

    Returns:
        (prom_vals, threshold) where `threshold` is None when neither
        prominence filter is active (nothing was cut on prominence grounds).
    """
    if interior.size == 0:
        return np.zeros(0), None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        prom_vals = peak_prominences(signed_data, interior)[0]

    if prominence is None and prominence_relative is None:
        return prom_vals, None

    threshold = float(prominence) if prominence is not None else 0.0
    surviving = prom_vals[prom_vals >= threshold] if prominence is not None else prom_vals
    if prominence_relative is not None and surviving.size:
        max_prom = float(surviving.max())
        if max_prom > 0.0:
            threshold = max(threshold, float(prominence_relative) * max_prom)
    return prom_vals, threshold


def mature_lens(z: pd.Series,
                prominence=None,
                prominence_relative=None,
                distance=None) -> dict:
    """Accepted/rejected z extrema under the current extrema-filter settings.

    Args:
        z: the smoothed vorticity the detector runs on (``df['z']`` /
           ``vorticity_smoothed2``), indexed as in the working frame.
        prominence, prominence_relative, distance: the extrema-filter
           parameters, passed through to ``find_peaks_valleys`` verbatim.

    Returns:
        dict with, for each of 'peak' and 'valley':
          ``accepted_<kind>s`` / ``rejected_<kind>s`` — positional indices;
          ``<kind>_prominences`` — {position: prominence} for interior
            candidates (boundary extrema are unconditionally preserved and
            have no meaningful prominence, so they are absent);
          ``<kind>_threshold`` — the effective prominence cut, or None.
        plus ``n`` (series length) and ``boundary`` (preserved boundary
        positions).

    The accepted sets are read from ``find_peaks_valleys`` called with exactly
    the pipeline's arguments, so they are the same objects ``find_mature_stage``
    consumes — including the ``result.iloc[zeros] = 0`` overwrite, which the
    package applies after prominence filtering.
    """
    data = np.asarray(z, dtype=float)
    n = data.size

    candidates = find_peaks_valleys(z)
    accepted = find_peaks_valleys(z, prominence=prominence,
                                  prominence_relative=prominence_relative,
                                  distance=distance)

    out = {"n": n, "boundary": tuple(i for i in (0, n - 1) if n > 0)}
    for kind, signed in (("peak", data), ("valley", -data)):
        cand = _label_positions(candidates, kind)
        acc = _label_positions(accepted, kind)
        rej = np.array(sorted(set(cand.tolist()) - set(acc.tolist())), dtype=int)

        interior = np.array([i for i in cand if i not in (0, n - 1)], dtype=int)
        prom_vals, threshold = _effective_threshold(
            signed, interior, prominence, prominence_relative)

        out[f"accepted_{kind}s"] = acc
        out[f"rejected_{kind}s"] = rej
        out[f"{kind}_prominences"] = dict(zip(interior.tolist(),
                                              prom_vals.tolist()))
        out[f"{kind}_threshold"] = threshold
    return out


def mature_ledger(df_after_decay: pd.DataFrame, **args_periods) -> list[dict]:
    """Candidate mature windows, and why the discarded ones were discarded.

    ``find_mature_stage`` writes a window around every qualifying z_valley and
    then applies a STRICT confirmation: a mature block survives only if the
    timestep before it is 'intensification' AND the timestep after it is
    'decay' (see the long comment in ``find_mature_stage`` — a plateau is only
    confirmed as the storm's peak once the storm is observed to decay). A
    window that fails leaves no trace whatsoever in the output, so from the
    final figure a mature phase that was found and then rejected is
    indistinguishable from one that was never found.

    This is the one place in the module that reconstructs a criterion the
    package does not expose as a callable — the window sizing lives inline
    inside ``find_mature_stage``. Two things keep it honest:

      * the amplitude branch calls ``_amplitude_mature_bounds`` (the package's
        own function) rather than re-deriving it; only the derivative branch's
        four lines of time-proportion arithmetic are transcribed;
      * the confirmed set is pinned by a fidelity test against
        ``find_mature_stage``'s actual output on real tracks.

    Reading the neighbours from the INPUT frame (the state after step 2) is
    equivalent to what the package does after writing the windows: a block's
    neighbour is by definition not itself mature (otherwise it would be part of
    the same contiguous block), so the mature writes cannot have changed it.

    Args:
        df_after_decay: the working frame after steps 1-2 have run — the exact
            state ``find_mature_stage`` receives in the pipeline.
        **args_periods: as built by ``build_args_periods``.

    Returns:
        list of records: ``start``/``end`` (window bounds), ``z_valley``,
        ``written`` (passed the length floor and was written), ``confirmed``
        (survived the neighbour check), ``reason`` (empty when confirmed),
        ``prev_label``/``next_label``.
    """
    threshold_mature_distance = args_periods['threshold_mature_distance']
    threshold_mature_length = args_periods['threshold_mature_length']
    length_scale = args_periods.get('length_scale', 'global')
    mature_method = args_periods.get('mature_method', 'derivative')
    mature_amplitude_fraction = args_periods.get('mature_amplitude_fraction', 0.90)

    df = df_after_decay
    index = df.index
    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index
    series_length = index[-1] - index[0]
    dt = index[1] - index[0]

    records = []
    written_mask = np.zeros(len(index), dtype=bool)

    for z_valley in z_valleys:
        next_z_peak = z_peaks[z_peaks > z_valley]
        previous_z_peak = z_peaks[z_peaks < z_valley]
        if len(previous_z_peak) == 0 or len(next_z_peak) == 0:
            records.append({
                "z_valley": z_valley, "start": z_valley, "end": z_valley,
                "written": False, "confirmed": False,
                "reason": "no z_peak on both sides",
                "prev_label": None, "next_label": None,
            })
            continue
        previous_z_peak = previous_z_peak[-1]
        next_z_peak = next_z_peak[0]

        if mature_method == 'amplitude':
            mature_start, mature_end = _amplitude_mature_bounds(
                df, previous_z_peak, z_valley, next_z_peak, mature_amplitude_fraction)
        else:
            mature_start = z_valley - (z_valley - previous_z_peak) * threshold_mature_distance
            mature_end = z_valley + (next_z_peak - z_valley) * threshold_mature_distance

        sl = _positional_slice(index, mature_start, mature_end)
        mature_indexes = index[sl]
        if len(mature_indexes) == 0:
            records.append({
                "z_valley": z_valley, "start": mature_start, "end": mature_end,
                "written": False, "confirmed": False,
                "reason": "empty window (no timestep inside it)",
                "prev_label": None, "next_label": None,
            })
            continue

        if mature_method == 'amplitude':
            written = True
            reason = ""
        else:
            mature_length_scale = ((next_z_peak - previous_z_peak)
                                   if length_scale == 'local' else series_length)
            floor = threshold_mature_length * mature_length_scale
            written = bool(mature_indexes[-1] - mature_indexes[0] > floor)
            reason = "" if written else (
                f"window too short: {mature_indexes[-1] - mature_indexes[0]} <= "
                f"threshold_mature_length x scale = {floor}")

        if written:
            written_mask[sl] = True
        records.append({
            "z_valley": z_valley, "start": mature_start, "end": mature_end,
            "written": written, "confirmed": False, "reason": reason,
            "prev_label": None, "next_label": None,
        })

    # ── the strict neighbour confirmation, per contiguous written block ──────
    periods = df['periods']
    for lo, hi in _runs(written_mask):
        block_start, block_end = index[lo], index[hi]
        prev_idx = block_start - dt
        next_idx = block_end + dt
        prev_label = (periods.loc[prev_idx] if prev_idx in periods.index else None)
        next_label = (periods.loc[next_idx] if next_idx in periods.index else None)
        prev_ok = prev_idx in periods.index and prev_label == 'intensification'
        next_ok = next_idx in periods.index and next_label == 'decay'
        why = []
        if not prev_ok:
            why.append("no preceding intensification"
                       if prev_idx in periods.index else
                       "block starts at the beginning of the series")
        if not next_ok:
            why.append("no following decay"
                       if next_idx in periods.index else
                       "block ends at the end of the series")
        for rec in records:
            if not rec["written"]:
                continue
            if rec["start"] > block_end or rec["end"] < block_start:
                continue
            rec["confirmed"] = bool(prev_ok and next_ok)
            rec["reason"] = "" if rec["confirmed"] else " · ".join(why)
            rec["prev_label"] = None if prev_label is None or pd.isna(prev_label) else str(prev_label)
            rec["next_label"] = None if next_label is None or pd.isna(next_label) else str(next_label)
            rec["block_start"], rec["block_end"] = block_start, block_end
    return records


def mature_confirmed_mask(df_after_decay: pd.DataFrame, records: list[dict]) -> np.ndarray:
    """Boolean mask of the mature windows the ledger says survive confirmation."""
    index = df_after_decay.index
    mask = np.zeros(len(index), dtype=bool)
    for rec in records:
        if rec.get("confirmed"):
            mask[_positional_slice(index, rec["start"], rec["end"])] = True
    return mask


# ══════════════════════════════════════════════════════════════════════════════
# PIECE 4b — incipient: the probe, rel vs tau, the knee, the produced boundary
# ══════════════════════════════════════════════════════════════════════════════

def knee_index(dz2, fraction: float = 0.5) -> int:
    """Position of the largest |d2z| in the leading `fraction` of the series.

    Diagnostic only — no phase rule reads it. It marks where curvature is
    strongest before the slope peaks, i.e. where a flat start turns into the
    rise the plateau rule is trying to time. Comparing it against the tau
    crossing shows whether tau is firing on the actual knee or somewhere on the
    flat before/after it.

    The search window is the leading `fraction` of the series (default: the
    first half) so the far larger curvature around the mature/decay turn cannot
    win. An empty window degrades to index 0.
    """
    a = np.abs(np.asarray(dz2, dtype=float))
    if a.size == 0:
        return 0
    stop = max(1, int(a.size * float(fraction)))
    window = a[:stop]
    if not np.isfinite(window).any():
        return 0
    return int(np.nanargmax(window))


def incipient_lens(z_unfil,
                   dz,
                   dz2,
                   signal: str = "derivative",
                   tau: float = 0.20,
                   crossing: str = "single",
                   k: int = 3,
                   smooth_window: int = 0,
                   smooth_polyorder: int = 3,
                   knee_fraction: float = 0.5) -> dict:
    """Everything the incipient layers draw, computed via the package helpers.

    Args:
        z_unfil: the UNFILTERED input vorticity (``df['z_unfil']`` /
            ``vorticity.zeta``) — the curve the "vorticity" probe reads.
        dz, dz2: the pipeline's first and second smoothed derivatives.
        signal, tau, crossing, k, smooth_window, smooth_polyorder: the plateau
            parameters, passed to the package helpers verbatim.
        knee_fraction: leading fraction of the series searched for the knee.

    Returns:
        dict with ``rel_raw``/``rel_smoothed`` (the normalised slope profile
        with the probe smoothing off and on), the corresponding boundaries
        ``boundary_raw``/``boundary_smoothed``, the probe curve before and
        after smoothing (``probe_raw``/``probe_smoothed``), ``knee``, and
        ``smoothing_applies`` — False when the window is inert because the
        probe reads the already-filtered derivative (see
        ``_incipient_plateau_rel``), in which case the two rel profiles are
        identical by construction.
    """
    z_raw = np.asarray(z_unfil, dtype=float)
    probe = pd.DataFrame({"z_unfil": z_raw,
                          "dz": np.asarray(dz, dtype=float)})

    rel_raw = _incipient_plateau_rel(probe, signal, 0, smooth_polyorder)
    rel_smoothed = _incipient_plateau_rel(probe, signal, smooth_window,
                                          smooth_polyorder)
    return {
        "rel_raw": rel_raw,
        "rel_smoothed": rel_smoothed,
        "boundary_raw": _incipient_plateau_boundary(rel_raw, tau, crossing, k),
        "boundary_smoothed": _incipient_plateau_boundary(rel_smoothed, tau,
                                                         crossing, k),
        "probe_raw": z_raw,
        "probe_smoothed": _smooth_incipient_probe(z_raw, smooth_window,
                                                  smooth_polyorder),
        "knee": knee_index(dz2, knee_fraction),
        "smoothing_applies": bool(int(smooth_window) > 0
                                  and signal == "vorticity"),
    }


def incipient_lead(df_result) -> int:
    """Length of the LEADING run of 'incipient' in a detection result.

    This is the boundary the run actually produced, READ BACK from the result
    rather than recomputed, so it stays correct under BOTH incipient methods.

    It can sit LATER than the plateau rule's own tau crossing, and that is not
    a discrepancy: ``find_incipient_period`` fills any leading NaN periods with
    'incipient' (the catch-all) before the plateau branch runs, so the produced
    phase may extend past the crossing. Showing both is the point — the gap
    between them is exactly the part of the incipient phase that tau did not
    decide.
    """
    inc = (df_result["periods"] == "incipient").to_numpy()
    if inc.size == 0 or not inc[0]:
        return 0
    return int(inc.size) if inc.all() else int(np.argmin(inc))
