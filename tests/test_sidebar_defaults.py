"""The sidebar opens with the PACKAGE defaults — one source, the signature.

Item 31, stage 2c (Danilo, 2026-09-28): the app's own default table is gone;
`app._DEFAULTS` derives every parameter's start-up value from
`inspect.signature(process_vorticity / get_periods)`, and "Reset to defaults"
returns there. Pinned here, against the REAL app (AppTest, public API only):

* anti-recurrence — every start-up widget value equals the declared rule
  applied to the signature, key by key. The expectation is re-derived HERE from
  the signature, not read from the app's code, so an app that drifted back to a
  table of its own fails;
* the published live config (what the Grid and a "Current settings" column run)
  equals the signature defaults, key by key;
* Reset returns to them after edits;
* app <-> package: an UNTOUCHED "Current settings" column gives the same phase
  map as `determine_periods(series)` with no arguments, on 3 TRAIN series (2
  real of the split, 1 of the swell batch) — with its positive control: one
  non-default sidebar value (cutoff_high=48) makes at least one of the 3 differ.
  The column is run on the Validate page (developer key), the page that offers
  the swell batch since the Benchmark page was retired (benchmark review, I3).
"""

from __future__ import annotations

import inspect
import sys
import warnings
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))
import benchmark_core as bc  # noqa: E402
from cyclophaser.determine_periods import (  # noqa: E402
    determine_periods, get_periods, process_vorticity,
)

NON_PARAMS = {"zeta_df", "vorticity", "plot", "plot_steps", "export_dict"}
# Conditional widgets hidden at start-up under the package defaults: the
# geometric-only threshold under incipient_method='plateau', the Savitzky-Golay
# window values under smoothing 'off', the absolute prominence in relative mode.
HIDDEN_AT_START = {"thr_inc_len", "sm_val", "sm2_val", "extrema_prominence_val"}


def _sig() -> dict:
    out = {}
    for fn in (process_vorticity, get_periods):
        for k, p in inspect.signature(fn).parameters.items():
            if k not in NON_PARAMS and p.default is not inspect.Parameter.empty:
                out[k] = p.default
    return out


def _expected_widgets(sig: dict) -> dict:
    """The declared rule (DESIGN §12.1), from the signature alone."""
    ints = {"cutoff_low", "cutoff_high", "replace_endpoints_with_lowpass",
            "savgol_polynomial", "incipient_plateau_k", "incipient_smooth_window",
            "incipient_smooth_polyorder"}
    widget = {"cutoff_low": "cutoff_low", "cutoff_high": "cutoff_high",
              "replace_endpoints_with_lowpass": "replace_endpoints",
              "savgol_polynomial": "savgol_poly", "boundary_padding": "boundary_padding",
              "threshold_intensification_length": "thr_int_len",
              "threshold_intensification_gap": "thr_int_gap",
              "intensification_min_depth": "intensification_min_depth",
              "threshold_mature_distance": "thr_mat_dist",
              "threshold_mature_length": "thr_mat_len",
              "threshold_decay_length": "thr_dec_len", "threshold_decay_gap": "thr_dec_gap",
              "threshold_incipient_length": "thr_inc_len", "length_scale": "length_scale",
              "mature_method": "mature_method",
              "mature_amplitude_fraction": "mature_amplitude_fraction",
              "mature_min_depth": "mature_min_depth", "reclassify_index0": "reclassify_index0",
              "incipient_method": "incipient_method",
              "incipient_plateau_tau": "incipient_plateau_tau",
              "incipient_plateau_signal": "incipient_plateau_signal",
              "incipient_plateau_crossing": "incipient_plateau_crossing",
              "incipient_plateau_k": "incipient_plateau_k",
              "incipient_smooth_window": "incipient_smooth_window",
              "incipient_smooth_polyorder": "incipient_smooth_polyorder",
              "incipient_plateau_spare_intensification":
                  "incipient_plateau_spare_intensification"}
    out = {w: (int(sig[p]) if p in ints else sig[p]) for p, w in widget.items()}
    out["use_filter"] = sig["use_filter"] in ("auto", True)
    for mode_k, p in (("sm_mode", "use_smoothing"), ("sm2_mode", "use_smoothing_twice")):
        out[mode_k] = {"auto": "auto", False: "off"}.get(sig[p], "manual")
    pr, pa = sig["prominence_relative"], sig["prominence"]
    out["extrema_prominence_enabled"] = pr is not None or pa is not None
    out["extrema_prominence_mode"] = ("relative" if pr is not None
                                      else "absolute" if pa is not None else "relative")
    if pr is not None:
        out["extrema_prominence_rel_val"] = pr
    if pa is not None:
        out["extrema_prominence_val"] = pa
    out["decay_tail_enabled"] = sig["decay_tail_amplitude_fraction"] is not None
    if sig["decay_tail_amplitude_fraction"] is not None:
        out["decay_tail_fraction_val"] = sig["decay_tail_amplitude_fraction"]
    return out


