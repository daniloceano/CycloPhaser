Running the tests
=================

From a clone of the repository, install CycloPhaser and the test dependencies,
then run the suite:

.. code-block:: bash

   git clone https://github.com/daniloceano/CycloPhaser.git
   cd CycloPhaser
   pip install -e .
   pip install pytest pyyaml
   pytest -m "not browser"

``-m "not browser"`` leaves out the tests marked ``browser``. Those drive a real
Chromium against the calibration app; they need Playwright and a browser, and
they are run by hand.

What the suite checks, among other things:

* the filtering and the phase detection against stored reference outputs;
* the phase timing on synthetic cyclones, against the manual labels of those
  series;
* the calibration app's logic (configuration files, track reading, the layer
  inspector).

The continuous-integration job runs the suite on Python 3.12.
