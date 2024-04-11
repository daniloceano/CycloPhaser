# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    determine_periods.py                               :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: daniloceano <danilo.oceano@gmail.com>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2023/05/19 19:06:47 by danilocs          #+#    #+#              #
#    Updated: 2024/04/11 19:59:55 by daniloceano      ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os
import csv

import xarray as xr
import pandas as pd
import numpy as np

from scipy.signal import argrelextrema
from scipy.signal import savgol_filter 

import cyclophaser.lanczos_filter as lanfil
from cyclophaser.plots import plot_all_periods, plot_didactic
from cyclophaser.find_stages import find_incipient_period 
from cyclophaser.find_stages import find_intensification_period
from cyclophaser.find_stages import find_decay_period 
from cyclophaser.find_stages import find_mature_stage
from cyclophaser.find_stages import find_residual_period

def check_create_folder(DirName, verbosity=False):
    if not os.path.exists(DirName):
                os.makedirs(DirName)
                print(DirName+' created')
    else:
        if verbosity:
            print(DirName+' directory exists')


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
        zeta_df (pandas.DataFrame): Input dataframe containing 'zeta' data.
        use_filter (bool or str, optional): Apply Lanczos filter to vorticity. 'auto' for default window length or specify length. Default is 'auto'.
        replace_endpoints_with_lowpass (float, optional): Replace endpoints with a lowpass filter and choose the window length. Default is 24.
        use_smoothing (bool or str, optional): Apply Savgol smoothing to filtered vorticity. 'auto' for default window length or specify length. Default is 'auto'.
        use_smoothing_twice (bool or str, optional): Apply Savgol smoothing twice to the first smoothed vorticity. 'auto' for default window length or specify length. Default is 'auto'.
        savgol_polynomial (int, optional): Polynomial order for Savgol smoothing. Default is 3.
        cutoff_low (float, optional): Low-frequency cutoff for Lanczos filter. Default is 168.
        cutoff_high (float, optional): High-frequency cutoff for Lanczos filter. Default is 48.0.
        filter_derivatives (bool, optional): Apply filtering to derivative results. Default is True.

    Returns:
        xarray.DataArray: A DataArray containing various calculated variables and derivatives.

    Note:
        - The Lanczos filter and Savgol filter are applied using external functions 'lanfil.lanczos_bandpass_filter'
          and 'savgol_filter', respectively.
        - The 'window_length_savgol' and 'window_length_savgol_2nd' calculations depend on the input 'use_smoothing' and
          'use_smoothing_twice' values or are determined automatically for 'auto'.
        - The filtering of derivatives is controlled by the 'filter_derivatives' parameter.

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
    
    # Savgol window can't be higher than the polynomial
    if window_length_savgol_2nd < savgol_polynomial:
        window_length_savgol_2nd = 3
    
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
    
    # Smooth filtered vorticity with Savgol filter
    if use_smoothing:
        vorticity_smoothed = xr.DataArray(
            savgol_filter(filtered_vorticity, window_length_savgol, savgol_polynomial, mode="nearest"),
            coords={'time': zeta_df.index})
        if use_smoothing_twice:
            vorticity_smoothed2 = xr.DataArray(
                savgol_filter(vorticity_smoothed, window_length_savgol_2nd, savgol_polynomial, mode="nearest"),
                coords={'time': zeta_df.index})
        else:
            vorticity_smoothed2 = vorticity_smoothed
    else:
        vorticity_smoothed = filtered_vorticity
        vorticity_smoothed2 = vorticity_smoothed
    
    da = da.assign(variables={'vorticity_smoothed': vorticity_smoothed,
                              'vorticity_smoothed2': vorticity_smoothed2})
    
    # Calculate the derivatives from smoothed (or not) vorticity
    dzfilt_dt = vorticity_smoothed2.differentiate('time', datetime_unit='h')
    dzfilt_dt2 = dzfilt_dt.differentiate('time', datetime_unit='h')

    # Filter derivatives: not an option because they are too noisy. Otherwise the results are too lame
    dz_dt_filt = xr.DataArray(
        savgol_filter(dzfilt_dt, window_length_savgol, savgol_polynomial, mode="nearest"),
        coords={'time':zeta_df.index})
    dz_dt2_filt = xr.DataArray(
        savgol_filter(dzfilt_dt2, window_length_savgol, savgol_polynomial, mode="nearest"),
        coords={'time':zeta_df.index})
    
    dz_dt_smoothed2 = xr.DataArray(
        savgol_filter(dz_dt_filt, window_length_savgol, savgol_polynomial, mode="nearest"),
        coords={'time':zeta_df.index})
    dz_dt2_smoothed2 = xr.DataArray(
        savgol_filter(dz_dt2_filt, window_length_savgol, savgol_polynomial, mode="nearest"),
        coords={'time':zeta_df.index})

    # Assign variables to xarray
    da = da.assign(variables={'dz_dt_filt': dz_dt_filt,
                              'dz_dt2_filt': dz_dt2_filt,
                              'dz_dt_smoothed2': dz_dt_smoothed2,
                              'dz_dt2_smoothed2': dz_dt2_smoothed2})

    return da 

