API reference
=============

The three public entry points. Their parameters and defaults are read from the
code (the docstrings and the signatures).

determine_periods
-----------------

Filtering and phase detection in one call.

.. autofunction:: cyclophaser.determine_periods

process_vorticity
-----------------

The filtering step alone.

.. autofunction:: cyclophaser.determine_periods.process_vorticity

get_periods
-----------

The phase-detection step alone, on the output of ``process_vorticity``.

.. autofunction:: cyclophaser.determine_periods.get_periods
