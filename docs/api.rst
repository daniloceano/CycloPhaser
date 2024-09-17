CycloPhaser API Reference
=========================

The CycloPhaser package provides an automatic detection of extratropical cyclone life cycles through vorticity data time series analysis. This API is designed primarily for atmospheric science researchers.

determine_periods
-----------------

.. autofunction:: cyclophaser.determine_periods

The ``determine_periods`` function is the core of CycloPhaser, allowing users to analyze time series data of vorticity values and detect various stages of cyclone life cycles.

Parameters:

- **series**: List of vorticity values.
- **x**: Temporal range or labels for the series. Optional.
- **plot**: Path for saving plots. Optional.
- **plot_steps**: Path for saving step-by-step didactic plots. Optional.
- **export_dict**: Path for exporting the periods as a CSV file. Optional.
- **use_filter**: Whether to apply a filter to the vorticity data. Optional.
- **replace_endpoints_with_lowpass**: Replace the endpoints with a lowpass filter. Optional.
- **use_smoothing**: Whether to apply smoothing to the vorticity data. Optional.
- **use_smoothing_twice**: Whether to apply smoothing twice to the vorticity data. Optional.
- **savgol_polynomial**: Polynomial order for Savgol smoothing. Optional.
- **cutoff_low**: Low-frequency cutoff for Lanczos filter. Optional.
- **cutoff_high**: High-frequency cutoff for Lanczos filter. Optional.
- **threshold_intensification_length**: Minimum length for the intensification period. Optional.
- **threshold_intensification_gap**: Maximum gap allowed between intensification periods. Optional.
- **threshold_mature_distance**: Distance threshold for mature stage detection. Optional.
- **threshold_mature_length**: Minimum length for the mature stage. Optional.
- **threshold_decay_length**: Minimum length for the decay stage. Optional.
- **threshold_decay_gap**: Maximum gap allowed between decay periods. Optional.
- **threshold_incipient_length**: Minimum length for the incipient stage. Optional.

Returns:
    - A pandas DataFrame containing the detected periods and associated information.

Example Usage:

.. code-block:: python

    from cyclophaser import determine_periods
    import pandas as pd

    track_file = 'tests/test.csv'
    track = pd.read_csv(track_file, parse_dates=[0], delimiter=';', index_col=[0])
    series = track['min_zeta_850'].tolist()
    x = track.index.tolist()

    options = {
        "plot": 'path/to/save/plots',
        "plot_steps": 'path/to/save/plot_steps',
        "export_dict": 'path/to/export/csv',
        "use_filter": 'auto',
        "replace_endpoints_with_lowpass": 24,
        "use_smoothing": 'auto',
        "savgol_polynomial": 3,
        "cutoff_low": 168,
        "cutoff_high": 48,
        "threshold_intensification_length": 0.075,
        "threshold_intensification_gap": 0.075,
        "threshold_mature_distance": 0.125,
        "threshold_mature_length": 0.03,
        "threshold_decay_length": 0.075,
        "threshold_decay_gap": 0.075,
        "threshold_incipient_length": 0.4
    }

    result = determine_periods(series, x=x, **options)

This API guide provides an overview of the available functionalities in CycloPhaser. For detailed information on each function and its parameters, refer to the in-code documentation.