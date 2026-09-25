"""The Inspector view, driven through the real app script via AppTest — no browser.

Item 30a: the app sends ``mature_min_depth`` and ``intensification_min_depth``
to the inspector on every run, and ``layer_inspector.build_args_periods`` used
to reject both, so the view showed "Inspector error: ..." for any track. The
pure fidelity tests live in tests/test_layer_inspector.py; this file checks
the path the user actually sees: the error is gone, and the ledger tables carry
the depth floors.

The app loads only ``example_file`` by default. Its intensification candidates
have D2 = 1.000 and 0.565 — both above the slider's 0.50 maximum — so the
intensification floor cannot reject anything here and is checked only for
consistency (every ACCEPTED candidate clears it). The mature floor at 1.00 does
remove valleys, and that reason must reach the table.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"
sys.path.insert(0, str(APP.parent))

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

import layer_inspector as li  # noqa: E402  (the same module object app.py imports)

_INSPECTOR_ERROR = "Inspector error"


def _inspector(int_floor: float, mat_floor: float) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=180)
    at.run()
    for r in at.radio:
        if set(r.options) >= {"Grid", "Inspector", "Label"}:
            r.set_value("Inspector")
            break
    at.run()
    for key in ("inspector_ribbon", "inspector_ledger", "inspector_mature"):
        at.checkbox(key=key).check()
    at.slider(key="intensification_min_depth").set_value(int_floor)
    at.slider(key="mature_min_depth").set_value(mat_floor)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _inspector_errors(at) -> list:
    return [e.value for e in at.error if e.value.startswith(_INSPECTOR_ERROR)]


def test_positive_control_the_pre_fix_key_set_shows_the_inspector_error(monkeypatch):
    """Without the two keys the view must show the error — otherwise the
    "no error" assertion below could not see a regression at all."""
    monkeypatch.delitem(li._ARGS_PERIODS_DEFAULTS, "mature_min_depth")
    monkeypatch.delitem(li._ARGS_PERIODS_DEFAULTS, "intensification_min_depth")
    errors = _inspector_errors(_inspector(0.0, 0.0))
    assert any("not stage-detection parameters" in e for e in errors), errors


def test_inspector_renders_with_the_depth_floors_set():
    at = _inspector(0.50, 1.00)
    assert _inspector_errors(at) == []

    tables = {("Verdict" in d.value.columns): d.value for d in at.dataframe}
    ledger, mature = tables[True], tables[False]
    assert "Depth (D2)" in ledger.columns
    assert "Depth (D1)" in mature.columns

    accepted = ledger[(ledger["Step"] == "intensification")
                      & ledger["Type"].str.startswith("candidate")
                      & (ledger["Verdict"] == "ACCEPTED")]
    assert len(accepted) > 0
    assert (accepted["Depth (D2)"].astype(float) >= 0.50).all()

    assert "below mature_min_depth" in mature["Discard reason"].tolist()
    below = mature[mature["Discard reason"] == "below mature_min_depth"]
    assert (below["Depth (D1)"].astype(float) < 1.00).all()
    assert (below["Written"] == "no").all()
