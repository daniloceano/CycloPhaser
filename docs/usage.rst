.. _usage:

Usage Guide
===========

.. contents::
   :local:
   :depth: 2

Introduction
------------

The example provided in this guide demonstrates how to use the CycloPhaser package to analyze the life cycle phases of an extratropical cyclone. The data used in this example corresponds to the track file of a specific extratropical cyclone whose genesis occurred near the eastern coast of Argentina. This track file was produced using the LorenzCycleToolkit (https://github.com/daniloceano/LorenzCycleToolkit). The file contains the cyclone's position, as well as information regarding the minimum relative vorticity, geopotential height, and maximum wind speeds within a defined domain centered on the cyclone. CycloPhaser helps in dissecting this cyclone into distinct life cycle phases using the minimum vorticity time series.

Arguments and Parameters for determine_periods
----------------------------------------------

- **series**: (list, np.ndarray, pd.Series, xr.DataArray) A time series of vorticity values to be analyzed. **Note:** The algorithm is optimized for vorticity data, though it can potentially handle other meteorological fields like sea level pressure (SLP) or geopotential height. Use caution with these as they are untested for precise cyclone phase detection.

- **x**: (list, pd.DatetimeIndex, optional) Temporal labels corresponding to the `series`. This list must match the length of the `series`. **Default**: None.

- **hemisphere**: (str, optional) Hemisphere of the data. Set to `"southern"` (default) to apply Southern Hemisphere conventions, or `"northern"` to automatically multiply input values by -1 for Northern Hemisphere compatibility. **Note**: This setting is especially relevant for vorticity data, where conventions vary by hemisphere. When using **wind speed data**, set `"northern"` for detection maxima in both hemispheres. For **sea level pressure (SLP) data**, keep `"southern"` as the default.

- **plot**: (str or bool, optional) Path for saving generated plots. Set to `False` to disable plotting. **Default**: False.

- **plot_steps**: (str or bool, optional) Path for saving detailed step-by-step plots to illustrate each processing stage. Set to `False` to disable step-wise plotting. **Default**: False.

- **export_dict**: (str or bool, optional) Path for exporting detected cyclone periods as a CSV file. Set to `False` to skip exporting. **Default**: False.

- **use_filter**: (str or int, optional) Apply a Lanczos filter to the `series`. Specify a window length as an integer to customize or use `'auto'` for adaptive length based on dataset size (half of series length). **Units**: Time steps. **Default**: 'auto'.  
  **Recommendation**: If using relative vorticity series, turn off `use_filter` if the tracking procedure already applies spatial filtering to avoid over-filtering and signal loss. For hourly ERA5 data, `'auto'` is typically effective, though this may need adjustment for different temporal resolutions and spatial resolutions. Use smoothing also if noise levels are too high.

- **replace_endpoints_with_lowpass**: (int, optional) Applies a lowpass filter to smooth the series endpoints, which helps stabilize edge effects during filtering. Specify the window length. **Units**: Time steps. **Default**: 24.  
  **Recommendation**: For hourly relative vorticity data, a 24-hour (24 time steps) setting is effective. Adjust this based on the temporal and spatial resolution of the original data, especially if using data with higher spatial resolution.

- **use_smoothing**: (str, int, optional) Apply Savgol smoothing to filtered vorticity data. Set to `'auto'` to automatically choose an appropriate window length, or provide an integer window length directly. **Note**: The specified window length must be an odd number and greater than or equal to `savgol_polynomial`. Set `use_smoothing=False` to deactivate. **Units**: Time steps. **Default**: 'auto'.  
  **Recommendation**: This setting is sensitive to the length of the time series. The `'auto'` setting uses a window length approximately 1/4 of the series length for series >8 days; otherwise, it uses about 1/2. For lower-noise data, this value can be decreased, and for higher-noise data, increase it accordingly.

- **use_smoothing_twice**: (str, int, optional) Apply a second pass of Savgol smoothing for further noise reduction. This uses similar parameters to `use_smoothing`. **Default**: 'auto'.  
  **Recommendation**: This should be a gentler smoothing than the initial `use_smoothing`. The `'auto'` setting applies half the window length used in the first pass.

- **savgol_polynomial**: (int, optional) Polynomial order for Savgol smoothing, which must be less than or equal to the window length specified in `use_smoothing` and `use_smoothing_twice`. **Default**: 3.  
  **Recommendation**: Higher values retain sharper peaks and more detailed features but can increase noise; lower values provide a smoother output that may oversmooth finer details. For noisier data, a lower polynomial value is preferable, and for cleaner data, a higher value helps preserve more details.

- **cutoff_low**: (float, optional) Low-frequency cutoff for the Lanczos filter, designed for data with hourly resolution. **Units**: Time steps. **Default**: 168.  
  **Recommendation**: Set this to the equivalent of 7 days in time steps to filter out planetary wave influences on vorticity.

- **cutoff_high**: (float, optional) High-frequency cutoff for the Lanczos filter, suitable for reducing high-frequency noise in hourly data. **Units**: Time steps. **Default**: 48.  
  **Recommendation**: Set this to the equivalent of 2 days in time steps to effectively filter out mesoscale influences on vorticity.

**Note on Default Values and Data Frequency**: The above default settings assume hourly data frequency. For datasets with different time resolutions (e.g., daily or sub-hourly), adjustments are recommended for parameters like `cutoff_low`, `cutoff_high`, `replace_endpoints_with_lowpass`, and `use_smoothing`. For example, if using daily data, reduce cutoff values by a factor of 24 to adapt accordingly.

Example Usage
-------------

Below is an example of using the CycloPhaser package with default options. The function will generate plots and a CSV file that contains detected cyclone life cycle phases.

.. code-block:: python

   from cyclophaser import determine_periods, example_file
   import pandas as pd

   # Load test data
   track = pd.read_csv(example_file, parse_dates=[0], delimiter=';', index_col=[0])
   series = track['min_max_zeta_850']

   # Example options for using CycloPhaser with default settings
   result = determine_periods(series, plot="test_default", plot_steps="test_steps_default", export_dict="test_default")

Output Examples
---------------

1. **Vorticity Data with Detected Periods**:

.. figure:: _images/test_default.png
   :alt: Vorticity Data with Detected Periods

   This plot shows the vorticity data with key cyclone life cycle phases, such as intensification, decay, mature, and residual stages.

2. **Step-by-Step Didactic Plot**:

.. figure:: _images/test_steps_default.png
   :alt: Step-by-Step Didactic Plot

   The step-by-step plot provides a detailed breakdown of how the vorticity data is processed and how each cyclone phase is detected. This plot illustrates the filtering, smoothing, and phase detection processes.

3. **CSV Output**:

   The results of the detected cyclone life cycle phases are also exported as a CSV file, allowing for further analysis. Below is a preview of the CSV content:

.. code-block::

   phase,start,end
   intensification,2008-08-17,2008-08-19
   mature,2008-08-19,2008-08-20
   decay,2008-08-20,2008-08-22
   residual,2008-08-22,2008-08-24

This example showcases how users can utilize the CycloPhaser package to automatically detect and visualize extratropical cyclone life cycle phases from vorticity data.

Customizing Filtering
---------------------

In the previous example, the phase positioning might not match expectations for all datasets. To improve results, you can easily customize the filtering parameters:

.. code-block:: python

    from cyclophaser import determine_periods

    # Example options for custom filtering
    process_vorticity_args = {
        'cutoff_low': 100,
        'cutoff_high': 20,
        'use_filter': True,
        'use_smoothing': 10,
        'use_smoothing_twice': False,
    }

    # Example usage with custom parameters
    result = determine_periods(series, x=x, plot='test_custom', **process_vorticity_args)

.. figure:: _images/test_custom.png
    :alt: Vorticity Data with Detected Periods and Custom Parameters

    Cyclone phases positioning corrected using default parameters.


Important Notes
---------------

- **Hemisphere Support**: The tool is primarily set up for vorticity data from the southern hemisphere (negative vorticity). For northern hemisphere data, such as wind data or when working with vorticity from the northern hemisphere, set the `hemisphere` parameter to `'northern'` to automatically invert the values.
  
- **Oscillation Warning**: If excessive oscillations are detected at the start or end of the series, a warning will be issued, suggesting that the user adjusts parameters like `use_filter`, `replace_endpoints_with_lowpass`, or `use_smoothing` to reduce these effects.

- **Customization**: Most parameters, including filtering options and threshold values, can be customized to fit your dataset.