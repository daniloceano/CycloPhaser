"""The Validate page (benchmark review, I2) — AppTest, public API only.

Every test starts where a developer starts: the developer key on, the Calibrate
page opened once, then "Validate against labels" from the menu. AppTest cannot
drive a file uploader, so the "Upload YAML" path is exercised in Chromium
(tests/test_validate_browser.py).

What needs a control and has one:

* The page is absent without the key — and present with it.
* The agreement numbers are the Benchmark's — the Benchmark page itself, run
  on the same configurations and the same 47 tracks, shows the same counts.
* No test-split id and none of "hit rate", "accuracy", "score" appear on the
  page — and the same scanners find them on the Benchmark page.
* The label panel comes first — the call order of the figure functions, which
  would show a column first if the order were wrong.
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
import compare_tab as ct  # noqa: E402
import config_text  # noqa: E402
import validate_core as vc  # noqa: E402
import validate_tab as vt  # noqa: E402

CALIBRATE = "app_pages/calibrate.py"
COMPARE = "app_pages/compare.py"
BENCHMARK = "app_pages/benchmark.py"
VALIDATE = "app_pages/validate.py"
CONFIG = "cyclophaser_params-track.yaml"
WORDS = ("hit rate", "accuracy", "score")


@pytest.fixture(autouse=True)
def _developer_key(monkeypatch):
    monkeypatch.setenv("CYCLOPHASER_APP_DEV", "1")


# ── helpers ───────────────────────────────────────────────────────────────────
def _ok(at):
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _app() -> AppTest:
    """The Calibrate page, opened once."""
    at = AppTest.from_file(str(APP), default_timeout=900)
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


def _set(at, kind, key, value):
    _w(at, kind, key).set_value(value)
    at.run()
    return _ok(at)


def _validate(at=None):
    return _go(at or _app(), VALIDATE)


def _add_config(at, name=CONFIG):
    _set(at, "selectbox", "val_pick_config", name)
    return _click(at, "val_add_config")


def _add_snapshot(at, stem="v2.0.0"):
    _set(at, "selectbox", "val_pick_snapshot", stem)
    return _click(at, "val_add_snapshot")


def _defaults_and_track(at=None):
    """T6's state: Defaults × params-track, run on the 47 train tracks."""
    at = _validate(at)
    _click(at, "val_add_defaults")
    _add_config(at)
    return _click(at, "val_run")


def _option_ids(ms) -> list[str]:
    """A multiselect's options are shown as "id (source, …)"; the id."""
    return [str(o).split(" ")[0] for o in ms.options]


def _n_images(at) -> int:
    return len(at.get("image")) + len(at.get("imgs"))


def _frames(at):
    return [df.value for df in at.dataframe]


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
            opts = list(getattr(e, "options", None) or [])
            out += [str(o) for o in opts]
            if kind == "multiselect":
                out += [str(v) for v in (e.value or [])]
            if kind == "text_area":
                out.append(str(e.value))
    out += [str(e.label) for e in at.expander]
    for f in _frames(at):
        out += [str(i) for i in f.index] + [str(c) for c in f.columns]
        out += [str(v) for v in f.to_numpy().ravel()]
    for kind in ("file_uploader", "page_link", "toggle"):
        for e in at.get(kind):
            proto = getattr(e, "proto", None)
            for attr in ("label", "help"):
                if proto is not None and getattr(proto, attr, ""):
                    out.append(str(getattr(proto, attr)))
    return out


def _ids_found(texts, ids) -> set[str]:
    pats = {i: re.compile(r"(?<![A-Za-z0-9])" + re.escape(i) + r"(?![A-Za-z0-9])")
            for i in ids}
    return {i for i, p in pats.items() if any(p.search(t) for t in texts)}


def _words_found(texts) -> set[str]:
    found = set()
    for t in texts:
        t = re.sub(r"not a score", "", t, flags=re.I)
        for w in WORDS:
            if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", t, re.I):
                found.add(w)
    return found


def _main_sequence(at) -> list[tuple[str, str]]:
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


class _Counter:
    def __init__(self, monkeypatch):
        self.n = 0
        real = cc.run_cell

        def counted(doc, series):
            self.n += 1
            return real(doc, series)
        monkeypatch.setattr(cc, "run_cell", counted)


def _train_ids():
    return sorted(vc.load_population(False)["series"])


