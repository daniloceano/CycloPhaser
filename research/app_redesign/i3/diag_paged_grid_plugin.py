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
* DIAG_CPU_RATE (optional): CPU throttling of the page (CDP
  Emulation.setCPUThrottlingRate), e.g. 4 or 6 — a slow machine's browser.
* Script runs: the app server of the session gets diag_server/ on PYTHONPATH and
  DIAG_RUNLOG, so its sitecustomize.py logs the wall-clock START/END of every
  script run (the app's code is not touched). Each click the test makes
  (Locator.click) and each 404 on /media/ are timestamped in the browser
  process; every script run is attributed to the last click before it.
* Controls of the test's console criterion (case B of the second correction):
  DIAG_NO_SETTLE=1 replaces the test module's `_settled` by a bare
  `lp.settle()` (no wait for the figures), so with DIAG_LATENCY_MS the /media/
  404s do happen — the test must still pass, the final state being intact;
  DIAG_INJECT_ERROR=1 logs one unrelated console.error on the page — the test
  must fail.
* One JSON line per run in <DIAG_OUT>/<label>.jsonl: outcome, the assertion
  message, console errors, image counts and the broken sources. Screenshots of
  passing runs are deleted; failing runs keep theirs.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

TARGET = "test_the_paged_grid_keeps_page_size_page_and_marks_in_the_browser"
OUT = Path(os.environ.get("DIAG_OUT", "."))
LABEL = os.environ.get("DIAG_LABEL", "run")
_state: dict = {"pages": [], "final": [], "nodeid": None, "events": [], "t0": 0.0}
HERE = Path(__file__).resolve().parent
RUNLOG = OUT / f"{LABEL}_server_runs.log"

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


def _control(selector: str) -> str:
    for pat, name in (("Next ▶", "next"), ("◀ Previous", "previous"),
                      ('option[name="24"', "page size → 24"), ("Tracks per page", "page size (open)"),
                      ('"Inspector"', "mode → Inspector"), ('"Grid"', "mode → Grid"),
                      ('"Benchmark"', "menu → Benchmark"), ('"Calibrate"', "menu → Calibrate"),
                      ("ancestor::label", "mark as bad"), ("Sample data", "sample data")):
        if pat in selector:
            return name
    return selector[-80:]


def pytest_configure(config):
    OUT.mkdir(parents=True, exist_ok=True)
    RUNLOG.unlink(missing_ok=True)
    os.environ["DIAG_RUNLOG"] = str(RUNLOG)
    os.environ["PYTHONPATH"] = os.pathsep.join(
        [str(HERE / "diag_server"), os.environ.get("PYTHONPATH", "")])
    from playwright.sync_api import Locator

    real_click = Locator.click

    def click(self, *a, **k):
        m = re.search(r"selector='(.*)'", str(self))
        _state["events"].append(("click", time.time(), _control(m.group(1) if m else str(self))))
        return real_click(self, *a, **k)

    Locator.click = click
    tests_dir = Path(config.rootpath) / "tests"
    sys.path.insert(0, str(tests_dir))
    import browser_harness
    from playwright.sync_api import Browser

    real_init = browser_harness.LabelPage.__init__

    latency = int(os.environ.get("DIAG_LATENCY_MS", "0"))
    cpu = float(os.environ.get("DIAG_CPU_RATE", "0"))

    def init(self, page):
        real_init(self, page)
        _state["pages"].append(self)
        page.on("response", lambda r: _state["events"].append(("404", time.time(), r.url))
                if r.status == 404 and "/media/" in r.url else None)
        if os.environ.get("DIAG_INJECT_ERROR") == "1":
            page.evaluate("() => console.error('diag: injected unrelated error')")
        if cpu > 1:
            page.context.new_cdp_session(page).send(
                "Emulation.setCPUThrottlingRate", {"rate": cpu})
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
    if os.environ.get("DIAG_NO_SETTLE") == "1" and hasattr(item.module, "_settled"):
        item.module._settled = lambda lp, *a, **k: lp.settle()
    _state.update(pages=[], final=[], nodeid=item.nodeid, events=[], t0=time.time(),
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
    # timeline: every script EXECUTION from the server log (see
    # diag_server/sitecustomize.py: an interrupted execution and the one that
    # follows it inside the same _run_script call are two), attributed to the
    # last click before the execution began
    runs = []                       # (start, end, how it ended)
    if RUNLOG.exists():
        begin: dict = {}
        for line in RUNLOG.read_text().splitlines():
            f = line.split()
            if f[0] == "START":
                begin[f[2]] = float(f[1])
            elif f[0] == "FIN" and f[2] in begin:
                t = float(f[1])
                if begin[f[2]] >= _state["t0"]:
                    runs.append((begin[f[2]], t, f[3]))
                begin[f[2]] = t     # a rerun inside the same call starts now
            elif f[0] == "END":
                begin.pop(f[2], None)
    clicks = [e for e in _state["events"] if e[0] == "click"]
    per_click = []
    for i, (_k, t, name) in enumerate(clicks):
        t_next = clicks[i + 1][1] if i + 1 < len(clicks) else float("inf")
        rs = [r for r in runs if t <= r[0] < t_next]
        e404 = [e for e in _state["events"] if e[0] == "404" and t <= e[1] < t_next]
        per_click.append({"control": name, "t": round(t - _state["t0"], 3),
                          "script_runs": len(rs),
                          "interrupted": sum(1 for r in rs if r[2] == "SCRIPT_STOPPED_FOR_RERUN"),
                          "runs_rel_s": [[round(a - t, 3), round(b - t, 3), how[7:]]
                                         for a, b, how in rs],
                          "media_404_rel_s": [round(e[1] - t, 3) for e in e404]})
    rec["per_click"] = per_click
    rec["media_404"] = len([e for e in _state["events"] if e[0] == "404"])
    if not failed:
        for f in _state["final"]:
            if f.get("screenshot"):
                (OUT / f["screenshot"]).unlink(missing_ok=True)
    with open(OUT / f"{LABEL}.jsonl", "a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
