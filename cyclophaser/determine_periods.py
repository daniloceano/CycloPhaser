# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    determine_periods.py                               :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: daniloceano <danilo.oceano@gmail.com>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2023/05/19 19:06:47 by danilocs          #+#    #+#              #
#    Updated: 2024/11/08 16:51:45 by daniloceano      ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os
import csv
import warnings

import xarray as xr
import pandas as pd
import numpy as np

from scipy.signal import argrelextrema
from scipy.signal import savgol_filter
from scipy.signal import peak_prominences

from typing import Union

import cyclophaser.lanczos_filter as lanfil
from cyclophaser.plots import plot_all_periods, plot_didactic
from cyclophaser.find_stages import find_incipient_period 
from cyclophaser.find_stages import find_intensification_period
from cyclophaser.find_stages import find_decay_period 
from cyclophaser.find_stages import find_mature_stage
from cyclophaser.find_stages import find_residual_period

def _collapse_plateaux(indices):
    """Collapse runs of consecutive indices to their midpoint (floor for even runs).

    argrelextrema with np.greater_equal / np.less_equal marks every member of a
    flat plateau as an extremum.  This helper reduces each such run to a single
    representative index so downstream phase-detection logic sees one extremum
    per plateau rather than a burst of duplicates.

    Example: [2, 3, 4] → [3]  (odd run, exact midpoint)
             [2, 3]    → [2]  (even run, floor of mean)
    """
    if len(indices) == 0:
        return indices
    collapsed = []
    run = [indices[0]]
    for idx in indices[1:]:
        if idx == run[-1] + 1:
            run.append(idx)
        else:
            collapsed.append(int(np.floor(np.mean(run))))
            run = [idx]
    collapsed.append(int(np.floor(np.mean(run))))
    return np.array(collapsed, dtype=indices.dtype)


def find_peaks_valleys(series, prominence=None, prominence_relative=None, distance=None):
    """Find peaks, valleys, and zero locations in a pandas Series.

    Uses argrelextrema with np.greater_equal / np.less_equal so that a flat
    plateau at a local extremum is still detected (strict > / < would miss it).
    Consecutive indices returned by argrelextrema (plateau members) are collapsed
    to a single representative point — the floor-midpoint of the run — to avoid
    duplicate markings and peak/valley overlap within plateaux.

    NOTE (#14 — pending fix): argrelextrema uses mode='clip' by default, which
    compares boundary indices against themselves as the "missing" neighbour.
    This means index 0 is marked as a peak whenever data[0] >= data[1], and
    index N-1 whenever data[-1] >= data[-2], regardless of whether the boundary
    is a true extremum or merely a smoothing artefact (most visible in dz and
    dz2, whose boundary values are distorted by savgol_filter mode='nearest').
    Fixing this without incorrectly removing genuine boundary extrema in z
    (which correspond to the start/end of the cyclone lifecycle at a vorticity
    minimum) requires additional investigation and a dedicated visual checkpoint.

    Prominence modes
    ----------------
    Two prominence-based filters are available and may be used independently or
    together.  Both act only on *interior* extrema; boundary indices (0 and N-1)
    are always preserved.

    **Relative (recommended)**: ``prominence_relative`` — fraction of the
    largest prominence among all interior candidates.  Adapts automatically to
    each cyclone's intensity, making it robust across weak and strong systems.
    Example: 0.10 keeps only extrema whose prominence is ≥ 10 % of the
    dominant extremum's prominence.

    **Absolute**: ``prominence`` — fixed threshold in the same units as the
    signal.  Useful when the scale is known, but requires re-tuning for
    datasets with different vorticity magnitudes.

    When both are active, absolute is applied first; relative is then applied
    to the surviving set (denominator = max prominence of that surviving set).

    Args:
        series:              pandas Series (z, dz, or dz2 from the preprocessed
                             vorticity).
        prominence:          float or None. Absolute minimum prominence threshold.
                             Default None disables absolute filtering (no-op).
        prominence_relative: float or None. Relative threshold as a fraction of
                             the largest interior prominence.  Example: 0.10
                             removes any interior extremum whose prominence is
                             below 10 % of the most prominent one.  Default None
                             disables relative filtering (no-op).
        distance:            int or None. Minimum number of steps separating any
                             two surviving same-type extrema.  When candidates
                             are closer than this, the one with higher prominence
                             is kept.  Boundary indices are always preserved and
                             count toward the exclusion radius.  Default None
                             disables distance filtering (no-op).

    Returns:
        result: pandas Series with NaN, 'peak', 'valley', or 0 at each position
    """
    data = series.values
    N = len(data)

    # Detect raw extrema (>= / <= catches flat-top plateaux as multiple indices)
    peaks   = argrelextrema(data, np.greater_equal)[0]
    valleys = argrelextrema(data, np.less_equal)[0]
    zeros   = np.where(data == 0)[0]

    # Collapse each run of consecutive plateau indices to a single midpoint
    peaks   = _collapse_plateaux(peaks)
    valleys = _collapse_plateaux(valleys)

    # After collapsing, a shared midpoint can still appear in both arrays when a
    # perfectly flat plateau sits at a true minimum (the plateau members satisfy
    # both >= and <= relative to their identical neighbours).  Valleys take
    # priority (assignment order below), so remove any overlap from peaks to keep
    # the result unambiguous.
    overlap = np.intersect1d(peaks, valleys)
    if len(overlap):
        peaks = peaks[~np.isin(peaks, overlap)]

    # Optional prominence / distance refinement (no-op when all three are None)
    if prominence is not None or prominence_relative is not None or distance is not None:
        peaks   = _refine_extrema(data,  data, peaks,   prominence, prominence_relative, distance, N)
        valleys = _refine_extrema(data, -data, valleys, prominence, prominence_relative, distance, N)

    # Build result series
    result = pd.Series(index=series.index, dtype=object)
    result[:] = np.nan
    result.iloc[peaks]   = 'peak'
    result.iloc[valleys] = 'valley'
    result.iloc[zeros]   = 0

    return result


def _refine_extrema(data, signed_data, candidates, prominence, prominence_relative, distance, N):
    """Filter *candidates* by prominence (absolute and/or relative) and/or distance.

    Boundary indices (0 and N-1) are unconditionally preserved.  Interior
    candidates are pruned in order: absolute prominence → relative prominence →
    minimum distance (greedy, highest-prominence-first).  Prominences are
    computed once on the initial interior set and kept in sync after each
    filtering step.

    Args:
        data:                original data array (passed for API symmetry; not
                             used directly — signed_data carries the sign).
        signed_data:         data for the extremum type: ``data`` for peaks,
                             ``-data`` for valleys.
        candidates:          1-D integer array of candidate indices (collapsed).
        prominence:          float absolute threshold, or None.
        prominence_relative: float relative threshold (fraction of max interior
                             prominence), or None.
        distance:            int minimum separation in steps, or None.
        N:                   total series length.

    Returns:
        numpy array of surviving candidate indices (sorted ascending).
    """
    if len(candidates) == 0:
        return candidates

    boundary = {i for i in (0, N - 1) if i in set(candidates)}
    interior = np.array([i for i in candidates if i not in boundary])

    # Compute prominence once for all interior candidates.
    # Reused by all three filters; kept in sync after each filtering step.
    if len(interior) > 0 and (prominence is not None or prominence_relative is not None or distance is not None):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prom_vals = peak_prominences(signed_data, interior)[0]
    else:
        prom_vals = np.zeros(len(interior))

    # --- Absolute prominence filtering ---
    if prominence is not None and len(interior) > 0:
        mask      = prom_vals >= prominence
        interior  = interior[mask]
        prom_vals = prom_vals[mask]

    # --- Relative prominence filtering ---
    # Threshold = prominence_relative × max(prom_vals of surviving interior).
    # If absolute was applied first, the denominator is the max of the post-
    # absolute set, so the relative fraction is applied consistently within
    # the surviving population.
    if prominence_relative is not None and len(interior) > 0:
        max_prom = prom_vals.max() if len(prom_vals) > 0 else 0.0
        if max_prom > 0.0:
            mask      = prom_vals >= prominence_relative * max_prom
            interior  = interior[mask]
            prom_vals = prom_vals[mask]

    # --- Distance filtering (greedy, highest prominence first) ---
    if distance is not None:
        order = np.argsort(-prom_vals) if len(interior) > 0 else np.array([], dtype=int)
        kept  = list(boundary)
        for rank in order:
            idx = interior[rank]
            if all(abs(idx - k) >= distance for k in kept):
                kept.append(idx)
        surviving_interior = np.array([i for i in interior if i in set(kept)])
    else:
        surviving_interior = interior

    result = np.array(sorted(boundary | set(surviving_interior.tolist())), dtype=np.intp)
    return result