def get_periods(vorticity,  plot=False, plot_steps=False, export_dict=False, periods_args=None):
    default_args = {
        'threshold_intensification_length': 0.125,
        'threshold_intensification_gap': 0.075,
        'threshold_mature_distance': 0.125,
        'threshold_mature_length': 0.03,
        'threshold_decay_length': 0.075,
        'threshold_decay_gap': 0.075,
        'threshold_incipient_length': 0.4
    }

    # Update the default arguments with any user-provided arguments
    if periods_args is not None:
        default_args.update(periods_args)

    z = vorticity.vorticity_smoothed2
    dz = vorticity.dz_dt_smoothed2
    dz2 = vorticity.dz_dt2_smoothed2

    df = z.to_dataframe().rename(columns={'vorticity_smoothed2':'z'})
    df['z_unfil'] = vorticity.zeta.to_dataframe()
    df['dz'] = dz.to_dataframe()
    df['dz2'] = dz2.to_dataframe()

    df['z_peaks_valleys'] = find_peaks_valleys(df['z'])
    df['dz_peaks_valleys'] = find_peaks_valleys(df['dz'])
    df['dz2_peaks_valleys'] = find_peaks_valleys(df['dz2'])

    df['periods'] = np.nan
    df['periods'] = df['periods'].astype('object')

    df = find_intensification_period(df, **default_args)
    df = find_decay_period(df, **default_args)
    df = find_mature_stage(df, **default_args)
    df = find_residual_period(df)

    # 1) Fill consecutive intensification or decay periods that have NaNs between them
    # 2) Remove periods that are too short and fill with the previous period
    # (or the next one if there is no previous period)
    df = post_process_periods(df)

    df = find_incipient_period(df, **default_args)

    # Pass the periods to a dictionary with each period's name as key
    #  and their corresponding start and end times as values.
    # Also, add extra 6 hours to the start and end of the periods as "confidence intervals"
    periods_dict = periods_to_dict(df)

    # Create plots, if requested
    if plot:
        plot_all_periods(periods_dict, df, ax=None, vorticity=vorticity, periods_outfile_path=plot)
    if plot_steps:
        plot_didactic(df, vorticity, plot_steps, **default_args)
    # Export csv, if requested
    if export_dict:
        export_periods_to_csv(periods_dict, export_dict)

    return df

def determine_periods(series,
                      x=None,
                      plot=False,
                      plot_steps=False,
                      export_dict=False,
                      process_vorticity_args=None,
                      periods_args=None):
    """
    Determine meteorological periods from a series of vorticity data.

    Args:
        series (list): List of vorticity values.
        x (list, optional): Temporal range or other labels for the series. Default is None.
        vorticity_column (str, optional): Column name for the 'zeta' data in the DataFrame. Default is 'zeta'.
        plot (str, optional): Whether to generate and save plots. Default is False. Input string is the path to save the plots.
        plot_steps (str, optional): Whether to generate didactic step-by-step plots. Default is False. Input string is the path to save the plots.
        export_dict (str, optional): Whether to export periods as a CSV dictionary. Default is False. Input string is the path to save the CSV file.
        process_vorticity_args (dict, optional): Custom arguments for the process_vorticity function. Default is None.

    Returns:
        pandas.DataFrame: DataFrame containing determined periods and associated information.

    Raises:
        ValueError: If the input 'series' is not a list.
    """

    if not isinstance(series, list):
        raise ValueError("Input 'series' must be a list of values.")

    # Create DataFrame from the series
    if x is not None:
        if len(x) != len(series):
            raise ValueError("Length of 'x' and 'series' must be the same.")
        zeta_df = pd.DataFrame({'zeta': series}, index=x)
    else:
        zeta_df = pd.DataFrame({'zeta': series})

    # Rest of the function remains the same as before
    if process_vorticity_args is None:
        process_vorticity_args = {}
    vorticity = process_vorticity(zeta_df.copy(), **process_vorticity_args)

    args = [plot, plot_steps, export_dict]
    if periods_args is None:
        periods_args = {}
    return get_periods(vorticity.copy(), *args, periods_args)


if __name__ == '__main__':
    # Read the data from the CSV file
    track_file = '../tests/test.csv'
    track = pd.read_csv(track_file, parse_dates=[0], delimiter=';', index_col=[0])

    # Extract the vorticity data as a list and the index as a temporal range
    series = track['min_max_zeta_850'].tolist()
    x = track.index.tolist()  # Using the DataFrame index as the temporal range

    # Testing options
    process_vorticity_args = {
            "use_filter": False,
            "use_smoothing_twice": False
        }

    periods_args= {
        'threshold_intensification_length': 0.10,  # Decreased threshold
        'threshold_intensification_gap': 0.05,
        'threshold_mature_distance': 0.10,
        'threshold_mature_length': 0.02,
        'threshold_decay_length': 0.06,
        'threshold_decay_gap': 0.06,
        'threshold_incipient_length': 0.35
        }

    # Test the determine_periods function
    result = determine_periods(series,
            x=x,
            plot="test",
            plot_steps="test_steps",
            export_dict=False,
            process_vorticity_args=process_vorticity_args,
            periods_args=periods_args)
