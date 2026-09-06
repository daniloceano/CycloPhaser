"""The labelling chart, driven by a real browser against the real app.

Read tests/browser_harness.py first: it explains why this exists rather than a
DOM stub, and what "verified" is allowed to mean here.

The short version. Three deliveries of the drag interaction passed their checks
and worked in nobody's browser, because the checks ran the component's JS against
a simulated DOM and the fault was in the Python that mounts the component. So
every assertion below is made against a value that Streamlit rendered from
`st.session_state` — the phase table — after a real pointer or a real keystroke.
Reading the SVG would prove only that the browser drew something.

The four gestures pinned here are the four that were broken or unprovable:

  1. drag a boundary bar right, and back left again;
  2. drag a tolerance handle to widen the bar, and again to narrow it;
  3. release the pointer OUTSIDE the chart mid-drag — the case `pointerup` on
     the `<svg>` could never see, which lost the edit with no error at all;
  4. drag while Streamlit reruns underneath — a rerender used to destroy and
     rebuild the SVG, taking the listeners and the gesture with it.

Plus the two paths that make a chart failure survivable: the keyboard, and the
table, which is the canonical way to write a label and must move the chart.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests"))

# Playwright, its browser, and Streamlit are TEST-only and hand-installed:
#     pip install playwright && python -m playwright install chromium
# Absent, this module skips whole. It must never be able to fail the package's
# CI, which installs the wheel plus pytest and nothing else.
playwright_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright is not installed (browser tests)")
pytest.importorskip("streamlit", reason="Streamlit not installed (app-only)")

from browser_harness import AppServer, LabelPage  # noqa: E402


def _chromium_present() -> bool:
    try:
        with playwright_api.sync_playwright() as pw:
            return bool(pw.chromium.executable_path) and \
                Path(pw.chromium.executable_path).exists()
    except Exception:
        return False


requires_browser = pytest.mark.skipif(
    not _chromium_present(),
    reason="Chromium is not installed: python -m playwright install chromium")

pytestmark = [requires_browser, pytest.mark.browser]


# ── one server and one browser for the whole module ─────────────────────────
# Booting Streamlit and loading 63 series takes seconds; doing it per test would
# make the suite unrunnable and nobody would run it, which is how the previous
# rounds went unverified.

@pytest.fixture(scope="module")
def server(tmp_path_factory):
    srv = AppServer(tmp_path_factory.mktemp("app") / "streamlit.log").start()
    yield srv
    srv.stop()


@pytest.fixture(scope="module")
def lab(server):
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1100})
        page.set_default_timeout(60_000)
        lp = LabelPage(page).open(server.url)
        yield lp
        browser.close()


@pytest.fixture
def fresh(lab):
    """Put the table into a known state before each test, through the TABLE.

    Deliberately not through the chart: a test whose setup uses the thing under
    test cannot fail honestly.
    """
    lab.set_start_idx(1, 20)
    lab.set_tolerance_idx(1, 4)
    lab.set_start_idx(2, 50)
    lab.set_tolerance_idx(2, 5)
    lab.set_unsure(1, False)
    lab.set_unsure(2, False)
    assert lab.table_state()[1] == (20, 4, False), lab.table_state()
    return lab


# ══════════════════════════════════════════════════════════════════════════════
# 0. The component mounts at all
# ══════════════════════════════════════════════════════════════════════════════

def test_the_chart_component_actually_mounts(lab):
    """The bug that cost three rounds, pinned directly.

    `key=f"lab_chart__{sid}"` made every mount raise BidiComponentInvalidIdError
    (`__` is reserved inside a bidirectional component's id) and the exception
    was swallowed by a static Plotly fallback, so the app drew an undraggable
    picture and reported nothing. This test is the one that would have caught it
    on day one: is the hand-drawn SVG in the document, in a browser, or not.
    """
    assert lab.mount_error() is None, lab.mount_error()
    assert lab.has_chart(), (
        "no #cp-label-chart svg in the page — the component did not mount")
    assert lab.chart_alert() == ""


# Streamlit re-requests a cached figure from the mode you just left and gets a
# 404 for it. Noisy, harmless, and nothing to do with this front — but a test
# that fails on it gets muted, and a muted test is how a real page error would
# get through.
_APP_NOISE = ("Failed to load resource", "Image source error", "/media/")


def test_no_javascript_errors_on_the_page(lab):
    real = [e for e in lab.errors if not any(n in e for n in _APP_NOISE)]
    assert not real, real


def test_the_table_shows_a_row_per_phase(lab):
    assert lab.n_rows() == 4
    assert lab.phase_name(0) == "incipient"
    assert lab.start_idx(0) == 0


# ══════════════════════════════════════════════════════════════════════════════
# ACTION 1 — drag the body of a boundary bar, there and back
# ══════════════════════════════════════════════════════════════════════════════

def test_dragging_a_bar_right_moves_the_boundary_in_python(fresh):
    fresh.drag_boundary(1, 34)
    assert fresh.start_idx(1) == pytest.approx(34, abs=1), fresh.table_state()
    assert fresh.tolerance_idx(1) == 4, "a body drag must not touch the margin"
    assert fresh.start_idx(2) == 50, "it must not disturb its neighbour"


def test_dragging_a_bar_back_left_moves_it_back(fresh):
    fresh.drag_boundary(1, 34)
    assert fresh.start_idx(1) == pytest.approx(34, abs=1)
    fresh.drag_boundary(1, 12)
    assert fresh.start_idx(1) == pytest.approx(12, abs=1), fresh.table_state()


def test_the_same_drag_twice_is_delivered_twice(fresh):
    """The replay guard used to key on the positions, so an identical second
    gesture looked like a stale repeat of the first and was DISCARDED — the bar
    sprang back on its own. The component now sends a monotonic counter."""
    fresh.drag_boundary(1, 30)
    assert fresh.start_idx(1) == pytest.approx(30, abs=1)
    fresh.drag_boundary(1, 15)
    assert fresh.start_idx(1) == pytest.approx(15, abs=1)
    fresh.drag_boundary(1, 30)                      # byte-identical to the first
    assert fresh.start_idx(1) == pytest.approx(30, abs=1), fresh.table_state()


def test_a_bar_cannot_be_dragged_past_its_neighbour(fresh):
    fresh.drag_boundary(1, 90)                      # the next boundary is at 50
    assert fresh.start_idx(1) <= 49, fresh.table_state()
    assert fresh.start_idx(2) == 50


# ══════════════════════════════════════════════════════════════════════════════
# ACTION 2 — drag a tolerance handle, wider and narrower
# ══════════════════════════════════════════════════════════════════════════════

def test_dragging_the_edge_widens_the_margin_in_python(fresh):
    fresh.drag_tolerance(2, 62)                     # boundary at 50 -> |62-50|
    assert fresh.tolerance_idx(2) == pytest.approx(12, abs=1), fresh.table_state()
    assert fresh.start_idx(2) == 50, "widening must not move the boundary"


def test_dragging_the_edge_back_narrows_the_margin(fresh):
    fresh.drag_tolerance(2, 62)
    assert fresh.tolerance_idx(2) == pytest.approx(12, abs=1)
    fresh.drag_tolerance(2, 52)
    assert fresh.tolerance_idx(2) == pytest.approx(2, abs=1), fresh.table_state()
    assert fresh.start_idx(2) == 50


# ══════════════════════════════════════════════════════════════════════════════
# ACTION 3 — let go of the pointer outside the chart
# ══════════════════════════════════════════════════════════════════════════════

def test_releasing_the_pointer_outside_the_svg_still_commits(fresh):
    """`pointerup` was bound to the `<svg>`, so a release anywhere else was never
    delivered: `finish()` never ran, `setTriggerValue` was never called, and the
    edit vanished WITHOUT ANY ERROR. The listeners are on `window` now.

    This is the gesture a person makes constantly — overshoot the plot while
    dragging a boundary toward the end of the series and let go — so it failing
    silently is most of what "dragging doesn't work" meant.
    """
    fresh.drag_boundary(1, 40, release_outside=True)
    assert fresh.start_idx(1) == pytest.approx(40, abs=2), (
        f"the edit was lost when the pointer left the chart: {fresh.table_state()}")
    assert fresh.chart_alert() == ""


# ══════════════════════════════════════════════════════════════════════════════
# ACTION 4 — drag through a Streamlit rerun
# ══════════════════════════════════════════════════════════════════════════════

def test_a_drag_survives_a_rerender_underneath_it(fresh):
    """Any sidebar widget reruns the script, and the component's JS runs again
    with it. It used to `prev.remove()` and rebuild the SVG from scratch, which
    destroyed the listeners and the in-flight gesture. The node is preserved now,
    and a rerender never overwrites phases while a drag is live.
    """
    fresh.drag_boundary(1, 38, before_release=fresh.poke_sidebar)
    assert fresh.has_chart(), "the chart disappeared during the rerender"
    assert fresh.start_idx(1) == pytest.approx(38, abs=2), (
        f"the rerender ate the drag: {fresh.table_state()}")


def test_the_chart_survives_a_rerun_with_no_drag_in_flight(fresh):
    fresh.drag_boundary(1, 25)
    fresh.poke_sidebar()
    fresh.settle()
    assert fresh.has_chart()
    assert fresh.start_idx(1) == pytest.approx(25, abs=1), (
        "the value did not survive a server rerender, so it never reached Python")


# ══════════════════════════════════════════════════════════════════════════════
# The keyboard — the path that works when the pointer does not
# ══════════════════════════════════════════════════════════════════════════════

def test_arrow_keys_move_the_selected_boundary_one_step(fresh):
    fresh.click_boundary(1)
    before = fresh.start_idx(1)
    fresh.press("ArrowRight")
    assert fresh.start_idx(1) == before + 1, fresh.table_state()
    fresh.press("ArrowLeft")
    assert fresh.start_idx(1) == before


def test_shift_arrow_moves_five_steps(fresh):
    fresh.click_boundary(1)
    before = fresh.start_idx(1)
    fresh.press("Shift+ArrowRight")
    assert fresh.start_idx(1) == before + 5, fresh.table_state()
    fresh.press("Shift+ArrowLeft")
    assert fresh.start_idx(1) == before


def test_up_and_down_adjust_the_margin(fresh):
    fresh.click_boundary(1)
    before = fresh.tolerance_idx(1)
    fresh.press("ArrowUp")
    assert fresh.tolerance_idx(1) == before + 1, fresh.table_state()
    fresh.press("Shift+ArrowUp")
    assert fresh.tolerance_idx(1) == before + 6
    fresh.press("Shift+ArrowDown")
    fresh.press("ArrowDown")
    assert fresh.tolerance_idx(1) == before
    assert fresh.start_idx(1) == 20, "a margin key must not move the boundary"


# ══════════════════════════════════════════════════════════════════════════════
# The table and the chart are ONE state, in both directions
# ══════════════════════════════════════════════════════════════════════════════

def test_a_number_typed_in_the_table_moves_the_bar(fresh):
    """The table is the canonical path, so this direction is the one that must
    never break: it is what a labeller falls back to when the chart does."""
    fresh.set_start_idx(1, 31)
    assert fresh.start_idx(1) == 31
    drawn = fresh.page.locator(fresh.CHART).evaluate(
        "(svg) => svg.parentElement.__cp.PH[1].start_idx")
    assert drawn == 31, f"the chart still shows {drawn}"


def test_a_drag_updates_the_number(fresh):
    fresh.drag_boundary(2, 61)
    assert fresh.start_idx(2) == pytest.approx(61, abs=1), fresh.table_state()


def test_a_margin_typed_in_the_table_resizes_the_bar(fresh):
    fresh.set_tolerance_idx(2, 9)
    assert fresh.tolerance_idx(2) == 9
    drawn = fresh.page.locator(fresh.CHART).evaluate(
        "(svg) => svg.parentElement.__cp.PH[2].tolerance_idx")
    assert drawn == 9


def test_the_first_row_start_is_not_editable(fresh):
    """It is 0 by construction — a partition of [0, n) begins at 0."""
    assert fresh.page.get_by_label("start_idx, row 0", exact=True).is_disabled()
    assert fresh.start_idx(0) == 0


# ══════════════════════════════════════════════════════════════════════════════
# "Not sure", per boundary
# ══════════════════════════════════════════════════════════════════════════════

def test_not_sure_is_per_boundary_and_survives_a_drag(fresh):
    """Ambiguity used to be a property of the whole series, so one unreadable
    transition voided every boundary in the cyclone. Ticked here, it must stay
    ticked when the bar it belongs to is dragged — the chart does not send the
    flag and must not be able to clear it."""
    fresh.set_unsure(2, True)
    assert fresh.is_unsure(2) and not fresh.is_unsure(1)
    fresh.drag_boundary(2, 55)
    assert fresh.is_unsure(2), "the drag cleared the not-sure mark"
    assert not fresh.is_unsure(1), "it leaked onto another boundary"
    fresh.set_unsure(2, False)


def test_the_first_row_cannot_be_unsure(fresh):
    assert fresh.page.get_by_label("unsure, row 0", exact=True).is_disabled()


# ══════════════════════════════════════════════════════════════════════════════
# Blindness, reconfirmed in the browser
# ══════════════════════════════════════════════════════════════════════════════

def test_nothing_the_detector_produced_is_on_the_page(lab):
    """The AST tests prove the tab cannot IMPORT a detector. This proves the
    rendered page carries no detector vocabulary either — the payload crosses
    into the browser as JSON, so anything leaking would be visible here."""
    body = lab.page.locator("body").inner_text().lower()
    for word in ("get_periods", "process_vorticity", "find_stages",
                 "vorticity_smoothed", "filtered_vorticity", "z_peaks_valleys"):
        assert word not in body, word
    series = lab.page.locator(lab.CHART).evaluate(
        "(svg) => svg.querySelectorAll('path[stroke=\\'#1f2d3d\\']').length")
    assert series == 1, f"{series} series drawn; the label view shows exactly one"