def post_process_periods(df):
    """
    Post-processing of periods DataFrame.

    This function takes a periods DataFrame and perform the following post-processing steps:

    1. Find consecutive blocks of intensification and decay periods.
    2. Fill NaN periods between consecutive intensification or decay blocks with the previous phase.
    3. Replace periods of length dt with previous or next phase.

    Parameters
    ----------
    df : pandas DataFrame
        DataFrame containing the periods information.

    Returns
    -------
    df : pandas DataFrame
        Post-processed DataFrame.

    """
    dt = df.index[1] - df.index[0]
    
    # Find consecutive blocks of intensification and decay
    intensification_blocks = np.split(df[df['periods'] == 'intensification'].index, np.where(np.diff(df[df['periods'] == 'intensification'].index) != dt)[0] + 1)
    decay_blocks = np.split(df[df['periods'] == 'decay'].index, np.where(np.diff(df[df['periods'] == 'decay'].index) != dt)[0] + 1)
    
    # Fill NaN periods between consecutive intensification or decay blocks
    for blocks in [intensification_blocks, decay_blocks]:
        if len(blocks) > 1:
            phase = df.loc[blocks[0][0], 'periods']
            for i in range(len(blocks)):
                block = blocks[i]
                if i != 0:
                    if len(block) > 0:
                        last_index_prev_block = blocks[i -1][-1]
                        first_index_current_block = block[0]
                        preiods_between = df.loc[
                            (last_index_prev_block + dt):(first_index_current_block - dt)]['periods']
                        if all(pd.isna(preiods_between.unique())):
                            df.loc[preiods_between.index, 'periods'] = phase
    
    # Replace singleton periods (isolated single timestep) with the surrounding phase.
    # The original condition `len(period) == dt` compared a string length to a Timedelta,
    # which is always False — so this block never executed.
    for index in df.index:
        period = df.loc[index, 'periods']
        if pd.notna(period):
            prev_index = index - dt
            next_index = index + dt
            prev_same = prev_index in df.index and df.loc[prev_index, 'periods'] == period
            next_same = next_index in df.index and df.loc[next_index, 'periods'] == period
            if not prev_same and not next_same:
                if prev_index in df.index and prev_index != df.index[0]:
                    df.loc[index, 'periods'] = df.loc[prev_index, 'periods']
                elif next_index in df.index:
                    df.loc[index, 'periods'] = df.loc[next_index, 'periods']
    
    return df

def periods_to_dict(df):
    """
    Convert periods DataFrame to a dictionary of periods.

    Parameters
    ----------
    df : pandas DataFrame
        DataFrame containing the periods information.

    Returns
    -------
    periods_dict : dict
        Dictionary of periods, where the keys are the period names and the values are tuples of start and end indices.

    """
    periods_dict = {}

    # Find the start and end indices of each period
    period_starts = df[df['periods'] != df['periods'].shift()].index
    period_ends = df[df['periods'] != df['periods'].shift(-1)].index

    # Iterate over the periods and create keys in the dictionary
    for i in range(len(period_starts)):
        period_name = df.loc[period_starts[i], 'periods']
        start = period_starts[i]
        end = period_ends[i]

        # Check if the period name already exists in the dictionary
        if period_name in periods_dict.keys():
            # Count all existing entries for this phase (base name + any "name N" variants)
            count = sum(1 for k in periods_dict if k == period_name or k.startswith(f"{period_name} "))
            new_period_name = f"{period_name} {count + 1}"
            periods_dict[new_period_name] = (start, end)
        else:
            periods_dict[period_name] = (start, end)
        
    return periods_dict

def export_periods_to_csv(phases_dict, periods_outfile_path):

    filepath = f"{periods_outfile_path}.csv"

    # Extract phase names, start dates, and end dates from the periods dictionary
    data = [(phase, start, end) for phase, (start, end) in phases_dict.items()]
    
    # Write the data to a CSV file
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['', 'start', 'end'])  # Write the header
        writer.writerows(data)  # Write the data rows

    print(f"{filepath} written.")

