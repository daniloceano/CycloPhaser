"""Calibrate page after the app redesign's I3 — Streamlit AppTest, public API only.

The start screen, the paged Grid, the set statistics and the YAML "evaluation"
section without the developer key. The browser-side checks of the page trip are
in tests/test_app_pages_browser.py.
"""

from __future__ import annotations

import functools
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"
SAMPLE = sorted((REPO_ROOT / "tests" / "calibration_data").glob("*.csv"))
START = "Check CycloPhaser's phases on your cyclone tracks"

pytest.importorskip("streamlit")
yaml = pytest.importorskip("yaml")
pd = pytest.importorskip("pandas")
from streamlit.testing.v1 import AppTest  # noqa: E402


def _run(at) -> AppTest:
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _app(dev: bool = False) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=900)
    if dev:
        at.secrets["developer_mode"] = True
    return _run(at)


def _click(at, key: str) -> AppTest:
    at.button(key=key).click()
    return _run(at)


def _figures(at) -> int:
    """Images in the page. AppTest of streamlit 1.56 exposes st.image as
    element type "imgs", 1.63 as "image"; both through `at.get`."""
    return len(at.get("image")) + len(at.get("imgs"))


def _track_headings(at, names) -> list[str]:
    return [h.value.removeprefix("⚠️ ") for h in at.main.subheader
            if h.value.removeprefix("⚠️ ") in names]


def _page_line(at) -> str:
    hits = [m.value for m in at.main.markdown if "Page <b>" in m.value]
    assert hits, [m.value for m in at.main.markdown]
    return re.sub(r"<[^>]+>", "", hits[0])


