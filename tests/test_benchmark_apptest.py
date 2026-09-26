"""Streamlit-level tests for the Benchmark tab — public API only.

`filtered_state` and the rest of AppTest's internals are deliberately NOT used:
they broke on a Streamlit upgrade during Front B. Everything here goes through
the documented surface — `at.session_state`, the typed widget collections, and
`at.button` / `at.multiselect` / `at.selectbox` / `at.radio` interactions.

What is covered, and why each one is here rather than assumed:

* **N configurations load** — the tab's whole premise is more than one column.
* **Alignment by cyclone** — every column must report on the same series set,
  with the same ids, or the side-by-side reading is a lie.
* **The manual-label overlay is opt-in, both ways** — a display toggle that
  sticks ON is how a blind label stops being blind.
* **No column contaminates another.** This needs a POSITIVE CONTROL, because
  "the columns are independent" is trivially satisfied by a broken
  implementation that gives every column the same answer. So the tests first
  prove the two configurations are distinguishable on the selected series, then
  pin each column's output to the configuration it claims — the assertion that
  fails if the two are swapped — and `test_swapping_the_columns_would_fail_the_pin`
  performs the swap and requires the pin to reject it.
* **A row without a manual label never produces a scoring number**, in either
  mode. This gets its own positive control too
  (`test_the_unlabelled_guard_would_catch_a_leak`), because "no score appeared"
  is also what a metric that silently returns zero looks like.

Results are produced by an explicit **Run**; nothing recomputes on edit. Every
helper below therefore runs before asserting on results.
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


def _has(at, kind, key) -> bool:
    return any(w.key == key for w in getattr(at, kind))


def _add_config_column(at, filename):
    _widget(at, "selectbox", "bench_pick_config").set_value(filename)
    at.run()
    _widget(at, "button", "bench_add_config").click()
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _select(at, ids):
    _widget(at, "multiselect", "bench_ids_widget").set_value(list(ids))
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _run(at):
    _widget(at, "button", "bench_run").click()
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _loaded(at):
    """The tab's published per-column digest — ordinary session state."""
    assert "bench_last_results" in at.session_state
    return at.session_state["bench_last_results"]


def _two_column_app(n_cyclones=3, run=True) -> AppTest:
    at = _app()
    ms = _widget(at, "multiselect", "bench_ids_widget")
    _select(at, list(ms.options[:n_cyclones]))
    _add_config_column(at, CFG_A)
    _add_config_column(at, CFG_B)
    if run:
        _run(at)
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
    _run(at)
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
    ms = _widget(at, "multiselect", "bench_ids_widget")
    _select(at, list(ms.options[:5]))
    _run(at)
    selected = at.session_state["bench_selected_ids"]
    for col in _loaded(at):
        assert list(col["series"]) == list(selected)


# ══════════════════════════════════════════════════════════════════════════
# nothing recomputes on edit — Run is explicit
# ══════════════════════════════════════════════════════════════════════════

def test_no_results_exist_before_run():
    at = _app()
    ms = _widget(at, "multiselect", "bench_ids_widget")
    _select(at, list(ms.options[:2]))
    _add_config_column(at, CFG_A)
    assert "bench_last_results" not in at.session_state, (
        "results appeared without Run being pressed")


def test_editing_a_column_after_a_run_marks_the_results_out_of_date():
    at = _two_column_app()
    fp_before = at.session_state["bench_results_fingerprint"]
    cid = at.session_state["bench_columns"][0]["cid"]
    _widget(at, "text_area", f"bench_edit_{cid}").set_value(
        (bc.CONFIGS_DIR / CFG_B).read_text())
    at.run()
    _widget(at, "button", f"bench_apply_{cid}").click()
    at.run()
    # the stored results are the OLD ones; the fingerprint no longer matches
    assert at.session_state["bench_results_fingerprint"] == fp_before
    assert any("out of date" in w.value for w in at.warning), (
        "no out-of-date warning after the configuration changed")


# ══════════════════════════════════════════════════════════════════════════
# mode
# ══════════════════════════════════════════════════════════════════════════

def test_default_mode_is_validation():
    at = _app()
    assert at.session_state["bench_mode"] == "Validation"


