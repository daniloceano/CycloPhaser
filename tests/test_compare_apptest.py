"""The Compare page (benchmark review, I1) — AppTest, public API only.

Every test starts where a user starts: the Calibrate page, with data loaded
there, then Compare from the menu. AppTest cannot drive a file uploader, so the
"Upload YAML" path is exercised in Chromium (tests/test_compare_browser.py).

What needs a control and has one:

* "Defaults" is what Calibrate's Defaults button sets — and, before pressing
  it, the two differ (otherwise equality would prove nothing).
* The Compare phases are the Calibrate phases — and the same tracks without
  their time axis give different phases on at least one track (finding A11), so
  the comparison can fail.
* The text scan finds nothing on Compare — and finds the planted words on the
  Benchmark page, with the same scanner.
* Compare runs with the label readers raising — and the Benchmark page, under
  the same patch, does not (the patch reaches the app).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"
APP_DIR = APP.parent

pytest.importorskip("streamlit")
pytest.importorskip("yaml")
import streamlit as st  # noqa: E402
import yaml  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

sys.path.insert(0, str(APP_DIR))
import benchmark_core as bc  # noqa: E402
import compare_core as cc  # noqa: E402

CALIBRATE = "app_pages/calibrate.py"
COMPARE = "app_pages/compare.py"
BENCHMARK = "app_pages/benchmark.py"

FORBIDDEN = ("train", "test split", "adjudicated", "manual label", "swell",
             "sha256", "commit", "bad_cases", "ground truth", "research/")


# ── helpers ───────────────────────────────────────────────────────────────────
def _ok(at):
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _app(data: str | None = "sample") -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=600)
    at.run()
    if data == "sample":
        at.button(key="btn_sample").click()
        at.run()
    elif data == "example":
        at.button(key="btn_example").click()
        at.run()
    return _ok(at)


def _go(at, page):
    at.switch_page(page).run()
    return _ok(at)


def _click(at, key):
    at.button(key=key).click()
    at.run()
    return _ok(at)


def _w(at, kind, key):
    for w in getattr(at, kind):
        if w.key == key:
            return w
    raise AssertionError(f"no {kind} with key {key!r}")


def _set_cutoff(at, value):
    """On Calibrate: the one declared non-default value, High cutoff."""
    _w(at, "slider", "cutoff_high").set_value(value)
    at.run()
    return _ok(at)


def _two_columns(at, cutoff=48):
    """Calibrate with `cutoff` → Compare, Current settings + Defaults, Run."""
    _set_cutoff(at, cutoff)
    _go(at, COMPARE)
    _click(at, "cmp_add_current")
    _click(at, "cmp_add_defaults")
    return _click(at, "cmp_run")


def _n_images(at) -> int:
    """st.image elements. The element type is "imgs" on streamlit 1.56 and
    "image" on 1.63 (measured); both are counted."""
    return len(at.get("image")) + len(at.get("imgs"))


def _frames(at):
    return [df.value for df in at.dataframe]


def _relative_frame(at):
    return next(f for f in _frames(at) if "Sequence changed" in list(f.index))


def _per_config_frame(at):
    return next(f for f in _frames(at)
                if any("Incipient absent" in str(i) for i in f.index))


def _texts(at) -> list[str]:
    out = []
    for kind in ("title", "header", "subheader", "markdown", "caption", "info",
                 "warning", "error", "success", "code", "text"):
        out += [str(e.value) for e in getattr(at, kind)]
    for kind in ("button", "checkbox", "radio", "selectbox", "multiselect",
                 "text_area", "text_input", "number_input", "slider", "toggle"):
        for e in getattr(at, kind):
            out.append(str(e.label))
            if getattr(e, "help", None):
                out.append(str(e.help))
            out += [str(o) for o in (getattr(e, "options", None) or [])]
            if kind == "text_area":
                out.append(str(e.value))
    out += [str(e.label) for e in at.expander]
    for f in _frames(at):
        out += [str(i) for i in f.index] + [str(c) for c in f.columns]
        out += [str(v) for v in f.to_numpy().ravel()]
    for kind in ("file_uploader", "page_link"):
        for e in at.get(kind):
            proto = getattr(e, "proto", None)
            for attr in ("label", "help"):
                if proto is not None and getattr(proto, attr, ""):
                    out.append(str(getattr(proto, attr)))
    return out


def _forbidden_found(texts) -> set[str]:
    found = set()
    for term in FORBIDDEN:
        pat = re.compile(r"(?<!\w)" + re.escape(term)
                         + ("" if term.endswith("/") else r"(?!\w)"), re.I)
        if any(pat.search(t) for t in texts):
            found.add(term)
    return found


class _Counter:
    def __init__(self, monkeypatch):
        self.n = 0
        real = cc.run_cell

        def counted(doc, series):
            self.n += 1
            return real(doc, series)
        monkeypatch.setattr(cc, "run_cell", counted)


# ── the menu and the empty state ──────────────────────────────────────────────
def test_compare_is_in_the_calibration_menu_after_calibrate():
    src = APP.read_text()
    assert ('_pages = {"Calibration": [_PAGE_CALIBRATE, _PAGE_COMPARE, '
            '_PAGE_BENCHMARK]}') in src
    at = _go(_app(None), COMPARE)
    assert [t.value for t in at.title] == ["Compare configurations"]
    assert any("What changes in the phases of your tracks" in m.value
               for m in at.markdown)


def test_without_tracks_an_empty_state_links_to_calibrate():
    at = _go(_app(None), COMPARE)
    assert any("No tracks are loaded" in i.value for i in at.info)
    assert len(at.get("page_link")) == 1
    assert not any(b.key == "cmp_run" for b in at.button)


# ── tracks ────────────────────────────────────────────────────────────────────
def test_compare_receives_the_calibrate_tracks_all_selected():
    at = _go(_app(), COMPARE)
    published = list(at.session_state["_compare_live_tracks"])
    assert len(published) == 51
    ms = _w(at, "multiselect", "cmp_tracks")
    assert list(ms.options) == published
    assert list(ms.value) == published
    assert any(m.value.startswith("**51 of 51**") for m in at.markdown)


def test_all_invert_clear_and_individual_selection():
    at = _go(_app(), COMPARE)
    names = list(at.session_state["_compare_live_tracks"])
    _w(at, "multiselect", "cmp_tracks").set_value(names[:3])
    at.run()
    assert list(at.session_state["cmp_tracks"]) == names[:3]
    _click(at, "cmp_invert")
    assert list(at.session_state["cmp_tracks"]) == names[3:]
    _click(at, "cmp_clear")
    assert list(at.session_state["cmp_tracks"]) == []
    _click(at, "cmp_all")
    assert list(at.session_state["cmp_tracks"]) == names


# ── the three column sources ──────────────────────────────────────────────────
def test_current_settings_is_the_published_live_config():
    at = _app("example")
    _set_cutoff(at, 48)
    _go(at, COMPARE)
    _click(at, "cmp_add_current")
    col = at.session_state["cmp_columns"][-1]
    assert col["name"] == "Current settings"
    assert col["doc"] == cc.parameter_sections(at.session_state["_bench_live_config"])
    assert col["doc"]["filter_params"]["cutoff_high"] == 48


def test_defaults_is_what_the_calibrate_defaults_button_sets():
    at = _app("example")
    _set_cutoff(at, 48)
    live = at.session_state["_bench_live_config"]
    defaults = at.session_state["_compare_defaults_config"]
    # control: before pressing Defaults the two differ, in the declared value
    assert list(cc.config_differences(live, defaults)) == ["filter_params.cutoff_high"]
    _click(at, "btn_defaults")
    live = at.session_state["_bench_live_config"]
    assert live == at.session_state["_compare_defaults_config"]
    assert cc.config_key(live) == cc.config_key(defaults)
    _go(at, COMPARE)
    _click(at, "cmp_add_defaults")
    col = at.session_state["cmp_columns"][-1]
    assert col["name"] == "Defaults" and col["doc"] == cc.parameter_sections(defaults)


# ── Run: blocked, explicit, stale ─────────────────────────────────────────────
def test_run_without_columns_is_blocked_and_says_why_in_visible_text():
    at = _go(_app("example"), COMPARE)
    assert _w(at, "button", "cmp_run").disabled
    assert "To run, add at least one configuration." in [i.value for i in at.info]


def test_run_without_a_selected_track_is_blocked_and_says_why():
    at = _go(_app("example"), COMPARE)
    _click(at, "cmp_add_current")
    _click(at, "cmp_clear")
    assert _w(at, "button", "cmp_run").disabled
    assert "To run, select at least one track." in [i.value for i in at.info]


def test_nothing_recomputes_on_edit_and_results_go_stale(monkeypatch):
    at = _app()
    _two_columns(at)
    before = at.session_state["_cmp_results"]
    names = list(at.session_state["_compare_live_tracks"])
    count = _Counter(monkeypatch)
    _w(at, "multiselect", "cmp_tracks").set_value(names[:5])   # selection changed
    at.run()
    _click(at, "cmp_add_current")                     # a column added
    assert count.n == 0
    assert at.session_state["_cmp_results"] == before
    assert any(w.value.startswith("Results out of date") for w in at.warning)


# ── results ───────────────────────────────────────────────────────────────────
def test_the_relative_table_declares_the_set_and_the_reference():
    at = _app()
    _two_columns(at)
    assert any(m.value == "#### Relative to Current settings" for m in at.markdown)
    caps = [c.value for c in at.caption]
    assert any(c.startswith("Over the 51 selected track(s) of the last run. Each "
                            "configuration is compared with **Current settings**")
               for c in caps), caps
    rel = _relative_frame(at)
    assert list(rel.columns) == ["Defaults"]
    assert rel.loc["Tracks compared", "Defaults"] == "51 of 51"
    assert rel.loc["Sequence changed", "Defaults"].endswith(" of 51")
    assert any(c.startswith("Over the 51 selected track(s) of the last run; each "
                            "configuration on its own, not relative to Current "
                            "settings") for c in caps)


def test_changing_the_reference_runs_no_detection(monkeypatch):
    at = _app()
    _two_columns(at)
    count = _Counter(monkeypatch)
    _w(at, "selectbox", "cmp_reference").set_value("Defaults")
    at.run()
    _ok(at)
    assert count.n == 0
    assert any(m.value == "#### Relative to Defaults" for m in at.markdown)
    assert list(_relative_frame(at).columns) == ["Current settings"]
    assert not any(w.value.startswith("Results out of date") for w in at.warning)


def test_incipient_absent_is_a_count_per_column_outside_the_relative_table():
    at = _app()
    _two_columns(at)
    rel = _relative_frame(at)
    assert not any("ncipient" in str(i) for i in rel.index)
    per = _per_config_frame(at)
    assert list(per.columns) == ["Current settings", "Defaults"]
    res = at.session_state["_cmp_results"]
    for c in res["columns"]:
        k, ran = cc.incipient_absent(res["cells"][c["cid"]], res["ids"])
        assert per.loc["Incipient absent (first phase is not incipient)",
                       c["name"]] == f"{k} of {ran}"


def test_compare_phases_are_the_calibrate_phases():
    """Positive control on finding A11: the Compare cell of each track is what
    Calibrate's own call produces (`_run_process_vorticity` / `_run_get_periods`,
    copied here call for call), and the same tracks WITHOUT their time axis give
    a different answer on at least one of them."""
    import pandas as pd
    import warnings
    import track_io
    from cyclophaser.determine_periods import get_periods, process_vorticity
    from package_args import package_use_filter

    at = _app()
    # 'auto' Savitzky-Golay: the window process_vorticity reads off the time
    # index (> 8 days or not). The package defaults use no smoothing, so under
    # them the time axis changes nothing and the control could not fail.
    _w(at, "selectbox", "sm_mode").set_value("auto")
    at.run()
    _ok(at)
    assert at.session_state["_bench_live_config"]["filter_params"]["use_smoothing"] == "auto"
    _go(at, COMPARE)
    _click(at, "cmp_add_current")
    _click(at, "cmp_run")
    res = at.session_state["_cmp_results"]
    live = at.session_state["_bench_live_config"]
    fp, pp = live["filter_params"], live["phase_params"]
    cells = res["cells"][res["columns"][0]["cid"]]
    tracks = at.session_state["_compare_live_tracks"]

    def calibrate(series):
        zeta_df = pd.DataFrame({"zeta": series})
        zeta_df.index = series.index
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(
                zeta_df, use_filter=package_use_filter(fp["use_filter"]),
                cutoff_low=fp["cutoff_low"], cutoff_high=fp["cutoff_high"],
                use_smoothing=fp["use_smoothing"],
                use_smoothing_twice=fp["use_smoothing_twice"],
                replace_endpoints_with_lowpass=fp["replace_endpoints_with_lowpass"],
                savgol_polynomial=fp["savgol_polynomial"],
                boundary_padding=fp["boundary_padding"])
            out = get_periods(vorticity=vort, plot=False, plot_steps=False, **pp)
        return [tuple(r) for r in bc.phase_runs_from_periods(out["periods"])]

    stripped_differs = 0
    for sid in res["ids"]:
        series = track_io.read_track(tracks[sid])
        assert cells[sid]["runs"] == calibrate(series), sid
        no_time = pd.Series(series.to_numpy())
        if calibrate(no_time) != cells[sid]["runs"]:
            stripped_differs += 1
    assert stripped_differs > 0


def test_the_cache_is_keyed_by_content_and_holds_across_runs(monkeypatch):
    at = _app()
    _set_cutoff(at, 48)              # two different configurations, not one twice
    _go(at, COMPARE)
    _click(at, "cmp_add_current")
    _click(at, "cmp_add_defaults")
    names = list(at.session_state["_compare_live_tracks"])
    _w(at, "multiselect", "cmp_tracks").set_value(names[:4])
    at.run()
    st.cache_data.clear()
    count = _Counter(monkeypatch)
    _click(at, "cmp_run")
    assert count.n == 4 * 2
    _click(at, "cmp_run")                                   # warm
    assert count.n == 4 * 2
    # two tracks swap names: same contents, so nothing is recomputed
    tracks = dict(at.session_state["_compare_live_tracks"])
    a, b = names[0], names[1]
    tracks[a], tracks[b] = tracks[b], tracks[a]
    at.session_state["_compare_live_tracks"] = tracks
    at.run()
    _click(at, "cmp_run")
    assert count.n == 4 * 2
    # a new content under an old name: that track only, once per column
    example = (REPO_ROOT / "cyclophaser" / "example_data" / "example_file.csv").read_bytes()
    tracks[a] = example
    at.session_state["_compare_live_tracks"] = tracks
    at.run()
    _click(at, "cmp_run")
    assert count.n == 4 * 2 + 2


def test_show_only_cyclones_whose_sequence_differs():
    at = _app()
    _two_columns(at)
    res = at.session_state["_cmp_results"]
    ref, other = res["columns"]
    differing = [s for s in res["ids"] if cc.sequence_differs(
        res["cells"][other["cid"]][s], res["cells"][ref["cid"]][s])]
    assert 0 < len(differing) < len(res["ids"])        # the filter has work to do
    _w(at, "checkbox", "cmp_only_differing").check()
    at.run()
    _ok(at)
    assert any(c.value.startswith(f"{len(differing)} of the 51 selected track(s)")
               for c in at.caption)
    shown = [m.value.strip("*") for m in at.markdown
             if m.value.startswith("**") and m.value.strip("*") in res["ids"]]
    assert shown == differing[:12]
    assert sum(c.value == "sequence differs from reference"
               for c in at.caption) == len(shown)


def test_both_layouts_render_with_the_legend_and_errors_per_cell():
    at = _app()
    _go(at, COMPARE)
    _click(at, "cmp_add_current")
    _click(at, "cmp_add_defaults")
    # a configuration the package refuses, through Edit → one error per cell
    doc = at.session_state["cmp_columns"][1]["doc"]
    bad = {**doc, "filter_params": {**doc["filter_params"],
                                    "boundary_padding": "bogus"}}
    _w(at, "text_area", "cmp_edit_2").set_value(yaml.safe_dump(bad))
    at.run()
    _click(at, "cmp_apply_2")
    _click(at, "cmp_run")
    page = 12
    imgs = _n_images(at)
    assert imgs == page                                 # side by side: one per good cell
    errors = [e.value for e in at.error if e.value.startswith("Defaults: ")]
    assert len(errors) == page
    assert any("incipient" in m.value and "mature" in m.value for m in at.markdown)
    _w(at, "radio", "cmp_figure_layout").set_value("Stacked")
    at.run()
    _ok(at)
    assert _n_images(at) == page                  # one figure per track
    assert len([e for e in at.error if e.value.startswith("Defaults: ")]) == page


def test_the_compare_state_survives_a_trip_to_calibrate():
    at = _app()
    _two_columns(at)
    names = list(at.session_state["_compare_live_tracks"])
    _w(at, "selectbox", "cmp_reference").set_value("Defaults")
    at.run()
    _w(at, "radio", "cmp_figure_layout").set_value("Stacked")
    at.run()
    _w(at, "checkbox", "cmp_only_differing").check()
    at.run()
    _w(at, "selectbox", "cmp_page_size").set_value(24)
    at.run()
    _w(at, "multiselect", "cmp_tracks").set_value(names[:5])
    at.run()
    before = {k: at.session_state[k] for k in
              ("cmp_reference", "cmp_figure_layout", "cmp_only_differing",
               "cmp_page_size", "cmp_tracks", "cmp_columns", "_cmp_results")}
    _go(at, CALIBRATE)
    _go(at, COMPARE)
    after = {k: at.session_state[k] for k in before}
    assert after == before
    assert _w(at, "selectbox", "cmp_reference").value == "Defaults"
    assert _w(at, "radio", "cmp_figure_layout").value == "Stacked"


def test_edit_and_remove_a_column():
    at = _app("example")
    _go(at, COMPARE)
    _click(at, "cmp_add_current")
    _click(at, "cmp_add_defaults")
    doc = at.session_state["cmp_columns"][1]["doc"]
    _w(at, "text_area", "cmp_edit_2").set_value("filter_params: [unclosed")
    at.run()
    _click(at, "cmp_apply_2")
    assert any(e.value.startswith("Not applied: Invalid YAML") for e in at.error)
    assert at.session_state["cmp_columns"][1]["doc"] == doc
    new = {**doc, "filter_params": {**doc["filter_params"], "cutoff_high": 30}}
    _w(at, "text_area", "cmp_edit_2").set_value(yaml.safe_dump(new))
    at.run()
    _click(at, "cmp_apply_2")
    col = at.session_state["cmp_columns"][1]
    assert col["edited"] and col["doc"]["filter_params"]["cutoff_high"] == 30
    assert "Edited on this page." in [c.value for c in at.caption]
    assert any(c.value == "Differs from **Current settings** in 1 parameter(s):"
               for c in at.caption)
    _click(at, "cmp_remove_1")                          # the reference goes
    assert [c["name"] for c in at.session_state["cmp_columns"]] == ["Defaults"]
    assert _w(at, "selectbox", "cmp_reference").value == "Defaults"


# ── e2: no label vocabulary, no label reading ─────────────────────────────────
def test_e2_no_forbidden_term_anywhere_on_the_compare_page():
    seen = set()
    at = _go(_app(None), COMPARE)                      # empty state
    seen |= _forbidden_found(_texts(at))
    at = _app()
    _go(at, COMPARE)
    seen |= _forbidden_found(_texts(at))               # no columns yet
    _go(at, CALIBRATE)
    _two_columns(at)
    seen |= _forbidden_found(_texts(at))               # results, side by side
    _w(at, "checkbox", "cmp_only_differing").check()
    at.run()
    _w(at, "radio", "cmp_figure_layout").set_value("Stacked")
    at.run()
    _w(at, "selectbox", "cmp_reference").set_value("Defaults")
    at.run()
    seen |= _forbidden_found(_texts(at))               # filtered, stacked, other ref
    _click(at, "cmp_invert")
    seen |= _forbidden_found(_texts(at))               # stale
    assert seen == set()


def test_e2_the_scanner_finds_planted_terms_on_the_benchmark_page():
    at = _go(_app(None), BENCHMARK)
    found = _forbidden_found(_texts(at))
    assert {"train", "manual label", "swell"} <= found, found
    assert _forbidden_found(["see Research/labels", "Test Split", "a trainee"]) == \
        {"research/", "test split"}


def test_e2_compare_renders_and_runs_with_label_reading_broken(monkeypatch):
    import labels_core as lc

    def boom(*_a, **_k):
        raise RuntimeError("labels must not be read on the Compare page")

    at = _app()
    for mod, names in ((lc, ("read_labels", "read_split")),
                       (bc, ("read_labels", "read_split", "labels_for_display",
                             "split_membership"))):
        for name in names:
            monkeypatch.setattr(mod, name, boom)
    with pytest.raises(RuntimeError):
        bc.labels_for_display()
    _set_cutoff(at, 48)
    _go(at, COMPARE)
    _click(at, "cmp_add_current")
    _click(at, "cmp_add_defaults")
    _click(at, "cmp_run")
    assert at.session_state["_cmp_results"]["ids"]
    assert any(m.value == "#### Relative to Current settings" for m in at.markdown)
    # control: the same patch does reach the app — the Benchmark page fails
    at.switch_page(BENCHMARK).run()
    assert at.exception


# ── the Benchmark is unchanged ────────────────────────────────────────────────
def test_benchmark_pngs_are_byte_identical_to_before_the_move(tmp_path):
    import importlib.util
    import math
    import benchmark_tab as new
    try:
        old_src = subprocess.run(
            ["git", "show", "39e658c:tools/calibration_app/benchmark_tab.py"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    except Exception as exc:                            # no git, or no history
        pytest.skip(f"39e658c not available: {exc}")
    (tmp_path / "old_benchmark_tab.py").write_text(old_src)
    spec = importlib.util.spec_from_file_location("old_benchmark_tab",
                                                  tmp_path / "old_benchmark_tab.py")
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    v = tuple(math.sin(i / 7) * 1e-5 for i in range(90))
    z = tuple(math.sin(i / 9) * 4e-6 for i in range(90))
    runs = (("incipient", 0, 10), ("intensification", 11, 30), ("mature", 31, 45),
            ("decay", 46, 80), ("residual", 81, 89))
    assert new._png(new._cell_figure(v, runs, "a", z)) == \
        old._png(old._cell_figure(v, runs, "a", z))
    assert new._png(new._cell_figure(v, runs, "a")) == \
        old._png(old._cell_figure(v, runs, "a"))
    panels = (("a", runs, z), ("b", runs[1:], None))
    assert new._png(new._stacked_figure(v, panels)) == \
        old._png(old._stacked_figure(v, panels))


# ── round 2 (checkpoint corrections) ──────────────────────────────────────────
def _main_sequence(at) -> list[tuple[str, str]]:
    """(kind, text-or-key) of the main area's elements, in page order."""
    out = []

    def walk(node):
        for child in getattr(node, "children", {}).values():
            kind = getattr(child, "type", "")
            if kind in ("subheader", "markdown"):
                out.append((kind, str(child.value)))
            elif kind == "selectbox":
                out.append((kind, child.key))
            walk(child)
    walk(at.main)
    return out


