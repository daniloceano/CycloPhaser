"""The calibration app's pages (app redesign I1), driven by a real browser.

Read tests/browser_harness.py first. What is here and not in AppTest:

* the menu as a person sees it — sections, entries, and the Developer section
  absent without the key;
* the Manual labelling page end to end: drag a boundary, reveal an overlay, and
  SAVE — into a temporary COPY of manual_labels.yaml (the server is started with
  `labels_path=`), with the real file's bytes checked unchanged afterwards;
* what AppTest cannot drive at all: file uploads. An uploaded track and an
  imported YAML must survive a trip to Benchmark and back.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests"))

playwright_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright is not installed (browser tests)")
pytest.importorskip("streamlit", reason="Streamlit not installed (app-only)")
pytest.importorskip("yaml")

from browser_harness import (RENDER_TIMEOUT, SLIDER_HANDLE, AppServer,  # noqa: E402
                             LabelPage, selectbox, selectbox_value)

sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))
import labels_core as lc  # noqa: E402

REAL_LABELS = REPO_ROOT / "research" / "labels" / "manual_labels.yaml"
TRACK = REPO_ROOT / "docs" / "data" / "example_track_hourly.csv"
CONFIG = REPO_ROOT / "research" / "labels" / "configs" / "cyclophaser_params-track.yaml"


def _chromium_present() -> bool:
    try:
        with playwright_api.sync_playwright() as pw:
            return bool(pw.chromium.executable_path) and \
                Path(pw.chromium.executable_path).exists()
    except Exception:
        return False


pytestmark = [
    pytest.mark.skipif(not _chromium_present(), reason="Chromium is not installed: "
                       "python -m playwright install chromium"),
    pytest.mark.browser,
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def pw():
    with playwright_api.sync_playwright() as instance:
        yield instance


@pytest.fixture(scope="module")
def labels_copy(tmp_path_factory):
    """A temporary copy of the labels file, and the real file's sha256 before."""
    before = _sha(REAL_LABELS)
    copy = tmp_path_factory.mktemp("labels") / "manual_labels.yaml"
    shutil.copyfile(REAL_LABELS, copy)
    yield copy
    assert _sha(REAL_LABELS) == before, "the REAL manual_labels.yaml changed"


@pytest.fixture(scope="module")
def dev_server(tmp_path_factory, labels_copy):
    srv = AppServer(tmp_path_factory.mktemp("dev") / "streamlit.log",
                    developer=True, labels_path=labels_copy).start()
    yield srv
    srv.stop()


@pytest.fixture(scope="module")
def public_server(tmp_path_factory):
    srv = AppServer(tmp_path_factory.mktemp("pub") / "streamlit.log",
                    developer=False).start()
    yield srv
    srv.stop()


def _page(pw, width=1600, height=1000):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": height})
    page.set_default_timeout(60_000)
    return browser, page


def _nav_text(page) -> str:
    return page.locator('[data-testid="stSidebarNav"]').inner_text()


def _go(page, entry: str, wait_text: str) -> None:
    page.locator('[data-testid="stSidebarNav"]').get_by_text(entry, exact=True).click()
    page.wait_for_selector(f"text={wait_text}", timeout=RENDER_TIMEOUT)
    LabelPage(page).settle()


# ── the menu ──────────────────────────────────────────────────────────────────

def test_the_public_menu_has_calibrate_and_benchmark_and_no_developer(public_server, pw):
    browser, page = _page(pw)
    try:
        page.goto(public_server.url)
        page.wait_for_selector("text=Display mode", timeout=RENDER_TIMEOUT)
        nav = _nav_text(page)
        assert "Calibrate" in nav and "Benchmark" in nav, nav
        assert "Developer" not in nav and "Manual labelling" not in nav, nav
    finally:
        browser.close()


def test_the_developer_menu_has_the_labelling_page(dev_server, pw):
    browser, page = _page(pw)
    try:
        page.goto(dev_server.url)
        page.wait_for_selector("text=Display mode", timeout=RENDER_TIMEOUT)
        nav = _nav_text(page)
        for word in ("Calibrate", "Benchmark", "Developer", "Manual labelling"):
            assert word in nav, nav
    finally:
        browser.close()


# ── the Manual labelling page: drag, overlay, save (to the copy) ───────────────

def _status_line(page) -> str:
    return page.locator('[data-testid="stCaptionContainer"]').filter(
        has_text="blind").first.inner_text()


