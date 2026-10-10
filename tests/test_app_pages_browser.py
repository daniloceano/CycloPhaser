"""The calibration app's pages (app redesign I1), driven by a real browser.

Read tests/browser_harness.py first. What is here and not in AppTest:

* the menu as a person sees it — sections, entries, and the Developer section
  absent without the key; the old Benchmark page in no menu, and its address
  (`/benchmark`) opening the default page (benchmark review, I3);
* the Manual labelling page end to end: drag a boundary, reveal an overlay, and
  SAVE — into a temporary COPY of manual_labels.yaml (the server is started with
  `labels_path=`), with the real file's bytes checked unchanged afterwards;
* what AppTest cannot drive at all: file uploads. An uploaded track and an
  imported YAML must survive a trip to Compare and back (to Benchmark until I3).
"""

from __future__ import annotations

import hashlib
import shutil
import zipfile
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
# The heading of the Calibrate start screen (I3), shown only while no track is loaded.
START_SCREEN = "Check CycloPhaser's phases on your cyclone tracks"


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

def test_the_public_menu_has_calibrate_and_compare_and_no_developer(public_server, pw):
    browser, page = _page(pw)
    try:
        page.goto(public_server.url)
        page.wait_for_selector("text=1 · Data", timeout=RENDER_TIMEOUT)
        nav = _nav_text(page)
        assert "Calibrate" in nav and "Compare" in nav, nav
        for word in ("Developer", "Manual labelling", "Validate against labels",
                     "Benchmark"):
            assert word not in nav, (word, nav)
    finally:
        browser.close()


def test_the_developer_menu_has_the_labelling_and_validate_pages(dev_server, pw):
    browser, page = _page(pw)
    try:
        page.goto(dev_server.url)
        page.wait_for_selector("text=1 · Data", timeout=RENDER_TIMEOUT)
        nav = _nav_text(page)
        for word in ("Calibrate", "Compare", "Developer", "Manual labelling",
                     "Validate against labels"):
            assert word in nav, nav
        assert "Benchmark" not in nav, nav
    finally:
        browser.close()


def test_the_old_benchmark_address_opens_the_default_page(public_server, dev_server, pw):
    """Benchmark review, I3: no provisional page. `/benchmark` falls to what
    st.navigation does with an address it does not know, and that is the
    default page, Calibrate — with and without the developer key. Control: the
    same session then reaches Compare from the menu. What else Streamlit shows
    on the way (a "page not found" notice, the address it leaves in the bar) is
    printed for the record, not asserted."""
    for server in (public_server, dev_server):
        browser, page = _page(pw)
        try:
            lp = LabelPage(page)
            page.goto(server.url.rstrip("/") + "/benchmark")
            page.wait_for_selector("text=1 · Data", timeout=RENDER_TIMEOUT)
            lp.settle()
            main = page.locator('[data-testid="stMain"]').inner_text()
            assert START_SCREEN in main, main[:300]
            nav = _nav_text(page)
            assert "Calibrate" in nav and "Benchmark" not in nav, nav
            dialogs = page.get_by_role("dialog")
            notice = dialogs.first.inner_text() if dialogs.count() else ""
            print(f"/benchmark ({'developer' if server is dev_server else 'public'}): "
                  f"url={page.url} | notice={notice!r}")
            if notice:                  # a modal notice covers the menu: close it
                page.keyboard.press("Escape")
                dialogs.first.wait_for(state="hidden", timeout=RENDER_TIMEOUT)
            _go(page, "Compare", "Compare configurations")            # control
            assert not [e for e in lp.errors if e.startswith("pageerror")], lp.errors
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


# ── Calibrate sidebar helpers (I2 layout) ─────────────────────────────────────

def _calibrate(page, url) -> LabelPage:
    page.goto(url)
    page.wait_for_selector("text=1 · Data", timeout=RENDER_TIMEOUT)
    lp = LabelPage(page)
    lp.settle()
    return lp


def _uploader(page, label_part: str):
    return page.locator('[data-testid="stSidebar"] [data-testid="stFileUploader"]').filter(
        has_text=label_part).locator('input[type="file"]')


def _sidebar_button(page, name: str):
    """The sidebar's button. Since I3 the start screen repeats "Try example data"
    and "Sample data …" in the main area while nothing is loaded, so a bare
    role/name lookup would match two buttons."""
    return page.locator('[data-testid="stSidebar"]').get_by_role("button", name=name)


def _open_group(page, title: str) -> None:
    """Open one of the sidebar's Advanced expanders (they start closed)."""
    summary = page.locator('[data-testid="stSidebar"] [data-testid="stExpander"] summary').filter(
        has_text=title).first
    details = summary.locator("xpath=..")
    if details.get_attribute("open") is None:
        summary.click()
        page.wait_for_timeout(400)


