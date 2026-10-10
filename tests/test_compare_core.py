"""compare_core — the label-free logic behind the Compare page (benchmark review, I1).

Gated on streamlit like every other test of the calibration app: the CI recipe
installs only the wheel, pytest and PyYAML, and app tests stay out of it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "tools" / "calibration_app"
SAMPLE_DIR = APP_DIR / "sample_tracks"

pytest.importorskip("streamlit")
pytest.importorskip("yaml")
sys.path.insert(0, str(APP_DIR))
import compare_core as cc  # noqa: E402
import config_text  # noqa: E402


def _live_like() -> dict:
    """A complete configuration in the shape the Calibrate sidebar publishes."""
    pv, gp = cc.bc.current_defaults()["filter_params"], cc.bc.current_defaults()["phase_params"]
    fp = {k: v for k, v in pv.items() if k in cc.bc.PV_KEYS}
    fp["use_filter"] = True
    return {"filter_params": fp, "phase_params": dict(gp)}


def _cells(runs_by_id: dict) -> dict:
    return {sid: ({"error": "boom", "runs": None, "z": None} if runs is None else
                  {"error": None, "runs": runs, "z": None})
            for sid, runs in runs_by_id.items()}


A = [("incipient", 0, 4), ("intensification", 5, 9), ("mature", 10, 14)]


def test_relative_against_itself_has_no_change():
    col = _cells({"t1": A, "t2": A})
    m = cc.relative(col, col, ["t1", "t2"])
    assert m["n_compared"] == 2
    assert m["n_sequence_changed"] == 0
    assert m["shift_max"] == 0 and m["shift_median"] == 0.0
    assert m["appeared"] == {} and m["disappeared"] == {}
    # the column's own incipient count is NOT part of the relative measures
    assert "n_refused_incipient" not in m


def test_relative_counts_a_sequence_change_and_a_boundary_shift():
    shifted = [("incipient", 0, 6), ("intensification", 7, 9), ("mature", 10, 14)]
    no_inc = [("intensification", 0, 9), ("mature", 10, 14)]
    ref = _cells({"t1": A, "t2": A, "t3": A})
    col = _cells({"t1": shifted, "t2": no_inc, "t3": None})
    m = cc.relative(col, ref, ["t1", "t2", "t3"])
    assert m["n_compared"] == 2                 # t3 failed in the column
    assert m["n_sequence_changed"] == 1         # t2
    assert m["disappeared"] == {"incipient": 1}
    # t1 only (same sequence): boundaries at 5→7 and 10→10
    assert m["n_boundaries_compared"] == 2 and m["shift_max"] == 2
    assert m["shift_median"] == 1.0


def test_incipient_absent_is_the_column_own_count():
    col = _cells({"t1": A, "t2": [("intensification", 0, 9)], "t3": None})
    assert cc.incipient_absent(col, ["t1", "t2", "t3"]) == (1, 2)


def test_config_differences_tolerate_float_noise():
    a, b, c = _live_like(), _live_like(), _live_like()
    a["phase_params"]["mature_amplitude_fraction"] = 0.3
    b["phase_params"]["mature_amplitude_fraction"] = 0.1 + 0.2   # 0.30000000000000004
    c["phase_params"]["mature_amplitude_fraction"] = 0.31
    assert cc.config_differences(a, b) == {}
    diff = cc.config_differences(c, a)
    assert list(diff) == ["phase_params.mature_amplitude_fraction"]
    assert diff["phase_params.mature_amplitude_fraction"] == (0.31, 0.3)


def test_the_series_key_is_the_content_not_the_name():
    files = sorted(SAMPLE_DIR.glob("*.csv"))
    if len(files) < 2:
        pytest.skip("sample tracks not present")
    data = files[0].read_bytes()
    s1, s1b = cc.read_series(data), cc.read_series(bytes(data))
    assert cc.series_key(s1) == cc.series_key(s1b)
    other = cc.read_series(files[1].read_bytes())
    assert cc.series_key(other) != cc.series_key(s1)
    changed = s1.copy()
    changed.iloc[3] += 1e-9
    assert cc.series_key(changed) != cc.series_key(s1)
    moved = s1.copy()
    moved.index = moved.index + __import__("pandas").Timedelta("1h")
    assert cc.series_key(moved) != cc.series_key(s1)


def test_the_config_key_is_the_effective_configuration():
    base = _live_like()
    key = cc.config_key(base)
    auto = _live_like()
    auto["filter_params"]["use_filter"] = "auto"           # what True becomes
    assert cc.config_key(auto) == key
    reordered = {"phase_params": dict(reversed(list(base["phase_params"].items()))),
                 "filter_params": dict(reversed(list(base["filter_params"].items()))),
                 "metadata": {"anything": 1}}
    assert cc.config_key(reordered) == key
    other = _live_like()
    other["filter_params"]["cutoff_high"] = base["filter_params"]["cutoff_high"] + 6
    assert cc.config_key(other) != key


def test_audit_lists_filled_and_ignored_keys():
    doc = _live_like()
    del doc["filter_params"]["boundary_padding"]
    doc["phase_params"]["distance"] = 3
    a = cc.audit(doc)
    assert "phase_params.distance" in a["ignored"]
    filled = dict(a["filled"])
    assert "filter_params.boundary_padding" in filled
    # the same rule the Calibrate import uses (config_defaults.fill_missing)
    from config_defaults import fill_missing
    assert a["filled"] == fill_missing(cc.parameter_sections(doc))[1]
    assert cc.audit(_live_like()) == {"ignored": [], "filled": []}


def test_the_filled_keys_sentence_is_one_function_for_both_pages():
    app = (APP_DIR / "app.py").read_text()
    tab = (APP_DIR / "compare_tab.py").read_text()
    assert 'config_text.filled_keys_sentence(_r["filled"])' in app
    assert 'config_text.ignored_keys_sentence(_r["ignored"])' in app
    assert "config_text.filled_keys_sentence(" in tab
    assert "config_text.ignored_keys_sentence(" in tab
    # neither page types its own copy of the sentence
    for src in (app, tab):
        assert "were filled with the" not in src
    # round 2: the sentence names the package default each listed key differs from
    s = config_text.filled_keys_sentence([("filter_params.boundary_padding", "zero")])
    assert s == ("1 key(s) absent from this file were filled with the earlier "
                 "defaults older configuration files were written against, which "
                 "differ from the package's defaults: "
                 "filter_params.boundary_padding='zero' (package default 'reflect')")
    assert "current default" not in s
    assert config_text.filled_keys_sentence([]) == ""
    assert config_text.ignored_keys_sentence(["a.b"]) == "Ignored keys: a.b"


def test_the_filled_keys_sentence_lists_only_keys_that_differ_from_the_package():
    """Round 2, item 3. `fill_missing` and its list do not change; the sentence
    leaves out what the package would use anyway."""
    import yaml
    from config_defaults import fill_missing
    track = REPO_ROOT / "research" / "labels" / "configs" / "cyclophaser_params-track.yaml"
    _doc, filled = fill_missing(yaml.safe_load(track.read_text()))
    assert filled == [("phase_params.prominence", None)]       # the rule is unchanged
    assert config_text.filled_keys_sentence(filled) == ""        # package default is None too
    # still listed: prominence_relative absent → None, package default 0.3
    s = config_text.filled_keys_sentence([("phase_params.prominence_relative", None),
                                          ("phase_params.prominence", None)])
    assert s.startswith("1 key(s) absent from this file")
    assert "phase_params.prominence_relative=None (package default 0.3)" in s
    assert "phase_params.prominence=" not in s
    # use_filter compared after the app's translation, floats with the tolerance
    assert config_text.filled_keys_that_matter([("filter_params.use_filter", True)]) == []
    d = cc.bc.current_defaults()["phase_params"]["mature_amplitude_fraction"]
    assert config_text.filled_keys_that_matter(
        [("phase_params.mature_amplitude_fraction", d * (1 + 1e-15))]) == []
    assert config_text.filled_keys_that_matter(
        [("phase_params.mature_amplitude_fraction", d + 0.01)]) != []
    # a key the package does not read is not applied, so not listed
    assert config_text.filled_keys_that_matter([("phase_params.distance", 3)]) == []
