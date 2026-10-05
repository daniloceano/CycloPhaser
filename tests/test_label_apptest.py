"""Streamlit-widget-level tests for the Manual labelling page, via AppTest — no
browser. (It was the "Label" display mode of the Calibration tab until the app
redesign's I1 made it a page of its own, behind the developer key.)

`streamlit.testing.v1.AppTest` runs the real app script through Streamlit's
actual session_state/widget-key/rerun machinery, without a browser. It cannot
drive a pointer gesture on the hand-drawn SVG chart component — that needs a
real DOM, which is exactly why tests/test_label_browser.py exists and why
this file does not duplicate anything from it.

What it CAN catch, and what it is used for here, is the class of bug this
whole tab has already been bitten by once: a Streamlit widget with a stable
`key` ignores a changed `value=` on the next render and keeps showing
whatever it last showed the user (see label_tab.py's `_phase_table`
docstring). Two Python-side features added on top of the phase table rely on
getting this right without a live pointer at all:

  * the start/end-unsure checkboxes, where a phase row's "end" and the NEXT
    row's "start" are two on-screen handles onto the SAME stored boundary
    value, and must never be left showing different states;
  * the overlay layer checkboxes, which must be able to be switched on and
    off without perturbing any phase position underneath.

Both are ordinary Python/session_state wiring, not pointer interaction, so
AppTest is the right tool — and, unlike a hand-simulated DOM, it runs the
actual rerun cycle a browser would trigger.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402


LABEL_PAGE = "app_pages/label.py"


def _label_app() -> AppTest:
    """The app on its Manual labelling page, with the developer key on (the
    page is not in the menu without it)."""
    at = AppTest.from_file(str(APP), default_timeout=120)
    at.secrets["developer_mode"] = True
    at.run()
    at.switch_page(LABEL_PAGE).run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _start_unsure(at):
    return sorted((cb for cb in at.checkbox if cb.key and cb.key.startswith("labunsure-")),
                 key=lambda cb: int(cb.key.split("-")[-2]))


def _end_unsure(at):
    return sorted((cb for cb in at.checkbox if cb.key and cb.key.startswith("labendunsure-")),
                 key=lambda cb: int(cb.key.split("-")[-2]))


def _start_idx(at):
    return sorted((nb for nb in at.number_input if nb.key and nb.key.startswith("labstart-")),
                 key=lambda nb: int(nb.key.split("-")[-2]))


# ══════════════════════════════════════════════════════════════════════════
# Start/end-unsure: two on-screen handles, one stored value
# ══════════════════════════════════════════════════════════════════════════

def test_boundary_unsure_reconciles_between_adjacent_rows_both_directions():
    """Ticking row k's END must mirror onto row k+1's START, and back again —
    the same shared boundary, checked from both ends, in both directions."""
    at = _label_app()
    assert len(_end_unsure(at)) >= 2, "need at least two phases for this case"

    # end of row 0 -> start of row 1
    _end_unsure(at)[0].set_value(True)
    at.run()
    assert _start_unsure(at)[1].value is True, (
        "row 1's start-unsure did not pick up row 0's end-unsure")
    assert _end_unsure(at)[0].value is True

    # the reverse direction: start of row 1 -> end of row 0
    _start_unsure(at)[1].set_value(False)
    at.run()
    assert _end_unsure(at)[0].value is False, (
        "row 0's end-unsure did not follow row 1's start-unsure back down")
    assert _start_unsure(at)[1].value is False


def test_row_zero_start_maps_to_open_unsure_and_last_row_end_to_close_unsure():
    """The two edges with no adjacent phase to share a checkbox with: row 0's
    start (there is no row -1) and the last row's end (there is no row N)."""
    at = _label_app()
    su = _start_unsure(at)
    assert su[0].disabled is False, (
        "row 0's start-unsure must be settable now (it is open_unsure), "
        "not permanently disabled the way schema 3's single checkbox was")

    su[0].set_value(True)
    at.run()
    assert _start_unsure(at)[0].value is True

    # Re-fetched fresh: `rev` bumped on the change above, which rebuilds
    # every widget under a new key, and a checkbox handle from before that
    # rerun no longer refers to a live element.
    _end_unsure(at)[-1].set_value(True)
    at.run()
    assert _end_unsure(at)[-1].value is True
    # close_unsure has no adjacent row to mirror onto; every OTHER row's
    # start-unsure must be untouched by it
    assert all(not cb.value for cb in _start_unsure(at)[1:])


