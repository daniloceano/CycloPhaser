"""The Validate page in a real browser (benchmark review, I2) — criterion (e1).

Usability tasks of the I2 brief, counted. One interaction = a click, a choice in
a selector, an upload or typing. The starting point is the app with the
developer key and the Calibrate page opened once; it is not counted.

Budgets: T6 ≤ 6, T7 ≤ 3 (after T6), T8 ≤ 2 (after T6), T9 = 0.

What only a browser can check here: the menu entry, the visible text a blocked
Run shows without hovering (T9), the figures actually loading, the browser side
of the state kept across a trip to Calibrate (finding A12), the uploader, and
where the browser breaks a line in a narrow card (I1 pending item 2), and what
a copy of the warning gives (I2 round 2, R1).
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
yaml = pytest.importorskip("yaml")

from browser_harness import AppServer, selectbox_value  # noqa: E402
from test_compare_browser import MAIN, Session, _chromium_present  # noqa: E402

CONFIG = REPO_ROOT / "research" / "labels" / "configs" / "cyclophaser_params-track.yaml"
BUDGET = {"T6": 6, "T7": 3, "T8": 2, "T9": 0}
PAGE = "Validate against labels"
FILTER = "Show only tracks that disagree with the label (any column)"
SHOW_LABEL = "Show the label panel"
SEQ = ("Sequence · instrument evaluate_against_labels.py / score_phase_sequences · "
       "{tag}")
MAT = "Mature · instrument item19_core.pair_by_overlap (margin 6) · {tag}"

pytestmark = [
    pytest.mark.skipif(not _chromium_present(), reason="Chromium is not installed: "
                       "python -m playwright install chromium"),
    pytest.mark.browser,
]

# Every alphanumeric run of an element's text that the browser laid out on
# more than one line: a word broken in the middle. A break after "." or "_"
# splits two runs, so it is not counted.
BROKEN_WORDS_JS = """(els) => {
  const out = [];
  for (const el of els) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const re = /[A-Za-z0-9]+/g; let m;
      while ((m = re.exec(node.data))) {
        const r = document.createRange();
        r.setStart(node, m.index); r.setEnd(node, m.index + m[0].length);
        const tops = new Set([...r.getClientRects()].filter(x => x.width > 0)
                             .map(x => Math.round(x.top)));
        if (tops.size > 1) out.push(m[0]);
      }
    }
  }
  return out;
}"""


@pytest.fixture(scope="module")
def pw():
    with playwright_api.sync_playwright() as instance:
        yield instance


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    srv = AppServer(tmp_path_factory.mktemp("validate") / "streamlit.log",
                    developer=True).start()
    yield srv
    srv.stop()


class VSession(Session):
    def main_text(self) -> str:
        return " ".join(self.page.locator(MAIN).inner_text().split())

    def toggle_on(self, label: str) -> bool:
        """st.toggle's <input>, named by its label: role="switch" on 1.63.0, a
        plain checkbox on 1.56.0 (measured), so it is found by aria-label."""
        return self.page.locator(MAIN).locator(
            f'[data-testid="stCheckbox"] input[aria-label="{label}"]').is_checked()


def test_e1_tasks_t9_t6_t8_t7_within_budget(server, pw):
    s = VSession(pw, server.url)          # Calibrate, opened once: not counted
    counts = {}
    try:
        # T6: Defaults × params-track on the train split, both instrument blocks.
        s.n = 0
        s.menu(PAGE, PAGE)
        # T9 — here Run is blocked: the reason is on screen, no hover.
        assert s.visible("To run, add at least one configuration.")
        counts["T9"] = 0
        s.click("Add Defaults")
        s.choose("Calibration file (research/labels/configs/)", CONFIG.name)
        s.click("Add file")
        s.click("Run")
        s.wait("Train — n = 47")
        text = s.main_text()
        assert SEQ.format(tag="train, n = 47") in text
        assert MAT.format(tag="train, n = 47") in text
        assert s.table_visible()
        counts["T6"] = s.n
        # T8: only the tracks that disagree, and the figure of one.
        s.n = 0
        s.check(FILTER)
        s.wait("of the 47 selected track(s) disagree")
        assert s.images_loaded() >= 3            # label + two configurations
        assert "Label panel: hatched band" in s.main_text(), s.main_text()[-3000:]
        counts["T8"] = s.n
        # T7: the batch on, the adjudicated block apart.
        s.n = 0
        s.check("Include swell_item30 batch")
        s.click("Run")
        s.wait("Adjudicated — n = 5")
        text = s.main_text()
        assert "Train — n = 49" in text
        assert SEQ.format(tag="adjudicated, n = 5") in text
        counts["T7"] = s.n
        assert not s.lp.errors, s.lp.errors
    finally:
        s.close()
    print("e1 interactions:", counts)
    for task, n in counts.items():
        assert n <= BUDGET[task], (task, n, BUDGET[task])


def test_the_validate_state_survives_a_trip_to_calibrate_in_the_browser(server, pw):
    s = VSession(pw, server.url)
    try:
        s.menu(PAGE, PAGE)
        s.click("Add Defaults")
        s.click("Add Current settings")
        s.click("Run")
        s.wait("Train — n = 47")
        s.choose("Reference", "Current settings")
        s.wait("Relative to Current settings")
        s.check("Stacked")
        assert s.toggle_on(SHOW_LABEL)              # on by default
        s.check(SHOW_LABEL)
        assert not s.toggle_on(SHOW_LABEL)
        s.menu("Calibrate", "1 · Data")
        s.menu(PAGE, PAGE)
        s.wait("Relative to Current settings")
        assert selectbox_value(s.page, "Reference") == "Current settings"
        stacked = s.page.locator(MAIN).get_by_role("radio", name="Stacked")
        assert stacked.is_checked()
        assert not s.toggle_on(SHOW_LABEL)
        # an interaction after the return must not send the old values back
        s.check(FILTER)
        s.wait("of the 47 selected track(s) disagree")
        assert selectbox_value(s.page, "Reference") == "Current settings"
        assert stacked.is_checked() and not s.toggle_on(SHOW_LABEL)
        assert s.images_loaded() >= 1
        assert not s.lp.errors, s.lp.errors
    finally:
        s.close()


def _filled_warning(s):
    """The filled-keys warning block (config_text.warning_html, I2 round 2)."""
    warn = s.page.locator(f'{MAIN} [data-testid="stMarkdownContainer"] div').filter(
        has_text="absent from this file were filled")
    assert warn.count() >= 1
    return warn


def _broken_words_in_filled_warning(s) -> list[str]:
    return _filled_warning(s).evaluate_all(BROKEN_WORDS_JS)


def _copied_text(s) -> str:
    """What a copy of the warning gives: its rendered text."""
    return _filled_warning(s).last.inner_text()


def _control_detects_a_broken_word(s) -> list[str]:
    """The same measure on a word the browser must break: a narrow box that
    allows breaking anywhere."""
    return s.page.evaluate("""(js) => {
      const d = document.createElement('div');
      d.style.cssText = 'width:60px;overflow-wrap:anywhere;font-size:16px';
      d.textContent = 'phase_params.prominence_relative=None';
      document.querySelector('[data-testid="stMain"]').appendChild(d);
      const out = eval(js)([d]); d.remove(); return out; }""", BROKEN_WORDS_JS)


def test_the_filled_keys_warning_breaks_no_word_in_a_narrow_card(server, pw, tmp_path):
    doc = yaml.safe_load(CONFIG.read_text())
    del doc["phase_params"]["prominence_relative"]
    older = tmp_path / "params-track-older.yaml"
    older.write_text(yaml.safe_dump(doc, sort_keys=False))
    s = VSession(pw, server.url)
    try:
        s.start()                                  # sample data, for Compare
        # Compare, four columns: the narrowest card the page allows
        s.menu("Compare", "Compare configurations")
        s.click("Add Current settings")
        s.click("Add Defaults")
        s.upload(older)
        s.wait(older.stem)
        s.click("Add Current settings")
        s.wait("4 configurations is the limit")
        assert _broken_words_in_filled_warning(s) == []
        assert "prominence" in _control_detects_a_broken_word(s)    # control
        # round trip (R1): the copied key is the real key, no hidden character
        copied = _copied_text(s)
        assert "phase_params.prominence_relative=None" in copied, copied
        assert "\u200b" not in copied
        # Validate, six columns
        s.menu(PAGE, PAGE)
        s.upload(older)
        s.wait(older.stem)
        for _ in range(4):
            s.click("Add Current settings")
        s.click("Add Defaults")
        s.wait("6 configurations is the limit")
        assert _broken_words_in_filled_warning(s) == []
        assert "phase_params.prominence_relative=None" in _copied_text(s)
        assert not s.lp.errors, s.lp.errors
    finally:
        s.close()
        older.unlink()
    assert not older.exists()
