"""Calibrate page after the app redesign's I2 — Streamlit AppTest, public API only.

The guided sidebar (1 · Data, 2 · Starting configuration, 3 · Filtering,
Advanced, 4 · Save results), the developer-only functions, the empty start, the
bad-case mark across display modes and pages, the displayed version, and what
Save results packs. The browser-side checks (the download itself, the custom
format dialog driven by a person) are in tests/test_app_pages_browser.py.
"""

from __future__ import annotations

import io
import sys
import zipfile
from importlib import metadata
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"
CONFIG = REPO_ROOT / "research" / "labels" / "configs" / "cyclophaser_params-track.yaml"

pytest.importorskip("streamlit")
yaml = pytest.importorskip("yaml")
from streamlit.testing.v1 import AppTest  # noqa: E402

STEPS = ["1 · Data", "2 · Starting configuration", "3 · Filtering", "Advanced",
         "4 · Save results"]


def _app(dev: bool = False, data: bool = False) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=300)
    if dev:
        at.secrets["developer_mode"] = True
    at.run()
    if data:
        at.button(key="btn_example").click()
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _run(at) -> AppTest:
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _notice(at) -> str:
    texts = [w.value for w in at.sidebar.warning] + [c.value for c in at.sidebar.caption]
    hits = [t for t in texts if "differ" in t and "from defaults" in t]
    assert len(hits) == 1, texts
    return hits[0]


def _package(at, csv: bool = True, png: bool = False) -> zipfile.ZipFile:
    """Save results → set the options → Prepare → the ZIP that would download."""
    at.button(key="btn_save_results").click()
    _run(at)
    at.checkbox(key="save_include_csv").set_value(csv)
    at.checkbox(key="save_include_png").set_value(png)
    _run(at)
    at.button(key="save_prepare").click()
    _run(at)
    # The download button itself: AppTest of streamlit 1.56 does not expose
    # download buttons with their key, so its presence is checked only where it
    # is exposed; the real download is tested in Chromium on both versions
    # (tests/test_app_pages_browser.py). The bytes it serves are the prepared
    # package, read here.
    keyed = [b for b in at.get("download_button") if getattr(b, "key", None)]
    if keyed:
        assert any(b.key == "save_download" for b in keyed)
    return zipfile.ZipFile(io.BytesIO(at.session_state["_save_package"]["bytes"]))


# ── layout ────────────────────────────────────────────────────────────────────

def test_the_sidebar_steps_come_in_order():
    at = _app()
    assert [h.value for h in at.sidebar.subheader] == STEPS


def test_no_expander_inside_an_expander_in_the_sidebar():
    at = _app()
    # `.expander` on a block lists every expander in its subtree, the block
    # itself included: an expander holding no other one yields exactly one.
    groups = at.sidebar.expander
    assert len(groups) == 8, [e.label for e in groups]   # positive control
    for exp in groups:
        assert len(exp.expander) == 1, f"'{exp.label}' holds an expander"


def test_only_the_filtering_basics_are_outside_the_advanced_groups():
    at = _app()
    inside = {w.key for exp in at.sidebar.expander
              for kind in ("slider", "checkbox", "selectbox", "radio", "number_input")
              for w in getattr(exp, kind)}
    for key in ("use_filter", "cutoff_low", "cutoff_high"):
        assert key not in inside
    for key in ("boundary_padding", "replace_endpoints", "sm_mode", "savgol_poly",
                "thr_int_len", "mature_method", "incipient_method"):
        assert key in inside, key


# ── the Advanced notice ───────────────────────────────────────────────────────

def test_the_notice_counts_an_advanced_parameter_changed_by_hand():
    at = _app()
    assert _notice(at).startswith("0 advanced parameters")
    at.slider(key="thr_int_gap").set_value(0.2)
    _run(at)
    assert _notice(at).startswith("1 advanced parameter differs")
    # a BASIC filtering control is not counted
    at.slider(key="cutoff_high").set_value(48)
    _run(at)
    assert _notice(at).startswith("1 advanced parameter differs")


def test_the_notice_and_the_active_line_follow_an_imported_yaml():
    at = _app()
    assert any("Active: **Defaults**" in m.value for m in at.sidebar.markdown)
    at.file_uploader(key="yaml_import").set_value(
        (CONFIG.name, CONFIG.read_bytes(), "text/yaml"))
    _run(at)
    _run(at)
    assert not _notice(at).startswith("0 "), _notice(at)   # edge padding != reflect
    assert any(f"Active: **{CONFIG.name}**" in m.value for m in at.sidebar.markdown)
    at.slider(key="thr_dec_gap").set_value(0.25)
    _run(at)
    assert any("edited" in m.value for m in at.sidebar.markdown
               if m.value.startswith("Active:"))


