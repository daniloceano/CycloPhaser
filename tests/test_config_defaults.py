"""Item 31, decision (a): a config key that is absent is filled with the FROZEN
cyclophaser 2.0.0 default, and every filled key is listed.

`research/labels/config_defaults.py` holds the rule; the evaluator, the Benchmark
(`benchmark_core`) and the app's YAML import all go through it. What is pinned:

* the table IS the stage-0 parameter table's "default" column (never hand-typed),
  and covers exactly the detection parameters of the current signature;
* the fill touches absent keys only, lists them, and never mutates its input;
* the source of a filled value is the TABLE, not the live signature — with a
  positive control, since in stage 2a the two still coincide;
* evaluator and Benchmark resolve a config to the same arguments;
* params-15 lacks exactly one key (`prominence`), and the app imports it with
  that one key listed and prominence filtering left as the file describes.
"""

from __future__ import annotations

import datetime as _dt
import inspect
import json
import sys
import types
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
LABELS = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS))
sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))

import config_defaults as cd  # noqa: E402
from cyclophaser.determine_periods import get_periods, process_vorticity  # noqa: E402

P15 = LABELS / "configs" / "cyclophaser_params-15.yaml"
PARAM_TABLE = LABELS / "diagnostics" / "item31" / "param_table.json"
NON_DETECTION = {"zeta_df", "vorticity", "plot", "plot_steps", "export_dict"}


def test_the_table_is_the_stage0_default_column_value_and_type():
    rows = json.loads(PARAM_TABLE.read_text())["rows"]
    table = cd.defaults_2_0_0()
    want = {"filter_params": {}, "phase_params": {}}
    for r in rows:
        sec = {"filtragem": "filter_params", "fase": "phase_params"}.get(r["group"])
        if sec:
            want[sec][r["param"]] = r["default"]
    for sec in cd.SECTIONS:
        assert table[sec] == want[sec]
        for k, v in want[sec].items():
            assert type(table[sec][k]) is type(v), (sec, k)


def test_the_table_covers_exactly_the_signatures_detection_parameters():
    """Anti-drift: a parameter added to the package with no 2.0.0 value would be
    passed through unfilled — this fails first."""
    table = cd.defaults_2_0_0()
    pv = set(inspect.signature(process_vorticity).parameters) - NON_DETECTION
    gp = set(inspect.signature(get_periods).parameters) - NON_DETECTION
    assert set(table["filter_params"]) == pv
    assert set(table["phase_params"]) == gp


def test_fill_touches_absent_keys_only_and_lists_them():
    doc = {"filter_params": {"cutoff_high": 18},
           "phase_params": {"prominence_relative": None, "mature_method": "amplitude"},
           "metadata": {"x": 1}}
    before = json.dumps(doc, sort_keys=True)
    out, filled = cd.fill_missing(doc)
    assert json.dumps(doc, sort_keys=True) == before, "input was mutated"
    assert out["filter_params"]["cutoff_high"] == 18
    assert out["phase_params"]["prominence_relative"] is None     # explicit None kept
    assert out["phase_params"]["mature_method"] == "amplitude"
    assert out["metadata"] == {"x": 1}
    keys = [k for k, _ in filled]
    assert "filter_params.cutoff_high" not in keys
    assert "phase_params.prominence_relative" not in keys
    assert "phase_params.mature_method" not in keys
    table = cd.defaults_2_0_0()
    assert len(keys) == (len(table["filter_params"]) - 1) + (len(table["phase_params"]) - 2)
    for k, v in filled:
        sec, key = k.split(".", 1)
        assert out[sec][key] == v == table[sec][key]


def test_a_filled_value_comes_from_the_table_not_the_signature(tmp_path, monkeypatch):
    """POSITIVE CONTROL: in stage 2a the table and the signature coincide, so a
    fill that secretly read the signature would pass every test above. Point the
    module at a table with a sentinel value and require the sentinel."""
    doc = json.loads(cd.DEFAULTS_PATH.read_text())
    doc["phase_params"]["threshold_mature_length"] = 0.987654
    fake = tmp_path / "defaults_2.0.0.json"
    fake.write_text(json.dumps(doc))
    monkeypatch.setattr(cd, "DEFAULTS_PATH", fake)
    cd._table.cache_clear()
    try:
        out, filled = cd.fill_missing({"filter_params": {}, "phase_params": {}})
        assert out["phase_params"]["threshold_mature_length"] == 0.987654
        assert ("phase_params.threshold_mature_length", 0.987654) in filled
    finally:
        cd._table.cache_clear()


def test_params15_lacks_exactly_prominence():
    _out, filled = cd.fill_missing(yaml.safe_load(P15.read_text()))
    assert filled == [("phase_params.prominence", None)]


def test_evaluator_and_benchmark_resolve_a_config_identically(capsys):
    import benchmark_core as bc
    import evaluate_against_labels as ev
    trimmed = yaml.safe_load(P15.read_text())
    del trimmed["phase_params"]["mature_min_depth"]
    del trimmed["filter_params"]["boundary_padding"]
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
        yaml.safe_dump(trimmed, fh)
        path = Path(fh.name)
    try:
        pv_e, gp_e = ev.load_config(path)
        err = capsys.readouterr().err
    finally:
        path.unlink()
    pv_b, gp_b = bc.split_config(trimmed)
    assert (pv_e, gp_e) == (pv_b, gp_b)
    assert gp_e["mature_min_depth"] == 0.0 and pv_e["boundary_padding"] == "reflect"
    assert "phase_params.mature_min_depth=0.0" in err
    assert "filter_params.boundary_padding='reflect'" in err
    audit = bc.signature_audit(trimmed)
    assert audit["defaulted"]["phase_params.mature_min_depth"] == 0.0
    assert audit["defaulted"]["filter_params.boundary_padding"] == "reflect"


def _app_loader():
    src = (REPO_ROOT / "tools" / "calibration_app" / "app.py").read_text()
    start = src.index("_DEFAULTS: dict = {")
    fn = src.index("def _load_yaml_config(")
    end = src.index("\ndef ", fn + 1)
    st = types.SimpleNamespace(session_state={})
    ns = {"st": st, "yaml": yaml, "Path": Path, "datetime": _dt.datetime,
          "timezone": _dt.timezone, "__name__": "_config_defaults_loader"}
    exec(compile(src[start:end], "app.py", "exec"), ns)
    return ns["_load_yaml_config"], st.session_state


def test_the_app_import_lists_the_filled_key_and_keeps_the_files_meaning():
    load, state = _app_loader()
    res = load(P15.read_bytes())
    assert res["error"] is None
    assert res["filled"] == [("phase_params.prominence", None)]
    assert res["missing"] == ["phase_params.prominence"]
    # params-15 filters by RELATIVE prominence 0.3; the filled None for the
    # absolute threshold must not switch that off or write a value widget.
    assert state["extrema_prominence_enabled"] is True
    assert state["extrema_prominence_mode"] == "relative"
    assert "extrema_prominence_val" not in state


def test_the_app_import_fills_a_trimmed_file_with_2_0_0_values():
    load, state = _app_loader()
    state["mature_min_depth"] = 0.8                 # the session had the floor ON
    doc = yaml.safe_load(P15.read_text())
    del doc["phase_params"]["mature_min_depth"]
    res = load(yaml.safe_dump(doc).encode())
    assert res["error"] is None
    assert ("phase_params.mature_min_depth", 0.0) in res["filled"]
    assert state["mature_min_depth"] == 0.0, "absent key left the session's value in place"