def test_exploration_mode_switches_and_persists():
    at = _app()
    _widget(at, "radio", "bench_mode").set_value("Exploration")
    at.run()
    assert at.session_state["bench_mode"] == "Exploration"
    assert not at.exception, [str(e) for e in at.exception]


def test_cyclone_upload_is_offered_only_in_exploration_mode():
    """Validation restricts the selectable sources to the labelled ones."""
    at = _app()
    assert not _has(at, "file_uploader", "bench_data_upload"), (
        "Validation mode offers an unlabelled data source")
    _widget(at, "radio", "bench_mode").set_value("Exploration")
    at.run()
    assert _has(at, "file_uploader", "bench_data_upload"), (
        "Exploration mode does not offer the cyclone upload")


# ══════════════════════════════════════════════════════════════════════════
# the reference column
# ══════════════════════════════════════════════════════════════════════════

def test_reference_defaults_to_the_manual_label_when_labels_exist():
    at = _two_column_app()
    assert at.session_state["bench_reference"] == "Manual label"


def test_reference_can_be_pointed_at_a_configuration_column():
    at = _two_column_app()
    ref = _widget(at, "selectbox", "bench_reference")
    assert "params-11" in ref.options
    ref.set_value("params-11")
    at.run()
    assert at.session_state["bench_reference"] == "params-11"
    assert not at.exception, [str(e) for e in at.exception]


# ══════════════════════════════════════════════════════════════════════════
# figure layout
# ══════════════════════════════════════════════════════════════════════════

def test_figure_layout_defaults_to_side_by_side_and_switches_to_stacked():
    at = _two_column_app(n_cyclones=2)
    assert at.session_state["bench_figure_layout"] == "Side by side"
    _widget(at, "radio", "bench_figure_layout").set_value("Stacked")
    at.run()
    assert at.session_state["bench_figure_layout"] == "Stacked"
    assert not at.exception, [str(e) for e in at.exception]


def test_figure_layout_does_not_change_any_result():
    """Both arrangements show the same data."""
    at = _two_column_app(n_cyclones=2)
    before = [dict(c["series"]) for c in _loaded(at)]
    _widget(at, "radio", "bench_figure_layout").set_value("Stacked")
    at.run()
    after = _loaded(at)
    for i, col in enumerate(after):
        assert col["series"] == before[i]


# ══════════════════════════════════════════════════════════════════════════
# the manual-label overlay is opt-in, in both directions
# ══════════════════════════════════════════════════════════════════════════

def test_manual_label_overlay_is_off_by_default():
    at = _two_column_app()
    assert at.session_state["bench_show_labels"] is False


def test_manual_label_overlay_switches_on_and_back_off():
    at = _two_column_app()
    _widget(at, "checkbox", "bench_show_labels").set_value(True)
    at.run()
    assert at.session_state["bench_show_labels"] is True
    assert not at.exception, [str(e) for e in at.exception]
    _widget(at, "checkbox", "bench_show_labels").set_value(False)
    at.run()
    assert at.session_state["bench_show_labels"] is False
    assert not at.exception, [str(e) for e in at.exception]


def test_toggling_the_label_overlay_does_not_change_any_column_result():
    at = _two_column_app()
    before = [dict(c["series"]) for c in _loaded(at)]
    _widget(at, "checkbox", "bench_show_labels").set_value(True)
    at.run()
    for i, col in enumerate(_loaded(at)):
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
    """Guards the test below from being vacuous."""
    at = _two_column_app()
    ids = at.session_state["bench_selected_ids"]
    a, b = _loaded(at)
    differing = [s for s in ids if a["series"][s] != b["series"][s]]
    assert differing, (
        "params-1 and params-11 agree on all of "
        f"{ids} — pick series where they differ or the isolation test is vacuous")


def test_each_column_carries_its_own_configuration_not_its_neighbours():
    at = _two_column_app()
    ids = at.session_state["bench_selected_ids"]
    a, b = _loaded(at)
    assert a["series"] == _expected_for(CFG_A, ids), "column 0 is not params-1"
    assert b["series"] == _expected_for(CFG_B, ids), "column 1 is not params-11"


def test_swapping_the_columns_would_fail_the_pin():
    """POSITIVE CONTROL — the pin must reject swapped columns."""
    at = _two_column_app()
    ids = at.session_state["bench_selected_ids"]
    a, b = _loaded(at)
    exp_a, exp_b = _expected_for(CFG_A, ids), _expected_for(CFG_B, ids)
    assert a["series"] == exp_a and b["series"] == exp_b
    assert not (a["series"] == exp_b and b["series"] == exp_a), (
        "swapped columns satisfied the pin — the pin cannot detect contamination")