def process_vorticity(
        zeta_df,
        use_filter='auto',
        replace_endpoints_with_lowpass=24,
        use_smoothing='auto',
        use_smoothing_twice='auto', 
        savgol_polynomial=3,
        cutoff_low=168,
        cutoff_high=48.0,
        boundary_padding='zero'):
    """
    Calculate derivatives of vorticity and perform filtering and smoothing.

    Args:
        zeta_df (pandas.DataFrame): Input DataFrame containing 'zeta' data (vorticity time series).
        
        use_filter (str or bool or int, optional): Apply a Lanczos filter to vorticity data. Set to `'auto'`
            (or `True`, which is equivalent — see the "use_filter=True note" below) for the default window
            length of `len(series)//2`, `False` to skip filtering entirely, or an integer to specify the
            window length explicitly in time steps. **Units**: Time steps. Default is `'auto'`.
        
        replace_endpoints_with_lowpass (int, optional): If set, replaces the endpoints of the series with a lowpass 
            filter using a specified window length, helping to stabilize edge effects. **Units**: Time steps. Default is 24.
        
        use_smoothing (str or int, optional): Apply Savgol smoothing to the filtered vorticity. Set to `'auto'` for a 
            default window length or specify an integer value as the desired window length. Must be greater than or equal 
            to `savgol_polynomial`. **Units**: Time steps. Default is `'auto'`. **To deactivate**, set `use_smoothing` 
            to `False`.
        
        use_smoothing_twice (str or int, optional): Apply Savgol smoothing a second time for additional noise reduction. 
            Same requirements as `use_smoothing`. Default is `'auto'`.
        
        savgol_polynomial (int, optional): Polynomial order for Savgol smoothing. This must be less than or equal to the 
            window length (`use_smoothing` or `use_smoothing_twice` if specified). Default is 3.
        
        cutoff_low (float, optional): Low-frequency cutoff for the Lanczos filter, used to remove very low-frequency 
            noise. Suitable for time series data with hourly resolution. **Units**: Time steps. Default is 168.
        
        cutoff_high (float, optional): High-frequency cutoff for the Lanczos filter, used to remove high-frequency noise. 
            Suitable for time series data with hourly resolution. **Units**: Time steps. Default is 48.0.

        boundary_padding (str, optional): How the series is extended beyond its own
            ends before the Lanczos convolution. ``"zero"`` (default) reproduces the
            exact behaviour of all versions prior to this option; ``"reflect"``
            (recommended) and ``"edge"`` remove most of the zero-padding boundary
            artefact. See the "boundary_padding note" below. Only meaningful when
            ``use_filter`` is truthy. Default is ``"zero"``.

    use_filter=True note (behaviour change)
    ----------------------------------------
    ``use_filter=True`` now means the same as ``use_filter='auto'``: filtering on,
    window length ``len(series)//2``. It emits a ``UserWarning`` saying so.

    This is a BUG FIX WITH A BEHAVIOUR CHANGE. ``bool`` is a subclass of ``int``
    in Python, so the previous ``if use_filter == 'auto': ... else:
    window_length_lanczo = use_filter`` read ``True`` as the integer **1**. A
    1-tap Lanczos kernel is a single scalar multiply (0.0714 for
    ``cutoff_low=168``/``cutoff_high=24``), i.e. no convolution at all — so a
    caller asking for filtering silently received NONE, and the result differed
    from ``use_filter=False`` only by a constant factor that every downstream
    (difference-based) criterion cancels out.

    **Any series processed with ``use_filter=True`` on an earlier version was
    effectively unfiltered.** Parameter sets calibrated under that setting were
    therefore calibrated on an unfiltered signal and must be re-validated.

    ``use_filter=1`` still means a literal window length of 1 — the bool check
    runs before the int check, so ``True`` and ``1`` are no longer conflated.
    ``use_filter=False`` still disables filtering.

    boundary_padding note
    ----------------------
    ``lanczos_bandpass_filter`` and ``lanczos_filter`` have always convolved via
    ``scipy.signal.convolve(..., mode="same")``, which implicitly ZERO-PADS the
    input beyond its own ends. Vorticity has a non-zero floor (order -5e-5 s^-1),
    so those "missing" samples are a jump to zero rather than a neutral
    continuation, and two properties of this configuration amplify the damage:
    the kernel is about HALF the series length (``window_length_lanczo =
    len(zeta) // 2`` under ``use_filter='auto'``; measured kernel/series length
    ratio has a median of 0.494 over the 51-track calibration set), and the
    bandpass kernel does not actually reject DC at these window lengths
    (``sum(weights)`` median 0.629; ``|H(DC)|/|H|max`` median 0.79).

    The consequence is a step between the boundary value and the interior worth a
    median of **74 % of the cyclone's own peak-to-peak amplitude**, spread as a
    ramp over the boundary zone -- which is ``M//2`` ~ **24 % of the series at
    each end, about 48 % of every series**. The ramp carries the sign of a
    spurious DEEPENING, and on the calibration set it alone accounts for >= 80 %
    of the slope measured at t0 in **51/51 tracks**.

    Measured effect of the option on that set (normalised ``|dz|`` at the first
    and last sample, median over 51 tracks):

    ==========  ==========  =============  ================================
    mode        t0          last sample    detected phase sequences changed
    ==========  ==========  =============  ================================
    "zero"      0.95        0.98           -- (reference)
    "reflect"   0.42        0.35           14/51
    "edge"      0.50        0.38           13/51
    ==========  ==========  =============  ================================

    (For scale: a lightly-smoothed finite difference of the RAW series gives a
    median of 0.29 at t0, so "reflect" lands close to the uncontaminated signal.)

    ``"reflect"`` is the RECOMMENDED value; the default stays ``"zero"`` so that
    every existing call and every calibrated parameter set is reproduced exactly.
    Switching modes changes the smoothed signal in the boundary zone and
    therefore requires re-validating any calibrated thresholds -- it is not a
    drop-in swap.

    ``replace_endpoints_with_lowpass`` was introduced as a palliative for this
    same artefact and itself calls ``lanczos_filter``, i.e. it replaces
    zero-padded bandpass endpoints with zero-padded lowpass endpoints. With
    ``boundary_padding="reflect"`` it loses its reason to exist and is a
    candidate for future deprecation; it is deliberately left unchanged here and
    still defaults to 24.

    The Lanczos kernels themselves (``pass_weights``, ``pass_weights_bandpass``)
    and the Savitzky-Golay stages are NOT affected by this option: the correction
    is purely a boundary condition on the convolution.

    Returns:
        xarray.DataArray: A DataArray containing calculated vorticity variables, smoothed values, and their derivatives.

    Note:
        - Data Frequency and Parameters: If the data is not hourly, parameters such as `cutoff_low`, `cutoff_high`,
          `replace_endpoints_with_lowpass`, and `use_smoothing` should be adjusted accordingly.
        - The Lanczos filter and Savgol filter are applied using external functions 'lanfil.lanczos_bandpass_filter'
          and 'savgol_filter', respectively.
        - The 'window_length_savgol' and 'window_length_savgol_2nd' calculations depend on the input 'use_smoothing' and
          'use_smoothing_twice' values or are determined automatically for 'auto'.
        - Savgol Window Requirements: Ensure `use_smoothing` and `use_smoothing_twice` are greater than or equal
          to `savgol_polynomial` to avoid errors. For example, if `savgol_polynomial=3`, then `use_smoothing` must be
          at least 3.

    Example:
        >>> df = process_vorticity(zeta_df, cutoff_low=168, cutoff_high=24)
    """

    lanfil._validate_padding(boundary_padding)

    # Parameters
    #
    # use_filter accepts 'auto', a bool, or an explicit integer window length.
    # The bool branch MUST be tested before the int branch: bool is a subclass of
    # int in Python, so `isinstance(True, int)` is True and a bare int check would
    # silently read True as "window length 1". A 1-tap Lanczos kernel is a scalar
    # multiply -- no convolution at all -- so before this was fixed, asking for
    # filtering with use_filter=True disabled it instead (see the "use_filter=True
    # note" in the docstring above).
    if isinstance(use_filter, bool):
        # True means "filter on, pick the window for me" -- i.e. 'auto'.
        # False falls through to the `if use_filter:` guard below and skips
        # filtering entirely; the value assigned here is never used in that case.
        window_length_lanczo = len(zeta_df) // 2
        if use_filter:
            warnings.warn(
                "use_filter=True is interpreted as 'auto' (Lanczos window = "
                f"len(series)//2 = {window_length_lanczo} timesteps). Prior to "
                "this fix, True was read as the integer 1, which reduced the "
                "Lanczos filter to a single tap (a scalar multiply) and "
                "effectively disabled it -- results obtained with use_filter=True "
                "on earlier versions were UNFILTERED. Pass use_filter='auto' to "
                "silence this warning, or an explicit integer to set the window "
                "length yourself.",
                UserWarning,
            )
    elif use_filter == 'auto':
        window_length_lanczo = len(zeta_df) // 2
    else:
        window_length_lanczo = use_filter

    # Calculate window lengths for Savgol smoothing
    if use_smoothing == 'auto':
        if pd.Timedelta(zeta_df.index[-1] - zeta_df.index[0]) > pd.Timedelta('8D'):
            window_length_savgol = len(zeta_df) // 4 | 1
        else:
            window_length_savgol = len(zeta_df) // 2 | 1
    else:
        window_length_savgol = use_smoothing
        if isinstance(use_smoothing, int) and not isinstance(use_smoothing, bool):
            _orig = window_length_savgol
            window_length_savgol = window_length_savgol | 1  # ensure odd (consistent with 'auto' branch)
            _max_valid = len(zeta_df) if len(zeta_df) % 2 == 1 else len(zeta_df) - 1
            if window_length_savgol > _max_valid:
                window_length_savgol = _max_valid
            if window_length_savgol != _orig:
                warnings.warn(
                    f"use_smoothing={_orig} adjusted to {window_length_savgol} "
                    f"(savgol_filter requires an odd window length not exceeding "
                    f"the series length of {len(zeta_df)}).",
                    UserWarning
                )

    if use_smoothing_twice == 'auto':
        if pd.Timedelta(zeta_df.index[-1] - zeta_df.index[0]) > pd.Timedelta('8D'):
            window_length_savgol_2nd = window_length_savgol * 2  | 1
        else:
            window_length_savgol_2nd = window_length_savgol | 1
    else:
        window_length_savgol_2nd = use_smoothing_twice
        if isinstance(use_smoothing_twice, int) and not isinstance(use_smoothing_twice, bool):
            _orig_2nd = window_length_savgol_2nd
            window_length_savgol_2nd = window_length_savgol_2nd | 1  # ensure odd
            _max_valid = len(zeta_df) if len(zeta_df) % 2 == 1 else len(zeta_df) - 1
            if window_length_savgol_2nd > _max_valid:
                window_length_savgol_2nd = _max_valid
            if window_length_savgol_2nd != _orig_2nd:
                warnings.warn(
                    f"use_smoothing_twice={_orig_2nd} adjusted to {window_length_savgol_2nd} "
                    f"(savgol_filter requires an odd window length not exceeding "
                    f"the series length of {len(zeta_df)}).",
                    UserWarning
                )
    
    # Check Savgol window length only if smoothing is enabled
    if use_smoothing and window_length_savgol < savgol_polynomial:
        raise ValueError("First Savgol window length (use_smoothing) must be >= savgol_polynomial.")

    if use_smoothing_twice and window_length_savgol_2nd < savgol_polynomial:
        raise ValueError("Second Savgol window length (use_smoothing_twice) must be >= savgol_polynomial.")
    
    # Convert dataframe to xarray
    da = zeta_df.to_xarray()

    # Apply Lanczos filter to vorticity, if requested
    if use_filter:
        filtered_vorticity = lanfil.lanczos_bandpass_filter(
            da['zeta'].copy(), window_length_lanczo, 1 / cutoff_low, 1 / cutoff_high,
            boundary_padding=boundary_padding)
        filtered_vorticity = xr.DataArray(filtered_vorticity, coords={'time':zeta_df.index})
    else:
        filtered_vorticity = da['zeta'].copy()
    da = da.assign(variables={'filtered_vorticity': filtered_vorticity})

    # Use the first and last 5% of a lower pass filtered vorticity
    # to replace bandpass filtered vorticity
    if use_filter and replace_endpoints_with_lowpass:
        num_samples = len(filtered_vorticity)
        num_copy_samples = int(0.05 * num_samples)
        filtered_vorticity_low_pass = lanfil.lanczos_filter(
            da.zeta.copy(), window_length_lanczo, replace_endpoints_with_lowpass,
            boundary_padding=boundary_padding)
        filtered_vorticity.data[:num_copy_samples] = filtered_vorticity_low_pass.data[:num_copy_samples]
        filtered_vorticity.data[-num_copy_samples:] = filtered_vorticity_low_pass.data[-num_copy_samples:]  

    # Check if spurious oscillations are still present
    oscillation_start = abs(filtered_vorticity[1].values - filtered_vorticity[0].values)
    oscillation_end = abs(filtered_vorticity[-1].values - filtered_vorticity[-2].values)
    mean_magnitude = np.mean(np.abs(filtered_vorticity.values))

    # Compare to threshold
    oscillation_threshold = 0.2
    if (oscillation_start > oscillation_threshold * mean_magnitude) or (oscillation_end > oscillation_threshold * mean_magnitude):
        warnings.warn(
            "Detected potential spurious oscillations at the series boundaries. "
            "Consider adjusting 'use_filter', 'replace_endpoints_with_lowpass', or 'use_smoothing'."
        )
    
    # Smooth filtered vorticity with Savgol filter if smoothing is enabled
    if use_smoothing:
        # Apply the first Savgol smoothing pass
        vorticity_smoothed = xr.DataArray(
            savgol_filter(filtered_vorticity, window_length_savgol, savgol_polynomial, mode="nearest"),
            coords={'time': zeta_df.index}
        )
        # Apply the second smoothing pass if use_smoothing_twice is enabled
        if use_smoothing_twice:
            vorticity_smoothed2 = xr.DataArray(
                savgol_filter(vorticity_smoothed, window_length_savgol_2nd, savgol_polynomial, mode="nearest"),
                coords={'time': zeta_df.index}
            )
        else:
            vorticity_smoothed2 = vorticity_smoothed
    else:
        # If use_smoothing is False, no smoothing is applied, so use filtered_vorticity directly
        vorticity_smoothed = filtered_vorticity
        vorticity_smoothed2 = vorticity_smoothed  # No further smoothing applied if use_smoothing is False
    
    da = da.assign(variables={'vorticity_smoothed': vorticity_smoothed,
                              'vorticity_smoothed2': vorticity_smoothed2})
    
    # Calculate the derivatives from smoothed (or not) vorticity
    dzfilt_dt = vorticity_smoothed2.differentiate('time', datetime_unit='h')
    dzfilt_dt2 = dzfilt_dt.differentiate('time', datetime_unit='h')

    # Filter derivatives: not an option because they are too noisy. Otherwise the results are too lame
    # Use the same window length as 'auto'
    if not window_length_savgol:
        if pd.Timedelta(zeta_df.index[-1] - zeta_df.index[0]) > pd.Timedelta('8D'):
            window_length_savgol_derivatives = len(zeta_df) // 4 | 1
        else:
            window_length_savgol_derivatives = len(zeta_df) // 2 | 1
    else:
        window_length_savgol_derivatives = window_length_savgol
        
    # Savgol window length must be >= savgol_polynomial
    if window_length_savgol_derivatives < savgol_polynomial:
        window_length_savgol_derivatives = savgol_polynomial

    dz_dt_filt = xr.DataArray(
        savgol_filter(dzfilt_dt, window_length_savgol_derivatives, savgol_polynomial, mode="nearest"),
        coords={'time':zeta_df.index})
    dz_dt2_filt = xr.DataArray(
        savgol_filter(dzfilt_dt2, window_length_savgol_derivatives, savgol_polynomial, mode="nearest"),
        coords={'time':zeta_df.index})
    
    dz_dt_smoothed2 = xr.DataArray(
        savgol_filter(dz_dt_filt, window_length_savgol_derivatives, savgol_polynomial, mode="nearest"),
        coords={'time':zeta_df.index})
    dz_dt2_smoothed2 = xr.DataArray(
        savgol_filter(dz_dt2_filt, window_length_savgol_derivatives, savgol_polynomial, mode="nearest"),
        coords={'time':zeta_df.index})

    # Assign variables to xarray
    da = da.assign(variables={'dz_dt_filt': dz_dt_filt,
                              'dz_dt2_filt': dz_dt2_filt,
                              'dz_dt_smoothed2': dz_dt_smoothed2,
                              'dz_dt2_smoothed2': dz_dt2_smoothed2})

    return da 

