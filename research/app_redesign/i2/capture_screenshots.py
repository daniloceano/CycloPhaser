"""I2 gate (d): before (63f074f) / after screenshots, fixed viewport 1600x1000.

    python research/app_redesign/i2/capture_screenshots.py --variant before --root <checkout of 63f074f>
    python research/app_redesign/i2/capture_screenshots.py --variant after  --root <checkout of I2>

Writes research/app_redesign/i2/captures/<variant>/ (next to this script) and a
manifest.json. Every shot is the 1600x1000 viewport, or a clip of it; a long
sidebar is shot in PARTS, scrolling its own container between shots.

  sidebar_public_NN.png  Calibrate sidebar, no developer key, top to bottom
  sidebar_dev_NN.png     the same with the developer key
  main_no_data.png       Calibrate as opened (before: the example was loaded
                         silently; after: nothing loaded)
  save.png               after: the Save results dialog, example loaded;
                         before: where the exports were (the main area's
                         "Export all (ZIP)", example loaded)
  advanced_notice.png    after: the Advanced notice with one advanced value
                         changed and "Show which" on; before: the same value
                         changed in the old sidebar (no notice existed)
  label_overlays.png     the Manual labelling page (developer key) around the
                         "Show filtered/smoothed overlays" box
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
RENDER = 300_000


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start(root: Path, dev: bool):
    port = free_port()
    env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
    env.pop("CYCLOPHASER_APP_DEV", None)
    if dev:
        env["CYCLOPHASER_APP_DEV"] = "1"
    srv = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run",
         str(root / "tools" / "calibration_app" / "app.py"),
         "--server.port", str(port), "--server.headless", "true",
         "--server.fileWatcherType", "none", "--browser.gatherUsageStats", "false"],
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


def open_app(page, url):
    page.goto(url)
    page.wait_for_selector('[data-testid="stSidebar"]', timeout=RENDER)
    settle(page, 2500)


def sidebar_parts(page, out: Path, stem: str) -> list[str]:
    box = page.locator('[data-testid="stSidebar"]').bounding_box()
    clip = {"x": box["x"], "y": 0, "width": box["width"], "height": VIEWPORT["height"]}
    content = page.locator('[data-testid="stSidebarContent"]')
    total = content.evaluate("(e) => e.scrollHeight")
    step = VIEWPORT["height"] - 120
    names, y, i = [], 0, 1
    while True:
        content.evaluate(f"(e) => {{ e.scrollTop = {y}; }}")
        page.wait_for_timeout(500)
        name = f"{stem}_{i:02d}.png"
        page.screenshot(path=str(out / name), clip=clip)
        names.append(name)
        if y + VIEWPORT["height"] >= total:
            break
        y += step
        i += 1
    content.evaluate("(e) => { e.scrollTop = 0; }")
    return names


def load_example(page, variant):
    if variant == "after":
        page.get_by_role("button", name="Try example data").click()
        page.wait_for_selector("text=example_file", timeout=RENDER)
    settle(page, 2500)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["before", "after"], required=True)
    ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args()
    root, v = args.root.resolve(), args.variant
    out = HERE / "captures" / v
    out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    shots: dict = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        srv, url = start(root, dev=False)
        try:
            page = browser.new_page(viewport=VIEWPORT)
            page.set_default_timeout(RENDER)
            open_app(page, url)
            shots["sidebar_public"] = sidebar_parts(page, out, "sidebar_public")
            page.screenshot(path=str(out / "main_no_data.png"))
            shots["main_no_data"] = "main_no_data.png"
            page.close()
        finally:
            stop(srv)

        srv, url = start(root, dev=True)
        try:
            page = browser.new_page(viewport=VIEWPORT)
            page.set_default_timeout(RENDER)
            open_app(page, url)
            shots["sidebar_dev"] = sidebar_parts(page, out, "sidebar_dev")

            # the Advanced notice (after) / the same change in the old sidebar
            if v == "after":
                page.locator('[data-testid="stSidebar"] [data-testid="stExpander"] summary'
                             ).filter(has_text="Intensification").first.click()
                page.wait_for_timeout(500)
            slider = page.locator('[data-testid="stSidebar"] [data-testid="stSlider"]').filter(
                has_text="Max. intensification gap").locator(
                'input[type="range"], [role="slider"]').first
            if v == "before":
                page.locator('[data-testid="stSidebar"] [data-testid="stExpander"] summary'
                             ).filter(has_text="Advanced — intensification").first.click()
                page.wait_for_timeout(500)
            for _ in range(4):
                slider.press("ArrowRight")
                settle(page, 400)
            settle(page, 1500)
            if v == "after":
                adv = page.locator('[data-testid="stSidebar"]').get_by_text(
                    "Advanced", exact=True).first
                adv.scroll_into_view_if_needed()
                page.locator('[data-testid="stSidebar"]').get_by_text(
                    "Show which", exact=True).click()
                settle(page, 800)
            else:
                slider.scroll_into_view_if_needed()
            page.screenshot(path=str(out / "advanced_notice.png"))
            shots["advanced_notice"] = "advanced_notice.png"
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)

            # Save results dialog (after) / the old export buttons (before)
            load_example(page, v)
            if v == "after":
                page.get_by_role("button", name="Save results").click()
                page.get_by_role("dialog").wait_for(timeout=RENDER)
                page.wait_for_timeout(800)
            else:
                page.locator('[data-testid="stMain"]').get_by_text(
                    "Export all (ZIP)").first.scroll_into_view_if_needed()
            page.screenshot(path=str(out / "save.png"))
            shots["save"] = "save.png"
            page.close()

            # Label page, overlay box
            page = browser.new_page(viewport=VIEWPORT)
            page.set_default_timeout(RENDER)
            open_app(page, url)
            if v == "after":
                page.locator('[data-testid="stSidebarNav"]').get_by_text(
                    "Manual labelling", exact=True).click()
            else:
                page.locator('[data-testid="stSidebarNav"]').get_by_text(
                    "Manual labelling", exact=True).click()
            page.wait_for_selector("#cp-label-chart svg", timeout=RENDER)
            settle(page, 2500)
            page.get_by_role("checkbox", name="Show filtered/smoothed overlays",
                             exact=False).first.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            page.screenshot(path=str(out / "label_overlays.png"))
            shots["label_overlays"] = "label_overlays.png"
            page.close()
        finally:
            stop(srv)
        browser.close()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                          text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True,
                           text=True).stdout.strip()
    import streamlit
    (out / "manifest.json").write_text(json.dumps({
        "variant": v, "root_head": head, "root_has_uncommitted_changes": bool(dirty),
        "viewport": VIEWPORT, "streamlit": streamlit.__version__, "shots": shots},
        indent=1) + "\n")
    print(json.dumps(shots))


if __name__ == "__main__":
    main()
