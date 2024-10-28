# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.9.0] - 2024-10-28

### New Features
- **Hemisphere Support Argument**: Added `hemisphere` argument in `determine_periods` function. This enables users to specify `southern` or `northern` hemisphere data, with automatic sign inversion for the northern hemisphere. Improved compatibility with wind data by setting this option to "northern".

### Documentation Improvements
- **Detailed Argument Descriptions**: Updated the `determine_periods` and `process_vorticity` functions' documentation to include specific units, guidelines, and recommendations for each parameter, enhancing usability.
- **Parameter Recommendations**:
  - `use_filter`: Added usage guidelines based on data type and frequency. For example, recommended setting `use_filter='auto'` for ERA5 data.
  - `replace_endpoints_with_lowpass`: Recommended setting a 24-hour window for hourly vorticity data.
  - `use_smoothing` and `use_smoothing_twice`: Added detailed behavior of 'auto' settings and recommendations based on noise levels.
  - `savgol_polynomial`: Explained ideal usage for smoothing based on noise level.
  - `cutoff_low` and `cutoff_high`: Provided guidance for optimal values to filter out planetary and mesoscale influences in vorticity data.
- **Additional Usage Recommendations**: Included cases for using alternative data types like SLP and wind speed and noted expected behavior with phase transitions.
- **Error and Warning Details**: Updated documentation to clarify error conditions related to parameter constraints, particularly for `use_smoothing` and `savgol_polynomial`.

### Code Adjustments
- **Spurious Oscillations Warning**: Added functionality to check for spurious oscillations at the start and end of filtered data, with a warning suggesting adjustments to `use_filter`, `replace_endpoints_with_lowpass`, or `use_smoothing` if detected.
- **`use_filter` Activation**: Clarified that passing an integer as the window length is necessary for activation.
- **Optional Smoothing**: Adjusted `use_smoothing` and `use_smoothing_twice` logic to handle `False` as a deactivation option, bypassing the smoothing process when set to `False`.
- **Savgol Parameter Warnings**: Implemented a check to raise an error if `savgol` window length is smaller than `savgol_polynomial`, ensuring valid parameter configurations.

### Testing Enhancements
- **Output Verification in Tests**: Enhanced test cases to check not only for successful execution but also for expected output consistency. Created expected results for different configurations (`use_filter`, smoothing parameters, and hemisphere adjustments) and verified test output matches these expected results.
- **Suppression of Specific Warnings**: Suppressed spurious oscillation warnings in test cases to reduce unnecessary output during testing.

### Bug Fixes
- **Normalization Clarification**: Resolved confusion regarding normalization in plots by noting that visualization normalization does not impact the core data analysis.


## [1.8.11] - 2024-10-19

### Documentation Update
- Clarified in the **API documentation** and **Usage Guide** that the `series` argument in the `determine_periods` function does not need to be in a specific unit.

## [1.8.10] - 2024-10-18

### Environment and Dependencies

- **Dependency Conflicts Resolved**: Fixed multiple dependency conflicts that were causing failures during installation.
  - Updated `requirements.txt` and `Pipfile` to include all necessary packages and correct versions.
  - Added missing packages like `virtualenv`, `pipenv`, and other dependencies from the `requirements.txt` file.
  - Resolved issues with conflicting dependencies between different versions of `cmocean`, `scipy`, and `xarray`.
 

## [1.8.9] - 2024-10-18

### Bug Fixes
- Fixed Python version on `config.yml`

## [1.8.8] - 2024-10-18

### Bug Fixes
- Fixed conflicting dependencies between `Pipfile` and `requirements.txt`, ensuring compatibility during installation via Pipenv and regular pip installs.

## [1.8.7] - 2024-10-18

### Bug Fixes and Improvements
- **Resolved Legend Color Duplication Issue**: Updated the `plot_all_periods` function to handle multiple occurrences of the same phase (e.g., "intensification", "decay") and ensure that the phase is displayed only once in the legend, regardless of how many times it appears.
  - Generalized the phase handling so that it can manage any number of phase repetitions (e.g., "intensification 2", "mature 3") without affecting the plot’s visual integrity.
  - Fixed the issue with the residual phase showing the wrong color by ensuring that colors for phases are correctly mapped in all cases.
  
### Documentation Updates
- **Added Statement of Need Section**: Incorporated the Statement of Need from the paper into the documentation, explaining the relevance and purpose of the CycloPhaser package, along with detailed references.
  - Improved the introduction to the example in the `usage.rst` to clarify what data is loaded, providing background on the test data for users.
  - Replaced the figures in the `usage.rst` for the ones with the corrected colors.
  - Updated the example in the documentation to use the new structure for accessing the test data
  
### Package Management
- **Added Dependencies to `setup.py`**: Ensured all necessary dependencies are included in the `setup.py` file, resolving the issue of missing dependencies when installing the package via `pip install cyclophaser`.
  - Verified that all dependencies are correctly installed when the package is installed using pip.