# ── the menu ──────────────────────────────────────────────────────────────────
def test_validate_is_absent_without_the_developer_key(monkeypatch):
    monkeypatch.delenv("CYCLOPHASER_APP_DEV", raising=False)
    at = _app()
    # Newer AppTest refuses a file that is not a registered page (ValueError);
    # older AppTest lets it through and the default page renders. Either way
    # the Validate page must not (tests/test_app_navigation_apptest.py).
    try:
        at.switch_page(VALIDATE)
    except ValueError:
        pass
    at.run()
    _ok(at)
    assert vt.PAGE_TITLE not in [t.value for t in at.title]
    assert any(b.key == "btn_defaults" for b in at.button)   # Calibrate drew
    monkeypatch.setenv("CYCLOPHASER_APP_DEV", "1")            # control
    at = _validate()
    assert [t.value for t in at.title] == [vt.PAGE_TITLE]


def test_validate_sits_in_the_developer_menu_with_title_and_sentence():
    src = APP.read_text()
    assert '_pages["Developer"] = [_PAGE_LABEL, _PAGE_VALIDATE]' in src
    assert ('_PAGE_VALIDATE.url_path: (validate_tab.WIDGET_STATE_KEYS,\n'
            '                              validate_tab.WIDGET_STATE_PREFIXES)') in src
    at = _validate()
    assert [t.value for t in at.title] == ["Validate against labels"]
    assert any("agree with the manual labels of the train split" in m.value
               and "not a ground truth" in m.value for m in at.markdown)


# ── tracks ────────────────────────────────────────────────────────────────────
def test_the_offered_tracks_are_the_train_split_all_selected():
    at = _validate()
    ms = _w(at, "multiselect", "val_tracks")
    train = _train_ids()
    assert sorted(_option_ids(ms)) == train and len(train) == 47
    assert sorted(ms.value) == train
    assert not set(_option_ids(ms)) & vc.spent_ids()
    assert any(m.value == "**47 of 47** track(s) selected." for m in at.markdown)


def test_all_real_all_synthetic_invert_and_clear():
    at = _validate()
    pop = vc.load_population(False)
    real = sorted(s for s, k in pop["source"].items() if k == "real")
    _click(at, "val_all_real")
    assert sorted(_w(at, "multiselect", "val_tracks").value) == real
    assert len(real) == 35
    _click(at, "val_invert")
    syn = sorted(_w(at, "multiselect", "val_tracks").value)
    assert len(syn) == 12 and not set(syn) & set(real)
    _click(at, "val_clear")
    assert _w(at, "multiselect", "val_tracks").value == []
    _click(at, "val_all_synthetic")
    assert sorted(_w(at, "multiselect", "val_tracks").value) == syn
    _set(at, "multiselect", "val_tracks", real[:3])
    assert sorted(_w(at, "multiselect", "val_tracks").value) == real[:3]
    b = _w(at, "button", "val_invert")
    assert b.label == "Invert selection" and b.help == ct.INVERT_HELP


def test_the_batch_checkbox_adds_its_train_tracks_only():
    at = _validate()
    _w(at, "checkbox", "val_include_batch").check()
    at.run()
    _ok(at)
    pop = vc.load_population(True)
    ms = _w(at, "multiselect", "val_tracks")
    assert len(ms.options) == 54 and sorted(ms.value) == sorted(_option_ids(ms))
    assert set(pop["batch_ids"]) <= set(_option_ids(ms))
    assert not set(_option_ids(ms)) & vc.spent_ids()
    assert any(c.value.startswith("swell_item30: 7 train tracks loaded, 5 of them")
               for c in at.caption)
    _w(at, "checkbox", "val_include_batch").uncheck()
    at.run()
    assert len(_w(at, "multiselect", "val_tracks").options) == 47


# ── configurations ────────────────────────────────────────────────────────────
def test_the_column_sources():
    at = _validate()
    _click(at, "val_add_current")
    _click(at, "val_add_defaults")
    _add_config(at)
    _add_snapshot(at)
    cols = at.session_state["val_columns"]
    assert [c["origin"] for c in cols] == ["current", "defaults", "configs", "snapshot"]
    assert [c["name"] for c in cols] == ["Current settings", "Defaults",
                                         "params-track", "published v2.0.0"]
    live = at.session_state["_bench_live_config"]
    assert cols[0]["doc"] == cc.parameter_sections(live)
    assert cols[1]["doc"] == cc.parameter_sections(
        at.session_state["_compare_defaults_config"])
    text = (bc.CONFIGS_DIR / CONFIG).read_text()
    assert cols[2]["source_sha256"] == bc.sha256_text(text)
    assert cols[3]["doc"] == {} and cols[3]["snapshot_path"].endswith("v2.0.0.json")
    assert _w(at, "selectbox", "val_pick_config").label == \
        "Calibration file (research/labels/configs/)"
    assert _w(at, "selectbox", "val_pick_snapshot").label == \
        "Published release (research/snapshots/)"


