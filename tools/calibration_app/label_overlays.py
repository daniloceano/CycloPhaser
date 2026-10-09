"""Filtered/smoothed overlays for the Manual labelling page.

Moved out of app.py (I1 of the app redesign). The Manual labelling page is now a
page of its own, and app.py's Calibrate sidebar no longer runs while it is open,
so the overlay provider can no longer read the sidebar's widget variables as
globals. It reads the Calibrate sidebar's last published filter settings from
session_state instead (see `live_filter_params`).

This is the one place the labelling page reaches into cyclophaser:
label_tab.py itself imports nothing from the package (see its module
docstring), so the curves the labeller can choose to reveal are guaranteed to be
the SAME function the detector runs, computed here and handed down as plain
numbers plus a label/color pair.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pandas as pd

from cyclophaser.determine_periods import process_vorticity

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))
import layer_inspector as li  # noqa: E402
from package_args import package_use_filter  # noqa: E402

# Colors/labels are supplied HERE, not invented in label_tab.py: that module
# stays generic about what an "overlay" is (a name, a label, a color, values),
# so it never needs to know cyclophaser's own vocabulary to draw one.
# Progressively thinner in the app's stroke-width scheme (see _CHART_JS),
# matching pipeline order: each is one more processing step than the last.
LABEL_OVERLAY_STYLE = {
    "filtered_vorticity": {"label": "filtered_vorticity — Lanczos band-pass",
                          "color": "#1f9e89"},
    "vorticity_smoothed": {"label": "vorticity_smoothed — 1st Savitzky-Golay pass",
                          "color": "#e8702a"},
    "vorticity_smoothed2": {"label": "vorticity_smoothed2 — 2nd pass (what phase "
                                    "detection is actually run against)",
                           "color": "#8856a7"},
}

# process_vorticity's own argument names — the same keys the Calibrate page
# publishes under `_bench_live_config["filter_params"]`.
FILTER_KEYS = ("use_filter", "cutoff_low", "cutoff_high",
               "replace_endpoints_with_lowpass", "use_smoothing",
               "use_smoothing_twice", "savgol_polynomial", "boundary_padding")


def live_filter_params(session_state) -> tuple[dict, bool]:
    """The filter settings the overlays are computed with, and where they came from.

    Returns `(params, from_sidebar)`. `params` are the Calibrate sidebar's
    filter settings as that page last published them (`_bench_live_config`,
    the same document the "Add Current settings" button of the Compare and
    Validate pages reads), so an overlay shows what the detector sees under the calibration
    currently being tried. When Calibrate has not run in this session there is
    no sidebar state yet; `params` are then process_vorticity's own signature
    defaults — which is also what a fresh Calibrate sidebar starts from — and
    `from_sidebar` is False so the page can say so.
    """
    cfg = session_state.get("_bench_live_config") or {}
    fp = cfg.get("filter_params") or {}
    if all(k in fp for k in FILTER_KEYS):
        return {k: fp[k] for k in FILTER_KEYS}, True
    sig = inspect.signature(process_vorticity).parameters
    return {k: sig[k].default for k in FILTER_KEYS}, False


def label_overlays(values: pd.Series, filter_params: dict) -> dict[str, dict]:
    """The three process_vorticity layers for one raw series.

    Called ONLY from label_tab.py's overlay controls, and only after the
    labeller has explicitly opted into seeing it.

    Returns {name: {"label": str, "color": str, "values": [float, ...],
    "shared_values": [float, ...]}}.

    * `values` are in physical units.
    * `shared_values` are the same curves on the inspector's grouped 0-1 band
      (item 30c): `layer_inspector.rescaler` over the THREE layers together,
      so the amplitude each smoothing pass removes stays visible. label_tab.py
      maps that band onto the raw series' own range, or draws it as is, per
      the scale the labeller picks.

    The grouping is computed here, where the package's names may appear, rather
    than in label_tab.py, whose AST must stay free of them. The group is always
    all three layers, whichever are switched on, so toggling one never
    rescales the others.
    """
    fp = dict(filter_params)
    fp["use_filter"] = package_use_filter(fp["use_filter"])
    vort = process_vorticity(pd.DataFrame({"zeta": values}), **fp)
    group = li.rescaler([vort[name].values for name in LABEL_OVERLAY_STYLE], normalize=True)
    return {
        name: {**style,
               "values": [float(v) for v in vort[name].values],
               "shared_values": [float(v) for v in group(vort[name].values)]}
        for name, style in LABEL_OVERLAY_STYLE.items()
    }
