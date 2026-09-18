"""Streamlit-level tests for the Benchmark tab — public API only.

`filtered_state` and the rest of AppTest's internals are deliberately NOT used:
they broke on a Streamlit upgrade during Front B. Everything here goes through
the documented surface — `at.session_state`, the typed widget collections, and
`at.button`/`at.multiselect`/`at.selectbox` interactions.

What is covered, and why each one is here rather than assumed:

* **N configurations load** — the tab's whole premise is more than one column.
* **Alignment by cyclone** — every column must report on the same series set,
  with the same ids, or the side-by-side reading is a lie.
* **The manual-label overlay is opt-in, both ways** — a display toggle that
  sticks ON is how a blind label stops being blind.
* **No column contaminates another.** This is the one that needs a POSITIVE
  CONTROL, because "the columns are independent" is trivially satisfied by a
  broken implementation that gives every column the same answer. So the test
  first proves the two configurations are actually distinguishable on the
  selected series, then pins each column's output to the configuration that
  column claims — which is precisely the assertion that fails if the two are
  swapped. `test_swapping_the_columns_would_fail_the_pin` states that property
  explicitly by performing the swap and asserting the pin rejects it.
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

# Two configurations from opposite ends of the calibration: params-1 predates
# the filter fix entirely, params-11 is the current reference.
CFG_A = "cyclophaser_params-1.yaml"
CFG_B = "cyclophaser_params-11.yaml"


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


def _add_config_column(at, filename):
    _widget(at, "selectbox", "bench_pick_config").set_value(filename)
    at.run()
    _widget(at, "button", "bench_add_config").click()
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _select_cyclones(at, n=3):
    ms = _widget(at, "multiselect", "bench_ids_widget")
    ms.set_value(list(ms.options[:n]))
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _loaded(at):
    """The tab's published per-column digest — ordinary session state."""
    assert "bench_last_results" in at.session_state
    return at.session_state["bench_last_results"]


def _two_column_app(n_cyclones=3) -> AppTest:
    at = _app()
    _select_cyclones(at, n_cyclones)
    _add_config_column(at, CFG_A)
    _add_config_column(at, CFG_B)
    return at


# ══════════════════════════════════════════════════════════════════════════
# N configurations load, and align by cyclone
# ══════════════════════════════════════════════════════════════════════════

def test_two_configurations_load_as_two_columns():
    at = _two_column_app()
    cols = at.session_state["bench_columns"]
    assert len(cols) == 2, [c["name"] for c in cols]
    assert [c["origin_name"] for c in cols] == [CFG_A, CFG_B]
    assert len(_loaded(at)) == 2


def test_a_third_column_is_added_on_demand_without_disturbing_the_first_two():
    at = _two_column_app()
    before = [dict(c["series"]) for c in _loaded(at)]
    _add_config_column(at, "cyclophaser_params-5.yaml")
    after = _loaded(at)
    assert len(after) == 3
    for i in (0, 1):
        assert after[i]["series"] == before[i], (
            f"column {i} changed when a third column was added")


def test_every_column_reports_on_exactly_the_selected_cyclones():
    """Alignment: same ids, same order, in every column."""
    at = _two_column_app(n_cyclones=4)
    selected = at.session_state["bench_selected_ids"]
    assert len(selected) == 4
    for col in _loaded(at):
        assert list(col["series"]) == list(selected), (
            f"column {col['name']} is not aligned with the selection")


def test_changing_the_selection_repoints_every_column_together():
    at = _two_column_app(n_cyclones=2)
    _select_cyclones(at, 5)
    selected = at.session_state["bench_selected_ids"]
    for col in _loaded(at):
        assert list(col["series"]) == list(selected)


# ══════════════════════════════════════════════════════════════════════════
# the manual-label overlay is opt-in, in both directions
# ══════════════════════════════════════════════════════════════════════════

def test_manual_label_overlay_is_off_by_default():
    at = _two_column_app()
    assert at.session_state["bench_show_labels"] is False


def test_manual_label_overlay_switches_on_and_back_off():
    at = _two_column_app()
    cb = _widget(at, "checkbox", "bench_show_labels")
    cb.set_value(True)
    at.run()
    assert at.session_state["bench_show_labels"] is True
    assert not at.exception, [str(e) for e in at.exception]

    _widget(at, "checkbox", "bench_show_labels").set_value(False)
    at.run()
    assert at.session_state["bench_show_labels"] is False
    assert not at.exception, [str(e) for e in at.exception]