def test_six_columns_disable_every_add_control_with_a_visible_reason():
    at = _validate()
    for _ in range(5):
        _click(at, "val_add_current")
    assert not _w(at, "button", "val_add_current").disabled
    assert vt.LIMIT_REASON not in [i.value for i in at.info]
    _click(at, "val_add_defaults")                      # the sixth
    assert len(at.session_state["val_columns"]) == 6
    for key in ("val_add_current", "val_add_defaults"):
        assert _w(at, "button", key).disabled
    for key in ("val_pick_config", "val_pick_snapshot"):
        assert _w(at, "selectbox", key).disabled
    assert at.get("file_uploader")[0].proto.disabled
    assert vt.LIMIT_REASON in [i.value for i in at.info]
    assert vt.LIMIT_REASON == "6 configurations is the limit: remove one to add another."
    _click(at, "val_remove_1")
    assert not _w(at, "button", "val_add_current").disabled


def test_the_card_shows_differences_and_full_provenance(monkeypatch, tmp_path):
    # A calibration file with a historical `evaluation` block, an unknown key,
    # and two absent keys: prominence_relative (filled None, package 0.3) and
    # boundary_padding (pre-filter-fix). Written here and removed below.
    doc = yaml.safe_load((bc.CONFIGS_DIR / CONFIG).read_text())
    del doc["phase_params"]["prominence_relative"]
    del doc["filter_params"]["boundary_padding"]
    doc["phase_params"]["distance"] = 3
    doc["evaluation"] = {"bad_cases": ["20150069"], "bad_cases_count": 1,
                         "total_cyclones": 51}
    path = tmp_path / "cyclophaser_params-older.yaml"
    text = yaml.safe_dump(doc, sort_keys=False)
    path.write_text(text)
    monkeypatch.setattr(bc, "CONFIGS_DIR", tmp_path)
    try:
        at = _validate()
        _click(at, "val_add_defaults")
        _add_config(at, path.name)
    finally:
        path.unlink()
    assert not path.exists()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                          capture_output=True, text=True).stdout.strip()
    sha = bc.sha256_text(text)
    caps = [c.value for c in at.caption]
    assert f"`{sha[:12]}` · code `{head[:12]}`" in caps
    assert f"**1 · sha256 of the file** — `{sha}`" in caps
    assert f"**2 · running code commit** — `{head}`" in caps
    assert "**3 · keys the running code does not read** — `phase_params.distance`" in caps
    assert any(c.startswith("**4 · keys absent, filled by the rule") for c in caps)
    assert any("`phase_params.prominence_relative` = None (package default 0.3) — differs"
               in m.value for m in at.markdown)
    assert any(c.startswith("**5 · pre-filter-fix warning** — This YAML carries no")
               for c in caps)
    assert "**Historical annotation — not a score**" in caps
    assert any(c.startswith("`evaluation.bad_cases_count` = 1 of 51") for c in caps)
    warns = [w.value for w in at.warning]
    assert bc.PRE_FILTER_FIX_SHORT in warns
    filled = config_text.filled_keys_sentence(
        cc.audit(at.session_state["val_columns"][1]["doc"])["filled"])
    # R1 (round 2): the warning is an HTML block with <wbr>, not st.warning
    assert filled and config_text.warning_html(filled) in [m.value for m in at.markdown]
    lines = [m.value.replace("<wbr>", "") for m in at.markdown
             if "(reference: " in m.value]
    assert any("phase_params.prominence_relative</code>: '—' (reference: 0.3)" in ln
               or "phase_params.prominence_relative</code>: None (reference: 0.3)" in ln
               for ln in lines), lines
    # the snapshot card: its own provenance, no parameters to compare
    _add_snapshot(at)
    caps = [c.value for c in at.caption]
    assert "A published release: no parameters of its own to compare." in caps
    assert any(c.startswith("**3 · published release** — Frozen reference column")
               for c in caps)


