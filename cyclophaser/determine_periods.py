# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    determine_periods.py                               :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: Danilo <danilo.oceano@gmail.com>           +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2023/05/19 19:06:47 by danilocs          #+#    #+#              #
#    Updated: 2023/08/28 16:21:53 by Danilo           ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os
import csv

import xarray as xr
import pandas as pd
import numpy as np

from scipy.signal import argrelextrema
from scipy.signal import savgol_filter 

import lanczos_filter as lanfil
from plots import plot_all_periods, plot_didactic

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

def find_mature_stage(df):
    dz_peaks = df[df['dz_peaks_valleys'] == 'peak'].index
    dz_valleys = df[df['dz_peaks_valleys'] == 'valley'].index
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

        # Calculate the distances between z valley and the previous/next dz valleys
        distance_to_previous_z_peak = z_valley - previous_z_peak
        distance_to_next_z_peak = next_z_peak - z_valley

        mature_distance_previous = 0.125 * distance_to_previous_z_peak
        mature_distance_next = 0.125 * distance_to_next_z_peak

        mature_start = z_valley - mature_distance_previous
        mature_end = z_valley + mature_distance_next

        # Mature stage needs to be at least 3% of total length
        mature_indexes = df.loc[mature_start:mature_end].index
        if mature_indexes[-1] - mature_indexes[0] > 0.03 * series_length:
            # Fill the period between mature_start and mature_end with 'mature'
            df.loc[mature_start:mature_end, 'periods'] = 'mature'

    # Check if all mature stages are preceeded by an intensification
    mature_periods = df[df['periods'] == 'mature'].index
    if len(mature_periods) > 0:
        blocks = np.split(mature_periods, np.where(np.diff(mature_periods) != dt)[0] + 1)
        for block in blocks:
            block_start, block_end = block[0], block[-1]
            if df.loc[block_start - dt, 'periods'] != 'intensification':
                df.loc[block_start:block_end, 'periods'] = np.nan

    return df


def find_intensification_period(df):
    # Find z peaks and valleys
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index
    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index

    length = df.index[-1] - df.index[0]
    dt = df.index[1] - df.index[0]

    # Find intensification periods between z peaks and valleys
    for z_peak in z_peaks:
        next_z_valley = z_valleys[z_valleys > z_peak].min()
        if next_z_valley is not pd.NaT:
            intensification_start = z_peak
            intensification_end = next_z_valley

            # Intensification needs to be at least 7.5% of the total series length
            if intensification_end-intensification_start > length*0.12:
                df.loc[intensification_start:intensification_end, 'periods'] = 'intensification'
    
    # Check if there are multiple blocks of consecutive intensification periods
    intensefication_periods = df[df['periods'] == 'intensification'].index
    blocks = np.split(intensefication_periods, np.where(np.diff(intensefication_periods) != dt)[0] + 1)

    for i in range(len(blocks) - 1):
        block_end = blocks[i][-1]
        next_block_start = blocks[i+1][0]
        gap = next_block_start - block_end

        # If the gap between blocks is smaller than 7.5%, fill with intensification
        if gap < length*0.075:
            df.loc[block_end:next_block_start, 'periods'] = 'intensification'

    return df

def find_decay_period(df):
    # Find z peaks and valleys
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index
    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index

    length = df.index[-1] - df.index[0]
    dt = df.index[1] - df.index[0]

    # Find decay periods between z valleys and peaks
    for z_valley in z_valleys:
        next_z_peak = z_peaks[z_peaks > z_valley].min()
        if next_z_peak is not pd.NaT:
            decay_start = z_valley
            decay_end = next_z_peak
        else:
            decay_start = z_valley
            decay_end = df.index[-1]  # Last index of the DataFrame

        # Decay needs to be at least 12% of the total series length
        if decay_end - decay_start > length*0.12:
            df.loc[decay_start:decay_end, 'periods'] = 'decay'

    # Check if there are multiple blocks of consecutive decay periods
    decay_periods = df[df['periods'] == 'decay'].index
    blocks = np.split(decay_periods, np.where(np.diff(decay_periods) != dt)[0] + 1)

    for i in range(len(blocks) - 1):
        block_end = blocks[i][-1]
        next_block_start = blocks[i+1][0]
        gap = next_block_start - block_end

        # If the gap between blocks is smaller than 7.5%, fill with decay
        if gap < length*0.075:
            df.loc[block_end:next_block_start, 'periods'] = 'decay'

    return df

