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
- **process_vorticity_args**: Custom arguments for processing vorticity data. Optional.

Example Usage:

.. code-block:: python

    from cyclophaser import determine_periods

    track_file = 'tests/test.csv'
    track = pd.read_csv(track_file, parse_dates=[0], delimiter=';', index_col=[0])
    series = track['min_zeta_850'].tolist()
    x = track.index.tolist()

    options = {
        "plot": 'path/to/save/plots',
        "plot_steps": 'path/to/save/plot_steps',
        "export_dict": 'path/to/export/csv',
        "process_vorticity_args": {
            "use_filter": 'auto',
            "replace_endpoints_with_lowpass": 24,
            "use_smoothing": 'auto',
            "savgol_polynomial": 3,
            "cutoff_low": 168,
            "cutoff_high": 48
        }
    }

    result = determine_periods(series, x=x, **options)

This API guide provides an overview of the available functionalities in CycloPhaser. For detailed information on each function and its parameters, refer to the in-code documentation.