def test_editing_one_column_leaves_the_other_untouched():
    at = _two_column_app()
    before = [dict(c["series"]) for c in _loaded(at)]
    cid = at.session_state["bench_columns"][0]["cid"]
    _widget(at, "text_area", f"bench_edit_{cid}").set_value(
        (bc.CONFIGS_DIR / CFG_B).read_text())
    at.run()
    _widget(at, "button", f"bench_apply_{cid}").click()
    at.run()
    _run(at)
    cols = at.session_state["bench_columns"]
    assert cols[0]["edited"] is True, "the edited column is not marked edited"
    assert cols[1]["edited"] is False, "the untouched column was marked edited"
    after = _loaded(at)
    assert after[1]["series"] == before[1], "the untouched column's result moved"
    assert after[0]["series"] == _expected_for(
        CFG_B, at.session_state["bench_selected_ids"])


def test_an_edited_column_reports_edited_instead_of_a_source_hash():
    at = _two_column_app()
    cid = at.session_state["bench_columns"][0]["cid"]
    _widget(at, "text_area", f"bench_edit_{cid}").set_value(
        (bc.CONFIGS_DIR / CFG_B).read_text())
    at.run()
    _widget(at, "button", f"bench_apply_{cid}").click()
    at.run()
    captions = [c.value for c in at.caption]
    assert any("edited in session" in c for c in captions), (
        "no column advertises itself as edited")


def test_removing_a_column_leaves_the_others_intact():
    at = _two_column_app()
    before = _loaded(at)[1]["series"]
    cid = at.session_state["bench_columns"][0]["cid"]
    _widget(at, "button", f"bench_del_{cid}").click()
    at.run()
    _run(at)
    remaining = _loaded(at)
    assert len(remaining) == 1
    assert remaining[0]["series"] == before


# ══════════════════════════════════════════════════════════════════════════
# no label, no score — with its own positive control
# ══════════════════════════════════════════════════════════════════════════

def _unlabelled_app() -> tuple[AppTest, str, str]:
    """Exploration mode with one uploaded (unlabelled) track beside a labelled one.

    All 63 bundled records are labelled, so the only way to obtain an unlabelled
    row is the Exploration upload — which is exactly the path this exercises.
    The uploaded series is injected through `bench_extra_series`, the same
    session-state entry the file uploader writes to.
    """
    series, _src = bc.load_all_series()
    labelled = sorted(s for s in series if not s.startswith("s"))[0]
    at = _app()
    _widget(at, "radio", "bench_mode").set_value("Exploration")
    at.run()
    at.session_state["bench_extra_series"] = {
        "uploaded_track": [float(x) for x in series[labelled].values]}
    at.run()
    _select(at, [labelled, "uploaded_track"])
    _add_config_column(at, CFG_B)
    _run(at)
    return at, labelled, "uploaded_track"


def test_the_uploaded_row_really_has_no_label():
    """Guards the two tests below from being vacuous."""
    labels = bc.labels_for_display()
    assert "uploaded_track" not in labels


def test_an_unlabelled_row_is_computed_but_never_scored():
    at, labelled, unlabelled = _unlabelled_app()
    col = _loaded(at)[0]
    # it IS run and shown ...
    assert unlabelled in col["series"], "the unlabelled row was not computed"
    assert col["series"][unlabelled], "the unlabelled row produced no phases"
    # ... and it is NOT scored.
    labels = bc.labels_for_display()
    assert bc.scoreable([labelled, unlabelled], labels) == [labelled]
    assert bc.unscoreable([labelled, unlabelled], labels) == [unlabelled]