def test_toggling_the_label_overlay_does_not_change_any_column_result():
    """A display switch must not move a measurement."""
    at = _two_column_app()
    before = [dict(c["series"]) for c in _loaded(at)]
    _widget(at, "checkbox", "bench_show_labels").set_value(True)
    at.run()
    after = _loaded(at)
    for i, col in enumerate(after):
        assert col["series"] == before[i], (
            f"column {i} moved when the label overlay was switched on")


# ══════════════════════════════════════════════════════════════════════════
# no column contaminates another — with the positive control
# ══════════════════════════════════════════════════════════════════════════

def _expected_for(filename, ids):
    """Detector output for one config, computed straight from benchmark_core."""
    import yaml
    doc = yaml.safe_load((bc.CONFIGS_DIR / filename).read_text())
    pv, gp = bc.split_config(doc)
    series, _ = bc.load_all_series()
    out = {}
    for sid in ids:
        res = bc.run_series(pv, gp, series[sid])
        out[sid] = (None if res["error"]
                    else [[p, a, b] for p, a, b in res["runs"]])
    return out


def test_the_two_configurations_are_actually_distinguishable():
    """Guards the test below from being vacuous.

    If params-1 and params-11 happened to agree on every selected series, the
    'each column matches its own config' assertion would also hold after a swap
    and would prove nothing. So this is asserted first, separately.
    """
    at = _two_column_app()
    ids = at.session_state["bench_selected_ids"]
    a, b = _loaded(at)
    differing = [s for s in ids if a["series"][s] != b["series"][s]]
    assert differing, (
        "params-1 and params-11 agree on all of "
        f"{ids} — pick series where they differ or the isolation test is vacuous")


def test_each_column_carries_its_own_configuration_not_its_neighbours():
    """The pin: column i's output is what config i produces, run independently."""
    at = _two_column_app()
    ids = at.session_state["bench_selected_ids"]
    a, b = _loaded(at)
    assert a["series"] == _expected_for(CFG_A, ids), "column 0 is not params-1"
    assert b["series"] == _expected_for(CFG_B, ids), "column 1 is not params-11"


def test_swapping_the_columns_would_fail_the_pin():
    """POSITIVE CONTROL — the test above must reject swapped columns.

    Without this, 'each column matches its own config' could be passing for the
    wrong reason. Here the swap is performed deliberately and the same
    comparison is required to reject it.
    """
    at = _two_column_app()
    ids = at.session_state["bench_selected_ids"]
    a, b = _loaded(at)
    exp_a = _expected_for(CFG_A, ids)
    exp_b = _expected_for(CFG_B, ids)

    # the correct pairing holds ...
    assert a["series"] == exp_a and b["series"] == exp_b
    # ... and the swapped one does not.
    assert not (a["series"] == exp_b and b["series"] == exp_a), (
        "swapped columns satisfied the pin — the pin cannot detect contamination")


def test_editing_one_column_leaves_the_other_untouched():
    """Editing marks only the edited column, and moves only its result."""
    at = _two_column_app()
    before = [dict(c["series"]) for c in _loaded(at)]
    cid = at.session_state["bench_columns"][0]["cid"]

    edited_yaml = (bc.CONFIGS_DIR / CFG_B).read_text()
    _widget(at, "text_area", f"bench_edit_{cid}").set_value(edited_yaml)
    at.run()
    _widget(at, "button", f"bench_apply_{cid}").click()
    at.run()
    assert not at.exception, [str(e) for e in at.exception]

    cols = at.session_state["bench_columns"]
    assert cols[0]["edited"] is True, "the edited column is not marked edited"
    assert cols[1]["edited"] is False, "the untouched column was marked edited"

    after = _loaded(at)
    assert after[1]["series"] == before[1], "the untouched column's result moved"
    assert after[0]["series"] == _expected_for(CFG_B, at.session_state["bench_selected_ids"])


def test_an_edited_column_reports_edited_instead_of_a_source_hash():
    """Header item 1: a session edit must not keep advertising the file's hash."""
    at = _two_column_app()
    cid = at.session_state["bench_columns"][0]["cid"]
    _widget(at, "text_area", f"bench_edit_{cid}").set_value(
        (bc.CONFIGS_DIR / CFG_B).read_text())
    at.run()
    _widget(at, "button", f"bench_apply_{cid}").click()
    at.run()
    captions = [c.value for c in at.caption]
    assert any("editado na sessão" in c for c in captions), (
        "no column advertises itself as edited")


def test_removing_a_column_leaves_the_others_intact():
    at = _two_column_app()
    before = _loaded(at)[1]["series"]
    cid = at.session_state["bench_columns"][0]["cid"]
    _widget(at, "button", f"bench_del_{cid}").click()
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    remaining = _loaded(at)
    assert len(remaining) == 1
    assert remaining[0]["series"] == before