def test_label_page_drag_reveal_overlay_and_save(dev_server, pw, labels_copy):
    browser, page = _page(pw, 1600, 1100)
    try:
        lp = LabelPage(page).open(dev_server.url)
        assert not lp.errors, lp.errors
        # a train-split real case: no lock, not a frozen synthetic
        for _ in range(80):
            status = _status_line(page)
            if "🔒" not in status and "❄️" not in status:
                break
            page.get_by_role("button", name="Next ▸").click()
            lp.settle()
        else:
            pytest.fail("no unlocked real case in 80 steps")
        sid = page.locator(lp.CHART).get_attribute("data-sid")
        n = int(page.locator(lp.CHART).get_attribute("data-n"))
        assert lc.read_split()["train"].count(sid) == 1, sid
        assert status.startswith("🙈 blind"), status

        # known starting positions, typed into the table (not via the chart)
        lp.set_start_idx(3, (3 * n) // 4)
        lp.set_start_idx(2, n // 2)
        lp.set_start_idx(1, n // 6)
        target = n // 3
        lp.drag_boundary(1, target)
        dragged = lp.start_idx(1)
        assert dragged == pytest.approx(target, abs=2), (dragged, target)

        lp.enable_overlay("vorticity_smoothed2")
        assert _status_line(page).startswith("👁 overlays revealed"), _status_line(page)
        assert lp.start_idx(1) == dragged, "revealing an overlay moved a boundary"

        ow = page.get_by_label("Overwrite the existing label", exact=False)
        if ow.count() and not ow.is_checked():
            ow.locator("xpath=ancestor::label[1]").click()
            lp.settle()
        before = lc.read_labels(path=labels_copy).get(sid)
        page.get_by_role("button", name="💾 Save & next").click()
        lp.settle(2000)

        rec = lc.read_labels(path=labels_copy)[sid]
        assert rec["phases"][1]["start_idx"] == dragged
        assert rec["overlays_shown"] == ["vorticity_smoothed2"]
        if before is not None:
            assert rec.get("superseded"), "the overwritten label left no history"
        # the page moved on to the next case after saving
        assert page.locator(lp.CHART).get_attribute("data-sid") != sid
    finally:
        browser.close()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", str(REAL_LABELS)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    assert status == "", status


# ── uploads and the imported YAML survive a trip to another page ──────────────

def test_an_uploaded_track_and_an_imported_yaml_survive_a_page_trip(dev_server, pw):
    browser, page = _page(pw, 1600, 1000)
    lp = LabelPage(page)
    try:
        page.goto(dev_server.url)
        page.wait_for_selector("text=Display mode", timeout=RENDER_TIMEOUT)
        lp.settle()
        assert selectbox_value(page, "Boundary padding") != "edge"   # params-track sets edge

        page.locator('[data-testid="stSidebar"] input[type="file"]').set_input_files(
            str(CONFIG))
        page.wait_for_selector("text=parameters from YAML", timeout=RENDER_TIMEOUT)
        lp.settle()
        page.locator('[data-testid="stMain"] input[type="file"]').first.set_input_files(
            str(TRACK))
        page.wait_for_selector(f"text={TRACK.stem}", timeout=RENDER_TIMEOUT)
        lp.settle()
        assert selectbox_value(page, "Boundary padding") == "edge"

        _go(page, "Benchmark", "1 · Mode")
        _go(page, "Calibrate", "Display mode")

        main = page.locator('[data-testid="stMain"]').inner_text()
        assert f"Still using the 1 track(s) uploaded before you switched pages" in main
        assert TRACK.stem in main
        assert "No file uploaded" not in main
        assert "parameters from YAML" in page.locator(
            '[data-testid="stSidebar"]').inner_text()
        assert selectbox_value(page, "Boundary padding") == "edge"
        assert not lp.errors, lp.errors
    finally:
        browser.close()


# ── the sidebar as the browser shows it, after trips ───────────────────────────

# Every control's name=value, in either supported Streamlit rendering (see
# browser_harness: a selectbox named "Selected <value>. <label>" with an empty
# input on 1.56, a <div role="slider"> with aria-valuenow).
_SIDEBAR_SNAPSHOT_JS = """(root) => [...root.querySelectorAll('input, [role=slider]')]
    .filter((e) => e.type !== 'file')
    .map((e) => {
      let name = e.getAttribute('aria-label') ||
                 (e.closest('label') && e.closest('label').innerText.trim()) || e.type;
      let value = (e.type === 'checkbox' || e.type === 'radio') ? e.checked
                : (e.tagName !== 'INPUT') ? e.getAttribute('aria-valuenow') : e.value;
      const m = /^Selected (.*)\\. (.*)$/s.exec(name);
      if (m) { name = m[2]; if (!value) value = m[1]; }
      return name + '=' + value; })"""


def _sidebar_snapshot(page) -> list[str]:
    return page.locator('[data-testid="stSidebar"]').evaluate(_SIDEBAR_SNAPSHOT_JS)


def test_sidebar_values_set_in_the_ui_are_shown_after_page_trips(dev_server, pw):
    """What AppTest cannot see: the BROWSER side. On return to Calibrate the
    browser must draw the kept values, not the widgets' defaults — and must not
    send the defaults back on the next interaction (both were wrong before the
    arrival-run write in app.py `_keep_page_state`, while the server-side state
    was right)."""
    browser, page = _page(pw, 1600, 1000)
    lp = LabelPage(page)
    try:
        page.goto(dev_server.url)
        page.wait_for_selector("text=Display mode", timeout=RENDER_TIMEOUT)
        lp.settle()
        default = _sidebar_snapshot(page)
        sliders = page.locator('[data-testid="stSidebar"]').locator(SLIDER_HANDLE)
        for i in range(3):
            sliders.nth(i).press("ArrowLeft")
            lp.settle(600)
        selectbox(page, "Boundary padding").first.click()
        page.get_by_role("option", name="zero", exact=True).click()
        lp.settle()
        edited = _sidebar_snapshot(page)
        assert edited != default
        # two sliders and the selectbox (the third slider may already sit at its min)
        assert sum(a != b for a, b in zip(edited, default)) >= 3, (edited, default)

        for _ in range(2):
            _go(page, "Benchmark", "1 · Mode")
            _go(page, "Calibrate", "Display mode")
            assert _sidebar_snapshot(page) == edited
        # an interaction AFTER the return must not send defaults back
        page.get_by_text("Inspector", exact=True).first.click()
        lp.settle()
        assert _sidebar_snapshot(page) == edited
        assert not lp.errors, lp.errors
    finally:
        browser.close()