def get_periods(vorticity,
                plot: Union[str, bool] = False,
                plot_steps: Union[str, bool] = False,
                export_dict: Union[str, bool] = False,
                threshold_intensification_length: float = 0.075,
                threshold_intensification_gap: float = 0.075,
                threshold_mature_distance: float = 0.125,
                threshold_mature_length: float = 0.03,
                threshold_decay_length: float = 0.075,
                threshold_decay_gap: float = 0.075,
                threshold_incipient_length: float = 0.4,
                prominence: float = None,
                prominence_relative: float = None,
                distance: int = None,
                length_scale: str = "global",
                mature_method: str = "derivative",
                mature_amplitude_fraction: float = 0.90,
                decay_tail_amplitude_fraction: float = None) -> pd.DataFrame:
    """
    Detect life cycle periods (e.g., intensification, decay, mature stages) from data.

    Detection pipeline and phase precedence
    ----------------------------------------
    The detection functions are called in the following fixed order:

        1. find_intensification_period
        2. find_decay_period
        3. find_mature_stage
        4. find_residual_period
        5. post_process_periods   (gap-filling and singleton removal)
        6. find_incipient_period  (fills any remaining NaN at the series start)

    Each function writes to the 'periods' column of the DataFrame.  Functions
    called later can **overwrite** regions already labelled by earlier functions.
    The most significant consequence is that ``find_decay_period`` (step 2) may
    overwrite timesteps that ``find_intensification_period`` (step 1) had already
    marked, because both functions scan the same z-peaks/valleys and their
    detected intervals can overlap.

    decay_tail_amplitude_fraction note
    ------------------------------------
    ``find_residual_period`` (step 4) has a catch-all rule that labels the NaN
    tail after the last 'decay' block 'residual'. On a single-cycle series this
    can be triggered by an "orphan" interior z_peak — a peak with no surviving
    z_valley after it, which can pass ``prominence_relative`` filtering purely
    because relative prominence is computed separately for peaks and valleys
    (the largest interior peak always scores 1.0 by construction) — which
    truncates ``find_decay_period``'s decay block early, well before the
    cyclone has actually dissipated. With ``decay_tail_amplitude_fraction`` set
    (opt-in; default None reproduces prior behaviour exactly),
    ``find_residual_period`` checks whether that NaN tail contains a genuine
    re-deepening — a drop below the tail's running-maximum z larger than this
    fraction of the cycle's own peak-to-valley amplitude — and, if not, extends
    'decay' over the tail instead of leaving it for the catch-all to mark
    'residual'. It only ever adds 'decay' to already-NaN timesteps and never
    touches ``z_peaks_valleys`` or any other extrema, so it cannot affect the
    mature window (already computed by step 3 at this point in the pipeline).
    See ``find_stages.find_residual_period`` for the full mechanism, rationale,
    and the validated calibration (0.05, confirmed safe over (0.0356, 0.0651]
    on the research/adaptive-thresholds 51-track calibration set).

    Threshold calibration note
    ---------------------------
    Because of this precedence, the practical effect of a threshold may be
    smaller than expected.  For example, ``threshold_intensification_gap``
    controls the maximum gap that is bridged between two intensification blocks;
    however, if ``find_decay_period`` subsequently marks those same timesteps as
    decay, the gap-bridging has no visible effect on the final output.  When
    calibrating thresholds, always inspect the final 'periods' column rather than
    assuming each parameter acts in isolation.

    length_scale note
    ------------------
    ``threshold_intensification_length``, ``threshold_intensification_gap``,
    ``threshold_mature_length``, ``threshold_decay_length`` and
    ``threshold_decay_gap`` are all fractions of a *length*.  With the default
    ``length_scale="global"`` that length is the whole input series
    (``df.index[-1] - df.index[0]``) — the historical behaviour, unchanged.
    With ``length_scale="local"`` each candidate segment is instead checked
    against the span of the local oscillation it belongs to (see
    ``find_stages._local_cycle_scale``), so a threshold like 0.075 means
    "7.5% of *this cycle*" rather than "7.5% of the whole track". This matters
    for series where one segment (e.g. a long intensification) or one life
    cycle dominates the total length: under "global", that segment inflates
    the denominator for every other threshold check in the series, which can
    reject legitimate short segments elsewhere (a short decay after a long
    intensification, or an entire smaller second life cycle in a two-cycle
    track). ``threshold_mature_distance`` and ``threshold_incipient_length``
    are unaffected by this option — they were already local.

    mature_method note
    -------------------
    With the default ``mature_method="derivative"`` the mature window around
    each z_valley is sized as a fixed proportion (``threshold_mature_distance``)
    of the *time* distance to the neighbouring z_peak — the historical
    behaviour, unchanged. With ``mature_method="amplitude"`` the window is
    instead the contiguous stretch of z around the z_valley whose value stays
    within ``mature_amplitude_fraction`` of the cycle's own peak-to-valley
    amplitude on each side (see ``find_stages._amplitude_mature_bounds`` for
    the full implementation). Concretely, for each side (previous_z_peak on
    the intensification side, next_z_peak on the decay side) the amplitude is
    measured as ``z[side_peak] - z[z_valley]`` — the peak-to-valley DROP, never
    the extremum's absolute value (vorticity has a non-zero floor, so "90% of
    the raw extreme" would not be a meaningful fraction on its own — same
    reasoning as ``prominence_relative`` in ``find_peaks_valleys``). The level
    a timestep's z must stay at or below to still count as mature is then
    ``z[side_peak] - mature_amplitude_fraction * amplitude_side``, walked
    outward from z_valley and stopped at the first violation on that side
    (kept strictly contiguous). The two sides are evaluated independently,
    mirroring the existing asymmetric treatment of ``threshold_mature_distance``.
    This matters because "derivative" locates the window using the smoothed
    *derivative*'s extrema, which can lag the true z minimum by a few
    timesteps (see "Phase detection lag note" below) and so displace the
    mature window forward of where the cyclone was actually most intense;
    "amplitude" anchors directly on z's own value and carries no such lag.
    Both methods are still subject to the same downstream physical
    requirement — a candidate mature window is only confirmed if the cyclone
    is subsequently observed to decay (see the neighbour-confirmation comment
    in ``find_stages.find_mature_stage``) — this is unrelated to
    ``threshold_mature_length`` and applies in both modes equally.

    ``threshold_mature_length``/``length_scale``, however, apply ONLY to
    ``mature_method="derivative"``. In "amplitude" mode they have NO effect:
    that minimum-duration floor was calibrated for "derivative"'s
    fixed-time-proportion window, and reusing it for "amplitude" was observed
    to discard well-centred amplitude windows for being narrow — narrowness
    that is an expected, physically meaningful outcome of
    ``mature_amplitude_fraction`` there, not a defect to filter out. No
    replacement minimum-duration safeguard exists for "amplitude" at this
    time (deliberate, to evaluate the method unconstrained first).

    Phase detection lag note
    ------------------------
    The detected *start* of a phase may lag the true onset of that phase in the
    input vorticity series by up to approximately 15–18 h (5–6 timesteps at
    3-hourly resolution).  This lag is an inherent consequence of the Lanczos +
    Savgol filtering chain: the smoothed signal requires several timesteps to
    build up enough amplitude for the algorithm to reliably identify a new
    feature.  The lag is most pronounced for ``residual`` (re-intensification
    after decay), where it was consistently observed to be 15–18 h across
    controlled synthetic test cases.  Other transitions (e.g. the onset of
    intensification when no explicit incipient segment precedes it) can show
    similar lags.  When interpreting results or defining search windows for
    event attribution, a margin of at least 18 h around detected phase
    boundaries is recommended.

    Args:
        vorticity (xarray.DataArray): Processed vorticity dataset.
        plot (Union[str, bool], optional): Path to save plots or False to disable plotting. Default is False.
        plot_steps (Union[str, bool], optional): Path to save step-by-step plots or False to disable. Default is False.
        export_dict (Union[str, bool], optional): Path to export periods to CSV or False to disable. Default is False.
        threshold_intensification_length (float, optional): Minimum intensification length. Default is 0.075.
        threshold_intensification_gap (float, optional): Maximum gap in intensification periods. Default is 0.075.
        threshold_mature_distance (float, optional): Distance threshold for mature stage detection. Default is 0.125.
        threshold_mature_length (float, optional): Minimum mature stage length. Default is 0.03.
        threshold_decay_length (float, optional): Minimum decay stage length. Default is 0.075.
        threshold_decay_gap (float, optional): Maximum gap in decay periods. Default is 0.075.
        threshold_incipient_length (float, optional): Minimum incipient length. Default is 0.4.
        prominence (float, optional): Absolute minimum prominence threshold for
            z-extrema filtering. Default None (no-op). See ``find_peaks_valleys``
            for the full description of prominence modes.
        prominence_relative (float, optional): Relative prominence threshold as a
            fraction of the most prominent interior z-extremum. **Recommended
            mode**: adapts to each cyclone's intensity, generalising across weak
            and strong systems without re-tuning. Example: 0.10 keeps only
            z-extrema whose prominence is ≥ 10 % of the dominant extremum's
            prominence. Default None (no-op).
        distance (int, optional): Minimum separation in timesteps between two
            same-type z-extrema. Default None (no-op).
        length_scale (str, optional): "global" (default) or "local". See the
            "length_scale note" above. Default "global" reproduces the exact
            behaviour of all versions prior to this option.
        mature_method (str, optional): "derivative" (default) or "amplitude".
            "derivative" is the original method: the mature window is a fixed
            proportion (``threshold_mature_distance``) of the *time* distance
            between the z_valley and each neighbouring z_peak. "amplitude"
            (opt-in) instead defines the mature window as the contiguous
            stretch of z around the z_valley that stays within
            ``mature_amplitude_fraction`` of the cycle's own peak-to-valley
            amplitude on each side — anchored on z's amplitude rather than on
            dz extrema, so it does not inherit the smoothed-derivative phase
            lag that can displace "derivative"'s window forward of the true z
            minimum on some real cyclones. See
            ``find_stages._amplitude_mature_bounds`` for the full definition.
            Default "derivative" reproduces the exact behaviour of all
            versions prior to this option.
        mature_amplitude_fraction (float, optional): Fraction (0, 1] of each
            side's peak-to-valley amplitude a timestep's z must still reach to
            count as mature. Only used when ``mature_method="amplitude"``.
            Default 0.90.
        decay_tail_amplitude_fraction (float, optional): Fraction (0, 1] of the
            cycle's peak-to-valley amplitude. See the "decay_tail_amplitude_fraction
            note" above and ``find_stages.find_residual_period`` for the full
            mechanism. Default None disables this check, reproducing the exact
            behaviour of all versions prior to this option.

    Returns:
        pd.DataFrame: DataFrame containing detected periods and associated information.

    Raises:
        ValueError: If ``length_scale`` is not "global" or "local", if
            ``mature_method`` is not "derivative" or "amplitude", or if
            ``decay_tail_amplitude_fraction`` is not None and not in (0, 1].
    """
    if length_scale not in ("global", "local"):
        raise ValueError(f"length_scale must be 'global' or 'local', got {length_scale!r}.")
    if mature_method not in ("derivative", "amplitude"):
        raise ValueError(f"mature_method must be 'derivative' or 'amplitude', got {mature_method!r}.")

    # Extract smoothed vorticity and derivatives
    z = vorticity.vorticity_smoothed2
    dz = vorticity.dz_dt_smoothed2
    dz2 = vorticity.dz_dt2_smoothed2

    # Create a DataFrame with the necessary variables
    df = z.to_dataframe().rename(columns={'vorticity_smoothed2': 'z'})
    df['z_unfil'] = vorticity.zeta.to_dataframe()
    df['dz'] = dz.to_dataframe()
    df['dz2'] = dz2.to_dataframe()

    # Find peaks, valleys, and zero locations for z, dz, and dz2.
    # prominence filters are applied only to z: they remove spurious vorticity
    # bumps irrelevant to the life cycle.  Applying them to dz would discard the
    # low-amplitude early dz valleys that find_incipient_period relies on to
    # locate the incipient/intensification boundary.
    df['z_peaks_valleys']   = find_peaks_valleys(df['z'],
                                                  prominence=prominence,
                                                  prominence_relative=prominence_relative,
                                                  distance=distance)
    df['dz_peaks_valleys']  = find_peaks_valleys(df['dz'])
    df['dz2_peaks_valleys'] = find_peaks_valleys(df['dz2'])

    # Initialize periods column
    df['periods'] = np.nan
    df['periods'] = df['periods'].astype('object')

    args_periods = {
        "threshold_intensification_length": threshold_intensification_length,
        "threshold_intensification_gap": threshold_intensification_gap,
        "threshold_mature_distance": threshold_mature_distance,
        "threshold_mature_length": threshold_mature_length,
        "threshold_decay_length": threshold_decay_length,
        "threshold_decay_gap": threshold_decay_gap,
        "threshold_incipient_length": threshold_incipient_length,
        "length_scale": length_scale,
        "mature_method": mature_method,
        "mature_amplitude_fraction": mature_amplitude_fraction,
        "decay_tail_amplitude_fraction": decay_tail_amplitude_fraction,
    }

    # Detect different stages of cyclone lifecycle
    df = find_intensification_period(df, **args_periods)
    df = find_decay_period(df, **args_periods)
    df = find_mature_stage(df, **args_periods)
    df = find_residual_period(df, **args_periods)

    # Fill gaps between consecutive periods and clean up too short periods
    df = post_process_periods(df)

    # Detect incipient stages
    df = find_incipient_period(df, **args_periods)

    # Check for gaps or unexpected residual stages
    detected_periods = df['periods'].dropna().unique()
    if 'residual' in detected_periods[:-1]:
        warnings.warn(
            "Residual period detected in the middle of the time series, which may indicate data quality issues. "
            "Adjusting pre-processing options might help resolve this issue.", 
            UserWarning
        )
    gaps = df['periods'].isna().sum()
    if gaps > 0:
        warnings.warn(
            f"{gaps} time steps are unclassified, which may suggest data quality issues. "
            "Consider adjusting pre-processing options to reduce these gaps.", 
            UserWarning
        )

    # Convert periods to dictionary with start and end times
    periods_dict = periods_to_dict(df)

    # Create plots, if requested
    if plot:
        plot_all_periods(periods_dict, df, ax=None, vorticity=vorticity, periods_outfile_path=plot)
    if plot_steps:
        plot_didactic(df, vorticity, plot_steps,
                      threshold_intensification_length=threshold_intensification_length,
                      threshold_intensification_gap=threshold_intensification_gap,
                      threshold_mature_distance=threshold_mature_distance,
                      threshold_mature_length=threshold_mature_length,
                      threshold_decay_length=threshold_decay_length,
                      threshold_decay_gap=threshold_decay_gap,
                      threshold_incipient_length=threshold_incipient_length,
                      length_scale=length_scale,
                      mature_method=mature_method,
                      mature_amplitude_fraction=mature_amplitude_fraction)
    
    # Export to CSV if requested
    if export_dict:
        export_periods_to_csv(periods_dict, export_dict)

    return df