# ── uploads and the imported YAML survive a trip to another page ──────────────

def test_an_uploaded_track_and_an_imported_yaml_survive_a_page_trip(dev_server, pw):
    browser, page = _page(pw, 1600, 1000)
    try:
        lp = _calibrate(page, dev_server.url)
        assert selectbox_value(page, "Boundary padding") != "edge"   # params-track sets edge

        _uploader(page, "saved configuration").set_input_files(str(CONFIG))
        page.wait_for_selector("text=parameters from YAML", timeout=RENDER_TIMEOUT)
        lp.settle()
        _uploader(page, "Upload tracks").set_input_files(str(TRACK))
        page.wait_for_selector(f"text={TRACK.stem}", timeout=RENDER_TIMEOUT)
        lp.settle()
        assert selectbox_value(page, "Boundary padding") == "edge"

        _go(page, "Compare", "Compare configurations")
        _go(page, "Calibrate", "1 · Data")

        body = page.locator("body").inner_text()
        assert "Still using the 1 track(s) uploaded before you switched pages" in body
        assert TRACK.stem in page.locator('[data-testid="stMain"]').inner_text()
        assert START_SCREEN not in body           # I3: the start screen replaced the no-data line
        sidebar = page.locator('[data-testid="stSidebar"]').inner_text()
        assert "parameters from YAML" in sidebar and f"Active: {CONFIG.name}" in sidebar
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
    try:
        lp = _calibrate(page, dev_server.url)
        _sidebar_button(page, "Try example data").click()
        lp.settle()
        default = _sidebar_snapshot(page)
        sliders = page.locator('[data-testid="stSidebar"]').locator(SLIDER_HANDLE)
        for i in range(2):                       # Low and High cutoff (step 3)
            sliders.nth(i).press("ArrowLeft")
            lp.settle(600)
        _open_group(page, "Filtering options")
        selectbox(page, "Boundary padding").first.click()
        page.get_by_role("option", name="zero", exact=True).click()
        lp.settle()
        edited = _sidebar_snapshot(page)
        assert edited != default
        assert sum(a != b for a, b in zip(edited, default)) >= 3, (edited, default)

        for _ in range(2):
            _go(page, "Compare", "Compare configurations")
            _go(page, "Calibrate", "1 · Data")
            assert _sidebar_snapshot(page) == edited
        # an interaction AFTER the return must not send defaults back
        page.get_by_text("Inspector", exact=True).first.click()
        lp.settle()
        assert _sidebar_snapshot(page) == edited
        assert not lp.errors, lp.errors
    finally:
        browser.close()


# ── Save results: the file that actually downloads ────────────────────────────

def _download_package(page, lp, png: bool) -> list[str]:
    page.get_by_role("button", name="Save results").click()
    dialog = page.get_by_role("dialog")
    dialog.wait_for(timeout=RENDER_TIMEOUT)
    box = dialog.get_by_label("Figures (PNG)", exact=True)
    if box.is_checked() != png:
        box.locator("xpath=ancestor::label[1]").click()
        lp.settle()
    dialog.get_by_role("button", name="Prepare package").click()
    lp.settle(1500)
    with page.expect_download(timeout=RENDER_TIMEOUT) as dl:
        dialog.get_by_role("button", name="Download cyclophaser_results.zip").click()
    path = dl.value.path()
    names = zipfile.ZipFile(path).namelist()
    dialog.get_by_role("button", name="Done", exact=True).click()
    lp.settle()
    return names


def test_save_results_downloads_what_the_options_say(dev_server, pw):
    browser, page = _page(pw, 1600, 1000)
    try:
        lp = _calibrate(page, dev_server.url)
        _sidebar_button(page, "Try example data").click()
        page.wait_for_selector("text=example_file", timeout=RENDER_TIMEOUT)
        lp.settle()
        # defaults: the configuration always, the phase tables on, no figures
        assert sorted(_download_package(page, lp, png=False)) == [
            "example_file_periods.csv", "parameters.yaml"]
        assert sorted(_download_package(page, lp, png=True)) == [
            "example_file_periods.csv", "example_file_periods.png", "parameters.yaml"]
        assert not lp.errors, lp.errors
    finally:
        browser.close()


# ── the custom-format dialog, driven like a person would ──────────────────────