def _counting_get_periods(monkeypatch) -> list:
    import cyclophaser.determine_periods  # noqa: F401
    dp = sys.modules["cyclophaser.determine_periods"]
    calls = []
    real = dp.get_periods

    @functools.wraps(real)          # keeps the signature the app reads its defaults from
    def counting(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(dp, "get_periods", counting)
    return calls


# ── the start screen ──────────────────────────────────────────────────────────

def test_the_start_screen_explains_and_runs_no_detection(monkeypatch):
    import streamlit as st
    calls = _counting_get_periods(monkeypatch)
    st.cache_data.clear()
    at = _app()
    assert [h.value for h in at.main.subheader] == [START]
    text = "\n".join(m.value for m in at.main.markdown)
    for step in ("1. **Load tracks**", "2. **Check the figures**",
                 "3. **Adjust the filtering**", "4. **Save**"):
        assert step in text, step
    assert "https://cyclophaser.readthedocs.io" in text
    assert {b.key for b in at.main.button} == {"start_example", "start_sample"}
    assert _figures(at) == 0 and calls == []
    # positive control: the counter is wired
    _click(at, "start_example")
    assert calls, "loading the example ran no detection — the counter is not wired"


@pytest.mark.parametrize("start_key, side_key", [("start_example", "btn_example"),
                                                 ("start_sample", "btn_sample")])
def test_a_start_screen_button_does_what_the_sidebar_button_does(start_key, side_key):
    via_start = _click(_app(), start_key)
    via_side = _click(_app(), side_key)
    for at in (via_start, via_side):
        assert START not in [h.value for h in at.main.subheader]
    loaded = [m.value for m in via_start.sidebar.markdown if "loaded" in m.value]
    assert loaded and loaded == [m.value for m in via_side.sidebar.markdown
                                 if "loaded" in m.value], loaded
    assert ([h.value for h in via_start.main.subheader]
            == [h.value for h in via_side.main.subheader])
    for k in ("load_example", "load_all_test_cyclones"):
        got = [at.session_state[k] if k in at.session_state else None
               for at in (via_start, via_side)]
        assert got[0] == got[1], (k, got)


# ── the paged grid ────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def sample_names():
    assert len(SAMPLE) == 51, len(SAMPLE)
    return [p.stem for p in SAMPLE]


def test_only_the_tracks_of_the_current_page_get_a_figure(monkeypatch, sample_names):
    import streamlit as st
    calls = _counting_get_periods(monkeypatch)
    st.cache_data.clear()
    at = _click(_app(), "btn_sample")
    # detection still runs on every loaded track …
    assert len(calls) == 51, len(calls)
    # … but only the page's 12 tracks are drawn
    shown = _track_headings(at, set(sample_names))
    assert len(shown) == 12 and _figures(at) == 12, (shown, _figures(at))
    assert _page_line(at) == "Page 1 of 5 · tracks 1–12 of 51"
    # the consolidated table still has all of them
    table = next(d.value for d in at.main.dataframe if d.value.index.name == "Cyclone")
    assert len(table) == 51
    # 24 per page: 24 figures
    at.selectbox(key="grid_page_size").set_value(24)
    _run(at)
    assert _figures(at) == 24 and _page_line(at) == "Page 1 of 3 · tracks 1–24 of 51"


def test_the_pages_cover_every_track_once_and_a_new_set_starts_at_page_one(sample_names):
    at = _click(_app(), "btn_sample")
    seen, lines = [], []
    while True:
        seen += _track_headings(at, set(sample_names))
        lines.append(_page_line(at))
        if at.button(key="grid_next_top").disabled:
            break
        _click(at, "grid_next_top")
    assert sorted(seen) == sorted(sample_names) and len(seen) == 51
    assert lines[-1] == "Page 5 of 5 · tracks 49–51 of 51" and _figures(at) == 3
    _click(at, "grid_prev_top")
    assert _page_line(at) == "Page 4 of 5 · tracks 37–48 of 51"
    _click(at, "grid_prev_bottom")
    assert _page_line(at) == "Page 3 of 5 · tracks 25–36 of 51"
    # changing the loaded set (the example added) goes back to page 1
    _click(at, "btn_example")
    assert _page_line(at) == "Page 1 of 5 · tracks 1–12 of 52"
    assert at.button(key="grid_prev_top").disabled


def test_a_bad_case_mark_on_page_one_survives_page_two_the_inspector_and_benchmark(
        sample_names):
    at = _click(_app(dev=True), "btn_sample")
    first = _track_headings(at, set(sample_names))[0]
    mark = f"badcase__{first}"
    at.checkbox(key=mark).check()
    _run(at)
    _click(at, "grid_next_top")
    assert first not in _track_headings(at, set(sample_names))
    assert at.session_state[mark] is True
    at.radio(key="view_mode").set_value("Inspector")
    _run(at)
    assert at.session_state[mark] is True
    at.radio(key="view_mode").set_value("Grid")
    _run(at)
    at.switch_page("app_pages/benchmark.py")
    _run(at)
    at.switch_page("app_pages/calibrate.py")
    _run(at)
    # still on page 2 after the trip; back to page 1, the box is still ticked
    assert _page_line(at) == "Page 2 of 5 · tracks 13–24 of 51"
    _click(at, "grid_prev_top")
    assert at.checkbox(key=mark).value is True
    assert any(m.value.startswith("1 /") for m in at.metric)


def test_the_page_size_survives_the_inspector_and_a_page_trip():
    at = _click(_app(), "btn_sample")
    at.selectbox(key="grid_page_size").set_value(48)
    _run(at)
    at.radio(key="view_mode").set_value("Inspector")
    _run(at)
    at.radio(key="view_mode").set_value("Grid")
    _run(at)
    assert at.selectbox(key="grid_page_size").value == 48
    at.switch_page("app_pages/benchmark.py")
    _run(at)
    at.switch_page("app_pages/calibrate.py")
    _run(at)
    assert at.selectbox(key="grid_page_size").value == 48
    assert _figures(at) == 48


def test_the_grid_columns_survive_the_inspector_and_a_page_trip():
    at = _click(_app(), "btn_example")
    at.select_slider(key="n_cols").set_value(3)
    _run(at)
    at.radio(key="view_mode").set_value("Inspector")
    _run(at)
    at.radio(key="view_mode").set_value("Grid")
    _run(at)
    assert at.select_slider(key="n_cols").value == 3
    at.switch_page("app_pages/benchmark.py")
    _run(at)
    at.switch_page("app_pages/calibrate.py")
    _run(at)
    assert at.select_slider(key="n_cols").value == 3


# ── set statistics ────────────────────────────────────────────────────────────

def _expected_stats() -> dict:
    """Computed here, independently of the app: each sample track read with
    pandas, phases from cyclophaser's own determine_periods + periods_to_dict at
    the package defaults (what the app runs with nothing changed). Every key the
    package produces ("intensification", "intensification 2", …) is counted on
    its own: nothing is merged."""
    from cyclophaser.determine_periods import determine_periods, periods_to_dict

    presence, seqs, durations, cycle = Counter(), Counter(), {}, []
    for p in SAMPLE:
        df = pd.read_csv(p, sep=";", parse_dates=["time"]).set_index("time")
        periods = periods_to_dict(determine_periods(df.iloc[:, 0]))
        seqs[tuple(periods)] += 1
        presence.update(periods.keys())
        for k, (s, e) in periods.items():
            durations.setdefault(k, []).append((e - s) / pd.Timedelta(hours=1))
        ends = [e for _s, e in periods.values()]
        starts = [s for s, _e in periods.values()]
        cycle.append((max(ends) - min(starts)) / pd.Timedelta(hours=1))
    return {"n": len(SAMPLE), "presence": presence, "seqs": seqs,
            "durations": durations, "cycle": cycle}


def _package_palette() -> dict:
    """cyclophaser/plots.py's phase colours, read from the file (the figures'
    palette), not from the app."""
    import ast
    tree = ast.parse((REPO_ROOT / "cyclophaser" / "plots.py").read_text())
    return next(ast.literal_eval(n.value) for n in ast.walk(tree)
                if isinstance(n, ast.Assign)
                and any(getattr(t, "id", None) == "colors_phases" for t in n.targets))


def _sequence_rows(at) -> list[tuple[tuple, int, list[tuple[str, str]]]]:
    """(names, tracks, [(square colour, square number)]) per row of the
    sequences table, read from the markdown the page sends."""
    import html
    src = next(m.value for m in at.main.markdown if 'class="seq-table"' in m.value)
    rows = []
    for tr in re.findall(r"<tr><td.*?</tr>", src, re.S):
        names = html.unescape(re.search(r'<span class="seq-names">(.*?)</span>', tr).group(1))
        count = int(re.search(r'<td class="seq-n"[^>]*>(\d+)</td>', tr).group(1))
        squares = re.findall(r'class="seq-sq"[^>]*?background:([^;]+);[^>]*>(\d*)</span>', tr)
        rows.append((tuple(names.split(" → ")), count, squares))
    return rows


def test_the_set_statistics_match_an_independent_computation(sample_names):
    exp = _expected_stats()
    at = _click(_app(), "btn_sample")
    assert "Set statistics" in [h.value for h in at.main.subheader]
    assert ("Descriptive statistics of the detected phases — not a quality score."
            in [c.value for c in at.main.caption])
    metrics = {m.label: m.value for m in at.main.metric}
    assert metrics["Analysed"] == "51" and metrics["Failed"] == "0", metrics
    assert float(metrics["Whole cycle, median (h)"]) == pytest.approx(
        statistics.median(exp["cycle"]), abs=0.05)

    phases = next(d.value for d in at.main.dataframe if "Phase" in d.value.columns)
    by_phase = phases.set_index("Phase")
    assert set(by_phase.index) == set(exp["presence"]), (set(by_phase.index), exp["presence"])
    assert any(re.search(r" \d+$", k) for k in exp["presence"]), \
        "positive control: the sample has a repeated phase"
    for key, n in exp["presence"].items():
        row = by_phase.loc[key]
        assert row["Tracks with it (n)"] == n, key
        assert row["Tracks with it (%)"] == pytest.approx(100 * n / exp["n"], abs=0.05), key
        assert row["Durations (n)"] == len(exp["durations"][key]), key
        assert row["Median duration (h)"] == pytest.approx(
            statistics.median(exp["durations"][key]), abs=0.05), key

    # the 5 most common sequences, with their squares in the figures' colours
    palette = _package_palette()
    want = sorted(exp["seqs"].items(), key=lambda kv: (-kv[1], " → ".join(kv[0])))[:5]
    rows = _sequence_rows(at)
    assert [(names, n) for names, n, _sq in rows] == want
    for names, _n, squares in rows:
        assert len(squares) == len(names)
        for key, (colour, number) in zip(names, squares):
            assert colour == palette[re.sub(r" \d+$", "", key)], (key, colour)
            m = re.search(r" (\d+)$", key)
            assert number == (m.group(1) if m else ""), (key, number)
    assert any(sq[1] for _names, _n, squares in rows for sq in squares), \
        "positive control: a repeated phase is in the top 5"

    # every sample track has dates: all 51 in the durations, none left out
    cap = " ".join(c.value for c in at.main.caption)
    assert "51 track(s) with dates are in the durations; 0 left out" in cap, cap
    assert "summed" not in cap


def test_the_statistics_make_no_detection_call_of_their_own(monkeypatch):
    """A rerun that changes nothing detection depends on (the page size) is a
    cache hit everywhere: no get_periods call although the statistics are
    redrawn."""
    import streamlit as st
    calls = _counting_get_periods(monkeypatch)
    st.cache_data.clear()
    at = _click(_app(), "btn_sample")
    assert len(calls) == 51
    del calls[:]
    _click(at, "grid_next_top")
    assert "Set statistics" in [h.value for h in at.main.subheader]
    assert calls == []


def test_a_track_without_dates_is_left_out_of_the_durations_only():
    """The readers of the app always give dates, so this branch is checked on
    the statistics function with a hand-made input whose answer is known: one
    dated track (2 h of intensification, 3 h of decay) and one on integer steps."""
    sys.path.insert(0, str(APP.parent))
    import set_stats
    t = pd.Timestamp("2020-01-01 00:00")
    h = pd.Timedelta(hours=1)
    stats = set_stats.compute_set_stats({
        "dated": {"ok": True, "periods_dict": {"intensification": (t, t + 2 * h),
                                               "decay": (t + 3 * h, t + 6 * h)}},
        "steps": {"ok": True, "periods_dict": {"intensification": (0, 4)}},
        "broken": {"ok": False},
    })
    assert stats["n_analysed"] == 2 and stats["failed"] == ["broken"]
    assert stats["n_dated"] == 1 and stats["n_undated"] == 1
    assert stats["presence"] == {"intensification": 2, "decay": 1}
    assert stats["durations"] == {"intensification": [2.0], "decay": [3.0],
                                  "whole cycle": [6.0]}


def test_a_repeated_phase_is_counted_under_its_own_key():
    """'intensification 2' is not merged into 'intensification'."""
    sys.path.insert(0, str(APP.parent))
    import set_stats
    t = pd.Timestamp("2020-01-01 00:00")
    h = pd.Timedelta(hours=1)
    stats = set_stats.compute_set_stats({
        "twice": {"ok": True, "periods_dict": {
            "intensification": (t, t + 2 * h), "decay": (t + 3 * h, t + 4 * h),
            "intensification 2": (t + 5 * h, t + 10 * h)}},
        "once": {"ok": True, "periods_dict": {"intensification": (t, t + 4 * h)}},
    })
    assert stats["phases"] == ["intensification", "intensification 2", "decay"]
    assert stats["presence"] == {"intensification": 2, "intensification 2": 1, "decay": 1}
    assert stats["durations"]["intensification"] == [2.0, 4.0]
    assert stats["durations"]["intensification 2"] == [5.0]


# ── YAML "evaluation" without the developer key ───────────────────────────────

def _yaml_with_evaluation() -> bytes:
    cfg = REPO_ROOT / "research" / "labels" / "configs" / "cyclophaser_params-track.yaml"
    doc = yaml.safe_load(cfg.read_text())
    doc["evaluation"] = {"total_cyclones": 1, "bad_cases_count": 1,
                         "bad_cases_percent": 100.0, "bad_cases": ["example_file"]}
    return yaml.safe_dump(doc).encode()


def _upload_yaml(at, data: bytes) -> AppTest:
    at.file_uploader(key="yaml_import").set_value(("with_evaluation.yaml", data, "text/yaml"))
    _run(at)
    return _run(at)            # the import reruns once to show the new values


@pytest.mark.parametrize("dev", [False, True])
def test_a_yaml_evaluation_is_restored_only_with_the_developer_key(dev, monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    data = _yaml_with_evaluation()
    at = _click(_app(dev=dev), "btn_example")
    _upload_yaml(at, data)
    warnings = " ".join(w.value for w in at.sidebar.warning)
    if dev:
        assert at.session_state["badcase__example_file"] is True
        assert "evaluation (developer only)" not in warnings
    else:
        assert "badcase__example_file" not in at.session_state
        assert "Ignored keys: evaluation (developer only)" in warnings, warnings
