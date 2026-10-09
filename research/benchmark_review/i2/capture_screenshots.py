"""I2 gate (d): real screenshots of the Validate page, developer key, 1600x1000.

    python research/benchmark_review/i2/capture_screenshots.py [--out DIR]

Uses the test harness (tests/browser_harness.py: `streamlit run` of the app on a
free port, developer key on) and the counted session of
tests/test_validate_browser.py. Starting point as in e1: Calibrate opened once.

  01_arrival.png        Validate on arrival: title, sentence, status line, tracks
  02_run_blocked.png    no configuration: Run blocked, the reason in visible text
  03_cards.png          Defaults, params-track (configs/), published v2.0.0 and an
                        uploaded older file (params-track without
                        prominence_relative and boundary_padding, with an
                        `evaluation` block; written by this script to a
                        temporary file and removed)
  04_provenance.png     the older file's "Provenance" open: sha256, commit, keys
                        not read, keys filled, pre-filter-fix, the historical
                        annotation "not a score"
  05_train_block.png    after Run: Reference on top, "Agreement with manual
                        labels", the train block, both instruments
  06_disagreements.png  one column's list of tracks that disagree, open
  07_side_by_side.png   per track, label panel first with its tolerance bands
  08_stacked.png        per track, Stacked, label panel on top
  09_filter.png         "Show only tracks that disagree with the label (any column)"
  10_adjudicated.png    the batch on and Run: train n = 49 and adjudicated n = 5
  11_limit.png          six columns: add controls disabled, reason shown
  12_validate_filled_warning.png  the older file's card at six columns
  13_compare_filled_warning.png   the same file as the 4th Compare column
                        (pending item 2: no word broken mid-word)
  Round 2 (checkpoint corrections), same session unless noted:
  14_disagreement_headers.png     the lists' headers: counts per instrument (R2)
  15_snapshot_note.png            batch on, published v2.0.0: "2 of 49 tracks are
                                  not in this snapshot … not counted" (R3)
  16_validate_results_current.png "Results are current" next to Run (F2)
  17_compare_results_current.png  the same on Compare (F2)
  18_validate_warning_dark.png    the warning block, dark theme (R1)
  19_compare_warning_dark.png     the same on Compare, dark theme (R1)
                                  (a second server, STREAMLIT_THEME_BASE=dark)
  full_page.png         the whole page after the first Run (viewport made as
                        tall as the content, as in I1 round 2)

manifest.json records the interpreter, streamlit, HEAD, the number of tracked
files changed in the working tree, browser errors and each PNG's real size.
"""

from __future__ import annotations

import argparse
import json
import os
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

import test_validate_browser as T  # noqa: E402

MAIN = T.MAIN
_CONTENT_HEIGHT_JS = """() => Math.max(...[
    document.querySelector('[data-testid="stMain"]'),
    document.querySelector('[data-testid="stAppViewContainer"]'),
    document.scrollingElement].filter(Boolean).map(e => e.scrollHeight))"""


def _top(s, text: str, exact: bool = True) -> None:
    s.page.locator(MAIN).get_by_text(text, exact=exact).first.evaluate(
        "e => e.scrollIntoView({block: 'start'})")
    s.page.wait_for_timeout(700)


def _shot(s, out: Path, name: str) -> None:
    s.page.screenshot(path=str(out / name))


def _full_page(s, out: Path, name: str) -> None:
    size = dict(s.page.viewport_size)
    s.page.evaluate("() => window.scrollTo(0, 0)")
    s.page.locator(MAIN).evaluate("e => e.scrollTo(0, 0)")
    height = int(s.page.evaluate(_CONTENT_HEIGHT_JS)) + 40
    s.page.set_viewport_size({"width": size["width"], "height": height})
    s.lp.settle(2000)
    s.images_loaded()
    height = int(s.page.evaluate(_CONTENT_HEIGHT_JS)) + 40
    s.page.set_viewport_size({"width": size["width"], "height": height})
    s.lp.settle(1500)
    s.page.screenshot(path=str(out / name), full_page=True)
    s.page.set_viewport_size(size)
    s.lp.settle(800)


def _png_size(path: Path) -> list[int]:
    with open(path, "rb") as f:
        head = f.read(24)
    return list(struct.unpack(">II", head[16:24]))


def _older_file(tmpdir: Path) -> Path:
    import yaml
    doc = yaml.safe_load(T.CONFIG.read_text())
    doc["phase_params"].pop("prominence_relative", None)
    doc["filter_params"].pop("boundary_padding", None)
    doc["evaluation"] = {"bad_cases": ["20150069", "20170154"], "bad_cases_count": 2,
                         "total_cyclones": 51}
    path = tmpdir / "params-track-older.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False))
    return path


def _expander(s, label_start: str, nth: int = 0):
    exp = s.page.locator(f'{MAIN} [data-testid="stExpander"]').filter(
        has_text=label_start).nth(nth)
    exp.locator("summary").click()
    s.lp.settle()
    return exp


