# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


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
