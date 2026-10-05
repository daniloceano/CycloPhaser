# Data used by the documentation

`example_track_hourly.csv` — the example track of the usage guide.

* What it is: hourly 850 hPa relative vorticity (s⁻¹) at the centre of one
  South-Atlantic extratropical cyclone, from ERA5 (column `min_max_zeta_850`).
  Southern-Hemisphere sign: a deeper cyclone is more negative.
* Where it comes from: a byte-for-byte copy of
  `tests/calibration_data/20150436.csv`, one of the 51 real ERA5 cyclone tracks
  (2015-2020) added to the repository in commit `11e530a` for the package's
  real-data tests. Track id `20150436` is in the training split of
  `research/labels/split.yaml`.
* Why this one: the package's own example file (`cyclophaser/example_data/`) is
  3-hourly, while the filtering defaults are counted in time steps and meant for
  hourly series. The candidates and the choice are recorded in
  `research/cleanup/passo4/hourly_series_options.md`.
