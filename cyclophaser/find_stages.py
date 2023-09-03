import numpy as np
import pandas as pd

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

    # Check if all mature stages are preceded by an intensification and followed by decay
    mature_periods = df[df['periods'] == 'mature'].index
    if len(mature_periods) > 0:
        blocks = np.split(mature_periods, np.where(np.diff(mature_periods) != dt)[0] + 1)
        for block in blocks:
            block_start, block_end = block[0], block[-1]
            if df.loc[block_start - dt, 'periods'] != 'intensification' or \
               df.loc[block_end + dt, 'periods'] != 'decay':
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

    # If there's only one phase, fills with 'residual' the NaNs after the last block of it.
    if num_unique_phases == 1:
        phase_to_fill = unique_phases[0]

        # Find consecutive blocks of the same phase
        phase_blocks = np.split(df[df['periods'] == phase_to_fill].index,
                                np.where(np.diff(df['periods'] == phase_to_fill) != 0)[0] + 1)

        # Find the last block of the same phase
        last_phase_block = phase_blocks[-1]

        # Find the index right after the last block
        last_phase_block_end = last_phase_block[-1] if len(last_phase_block) > 0 else df.index[0]
        dt = df.index[1] - df.index[0]

        # Fill NaNs after the last block with 'residual'
        df.loc[last_phase_block_end + dt:, 'periods'].fillna('residual', inplace=True)

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

if __name__ == '__main__':

    import determine_periods as det

    track_file = "../tests/test.csv"
    track = pd.read_csv(track_file, parse_dates=[0], delimiter=';', index_col=[0])

    # Testing
    options = {
        "vorticity_column": 'min_zeta_850',
        "plot": False,
        "plot_steps": False,
        "export_dict": False,
        "process_vorticity_args": {
            "use_filter": False,
            "use_smoothing_twice": len(track)// 4 | 1}
    }

    args = [options["plot"], options["plot_steps"], options["export_dict"]]
    
    zeta_df = pd.DataFrame(track[options["vorticity_column"]].rename('zeta'))

    # Modify the array_vorticity_args if provided, otherwise use defaults
    vorticity = det.array_vorticity(zeta_df.copy(), **options["process_vorticity_args"])

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

    df = find_intensification_period(df)

    df = find_decay_period(df)

    df = find_mature_stage(df)

    df = find_residual_period(df)

    # 1) Fill consecutive intensification or decay periods that have NaNs between them
    # 2) Remove periods that are too short and fill with the previous period
    # (or the next one if there is no previous period)
    df = det.post_process_periods(df)

    df = find_incipient_period(df)

