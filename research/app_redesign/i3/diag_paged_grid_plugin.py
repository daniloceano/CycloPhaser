"""Diagnosis of the intermittent failure of
tests/test_app_pages_browser.py::test_the_paged_grid_keeps_page_size_page_and_marks_in_the_browser
(console: "Failed to load resource … 404" / "Image source error …/media/<hash>.png").

A pytest plugin; the test and the harness are not changed.

    DIAG_REPEAT=20 DIAG_OUT=<dir> DIAG_LABEL=<label> \\
      <python> -m pytest -p diag_paged_grid_plugin <the test's node id>
    (with research/app_redesign/i3 on PYTHONPATH)

* The test runs DIAG_REPEAT times in ONE session (parametrized, as pytest-repeat
  does), so the module's dev server is shared, as in the full Chromium run.
* Before the test's own `browser.close()` (its `finally`), every open page is
  examined: after a 3 s wait, the FINAL state — each image of the main area
  ([data-testid=stImage] img): loaded (complete, naturalWidth > 0) or broken —
  plus a full-viewport screenshot.
* The console errors the harness collected (LabelPage.errors) are read from
  every LabelPage the test created.
* DIAG_LATENCY_MS (optional, default 0): a STRESS variant. Every page the test
  opens gets Chromium's network emulation (CDP Network.emulateNetworkConditions)
  with that added latency per HTTP request — the images (/media/…) arrive late,
  as on a loaded machine, so the test's clicks land while the previous page's
  figures are still loading. The websocket that drives the app is not delayed.
* One JSON line per run in <DIAG_OUT>/<label>.jsonl: outcome, the assertion
  message, console errors, image counts and the broken sources. Screenshots of
  passing runs are deleted; failing runs keep theirs.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TARGET = "test_the_paged_grid_keeps_page_size_page_and_marks_in_the_browser"
OUT = Path(os.environ.get("DIAG_OUT", "."))
LABEL = os.environ.get("DIAG_LABEL", "run")
_state: dict = {"pages": [], "final": [], "nodeid": None}

_JS_WAIT_SETTLED = """() => [...document.querySelectorAll(
    '[data-testid="stMain"] [data-testid="stImage"] img')].every(i => i.complete)"""

# An image that did not load: ask the server for its URL now. 404 = gone for
# good (broken in the final state); 200 = it was only late.
_JS_STATUS = """async (src) => { try { return (await fetch(src, {cache: 'no-store'})).status; }
                                   catch (e) { return String(e); } }"""

_JS_IMAGES = """() => [...document.querySelectorAll(
    '[data-testid="stMain"] [data-testid="stImage"] img')].map(i => ({
        src: i.currentSrc || i.src, complete: i.complete, w: i.naturalWidth}))"""


def pytest_generate_tests(metafunc):
    n = int(os.environ.get("DIAG_REPEAT", "0"))
    if n and metafunc.function.__name__ == TARGET:
        metafunc.fixturenames.append("diag_rep")
        metafunc.parametrize("diag_rep", range(1, n + 1))


def pytest_configure(config):
    OUT.mkdir(parents=True, exist_ok=True)
    tests_dir = Path(config.rootpath) / "tests"
    sys.path.insert(0, str(tests_dir))
    import browser_harness
    from playwright.sync_api import Browser

    real_init = browser_harness.LabelPage.__init__

    latency = int(os.environ.get("DIAG_LATENCY_MS", "0"))

    def init(self, page):
        real_init(self, page)
        _state["pages"].append(self)
        if latency:
            cdp = page.context.new_cdp_session(page)
            cdp.send("Network.enable")
            cdp.send("Network.emulateNetworkConditions", {
                "offline": False, "latency": latency,
                "downloadThroughput": -1, "uploadThroughput": -1})

    browser_harness.LabelPage.__init__ = init

    real_close = Browser.close

    def close(self, *a, **k):
        for ctx in self.contexts:
            for page in ctx.pages:
                try:
                    # final state: wait until every image request has ended
                    # (loaded or failed), up to 20 s, then examine
                    page.wait_for_timeout(1000)
                    try:
                        page.wait_for_function(_JS_WAIT_SETTLED, timeout=20_000)
                    except Exception:
                        pass
                    imgs = page.evaluate(_JS_IMAGES)
                    for im in imgs:
                        if not (im["complete"] and im["w"] > 0):
                            im["status_now"] = page.evaluate(_JS_STATUS, im["src"])
                    shot = OUT / f"{LABEL}_{_state['nodeid_tag']}.png"
                    page.screenshot(path=str(shot))
                    _state["final"].append({"images": imgs, "screenshot": shot.name})
                except Exception as exc:   # the diagnosis must not mask the test
                    _state["final"].append({"error": repr(exc)})
        return real_close(self, *a, **k)

    Browser.close = close


def pytest_runtest_setup(item):
    _state.update(pages=[], final=[], nodeid=item.nodeid,
                  nodeid_tag=item.nodeid.split("[")[-1].rstrip("]"))


def pytest_runtest_makereport(item, call):
    if call.when != "call" or TARGET not in item.nodeid:
        return
    failed = call.excinfo is not None
    images = [im for f in _state["final"] for im in f.get("images", [])]
    not_loaded = [im for im in images if not (im["complete"] and im["w"] > 0)]
    broken = [f'{im["src"]} -> {im.get("status_now")}' for im in not_loaded]
    rec = {
        "label": LABEL, "run": _state["nodeid_tag"], "outcome": "failed" if failed else "passed",
        "message": (str(call.excinfo.value).splitlines()[0][:400] if failed else None),
        "console_errors": [e for p in _state["pages"] for e in p.errors],
        "final_images": len(images), "final_not_loaded": len(not_loaded),
        "final_broken": sum(1 for im in not_loaded if im.get("status_now") != 200),
        "broken_srcs": broken,
        "screenshot": [f.get("screenshot") for f in _state["final"]],
    }
    if not failed:
        for f in _state["final"]:
            if f.get("screenshot"):
                (OUT / f["screenshot"]).unlink(missing_ok=True)
    with open(OUT / f"{LABEL}.jsonl", "a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