def _custom_file(path: Path) -> Path:
    """The example track as ',' + lat,vor,lon,date with day-first dates."""
    import pandas as pd
    rows = ["lat,vor,lon,date"]
    for line in TRACK.read_text().splitlines()[1:]:
        t, v = line.split(";")[:2]
        rows.append(f"-30,{v},-45,{pd.Timestamp(t):%d/%m/%Y %H:%M}")
    path.write_text("\n".join(rows) + "\n")
    return path


def test_the_custom_format_dialog_reads_a_non_standard_file(dev_server, pw, tmp_path):
    browser, page = _page(pw, 1600, 1000)
    try:
        lp = _calibrate(page, dev_server.url)
        odd = _custom_file(tmp_path / "odd.txt")
        _uploader(page, "Upload tracks").set_input_files(str(odd))
        lp.settle()
        assert "refused" in page.locator('[data-testid="stSidebar"]').inner_text()
        assert START_SCREEN in page.locator('[data-testid="stMain"]').inner_text()

        page.get_by_role("button", name="Custom format…").click()
        dialog = page.get_by_role("dialog")
        dialog.wait_for(timeout=RENDER_TIMEOUT)
        dialog.get_by_label("Enable custom track format").locator(
            "xpath=ancestor::label[1]").click()
        lp.settle()
        selectbox(page, "Separator").first.click()
        page.get_by_role("option", name=",", exact=True).click()
        lp.settle()
        for label, value in (("Date column", "date"), ("Vorticity column", "vor"),
                             ("Date format (optional)", "%d/%m/%Y %H:%M")):
            field = dialog.get_by_label(label, exact=True)
            field.fill(value)
            field.press("Enter")
            lp.settle()
        dialog.get_by_text("Preview — ").first.wait_for(timeout=RENDER_TIMEOUT)
        dialog.get_by_label("Use `odd.txt` as previewed", exact=False).locator(
            "xpath=ancestor::label[1]").click()
        lp.settle()
        dialog.get_by_role("button", name="Done").click()
        page.wait_for_selector('[data-testid="stMain"] >> text=odd', timeout=RENDER_TIMEOUT)
        lp.settle()
        assert "1 track loaded" in page.locator('[data-testid="stSidebar"]').inner_text()
        assert not lp.errors, lp.errors
    finally:
        browser.close()


# ── I3: the paged grid, from the start screen, in the browser ─────────────────

def _main(page):
    return page.locator('[data-testid="stMain"]')


def _grid_figures(page) -> int:
    return _main(page).locator('[data-testid="stImage"]').count()


def _page_line(page) -> str:
    return _main(page).get_by_text("Page ", exact=False).filter(
        has_text=" · tracks ").first.inner_text().strip()


# The main area holds exactly `n` images and every one has finished loading (a
# broken one never does, so a figure that stays broken fails here by timeout).
# The count matters: "every image loaded" is also true of an empty page, which
# a slow browser shows for a moment after the run has ended (CPU 4×, I3).
_JS_FIGURES_LOADED = """(n) => { const imgs = [...document.querySelectorAll(
    '[data-testid="stMain"] [data-testid="stImage"] img')];
    return imgs.length === n && imgs.every(i => i.complete && i.naturalWidth > 0); }"""


def _settled(lp: LabelPage, figures: int) -> None:
    """The app has finished its run AND the page's `figures` figures have loaded.

    Waited for before every click that reruns the app. Streamlit serves each
    figure from /media/<hash>.png only while the run that drew it is the
    current one; a click that starts a new run while the browser is still
    fetching the previous page's figures leaves those requests to fail with
    404 ("Image source error") — transient, the figures of the new run all
    load (diagnosed in research/app_redesign/i3/RELATORIO.md, "Falha
    intermitente"). The console stays checked: nothing is ignored.
    """
    lp.settle()
    lp.page.wait_for_function(_JS_FIGURES_LOADED, arg=figures, timeout=RENDER_TIMEOUT)


_JS_FIGURE_REQUESTS_ENDED = """() => [...document.querySelectorAll(
    '[data-testid="stMain"] [data-testid="stImage"] img')].every(i => i.complete)"""

# The final state's figures, URL by URL: every main-area image loaded, and the
# server still answers 200 for each of their URLs now.
_JS_FINAL_FIGURES = """async () => Promise.all([...document.querySelectorAll(
    '[data-testid="stMain"] [data-testid="stImage"] img')].map(async i => ({
        src: i.currentSrc || i.src, loaded: i.complete && i.naturalWidth > 0,
        status: (await fetch(i.currentSrc || i.src, {cache: 'no-store'})).status})))"""