# ══════════════════════════════════════════════════════════════════════════
# Overlays must be inert with respect to the phases drawn alongside them
# ══════════════════════════════════════════════════════════════════════════

def test_toggling_overlay_layers_does_not_move_any_phase():
    """The three overlay layers are drawn in the SAME chart as the raw
    series and the phase boundaries; switching them on and off one at a time
    must never perturb a single start_idx."""
    at = _label_app()
    before = [int(nb.value) for nb in _start_idx(at)]

    master = next(cb for cb in at.checkbox
                 if "Show filtered/smoothed overlays" in cb.label)
    master.set_value(True)
    at.run()

    layer_cbs = [cb for cb in at.checkbox if cb.key and cb.key.startswith("lab_overlay__")]
    assert len(layer_cbs) == 3, "expected the three process_vorticity layers"

    for cb in layer_cbs:
        cb.set_value(True)
        at.run()
        now = [int(nb.value) for nb in _start_idx(at)]
        assert now == before, (
            f"toggling {cb.label!r} on moved a phase: {now} != {before}")

    for cb in layer_cbs:
        cb.set_value(False)
        at.run()
        now = [int(nb.value) for nb in _start_idx(at)]
        assert now == before, (
            f"toggling {cb.label!r} off moved a phase: {now} != {before}")


# ══════════════════════════════════════════════════════════════════════════
# Confirmation checkboxes must survive a rerun issued earlier in the script
# ══════════════════════════════════════════════════════════════════════════
#
# A real bug, not a hypothetical: the overwrite/frozen-synthetic confirmation
# checkboxes read `value=False` on every render and relied on Streamlit's own
# widget-key memory to keep them ticked afterward. That memory does not
# survive being skipped for one script pass, and anything that calls
# `st.rerun()` from EARLIER in `render` than these checkboxes skips them for
# exactly one pass — enough to reset them to unticked. Reported as "I tick
# everything and Save stays disabled". The trigger then was the
# Inspection/Labelling switch, retired in I1; the phase table issues the same
# kind of early rerun on every edit, so that is the trigger used now.

def _synthetic_case_index(at) -> int:
    for sb in at.main.selectbox:
        if sb.label == "Jump to case":
            nav = sb
            break
    return next(i for i, o in enumerate(nav.options)
               if "frozen synthetic" in o and "TEST split" not in o)


def _rerun_from_the_phase_table(at) -> None:
    """Two phase-table edits that cancel out; each issues an st.rerun() from
    above the confirmation checkboxes."""
    _end_unsure(at)[0].set_value(True)
    at.run()
    _end_unsure(at)[0].set_value(False)
    at.run()


def test_overwrite_confirmation_survives_an_earlier_rerun():
    at = _label_app()
    for sb in at.main.selectbox:
        if sb.label == "Jump to case":
            sb.set_value(_synthetic_case_index(at))
    at.run()

    ow = next(cb for cb in at.checkbox
             if "Overwrite the existing label" in cb.label)
    ow.set_value(True)
    at.run()
    assert ow.value is True

    _rerun_from_the_phase_table(at)

    ow_after = next(cb for cb in at.checkbox
                   if "Overwrite the existing label" in cb.label)
    assert ow_after.value is True, (
        "the overwrite confirmation reset to unticked after a rerun issued "
        "earlier in the script")


def test_all_three_confirmations_together_enable_save():
    """The exact scenario reported: tick overwrite + both synthetic
    confirmations, with an early rerun in between, and Save must become
    available with no further explanation needed than what's already on
    screen — and with no mode to switch to first (retired in I1)."""
    at = _label_app()
    for sb in at.main.selectbox:
        if sb.label == "Jump to case":
            sb.set_value(_synthetic_case_index(at))
    at.run()

    next(cb for cb in at.checkbox
        if "Overwrite the existing label" in cb.label).set_value(True)
    at.run()
    _rerun_from_the_phase_table(at)
    next(cb for cb in at.checkbox
        if "I understand this is a frozen synthetic case" in cb.label).set_value(True)
    at.run()
    next(cb for cb in at.checkbox
        if "I still want to save a label for it" in cb.label).set_value(True)
    at.run()

    save_btn = next(b for b in at.button if "Save & next" in b.label)
    assert save_btn.disabled is False
    blockers = [c.value for c in at.caption if c.value.startswith("Cannot save yet")]
    assert blockers == []


