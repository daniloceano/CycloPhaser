"""phase_figures — each panel draws its OWN column's smoothed series (item 30c).

The Compare and Validate pages draw every per-track figure with
`phase_figures.cell_figure` / `stacked_figure`. These pins were the Benchmark
page's (tests/test_benchmark_apptest.py, retired with that page in the benchmark
review, I3) and now run against the module both pages use.

The two configurations: params-track, and params-track with ONE declared
non-default value, `filter_params.cutoff_high` = 48 (params-track: 18). It changes
the smoothed series, which `test_two_configurations_smooth_differently` checks
first — without it, "each cell draws its own column's curve" would also hold for
a cell drawing the other column's. The track is a train track.

Gated on streamlit like every other test of the calibration app: the CI recipe
installs only the wheel, pytest and PyYAML, and app tests stay out of it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "tools" / "calibration_app"

pytest.importorskip("streamlit")
yaml = pytest.importorskip("yaml")
sys.path.insert(0, str(APP_DIR))
import benchmark_core as bc  # noqa: E402
import layer_inspector as li  # noqa: E402
import phase_figures as pf  # noqa: E402
import validate_core as vc  # noqa: E402

CONFIG = "cyclophaser_params-track.yaml"
DECLARED = ("filter_params", "cutoff_high", 48, 18)


def _docs() -> tuple[dict, dict]:
    sec, key, value, in_track = DECLARED
    b = yaml.safe_load((bc.CONFIGS_DIR / CONFIG).read_text())
    assert b[sec][key] == in_track
    a = {**b, sec: {**b[sec], key: value}}
    return a, b


def _track():
    pop = vc.load_population(False)
    sid = sorted(pop["series"])[0]
    return pop["series"][sid]


def _run(doc, series) -> dict:
    pv, gp = bc.split_config(doc)
    res = bc.run_series(pv, gp, series)
    assert res["error"] is None, res["error"]
    return res


def _filtered_lines(fig):
    return [ln for ax in fig.axes for ln in ax.lines
            if ln.get_color() == pf.FILTERED_COLOR]


def _z(res) -> tuple:
    return tuple(float(v) for v in res["z"].values)


def test_two_configurations_smooth_differently():
    """POSITIVE CONTROL for the pins below."""
    a, b = _docs()
    series = _track()
    za, zb = _run(a, series)["z"].to_numpy(), _run(b, series)["z"].to_numpy()
    assert abs(za - zb).max() > 1e-7, "the two configs smooth identically here"


def test_each_cell_draws_its_own_columns_smoothed_series():
    a, b = _docs()
    series = _track()
    res_a, res_b = _run(a, series), _run(b, series)
    values = tuple(float(v) for v in series.values)
    for res, other in ((res_a, res_b), (res_b, res_a)):
        fig = pf.cell_figure(values, tuple(res["runs"]), "col", _z(res), li.PHASE_COLORS)
        lines = _filtered_lines(fig)
        assert len(lines) == 1, "a cell must draw exactly one smoothed curve"
        drawn = list(lines[0].get_ydata())
        assert drawn == list(_z(res))
        assert drawn != list(_z(other))
        # Grid convention: the smoothed curve on an axis of its own, raw in front.
        raw_ax = next(ax for ax in fig.axes
                      if any(ln.get_color() == pf.RAW_COLOR for ln in ax.lines))
        assert lines[0].axes is not raw_ax
        assert raw_ax.get_zorder() > lines[0].axes.get_zorder()


def test_a_cell_without_a_smoothed_series_draws_raw_only():
    """A published-release column (Validate) carries no `z`; its cell must not
    invent one."""
    a, _b = _docs()
    series = _track()
    res = _run(a, series)
    fig = pf.cell_figure(tuple(float(v) for v in series.values), tuple(res["runs"]),
                         "snapshot", None, li.PHASE_COLORS)
    assert _filtered_lines(fig) == []
    assert any(ln.get_color() == pf.RAW_COLOR for ax in fig.axes for ln in ax.lines)


def test_each_stacked_panel_draws_its_own_columns_smoothed_series():
    a, b = _docs()
    series = _track()
    res_a, res_b = _run(a, series), _run(b, series)
    za, zb = _z(res_a), _z(res_b)
    panels = (("label", tuple(res_a["runs"]), None),
              ("A", tuple(res_a["runs"]), za),
              ("B", tuple(res_b["runs"]), zb))
    fig = pf.stacked_figure(tuple(float(v) for v in series.values), panels,
                            li.PHASE_COLORS)
    lines = _filtered_lines(fig)
    assert [list(ln.get_ydata()) for ln in lines] == [list(za), list(zb)]
    # one twin range for every panel, so a flatter curve reads as flatter
    assert lines[0].axes.get_ylim() == lines[1].axes.get_ylim()