def _is_media_404(text: str, url: str) -> bool:
    """A console error about one figure's /media/ URL answering 404 — and
    nothing else: the browser's "Failed to load resource … 404" whose source
    is a /media/ URL, or Streamlit's "Image source error - …/media/…"."""
    return (("Image source error" in text and "/media/" in text)
            or (text.startswith("Failed to load resource") and "404" in text
                and "/media/" in url))


def test_the_paged_grid_keeps_page_size_page_and_marks_in_the_browser(dev_server, pw):
    """What AppTest cannot see, for the I3 grid: after a trip through the
    Inspector and the Compare page (the Benchmark page until I3), the browser
    shows the kept page size, the kept page and a mark set on a page that was
    not on screen — and only the current page's figures are in the DOM.

    Console errors — the one tolerance, and its condition. Streamlit serves a
    figure from /media/<hash>.png only while the run that drew it is the
    current one; when a click starts the next run while a slow browser is still
    fetching figures, those requests answer 404 and the console logs it. Each
    click here starts exactly ONE script run (measured; see
    research/app_redesign/i3/RELATORIO.md, "Segunda correção"), so this is a
    race inside Streamlit, not an extra run of the app. Hence:
      * a console error is tolerated ONLY if it is such a /media/ 404
        (`_is_media_404`), AND only because the final state is checked URL by
        URL: after the app has finished, every figure on the page loaded and
        every one of their URLs answers 200 (checked always, tolerated errors
        or not);
      * any other console error, and any page error, fails the test.
    """
    browser, page = _page(pw, 1600, 1000)
    try:
        console = []         # (text, source url) of every console error
        page.on("console", lambda m: console.append(
            (m.text, (m.location or {}).get("url", ""))) if m.type == "error" else None)
        lp = _calibrate(page, dev_server.url)
        assert START_SCREEN in _main(page).inner_text()
        _main(page).get_by_role("button", name="Sample data (51 TRACK cyclones)").click()
        page.wait_for_selector("text=Set statistics", timeout=RENDER_TIMEOUT)
        _settled(lp, 12)
        assert _page_line(page) == "Page 1 of 5 · tracks 1–12 of 51"
        assert _grid_figures(page) == 12

        mark = _main(page).get_by_role("checkbox", name="⚠️ Mark as bad").first
        mark.locator("xpath=ancestor::label[1]").click()
        _settled(lp, 12)
        assert mark.is_checked()

        selectbox(page, "Tracks per page").first.click()
        page.get_by_role("option", name="24", exact=True).click()
        _settled(lp, 24)
        assert _page_line(page) == "Page 1 of 3 · tracks 1–24 of 51"
        _main(page).get_by_role("button", name="Next ▶").first.click()
        _settled(lp, 24)
        assert _page_line(page) == "Page 2 of 3 · tracks 25–48 of 51"
        assert _grid_figures(page) == 24

        _main(page).get_by_text("Inspector", exact=True).first.click()
        _settled(lp, 0)
        _main(page).get_by_text("Grid", exact=True).first.click()
        _settled(lp, 24)
        _go(page, "Compare", "Compare configurations")
        _go(page, "Calibrate", "1 · Data")
        page.wait_for_selector("text=Set statistics", timeout=RENDER_TIMEOUT)
        _settled(lp, 24)
        assert selectbox_value(page, "Tracks per page") == "24"
        assert _page_line(page) == "Page 2 of 3 · tracks 25–48 of 51"
        assert _grid_figures(page) == 24

        # an interaction after the return must not send defaults back
        _main(page).get_by_role("button", name="◀ Previous").first.click()
        _settled(lp, 24)
        assert _page_line(page) == "Page 1 of 3 · tracks 1–24 of 51"
        assert selectbox_value(page, "Tracks per page") == "24"
        assert _main(page).get_by_role("checkbox", name="⚠️ Mark as bad").first.is_checked()
        assert "1 / 51" in _main(page).inner_text()

        # the final state, URL by URL — always. Its own wait: the app has
        # finished, and every image request has ended (an image that failed
        # for good also ends: complete, with no width — and is reported below)
        lp.settle()
        page.wait_for_function(_JS_FIGURE_REQUESTS_ENDED, timeout=RENDER_TIMEOUT)
        final = page.evaluate(_JS_FINAL_FIGURES)
        assert len(final) == 24, len(final)
        bad = [f for f in final if not f["loaded"] or f["status"] != 200]
        assert not bad, bad
        # only /media/ 404s may be in the console, and only with that final state
        assert not [e for e in lp.errors if e.startswith("pageerror")], lp.errors
        assert len(console) == len(lp.errors), (console, lp.errors)
        other = [t for t, u in console if not _is_media_404(t, u)]
        assert not other, other
    finally:
        browser.close()
