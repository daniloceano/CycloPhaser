"""I1 gate (d): before/after screenshots of Calibrate, Benchmark and Label.

    python research/app_redesign/i1/capture_screenshots.py \
        --variant before --root <checkout of develop>
    python research/app_redesign/i1/capture_screenshots.py \
        --variant after --root <checkout of the branch>

Writes research/app_redesign/i1/captures/<variant>/{calibrate,benchmark,label}.png
(next to this script, whatever `--root` is) plus a manifest.json naming the
measured checkout. Fixed viewport 1600x1000, Chromium, app started from the
checkout's root (so the root .streamlit/config.toml applies, as on Streamlit
Community Cloud). The app opens on its own defaults (no upload: the bundled
example track).

How each screen is reached:
  before — Calibration tab (default) · Benchmark tab · Display mode "Label";
  after  — Calibrate (default page) · menu Benchmark · menu Developer →
           Manual labelling (with CYCLOPHASER_APP_DEV=1).
Each screenshot is the viewport only, never a full-page capture.

`--extras` (after only) writes two more, into captures/after_extras/, and leaves
the six above alone:
  label_full.png       — the Manual labelling page from top to bottom (the case
                         picker, "Default ± steps", "Overlay scale", chart,
                         table, buttons). Streamlit scrolls inside its own
                         container, so a full-page screenshot would still be one
                         viewport; instead the viewport is made as tall as the
                         page's content (width stays 1600) and the page is
                         scrolled to the top. The height used is in the manifest.
  calibrate_public.png — Calibrate with NO developer key (the public view: no
                         Developer section in the menu), viewport 1600x1000.
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
    port = s.getsockname()[1]
    s.close()
    return port


def settle(page, ms=1500):
    page.wait_for_timeout(200)
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached",
                               timeout=RENDER)
    except Exception:
        pass
    page.wait_for_timeout(ms)


def start(root: Path, developer: bool):
    port = free_port()
    env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
    env.pop("CYCLOPHASER_APP_DEV", None)
    if developer:
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


_TO_TOP_JS = """() => { window.scrollTo(0, 0);
  for (const el of document.querySelectorAll('*')) {
    if (el.scrollTop) el.scrollTop = 0; } }"""


def capture_extras(root: Path) -> None:
    from playwright.sync_api import sync_playwright

    out = HERE / "captures" / "after_extras"
    out.mkdir(parents=True, exist_ok=True)
    info = {"variant": "after_extras", "files": {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        srv, url = start(root, developer=True)
        try:
            page = browser.new_page(viewport=VIEWPORT)
            page.set_default_timeout(RENDER)
            page.goto(url)
            page.wait_for_selector("text=Display mode", timeout=RENDER)
            settle(page)
            page.locator('[data-testid="stSidebarNav"]').get_by_text(
                "Manual labelling", exact=True).click()
            page.wait_for_selector("#cp-label-chart svg", timeout=RENDER)
            settle(page, 2500)
            height = page.evaluate("""() => Math.ceil(document.querySelector(
                '[data-testid="stMainBlockContainer"]').scrollHeight)""") + 120
            page.set_viewport_size({"width": VIEWPORT["width"], "height": height})
            settle(page, 2500)
            page.evaluate(_TO_TOP_JS)
            page.wait_for_timeout(800)
            page.screenshot(path=str(out / "label_full.png"))
            info["files"]["label_full.png"] = {
                "viewport": {"width": VIEWPORT["width"], "height": height},
                "developer_key": True}
            page.close()
        finally:
            stop(srv)

        srv, url = start(root, developer=False)
        try:
            page = browser.new_page(viewport=VIEWPORT)
            page.set_default_timeout(RENDER)
            page.goto(url)
            page.wait_for_selector("text=Display mode", timeout=RENDER)
            settle(page, 2500)
            nav = page.locator('[data-testid="stSidebarNav"]').inner_text()
            assert "Developer" not in nav and "Manual labelling" not in nav, nav
            page.screenshot(path=str(out / "calibrate_public.png"))
            info["files"]["calibrate_public.png"] = {
                "viewport": VIEWPORT, "developer_key": False,
                "menu_text": nav.replace("\n", " | ")}
            page.close()
        finally:
            stop(srv)
        browser.close()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                           capture_output=True, text=True).stdout.strip()
    import streamlit
    info.update({"root_head": head, "root_has_uncommitted_changes": bool(dirty),
                 "streamlit": streamlit.__version__})
    (out / "manifest.json").write_text(json.dumps(info, indent=1) + "\n")
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["before", "after"], required=True)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--extras", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    if args.extras:
        if args.variant != "after":
            ap.error("--extras exists for the after variant only")
        capture_extras(root)
        return
    out = HERE / "captures" / args.variant
    out.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    port = free_port()
    env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
    env.pop("CYCLOPHASER_APP_DEV", None)
    if args.variant == "after":
        env["CYCLOPHASER_APP_DEV"] = "1"
    srv = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run",
         str(root / "tools" / "calibration_app" / "app.py"),
         "--server.port", str(port), "--server.headless", "true",
         "--server.fileWatcherType", "none", "--browser.gatherUsageStats", "false"],
        cwd=str(root), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/"
    try:
        for _ in range(300):
            try:
                urllib.request.urlopen(url, timeout=2).read()
                break
            except Exception:
                time.sleep(0.4)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport=VIEWPORT)
            page.set_default_timeout(RENDER)
            page.goto(url)
            page.wait_for_selector("text=Display mode", timeout=RENDER)
            settle(page, 2500)
            page.screenshot(path=str(out / "calibrate.png"))

            if args.variant == "before":
                page.get_by_role("tab", name="Benchmark").click()
            else:
                page.locator('[data-testid="stSidebarNav"]').get_by_text(
                    "Benchmark", exact=True).click()
            page.wait_for_selector("text=1 · Mode", timeout=RENDER)
            settle(page, 2000)
            page.screenshot(path=str(out / "benchmark.png"))

            if args.variant == "before":
                page.get_by_role("tab", name="Calibration").click()
                settle(page)
                page.get_by_text("Label", exact=True).first.click()
            else:
                page.locator('[data-testid="stSidebarNav"]').get_by_text(
                    "Manual labelling", exact=True).click()
            page.wait_for_selector("#cp-label-chart svg", timeout=RENDER)
            settle(page, 2500)
            page.screenshot(path=str(out / "label.png"))
            browser.close()
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                               capture_output=True, text=True).stdout.strip()
        import streamlit
        (out / "manifest.json").write_text(json.dumps({
            "variant": args.variant, "root_head": head,
            "root_has_uncommitted_changes": bool(dirty),
            "viewport": VIEWPORT, "streamlit": streamlit.__version__,
            "files": ["calibrate.png", "benchmark.png", "label.png"],
        }, indent=1) + "\n")
        print(f"wrote {out}")
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=20)
        except subprocess.TimeoutExpired:
            srv.kill()


if __name__ == "__main__":
    main()