def test_edit_marks_the_card_edited_in_session_and_remove():
    at = _validate()
    _click(at, "val_add_defaults")
    _click(at, "val_add_current")
    doc = at.session_state["val_columns"][1]["doc"]
    _set(at, "text_area", "val_edit_2", "filter_params: [unclosed")
    _click(at, "val_apply_2")
    assert any(e.value.startswith("Not applied: Invalid YAML") for e in at.error)
    new = {**doc, "filter_params": {**doc["filter_params"], "cutoff_high": 30}}
    _set(at, "text_area", "val_edit_2", yaml.safe_dump(new))
    _click(at, "val_apply_2")
    col = at.session_state["val_columns"][1]
    assert col["edited"] and col["doc"]["filter_params"]["cutoff_high"] == 30
    caps = [c.value for c in at.caption]
    assert "Edited on this page." in caps
    assert "**1 · sha256 of the configuration as added** — edited in session" in caps
    assert any(c.startswith("`edited in session` · code `") for c in caps)
    assert any("filter_<wbr>params.<wbr>cutoff_<wbr>high</code>: 30 (reference: 18)"
               in m.value for m in at.markdown)
    _click(at, "val_remove_1")
    assert [c["name"] for c in at.session_state["val_columns"]] == ["Current settings"]
    assert _w(at, "selectbox", "val_reference").value == "Current settings"


def test_the_reference_selector_lists_columns_only_and_tops_the_results():
    at = _validate()
    _click(at, "val_add_defaults")
    _add_config(at)
    for state in ("before", "after"):
        sel = _w(at, "selectbox", "val_reference")
        assert list(sel.options) == ["Defaults", "params-track"]
        seq = _main_sequence(at)
        results = next(i for i, (k, v) in enumerate(seq) if v == "4 · Results")
        pos = seq.index(("selectbox", "val_reference"))
        assert pos > results
        assert not any(k == "subheader" for k, _v in seq[results + 1:pos])
        if state == "after":
            agr = next(i for i, (k, v) in enumerate(seq)
                       if v == "#### Agreement with manual labels")
            assert pos < agr
        else:
            _click(at, "val_run")
    assert "Manual label" not in _w(at, "selectbox", "val_reference").options


def test_run_blocked_says_why_in_visible_text():
    at = _validate()
    assert _w(at, "button", "val_run").disabled
    assert "To run, add at least one configuration." in [i.value for i in at.info]
    _click(at, "val_add_defaults")
    _click(at, "val_clear")
    assert _w(at, "button", "val_run").disabled
    assert "To run, select at least one track." in [i.value for i in at.info]
    _click(at, "val_all_real")
    assert not _w(at, "button", "val_run").disabled


def test_nothing_recomputes_on_edit_and_the_cache_holds_across_runs(monkeypatch):
    st.cache_data.clear()
    count = _Counter(monkeypatch)
    at = _defaults_and_track()
    assert count.n == 2 * 47
    _click(at, "val_run")
    assert count.n == 2 * 47                           # cached across runs
    doc = at.session_state["val_columns"][0]["doc"]
    new = {**doc, "filter_params": {**doc["filter_params"], "cutoff_high": 30}}
    _set(at, "text_area", "val_edit_1", yaml.safe_dump(new))
    _click(at, "val_apply_1")
    assert count.n == 2 * 47                           # nothing on edit
    assert any(w.value.startswith("Results out of date") for w in at.warning)
    _click(at, "val_run")
    assert count.n == 3 * 47                           # only the edited column
    assert not any(w.value.startswith("Results out of date") for w in at.warning)


# ── agreement ─────────────────────────────────────────────────────────────────
def test_train_block_shows_both_instruments_with_set_and_n():
    at = _defaults_and_track()
    md = [m.value for m in at.markdown]
    assert "#### Agreement with manual labels" in md
    assert "##### Train — n = 47" in md
    assert not any(m.startswith("##### Adjudicated") for m in md)
    assert f"**Sequence** · instrument `{bc.SEQUENCE_INSTRUMENT}` · train, n = 47" in md
    assert f"**Mature** · instrument `{bc.MATURE_INSTRUMENT}` · train, n = 47" in md
    assert vt.INSTRUMENTS_NOTE in [c.value for c in at.caption]
    assert "never added together (research/labels/README.md)" in vt.INSTRUMENTS_NOTE
    seq = next(f for f in _frames(at) if any("Sequence agrees" in i for i in f.index))
    mat = next(f for f in _frames(at) if any("Mature paired" in i for i in f.index))
    assert list(seq.index) == [
        "Sequence agrees with label (train, n = 47)",
        "Boundaries within the label's tolerance (train, n = 47)",
        "Boundaries the label marks unsure, not compared (train, n = 47)"]
    assert list(mat.index) == ["Mature paired within margin 6 (train, n = 47)"]
    assert list(seq.columns) == list(mat.columns) == ["Defaults", "params-track"]
    res = at.session_state["_val_results"]
    for c in res["columns"]:
        m = vc.agreement(res["cells"][c["cid"]], res["labels"], res["ids"], [])
        s, mm = m["train"]["sequence"], m["train"]["mature"]
        assert seq[c["name"]].iloc[0] == f"{s['n_sequence_match']} of {s['n_series']}"
        assert seq[c["name"]].iloc[1] == f"{s['n_boundaries_hit']} of {s['n_boundaries']}"
        assert mat[c["name"]].iloc[0] == f"{mm['n_hit']} of {mm['n']}"