def test_defaults_restores_the_package_signature():
    import inspect

    from cyclophaser.determine_periods import get_periods, process_vorticity
    at = _app()
    at.slider(key="cutoff_high").set_value(48)
    at.slider(key="thr_int_gap").set_value(0.2)
    at.radio(key="incipient_method").set_value("geometric")
    _run(at)
    assert at.session_state["cutoff_high"] == 48            # the edits took
    at.button(key="btn_defaults").click()
    _run(at)
    live = at.session_state["_bench_live_config"]
    for fn, sec in ((process_vorticity, "filter_params"), (get_periods, "phase_params")):
        sig = {k: p.default for k, p in inspect.signature(fn).parameters.items()
               if k in live[sec]}
        for k, v in sig.items():
            got = live[sec][k]
            if k == "use_filter":
                assert got is True and v == "auto"
            else:
                assert got == v, (k, got, v)
    assert _notice(at).startswith("0 advanced parameters")
    assert any("Active: **Defaults**" in m.value for m in at.sidebar.markdown)


# ── developer functions ───────────────────────────────────────────────────────

def _dev_surface(at) -> dict:
    return {
        "mark": any(c.key and c.key.startswith("badcase__") for c in at.checkbox),
        "summary": any(h.value == "Bad-case evaluation" for h in at.main.subheader),
        "clear": any("Clear bad-case marks" in (b.label or "") for b in at.button),
        "synthetic": any(c.key in ("load_synthetic_clean", "load_synthetic_noisy")
                         for c in at.checkbox),
    }


def test_developer_functions_are_absent_without_the_key(monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    at = _app(data=True)
    assert at.main.subheader, "positive control: the grid rendered"
    assert not any(_dev_surface(at).values()), _dev_surface(at)
    doc = yaml.safe_load(_package(at).read("parameters.yaml"))
    assert "evaluation" not in doc
    assert {"metadata", "filter_params", "phase_params"} <= set(doc)


def test_developer_functions_are_present_with_the_key(monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    at = _app(dev=True, data=True)
    assert all(_dev_surface(at).values()), _dev_surface(at)
    doc = yaml.safe_load(_package(at).read("parameters.yaml"))
    assert doc["evaluation"]["total_cyclones"] == 1


# ── nothing loaded, nothing runs ──────────────────────────────────────────────

def test_without_data_no_detection_runs(monkeypatch):
    import streamlit as st

    import cyclophaser.determine_periods  # noqa: F401
    dp = sys.modules["cyclophaser.determine_periods"]
    import functools
    calls = []
    real = dp.get_periods

    @functools.wraps(real)          # keeps the signature the app reads its defaults from
    def counting(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(dp, "get_periods", counting)
    st.cache_data.clear()
    at = _app()
    # I3 replaced the one-line no-data text with the start screen: its heading
    # is the only subheader, and no track was drawn.
    assert [h.value for h in at.main.subheader] == [
        "Check CycloPhaser's phases on your cyclone tracks"]
    assert calls == []
    # positive control: loading data does run it
    at.button(key="btn_example").click()
    _run(at)
    assert calls, "loading the example ran no detection — the counter is not wired"


# ── the bad-case mark survives display modes and pages ────────────────────────

def test_a_bad_case_mark_survives_grid_inspector_grid_and_a_page_trip():
    at = _app(dev=True, data=True)
    mark = next(c.key for c in at.checkbox if c.key and c.key.startswith("badcase__"))
    at.checkbox(key=mark).check()
    _run(at)
    at.radio(key="view_mode").set_value("Inspector")
    _run(at)
    assert at.session_state[mark] is True
    at.radio(key="view_mode").set_value("Grid")
    _run(at)
    assert at.checkbox(key=mark).value is True
    at.switch_page("app_pages/benchmark.py")
    _run(at)
    at.switch_page("app_pages/calibrate.py")
    _run(at)
    assert at.checkbox(key=mark).value is True
    assert any(m.value.startswith("1 /") for m in at.metric)


# ── version ───────────────────────────────────────────────────────────────────

def test_the_displayed_version_is_the_installed_package():
    at = _app()
    want = f"CycloPhaser {metadata.version('cyclophaser')}"
    assert any(c.value.startswith(want) for c in at.main.caption), (
        want, [c.value for c in at.main.caption])


# ── Save results ──────────────────────────────────────────────────────────────

def test_save_results_packs_what_the_options_say():
    at = _app(data=True)
    names = _package(at).namelist()                       # defaults: YAML + CSV
    assert names == ["parameters.yaml", "example_file_periods.csv"], names
    names = _package(at, csv=False, png=False).namelist()
    assert names == ["parameters.yaml"], names
    names = _package(at, csv=True, png=True).namelist()
    assert sorted(names) == ["example_file_periods.csv", "example_file_periods.png",
                             "parameters.yaml"], names


def test_the_saved_yaml_is_the_old_export_content():
    """Same document the old 'Export parameters (YAML)' wrote: metadata,
    filter_params, phase_params (+ evaluation with the developer key)."""
    at = _app(dev=True, data=True)
    doc = yaml.safe_load(_package(at).read("parameters.yaml"))
    assert list(doc) == ["metadata", "filter_params", "phase_params", "evaluation"]
    assert doc["metadata"]["cyclones_used"] == ["example_file"]
    assert doc["filter_params"] == {
        k: v for k, v in at.session_state["_bench_live_config"]["filter_params"].items()}
