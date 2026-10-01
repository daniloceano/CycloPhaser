Installation
============

CycloPhaser is on PyPI:

.. code-block:: bash

   pip install cyclophaser

We recommend installing it in its own environment, for example:

.. code-block:: bash

   python -m venv cyclophaser_env
   source cyclophaser_env/bin/activate      # Windows: cyclophaser_env\Scripts\activate
   pip install cyclophaser

or, with conda:

.. code-block:: bash

   conda create -n cyclophaser_env python=3.12
   conda activate cyclophaser_env
   pip install cyclophaser

pip installs the dependencies (NumPy, SciPy, pandas, xarray, Matplotlib, among
others).

Python version
--------------

CycloPhaser is tested with **Python 3.12**: that is the version its
continuous-integration job runs the test suite on.