def test_validate_numbers_equal_the_benchmark_train_table():
    at = _validate()
    _click(at, "val_add_current")
    _add_config(at)
    _click(at, "val_run")
    seq = next(f for f in _frames(at) if any("Sequence agrees" in i for i in f.index))
    mat = next(f for f in _frames(at) if any("Mature paired" in i for i in f.index))
    _go(at, BENCHMARK)
    _click(at, "bench_pick_train")
    _click(at, "bench_add_sidebar")
    _set(at, "selectbox", "bench_pick_config", CONFIG)
    _click(at, "bench_add_config")
    _click(at, "bench_run")
    bench = next(f for f in _frames(at) if "Sequence match" in list(f.index))
    assert len(at.session_state["bench_selected_ids"]) == 47
    for vname, bname in (("Current settings", "sidebar #1"),
                         ("params-track", "params-track")):
        assert seq[vname].iloc[0].replace(" of ", "/") == bench[bname]["Sequence match"]
        assert seq[vname].iloc[1].replace(" of ", "/") == \
            bench[bname]["Boundaries within margin"]
        assert mat[vname].iloc[0].replace(" of ", "/") == bench[bname]["Mature paired"]


def test_adjudicated_block_only_with_the_batch_and_never_pooled():
    at = _validate()
    _w(at, "checkbox", "val_include_batch").check()
    at.run()
    _click(at, "val_add_current")
    _click(at, "val_run")
    md = [m.value for m in at.markdown]
    assert "##### Train — n = 49" in md and "##### Adjudicated — n = 5" in md
    assert f"**Sequence** · instrument `{bc.SEQUENCE_INSTRUMENT}` · adjudicated, n = 5" in md
    idx = [i for f in _frames(at) for i in f.index]
    assert "Sequence agrees with label (adjudicated, n = 5)" in idx
    assert "Sequence agrees with label (train, n = 49)" in idx
    assert not any("n = 54" in t for t in md + idx)
    res = at.session_state["_val_results"]
    m = vc.agreement(res["cells"][1], res["labels"], res["ids"], res["adjudicated"])
    seq = [f for f in _frames(at) if any("Sequence agrees" in i for i in f.index)]
    assert seq[0]["Current settings"].iloc[0] == \
        f"{m['train']['sequence']['n_sequence_match']} of {m['train']['sequence']['n_series']}"
    assert seq[1]["Current settings"].iloc[0] == \
        f"{m['adjudicated']['sequence']['n_sequence_match']} of 5"
    assert m["train"]["sequence"]["n_series"] == 49


def test_disagreeing_tracks_listed_per_column_and_instrument():
    at = _defaults_and_track()
    res = at.session_state["_val_results"]
    labels = [e.label for e in at.expander]
    for c in res["columns"]:
        d = vc.disagreements(res["cells"][c["cid"]], res["labels"], res["ids"])
        # R2: one count per instrument, nothing that pools the two
        head = (f"Tracks that disagree with the label — {c['name']} (train, n = 47) · "
                f"sequence: {len(d['sequence_differs'])} differ, "
                f"{len(d['outside_tolerance'])} with a boundary outside its tolerance · "
                f"mature: {len(d['mature'])} not within the margin")
        assert head in labels, (head, labels)
        assert d["sequence_differs"] and d["mature"]    # control: there are lists
    assert not any(re.search(r"\): \d+$", lab) for lab in labels)
    md = [m.value for m in at.markdown if m.value.startswith("**Sequence instrument**")]
    assert len(md) == 2
    assert all("sequence differs from label:" in m and "**Mature instrument**" in m
               for m in md)


