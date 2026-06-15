.. _calibration_tool:

Interactive Calibration Tool
============================

.. contents::
   :local:
   :depth: 2

Overview
--------

CycloPhaser ships with a browser-based calibration app built with
`Streamlit <https://streamlit.io>`_ that allows you to tune all
filtering and phase-detection parameters visually, inspect how parameter
choices affect individual cyclones or a batch of them, and export
configurations for use in your own scripts.

The tool is **not part of the PyPI package** and is not installed by
``pip install cyclophaser``. It lives in the repository under
``tools/calibration_app/``.

Features
~~~~~~~~

- **Visual parameter tuning** — adjust the Lanczos filter cutoffs,
  Savgol smoothing windows, and all seven phase-detection thresholds
  through sidebar sliders and observe results immediately.
- **Multi-cyclone grid view** — upload multiple track CSV files and
  scan results in a configurable grid (1–6 columns) with compact
  twin-axis thumbnails for dense comparison.
- **Detailed diagnostics** — expand individual panels to see all four
  vorticity series (raw, filtered, smoothed ×2), phase boundaries, and
  per-phase durations.
- **YAML export / import** — save calibrated parameters to a YAML file
  and re-import them in a later session or pass them directly to
  ``determine_periods`` in a script.
- **CSV and figure export** — download detected phases as CSV and the
  diagnostic figure as PNG for each cyclone, or download a ZIP bundle
  with all cyclones at once.

Hosted version
--------------

A publicly hosted instance is available at:

**<STREAMLIT_APP_URL>**

.. note::

   Replace ``<STREAMLIT_APP_URL>`` with the actual URL after deploying
   to Streamlit Community Cloud.

Running locally
---------------

**Step 1 — Clone the repository**

.. code-block:: bash

   git clone https://github.com/daniloceano/CycloPhaser.git
   cd CycloPhaser

**Step 2 — Install dependencies**

.. code-block:: bash

   pip install -r tools/calibration_app/requirements.txt

This installs the app dependencies and pulls ``cyclophaser >= 2.0.0``
from PyPI. If you are actively developing CycloPhaser and want changes
to the source to take effect immediately, use the editable-install
variant instead:

.. code-block:: bash

   pip install -e .
   pip install -r tools/calibration_app/requirements-app.txt

**Step 3 — Launch**

.. code-block:: bash

   streamlit run tools/calibration_app/app.py

The app opens in your default browser at ``http://localhost:8501``.

Considerations and limitations
-------------------------------

Data privacy on the hosted version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The hosted app runs on Streamlit Community Cloud servers. Any track
files you upload are transmitted to those servers and held **in memory
for the duration of your session only** — they are not written to
persistent storage by the app. However, because files leave your local
machine, exercise caution with unpublished or sensitive data. For those
cases, run the app locally following the steps above; your files never
leave your computer.

Resource limits on the free tier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Streamlit Community Cloud free-tier instances have limited CPU and RAM.
Processing a large number of cyclones (typically more than ~30–50 track
files at once, depending on series length) may be slow or may exhaust
available memory. If you need to process many cyclones in batch, use
the scripted approach described below.

Batch processing without the app
---------------------------------

When you already have calibrated parameters (for example exported as a
YAML from the app) and want to apply them to a large collection of
tracks, a plain Python script is faster and more reproducible than the
browser interface. The example below reads every ``.csv`` file from a
``data/tracks/`` directory, runs ``determine_periods`` with custom
parameters, and writes a combined ``all_phases.csv`` summary file.

.. code-block:: python

   """
   Batch cyclone phase detection using CycloPhaser.

   Adjust the paths and parameters below to match your dataset.
   Parameters can be copied from a YAML file exported by the
   calibration app.

   Usage:
       python batch_detect_phases.py
   """

   from pathlib import Path
   import pandas as pd
   from cyclophaser import determine_periods

   # --- Configuration --------------------------------------------------
   TRACKS_DIR  = Path("data/tracks")     # directory with track CSV files
   RESULTS_DIR = Path("results/phases")  # output directory
   RESULTS_DIR.mkdir(parents=True, exist_ok=True)

   # Parameters calibrated with the app (edit or load from your YAML)
   PARAMS = dict(
       hemisphere="southern",
       use_filter=True,
       cutoff_low=168,
       cutoff_high=48,
       replace_endpoints_with_lowpass=24,
       use_smoothing="auto",
       use_smoothing_twice="auto",
       savgol_polynomial=3,
   )
   # --------------------------------------------------------------------

   track_files = sorted(TRACKS_DIR.glob("*.csv"))
   if not track_files:
       raise FileNotFoundError(f"No CSV files found in {TRACKS_DIR}")

   summary_records = []

   for track_file in track_files:
       cyclone_id = track_file.stem
       out_csv    = str(RESULTS_DIR / cyclone_id)

       try:
           track  = pd.read_csv(track_file, parse_dates=[0],
                                delimiter=";", index_col=0)
           series = track["min_max_zeta_850"]

           determine_periods(series, export_dict=out_csv, **PARAMS)

           phases = pd.read_csv(f"{out_csv}.csv")
           phases.insert(0, "cyclone_id", cyclone_id)
           summary_records.append(phases)
           print(f"OK   {cyclone_id}")

       except Exception as exc:
           print(f"FAIL {cyclone_id}: {exc}")

   if summary_records:
       all_phases = pd.concat(summary_records, ignore_index=True)
       all_phases.to_csv(RESULTS_DIR / "all_phases.csv", index=False)
       print(f"\nSummary written to {RESULTS_DIR / 'all_phases.csv'}")
       print(f"Processed {len(summary_records)} / {len(track_files)} cyclones successfully.")

Adapting the column name
~~~~~~~~~~~~~~~~~~~~~~~~

The example above assumes the track CSV contains a column named
``min_max_zeta_850``. Replace this with the actual vorticity column
name in your dataset. Refer to the :ref:`usage` guide for a description
of the expected input format.

Loading parameters from a YAML file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you exported parameters from the calibration app as ``params.yaml``,
you can load them programmatically:

.. code-block:: python

   import yaml
   with open("params.yaml") as f:
       config = yaml.safe_load(f)

   # The YAML contains 'filter_options' and 'period_options' sub-dicts.
   # Flatten them into kwargs for determine_periods:
   params = {}
   params.update(config.get("filter_options", {}))
   params.update(config.get("period_options", {}))
   # rename keys that differ between YAML and API if needed
   params["replace_endpoints_with_lowpass"] = params.pop(
       "replace_endpoints_with_lowpass", 24)

   determine_periods(series, export_dict=out_csv, **params)