def determine_periods(series: Union[list, np.ndarray, pd.Series, xr.DataArray],
                      x: Union[list, pd.DatetimeIndex] = None,
                      plot: Union[str, bool] = False,
                      plot_steps: Union[str, bool] = False,
                      export_dict: Union[str, bool] = False,
                      hemisphere: str = "southern",
                      use_filter: Union[str, bool, int] = 'auto',
                      replace_endpoints_with_lowpass: int = 24,
                      use_smoothing: Union[bool, str, int] = 'auto',
                      use_smoothing_twice: Union[bool, str, int] = 'auto',
                      savgol_polynomial: int = 3,
                      cutoff_low: float = 168,
                      cutoff_high: float = 48.0,
                      boundary_padding: str = "zero",
                      threshold_intensification_length: float = 0.075,
                      threshold_intensification_gap: float = 0.075,
                      threshold_mature_distance: float = 0.125,
                      threshold_mature_length: float = 0.03,
                      threshold_decay_length: float = 0.075,
                      threshold_decay_gap: float = 0.075,
                      threshold_incipient_length: float = 0.4,
                      prominence: float = None,
                      prominence_relative: float = None,
                      distance: int = None,
                      length_scale: str = "global",
                      mature_method: str = "derivative",
                      mature_amplitude_fraction: float = 0.90,
                      decay_tail_amplitude_fraction: float = None) -> pd.DataFrame:
    """
    Determine meteorological periods from a series of vorticity data.

    Args:
        series (Union[list, np.ndarray, pd.Series, xr.DataArray]): The vorticity time series to be analyzed.
            Accepts list, numpy array, pandas Series, or xarray DataArray formats. **Note:** The series does not need to 
            be in any specific units, though vorticity data is recommended. Other fields like SLP or geopotential height 
            may work but are untested.
        
        x (Union[list, pd.DatetimeIndex], optional): Temporal labels for `series`, expected as a list of datetime values 
            or a `pd.DatetimeIndex`. Only required if `series` is a list or array; automatically inferred from the `series` 
            index if using `pd.Series` or `xr.DataArray`. **Must match the length of `series**`.
        
        plot (Union[str, bool], optional): Path to save generated plots. Set to `False` to skip plotting. Default is `False`.
        
        plot_steps (Union[str, bool], optional): Path to save step-by-step didactic plots, useful for understanding each 
            phase of the algorithm. Set to `False` to disable. Default is `False`.
        
        export_dict (Union[str, bool], optional): Path to save detected periods as a CSV file. Set to `False` to skip 
            exporting. Default is `False`.

        hemisphere (str, optional): Hemisphere of the data. Set to `"southern"` (default) to apply southern hemisphere 
            conventions, or `"northern"` to automatically multiply input values by `-1` for northern hemisphere compatibility.
            **Note**: This setting is particularly relevant for vorticity data, where conventions vary by hemisphere. 
            When working with **wind speed data**, use `"northern"` to detect maxima in both hemispheres. For **sea level 
            pressure (SLP) data**, set to `"southern"` as the default convention.
        
        use_filter (Union[str, bool, int], optional): Apply a Lanczos filter to the vorticity data. Choose `'auto'`
            — or `True`, which is equivalent — to adapt the window length based on the data size (half of dataset
            length); `False` to skip filtering; or an integer to set a specific window length. `True` emits a
            `UserWarning` naming the resulting window: it used to be read as the integer 1, i.e. a single-tap
            kernel that disabled filtering altogether, so results obtained with `use_filter=True` on earlier
            versions were UNFILTERED. See the "use_filter=True note" in `process_vorticity`. **Units:** Time steps.
            Default is `'auto'`.
        
        replace_endpoints_with_lowpass (int, optional): Use a lowpass filter to replace the endpoints of the series, 
            stabilizing edge effects. Specify the window length. **Units:** Time steps. Default is 24.
        
        use_smoothing (Union[bool, str, int], optional): Apply Savitzky-Golay smoothing to the vorticity series. Choose 
            `True` to use a default window, specify an integer window length, or use `'auto'` to adapt the length based 
            on data. **Must be greater than or equal to `savgol_polynomial`** to avoid errors. Default is `'auto'`.
        
        use_smoothing_twice (Union[bool, str, int], optional): Apply a second Savitzky-Golay smoothing pass for additional 
            noise reduction. Choose `True`, `False`, or specify an integer. Default is `'auto'`.
        
        savgol_polynomial (int, optional): Polynomial order for Savitzky-Golay smoothing. **Must be less than or equal 
            to the window length specified in `use_smoothing` and `use_smoothing_twice`.** Default is 3.
        
        cutoff_low (float, optional): Low-frequency cutoff for the Lanczos filter to reduce low-frequency noise. Suitable 
            for hourly data. **Units:** Time steps. Default is 168.
        
        cutoff_high (float, optional): High-frequency cutoff for the Lanczos filter to reduce high-frequency noise. Suitable 
            for hourly data. **Units:** Time steps. Default is 48.0.

        boundary_padding (str, optional): How the series is extended beyond its own ends
            before the Lanczos convolution: `"zero"` (default), `"reflect"` (recommended)
            or `"edge"`. The historical `"zero"` behaviour comes from
            `scipy.signal.convolve(..., mode="same")` and injects a spurious deepening
            ramp worth a median of 74 % of the cyclone's amplitude over roughly 48 % of
            every series; `"reflect"` takes the normalised |dz| at t0 from a median 0.95
            down to 0.42 on the 51-track calibration set. The default remains `"zero"`
            so existing calls and calibrated parameter sets reproduce exactly — see the
            "boundary_padding note" in `process_vorticity` for the full mechanism,
            the measured numbers, and the consequences for `replace_endpoints_with_lowpass`.
        
        threshold_intensification_length (float, optional): Minimum required length of intensification phase as a fraction 
            of the dataset. Default is 0.075.
        
        threshold_intensification_gap (float, optional): Maximum allowed gap in intensification phase. Default is 0.075.
        
        threshold_mature_distance (float, optional): Threshold for mature phase duration, used to adjust the identification 
            of the mature stage. Default is 0.125.
        
        threshold_mature_length (float, optional): Minimum required length of the mature phase as a fraction of the dataset. 
            Default is 0.03.
        
        threshold_decay_length (float, optional): Minimum required length of the decay phase as a fraction of the dataset. 
            Default is 0.075.
        
        threshold_decay_gap (float, optional): Maximum allowed gap in decay phase. Default is 0.075.
        
        threshold_incipient_length (float, optional): Minimum required length of the incipient phase as a fraction of the
            dataset. Default is 0.4.

        length_scale (str, optional): "global" (default) or "local". Controls what
            length ``threshold_intensification_length``, ``threshold_intensification_gap``,
            ``threshold_mature_length``, ``threshold_decay_length`` and
            ``threshold_decay_gap`` are fractions *of*. "global" (default) uses the
            whole series length, reproducing the exact behaviour of all versions
            prior to this option. "local" uses the span of the local cycle each
            candidate segment belongs to instead — see ``get_periods`` for the
            full rationale and ``find_stages._local_cycle_scale`` for the precise
            definition. ``threshold_mature_distance`` and
            ``threshold_incipient_length`` are unaffected; they were already local.

        mature_method (str, optional): "derivative" (default) or "amplitude".
            See ``get_periods`` for the full rationale and
            ``find_stages._amplitude_mature_bounds`` for the precise definition
            of the "amplitude" method. Default "derivative" reproduces the
            exact behaviour of all versions prior to this option.

        mature_amplitude_fraction (float, optional): Fraction (0, 1] of each
            side's peak-to-valley amplitude a timestep's z must still reach to
            count as mature. Only used when ``mature_method="amplitude"``.
            Default 0.90.

        decay_tail_amplitude_fraction (float, optional): Fraction (0, 1] of the
            cycle's peak-to-valley amplitude that the NaN tail after the last
            decay block must dip below (relative to its own running maximum)
            to be treated as a genuine re-intensification rather than extended
            decay. See ``get_periods`` for the full rationale (an "orphan"
            z_peak that can truncate decay early on single-cycle series) and
            ``find_stages.find_residual_period`` for the precise mechanism.
            Default None disables this check, reproducing the exact behaviour
            of all versions prior to this option.

    Returns:
        pd.DataFrame: DataFrame containing detected cyclone life cycle phases and associated metadata.

    Raises:
        ValueError: If `series` is not a list, numpy array, pandas Series, or xarray DataArray, or if `use_smoothing` 
            or `use_smoothing_twice` are less than `savgol_polynomial`.

    Note:
        - **Data Frequency**: The default values for `cutoff_low`, `cutoff_high`, `replace_endpoints_with_lowpass`, 
          and `use_smoothing` assume hourly data. Adjust these parameters for other time resolutions.
        - **Savgol Smoothing**: Ensure `use_smoothing` and `use_smoothing_twice` are integers greater than or equal 
          to `savgol_polynomial`. To disable, set `use_smoothing` to `False`.
    """
    # Require temporal labels when the caller passes raw data without an index.
    if isinstance(series, (list, np.ndarray)) and x is None:
        raise ValueError(
            "x must be provided when series is a list or numpy array. "
            "Pass a list of datetime values or a pd.DatetimeIndex as x."
        )

    # Check hemisphere
    if hemisphere.lower() not in ["southern", "northern"]:
        raise ValueError("Hemisphere must be 'southern' or 'northern'.")
    
    # Adjust for hemisphere if needed (apply sign change before conversion to pd.Series)
    if hemisphere.lower() == "northern":
        if isinstance(series, list):
            series = [-val for val in series]
        else:
            series = -series  # Applies directly if series is already compatible with negation

    # Convert various input types to Series
    if isinstance(series, (list, np.ndarray)):
        series = pd.Series(series)
    elif isinstance(series, xr.DataArray):
        series = series.to_series()
    elif isinstance(series, pd.DataFrame):
        raise ValueError("Input series cannot be a DataFrame.")

    # Use index as x if available
    if x is None and isinstance(series, pd.Series):
        x = series.index
    
    # Ensure x has the correct length if provided
    if x is not None and len(x) != len(series):
        raise ValueError("Length of 'x' and 'series' must be the same.")

    # Create DataFrame with series as 'zeta'
    zeta_df = pd.DataFrame({'zeta': series})
    zeta_df.index = x

    if use_smoothing_twice and not use_smoothing:
        use_smoothing_twice = False
        warnings.warn("use_smoothing_twice is set but use_smoothing is not. Disabling use_smoothing_twice.")

    # Process vorticity using the provided arguments
    vorticity = process_vorticity(
        zeta_df,
        use_filter=use_filter,
        replace_endpoints_with_lowpass=replace_endpoints_with_lowpass,
        use_smoothing=use_smoothing,
        use_smoothing_twice=use_smoothing_twice,
        savgol_polynomial=savgol_polynomial,
        cutoff_low=cutoff_low,
        cutoff_high=cutoff_high,
        boundary_padding=boundary_padding
    )

    # Call `get_periods` with the appropriate arguments
    df = get_periods(
        vorticity=vorticity,
        plot=plot,
        plot_steps=plot_steps,
        export_dict=export_dict,
        threshold_intensification_length=threshold_intensification_length,
        threshold_intensification_gap=threshold_intensification_gap,
        threshold_mature_distance=threshold_mature_distance,
        threshold_mature_length=threshold_mature_length,
        threshold_decay_length=threshold_decay_length,
        threshold_decay_gap=threshold_decay_gap,
        threshold_incipient_length=threshold_incipient_length,
        prominence=prominence,
        prominence_relative=prominence_relative,
        distance=distance,
        length_scale=length_scale,
        mature_method=mature_method,
        mature_amplitude_fraction=mature_amplitude_fraction,
        decay_tail_amplitude_fraction=decay_tail_amplitude_fraction,
    )

    return df