# ── per track ─────────────────────────────────────────────────────────────────
def test_per_track_label_panel_first_notes_layouts_filter_and_pages(monkeypatch):
    order: list[str] = []
    real_label, real_cell, real_stacked = vt._label_png, ct._cell_png, vt._stacked_png
    stacked_calls: list[tuple] = []

    def label_png(values, runs, spans):
        order.append("label")
        return real_label(values, runs, spans)

    def cell_png(values, runs, title, z):
        order.append(title)
        return real_cell(values, runs, title, z)

    def stacked_png(values, panels, tolerances):
        stacked_calls.append((panels, tolerances))
        return real_stacked(values, panels, tolerances)
    monkeypatch.setattr(vt, "_label_png", label_png)
    monkeypatch.setattr(ct, "_cell_png", cell_png)
    monkeypatch.setattr(vt, "_stacked_png", stacked_png)

    at = _defaults_and_track()
    assert _w(at, "toggle", "val_show_label").value is True     # on by default
    assert _n_images(at) == 12 * 3
    assert order[:3] == ["label", "Defaults", "params-track"]
    assert order == ["label", "Defaults", "params-track"] * 12
    caps = [c.value for c in at.caption]
    assert any(c.startswith("Label panel: hatched band") for c in caps)
    assert {"sequence agrees with label", "sequence differs from label"} <= set(caps)
    assert any(c.startswith("mature ") and c.endswith("vs label (margin 6)")
               for c in caps)
    _w(at, "toggle", "val_show_label").set_value(False)
    at.run()
    assert _n_images(at) == 12 * 2
    _w(at, "toggle", "val_show_label").set_value(True)
    at.run()
    _set(at, "radio", "val_figure_layout", "Stacked")
    assert _n_images(at) == 12
    panels, tols = stacked_calls[-1]
    assert panels[0][0] == "label" and tols[0] and tols[1:] == (None, None)
    res = at.session_state["_val_results"]
    sid = res["ids"][11]
    assert tols[0] == vc.tolerance_spans(res["labels"][sid])
    assert any(c.startswith("**Defaults** — sequence ") for c in
               [c.value for c in at.caption])
    # pages: 47 tracks, 12 per page
    assert any("Page <b>1</b> of 4" in m.value for m in at.markdown)
    _click(at, "val_next")
    assert any("Page <b>2</b> of 4" in m.value for m in at.markdown)
    # the filter
    _w(at, "checkbox", "val_only_disagreeing").check()
    at.run()
    per_col = [vc.disagreements(res["cells"][c["cid"]], res["labels"], res["ids"])
               for c in res["columns"]]
    n_dis = sum(1 for s in res["ids"] if vc.disagrees(per_col, s))
    assert 0 < n_dis < 47
    assert any(c.value.startswith(f"{n_dis} of the 47 selected track(s) disagree")
               for c in at.caption)
    assert _w(at, "checkbox", "val_only_disagreeing").label == vt.FILTER_LABEL


def test_the_validate_state_survives_a_trip_to_calibrate():
    at = _defaults_and_track()
    ids = _train_ids()
    _set(at, "selectbox", "val_reference", "params-track")
    _set(at, "radio", "val_figure_layout", "Stacked")
    _set(at, "toggle", "val_show_label", False)
    _w(at, "checkbox", "val_only_disagreeing").check()
    at.run()
    _set(at, "selectbox", "val_page_size", 24)
    _set(at, "multiselect", "val_tracks", ids[:5])
    _w(at, "checkbox", "val_include_batch").check()
    at.run()
    keys = ("val_reference", "val_figure_layout", "val_show_label",
            "val_only_disagreeing", "val_page_size", "val_tracks",
            "val_include_batch", "val_columns", "_val_results")
    before = {k: at.session_state[k] for k in keys}
    assert len(before["val_tracks"]) == 5 + 7           # the batch joined
    _go(at, CALIBRATE)
    _go(at, VALIDATE)
    assert {k: at.session_state[k] for k in keys} == before
    assert _w(at, "selectbox", "val_reference").value == "params-track"
    assert _w(at, "radio", "val_figure_layout").value == "Stacked"
    assert _w(at, "toggle", "val_show_label").value is False
    for k in vt.WIDGET_STATE_KEYS:
        assert vt.KEEP_PREFIX + k in at.session_state, k


# ── e2 ────────────────────────────────────────────────────────────────────────
def test_e2_no_test_id_and_no_forbidden_word_anywhere():
    spent = vc.spent_ids()
    texts: list[str] = []
    at = _validate()
    texts += _texts(at)                                 # no columns
    _click(at, "val_add_defaults")
    _add_config(at)
    _add_snapshot(at)
    _click(at, "val_run")
    texts += _texts(at)                                 # results, side by side
    _set(at, "radio", "val_figure_layout", "Stacked")
    _w(at, "checkbox", "val_only_disagreeing").check()
    at.run()
    texts += _texts(at)                                 # stacked, filtered
    _w(at, "checkbox", "val_include_batch").check()
    at.run()
    texts += _texts(at)                                 # batch on, stale
    _click(at, "val_run")
    texts += _texts(at)                                 # batch results
    _click(at, "val_invert")
    texts += _texts(at)                                 # inverted, stale
    assert len(texts) > 500
    assert _ids_found(texts, spent) == set()
    assert _words_found(texts) == set()