def test_card_differences_are_a_compact_list_not_a_table():
    at = _app("example")
    _set_cutoff(at, 48)
    _go(at, COMPARE)
    _click(at, "cmp_add_current")
    _click(at, "cmp_add_defaults")
    assert "Differs from **Current settings** in 1 parameter(s):" in \
        [c.value for c in at.caption]
    # I2, pending item 1: the reference value is named, so the line cannot be
    # read as "changed from → to"; pending item 2: the name breaks only after
    # "." or "_" (<wbr>), never mid-word.
    lines = [m.value for m in at.markdown
             if "filter_params.cutoff_high" in m.value.replace("<wbr>", "")]
    assert len(lines) == 1
    line = lines[0].replace("<wbr>", "")
    assert "<code" in line and "filter_params.cutoff_high</code>: 18 (reference: 48)" in line
    assert "filter_<wbr>params.<wbr>cutoff_<wbr>high" in lines[0]
    assert "→" not in line and "overflow-wrap:anywhere" not in line
    assert not at.dataframe                        # no table anywhere before a Run


def test_the_reference_selector_tops_the_results_before_and_after_run():
    at = _app()
    _set_cutoff(at, 48)
    _go(at, COMPARE)
    _click(at, "cmp_add_current")
    for state in ("before", "after"):
        seq = _main_sequence(at)
        heads = [i for i, (k, v) in enumerate(seq) if k == "subheader"]
        results = next(i for i, (k, v) in enumerate(seq) if v == "4 · Results")
        sel = seq.index(("selectbox", "cmp_reference"))
        assert sel > results, (state, seq)
        assert all(not (results < h < sel) for h in heads), state
        if state == "after":
            rel = next(i for i, (k, v) in enumerate(seq) if v.startswith("#### Relative to"))
            assert sel < rel
        else:
            assert any(v.startswith("**Current settings**  ·  reference")
                       for k, v in seq if k == "markdown")
            _click(at, "cmp_add_defaults")
            _click(at, "cmp_run")