### Test Data Accessibility
- **Made Test CSV File Accessible from the Package**: Moved the example test data (`example_file.csv`) to be accessible from the installed package under the `cyclophaser` directory, ensuring that users can run examples without needing to modify paths manually.
  - Updated the usage examples to reflect the new accessible path for the test file.

### Other Improvements
- **Updated Column Names in Example**: Corrected the column name in the example provided in the `usage.rst` to `min_max_zeta_850` (previously `min_zeta_850`), ensuring that the example code runs successfully with the test data provided.


## [1.8.6] - 2024-10-03

### Documentation Improvement
- Added example usage for the `determine_periods` function, including default options and a CSV export feature.
- Included output examples with figures (`test_default.png`, `test_steps_default.png`) showcasing vorticity data with detected cyclone life cycle phases and step-by-step didactic plots.
- Added a section on customizing filtering parameters, including options for `cutoff_low`, `cutoff_high`, and smoothing settings (`use_filter`, `use_smoothing`, `use_smoothing_twice`).
- Introduced detailed explanations for key arguments like `series`, `x`, `plot`, `plot_steps`, and filtering options in the `usage.rst` file.
- Modified the layout of output examples in `usage.rst`, making it more user-friendly and emphasizing the CSV output, figures, and filtering customization.
- Added clarification in the "Important Notes" section explaining the processing of Northern Hemisphere (NH) data through multiplication of vorticity values by -1.

## [1.8.5] - 2024-09-27

### Documentation Improvement
- Updated the figure caption for the **CycloPhaser Methodology** to provide a more detailed and clearer explanation of the methodology steps. 
  - Each panel in the figure is now explained thoroughly, highlighting the key processes involved, including preprocessing with the Lanczos filter, smoothing with the Savitzky-Golay filter, and the detection of cyclone life cycle phases.
  - The new caption ensures users can easily follow the steps represented in the figure, aligning with the phase detection process described in the documentation.

## [1.8.4] - 2024-09-26

### Bug Fixes 
  - Updated the image path in `overview.rst` to point to the correct location.

## [1.8.3] - 2024-09-26

### Bug Fixes
- Fixed an issue where the image in the "Procedure Overview" section of the documentation was not rendering correctly. 
  - Updated the image path in `overview.rst` to point to the correct location.
  - Replaced the image format from `.pdf` to `.jpg` for better compatibility and ensured the image file is now located in the correct folder (`docs/_images`).


## [1.8.2] - 2024-09-26

### Documentation Updated
- Added an overview section in the documentation, explaining the CycloPhaser program and its main purpose, including its method for detecting cyclone life cycle phases by analyzing vorticity and derivative time series.
- Inserted a figure illustrating the CycloPhaser methodology and included references to the original publication for further details.
- Updated the procedure overview with a step-by-step explanation of the CycloPhaser methodology, detailing the filtering, phase detection, and residual stage processes.

## [1.8.1] - 2024-09-17

### Bug fixes
- Fixed inconsistency in README referencing MIT while `LICENSE` pointed to GPL v3.0. Resolved across all documentation.

## [1.8.0] - 2024-09-17

### Updated
- Updated `usage.rst` to include detailed explanations for all arguments of the `determine_periods` function, including new filtering and threshold options.
- Added new example usage sections in `usage.rst`, demonstrating how to:
  - Process vorticity data from ERA5.
  - Handle vorticity data from the TRACK algorithm (Hodges, 1994, 1995).
  - Customize filtering options for `determine_periods`.
- Clarified Southern Hemisphere support in the tool and noted future updates for Northern Hemisphere support.
- Updated `requirements.txt` by freezing the environment using `pip freeze` to ensure that all current dependencies and their versions are captured.
- Improved test coverage in `test_determine_periods_with_options.py`:
  - Added new options for ERA5, basic processing, and TRACK algorithms.
  - Ensured proper assertion checks for DataFrame outputs in all tests.
- Updated `api.rst` to provide detailed parameter descriptions and example usage of the `determine_periods` function for easier user reference.
- Enhanced the `Contribute` section in the documentation to provide a step-by-step guide for contributing to CycloPhaser via GitHub.
  - Added detailed instructions on forking, cloning, branching, and submitting pull requests.
  - Included guidance on running tests, committing changes, and adhering to code style using tools like `flake8` and `black`.
  - Encouraged contributions to both code and documentation, as well as participation in the issue tracker.
- Added badges for supported Python versions and Pypi version to the README file.
- Included ``testing.rst`` in the documentation to explain how users can run tests and validate functionality.

### Changed
- Refined the `determine_periods.py` script by exposing all arguments from `process_vorticity_args` directly as function arguments, making the usage more transparent and eliminating the need for nested dictionaries.
- Refactored `get_periods` to accept threshold parameters directly instead of handling them through a `default_args` dictionary.
- Updated the test cases in `test_determine_periods_with_options.py` to reflect the new function signatures by passing all processing and threshold arguments explicitly.
- Improved robustness in the `get_periods` function with better handling of arguments and integration with vorticity processing options.
- Enhanced docstrings for various functions, providing clearer explanations and usage examples across the package.

