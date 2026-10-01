How it works
============

CycloPhaser works in two steps. It first **filters** the vorticity series, to
remove the noise and the slow background. It then **detects phases** on the
filtered series, from its peaks and valleys. The figure follows one synthetic
cyclone through both steps. Every panel is the package's own output, run with
the defaults (made by ``docs/figures/make_methodology_figure.py`` in the
repository).

.. figure:: generated/methodology.png
   :alt: The filtering and phase-detection steps of CycloPhaser, panels A to K
   :width: 100%

   From the raw vorticity series (A) to the final phases (K). In the
   Southern-Hemisphere convention used here, a deeper cyclone has a lower
   (more negative) vorticity, so a deepening is a descent of the curve.

Filtering
---------

**(A) Raw series.** The relative vorticity at the cyclone's centre, one value
per time step, as it comes from the tracking.

**(B) Filtered series.** A Lanczos band-pass filter keeps the variations whose
period lies between two cutoffs: it removes the fast noise and the slow
background. Before filtering, the series is extended beyond its two ends by
mirroring it (``boundary_padding="reflect"``), so the filter does not invent a
jump at the start or the end of the track.

**(C) Smoothing (optional).** A Savitzky-Golay smoothing, once or twice, can be
applied after the filter. It is **off by default**.

**(D) Series used for detection.** The series the phases are read from. With
the defaults, smoothing is off, so it is the filtered series of (B). Its first
and second time derivatives are computed too.

Phase detection
---------------

**(E) Peaks and valleys.** The detection works on the peaks (filled dots) and
valleys (open dots) of the series. An oscillation that is weak compared with the
strongest one in the same series is discarded (the crossed-out valley and peak,
during the decay): it is too small to mark a change of phase. The type of the very first point is checked
against the next extremum that survives.

The phases are then assigned by one rule after another, in this order. A later
rule can overwrite what an earlier one wrote.

**(F) Intensification.** A stretch from a peak to the following valley, where
the cyclone deepens. It has to last long enough and to deepen enough compared
with the whole series.

**(G) Decay.** A stretch from a valley to the following peak, where the
cyclone weakens. It, too, has to last long enough.

**(H) Mature.** Around each valley deep enough compared with the whole series,
the stretch where the vorticity stays close to its extreme value: still at least
a given fraction as intense, on each side, as the peak-to-valley amplitude of
that cycle.

**(I) Residual.** What remains after the last decay. Here, the cyclone deepens
again at the end without reaching a mature phase, so that stretch is residual.
When the stretch after the last decay is flat instead, without a real
re-deepening, the decay is extended over it rather than leaving it residual.

Between (I) and (J), short gaps between phases are filled and phases too short
to stand on their own are removed.

**(J) Incipient.** The last rule to run, although incipient is the first phase.
It is the flat stretch at the start of the track, while the vorticity still
changes slowly, and it ends where it starts to change faster. It does not erase
an intensification that lies wholly before that point.

**(K) Final phases.** The phase of every time step, over the series used for
detection (black) and the raw series (grey).

Entry points
------------

* ``determine_periods(series, ...)`` does both steps, and can also save a
  figure and a table of the phases (see :doc:`usage`).
* ``process_vorticity(...)`` does the filtering (A to D), and
  ``get_periods(vorticity, ...)`` does the phase detection (E to K) on its
  output. Use them to run the two steps separately.

The rules of (F) to (J) are functions of ``cyclophaser.find_stages``. They are
**internal**: ``get_periods`` calls them with every parameter set. Called
directly without a parameter, they fall back to older values that are not the
package defaults.
