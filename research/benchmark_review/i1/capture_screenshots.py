"""I1 gate (d): real screenshots of the Compare page, public app, 1600x1000.

    python research/benchmark_review/i1/capture_screenshots.py [--out DIR]

Uses the test harness (tests/browser_harness.py: `streamlit run` of the app on
a free port, no developer key) and the counted `Session` of
tests/test_compare_browser.py, so the screenshots show the same path the e1
test drives. Starting point as in e1: Calibrate, High cutoff five steps up
(18 → 48), "Sample data (51 TRACK cyclones)".

  01_empty.png         Compare with no track loaded (a fresh session)
  02_run_blocked.png   tracks loaded, no configuration: Run blocked, reason shown
  03_columns.png       Current settings, Defaults and an uploaded YAML
                       (cyclophaser_params-track.yaml): the cards, each
                       difference one line; no filled-keys warning for that file
  04_results.png       after Run: the Reference selector at the top of
                       "4 · Results", the relative table, the per-configuration counts
  05_side_by_side.png  per track, Side by side
  06_stacked.png       per track, Stacked
  07_filter.png        "Show only cyclones whose sequence differs", Side by side
  08_reference.png     the reference switched to Defaults: the table follows
  09_filled_warning.png a 4th column, params-track WITHOUT prominence_relative
                       and boundary_padding (written by this script to a
                       temporary file): the filled-keys warning lists both
  10_limit.png         four columns: the add controls disabled, reason shown
  11_invert_help.png   the "Invert selection" help tooltip open (mouse over it)
  full_page.png        the whole page after Run with three columns. Streamlit
                       scrolls its main container, not the document, so
                       `full_page=True` alone captures the viewport (round 1's
                       full_page.png was a copy of 04_results.png); the
                       viewport is first made as tall as the content

manifest.json records the interpreter, the streamlit version, HEAD, the number
of tracked files changed in the working tree, and each file's real size in
pixels, read from its PNG header.
"""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tests"))

from browser_harness import AppServer  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

import test_compare_browser as T  # noqa: E402


def _top(s, text: str) -> None:
    """Scroll the main area so that `text` is at the top of the viewport."""
    s.page.locator(T.MAIN).get_by_text(text, exact=True).first.evaluate(
        "e => e.scrollIntoView({block: 'start'})")
    s.page.wait_for_timeout(600)


def _shot(s, out: Path, name: str) -> None:
    s.page.screenshot(path=str(out / name))


_CONTENT_HEIGHT_JS = """() => Math.max(...[
    document.querySelector('[data-testid="stMain"]'),
    document.querySelector('[data-testid="stAppViewContainer"]'),
    document.scrollingElement].filter(Boolean).map(e => e.scrollHeight))"""


def _full_page(s, out: Path, name: str) -> None:
    """The whole page: the viewport is made as tall as the scrolled content,
    then captured, then restored."""
    size = dict(s.page.viewport_size)
    s.page.evaluate("() => window.scrollTo(0, 0)")
    s.page.locator(T.MAIN).evaluate("e => e.scrollTo(0, 0)")
    height = int(s.page.evaluate(_CONTENT_HEIGHT_JS)) + 40
    s.page.set_viewport_size({"width": size["width"], "height": height})
    s.lp.settle(2000)
    s.images_loaded()
    height = int(s.page.evaluate(_CONTENT_HEIGHT_JS)) + 40   # after re-layout
    s.page.set_viewport_size({"width": size["width"], "height": height})
    s.lp.settle(1500)
    s.page.screenshot(path=str(out / name), full_page=True)
    s.page.set_viewport_size(size)
    s.lp.settle(800)


def _png_size(path: Path) -> list[int]:
    with open(path, "rb") as f:
        head = f.read(24)
    return list(struct.unpack(">II", head[16:24]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "captures"))
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    import streamlit
    srv = AppServer(out / "streamlit.log", developer=False).start()
    try:
        with sync_playwright() as pw:
            s = T.Session(pw, srv.url)
            s.menu("Compare", "Compare configurations")
            _shot(s, out, "01_empty.png")
            s.close()

            s = T.Session(pw, srv.url)
            s.start()
            s.menu("Compare", "Compare configurations")
            _top(s, "2 · Configurations")
            _shot(s, out, "02_run_blocked.png")
            s.click("Add Current settings")
            s.click("Add Defaults")
            s.upload(T.CONFIG)
            s.wait(T.CONFIG.stem)
            _top(s, "2 · Configurations")
            _shot(s, out, "03_columns.png")
            s.click("Run")
            s.wait("Relative to Current settings")
            s.images_loaded()
            _top(s, "4 · Results")
            _shot(s, out, "04_results.png")
            _full_page(s, out, "full_page.png")
            _top(s, "Per track")
            _shot(s, out, "05_side_by_side.png")
            s.check("Stacked")
            s.images_loaded()
            _top(s, "Per track")
            _shot(s, out, "06_stacked.png")
            s.check("Side by side")
            s.check("Show only cyclones whose sequence differs from the reference")
            s.images_loaded()
            _top(s, "Per track")
            _shot(s, out, "07_filter.png")
            s.choose("Reference", "Defaults")
            s.wait("Relative to Defaults")
            s.images_loaded()
            _top(s, "4 · Results")
            _shot(s, out, "08_reference.png")
            # a 4th column whose file lacks two keys the package now sets otherwise
            import yaml
            doc = yaml.safe_load(T.CONFIG.read_text())
            doc["phase_params"].pop("prominence_relative", None)
            doc["filter_params"].pop("boundary_padding", None)
            tmp = Path(tempfile.mkdtemp()) / "params-track-older.yaml"
            tmp.write_text(yaml.safe_dump(doc, sort_keys=False))
            s.page.locator(f'{T.MAIN} [data-testid="stFileUploader"] '
                           'input[type="file"]').set_input_files(str(tmp))
            s.lp.settle()
            s.wait("params-track-older")
            s.wait("which differ from the package's defaults")
            s.page.locator(T.MAIN).get_by_text(
                "which differ from the package's defaults", exact=False
            ).first.scroll_into_view_if_needed()
            s.page.wait_for_timeout(600)
            _shot(s, out, "09_filled_warning.png")
            _top(s, "2 · Configurations")
            _shot(s, out, "10_limit.png")
            _top(s, "1 · Tracks")
            s.page.locator(T.MAIN).get_by_role("button", name="Invert selection").hover()
            s.page.get_by_text("Selects the tracks that are not selected").first.wait_for(
                state="visible", timeout=30_000)
            s.page.wait_for_timeout(400)
            _shot(s, out, "11_invert_help.png")
            errors = list(s.lp.errors)
            s.close()
    finally:
        srv.stop()
    (out / "streamlit.log").unlink(missing_ok=True)
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           cwd=ROOT, capture_output=True, text=True).stdout
    manifest = {"python": sys.executable.replace(str(Path.home()), "~"),
                "streamlit": streamlit.__version__, "head": head,
                "tracked_files_changed": len(dirty.splitlines()),
                "viewport": "1600x1000", "browser_errors": errors,
                "files": {p.name: {"width_px": _png_size(p)[0], "height_px": _png_size(p)[1]}
                          for p in sorted(out.glob("*.png"))}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
