"""The Compare page in a real browser (benchmark review, I1) — criterion (e1).

Usability tasks of research/benchmark_review/stage0/DECISIONS.md, run from
scratch and counted. One interaction = a click, a choice in a selector, an
upload or typing. The starting point of every task is the Calibrate page with
"Sample data" loaded and one sidebar value changed (High cutoff, five steps up),
so that "Current settings" and "Defaults" are different configurations; that
setup is not counted, it is the state the tasks start from.

Budgets: T1 ≤ 5, T2 ≤ 5, T3 ≤ 2 (after T1), T4 ≤ 3 (after T1), T5 = 0.

What only a browser can check here: the uploader (T2), the menu entry, the
visible text a blocked Run shows without hovering (T5), the figures actually
loading, and the browser side of the state kept across a trip to Calibrate.
"""

from __future__ import annotations

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

CONFIG = REPO_ROOT / "research" / "labels" / "configs" / "cyclophaser_params-track.yaml"
BUDGET = {"T1": 5, "T2": 5, "T3": 2, "T4": 3, "T5": 0}
MAIN = '[data-testid="stMain"]'


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


@pytest.fixture(scope="module")
def pw():
    with playwright_api.sync_playwright() as instance:
        yield instance


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    srv = AppServer(tmp_path_factory.mktemp("compare") / "streamlit.log",
                    developer=False).start()
    yield srv
    srv.stop()


class Session:
    """A browser page on the app, with every user action counted."""

    def __init__(self, pw, url):
        self.browser = pw.chromium.launch()
        self.page = self.browser.new_page(viewport={"width": 1600, "height": 1000})
        self.page.set_default_timeout(60_000)
        self.lp = LabelPage(self.page)
        self.n = 0
        self.page.goto(url)
        self.page.wait_for_selector("text=1 · Data", timeout=RENDER_TIMEOUT)
        self.lp.settle()

    def close(self):
        self.browser.close()

    # ── the starting point (not counted) ──────────────────────────────────────
    def start(self) -> None:
        sliders = self.page.locator('[data-testid="stSidebar"]').locator(SLIDER_HANDLE)
        for _ in range(5):                      # High cutoff 18 → 48 (step 6)
            sliders.nth(1).press("ArrowRight")
            self.lp.settle(500)
        self.page.locator('[data-testid="stSidebar"]').get_by_role(
            "button", name="Sample data (51 TRACK cyclones)").click()
        self.page.wait_for_selector("text=51 tracks loaded", timeout=RENDER_TIMEOUT)
        self.lp.settle()

    # ── counted actions ───────────────────────────────────────────────────────
    def menu(self, entry: str, wait_text: str) -> None:
        self.n += 1
        self.page.locator('[data-testid="stSidebarNav"]').get_by_text(
            entry, exact=True).click()
        self.page.wait_for_selector(f"text={wait_text}", timeout=RENDER_TIMEOUT)
        self.lp.settle()

    def click(self, name: str) -> None:
        self.n += 1
        self.page.locator(MAIN).get_by_role("button", name=name, exact=True).click()
        self.lp.settle()

    def check(self, label: str) -> None:
        self.n += 1
        self.page.locator(MAIN).get_by_text(label, exact=True).click()
        self.lp.settle()

    def choose(self, label: str, option: str) -> None:
        """One choice in a selector (opening it is part of the same choice)."""
        self.n += 1
        box = selectbox(self.page, label).first
        # Scrolled into view BEFORE the click: when the click itself has to
        # scroll a long page, the dropdown opens and is closed by that scroll.
        box.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)
        box.click()
        self.page.get_by_role("option", name=option, exact=True).click()
        self.lp.settle()

    def upload(self, path: Path) -> None:
        self.n += 1
        self.page.locator(f'{MAIN} [data-testid="stFileUploader"] '
                          'input[type="file"]').set_input_files(str(path))
        self.lp.settle()

    # ── reading ───────────────────────────────────────────────────────────────
    def visible(self, text: str) -> bool:
        loc = self.page.locator(MAIN).get_by_text(text, exact=False)
        return loc.count() > 0 and loc.first.is_visible()

    def wait(self, text: str) -> None:
        self.page.locator(MAIN).get_by_text(text, exact=False).first.wait_for(
            state="visible", timeout=RENDER_TIMEOUT)
        self.lp.settle()

    def images_loaded(self) -> int:
        """Wait until every figure on the page has loaded; return how many."""
        self.page.wait_for_function(
            """() => { const im = [...document.querySelectorAll(
                   '[data-testid="stMain"] img')];
                 return im.length > 0 && im.every(i => i.complete && i.naturalWidth > 0); }""",
            timeout=RENDER_TIMEOUT)
        return self.page.locator(f"{MAIN} img").count()

    def table_visible(self) -> bool:
        return self.page.locator(f'{MAIN} [data-testid="stDataFrame"]').first.is_visible()


