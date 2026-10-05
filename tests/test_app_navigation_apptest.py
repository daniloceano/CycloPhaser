"""The calibration app's pages (app redesign I1) — Streamlit AppTest, public API only.

`st.navigation` registers the pages; `AppTest.switch_page` reaches a page only
when it is registered, and raises ValueError otherwise, so "is X in the menu"
is asked through that public call rather than through any element internals.

Covered here:

* the menu has Calibrate and Benchmark, and Calibrate is the default page;
* the Developer section (Manual labelling) is absent without the developer key
  and present with it — by st.secrets or by the CYCLOPHASER_APP_DEV variable —
  and a missing secrets file is not an error;
* the Calibrate sidebar, the dataset choice and the bad-case marks survive a
  trip to Benchmark and back — with a NEGATIVE control showing the same trip
  loses them when the shield in app.py is skipped, so the test is not vacuous;
* "Add column from current sidebar state" still reflects the Calibrate sidebar;
* the Benchmark page shows no score or metric against a test-split label.

File uploads cannot be driven through AppTest; their carry-over across pages is
covered in the browser (tests/test_app_pages_browser.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"

pytest.importorskip("streamlit")
pytest.importorskip("yaml")
from streamlit.testing.v1 import AppTest  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))
import benchmark_core as bc  # noqa: E402

CALIBRATE = "app_pages/calibrate.py"
BENCHMARK = "app_pages/benchmark.py"
LABEL = "app_pages/label.py"


def _app(secrets: dict | None = None) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=300)
    for k, v in (secrets or {}).items():
        at.secrets[k] = v
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _go(at: AppTest, page: str) -> AppTest:
    at.switch_page(page).run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _registered(at: AppTest, page: str) -> bool:
    try:
        at.switch_page(page)
    except ValueError:
        return False
    return True


def _w(at, kind, key):
    for w in getattr(at, kind):
        if w.key == key:
            return w
    raise AssertionError(f"no {kind} with key {key!r}")


# ── the menu ──────────────────────────────────────────────────────────────────

def test_the_menu_has_calibrate_and_benchmark_and_calibrate_is_the_default():
    at = _app()
    # the default page is Calibrate: its display-mode radio is on screen
    assert any(r.key == "view_mode" for r in at.radio)
    assert _registered(at, CALIBRATE) and _registered(at, BENCHMARK)
    _go(at, BENCHMARK)
    assert any(b.key == "bench_run" for b in at.button)
    assert not any(r.key == "view_mode" for r in at.radio)


def test_the_developer_page_is_absent_without_the_key(monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    at = _app()                       # no secrets file at all: not an error
    assert _registered(at, BENCHMARK)  # positive control for the call itself
    assert not _registered(at, LABEL)


def test_the_developer_page_is_absent_when_the_secret_is_false(monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    at = _app({"developer_mode": False})
    assert not _registered(at, LABEL)


def test_the_developer_page_is_present_with_the_secret(monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    at = _app({"developer_mode": True})
    assert _registered(at, LABEL)
    _go(at, LABEL)
    assert any(sb.label == "Jump to case" for sb in at.main.selectbox)


def test_the_developer_page_is_present_with_the_environment_variable(monkeypatch):
    monkeypatch.setenv("CYCLOPHASER_APP_DEV", "1")
    at = _app()
    assert _registered(at, LABEL)


# ── state across pages ────────────────────────────────────────────────────────

# Non-default values, one per kind of Calibrate control: a sidebar slider, a
# sidebar selectbox, a sidebar checkbox, a sidebar radio, the display-mode
# radio, and a dataset checkbox in the main area. boundary_padding comes before
# use_filter: switching the filter off disables it.
_EDITS = [("slider", "thr_int_len", None), ("selectbox", "boundary_padding", None),
          ("checkbox", "use_filter", False),
          ("radio", "incipient_plateau_crossing", None),
          ("radio", "view_mode", "Inspector"),
          ("checkbox", "load_synthetic_clean", True)]


def _edit_calibrate(at: AppTest) -> dict:
    for kind, key, value in _EDITS:
        w = _w(at, kind, key)
        if value is None:   # pick any option/value other than the current one
            if kind == "slider":
                value = w.min if w.value != w.min else w.max
            else:
                value = next(o for o in w.options if o != w.value)
        w.set_value(value)
        at.run()
        assert not at.exception, [str(e) for e in at.exception]
    return _snapshot(at)


def _snapshot(at: AppTest) -> dict:
    return {key: _w(at, kind, key).value for kind, key, _v in _EDITS}


def test_calibrate_state_survives_a_trip_to_benchmark_and_back():
    at = _app()
    before = _edit_calibrate(at)
    _go(at, BENCHMARK)
    _go(at, CALIBRATE)
    assert _snapshot(at) == before
    assert not at.warning, [w.value for w in at.warning]


def test_a_bad_case_mark_survives_a_trip_to_benchmark_and_back():
    """In Grid, where the marks are drawn. (Switching Grid → Inspector → Grid
    loses them on develop too — the checkboxes are only drawn in Grid; that is
    pre-existing and outside I1, where the marking moves anyway.)"""
    at = _app()
    mark = next(cb.key for cb in at.checkbox if cb.key and cb.key.startswith("badcase__"))
    at.checkbox(key=mark).check()
    at.run()
    _go(at, BENCHMARK)
    _go(at, CALIBRATE)
    assert at.checkbox(key=mark).value is True
    assert any(m.value.startswith("1 /") for m in at.metric)


def test_the_trip_loses_the_state_without_the_shield(tmp_path):
    """NEGATIVE CONTROL. The same trip, on a copy of app.py whose call to
    `_keep_page_state` is removed, must lose values — otherwise the test above
    would pass whatever app.py did."""
    app_dir = APP.parent
    src = APP.read_text()
    call = ("_keep_page_state(_page.url_path,\n"
            "                 arrived=_PREVIOUS_PAGE is not None and "
            "_PREVIOUS_PAGE != _page.url_path)\n")
    assert src.count(call) == 1
    shadow = app_dir / "_test_app_without_shield.py"
    shadow.write_text(src.replace(call, ""))
    try:
        at = AppTest.from_file(str(shadow), default_timeout=300)
        at.run()
        before = _edit_calibrate(at)
        _go(at, BENCHMARK)
        _go(at, CALIBRATE)
        assert _snapshot(at) != before
    finally:
        shadow.unlink()


def test_add_column_from_the_sidebar_reflects_the_calibrate_sidebar():
    at = _app()
    _w(at, "slider", "cutoff_high").set_value(48)
    at.run()
    _go(at, BENCHMARK)
    _w(at, "button", "bench_add_sidebar").click()
    at.run()
    import yaml
    col = at.session_state["bench_columns"][-1]
    assert yaml.safe_load(col["yaml_text"])["filter_params"]["cutoff_high"] == 48
    # and a later change on Calibrate is what the NEXT column gets
    _go(at, CALIBRATE)
    _w(at, "slider", "cutoff_high").set_value(40)
    at.run()
    _go(at, BENCHMARK)
    _w(at, "button", "bench_add_sidebar").click()
    at.run()
    col = at.session_state["bench_columns"][-1]
    assert yaml.safe_load(col["yaml_text"])["filter_params"]["cutoff_high"] == 40


# ── Benchmark: no score against a test-split label, anywhere ──────────────────

def _test_and_train_ids():
    m = bc.split_membership()
    return (sorted(s for s, v in m.items() if v == "test"),
            sorted(s for s, v in m.items() if v == "train"))


def test_validation_does_not_offer_the_test_split():
    test_ids, _train = _test_and_train_ids()
    at = _go(_app(), BENCHMARK)
    opts = {o.split(" ")[0] for o in _w(at, "multiselect", "bench_ids_widget").options}
    assert opts and not set(test_ids) & opts
    assert not any(b.key == "bench_pick_test" for b in at.button)


def test_exploration_runs_a_test_series_but_never_scores_it():
    """A test series selected in Exploration is treated as unlabelled: no test
    block, no manual-label reference metric, no per-cell score note."""
    test_ids, train_ids = _test_and_train_ids()
    t, r = test_ids[0], train_ids[0]
    at = _go(_app(), BENCHMARK)
    _w(at, "radio", "bench_mode").set_value("Exploration")
    at.run()
    ms = _w(at, "multiselect", "bench_ids_widget")
    ms.set_value([o for o in ms.options if o.split(" ")[0] in (t, r)])
    at.run()
    _w(at, "selectbox", "bench_pick_config").set_value("cyclophaser_params-track.yaml")
    at.run()
    _w(at, "button", "bench_add_config").click()
    at.run()
    _w(at, "selectbox", "bench_reference").set_value("Manual label")
    at.run()
    _w(at, "button", "bench_run").click()
    at.run()
    _w(at, "checkbox", "bench_score_labelled_subset").set_value(True)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]

    assert set(at.session_state["_bench_run_ids"]) == {t, r}
    assert not any(e.label.startswith("Test split") for e in at.expander)
    compared = [df.value for df in at.dataframe
                if "Cyclones compared" in list(df.value.index)]
    assert compared and all(int(v) == 1 for v in compared[0].iloc[0]), compared
    notes = [c.value for c in at.caption]
    assert "unlabelled — not scored" in notes
    # POSITIVE CONTROL: with the test label NOT withheld, the same run would
    # have been compared on both series — the guard above is what stops it.
    full = bc.labels_for_display()
    assert t in full
    ref = {sid: {"runs": bc.label_runs_for(full[sid])} for sid in (t, r)}
    assert bc.reference_metrics(at.session_state["_bench_runs"][0], ref,
                                [t, r])["n_compared"] == 2
