# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    determine_periods.py                               :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: daniloceano <danilo.oceano@gmail.com>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2023/05/19 19:06:47 by danilocs          #+#    #+#              #
#    Updated: 2024/10/29 17:24:27 by daniloceano      ###   ########.fr        #
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

from typing import Union

import cyclophaser.lanczos_filter as lanfil
from cyclophaser.plots import plot_all_periods, plot_didactic
from cyclophaser.find_stages import find_incipient_period 
from cyclophaser.find_stages import find_intensification_period
from cyclophaser.find_stages import find_decay_period 
from cyclophaser.find_stages import find_mature_stage
from cyclophaser.find_stages import find_residual_period

def find_peaks_valleys(series):
    """
    Find peaks, valleys, and zero locations in a pandas series

    Args:
    series: pandas Series

    Returns:
    result: pandas Series with nans, "peak", "valley", and 0 in their respective positions
    """
    # Extract the values of the series
    data = series.values

    # Find peaks, valleys, and zero locations
    peaks = argrelextrema(data, np.greater_equal)[0]
    valleys = argrelextrema(data, np.less_equal)[0]
    zeros = np.where(data == 0)[0]

    # Create a series of NaNs
    result = pd.Series(index=series.index, dtype=object)
    result[:] = np.nan

    # Label the peaks, valleys, and zero locations
    result.iloc[peaks] = 'peak'
    result.iloc[valleys] = 'valley'
    result.iloc[zeros] = 0

    return result



def post_process_periods(df):
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
    
    # Replace periods of length dt with previous or next phase
    for index in df.index:
        period = df.loc[index, 'periods']
        if pd.notna(period) and len(period) == dt:
            prev_index = index - dt
            next_index = index + dt
            if prev_index in df.index and prev_index != df.index[0]:
                df.loc[index, 'periods'] = df.loc[prev_index, 'periods']
            elif next_index in df.index:
                df.loc[index, 'periods'] = df.loc[next_index, 'periods']
    
    return df