def test_e1_tasks_t5_t1_t3_t4_within_budget(server, pw):
    s = Session(pw, server.url)
    counts = {}
    try:
        s.start()
        # T1: Current settings × Defaults, up to the relative table.
        s.n = 0
        s.menu("Compare", "Compare configurations")
        # T5 — here Run is blocked: the reason is on screen, no hover.
        assert s.visible("To run, add at least one configuration.")
        counts["T5"] = 0
        s.click("Add Current settings")
        s.click("Add Defaults")
        s.click("Run")
        s.wait("Relative to Current settings")
        assert s.table_visible()
        assert s.visible("Over the 51 selected track(s) of the last run")
        counts["T1"] = s.n
        # T3: only the tracks whose sequence differs, and one figure.
        s.n = 0
        s.check("Show only cyclones whose sequence differs from the reference")
        s.wait("of the 51 selected track(s) have")
        assert s.images_loaded() >= 2            # first track, both columns
        assert s.visible("sequence differs from reference")
        counts["T3"] = s.n
        # T4: another reference, and the table follows without a Run.
        s.n = 0
        s.choose("Reference", "Defaults")
        s.wait("Relative to Defaults")
        assert s.table_visible()
        assert not s.visible("Results out of date")
        counts["T4"] = s.n
        assert not s.lp.errors, s.lp.errors
    finally:
        s.close()
    print("e1 interactions:", counts)
    for task, n in counts.items():
        assert n <= BUDGET[task], (task, n, BUDGET[task])


def test_e1_task_t2_upload_a_yaml_within_budget(server, pw):
    s = Session(pw, server.url)
    try:
        s.start()
        s.n = 0
        s.menu("Compare", "Compare configurations")
        s.click("Add Current settings")
        s.upload(CONFIG)
        s.wait(CONFIG.stem)
        s.click("Run")
        s.wait("Relative to Current settings")
        assert s.table_visible()
        assert s.images_loaded() >= 2
        t2 = s.n
        assert not s.lp.errors, s.lp.errors
    finally:
        s.close()
    print("e1 interactions: {'T2': %d}" % t2)
    assert t2 <= BUDGET["T2"], t2


def test_the_compare_state_survives_a_trip_to_calibrate_in_the_browser(server, pw):
    s = Session(pw, server.url)
    try:
        s.start()
        s.menu("Compare", "Compare configurations")
        s.click("Add Current settings")
        s.click("Add Defaults")
        s.click("Run")
        s.wait("Relative to Current settings")
        s.choose("Reference", "Defaults")
        s.check("Stacked")
        s.wait("Relative to Defaults")
        s.menu("Calibrate", "1 · Data")
        s.menu("Compare", "Compare configurations")
        s.wait("Relative to Defaults")
        assert selectbox_value(s.page, "Reference") == "Defaults"
        stacked = s.page.locator(MAIN).get_by_role("radio", name="Stacked")
        assert stacked.is_checked()
        # an interaction after the return must not send the old values back
        s.check("Show only cyclones whose sequence differs from the reference")
        s.wait("of the 51 selected track(s) have")
        assert selectbox_value(s.page, "Reference") == "Defaults"
        assert stacked.is_checked()
        assert s.images_loaded() >= 1
        assert not s.lp.errors, s.lp.errors
    finally:
        s.close()
