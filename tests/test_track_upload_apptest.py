"""Streamlit-level tests for track upload and the use_filter translation.

Public AppTest API only — typed widget collections, `.help`, `.allowed_type`,
`file_uploader.set_value`, `at.session_state`, and the text of `at.error` /
`at.warning` / `at.caption` / `at.subheader`. No `filtered_state` or other
internals (they broke on a Streamlit upgrade during Front B).

What is covered:

* **Help exists** on both upload fields and on every custom-format control.
* **.txt is accepted** by both uploaders when the content is standard, and a
  standard .txt reaches the grid.
* **A non-standard file is refused** with a visible error pointing at the
  custom format, and never reaches the grid.
* **A custom file is previewed and waits for confirmation** — it is not in the
  grid before the tick, and is after it; the preview warns on positive
  (northern-hemisphere) vorticity. The Benchmark Exploration upload follows the
  same settings.
* **The grid no longer shows the use_filter=True warning** with the filter on
  and many cyclones. Its positive control proves the searched text is what the
  package emits for True, so "zero occurrences" cannot come from a stale string.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"
CAL = REPO_ROOT / "tests" / "calibration_data"
SOURCE = CAL / "20150069.csv"

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))
import track_format_ui as tfu  # noqa: E402

USE_FILTER_WARNING = "use_filter=True is interpreted"


def _app() -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=600)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _run(at) -> AppTest:
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _widget(at, kind, key):
    for w in getattr(at, kind):
        if w.key == key:
            return w
    raise AssertionError(f"no {kind} with key {key!r}")


def _custom_file(sign: int = 1) -> bytes:
    """SOURCE as ',' + lat,vor,lon,date with day-first dates."""
    rows = ["lat,vor,lon,date"]
    for i, line in enumerate(SOURCE.read_text().splitlines()[1:]):
        t, v = line.split(";")
        if sign < 0:
            v = v[1:] if v.startswith("-") else "-" + v
        rows.append(f"-30,{v},-45,{pd.Timestamp(t):%d/%m/%Y %H:%M}")
    return ("\n".join(rows) + "\n").encode()


def _enable_custom(at) -> AppTest:
    _widget(at, "checkbox", tfu.K_ON).check()
    _run(at)
    _widget(at, "selectbox", tfu.K_SEP).set_value(",")
    _widget(at, "text_input", tfu.K_DATE).set_value("date")
    _widget(at, "text_input", tfu.K_VORT).set_value("vor")
    _widget(at, "text_input", tfu.K_DFMT).set_value("%d/%m/%Y %H:%M")
    return _run(at)


def _errors(at) -> list[str]:
    return [e.value for e in at.error]


def _grid_names(at) -> list[str]:
    return [h.value for h in at.subheader]


# ── help (?) texts and accepted extensions ────────────────────────────────────
def test_upload_field_accepts_txt_and_has_help():
    at = _app()
    up = _widget(at, "file_uploader", "track_upload")
    assert set(up.allowed_type) == {".csv", ".txt"}
    assert up.help == tfu.UPLOAD_HELP
    assert "time;min_max_zeta_850" in up.help and "Custom track format" in up.help


def test_every_custom_format_control_has_help():
    at = _app()
    assert _widget(at, "checkbox", tfu.K_ON).help == tfu.HELP_ON
    _widget(at, "checkbox", tfu.K_ON).check()
    _run(at)
    expected = {
        ("selectbox", tfu.K_SEP): tfu.HELP_SEP,
        ("checkbox", tfu.K_HEADER): tfu.HELP_HEADER,
        ("text_input", tfu.K_DATE): tfu.HELP_DATE,
        ("text_input", tfu.K_VORT): tfu.HELP_VORT,
        ("text_input", tfu.K_DFMT): tfu.HELP_DFMT,
    }
    for (kind, key), text in expected.items():
        assert _widget(at, kind, key).help == text, key


def test_benchmark_upload_accepts_txt_and_has_help():
    at = _app()
    _widget(at, "radio", "bench_mode").set_value("Exploration")
    _run(at)
    up = _widget(at, "file_uploader", "bench_data_upload")
    assert set(up.allowed_type) == {".csv", ".txt"}
    assert tfu.UPLOAD_HELP in up.help


# ── the Calibration uploader ──────────────────────────────────────────────────
def test_standard_content_with_txt_extension_reaches_the_grid():
    at = _app()
    _widget(at, "file_uploader", "track_upload").set_value(
        ("20150069.txt", SOURCE.read_bytes(), "text/plain"))
    _run(at)
    assert _errors(at) == []
    assert "20150069" in _grid_names(at)


def test_non_standard_file_is_refused_visibly_and_never_reaches_the_grid():
    at = _app()
    _widget(at, "file_uploader", "track_upload").set_value(
        ("odd.txt", _custom_file(), "text/plain"))
    _run(at)
    errs = [e for e in _errors(at) if "odd.txt" in e]
    assert len(errs) == 1 and "not the standard track layout" in errs[0]
    assert "Custom track format" in errs[0]
    assert "odd" not in _grid_names(at)


def test_custom_file_is_previewed_and_used_only_after_confirmation():
    at = _enable_custom(_app())
    _widget(at, "file_uploader", "track_upload").set_value(
        ("odd.txt", _custom_file(), "text/plain"))
    _run(at)
    assert _errors(at) == []
    captions = " ".join(c.value for c in at.caption)
    n = len(SOURCE.read_text().splitlines()) - 1
    assert f"**{n}** points" in captions
    assert "odd" not in _grid_names(at), "used before confirmation"
    confirm = [c for c in at.checkbox if c.key.startswith("track_custom_ok_")]
    assert len(confirm) == 1 and confirm[0].help == tfu.HELP_CONFIRM
    confirm[0].check()
    _run(at)
    assert "odd" in _grid_names(at)
    assert _errors(at) == []


def test_positive_vorticity_warns_in_the_preview():
    at = _enable_custom(_app())
    _widget(at, "file_uploader", "track_upload").set_value(
        ("north.txt", _custom_file(sign=-1), "text/plain"))
    _run(at)
    assert any("SOUTHERN hemisphere" in w.value for w in at.warning)


# ── the Benchmark Exploration uploader, same settings ─────────────────────────
def test_benchmark_exploration_uses_the_same_custom_format():
    at = _enable_custom(_app())
    _widget(at, "radio", "bench_mode").set_value("Exploration")
    _run(at)
    _widget(at, "file_uploader", "bench_data_upload").set_value(
        ("odd.txt", _custom_file(), "text/plain"))
    _run(at)
    assert "odd" not in at.session_state["bench_extra_series"]
    [c for c in at.checkbox if c.key.startswith("bench_custom_ok_")][0].check()
    _run(at)
    got = at.session_state["bench_extra_series"]["odd"]
    expected = pd.read_csv(SOURCE, sep=";", index_col="time",
                           parse_dates=True)["min_max_zeta_850"].tolist()
    assert got == expected


# ── the use_filter warning no longer comes from the app ───────────────────────
def test_searched_text_is_what_the_package_emits_for_true():
    """Positive control for the zero-occurrence test below."""
    from cyclophaser.determine_periods import process_vorticity
    s = pd.read_csv(SOURCE, sep=";", index_col="time",
                    parse_dates=True)["min_max_zeta_850"]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        process_vorticity(pd.DataFrame({"zeta": s}), use_filter=True)
    assert any(USE_FILTER_WARNING in str(w.message) for w in caught)


def test_grid_with_filter_on_and_many_cyclones_shows_no_use_filter_warning():
    at = _app()
    _widget(at, "checkbox", "load_all_test_cyclones").check()
    _run(at)
    assert at.session_state["use_filter"] is True
    assert len(_grid_names(at)) > 50
    hits = [w.value for w in at.warning if USE_FILTER_WARNING in w.value]
    assert hits == []