def _scroll_to_warning(s) -> None:
    s.page.locator(f'{MAIN} [data-testid="stMarkdownContainer"] div').filter(
        has_text="absent from this file were filled").last.evaluate(
        "e => e.scrollIntoView({block: 'center'})")
    s.page.wait_for_timeout(700)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "captures"))
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    import streamlit
    tmpdir = Path(tempfile.mkdtemp())
    older = _older_file(tmpdir)
    srv = AppServer(out / "streamlit.log", developer=True).start()
    errors: list = []
    try:
        with sync_playwright() as pw:
            s = T.VSession(pw, srv.url)
            s.menu(T.PAGE, T.PAGE)
            _shot(s, out, "01_arrival.png")
            _top(s, "2 · Configurations")
            _shot(s, out, "02_run_blocked.png")
            s.click("Add Defaults")
            s.choose("Calibration file (research/labels/configs/)", T.CONFIG.name)
            s.click("Add file")
            s.choose("Published release (research/snapshots/)", "v2.0.0")
            s.click("Add release")
            s.upload(older)
            s.wait(older.stem)
            _top(s, "2 · Configurations")
            _shot(s, out, "03_cards.png")
            exp = _expander(s, "Provenance", 3)
            exp.evaluate("e => e.scrollIntoView({block: 'start'})")
            s.page.wait_for_timeout(700)
            _shot(s, out, "04_provenance.png")
            exp.locator("summary").click()
            s.lp.settle()
            s.click("Run")
            s.wait("Train — n = 47")
            s.images_loaded()
            _top(s, "4 · Results")
            _shot(s, out, "05_train_block.png")
            exp = _expander(s, "Tracks that disagree with the label — params-track")
            exp.evaluate("e => e.scrollIntoView({block: 'start'})")
            s.page.wait_for_timeout(700)
            _shot(s, out, "06_disagreements.png")
            exp.locator("summary").click()
            s.lp.settle()
            _full_page(s, out, "full_page.png")
            _top(s, "Per track")
            _shot(s, out, "07_side_by_side.png")
            s.check("Stacked")
            s.images_loaded()
            _top(s, "Per track")
            _shot(s, out, "08_stacked.png")
            s.check("Side by side")
            s.check(T.FILTER)
            s.images_loaded()
            _top(s, "Per track")
            _shot(s, out, "09_filter.png")
            s.check(T.FILTER)
            s.check("Include swell_item30 batch")
            s.click("Run")
            s.wait("Adjudicated — n = 5")
            _top(s, "Agreement with manual labels")
            _shot(s, out, "10_adjudicated.png")
            s.page.locator(MAIN).get_by_text("Tracks that disagree with the label",
                                             exact=False).first.evaluate(
                "e => e.scrollIntoView({block: 'center'})")
            s.page.wait_for_timeout(700)
            _shot(s, out, "14_disagreement_headers.png")
            s.page.locator(MAIN).get_by_text("are not in this snapshot",
                                             exact=False).first.evaluate(
                "e => e.scrollIntoView({block: 'center'})")
            s.page.wait_for_timeout(700)
            _shot(s, out, "15_snapshot_note.png")
            _top(s, "3 · Run")
            _shot(s, out, "16_validate_results_current.png")
            s.click("Add Current settings")
            s.click("Add Current settings")
            s.wait("6 configurations is the limit")
            _top(s, "2 · Configurations")
            _shot(s, out, "11_limit.png")
            _scroll_to_warning(s)
            _shot(s, out, "12_validate_filled_warning.png")
            errors += list(s.lp.errors)
            s.close()

            s = T.VSession(pw, srv.url)
            s.start()
            s.menu("Compare", "Compare configurations")
            s.click("Add Current settings")
            s.click("Add Defaults")
            s.click("Add Current settings")
            s.upload(older)
            s.wait(older.stem)
            s.wait("4 configurations is the limit")
            _scroll_to_warning(s)
            _shot(s, out, "13_compare_filled_warning.png")
            s.click("Run")
            s.wait("Results are current")
            _top(s, "3 · Run")
            _shot(s, out, "17_compare_results_current.png")
            errors += list(s.lp.errors)
            s.close()
    finally:
        srv.stop()
    # the dark theme, on a second server
    os.environ["STREAMLIT_THEME_BASE"] = "dark"
    srv = AppServer(out / "streamlit.log", developer=True).start()
    try:
        with sync_playwright() as pw:
            s = T.VSession(pw, srv.url)
            s.start()                              # on Calibrate: sample data
            s.menu("Compare", "Compare configurations")
            s.click("Add Current settings")
            s.upload(older)
            s.wait(older.stem)
            _scroll_to_warning(s)
            _shot(s, out, "19_compare_warning_dark.png")
            s.menu(T.PAGE, T.PAGE)
            s.upload(older)
            s.wait(older.stem)
            _scroll_to_warning(s)
            _shot(s, out, "18_validate_warning_dark.png")
            errors += list(s.lp.errors)
            s.close()
    finally:
        srv.stop()
        os.environ.pop("STREAMLIT_THEME_BASE", None)
        older.unlink(missing_ok=True)
        tmpdir.rmdir()
    (out / "streamlit.log").unlink(missing_ok=True)
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           cwd=ROOT, capture_output=True, text=True).stdout
    manifest = {"python": sys.executable.replace(str(Path.home()), "~"),
                "streamlit": streamlit.__version__, "head": head,
                "tracked_files_changed": len(dirty.splitlines()),
                "viewport": "1600x1000", "browser_errors": errors,
                "temporary_file_removed": not older.exists(),
                "files": {p.name: {"width_px": _png_size(p)[0], "height_px": _png_size(p)[1]}
                          for p in sorted(out.glob("*.png"))}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