### Bug fixes
- Resolved the `KeyError: 'threshold_decay_length'` by ensuring all required parameters are passed to `find_intensification_period`, `find_decay_period`, and other related functions.


## [1.7.4] - 2024-07-18

### Bug fixes 
- **determine_periods.py**: Avoided the FutureWarning while filling NaN values in a DataFrame slice

### Improved 
- Modified relative imports to ensure compatibility when running the script as a module.

### Updated
- **requirements.txt**: Updated dependencies to the latest compatible versions.

## [1.7.3] - 2024-04-15

### Bug fixes 

- **determine_periods.py**: reverted threshold_intensification_length back to 7.5%


## [1.7.2] - 2024-04-13

### Bug fixes 

- **determine_periods.py**: fixed wrong imports
- **find_stages.py**: fixed not finding residual period when the gap between stages is too large - was not really fixed on last update

## [1.7.1] - 2024-04-12

### Bug fixes 

- **determine_periods.py**: fixed not finding residual period when the gap between stages is too large

## [1.7.0] - 2024-04-11

### Modified

- **determine_periods.py**: thresholds for phase determination can be passed as optional arguments by the user
- **find_stages.py**: added arguments for passing the thresholds for phase determination
-- **plots.py**: used custom arguments from phase determination for plotting

### Bug fixes

- Wrong imports on scripts

## [1.6.0] - 2023-12-18

### Modified

- **README.md**: Updated to focus on directing users to the Read the Docs for usage and documentation. Simplified to enhance readability and direct users to comprehensive documentation online.
- **setup.py**: Included badges for download statistics and build status. The long description is now dynamically sourced from the README file to maintain consistency across platforms.
- **api.rst**: Added detailed information about the package's API, providing users with a clear understanding of available functionalities and usage.
- **installation.rst**: Updated to guide users for installation via pip, simplifying the installation process.
- **usage.rst**: Expanded to include detailed examples and more comprehensive documentation, offering users practical guidance and improved understanding of the package's capabilities.

These updates aim to enhance the user experience by providing clearer, more accessible documentation and a streamlined setup process.

## [1.5.6] - 2023-12-18

### Added

 - Documentation requirements text file

## [1.5.5] - 2023-12-18

### Bug fixes

 - Read the Docs configuration: python version

## [1.5.4] - 2023-12-18

### Bug fixes

 - Read the Docs configuration

## [1.5.3] - 2023-12-18

### Modified

 - Missing Read the Docs configuration: os version

## [1.5.2] - 2023-12-18

### Added

 - Missing Read the Docs configuration.


## [1.5.1] - 2023-12-18

### Added

- Integrated documentation with Read the Docs.
- Created and formatted Sphinx documentation files including `index.rst`, `installation.rst`, `usage.rst`, `api.rst`, `contribute.rst`, `changelog.rst`, and `license.rst`.

### Modified

- Updated project structure to support Sphinx documentation generation and hosting on Read the Docs.


## [1.5] - 2023-12-18

### Modified

- Updated the `determine_periods` function:
  - Changed the main input to accept a series of vorticity data directly.
  - Added an optional `x` parameter to handle time series or other types of indices.
  - Removed the `vorticity_column` parameter, as it is no longer applicable with the new input method.

## [1.4.2] - 2023-09-06

- Fixing version numbers

## [1.4.1] - 2023-09-06

### Modified

- Incipient stage will fill consecutive intensification and decay when they are on the start of the series and they are followed by another instensification
- Residual will not fill NaNs in the middle of the series
- Decay stage minimum duration updated from 12% to 7.5% to match intensification


## [1.4.0] - 2023-09-03

### Modified

- Incipient stage no longer fills decay when it's on the beginning of life cycle

## [1.3.15] - 2023-09-03

### Bug fixes

- CircleCI authentication for Test-Pypi
- Residual phases on the middle of the series

## [1.3.14] - 2023-08-30

### Added

- Added README
- Renamed array_vorticity to process_vorticity

## [1.3.13] - 2023-08-29

### Bug fixes

- Will only attempt to replace endpoints if use_filter is applied

## [1.3.12] - 2023-08-29

### Bug fixes

- config.yml

## [1.3.11] - 2023-08-29

### Bug fixes

- Bug fixes for requirements.txt

## [1.3.10] - 2023-08-29

### Added

- Directory for plotting images and exporting csv to be passed as argument for determine_periods
- Requirements file for pip

## [1.3.1] to [1.3.9] - 2023-08-29

- Multiple bug with testing solved

## [1.3.0] - 2023-08-29

### Added

- Added filtering and smoothing options as function parameters
- Added documentation

### Bug fixes

- Fixed plot_all_periods legends not diplaying properly

### Others

- Separated plots and finding periods on distinct files
