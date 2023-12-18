
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

Note: CycloPhaser is compatible with Python 3.x. Please ensure you have the correct version installed.


# Arguments and Parameters for determine_periods:

- series (list): A list of vorticity values.
- x (list, optional): Temporal range or other labels for the series. Default is None.
- plot (str, optional): Whether to generate and save plots. Default is False. Input string is the path to save the plots.
- plot_steps (str, optional): Whether to generate step-by-step didactic plots. Default is False. Input string is the path to save the plots.
- export_dict (str, optional): Whether to export periods as a CSV dictionary. Default is False. Input string is the path to save the CSV file.
- output_directory (str, optional): Directory for saving output files. Default is './'.
- array_vorticity_args (dict, optional): Custom arguments for the array_vorticity function. Refer to documentation for details.


# Customizing Filtering

The package also provides the array_vorticity function in the determine_periods.py module that allows you to customize filtering parameters:

```
from cyclophaser import determine_periods

# Define custom arguments
process_vorticity_args = {
    'cutoff_low': 168,
    'cutoff_high': 24,
    'use_filter': True,
    'replace_endpoints_with_lowpass': 24,
    'use_smoothing': True,
    'use_smoothing_twice': False,
    'savgol_polynomial': 3
}

# Example usage
series = [/* your vorticity data */]
x = [/* your time data */]
vorticity_data = determine_periods(series, x=x, **process_vorticity_args)
```

# Example: Processing vorticity data from TRACK algorithm Hodges (1994, 1995)

```
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
```

# Usage

The main script for determining meteorological periods is determine_periods.py. You can use it by passing your vorticity data as a CSV file and customizing the parameters as needed.

```
from cyclophaser import determine_periods

# Example options for ERA5 data
options_era5 = {
    "plot": 'test',
    "plot_steps": 'test_steps',
    "export_dict": 'test',
    "process_vorticity_args": {
        "use_filter": 'auto',
        "replace_endpoints_with_lowpass": 24,
        "use_smoothing": 'auto',
        "use_smoothing_twice": 'auto',
        "savgol_polynomial": 3,
        "cutoff_low": 168,
        "cutoff_high": 48
    }
}

series_era5 = [/* your ERA5 data */]
x_era5 = [/* your time data */]
result_era5 = determine_periods(series_era5, x=x_era5, **options_era5)
```

# Note

- The tool currently supports data from the southern hemisphere (negative vorticity) only.
- Future updates may include support for northern hemisphere data.

# Documentation

For detailed documentation, including function parameters and module descriptions, refer to the in-code comments and docstrings.

# Support and Contact

For support, feature requests, or any queries, please open an issue on the GitHub repository.

# License

This project is licensed under the MIT License.