def periods_to_dict(df):
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
            # Append a suffix to the period name
            suffix = len(periods_dict[period_name]) + 1 if len(periods_dict[period_name]) > 2 else 2
            new_period_name = f"{period_name} {suffix}"
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
        cutoff_high=48.0):
    """
    Calculate derivatives of vorticity and perform filtering and smoothing.

    Args:
        zeta_df (pandas.DataFrame): Input DataFrame containing 'zeta' data (vorticity time series).
        
        use_filter (str or int, optional): Apply a Lanczos filter to vorticity data. Set to `'auto'` for default window 
            length or provide an integer specifying the desired window length in time steps. **Units**: Time steps.
            Default is `'auto'`.
        
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
        
        filter_derivatives (bool, optional): Apply filtering to the derivative results to further reduce noise. 
            Default is True.

    Returns:
        xarray.DataArray: A DataArray containing calculated vorticity variables, smoothed values, and their derivatives.

    Note:
        - Data Frequency and Parameters: If the data is not hourly, parameters such as `cutoff_low`, `cutoff_high`, 
          `replace_endpoints_with_lowpass`, and `use_smoothing` should be adjusted accordingly.
        - The Lanczos filter and Savgol filter are applied using external functions 'lanfil.lanczos_bandpass_filter'
          and 'savgol_filter', respectively.
        - The 'window_length_savgol' and 'window_length_savgol_2nd' calculations depend on the input 'use_smoothing' and
          'use_smoothing_twice' values or are determined automatically for 'auto'.
        - The filtering of derivatives is controlled by the 'filter_derivatives' parameter.
        - Savgol Window Requirements: Ensure `use_smoothing` and `use_smoothing_twice` are greater than or equal 
          to `savgol_polynomial` to avoid errors. For example, if `savgol_polynomial=3`, then `use_smoothing` must be 
          at least 3.

    Example:
        >>> df = process_vorticity(zeta_df, cutoff_low=168, cutoff_high=24)
    """

    # Parameters
    if use_filter == 'auto':
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
    
    if use_smoothing_twice == 'auto':
        if pd.Timedelta(zeta_df.index[-1] - zeta_df.index[0]) > pd.Timedelta('8D'):
            window_length_savgol_2nd = window_length_savgol * 2  | 1
        else:
            window_length_savgol_2nd = window_length_savgol | 1
    else:
        window_length_savgol_2nd = use_smoothing_twice
    
    # Check Savgol window length only if smoothing is enabled
    if use_smoothing and window_length_savgol < savgol_polynomial:
        raise ValueError("First Savgol window length (use_smoothing) must be >= savgol_polynomial.")

    if use_smoothing_twice and window_length_savgol_2nd < savgol_polynomial:
        raise ValueError("Second Savgol window length (use_smoothing_twice) must be >= savgol_polynomial.")
    
    # Convert dataframe to xarray
    da = zeta_df.to_xarray()

    # Apply Lanczos filter to vorticity, if requested
    if use_filter:
        filtered_vorticity = lanfil.lanczos_bandpass_filter(da['zeta'].copy(), window_length_lanczo, 1 / cutoff_low, 1 / cutoff_high)
        filtered_vorticity = xr.DataArray(filtered_vorticity, coords={'time':zeta_df.index})
    else:
        filtered_vorticity = da['zeta'].copy()
    da = da.assign(variables={'filtered_vorticity': filtered_vorticity})

    # Use the first and last 5% of a lower pass filtered vorticity
    # to replace bandpass filtered vorticity
    if use_filter and replace_endpoints_with_lowpass:
        num_samples = len(filtered_vorticity)
        num_copy_samples = int(0.05 * num_samples)
        filtered_vorticity_low_pass = lanfil.lanczos_filter(da.zeta.copy(), window_length_lanczo, replace_endpoints_with_lowpass)
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
                threshold_incipient_length: float = 0.4) -> pd.DataFrame:
    """
    Detect life cycle periods (e.g., intensification, decay, mature stages) from data.
    
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
    
    Returns:
        pd.DataFrame: DataFrame containing detected periods and associated information.
    """
    
    # Extract smoothed vorticity and derivatives
    z = vorticity.vorticity_smoothed2
    dz = vorticity.dz_dt_smoothed2
    dz2 = vorticity.dz_dt2_smoothed2

    # Create a DataFrame with the necessary variables
    df = z.to_dataframe().rename(columns={'vorticity_smoothed2': 'z'})
    df['z_unfil'] = vorticity.zeta.to_dataframe()
    df['dz'] = dz.to_dataframe()
    df['dz2'] = dz2.to_dataframe()

    # Find peaks, valleys, and zero locations for z, dz, and dz2
    df['z_peaks_valleys'] = find_peaks_valleys(df['z'])
    df['dz_peaks_valleys'] = find_peaks_valleys(df['dz'])
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
        "threshold_incipient_length": threshold_incipient_length
    }

    # Detect different stages of cyclone lifecycle
    df = find_intensification_period(df, **args_periods)
    df = find_decay_period(df, **args_periods)
    df = find_mature_stage(df, **args_periods)
    df = find_residual_period(df)

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
                      threshold_incipient_length=threshold_incipient_length)
    
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
                      use_filter: Union[str, int] = 'auto',
                      replace_endpoints_with_lowpass: int = 24,
                      use_smoothing: Union[bool, str, int] = 'auto',
                      use_smoothing_twice: Union[bool, str, int] = 'auto',
                      savgol_polynomial: int = 3,
                      cutoff_low: float = 168,
                      cutoff_high: float = 48.0,
                      threshold_intensification_length: float = 0.075,
                      threshold_intensification_gap: float = 0.075,
                      threshold_mature_distance: float = 0.125,
                      threshold_mature_length: float = 0.03,
                      threshold_decay_length: float = 0.075,
                      threshold_decay_gap: float = 0.075,
                      threshold_incipient_length: float = 0.4) -> pd.DataFrame:
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
        
        use_filter (Union[str, int], optional): Apply a Lanczos filter to the vorticity data. Choose `'auto'` to adapt 
            the window length based on the data size (half of dataset length) or specify an integer to set a specific window 
            length. **Units:** Time steps. Default is `'auto'`.
        
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
        cutoff_high=cutoff_high
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
        threshold_incipient_length=threshold_incipient_length
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