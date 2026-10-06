"""I3 gate (d): before (6016486) / after screenshots, fixed viewport 1600x1000.

    python research/app_redesign/i3/capture_screenshots.py --variant before --root <checkout of 6016486>
    python research/app_redesign/i3/capture_screenshots.py --variant after  --root <checkout of I3>

Writes research/app_redesign/i3/captures/<variant>/ and a manifest.json. Public
app (no developer key). Every shot is the whole 1600x1000 viewport, the main
area scrolled so that the named element is at the top.

  start.png          Calibrate as opened, nothing loaded (before: I2's one line;
                     after: the start screen)
  grid_page1.png     51 sample tracks loaded (sidebar's "Sample data"), the top
                     of the Grid: mode, columns, page size and page controls
  grid_page2.png     after only: the same after "Next ▶" (before: no pages)
  grid_page1_end.png the end of the grid of page 1: after, the bottom page
                     controls; before, the last figures of the single grid
  stats.png          after: the "Set statistics" block at the top of the
                     viewport; before: the end of the page (no such block)
  stats_durations.png after only: the box plot of durations, n per phase
  stats_sequences_dark.png after only: the same, the app served with
                     --theme.base dark (contrast of the squares and the text)
  stats_sequences.png after only: the 5 most common sequences, which include
                     ones with a repeated phase ("intensification 2", …)

The manifest also records the version the page header shows and the
`importlib.metadata` version of the interpreter that serves the app.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWPORT = {"width": 1600, "height": 1000}
RENDER = 600_000


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start(root: Path, theme: str | None = None):
    port = free_port()
    env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
    env.pop("CYCLOPHASER_APP_DEV", None)
    srv = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run",
         str(root / "tools" / "calibration_app" / "app.py"),
         "--server.port", str(port), "--server.headless", "true",
         "--server.fileWatcherType", "none", "--browser.gatherUsageStats", "false",
         *(["--theme.base", theme] if theme else [])],
        cwd=str(root), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/"
    for _ in range(300):
        try:
            urllib.request.urlopen(url, timeout=2).read()
            break
        except Exception:
            time.sleep(0.4)
    return srv, url


def stop(srv) -> None:
    srv.terminate()
    try:
        srv.wait(timeout=20)
    except subprocess.TimeoutExpired:
        srv.kill()


def settle(page, ms=1500):
    page.wait_for_timeout(200)
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached",
                               timeout=RENDER)
    except Exception:
        pass
    page.wait_for_timeout(ms)


def to_top(locator, page, offset: int = 70) -> None:
    """Scroll the main area so `locator` sits near the top of the viewport."""
    locator.evaluate("(e) => e.scrollIntoView({block: 'start'})")
    page.wait_for_timeout(300)
    page.mouse.move(1000, 500)
    page.mouse.wheel(0, -offset)
    page.mouse.move(VIEWPORT["width"] - 10, VIEWPORT["height"] - 10)
    page.wait_for_timeout(700)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["before", "after"], required=True)
    ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args()
    root, v = args.root.resolve(), args.variant
    out = HERE / "captures" / v
    out.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                          capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                                cwd=root, capture_output=True, text=True).stdout.strip())
    import streamlit
    manifest: dict = {"variant": v, "root_head": head, "root_tracked_changes": dirty,
                      "streamlit": streamlit.__version__, "viewport": VIEWPORT, "shots": {}}
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        srv, url = start(root)
        try:
            page = browser.new_page(viewport=VIEWPORT)
            page.set_default_timeout(RENDER)
            page.goto(url)
            page.wait_for_selector('[data-testid="stSidebar"]', timeout=RENDER)
            settle(page, 2500)
            page.screenshot(path=str(out / "start.png"))
            manifest["shots"]["start"] = "start.png"
            import importlib.metadata as md
            import re
            header = page.locator('[data-testid="stMain"]').get_by_text(
                "CycloPhaser ", exact=False).filter(has_text="Phase detection").first.inner_text()
            manifest["header_version"] = re.search(r"CycloPhaser (\S+)", header).group(1)
            manifest["metadata_version"] = md.version("cyclophaser")

            main_ = page.locator('[data-testid="stMain"]')
            page.locator('[data-testid="stSidebar"]').get_by_role(
                "button", name="Sample data (51 TRACK cyclones)").click()
            page.wait_for_selector("text=Consolidated diagnostics", timeout=RENDER)
            # the pointer rests on the button just pressed and its tooltip would
            # cover the shots: move it to an empty corner of the main area
            page.mouse.move(VIEWPORT["width"] - 10, VIEWPORT["height"] - 10)
            # … and the tooltip also shows while the button has the focus
            page.evaluate("() => document.activeElement && document.activeElement.blur()")
            settle(page, 3000)

            to_top(main_.get_by_text("Display mode", exact=True).first, page)
            page.screenshot(path=str(out / "grid_page1.png"))
            manifest["shots"]["grid_page1"] = "grid_page1.png"

            if v == "after":
                to_top(main_.get_by_text("Consolidated diagnostics").first, page, 520)
            else:
                to_top(main_.get_by_text("Consolidated diagnostics").first, page, 700)
            page.screenshot(path=str(out / "grid_page1_end.png"))
            manifest["shots"]["grid_page1_end"] = "grid_page1_end.png"

            if v == "after":
                to_top(main_.get_by_text("Set statistics", exact=True).first, page)
                page.wait_for_timeout(1500)          # the Plotly chart draws late
                page.screenshot(path=str(out / "stats.png"))
                manifest["shots"]["stats"] = "stats.png"
                to_top(main_.locator('[data-testid="stPlotlyChart"]').last, page, 120)
                page.wait_for_timeout(1000)
                page.screenshot(path=str(out / "stats_durations.png"))
                manifest["shots"]["stats_durations"] = "stats_durations.png"
                to_top(main_.get_by_text("most common phase sequences").first, page)
                page.screenshot(path=str(out / "stats_sequences.png"))
                manifest["shots"]["stats_sequences"] = "stats_sequences.png"

                to_top(main_.get_by_text("Display mode", exact=True).first, page)
                main_.get_by_role("button", name="Next ▶").first.click()
                settle(page, 3000)
                to_top(main_.get_by_text("Display mode", exact=True).first, page)
                page.screenshot(path=str(out / "grid_page2.png"))
                manifest["shots"]["grid_page2"] = "grid_page2.png"
            else:
                main_.evaluate("(e) => window.scrollTo(0, 1e9)")
                last = main_.locator('[data-testid="stDataFrame"]').last
                last.evaluate("(e) => e.scrollIntoView({block: 'end'})")
                page.wait_for_timeout(800)
                page.screenshot(path=str(out / "stats.png"))
                manifest["shots"]["stats"] = "stats.png (before: end of the page, no block)"
                manifest["shots"]["grid_page2"] = "absent: before has no grid pages"
            page.close()
        finally:
            stop(srv)
        if v == "after":
            srv, url = start(root, theme="dark")
            try:
                page = browser.new_page(viewport=VIEWPORT)
                page.set_default_timeout(RENDER)
                page.goto(url)
                page.wait_for_selector('[data-testid="stSidebar"]', timeout=RENDER)
                settle(page, 2500)
                page.locator('[data-testid="stSidebar"]').get_by_role(
                    "button", name="Sample data (51 TRACK cyclones)").click()
                page.wait_for_selector("text=most common phase sequences", timeout=RENDER)
                page.mouse.move(VIEWPORT["width"] - 10, VIEWPORT["height"] - 10)
                page.evaluate("() => document.activeElement && document.activeElement.blur()")
                settle(page, 3000)
                to_top(page.locator('[data-testid="stMain"]').get_by_text(
                    "most common phase sequences").first, page)
                page.screenshot(path=str(out / "stats_sequences_dark.png"))
                manifest["shots"]["stats_sequences_dark"] = "stats_sequences_dark.png"
                page.close()
            finally:
                stop(srv)
        browser.close()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
