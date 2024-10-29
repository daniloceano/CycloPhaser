CycloPhaser API Reference
=========================

The CycloPhaser package provides automatic detection of extratropical cyclone life cycles through vorticity data time series analysis. This API is primarily designed for researchers in atmospheric sciences.

determine_periods
-----------------

.. autofunction:: cyclophaser.determine_periods

The ``determine_periods`` function is the core of CycloPhaser, allowing users to analyze time series data of vorticity values and detect various stages of cyclone life cycles.

**Parameters**:

- **series**: (list or np.ndarray, pd.Series, or xr.DataArray) The primary data to be analyzed, representing vorticity or other cyclone-related time series. **Note:** The series does not need to be in any specific units, but it should typically represent vorticity or other cyclone-related metrics. Use with caution for data types beyond vorticity, as these have not been fully tested yet.
- **x**: (list or pd.DatetimeIndex, optional) Temporal labels for the `series`, expected to be in the same length as `series`. If `series` is provided as a pandas Series or xarray DataArray, `x` is inferred from the index. When using a list or numpy array for `series`, `x` must be provided explicitly.
- **plot**: (str or bool, optional) Path for saving generated plots. Set to `False` to disable plotting. Default is False.
- **plot_steps**: (str or bool, optional) Path for saving step-by-step didactic plots. Set to `False` to disable step-wise plotting. Default is False.
- **export_dict**: (str or bool, optional) Path for exporting the detected periods as a CSV file. Set to `False` to skip exporting. Default is False.
- **hemisphere**: (str, optional) Hemisphere of the data. Set to `"southern"` (default) to apply Southern Hemisphere conventions, or `"northern"` to automatically multiply input values by -1 for Northern Hemisphere compatibility. **Note**: This setting is especially relevant for vorticity data, where conventions vary by hemisphere. When using **wind speed data**, set `"northern"` for detection maxima in both hemispheres. For **sea level pressure (SLP) data**, keep `"southern"` as the default.
- **use_filter**: (str or int, optional) Apply a Lanczos filter to the vorticity data. Set to `'auto'` for a default window length or specify an integer. **Units:** Time steps. Default is 'auto'.
- **replace_endpoints_with_lowpass**: (int, optional) Replace the endpoints of the series with a lowpass filter. **Units:** Time steps. Default is 24.
- **use_smoothing**: (str or int, optional) Apply Savgol smoothing to the vorticity data. Set to `'auto'` for an automatically chosen window length or provide an integer value for a custom window length. **Units:** Time steps.
- **use_smoothing_twice**: (str or int, optional) Apply Savgol smoothing twice for additional noise reduction. Same requirements as `use_smoothing`. Default is 'auto'.
- **savgol_polynomial**: (int, optional) Polynomial order for Savgol smoothing. **Note:** This must be less than or equal to the window length specified in `use_smoothing`. Default is 3.
- **cutoff_low** and **cutoff_high**: (float, optional) Low and high-frequency cutoffs for the Lanczos filter, respectively. **Units:** Time steps. Default values are 168 and 48, respectively.
- **threshold_intensification_length**: (float, optional) Minimum required length for intensification periods as a fraction of the series length. Default is 0.075.
- **threshold_intensification_gap**: (float, optional) Maximum gap allowed in intensification periods. Default is 0.075.
- **threshold_mature_distance**: (float, optional) Distance threshold for detecting the mature stage. Default is 0.125.
- **threshold_mature_length**: (float, optional) Minimum required length for mature periods as a fraction of the series length. Default is 0.03.
- **threshold_decay_length**: (float, optional) Minimum required length for decay periods as a fraction of the series length. Default is 0.075.
- **threshold_decay_gap**: (float, optional) Maximum gap allowed in decay periods. Default is 0.075.
- **threshold_incipient_length**: (float, optional) Minimum required length for incipient periods as a fraction of the series length. Default is 0.4.

**Returns**:

- A pandas DataFrame containing the detected cyclone life cycle periods. The DataFrame includes fields for smoothed vorticity values, their first and second derivatives, and labeled stages such as 'intensification', 'mature', 'decay', and 'incipient'.

**Example Usage**:

.. code-block:: python

    from cyclophaser import determine_periods
    import pandas as pd

    track_file = 'tests/test.csv'
    track = pd.read_csv(track_file, parse_dates=[0], delimiter=';', index_col=[0])
    series = track['min_zeta_850']

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