def test_scoring_counts_only_the_labelled_rows():
    at, labelled, unlabelled = _unlabelled_app()
    labels = bc.labels_for_display()
    runs = {sid: {"runs": [tuple(r) for r in v], "starts": None}
            for sid, v in _loaded(at)[0]["series"].items() if v}
    for sid in runs:
        runs[sid]["starts"] = [(p, a) for p, a, _ in runs[sid]["runs"]]
    seq = bc.sequence_metrics(runs, labels, [labelled, unlabelled])
    mat = bc.mature_metrics(runs, labels, [labelled, unlabelled])
    assert seq["n_series"] == 1, (
        f"sequence metric scored {seq['n_series']} series over one labelled row")
    assert mat["n"] <= 1, (
        f"mature metric scored {mat['n']} series over one labelled row")
    assert all(r["id"] != unlabelled for r in mat["rows"]), (
        "the unlabelled row appears in the mature rows")


def test_the_unlabelled_guard_would_catch_a_leak():
    """POSITIVE CONTROL — the assertions above must be able to fail.

    "No score appeared" is also what a metric that silently returns zero looks
    like. So the same call is repeated against a labels dict that DOES carry the
    unlabelled id: the count must then rise to 2, proving the guard above is
    measuring the gate and not an empty code path.
    """
    at, labelled, unlabelled = _unlabelled_app()
    labels = dict(bc.labels_for_display())
    runs = {sid: {"runs": [tuple(r) for r in v], "starts": None}
            for sid, v in _loaded(at)[0]["series"].items() if v}
    for sid in runs:
        runs[sid]["starts"] = [(p, a) for p, a, _ in runs[sid]["runs"]]

    assert bc.sequence_metrics(runs, labels, [labelled, unlabelled])["n_series"] == 1

    # now pretend the unlabelled row had a label after all
    leaked = dict(labels[labelled])
    leaked["id"] = unlabelled
    labels[unlabelled] = leaked
    assert bc.sequence_metrics(runs, labels, [labelled, unlabelled])["n_series"] == 2, (
        "the sequence metric did not react to an extra label — the guard above "
        "would pass even if unlabelled rows were being scored")


# ══════════════════════════════════════════════════════════════════════════
# the configuration cards belong INSIDE section 3
# ══════════════════════════════════════════════════════════════════════════

def _section(at, prefix):
    for e in at.expander:
        if e.label.startswith(prefix):
            return e
    raise AssertionError(f"no section starting {prefix!r}; "
                         f"have {[e.label for e in at.expander]}")


def test_configuration_cards_render_inside_section_three():
    """The defect this replaced: cards rendered BELOW the section, so collapsing
    '3 · Configurations' hid the section and left the cards orphaned on screen.

    A card's own controls must be descendants of that section — then collapsing
    it hides them, which is what a collapse is supposed to mean.
    """
    at = _two_column_app(n_cyclones=1, run=False)
    sec3 = _section(at, "3 · Configurations")
    inside = {b.key for b in sec3.button if b.key}
    for col in at.session_state["bench_columns"]:
        cid = col["cid"]
        assert f"bench_del_{cid}" in inside, (
            f"column {col['name']}'s Remove button renders outside section 3")
        assert f"bench_apply_{cid}" in inside, (
            f"column {col['name']}'s Apply button renders outside section 3")


def test_run_button_lives_in_section_three_and_results_in_section_four():
    at = _two_column_app(n_cyclones=1)
    assert "bench_run" in {b.key for b in _section(at, "3 · Config").button if b.key}
    sec4 = _section(at, "4 · Results")
    assert any(r.key == "bench_figure_layout" for r in sec4.radio), (
        "the figure-layout control is not inside section 4")


def test_the_individual_pill_list_is_collapsed_by_default():
    """Section 2 shows a summary line and shortcuts; the 63 pills sit behind a
    closed drop-down rather than filling the section."""
    at = _app()
    chooser = _section(at, "Choose individually")
    assert any(m.key == "bench_ids_widget" for m in chooser.multiselect)


def test_switching_back_to_validation_drops_the_unlabelled_rows():
    """Validation offers labelled sources only, so an uploaded track selected in
    Exploration must not be carried into a run that claims to be scored."""
    at, labelled, unlabelled = _unlabelled_app()
    assert unlabelled in at.session_state["bench_selected_ids"]
    _widget(at, "radio", "bench_mode").set_value("Validation")
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert unlabelled not in at.session_state["bench_selected_ids"], (
        "an unlabelled track survived the switch into Validation mode")
    assert labelled in at.session_state["bench_selected_ids"]


# ══════════════════════════════════════════════════════════════════════════
# a disabled control must say what is blocking it
# ══════════════════════════════════════════════════════════════════════════

