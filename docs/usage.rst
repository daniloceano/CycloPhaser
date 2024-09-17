Arguments and Parameters for determine_periods
----------------------------------------------

- **series** (list): A list of vorticity values.
- **x** (list, optional): Temporal range or other labels for the series. Default is None.
- **plot** (str, optional): Path to save plots. If provided, plots will be generated and saved. Default is False.
- **plot_steps** (str, optional): Path to save step-by-step didactic plots. If provided, detailed stepwise plots will be generated. Default is False.
- **export_dict** (str, optional): Path to save periods as a CSV dictionary. If provided, the periods will be exported to CSV. Default is False.
- **output_directory** (str, optional): Directory for saving output files (e.g., plots, CSV). Default is './'.
- **use_filter** (bool, optional): Whether to apply the Lanczos filter to vorticity. Default is 'auto'.
- **replace_endpoints_with_lowpass** (int, optional): Window length for replacing endpoints with a lowpass filter. Default is 24.
- **use_smoothing** (bool, optional): Whether to apply Savitzky-Golay smoothing to the filtered vorticity. Default is 'auto'.
- **use_smoothing_twice** (bool, optional): Whether to apply Savitzky-Golay smoothing twice. Default is 'auto'.
- **savgol_polynomial** (int, optional): Polynomial order for Savitzky-Golay smoothing. Default is 3.
- **cutoff_low** (float, optional): Low-frequency cutoff for Lanczos filter. Default is 168.
- **cutoff_high** (float, optional): High-frequency cutoff for Lanczos filter. Default is 48.

Customizing Filtering
---------------------

The package provides a function to customize the filtering parameters through ``determine_periods``:

.. code-block:: python

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
    result = determine_periods(series, x=x, **process_vorticity_args)

Example: Processing Vorticity Data from the TRACK Algorithm (Hodges, 1994, 1995)
-------------------------------------------------------------------------------

The tool can process vorticity data obtained from TRACK algorithms. Here’s how you can use it:

.. code-block:: python

    options_track = {
        "vorticity_column": 'vor42',
        "plot": 'output_plot.png',
        "plot_steps": 'output_steps.png',
        "export_dict": 'output_periods.csv',
        "use_filter": False,
        "use_smoothing_twice": len(track) // 4 | 1
    }

    result_track = determine_periods(series, x=x, **options_track)

Example: Processing Vorticity Data from ERA5
--------------------------------------------

Here is how you can process ERA5 data using the ``determine_periods`` function:

.. code-block:: python

    from cyclophaser import determine_periods

    # Example options for ERA5 data
    options_era5 = {
        "plot": 'output_era5_plot.png',
        "plot_steps": 'output_era5_steps.png',
        "export_dict": 'output_era5_periods.csv',
        "use_filter": 'auto',
        "replace_endpoints_with_lowpass": 24,
        "use_smoothing": 'auto',
        "use_smoothing_twice": 'auto',
        "savgol_polynomial": 3,
        "cutoff_low": 168,
        "cutoff_high": 48
    }

    series_era5 = [/* your ERA5 data */]
    x_era5 = [/* your time data */]
    result_era5 = determine_periods(series_era5, x=x_era5, **options_era5)

Important Notes
---------------

- **Southern Hemisphere Support**: The tool currently supports vorticity data from the southern hemisphere (negative vorticity). Future versions will include northern hemisphere support.
- **Customization**: Most parameters, including filtering options and threshold values, can be customized to fit your dataset.
