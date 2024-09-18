import os
from glob import glob

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator

from cyclophaser import determine_periods
from cyclophaser.determine_periods import periods_to_dict, process_vorticity

def plot_all_periods(cyclone_id, phases_dict, ax, vorticity):
    colors_phases = {'incipient': '#65a1e6',
                      'intensification': '#f7b538',
                        'mature': '#d62828',
                          'decay': '#9aa981',
                          'residual': 'gray'}
    
    vorticity['zeta'] = vorticity['zeta'] * 1e5

    ax.plot(vorticity.time, vorticity.zeta, linewidth=10, color='gray', alpha=0.8, label=r'ζ')
    # ax.plot(vorticity.time, vorticity.vorticity_smoothed, linewidth=6,
    #          c='#1d3557', alpha=0.8, label=r'$ζ_{fs}$')
    # ax.plot(vorticity.time, vorticity.vorticity_smoothed2, linewidth=3,
    #          c='#e63946', alpha=0.6, label=r'$ζ_{fs^{2}}$')

    dt = pd.Timedelta(1, unit='h')

    # Shade the areas between the beginning and end of each period
    for phase, (start, end) in phases_dict.items():
        # Extract the base phase name (without suffix)
        base_phase = phase.split()[0]

        # Access the color based on the base phase name
        color = colors_phases[base_phase]

        # Fill between the start and end indices with the corresponding color
        ax.fill_between(vorticity.time, vorticity.zeta.values,
                         where=(vorticity.time >= start) & (vorticity.time <= end + dt),
                        alpha=0.5, color=color, label=base_phase)

    # Add scientific notation to y-axis
    ax.ticklabel_format(axis='y', style='sci', scilimits=(-3, 3))

    # Format the x-axis
    date_format = mdates.DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_format)
    ax.set_xlim(vorticity.time.min(), vorticity.time.max())
    ax.set_ylim(vorticity.zeta.min() - 0.25e-5, 0)

    # Add this line to set x-tick locator
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6))  

    # Add y-axis label
    ax.set_ylabel('FIltered Central Relative Vorticity', fontsize=16)

    # Rotate the x-tick labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=12)
    plt.setp(ax.get_yticklabels(), fontsize=12)

    # Add a legend
    ax.legend(loc='upper right', bbox_to_anchor=(1.4, 0.7), fontsize=14)


results_dir = '/Users/danilocoutodesouza/Documents/Programs_and_scripts/SWSA-cyclones_energetic-analysis/raw_data/SAt'

system = 'SAt_20101172'

fig = plt.figure(figsize=(10, 7))

print(f"Processing {system}")
cyclone_id = system.split('_')[1]
RG = system.split('_')[0]
year = str(cyclone_id)[0:4]
cyclone_id = int(cyclone_id)
track_file = glob(f'{results_dir}/*201012.csv')[0]
tracks = pd.read_csv(track_file)

tracks.columns = ['track_id', 'date', 'lon vor', 'lat vor', 'vor42']

track = tracks[tracks['track_id']==cyclone_id][['date','vor42']]

# Create temporary files for cyclophaser function
track = track.rename(columns={"date":"time"})
track['vor42'] = - track['vor42'] * 1e-5
tmp_file = (f"tmp_{RG}-{cyclone_id}.csv")
track.to_csv(tmp_file, index=False, sep=';')

zeta = list(track['vor42'].values)
time = list(pd.to_datetime(track['time'].values))

use_filter=False
use_smoothing=len(zeta) // 8 | 1
use_smoothing_twice=False

df_periods = determine_periods(zeta, x=time, use_filter=use_filter, use_smoothing=use_smoothing, use_smoothing_twice=use_smoothing_twice)
periods_dict = periods_to_dict(df_periods)

ax = fig.add_subplot(111)

zeta_df = pd.DataFrame(track['vor42'].rename('zeta'))
zeta_df.index = pd.to_datetime(track['time'])

vorticity = process_vorticity(zeta_df.copy(), use_filter=use_filter, use_smoothing=use_smoothing, use_smoothing_twice=use_smoothing_twice)

plot_all_periods(cyclone_id, periods_dict, ax, vorticity)

os.remove(tmp_file)

# Remove scientific notation from the y-axis tick labels and add it manually
for ax in fig.get_axes():
    ax.ticklabel_format(axis='y', style='plain')  # Use plain style for y-axis labels
    ax.yaxis.offsetText.set_fontsize(12)  # Adjust font size if needed
    ax.yaxis.labelpad = 20  # Increase the label pad to provide more space

    # Add custom text for scientific notation
    ax.annotate('1e-5', xy=(0.2, 1), xytext=(-50, 10), 
                xycoords='axes fraction', textcoords='offset points', 
                fontsize=12, ha='center')
    
plt.tight_layout()
fname = f'./paper/life-cycle.png'
plt.savefig(fname, dpi=500)
print(f"{fname} created.")