def _app() -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _widget(at, kind, key):
    for w in getattr(at, kind):
        if w.key == key:
            return w
    raise AssertionError(f"no {kind} with key {key!r}")


# ── anti-recurrence ─────────────────────────────────────────────────────────────

def test_sidebar_start_up_values_are_the_signature_defaults():
    at = _app()
    want = _expected_widgets(_sig())
    rendered = {k for k in want if k in at.session_state}
    assert set(want) - rendered <= HIDDEN_AT_START, (
        f"widgets missing at start-up beyond the declared hidden ones: "
        f"{sorted(set(want) - rendered - HIDDEN_AT_START)}")
    wrong = {k: (at.session_state[k], want[k]) for k in rendered
             if at.session_state[k] != want[k]}
    assert wrong == {}, f"(sidebar, signature-derived) differ: {wrong}"


def test_the_published_live_config_is_the_signature_defaults_key_by_key():
    """What the Grid and a "Current settings" column actually run."""
    live = _app().session_state["_bench_live_config"]
    sig = _sig()
    pv = set(inspect.signature(process_vorticity).parameters) - NON_PARAMS
    gp = set(inspect.signature(get_periods).parameters) - NON_PARAMS
    assert set(live["filter_params"]) == pv
    assert set(live["phase_params"]) == gp
    for k, v in {**live["filter_params"], **live["phase_params"]}.items():
        if k == "use_filter":
            assert v is True and sig[k] == "auto", (k, v, sig[k])   # True ≡ 'auto'
        else:
            assert v == sig[k] and (v is None) == (sig[k] is None), (k, v, sig[k])


def test_reset_returns_to_the_signature_defaults():
    at = _app()
    _widget(at, "slider", "cutoff_high").set_value(48)
    _widget(at, "radio", "incipient_method").set_value("geometric")
    _widget(at, "checkbox", "decay_tail_enabled").set_value(False)
    at.run()
    assert at.session_state["cutoff_high"] == 48          # the edits took
    # "Reset to defaults" became the "Defaults" button of step 2 (I2)
    reset = next(b for b in at.button if b.key == "btn_defaults")
    reset.click()
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    want = _expected_widgets(_sig())
    for k in ("cutoff_high", "incipient_method", "decay_tail_enabled"):
        assert at.session_state[k] == want[k], (k, at.session_state[k], want[k])


# ── app <-> package: the sidebar column IS determine_periods() ──────────────────

def _three_train_ids() -> list[str]:
    sp = bc.read_split()
    real_train = sorted(s for s in sp["train"] if not s.startswith("s"))[:2]
    batch_train = sorted(s for s, m in bc.batch_membership().items() if m == "train")[:1]
    return real_train + batch_train


def _sidebar_column_runs(set_cutoff_high=None) -> dict:
    """The "Current settings" column on the Validate page (developer key), run
    on the 3 ids: {id: [[phase, start, end], ...]}."""
    import os
    old = os.environ.get("CYCLOPHASER_APP_DEV")
    os.environ["CYCLOPHASER_APP_DEV"] = "1"
    try:
        at = _app()
        if set_cutoff_high is not None:     # the sidebar is the Calibrate page's
            _widget(at, "slider", "cutoff_high").set_value(set_cutoff_high)
            at.run()
        at.switch_page("app_pages/validate.py").run()
        _widget(at, "checkbox", "val_include_batch").set_value(True)
        at.run()
        ids = _three_train_ids()
        _widget(at, "multiselect", "val_tracks").set_value(ids)
        at.run()
        _widget(at, "button", "val_add_current").click()
        at.run()
        _widget(at, "button", "val_run").click()
        at.run()
        assert not at.exception, [str(e) for e in at.exception]
    finally:
        if old is None:
            os.environ.pop("CYCLOPHASER_APP_DEV", None)
        else:
            os.environ["CYCLOPHASER_APP_DEV"] = old
    res = at.session_state["_val_results"]
    (col,) = res["columns"]
    assert res["ids"] == ids
    cells = res["cells"][col["cid"]]
    return {sid: [list(r) for r in cells[sid]["runs"]] for sid in ids}


def _package_runs() -> dict:
    series, _ = bc.load_all_series()
    batch, _ = bc.load_batch(series)
    out = {}
    for sid in _three_train_ids():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = determine_periods({**series, **batch}[sid])
        out[sid] = [[p, a, b] for p, a, b in bc.phase_runs_from_periods(res["periods"])]
    return out


def test_an_untouched_sidebar_column_equals_determine_periods_without_arguments():
    ids = _three_train_ids()
    assert len(ids) == 3 and ids[2] in bc.batch_membership()     # one swell-batch series
    assert _sidebar_column_runs() == _package_runs()


def test_the_equivalence_above_can_fail():
    """POSITIVE CONTROL: one non-default sidebar value (cutoff_high=48) must
    make the sidebar column differ from determine_periods() on at least one of
    the 3 — otherwise the equality above could be vacuous."""
    got, want = _sidebar_column_runs(set_cutoff_high=48), _package_runs()
    assert any(got[s] != want[s] for s in want)
