"""Streamlit-widget-level tests for the Label tab, via AppTest — no browser.

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


def _label_app() -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    for r in at.radio:
        if set(r.options) >= {"Grid", "Inspector", "Label"}:
            r.set_value("Label")
            break
    at.run()
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