# ══════════════════════════════════════════════════════════════════════════
# Previous/Next: pure navigation, never a save
# ══════════════════════════════════════════════════════════════════════════

def test_no_incipient_and_remove_last_buttons_are_gone():
    at = _label_app()
    labels = {b.label for b in at.main.button}
    assert "No incipient" not in labels
    assert "－ Remove last" not in labels
    assert "← Back" not in labels
    assert {"◂ Previous", "Next ▸"} <= labels


def test_previous_and_next_move_through_the_queue_without_saving():
    import sys
    sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))
    import labels_core as lc

    before_text = lc.LABELS_PATH.read_text()

    at = _label_app()

    def pos_value(at):
        for sb in at.main.selectbox:
            if sb.label == "Jump to case":
                return sb.value

    start = pos_value(at)
    next(b for b in at.button if b.label == "Next ▸").click()
    at.run()
    after_next = pos_value(at)
    assert after_next != start

    next(b for b in at.button if b.label == "◂ Previous").click()
    at.run()
    after_previous = pos_value(at)
    assert after_previous == start

    assert lc.LABELS_PATH.read_text() == before_text, (
        "Previous/Next must never write to manual_labels.yaml")


# ══════════════════════════════════════════════════════════════════════════
# Overlay scale — "Raw range" by default (2c9ab1d), item 30c's 0-1 kept
# ══════════════════════════════════════════════════════════════════════════

def _scale_radios(at):
    return [r for r in at.radio if r.key and r.key.startswith("lab_overlay_scale__")]


def test_overlay_scale_is_offered_and_defaults_to_the_raw_range():
    at = _label_app()
    radios = _scale_radios(at)
    assert len(radios) == 1 and radios[0].label == "Overlay scale"
    assert list(radios[0].options) == ["Raw range", "Shared 0-1", "Physical"]
    assert radios[0].value == "Raw range"


def test_overlays_are_offered_with_no_mode_to_switch_to():
    """The Inspection/Labelling switch is retired: the overlay controls are on
    the page from the start, and so are the save buttons."""
    at = _label_app()
    assert not any(set(r.options) >= {"Inspection", "Labelling"} for r in at.radio)
    assert any("Show filtered/smoothed overlays" in cb.label for cb in at.checkbox)
    assert {"💾 Save & next", "Save ambiguous"} <= {b.label for b in at.button}


def test_revealing_an_overlay_records_it_and_unblinds_the_case():
    at = _label_app()
    assert any(c.value.startswith("🙈 blind") for c in at.caption)
    next(cb for cb in at.checkbox
         if "Show filtered/smoothed overlays" in cb.label).set_value(True)
    at.run()
    layer = next(cb for cb in at.checkbox
                 if cb.key and cb.key.endswith("__vorticity_smoothed2"))
    sid = layer.key[len("lab_overlay__"):-len("__vorticity_smoothed2")]
    layer.set_value(True)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert at.session_state[f"_lab_overlays_seen__{sid}"] == {"vorticity_smoothed2"}
    assert any(c.value.startswith("👁 overlays revealed") for c in at.caption)


def test_switching_the_overlay_scale_does_not_move_any_phase():
    at = _label_app()
    before = [int(nb.value) for nb in _start_idx(at)]
    next(cb for cb in at.checkbox
         if "Show filtered/smoothed overlays" in cb.label).set_value(True)
    at.run()
    for cb in (cb for cb in at.checkbox if cb.key and cb.key.startswith("lab_overlay__")):
        cb.set_value(True)
        at.run()
    for value in ("Shared 0-1", "Physical", "Raw range"):
        _scale_radios(at)[0].set_value(value)
        at.run()
        assert not at.exception, [str(e) for e in at.exception]
        assert [int(nb.value) for nb in _start_idx(at)] == before


