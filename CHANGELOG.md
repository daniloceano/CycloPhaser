# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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