def _run_blocked_message(at) -> str | None:
    for i in at.info:
        if "to run." in i.value:
            return i.value
    return None


def test_run_is_disabled_and_explains_itself_when_nothing_is_set_up():
    at = _app()
    assert _widget(at, "button", "bench_run").disabled
    msg = _run_blocked_message(at)
    assert msg, "Run is disabled with no explanation"
    assert "configuration" in msg and "cyclone" in msg, msg


def test_run_names_the_missing_configuration():
    at = _app()
    _select(at, ["20150069"])
    assert _widget(at, "button", "bench_run").disabled
    msg = _run_blocked_message(at)
    assert msg and "configuration" in msg, msg
    assert "cyclone" not in msg, (
        f"names a blocker that is already satisfied: {msg}")


def test_run_names_the_missing_selection():
    at = _app()
    _add_config_column(at, CFG_B)
    assert _widget(at, "button", "bench_run").disabled
    msg = _run_blocked_message(at)
    assert msg and "cyclone" in msg, msg
    assert "configuration" not in msg, (
        f"names a blocker that is already satisfied: {msg}")


def test_run_is_enabled_once_both_preconditions_are_met():
    at = _app()
    _select(at, ["20150069"])
    _add_config_column(at, CFG_B)
    assert not _widget(at, "button", "bench_run").disabled
    assert _run_blocked_message(at) is None, "still explaining a blocker"


def test_the_blocked_message_keeps_the_section_name_readable():
    """`.capitalize()` would lowercase the rest and print '2 · data'."""
    at = _app()
    msg = _run_blocked_message(at)
    assert "2 · Data" in msg, msg


# ══════════════════════════════════════════════════════════════════════════
# the mode leak — with its own positive control
# ══════════════════════════════════════════════════════════════════════════

def test_forcing_an_unlabelled_row_back_into_a_validation_run_is_rejected():
    """POSITIVE CONTROL for the mode leak.

    Validation is presented as scored against the manual labels. An uploaded
    track carries no label, so if one survives in a Validation selection it
    reaches a run that claims to be scored and is not.

    The ordinary path is checked first (switching modes prunes it). Then the
    leak is FORCED — the id is written straight back into the selection, which
    is what a stale rerun or a future refactor that drops the pruning would
    produce — and the guard is required to reject it again. Without the forced
    half, this test would pass on an implementation that pruned once by accident
    and never again.
    """
    at, labelled, unlabelled = _unlabelled_app()
    labels = bc.labels_for_display()
    assert unlabelled not in labels, "the fixture is not actually unlabelled"

    # ordinary path: switching to Validation prunes the unlabelled track
    _widget(at, "radio", "bench_mode").set_value("Validation")
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert unlabelled not in at.session_state["bench_selected_ids"]

    # FORCE the leak back into the selection
    at.session_state["bench_selected_ids"] = [labelled, unlabelled]
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert unlabelled not in at.session_state["bench_selected_ids"], (
        "an unlabelled track survived in a Validation selection — it would "
        "enter a run presented as scored")

    # and it must not reach the results of a Validation run either
    _run(at)
    for col in _loaded(at):
        assert unlabelled not in col["series"], (
            f"column {col['name']} ran the unlabelled track in Validation mode")

    # the second line of defence is independent of the pruning: even given both
    # ids, nothing scoreable comes back for the unlabelled one
    assert bc.scoreable([labelled, unlabelled], labels) == [labelled]


def test_the_mode_leak_guard_is_sensitive():
    """The assertion above must be able to fail.

    In Exploration the very same id IS kept and IS run — so the check is
    reacting to the mode, not to an id that could never be selected at all.
    """
    at, labelled, unlabelled = _unlabelled_app()
    assert unlabelled in at.session_state["bench_selected_ids"], (
        "Exploration did not keep the uploaded track, so the Validation "
        "assertion proves nothing")
    assert any(unlabelled in col["series"] for col in _loaded(at)), (
        "Exploration did not run the uploaded track, so the Validation "
        "assertion proves nothing")


# ══════════════════════════════════════════════════════════════════════════
# the baseline card must not be diffed against itself
# ══════════════════════════════════════════════════════════════════════════