def test_onto_raw_range_maps_the_band_onto_the_raw_min_and_max():
    """Decision (iii) of 2c9ab1d: overlays drawn on the raw series' own range.
    Band 0 lands on the raw minimum, band 1 on the raw maximum, NaN ignored
    for the range exactly as `unit_band` ignores it."""
    import sys

    import numpy as np
    sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))
    import label_tab

    raw = np.array([-3.0, np.nan, 1.0, -1.0])
    got = label_tab.onto_raw_range([0.0, 0.5, 1.0], raw)
    assert got == [-3.0, -1.0, 1.0]
    # the round trip: the raw series' own band maps back onto itself
    fin = raw[np.isfinite(raw)]
    back = label_tab.onto_raw_range(label_tab.unit_band(fin), fin)
    assert np.allclose(back, fin)


def test_the_default_tolerance_input_is_on_the_page_not_in_a_sidebar():
    at = _label_app()
    assert [nb.key for nb in at.main.number_input
            if nb.key == "label_default_tolerance"] == ["label_default_tolerance"]
    assert not any(nb.key == "label_default_tolerance" for nb in at.sidebar.number_input)
    # and none of the Calibrate sidebar is drawn on this page
    assert not at.sidebar.slider and not at.sidebar.number_input


def test_unit_band_matches_the_inspectors_raw_band():
    """label_tab may not import the inspector, so `unit_band` re-writes its
    arithmetic; this pins the two to agree, edge cases included."""
    import sys

    import numpy as np
    sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))
    sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))
    import label_tab
    import layer_inspector as li
    import labels_core as lc

    real = next(iter(lc.load_real_series().values())).to_numpy()
    cases = {
        "real series": real,
        "with NaN": np.where(np.arange(len(real)) % 7 == 0, np.nan, real),
        "flat": np.full(12, 3e-5),
        "all NaN": np.full(5, np.nan),
    }
    for name, a in cases.items():
        want = li.rescaler([a], True)(a)
        got = np.asarray(label_tab.unit_band(a))
        assert np.array_equal(got, want, equal_nan=True), name
    assert min(label_tab.unit_band(real)) == 0.0
    assert max(label_tab.unit_band(real)) == 1.0


# ══════════════════════════════════════════════════════════════════════════
# item 30 part 3 — the VALIDATION batch appears unlabelled, save-once
# ══════════════════════════════════════════════════════════════════════════

def test_the_validation_cases_are_in_the_queue_unlabelled_and_marked():
    val = {"19900808", "19940737", "19960808", "20000821", "19861089"}
    at = _label_app()
    nav = next(sb for sb in at.main.selectbox if sb.label == "Jump to case")
    opts = [o for o in nav.options if any(v in o for v in val)]
    assert len(opts) == 5
    # spent before labelling (item 30 closing, 27 Sept 2026): locked outright
    assert all("[VALIDATION spent — locked]" in o for o in opts), opts
    # appended last: after every other case, the 10 of the swell batch included
    last5 = nav.options[-5:]
    assert {o for o in last5} == set(opts)


def test_a_spent_validation_case_cannot_be_saved_even_once():
    """Item 30 closing: `batches.swell_item30_val` is "spent before labelling".
    Where saving is otherwise allowed, an UNLABELLED validation case has both
    save buttons disabled, and the lock is the ONLY
    blocker named (no overwrite, no synthetic confirmation, no sequence
    problem), so it is the lock that disables them. Nothing is written."""
    import sys
    sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))
    import labels_core as lc
    before = lc.LABELS_PATH.read_text()
    val = {"19900808", "19940737", "19960808", "20000821", "19861089"}
    at = _label_app()
    nav = next(sb for sb in at.main.selectbox if sb.label == "Jump to case")
    idx = next(i for i, o in enumerate(nav.options) if any(v in o for v in val))
    nav.set_value(idx)
    at.run()
    saves = [b for b in at.button if b.label in ("💾 Save & next", "Save ambiguous")]
    assert len(saves) == 2 and all(b.disabled for b in saves)
    blocked = [c.value for c in at.caption if c.value.startswith("Cannot save yet")]
    assert blocked == ["Cannot save yet — this validation case is SPENT (never "
                       "labelled) — saving is blocked, not just discouraged."], blocked
    assert lc.LABELS_PATH.read_text() == before