def test_four_columns_disable_every_add_control_with_a_visible_reason():
    at = _go(_app("example"), COMPARE)
    for key in ("cmp_add_current", "cmp_add_defaults", "cmp_add_current"):
        _click(at, key)
    assert not _w(at, "button", "cmp_add_current").disabled
    assert compare_tab_limit() not in [i.value for i in at.info]
    _click(at, "cmp_add_defaults")                  # the fourth
    assert len(at.session_state["cmp_columns"]) == 4
    assert _w(at, "button", "cmp_add_current").disabled
    assert _w(at, "button", "cmp_add_defaults").disabled
    up = at.get("file_uploader")[0]
    assert up.proto.disabled
    assert compare_tab_limit() in [i.value for i in at.info]
    _click(at, "cmp_remove_1")
    assert not _w(at, "button", "cmp_add_current").disabled


def compare_tab_limit() -> str:
    import compare_tab
    return compare_tab.LIMIT_REASON


def test_invert_selection_is_labelled_and_explained_on_compare_only():
    at = _go(_app("example"), COMPARE)
    b = _w(at, "button", "cmp_invert")
    assert b.label == "Invert selection"
    assert b.help == ("Selects the tracks that are not selected and clears the ones "
                      "that are.")
    _go(at, BENCHMARK)
    assert _w(at, "button", "bench_pick_invert").label == "Invert"


def test_a_new_run_clears_the_out_of_date_warning():
    """I2 round 2, F2: after a new Run the out-of-date warning is gone and the
    slot says the results are current (with nothing drawn there, AppTest on
    streamlit 1.56.0 kept the warning of the click's own pass)."""
    at = _two_columns(_app())
    current = "Results are current: 2 configuration(s) × 51 track(s)."
    assert current in [c.value for c in at.caption]
    _click(at, "cmp_add_current")                        # a third column: stale
    assert any(w.value.startswith("Results out of date") for w in at.warning)
    assert current not in [c.value for c in at.caption]
    _click(at, "cmp_run")
    assert not any(w.value.startswith("Results out of date") for w in at.warning)
    assert "Results are current: 3 configuration(s) × 51 track(s)." in \
        [c.value for c in at.caption]
