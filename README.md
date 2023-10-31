
![Glacial Indifference](https://github.com/daniloceano/CycloPhaser/assets/56005607/35597b83-26fb-41ba-838d-f414ae540317)

The CycloPhaser calculates extratropical cyclone life cycle phases from vorticity data using Python.

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/daniloceano/CycloPhaser
   cd CycloPhaser

2. Install dependencies using pip

   ```
   pip install -r requirements.txt


# Arguments and Parameters for determine_periods:

- track_file (str): Path to the CSV file containing track data.
- vorticity_column (str, optional): Column name for the vorticity data in the CSV file. Default is 'min_zeta_850'.
- plot (bool, optional): Whether to generate and save plots. Default is False.
- plot_steps (bool, optional): Whether to generate step-by-step didactic plots. Default is False.
- export_dict (bool, optional): Whether to export periods as a CSV dictionary. Default is False.
- output_directory (str, optional): Directory for saving output files. Default is './'.
- array_vorticity_args (dict, optional): Custom arguments for the array_vorticity function. Refer to documentation for details.


# Customizing Filtering

The package also provides the array_vorticity function in the determine_periods.py module that allows you to customize filtering parameters:

```
from cyclophaser import determine_periods

# Load your zeta_df DataFrame
track_file = 'tests/test.csv'  # Load your data here

# Define custom arguments
array_vorticity_args = {
    'cutoff_low': 168,
    'cutoff_high': 24,
    'use_filter': True,
    'replace_endpoints_with_lowpass': 24,
    'use_smoothing': True,
    'use_smoothing_twice': False,
    'savgol_polynomial': 3
}

# Apply vorticity calculations and filtering
vorticity_data = determine_periods(track_file, **array_vorticity_args)
```

# Usage

The main script for determining meteorological periods is determine_periods.py. You can use it by passing your vorticity data as a CSV file and customizing the parameters as needed.

```
from cyclophaser import determine_periods

# Example: Processing vorticity data from ERA5
options_era5 = {
    "vorticity_column": 'min_zeta_850',
    "plot": 'test',
    "plot_steps": 'test_steps',
    "export_dict": 'test',
    "array_vorticity_args": {
        "use_filter": 'auto',
        "replace_endpoints_with_lowpass": 24,
        "use_smoothing": 'auto',
        "use_smoothing_twice": 'auto',
        "savgol_polynomial": 3,
        "cutoff_low": 168,
        "cutoff_high": 48
    }
}

# Example: Processing vorticity data from TRACK algorithm Hodges (1994, 1995)
options_track = {
    "vorticity_column": 'vor42',
    "plot": periods_outfile,
    "plot_steps": periods_didatic_outfile,
    "export_dict": periods_csv_outfile,
    "array_vorticity_args": {
        "use_filter": False,
        "use_smoothing_twice": len(track) // 4 | 1
    }
}

# Determine meteorological periods using the above options
result_era5 = determine_periods(track_file_era5, **options_era5)
result_track = determine_periods(track_file_track, **options_track)
```

Important:

- The input file "track_data.csv" must contain dates in the first column, named "time"
- The vorticity column name can be passed in the "vorticity_column" argument of the "determine_perdios" function (default is "min_zeta_850")
- For the current version, only data from the southern hemisphere can be passed (negative vorticity)

# Documentation

For detailed documentation of the package's functions, modules, and parameters, refer to the in-code comments and docstrings.

# License

This project is licensed under the MIT License.