# This is purely for testing purposes
def main():
    from cyclophaser import example_file
    
    # Read data from the CSV file using pandas
    track = pd.read_csv(example_file, parse_dates=[0], delimiter=';', index_col=[0])
    
    # Define different input formats for testing
    series_pd = track['min_max_zeta_850']
    x_pd = track.index  # Use DataFrame index as the temporal range

    # Convert to numpy array for testing
    series_np = np.array(series_pd)
    x_np = np.array(x_pd)

    # Convert to xarray DataArray for testing
    series_xr = xr.DataArray(series_pd.values, coords=[x_pd], dims="time")

    # Convert to plain lists for testing
    series_list = series_pd.tolist()
    x_list = x_pd.tolist()

    # Test with default parameters
    print("\nTesting with default parameters but without filtering...")
    result_default = determine_periods(series_pd, x=x_pd, plot="test_default", plot_steps="test_steps_default")
    print(result_default.head())

    # Test with default parameters but without filtering
    print("\nTesting with default parameters but without filtering...")
    result_default = determine_periods(series_pd, x=x_pd, plot="test_default_no_filter", plot_steps="test_steps_default_no_filter", use_filter=False)
    print(result_default.head())

    # Test with default parameters but without smoothing
    print("\nTesting with default parameters but without smoothing...")
    result_default = determine_periods(series_pd, x=x_pd, plot="test_default_no_smoothing", plot_steps="test_steps_default_no_smoothing", use_smoothing=False)
    print(result_default.head())

    # Test using pandas Series and index
    print("Testing with pandas Series and index...")
    result_pd = determine_periods(series_pd, x=x_pd, plot="test_pandas", plot_steps="test_steps_pandas")
    print(result_pd.head())

    # Test using numpy arrays
    print("\nTesting with numpy arrays...")
    result_np = determine_periods(series_np, x=x_np, plot="test_numpy", plot_steps="test_steps_numpy")
    print(result_np.head())

    # Test using xarray DataArray
    print("\nTesting with xarray DataArray...")
    result_xr = determine_periods(series_xr, plot="test_xarray", plot_steps="test_steps_xarray")
    print(result_xr.head())

    # Test using lists
    print("\nTesting with lists...")
    result_list = determine_periods(series_list, x=x_list, plot="test_list", plot_steps="test_steps_list")
    print(result_list.head())

    # Additional example usage with custom parameters
    print("\nTesting with custom parameters...")
    result_custom = determine_periods(series_pd, x=x_pd, plot='test_custom', cutoff_low=100, cutoff_high=20, use_filter=True, use_smoothing=10, use_smoothing_twice=False)
    print(result_custom.head())

    # Test with custom thresholds
    print("\nTesting with custom thresholds...")
    result_bad_options = determine_periods(
        series=series_pd,
        x=x_pd,
        plot="test_bad_options",
        plot_steps="test_steps_bad_options",
        export_dict=False,
        use_filter=False,
        use_smoothing_twice=False,
        threshold_intensification_length=0.25,
        threshold_intensification_gap=0.075,
        threshold_mature_distance=0.125,
        threshold_mature_length=0.03,
        threshold_decay_length=0.075,
        threshold_decay_gap=0.075,
        threshold_incipient_length=0.4
    )
    print(result_bad_options.head())

if __name__ == '__main__':
    main()