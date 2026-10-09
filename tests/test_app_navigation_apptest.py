"""The calibration app's pages (app redesign I1) — Streamlit AppTest, public API only.

"Is X in the menu" is asked by its EFFECT, not through AppTest's own page
bookkeeping: switch to the page's file, run, and look at which page actually
rendered. `AppTest.switch_page` itself cannot be trusted for this across the
supported range: up to at least streamlit 1.58 it only checks that the FILE
exists, so it "reaches" an unregistered page too, and st.navigation then
renders the default page (Calibrate) instead. Each page is recognised by what
only it draws: Calibrate `btn_defaults` (its sidebar's "Defaults"), Compare its
title "Compare configurations", Manual labelling `label_default_tolerance`.

Covered here:

* the menu has Calibrate and Compare, and Calibrate is the default page;
* the old Benchmark page is gone (benchmark review, I3): its files are deleted,
  app.py does not name it, and its address renders the default page;
* the Developer section (Manual labelling) is absent without the developer key
  and present with it — by st.secrets or by the CYCLOPHASER_APP_DEV variable —
  and a missing secrets file is not an error;
* the Calibrate sidebar, the dataset choice and the bad-case marks survive a
  trip to Compare and back — with a NEGATIVE control showing the same trip
  loses them when the shield in app.py is skipped, so the test is not vacuous;
* Compare's "Add Current settings" reflects the Calibrate sidebar.

That no test-split label is ever scored is the Validate page's to show
(tests/test_validate_core.py, tests/test_validate_apptest.py); the Compare page
reads no label at all (tests/test_compare_apptest.py).

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
CALIBRATE = "app_pages/calibrate.py"
COMPARE = "app_pages/compare.py"
OLD_BENCHMARK = "app_pages/benchmark.py"   # retired in I3; the file is gone
LABEL = "app_pages/label.py"


def _app(secrets: dict | None = None, data: bool = False) -> AppTest:
    """The app on Calibrate. `data` loads the example track ("Try example
    data"): since I2 nothing is loaded until the user asks, and the main area
    (display mode, grid) is drawn only with data."""
    at = AppTest.from_file(str(APP), default_timeout=300)
    for k, v in (secrets or {}).items():
        at.secrets[k] = v
    at.run()
    if data:
        at.button(key="btn_example").click()
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _go(at: AppTest, page: str) -> AppTest:
    at.switch_page(page).run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _rendered(at: AppTest, page: str) -> str:
    """Switch to `page`, run, and name the page that actually rendered.

    Newer AppTest raises ValueError for a file that is not a registered page
    and stays on the current page; older AppTest lets the switch through and
    st.navigation renders the default page. Asked from Calibrate (the default
    page), both come out as "calibrate" for an unregistered page — never as
    the page asked for."""
    try:
        at.switch_page(page)
    except ValueError:
        pass
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    found = {
        "calibrate": any(b.key == "btn_defaults" for b in at.button),
        "compare": [t.value for t in at.title] == ["Compare configurations"],
        "label": any(n.key == "label_default_tolerance" for n in at.number_input),
    }
    assert sum(found.values()) == 1, found
    return next(k for k, v in found.items() if v)


def _w(at, kind, key):
    for w in getattr(at, kind):
        if w.key == key:
            return w
    raise AssertionError(f"no {kind} with key {key!r}")


# ── the menu ──────────────────────────────────────────────────────────────────

def test_the_menu_has_calibrate_and_compare_and_calibrate_is_the_default():
    at = _app()
    # the default page is Calibrate: its "Defaults" button is on screen
    assert any(b.key == "btn_defaults" for b in at.button)
    assert _rendered(at, COMPARE) == "compare"
    assert _rendered(at, CALIBRATE) == "calibrate"


def test_the_benchmark_page_is_gone(monkeypatch):
    """Benchmark review, I3: the page and its module are deleted, app.py names
    neither, and the old address renders the default page — with and without
    the developer key. Control: from the same state, Compare does render."""
    app_dir = APP.parent
    assert not (app_dir / OLD_BENCHMARK).exists()
    assert not (app_dir / "benchmark_tab.py").exists()
    assert (app_dir / "benchmark_core.py").exists()          # the module stays
    src = APP.read_text()
    assert "benchmark_tab" not in src and "_PAGE_BENCHMARK" not in src
    assert '_pages = {"Calibration": [_PAGE_CALIBRATE, _PAGE_COMPARE]}' in src
    assert '_pages["Developer"] = [_PAGE_LABEL, _PAGE_VALIDATE]' in src
    for dev in (False, True):
        if dev:
            monkeypatch.setenv("CYCLOPHASER_APP_DEV", "1")
        else:
            monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
        at = _app()
        assert _rendered(at, OLD_BENCHMARK) == "calibrate"
        assert _rendered(at, COMPARE) == "compare"           # control
        assert not any("bench_" in (b.key or "") for b in at.button)


def test_the_developer_page_is_absent_without_the_key(monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    at = _app()                       # no secrets file at all: not an error
    assert _rendered(at, LABEL) == "calibrate"       # Calibrate, not Label
    assert _rendered(at, COMPARE) == "compare"       # positive control: switching works


def test_the_developer_page_is_absent_when_the_secret_is_false(monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    at = _app({"developer_mode": False})
    assert _rendered(at, LABEL) == "calibrate"


def test_the_developer_page_is_present_with_the_secret(monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    at = _app({"developer_mode": True})
    assert _rendered(at, LABEL) == "label"
    assert any(sb.label == "Jump to case" for sb in at.main.selectbox)


def test_the_developer_page_is_present_with_the_environment_variable(monkeypatch):
    monkeypatch.setenv("CYCLOPHASER_APP_DEV", "1")
    at = _app()
    assert _rendered(at, LABEL) == "label"


# ── state across pages ────────────────────────────────────────────────────────

# Non-default values, one per kind of Calibrate control: a sidebar slider, a
# sidebar selectbox, a sidebar checkbox, a sidebar radio, the display-mode
# radio, and an Inspector checkbox in the main area (drawn once view_mode is
# Inspector). boundary_padding comes before use_filter: switching the filter off
# disables it. (The dataset choice was a checkbox here until I2; it is now set by
# buttons into plain session state, which page clean-up never touches.)
_EDITS = [("slider", "thr_int_len", None), ("selectbox", "boundary_padding", None),
          ("checkbox", "use_filter", False),
          ("radio", "incipient_plateau_crossing", None),
          ("radio", "view_mode", "Inspector"),
          ("checkbox", "inspector_ribbon", False)]


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
    # a widget that is not drawn (e.g. an Inspector box after view_mode fell
    # back to Grid) is recorded as absent, so a lost state compares unequal
    # instead of raising
    out = {}
    for kind, key, _v in _EDITS:
        try:
            out[key] = _w(at, kind, key).value
        except AssertionError:
            out[key] = "<absent>"
    return out


def test_calibrate_state_survives_a_trip_to_compare_and_back():
    at = _app(data=True)
    before = _edit_calibrate(at)
    _go(at, COMPARE)
    _go(at, CALIBRATE)
    assert _snapshot(at) == before
    # no warning beyond the Advanced notice, which these edits trigger on purpose
    others = [w.value for w in at.warning if "differ from defaults" not in w.value]
    assert not others, others


def test_a_bad_case_mark_survives_a_trip_to_compare_and_back():
    """In Grid, where the marks are drawn. (Switching Grid → Inspector → Grid
    is covered by tests/test_calibrate_i2_apptest.py since I2.) Marking is a
    developer function, so the key is on."""
    at = _app({"developer_mode": True}, data=True)
    mark = next(cb.key for cb in at.checkbox if cb.key and cb.key.startswith("badcase__"))
    at.checkbox(key=mark).check()
    at.run()
    _go(at, COMPARE)
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
        at.button(key="btn_example").click()
        at.run()
        before = _edit_calibrate(at)
        _go(at, COMPARE)
        _go(at, CALIBRATE)
        assert _snapshot(at) != before
    finally:
        shadow.unlink()


def test_add_column_from_the_sidebar_reflects_the_calibrate_sidebar():
    """Compare's "Add Current settings" (the Benchmark's "Add column from
    current sidebar state" until I3). Compare draws its controls only with
    tracks loaded, hence the example track."""
    at = _app(data=True)
    _w(at, "slider", "cutoff_high").set_value(48)
    at.run()
    _go(at, COMPARE)
    _w(at, "button", "cmp_add_current").click()
    at.run()
    col = at.session_state["cmp_columns"][-1]
    assert col["doc"]["filter_params"]["cutoff_high"] == 48
    # and a later change on Calibrate is what the NEXT column gets
    _go(at, CALIBRATE)
    _w(at, "slider", "cutoff_high").set_value(40)
    at.run()
    _go(at, COMPARE)
    _w(at, "button", "cmp_add_current").click()
    at.run()
    col = at.session_state["cmp_columns"][-1]
    assert col["doc"]["filter_params"]["cutoff_high"] == 40
