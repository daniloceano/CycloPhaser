"""I3 gate (d): real screenshots after the Benchmark page's removal, 1600x1000.

    python research/benchmark_review/i3/capture_screenshots.py [--out DIR]

Two servers from the test harness (tests/browser_harness.py): the PUBLIC app
(no developer key) and the developer one.

  01_public_menu.png           public app as opened: Calibration = Calibrate, Compare
  02_public_benchmark_address.png  /benchmark on the public app: what Streamlit shows
  03_public_after_notice.png   the same after closing the notice (Escape): Calibrate
  04_developer_menu.png        developer app as opened: + Developer = Manual
                               labelling, Validate against labels
  05_developer_benchmark_address.png  /benchmark on the developer app
  06_f5_headers.png            Validate, Defaults × params-track, Run: the
                               disagreement headers ("N tracks differ", "N tracks
                               with a boundary outside its tolerance")
  07_f5_header_open.png        one of them open

manifest.json records the interpreter, streamlit, HEAD, the number of tracked
files changed in the working tree, the notice text, browser errors and each
PNG's real size.
"""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tests"))

from browser_harness import RENDER_TIMEOUT, AppServer, LabelPage  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

import test_validate_browser as T  # noqa: E402

MAIN = T.MAIN
SIZE = {"width": 1600, "height": 1000}


def _png_size(path: Path) -> list[int]:
    with open(path, "rb") as f:
        head = f.read(24)
    return list(struct.unpack(">II", head[16:24]))


def _opened(pw, url: str, path: str = ""):
    browser = pw.chromium.launch()
    page = browser.new_page(viewport=SIZE)
    page.set_default_timeout(60_000)
    lp = LabelPage(page)
    page.goto(url.rstrip("/") + path)
    page.wait_for_selector("text=1 · Data", timeout=RENDER_TIMEOUT)
    lp.settle(1500)
    return browser, page, lp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "captures"))
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    import streamlit
    pub = AppServer(out / "streamlit_public.log", developer=False).start()
    dev = AppServer(out / "streamlit_dev.log", developer=True).start()
    errors: list = []
    notices: dict = {}
    try:
        with sync_playwright() as pw:
            for tag, srv, n in (("public", pub, 1), ("developer", dev, 4)):
                browser, page, lp = _opened(pw, srv.url)
                page.screenshot(path=str(out / f"{n:02d}_{tag}_menu.png"))
                errors += [f"{tag} menu: {e}" for e in lp.errors]
                browser.close()
                browser, page, lp = _opened(pw, srv.url, "/benchmark")
                dialog = page.get_by_role("dialog")
                notices[tag] = {"url_after": page.url.replace(srv.url, "<server>/"),
                                "notice": dialog.first.inner_text() if dialog.count() else ""}
                page.screenshot(path=str(out / f"{n + 1:02d}_{tag}_benchmark_address.png"))
                if tag == "public":
                    page.keyboard.press("Escape")
                    dialog.first.wait_for(state="hidden", timeout=RENDER_TIMEOUT)
                    lp.settle()
                    page.screenshot(path=str(out / "03_public_after_notice.png"))
                errors += [f"{tag} /benchmark: {e}" for e in lp.errors]
                browser.close()

            s = T.VSession(pw, dev.url)
            s.menu(T.PAGE, T.PAGE)
            s.click("Add Defaults")
            s.choose("Calibration file (research/labels/configs/)", T.CONFIG.name)
            s.click("Add file")
            s.click("Run")
            s.wait("Train — n = 47")
            s.images_loaded()
            head = s.page.locator(MAIN).get_by_text("Tracks that disagree with the label",
                                                    exact=False)
            head.first.evaluate("e => e.scrollIntoView({block: 'center'})")
            s.page.wait_for_timeout(700)
            s.page.screenshot(path=str(out / "06_f5_headers.png"))
            exp = s.page.locator(f'{MAIN} [data-testid="stExpander"]').filter(
                has_text="Tracks that disagree with the label — params-track").first
            exp.locator("summary").click()
            s.lp.settle()
            exp.evaluate("e => e.scrollIntoView({block: 'start'})")
            s.page.wait_for_timeout(700)
            s.page.screenshot(path=str(out / "07_f5_header_open.png"))
            headers = [t.strip() for t in head.all_inner_texts()]
            errors += [f"validate: {e}" for e in s.lp.errors]
            s.close()
    finally:
        pub.stop()
        dev.stop()
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                                    text=True).stdout.strip()
    manifest = {
        "python": sys.executable.replace(str(Path.home()), "~"),
        "streamlit": streamlit.__version__,
        "head": git("rev-parse", "--short", "HEAD"),
        "tracked_files_changed": len(git("status", "--porcelain",
                                         "--untracked-files=no").splitlines()),
        "benchmark_address": notices,
        "f5_headers": headers,
        "browser_errors": errors,
        "png": {p.name: _png_size(p) for p in sorted(out.glob("*.png"))},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    for log in out.glob("streamlit_*.log"):
        log.unlink()
    print(json.dumps(manifest, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
