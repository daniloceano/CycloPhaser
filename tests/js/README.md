# Headless checks for the labelling chart

`chart_drag_spec.mjs` runs `tools/calibration_app/label_tab.py`'s `_CHART_JS`
against a minimal SVG/DOM stub (`dom.mjs`) under Node, with no browser.

It exists because the labelling chart is hand-drawn JavaScript, and the one
property that matters most about it cannot be checked from Python: that a drag
is **horizontal only**. `dom.mjs` supplies pointer events whose `clientY` throws
if anything reads it, so "the bar cannot leave the time axis" is enforced rather
than asserted.

Driven from `tests/test_manual_labels.py`, which writes `chart.mjs` out of the
Python module before invoking Node — so the spec always runs the JS that ships.
Skipped when Node is not installed.

    node tests/js/chart_drag_spec.mjs      # after chart.mjs has been written
