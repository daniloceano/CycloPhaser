.. _calibration_tool:

Calibration app
===============

The calibration app runs CycloPhaser on your own tracks, in the browser, and
shows how each filtering and phase-detection parameter changes the result.

**Hosted version:** https://cyclophaser.streamlit.app

What it is for
--------------

* Tune the filtering and the phase-detection parameters on a set of tracks and
  see the detected phases of every track at once.
* Inspect one track in detail: the filtered series, the peaks and valleys, and
  what each detection rule decided.
* Compare configurations side by side (the Benchmark tab).
* **Export** the parameters as a YAML file, and load it back later.

The exported YAML has two sections, ``filter_params`` and ``phase_params``.
Pass them to ``determine_periods`` to run the same configuration in a script:

.. code-block:: python

   import yaml
   from cyclophaser import determine_periods

   with open("parameters.yaml") as f:
       config = yaml.safe_load(f)

   result = determine_periods(series, **config["filter_params"], **config["phase_params"])

A check that is switched off in the app (the prominence filter, the decay-tail
extension) is written to the file as ``null``, which is how the package reads
"off".

The hosted version holds uploaded files in memory for the session only, but the
files do leave your computer. For unpublished or sensitive data, run the app
locally.

Run it locally
--------------

From a clone of the repository:

.. code-block:: bash

   git clone https://github.com/daniloceano/CycloPhaser.git
   cd CycloPhaser/tools/calibration_app
   pip install -r requirements-app.txt
   streamlit run app.py

``requirements-app.txt`` installs CycloPhaser from the clone, in editable mode.
The app opens at http://localhost:8501.

The app's own documentation (input formats, display modes, the Benchmark tab)
is in :repo:`tools/calibration_app/README.md`.