def test_the_parameter_baseline_card_is_labelled_not_diffed_against_itself():
    """With the manual label as reference, the first config column becomes the
    parameter baseline. Diffing it against itself printed "No parameter differs
    from params-1" on params-1's own card — true, and unreadable as anything but
    a claim about the configuration."""
    at = _two_column_app(n_cyclones=1, run=False)
    assert at.session_state["bench_reference"] == "Manual label"
    caps = [c.value for c in at.caption]
    assert any("Parameter baseline" in c for c in caps), (
        "the baseline column is not labelled as the baseline")
    assert not any("No parameter differs from **params-1**" in c for c in caps), (
        "the baseline card is still being diffed against itself")


def test_a_non_baseline_card_still_shows_its_differences():
    """Guards the test above from passing by suppressing every diff."""
    at = _two_column_app(n_cyclones=1, run=False)
    caps = [c.value for c in at.caption]
    assert any("Differs from **params-1**" in c for c in caps), (
        "the non-baseline column stopped reporting its differences")


# ══════════════════════════════════════════════════════════════════════════
# item 30c — the column's smoothed series in every cell and stacked panel
# ══════════════════════════════════════════════════════════════════════════

import benchmark_tab as bt  # noqa: E402


def _filtered_lines(fig):
    return [ln for ax in fig.axes for ln in ax.lines
            if ln.get_color() == bt.FILTERED_COLOR]


def _column_z(filename, sid):
    import yaml
    pv, gp = bc.split_config(yaml.safe_load((bc.CONFIGS_DIR / filename).read_text()))
    series, _ = bc.load_all_series()
    res = bc.run_series(pv, gp, series[sid])
    return series[sid], res


def test_the_two_columns_smooth_differently():
    """POSITIVE CONTROL for the two pins below: if both configurations produced
    the same smoothed series, "each cell draws its own column's" would hold for
    a cell drawing the wrong column's."""
    sid = sorted(bc.load_all_series()[0])[0]
    za = _column_z(CFG_A, sid)[1]["z"].to_numpy()
    zb = _column_z(CFG_B, sid)[1]["z"].to_numpy()
    assert abs(za - zb).max() > 1e-7, "the two configs smooth identically here"


def test_each_cell_draws_its_own_columns_smoothed_series():
    sid = sorted(bc.load_all_series()[0])[0]
    raw, res_a = _column_z(CFG_A, sid)
    _, res_b = _column_z(CFG_B, sid)
    values = tuple(float(v) for v in raw.values)
    for res, other in ((res_a, res_b), (res_b, res_a)):
        z = tuple(float(v) for v in res["z"].values)
        fig = bt._cell_figure(values, tuple(res["runs"]), "col", z)
        lines = _filtered_lines(fig)
        assert len(lines) == 1, "a cell must draw exactly one smoothed curve"
        drawn = list(lines[0].get_ydata())
        assert drawn == list(z)
        assert drawn != [float(v) for v in other["z"].values]
        # Grid convention: the smoothed curve on an axis of its own, raw in front.
        raw_ax = next(ax for ax in fig.axes
                      if any(ln.get_color() == bt.RAW_COLOR for ln in ax.lines))
        assert lines[0].axes is not raw_ax
        assert raw_ax.get_zorder() > lines[0].axes.get_zorder()


def test_a_cell_without_a_smoothed_series_draws_raw_only():
    """A frozen-snapshot column carries no `z`; its cell must not invent one."""
    sid = sorted(bc.load_all_series()[0])[0]
    raw, res = _column_z(CFG_A, sid)
    fig = bt._cell_figure(tuple(float(v) for v in raw.values),
                          tuple(res["runs"]), "snapshot", None)
    assert _filtered_lines(fig) == []


def test_each_stacked_panel_draws_its_own_columns_smoothed_series():
    sid = sorted(bc.load_all_series()[0])[0]
    raw, res_a = _column_z(CFG_A, sid)
    _, res_b = _column_z(CFG_B, sid)
    za = tuple(float(v) for v in res_a["z"].values)
    zb = tuple(float(v) for v in res_b["z"].values)
    panels = (("manual label", tuple(res_a["runs"]), None),
              ("A", tuple(res_a["runs"]), za),
              ("B", tuple(res_b["runs"]), zb))
    fig = bt._stacked_figure(tuple(float(v) for v in raw.values), panels)
    lines = _filtered_lines(fig)
    assert [list(ln.get_ydata()) for ln in lines] == [list(za), list(zb)]
    # one twin range for every panel, so a flatter curve reads as flatter
    assert lines[0].axes.get_ylim() == lines[1].axes.get_ylim()