def test_e2_the_scanners_find_planted_terms_on_the_benchmark_page():
    spent = vc.spent_ids()
    at = _go(_app(), BENCHMARK)
    _set(at, "radio", "bench_mode", "Exploration")
    found = _ids_found(_texts(at), spent)
    assert len(found) >= 16, found                      # the test ids are offered there
    _set(at, "radio", "bench_mode", "Validation")
    _click(at, "bench_pick_synth")
    _click(at, "bench_add_sidebar")
    _click(at, "bench_run")
    assert "hit rate" in _words_found(_texts(at))
    assert _words_found(["Accuracy of x", "a Score.", "not a score", "scores",
                         "score_phase_sequences"]) == {"accuracy", "score"}
    assert _ids_found(["id 20150069.", "x201500690"], {"20150069"}) == {"20150069"}


# ── shared with the Compare page ──────────────────────────────────────────────
def test_relative_table_and_per_configuration_block_match_compare():
    src = (APP_DIR / "validate_tab.py").read_text()
    assert "ct._render_relative(run_cols, cells, ids, ref_run)" in src
    assert "ct._render_per_column(run_cols, cells, ids" in src
    at = _defaults_and_track()
    res = at.session_state["_val_results"]
    rel = next(f for f in _frames(at) if "Sequence changed" in list(f.index))
    m = cc.relative(res["cells"][2], res["cells"][1], res["ids"])
    assert rel["params-track"]["Sequence changed"] == \
        f"{m['n_sequence_changed']} of {m['n_compared']}"
    assert any(m.value == "#### Relative to Defaults" for m in at.markdown)
    # the same table, row for row, on the Compare page
    cmp = AppTest.from_file(str(APP), default_timeout=900)
    cmp.run()
    _click(cmp, "btn_example")
    _go(cmp, COMPARE)
    _click(cmp, "cmp_add_current")
    _click(cmp, "cmp_add_defaults")
    _click(cmp, "cmp_run")
    crel = next(f for f in _frames(cmp) if "Sequence changed" in list(f.index))
    assert list(crel.index) == list(rel.index)
    cper = next(f for f in _frames(cmp) if any("Incipient absent" in str(i)
                                               for i in f.index))
    vper = next(f for f in _frames(at) if any("Incipient absent" in str(i)
                                              for i in f.index))
    assert list(cper.index) == list(vper.index)


def test_card_format_and_filled_warning_shared_by_both_pages():
    for name in ("compare_tab.py", "validate_tab.py"):
        src = (APP_DIR / name).read_text()
        assert "config_text.differences_html(diffs)" in src
        assert "st.markdown(config_text.warning_html(filled), unsafe_allow_html=True)" in src
        assert "config_text.warning_html(\n" in src             # the ignored-keys one
        assert "→" not in src.split("def _differences_html")[-1].split("def _legend")[0]
    assert config_text.differences_html({"phase_params.prominence_relative": (None, 0.3)}) \
        .count("(reference: 0.3)") == 1
    s = config_text.filled_keys_sentence([("phase_params.prominence_relative", None)])
    b = config_text.warning_html(s)
    assert "phase_<wbr>params.<wbr>prominence_<wbr>relative=None" in b
    assert "default 0.3)" in b                         # a number is not broken
    assert re.sub(r"<[^>]+>", "", b) == s              # no character added
    # on both pages: a column without prominence_relative, through Edit
    for page, add, edit, apply in ((COMPARE, "cmp_add_defaults", "cmp_edit_1", "cmp_apply_1"),
                                   (VALIDATE, "val_add_defaults", "val_edit_1", "val_apply_1")):
        at = _app()
        _click(at, "btn_example")
        _go(at, page)
        _click(at, add)
        doc = yaml.safe_load(_w(at, "text_area", edit).value)
        del doc["phase_params"]["prominence_relative"]
        _set(at, "text_area", edit, yaml.safe_dump(doc))
        _click(at, apply)
        assert b in [m.value for m in at.markdown], page
        assert not any("absent from this file" in w.value for w in at.warning), page


# ── round 2 (checkpoint corrections) ──────────────────────────────────────────
def _drop_key_through_edit(at, edit, apply, extra=None):
    """Edit the first column: no prominence_relative (filled), plus `extra`."""
    doc = yaml.safe_load(_w(at, "text_area", edit).value)
    del doc["phase_params"]["prominence_relative"]
    doc["phase_params"].update(extra or {})
    _set(at, "text_area", edit, yaml.safe_dump(doc))
    return _click(at, apply)