def find_residual_period(df):
    unique_phases = [item for item in df['periods'].unique() if pd.notnull(item)]
    num_unique_phases = len(unique_phases)

    if num_unique_phases == 1:
        phase_to_fill = unique_phases[0]

        last_phase_index = df[df['periods'] == phase_to_fill].index[-1]
        dt = df.index[1] - df.index[0]
        df.loc[last_phase_index + dt:, 'periods'].fillna('residual', inplace=True)
    else:
        mature_periods = df[df['periods'] == 'mature'].index
        decay_periods = df[df['periods'] == 'decay'].index
        intensification_periods = df[df['periods'] == 'intensification'].index

        # Find residual periods where there is no decay stage after the mature stage
        for mature_period in mature_periods:
            if len(unique_phases) > 2:
                next_decay_period = decay_periods[decay_periods > mature_period].min()
                if next_decay_period is pd.NaT:
                    df.loc[mature_period:, 'periods'] = 'residual'
                    
        # Update mature periods
        mature_periods = df[df['periods'] == 'mature'].index

        # Fills with residual period intensification stage if there isn't a mature stage after it
        # but only if there's more than two periods
        if len(unique_phases) > 2:
            for intensification_period in intensification_periods:
                next_mature_period = mature_periods[mature_periods > intensification_period].min()
                if next_mature_period is pd.NaT:
                    df.loc[intensification_period:, 'periods'] = 'residual'

        # Fill NaNs after decay with residual if there is a decay, else, fill the NaNs after mature
        if 'decay' in unique_phases:
            last_decay_index = df[df['periods'] == 'decay'].index[-1]
        elif 'mature' in unique_phases:
            last_decay_index = df[df['periods'] == 'mature'].index[-1]
        dt = df.index[1] - df.index[0]
        df.loc[last_decay_index + dt:, 'periods'].fillna('residual', inplace=True)

    return df

def find_incipient_period(df):

    periods = df['periods']
    mature_periods = df[periods == 'mature'].index
    decay_periods = df[periods == 'decay'].index

    dt = df.index[1] - df.index[0]

    # if there's more than one period
    if len([item for item in df['periods'].unique() if (pd.notnull(item) and item != 'residual')]) > 2:
        # Find blocks of continuous indexes for 'decay' periods
        blocks = np.split(decay_periods, np.where(np.diff(decay_periods) != dt)[0] + 1)

        # Iterate over the blocks
        for block in blocks:
            if len(block) > 0:
                first_index = block[0]

                if first_index == df.index[0]:
                    df.loc[block, 'periods'] = 'incipient'

                else:
                    prev_index = first_index - dt
                    # Check if the previous index is incipient AND before mature stage
                    if (df.loc[prev_index, 'periods'] == 'incipient' or pd.isna(df.loc[prev_index, 'periods'])) and \
                    (len(mature_periods) > 0 and prev_index < mature_periods[-1]):
                        # Set the first period of the block to incipient
                        df.loc[block, 'periods'] = 'incipient'

    
    df['periods'].fillna('incipient', inplace=True)

    # If there's more than 2 unique phases other than residual and life cycle begins with
    # incipient fill first 6 hours with incipient.
    # If the life cycle begins with intensification, incipient phase will be from the
    # beginning of it, until 2/5 to the next dz_valley
    if len([item for item in df['periods'].unique() if (pd.notnull(item) and item != 'residual')]) > 2:
        phase_order = [item for item in df['periods'].unique() if pd.notnull(item)]
        if phase_order[0] in ['incipient', 'intensification'] or (phase_order[0] == 'incipient' and phase_order[1] == 'intensification'):
            start_time = df.iloc[0].name
            # Check if there's a dz valley before the next mature stage
            next_dz_valley = df[1:][df[1:]['dz_peaks_valleys'] == 'valley'].index.min()
            next_mature = df[df['periods'] == 'mature'].index.min()
            if next_dz_valley < next_mature:
                time_range = start_time + 2 * (next_dz_valley - start_time) / 5
                df.loc[start_time:time_range, 'periods'] = 'incipient'

    return df

import pandas as pd

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

