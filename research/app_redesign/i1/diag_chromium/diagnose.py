"""I1, second correction — diagnosis BEFORE any fix of the 3 Chromium tests that
time out on streamlit 1.56.0.

    <python with the streamlit under test> research/app_redesign/i1/diag_chromium/diagnose.py <label>

Starts the app with that interpreter (tests/browser_harness.AppServer, developer
key on), reproduces each failing test up to the control it waits for, and looks
the control up the way the test does, with a short timeout. Either way it saves a
screenshot of that moment and a dump of the controls actually on screen (tag,
role, accessible name, value), so each case can be classed as TEST (the control
is there, under another name/structure) or APP (it is not there, or shows the
wrong value). Output: diag_chromium/<label>/{a,b,c}_*.png and report.json.

  a — test_the_table_shows_a_row_per_phase: get_by_label("phase, row 0")
  b — test_an_uploaded_track_and_an_imported_yaml_...: get_by_label("Boundary padding")
  c — test_sidebar_values_set_in_the_ui_...: sidebar slider input[type=range]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tests"))

from browser_harness import RENDER_TIMEOUT, AppServer, LabelPage  # noqa: E402

DUMP_JS = """(root) => [...root.querySelectorAll(
    'input, [role=combobox], [role=slider], [role=listbox], select, button[role=combobox]')]
  .slice(0, 60).map((e) => ({
    tag: e.tagName.toLowerCase(), type: e.getAttribute('type'),
    role: e.getAttribute('role'), aria_label: e.getAttribute('aria-label'),
    aria_labelledby: e.getAttribute('aria-labelledby'),
    labelled_text: (e.getAttribute('aria-labelledby') || '').split(' ')
        .map((id) => (document.getElementById(id) || {}).innerText || '').join(' | '),
    value: e.value === undefined ? null : e.value,
    aria_valuenow: e.getAttribute('aria-valuenow'),
    testid: (e.closest('[data-testid^=st]') || {}).dataset ?
        e.closest('[data-testid^=st]').dataset.testid : null,
  }))"""


def probe(page, name: str, locate, root_sel: str, out: Path) -> dict:
    found, err = None, None
    try:
        loc = locate()
        loc.first.wait_for(state="attached", timeout=10_000)
        found = {"count": loc.count(),
                 "value": loc.first.input_value() if loc.first.evaluate(
                     "(e) => 'value' in e") else None}
    except Exception as exc:          # the test's own lookup failed
        err = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
    page.screenshot(path=str(out / f"{name}.png"))
    controls = page.locator(root_sel).first.evaluate(DUMP_JS)
    return {"lookup_found": found, "lookup_error": err, "controls": controls}


def main() -> None:
    label = sys.argv[1]
    out = HERE / label
    out.mkdir(parents=True, exist_ok=True)
    import streamlit
    from playwright.sync_api import sync_playwright
    report = {"streamlit": streamlit.__version__, "python": sys.executable}
    srv = AppServer(out / "streamlit.log", developer=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1600, "height": 1100})
            page.set_default_timeout(60_000)

            # a — Label page, phase selectbox of row 0
            LabelPage(page).open(srv.url)
            report["a_phase_row_0"] = probe(
                page, "a_phase_row_0",
                lambda: page.get_by_label("phase, row 0", exact=True),
                '[data-testid="stMain"]', out)

            # b, c — Calibrate sidebar
            page.goto(srv.url)
            page.wait_for_selector("text=Display mode", timeout=RENDER_TIMEOUT)
            LabelPage(page).settle()
            report["b_boundary_padding"] = probe(
                page, "b_boundary_padding",
                lambda: page.get_by_label("Boundary padding", exact=True),
                '[data-testid="stSidebar"]', out)
            report["c_sidebar_slider"] = probe(
                page, "c_sidebar_slider",
                lambda: page.locator('[data-testid="stSidebar"] [data-testid="stSlider"] '
                                     'input[type="range"]'),
                '[data-testid="stSidebar"]', out)
            browser.close()
    finally:
        srv.stop()
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    for k in ("a_phase_row_0", "b_boundary_padding", "c_sidebar_slider"):
        print(k, "found:", report[k]["lookup_found"], "| error:", report[k]["lookup_error"])


if __name__ == "__main__":
    main()
