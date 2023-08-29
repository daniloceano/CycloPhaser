from cyclophaser.determine_periods import determine_periods

track_file = 'tests/test.csv'
output_directory = './'

# Specify options for the determine_periods function
options = {
    "plot": True,
    "plot_steps": True,
    "export_dict": False,
    "output_directory": output_directory,
    "array_vorticity_args": {
        "use_filter": 'auto',
        "replace_endpoints_with_lowpass": 0.1,
        "use_smoothing": 'auto',
        "use_smoothing_twice": 'auto',
        "savgol_polynomial": 3,
        "cutoff_low": 200,
        "cutoff_high": 48
    }
}

# Call the determine_periods function with options
determine_periods(track_file, **options)
