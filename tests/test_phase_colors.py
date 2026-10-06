"""The calibration app's phase palette is the one the package draws with.

cyclophaser/plots.py colours the phase figures (and so the PNGs and the Grid)
with a literal `colors_phases`; the app keeps its own copy in
layer_inspector.PHASE_COLORS, its single source (app.py, the Inspector renderers
and the set statistics read it). The package file is READ, never imported or
changed: the literal is taken from its source with `ast`.

The Benchmark and Manual labelling pages still carry copies of their own
(benchmark_tab.PHASE_COLORS, research/labels/labels_core.PHASE_COLORS); they are
checked here as well, so no copy can drift.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "tools" / "calibration_app"


def _package_palette() -> dict:
    tree = ast.parse((REPO_ROOT / "cyclophaser" / "plots.py").read_text())
    found = [ast.literal_eval(node.value) for node in ast.walk(tree)
             if isinstance(node, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "colors_phases" for t in node.targets)]
    assert found, "no `colors_phases` literal in cyclophaser/plots.py"
    assert all(f == found[0] for f in found), found
    return found[0]


def test_the_app_palette_is_the_package_palette():
    sys.path.insert(0, str(APP_DIR))
    import layer_inspector
    assert layer_inspector.PHASE_COLORS == _package_palette()
    assert set(_package_palette()) == {"incipient", "intensification", "mature",
                                       "decay", "residual"}


def test_the_app_reads_the_single_source():
    src = (APP_DIR / "app.py").read_text()
    assert "PHASE_COLORS = li.PHASE_COLORS" in src
    # the phase colours are not re-typed in the Calibrate page's own modules
    # (the Inspector renderers import PHASE_COLORS from layer_inspector)
    for mod in ("app.py", "set_stats.py"):
        text = (APP_DIR / mod).read_text()
        for hex_ in _package_palette().values():
            if hex_.startswith("#"):
                assert hex_ not in text, (mod, hex_)
    for mod in ("inspector_plotly.py", "inspector_mpl.py"):
        assert "PHASE_COLORS = {" not in (APP_DIR / mod).read_text(), mod


def test_the_other_pages_copies_have_not_drifted():
    pytest.importorskip("streamlit")
    sys.path.insert(0, str(APP_DIR))
    sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))
    import benchmark_tab
    import labels_core
    assert benchmark_tab.PHASE_COLORS == _package_palette()
    assert labels_core.PHASE_COLORS == _package_palette()
