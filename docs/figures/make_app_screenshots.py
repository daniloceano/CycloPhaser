#!/usr/bin/env python
"""Screenshots of the calibration app for the documentation (docs/generated/app_*.png).

    python docs/figures/make_app_screenshots.py

Needs the app's dependencies (streamlit, plotly — tools/calibration_app/
requirements-app.txt) and Playwright with Chromium
(``python -m playwright install chromium``). Run it from the repository root, in
the environment the app runs in.

The script starts the app from this checkout as the PUBLIC app (the developer
key, ``CYCLOPHASER_APP_DEV``, is removed from the environment, so the developer
pages and functions are not in the pictures), drives it in Chromium at a fixed
window size and writes:

  app_start.png       Calibrate as opened: the page menu, step 1 of the sidebar
                      and the start screen
  app_sidebar.png     the whole Calibrate sidebar: 1 · Data, 2 · Starting
                      configuration, 3 · Filtering, Advanced, 4 · Save results
                      (a tall window, so it fits in one picture)
  app_grid.png        the 51 sample tracks loaded: display mode, grid columns,
                      tracks per page and the page controls above the first figures
  app_statistics.png  the "Set statistics" block at the end of the Grid
  app_save.png        the Save results dialog

Pictures of a browser are not byte-for-byte reproducible (fonts, anti-aliasing);
the script fixes everything else: the data (the bundled sample tracks), the
defaults, the window size and the steps.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "tools" / "calibration_app" / "app.py"
OUT = ROOT / "docs" / "generated"
WINDOW = {"width": 1440, "height": 900}
TALL = {"width": 1440, "height": 2300}
TIMEOUT = 600_000


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _start_app():
    port = _free_port()
    env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
    env.pop("CYCLOPHASER_APP_DEV", None)               # the public app
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(APP),
         "--server.port", str(port), "--server.headless", "true",
         "--server.fileWatcherType", "none", "--browser.gatherUsageStats", "false"],
        cwd=str(ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/"
    for _ in range(300):
        try:
            urllib.request.urlopen(url, timeout=2).read()
            return proc, url
        except Exception:
            time.sleep(0.4)
    proc.terminate()
    raise RuntimeError("the app did not start")


def _settle(page, ms: int = 1500) -> None:
    """The app has finished its run and every figure on the page has loaded."""
    page.wait_for_timeout(300)
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached",
                               timeout=TIMEOUT)
    except Exception:
        pass
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-testid="stMain"] img')]
                 .every(i => i.complete && i.naturalWidth > 0)""", timeout=TIMEOUT)
    page.wait_for_timeout(ms)


def _rest_pointer(page, size: dict) -> None:
    """Move the pointer to an empty corner and drop the focus: a button's tooltip
    shows while it is hovered or focused."""
    page.mouse.move(size["width"] - 5, size["height"] - 5)
    page.evaluate("() => document.activeElement && document.activeElement.blur()")


def _to_top(page, locator, offset: int = 60) -> None:
    locator.evaluate("(e) => e.scrollIntoView({block: 'start'})")
    page.mouse.move(900, 400)
    page.mouse.wheel(0, -offset)
    page.wait_for_timeout(800)


def _open(browser, url, size):
    page = browser.new_page(viewport=size)
    page.set_default_timeout(TIMEOUT)
    page.goto(url)
    page.wait_for_selector("text=1 · Data", timeout=TIMEOUT)
    _settle(page, 2500)
    return page


def _load_sample(page, size) -> None:
    page.locator('[data-testid="stSidebar"]').get_by_role(
        "button", name="Sample data (51 TRACK cyclones)").click()
    page.wait_for_selector("text=Set statistics", timeout=TIMEOUT)
    _rest_pointer(page, size)
    _settle(page, 2500)


def main() -> None:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    proc, url = _start_app()
    written = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()

            page = _open(browser, url, WINDOW)
            page.screenshot(path=str(OUT / "app_start.png"))
            written.append("app_start.png")
            page.close()

            page = _open(browser, url, TALL)
            sidebar = page.locator('[data-testid="stSidebar"]')
            height = page.locator('[data-testid="stSidebarContent"]').evaluate(
                "(e) => e.scrollHeight")
            box = sidebar.bounding_box()
            page.screenshot(path=str(OUT / "app_sidebar.png"),
                            clip={"x": box["x"], "y": 0, "width": box["width"],
                                  "height": min(height, TALL["height"])})
            written.append("app_sidebar.png")
            page.close()

            page = _open(browser, url, WINDOW)
            _load_sample(page, WINDOW)
            main_ = page.locator('[data-testid="stMain"]')
            _to_top(page, main_.get_by_text("Display mode", exact=True).first)
            page.screenshot(path=str(OUT / "app_grid.png"))
            written.append("app_grid.png")

            _to_top(page, main_.get_by_text("Set statistics", exact=True).first)
            page.wait_for_timeout(1500)                 # the Plotly chart draws late
            page.screenshot(path=str(OUT / "app_statistics.png"))
            written.append("app_statistics.png")

            page.locator('[data-testid="stSidebar"]').get_by_role(
                "button", name="Save results").click()
            page.get_by_role("dialog").wait_for(timeout=TIMEOUT)
            _rest_pointer(page, WINDOW)
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUT / "app_save.png"))
            written.append("app_save.png")
            page.close()
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
    for name in written:
        print(f"wrote docs/generated/{name}")


if __name__ == "__main__":
    main()
