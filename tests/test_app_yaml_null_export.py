"""The calibration app's YAML export writes switched-off parameters as an explicit
null, and the file reproduces the app's detection (Passo 4, Fase B).

Three phase parameters are switched on and off with a check box in the app:
prominence, prominence_relative and decay_tail_amplitude_fraction. OFF is None.
The export used to OMIT a None value; passed to determine_periods, an omitted
key takes the package default, which for prominence_relative and
decay_tail_amplitude_fraction is not OFF, so the file silently described another
configuration. These tests run the app's REAL `_build_yaml` and
`_load_yaml_config` (executed from app.py's source, like
tests/test_config_defaults.py does) and check:

* every None is written as null;
* the exported file, passed to determine_periods, gives the same detection as
  the app's own call — and (positive control) dropping the nulls would not;
* importing the file back switches the three checks OFF, with no conversion
  error.
"""
import datetime as _dt
import inspect
import types
import warnings
from pathlib import Path

import pandas as pd
import pytest
import yaml

from cyclophaser import determine_periods

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PY = REPO_ROOT / "tools" / "calibration_app" / "app.py"
TRACK = REPO_ROOT / "tests" / "calibration_data" / "20160735.csv"   # train split
OFF_KEYS = ("prominence", "prominence_relative", "decay_tail_amplitude_fraction")

# _load_yaml_config imports research/labels/config_defaults, as in the app
import sys  # noqa: E402
if str(REPO_ROOT / "research" / "labels") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))


def _signature_defaults(fn):
    return {k: v.default for k, v in inspect.signature(fn).parameters.items()
            if v.default is not inspect.Parameter.empty}


def _app_namespace():
    """app.py from `_DEFAULTS` to the end of `_load_yaml_config` (constants, the
    parsers, the YAML maps, the loader), plus `_build_yaml`, with a stub `st`."""
    src = APP_PY.read_text()
    start = src.index("_DEFAULTS: dict = {")
    fn = src.index("def _load_yaml_config(")
    end = src.index("\ndef ", fn + 1)
    st = types.SimpleNamespace(session_state={})
    ns = {"st": st, "yaml": yaml, "Path": Path, "datetime": _dt.datetime,
          "timezone": _dt.timezone, "__name__": "_yaml_null_export"}
    exec(compile(src[start:end], "app.py", "exec"), ns)
    b0 = src.index("def _build_yaml(")
    b1 = src.index("\n    return yaml.dump(", b0)
    b1 = src.index("\n", b1 + 1)
    exec(compile(src[b0:b1], "app.py", "exec"), ns)
    return ns, st.session_state


def _export_with_checks_off():
    """The app's state with the three checks OFF and everything else at the
    package defaults, exported by the real _build_yaml."""
    import cyclophaser.determine_periods  # noqa: F401
    dp = sys.modules["cyclophaser.determine_periods"]
    ns, state = _app_namespace()
    fp = _signature_defaults(dp.process_vorticity)
    phase = {k: v for k, v in _signature_defaults(dp.get_periods).items()
             if k not in ("plot", "plot_steps", "export_dict")}
    phase.update({k: None for k in OFF_KEYS})
    ns.update(_PHASE_PARAMS=phase, _CP_VERSION="test", _compute_evaluation=lambda names: {},
              use_filter=fp["use_filter"], cutoff_low=fp["cutoff_low"], cutoff_high=fp["cutoff_high"],
              replace_endpoints=fp["replace_endpoints_with_lowpass"], use_smoothing=fp["use_smoothing"],
              use_smoothing_twice=fp["use_smoothing_twice"], savgol_poly=fp["savgol_polynomial"],
              boundary_padding=fp["boundary_padding"])
    text = ns["_build_yaml"](["track"])
    return ns, state, text, fp, phase


def _series():
    return pd.read_csv(TRACK, sep=";", parse_dates=[0], index_col=0)["min_max_zeta_850"]


def test_switched_off_parameters_are_written_as_null():
    _ns, _state, text, _fp, _phase = _export_with_checks_off()
    doc = yaml.safe_load(text)
    for k in OFF_KEYS:
        assert k in doc["phase_params"], f"{k} omitted from the export"
        assert doc["phase_params"][k] is None, f"{k} exported as {doc['phase_params'][k]!r}"


def test_the_exported_file_reproduces_the_apps_detection():
    _ns, _state, text, fp, phase = _export_with_checks_off()
    doc = yaml.safe_load(text)
    s = _series()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        app_call = determine_periods(s, **fp, **phase)["periods"]
        from_file = determine_periods(s, **doc["filter_params"], **doc["phase_params"])["periods"]
        dropped = {k: v for k, v in doc["phase_params"].items() if k not in OFF_KEYS}
        old_export = determine_periods(s, **doc["filter_params"], **dropped)["periods"]
    assert from_file.equals(app_call)
    # positive control: on this track the omission the old export made changes the result
    assert not old_export.equals(app_call)


@pytest.mark.parametrize("session_before", [True, False])
def test_importing_the_file_switches_the_checks_off(session_before):
    ns, state, text, _fp, _phase = _export_with_checks_off()
    state["extrema_prominence_enabled"] = session_before
    state["decay_tail_enabled"] = session_before
    res = ns["_load_yaml_config"](text.encode())
    assert res["error"] is None
    assert not [i for i in res["ignored"] if "conversion error" in i], res["ignored"]
    assert state["extrema_prominence_enabled"] is False
    assert state["decay_tail_enabled"] is False