def test_a_run_keeps_each_columns_own_smoothed_series():
    """End to end through the tab: what the cells are drawn from is the
    column's own `z`, computed with that column's filter_params."""
    at = _two_column_app(n_cyclones=1)
    sid = next(iter(_loaded(at)[0]["series"]))
    runs = at.session_state["_bench_runs"]
    for filename, per_col in zip((CFG_A, CFG_B), runs):
        want = _column_z(filename, sid)[1]["z"].to_numpy()
        assert list(per_col[sid]["z"].to_numpy()) == list(want)
    _widget(at, "radio", "bench_figure_layout").set_value("Stacked")
    at.run()
    assert not at.exception, [str(e) for e in at.exception]


# ══════════════════════════════════════════════════════════════════════════
# item 30c — "Include swell_item30 batch"
# ══════════════════════════════════════════════════════════════════════════

BATCH_TEST = {"19930748", "20111118", "19990549"}


def _batch():
    return bc.batch_membership()


def test_the_batch_is_what_split_yaml_records():
    """Guards the tests below from passing on an empty or reshuffled batch."""
    m = _batch()
    assert len(m) == 10
    assert {s for s, v in m.items() if v == "test"} == BATCH_TEST


def test_the_default_population_does_not_contain_the_batch():
    series, _ = bc.load_all_series()
    assert len(series) == 63
    assert not set(_batch()) & set(series)
    assert not set(_batch()) & set(bc.split_membership())


def test_the_batch_is_off_by_default_and_not_selectable():
    at = _app()
    assert at.session_state["bench_include_swell_batch"] is False
    opts = set(_widget(at, "multiselect", "bench_ids_widget").options)
    assert len(opts) == 63
    assert not {o.split(" ")[0] for o in opts} & set(_batch())


def test_the_batch_appears_with_the_control_on_and_goes_with_it_off():
    at = _app()
    _widget(at, "checkbox", "bench_include_swell_batch").set_value(True)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    opts = {o.split(" ")[0] for o in _widget(at, "multiselect", "bench_ids_widget").options}
    assert set(_batch()) <= opts and len(opts) == 73

    _select(at, sorted(_batch()))
    _widget(at, "checkbox", "bench_include_swell_batch").set_value(False)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    opts = {o.split(" ")[0] for o in _widget(at, "multiselect", "bench_ids_widget").options}
    assert len(opts) == 63 and not set(_batch()) & opts
    assert not set(_batch()) & set(at.session_state["bench_selected_ids"]), (
        "batch ids stayed selected after the batch was switched off")


def test_the_split_buttons_treat_the_batch_like_the_split():
    """Train and Test pick the batch's 7 and 3 alongside the 47 and 16 — and,
    as the positive control, not while the batch is off.

    One fresh app per click: pressing Train and then Test in the same session
    empties the selection, a defect that predates item 30c (reproduced on
    99f5a9a) and is not what this test is about."""
    def picked(key, batch):
        at = _app()
        if batch:
            _widget(at, "checkbox", "bench_include_swell_batch").set_value(True)
            at.run()
        _widget(at, "button", key).click()
        at.run()
        assert not at.exception, [str(e) for e in at.exception]
        return set(at.session_state["bench_selected_ids"])

    assert len(picked("bench_pick_train", False)) == 47
    assert len(picked("bench_pick_test", False)) == 16
    train = picked("bench_pick_train", True)
    assert len(train) == 54 and not train & BATCH_TEST
    test = picked("bench_pick_test", True)
    assert len(test) == 19 and BATCH_TEST <= test


def test_the_batch_test_cases_score_only_in_the_test_block():
    """The 3 are scored where the 16 are — the frozen test block — and never
    in the train one. Only the blocks' series counts are read here."""
    at = _app()
    _widget(at, "checkbox", "bench_include_swell_batch").set_value(True)
    at.run()
    _select(at, sorted(_batch()))
    _add_config_column(at, CFG_B)
    _run(at)
    labels = [e.label for e in at.expander]
    assert "Train split — 7 series" in labels, labels
    assert "Test split (frozen) — 3 series" in labels, labels
