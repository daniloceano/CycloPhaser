CycloPhaser API Reference
=========================

The CycloPhaser package provides automatic detection of extratropical cyclone life cycles through vorticity data time series analysis. This API is primarily designed for researchers in atmospheric sciences.

determine_periods
-----------------

.. autofunction:: cyclophaser.determine_periods

The ``determine_periods`` function is the core of CycloPhaser, allowing users to analyze time series data of vorticity values and detect various stages of cyclone life cycles.

**Parameters**:

- **series**: (list) A list of vorticity values to be analyzed. **Note:** The series does not need to be in any specific units. The algorithm is designed to work with vorticity data, but other meteorological fields like sea level pressure (SLP) or geopotential height. However, these have not been fully tested yet, so care is advised when interpreting results from fields other than vorticity.
- **x**: (list, optional) Temporal range or labels corresponding to the series. This list must be the same length as the vorticity `series`. Default is None.
- **plot**: (str or bool, optional) Path for saving generated plots. Set to `False` to disable plotting. Default is False.
- **plot_steps**: (str or bool, optional) Path for saving step-by-step didactic plots. Set to `False` to disable step-wise plotting. Default is False.
- **export_dict**: (str or bool, optional) Path for exporting the detected periods as a CSV file. Set to `False` to skip exporting. Default is False.
- **use_filter**: (str or bool, optional) Whether to apply a Lanczos filter to the vorticity data. Specify a window length as an integer, or set to 'auto' to automatically adapt based on the data. Default is 'auto'.
- **replace_endpoints_with_lowpass**: (int, optional) Replace the endpoints of the series with a lowpass filter. Specify the window length. Default is 24.
- **use_smoothing**: (str or bool, optional) Apply Savgol smoothing to the vorticity data. Specify the window length, or use 'auto' to adapt based on data length. Default is 'auto'.
- **use_smoothing_twice**: (str or bool, optional) Apply Savgol smoothing twice for additional noise reduction. Same options as `use_smoothing`. Default is 'auto'.
- **savgol_polynomial**: (int, optional) Polynomial order for Savgol smoothing. Default is 3.
- **cutoff_low**: (float, optional) Low-frequency cutoff for the Lanczos filter. Default is 168.
- **cutoff_high**: (float, optional) High-frequency cutoff for the Lanczos filter. Default is 48.
- **threshold_intensification_length**: (float, optional) Minimum length for the intensification period. Default is 0.075 (7.5% of total series length).
- **threshold_intensification_gap**: (float, optional) Maximum gap allowed between intensification periods. Default is 0.075.
- **threshold_mature_distance**: (float, optional) Distance threshold for detecting the mature stage. Default is 0.125.
- **threshold_mature_length**: (float, optional) Minimum length for the mature stage. Default is 0.03 (3% of total series length).
- **threshold_decay_length**: (float, optional) Minimum length for the decay period. Default is 0.075.
- **threshold_decay_gap**: (float, optional) Maximum gap allowed between decay periods. Default is 0.075.
- **threshold_incipient_length**: (float, optional) Minimum length for the incipient stage. Default is 0.4 (40% of the total time step to the next transition).

**Returns**:

- A pandas DataFrame containing the detected cyclone life cycle periods. The DataFrame includes fields for smoothed vorticity values, their first and second derivatives, and labeled stages such as 'intensification', 'mature', 'decay', and 'incipient'.

**Example Usage**:

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
        "use_smoothing_twice": 'auto',
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