def array_vorticity(
        zeta_df,
        frequency=24.0,
        savgol_polynomial=3,
        window_length_savgol='default',
        window_length_savgol_2nd='default',
        window_length_lanczo='default'):
    """
    Calculate derivatives of the vorticity and filter the resulting series

    Args:
    df: pandas DataFrame

    Returns:
    xarray DataArray
    """

    # Parameters
    if window_length_lanczo == 'default':
        window_length_lanczo = len(zeta_df) // 2 

    if window_length_savgol == 'default':
        window_length_savgol = len(zeta_df) | 1
        if pd.Timedelta(zeta_df.index[-1] - zeta_df.index[0]) > pd.Timedelta('8D'):
            window_length_savgol_2nd = window_length_savgol // 2 | 1
        else:
            window_length_savgol_2nd = window_length_savgol // 4 | 1

    if window_length_savgol_2nd < savgol_polynomial:
        window_length_savgol_2nd = 3

    cutoff_low = 1.0 / (7 * 24.0)
    cutoff_high = 1.0 / 48.0  # 24 hours
    
    # Convert dataframe to xarray
    da = zeta_df.to_xarray()

    # Apply Lanczos filter to vorticity 
    zeta_filtred = lanfil.lanczos_bandpass_filter(da['zeta'].copy(), window_length_lanczo, cutoff_low, cutoff_high)
    zeta_filtred_low_pass = lanfil.lanczos_filter(da.zeta.copy(), window_length_lanczo, frequency)
    zeta_filtred = xr.DataArray(zeta_filtred, coords={'time':zeta_df.index})
    da = da.assign(variables={'zeta_filt': zeta_filtred})

    num_samples = len(zeta_filtred)
    num_copy_samples = int(0.05 * num_samples)
    zeta_filtred.data[:num_copy_samples] = zeta_filtred_low_pass.data[:num_copy_samples]
    zeta_filtred.data[-num_copy_samples:] = zeta_filtred_low_pass.data[-num_copy_samples:]

    if pd.Timedelta(zeta_df.index[-1] - zeta_df.index[0]) > pd.Timedelta('8D'):
        window_length_savgol = window_length_savgol // 2 | 1
        
    # Smooth filtered vorticity with Savgol filter
    zeta_smoothed = xr.DataArray(
        savgol_filter(zeta_filtred, window_length_savgol//2|1, savgol_polynomial, mode="nearest"),
        coords={'time':zeta_df.index})

    zeta_smoothed2 = xr.DataArray(
            savgol_filter(zeta_smoothed, window_length_savgol_2nd, savgol_polynomial, mode="nearest"),
            coords={'time':zeta_df.index})
    
    da = da.assign(variables={'zeta_smoothed': zeta_smoothed})
    da = da.assign(variables={'zeta_smoothed2': zeta_smoothed2})

    # Calculate vorticity derivatives
    dz_dt = da.zeta.differentiate('time', datetime_unit='h')
    dz_dt2 = dz_dt.differentiate('time', datetime_unit='h')
    
    # Calculate the smoothed vorticity derivatives 
    dzfilt_dt = zeta_smoothed2.differentiate('time', datetime_unit='h')
    dzfilt_dt2 = dzfilt_dt.differentiate('time', datetime_unit='h')

    # Filter derivatives
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
    da = da.assign(variables={'dz_dt': dz_dt,
                              'dz_dt2': dz_dt2,
                              'dz_dt_filt': dz_dt_filt,
                              'dz_dt2_filt': dz_dt2_filt,
                              'dz_dt_smoothed2': dz_dt_smoothed2,
                              'dz_dt2_smoothed2': dz_dt2_smoothed2})

    return da 

def get_periods(vorticity,  plot=False, plot_steps=False, export_dict=False, output_directory='./'):

    z = vorticity.zeta_smoothed2
    dz = vorticity.dz_dt_smoothed2
    dz2 = vorticity.dz_dt2_smoothed2

    df = z.to_dataframe().rename(columns={'zeta_smoothed2':'z'})
    df['z_unfil'] = vorticity.zeta.to_dataframe()
    df['dz'] = dz.to_dataframe()
    df['dz2'] = dz2.to_dataframe()

    df['z_peaks_valleys'] = find_peaks_valleys(df['z'])
    df['dz_peaks_valleys'] = find_peaks_valleys(df['dz'])
    df['dz2_peaks_valleys'] = find_peaks_valleys(df['dz2'])

    df['periods'] = np.nan

    df = find_intensification_period(df)

    df = find_decay_period(df)

    df = find_mature_stage(df)

    df = find_residual_period(df)

    # 1) Fill consecutive intensification or decay periods that have NaNs between them
    # 2) Remove periods that are too short and fill with the previous period
    # (or the next one if there is no previous period)
    df = post_process_periods(df)

    df = find_incipient_period(df)

    # Pass the periods to a dictionary with each period's name as key
    #  and their corresponding start and end times as values.
    # Also, add extra 6 hours to the start and end of the periods as "confidence intervals"
    periods_dict = periods_to_dict(df)

    # Set the output file names
    periods_outfile_path = output_directory + 'periods'
    periods_didatic_outfile_path = output_directory + 'periods_didatic'

    # Create plots, if requested
    if plot:
        plot_all_periods(periods_dict, df, ax=None, vorticity=vorticity, periods_outfile_path=periods_outfile_path)
    if plot_steps:
        plot_didactic(df, vorticity, periods_didatic_outfile_path)
    # Export csv, if requested
    if export_dict:
        export_periods_to_csv(periods_dict, periods_outfile_path)

    return df

def determine_periods(track_file,  plot=False, plot_steps=False, export_dict=False, output_directory='./'):

    args = [plot, plot_steps, export_dict, output_directory]

    # Read the track file and extract the vorticity data
    track = pd.read_csv(track_file, parse_dates=[0], delimiter=';', index_col=[0])
    zeta_df = pd.DataFrame(track['min_zeta_850'].rename('zeta'))        
    vorticity = array_vorticity(zeta_df.copy())

    # Determine the periods
    return get_periods(vorticity.copy(), *args)

if __name__ == "__main__":
    determine_periods('../tests/test.csv',  plot=True, plot_steps=True, export_dict=False, output_directory='./')