def test_no_rendered_text_contains_a_zero_width_space():
    zw = "\u200b"
    for name in ("compare_tab.py", "validate_tab.py", "config_text.py"):
        assert zw not in (APP_DIR / name).read_text(), name
    texts: list[str] = []
    at = _app()
    _click(at, "btn_example")
    _go(at, COMPARE)
    _click(at, "cmp_add_defaults")
    _click(at, "cmp_add_current")
    _drop_key_through_edit(at, "cmp_edit_1", "cmp_apply_1", {"distance": 3})
    _click(at, "cmp_run")
    texts += _texts(at)
    _go(at, VALIDATE)
    _click(at, "val_add_defaults")
    _add_snapshot(at)
    _drop_key_through_edit(at, "val_edit_1", "val_apply_1", {"distance": 3})
    _click(at, "val_run")
    texts += _texts(at)
    joined = "\n".join(texts)
    assert "absent from this file were filled" in joined          # the warnings are scanned
    assert "Ignored keys: phase_" in joined
    assert not [t for t in texts if zw in t]
    assert [t for t in texts + [f"a{zw}b"] if zw in t] == [f"a{zw}b"]    # control


def test_a_key_copied_from_a_warning_is_the_real_key():
    import html as html_lib
    at = _validate()
    _click(at, "val_add_defaults")
    _drop_key_through_edit(at, "val_edit_1", "val_apply_1")
    block = next(m.value for m in at.markdown if "absent from this file were filled" in m.value)
    copied = html_lib.unescape(re.sub(r"<[^>]+>", "", block))     # what a copy gives
    key = re.search(r"(phase_params\.[A-Za-z_]+)=None", copied).group(1)
    assert key == "phase_params.prominence_relative"
    doc = cc.parameter_sections(at.session_state["val_columns"][0]["doc"])
    section, name = key.split(".", 1)
    doc[section][name] = 0.3                                      # pasted into a YAML
    assert cc.audit(doc)["ignored"] == []
    # control: the round-1 name, with a hidden U+200B, would be ignored
    doc[section].pop(name)
    doc[section]["prominence_\u200brelative"] = 0.3
    assert cc.audit(doc)["ignored"] == ["phase_params.prominence_\u200brelative"]


def test_a_published_release_without_the_batch_tracks_says_so():
    at = _validate()
    _w(at, "checkbox", "val_include_batch").check()
    at.run()
    _click(at, "val_add_current")
    _add_snapshot(at)
    _click(at, "val_run")
    caps = [c.value for c in at.caption]
    note = ("published v2.0.0: {} of {} tracks are not in this snapshot (published "
            "releases cover the 51 + 12 bundled series) and are not counted.")
    assert caps.count(note.format(2, 49)) == 2                   # under both tables
    assert caps.count(note.format(5, 5)) == 2                    # adjudicated block
    assert note.format(7, 54) + ' "Tracks compared" leaves them out.' in caps
    per = next(f for f in _frames(at) if any("Incipient absent" in str(i) for i in f.index))
    assert per["published v2.0.0"]["Not in this snapshot (not counted)"] == "7 of 54"
    assert per["published v2.0.0"]["Detection failed"] == "0 of 54"
    assert per["Current settings"]["Not in this snapshot (not counted)"] == "0 of 54"
    heads = [e.label for e in at.expander if e.label.startswith("Tracks that disagree")]
    assert any(h.startswith("Tracks that disagree with the label — published v2.0.0 "
                            "(train, n = 49)") and h.endswith("not in this snapshot: 2")
               for h in heads), heads
    assert not any("published v2.0.0" in h and "detection failed" in h for h in heads)
    # per track: the batch tracks say so, as a note and not as an error
    batch = vc.load_population(True)["batch_ids"]
    _set(at, "multiselect", "val_tracks", batch)
    _click(at, "val_run")
    assert [c.value for c in at.caption].count("published v2.0.0: not in this snapshot") == 7
    assert not any("not in" in e.value for e in at.error)
    # control: without the batch, no note
    _w(at, "checkbox", "val_include_batch").uncheck()
    at.run()
    _click(at, "val_all_real")
    _click(at, "val_run")
    assert not any("not in this snapshot" in c.value for c in at.caption)


def test_validate_says_results_are_current_after_a_run():
    at = _defaults_and_track()
    current = "Results are current: 2 configuration(s) × 47 track(s)."
    assert current in [c.value for c in at.caption]
    _click(at, "val_add_current")
    assert any(w.value.startswith("Results out of date") for w in at.warning)
    assert current not in [c.value for c in at.caption]
    _click(at, "val_run")
    assert not any(w.value.startswith("Results out of date") for w in at.warning)
    assert "Results are current: 3 configuration(s) × 47 track(s)." in \
        [c.value for c in at.caption]
