"""Manual labelling page (developer key only) — BLIND labelling of the whole
phase sequence.

Cut off from the Calibrate page on purpose: it does not read the Calibrate page's
loaded tracks or run any detection on them. It loads its own series (the 51
calibration tracks, the 12 synthetic cases and the item-30 batches) straight from
disk and draws the raw input; see label_tab.py's module docstring for why that
isolation is the requirement. The one thing taken from Calibrate is the filter
setting the optional overlays are computed with (label_overlays.py).

Saving writes research/labels/manual_labels.yaml, which is why the page is only
in the menu with the developer key (app.py, `_developer_mode`).
"""

import sys
from pathlib import Path

import streamlit as st

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import label_overlays  # noqa: E402
import label_tab  # noqa: E402

_filter_params, _from_sidebar = label_overlays.live_filter_params(st.session_state)



def _overlay_provider(values):
    return label_overlays.label_overlays(values, _filter_params)


# Named on the provider rather than passed to render(): render's signature is
# pinned by tests/test_manual_labels.py to (default_tolerance, overlay_provider).
_overlay_provider.source = (
    "the Calibrate sidebar's filter settings" if _from_sidebar else
    "the package's default filter settings (Calibrate has not been opened in "
    "this session)")

label_tab.render(overlay_provider=_overlay_provider)
