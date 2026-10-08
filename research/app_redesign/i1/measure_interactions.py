"""I1 observation: cost of one Label interaction and one Benchmark interaction,
before (develop) and after (feat/app-redesign). See PREVISOES.md, written first.

    python research/app_redesign/i1/measure_interactions.py \
        --variant before --root <checkout of develop> --out before.json
    python research/app_redesign/i1/measure_interactions.py \
        --variant after  --root <checkout of the branch> --out after.json

`--root` is the checkout whose app is measured; this script itself can live in
another one. The app is run with `streamlit run <root>/tools/calibration_app/
app.py`, cwd = root, through a LAUNCHER that changes nothing in the app and adds
two counters, written one line per event to a log file:

* `CALL <name>` for every call of a function decorated with `st.cache_data` —
  hit or miss, both count — so "the detection of Calibrate ran" is a count of
  `CALL _run_get_periods` (one per loaded track per script run);
* `RUN <seconds>` for every script run, timed around ScriptRunner._run_script on
  the server.

Steps, in Chromium (viewport 1600x1000): open the app, tick "Load all test
cyclones" (51 tracks) and let it settle; then
  Label     — before: Display mode -> "Label"; after: menu -> Manual labelling;
              then 5 x click "Next ▸";
  Benchmark — before: the Benchmark tab; after: menu -> Benchmark;
              then 5 x click "Show manual labels as a first column".
Per click: the server time of the script run(s) the click caused (sum of RUN
lines appended), the `_run_get_periods` calls it caused, and the client wall
time from the click until the page is quiet again.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

LAUNCHER = r'''
import functools, sys, time
log_path = sys.argv[1]
def _log(line):
    with open(log_path, "a") as f:
        f.write(line + "\n")

import streamlit as st
import streamlit.runtime.caching as _caching
_orig = st.cache_data

def _count(cached, name):
    @functools.wraps(cached)
    def wrapper(*a, **k):
        _log("CALL " + name)
        return cached(*a, **k)
    for attr in ("clear",):
        if hasattr(cached, attr):
            setattr(wrapper, attr, getattr(cached, attr))
    return wrapper

class _Counting:
    def __call__(self, func=None, **kw):
        if callable(func):
            return _count(_orig(func, **kw), func.__name__)
        return lambda f: _count(_orig(f, **kw), f.__name__)
    def __getattr__(self, name):
        return getattr(_orig, name)

st.cache_data = _Counting()
_caching.cache_data = st.cache_data

from streamlit.runtime.scriptrunner import script_runner as _sr
_orig_run = _sr.ScriptRunner._run_script
def _timed(self, rerun_data):
    t0 = time.perf_counter()
    try:
        return _orig_run(self, rerun_data)
    finally:
        _log("RUN %.4f" % (time.perf_counter() - t0))
_sr.ScriptRunner._run_script = _timed

from streamlit.web import cli
sys.argv = ["streamlit", "run", *sys.argv[2:]]
sys.exit(cli.main())
'''

REPS = 5
RENDER = 300_000


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def read_log(path: Path) -> list[str]:
    return path.read_text().splitlines() if path.exists() else []


def settle(page, quiet_ms=800):
    """Until the status widget is gone and the event log has been quiet."""
    page.wait_for_timeout(150)
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached",
                               timeout=RENDER)
    except Exception:
        pass
    page.wait_for_timeout(quiet_ms)


def wait_log_quiet(path: Path, quiet_s=1.0, timeout_s=600):
    last, t_end = len(read_log(path)), time.time() + timeout_s
    stable_since = time.time()
    while time.time() < t_end:
        time.sleep(0.2)
        n = len(read_log(path))
        if n != last:
            last, stable_since = n, time.time()
        elif time.time() - stable_since >= quiet_s:
            return


def one_click(page, log: Path, do_click) -> dict:
    wait_log_quiet(log)
    n0 = len(read_log(log))
    t0 = time.perf_counter()
    do_click()
    settle(page, quiet_ms=300)
    wait_log_quiet(log, quiet_s=1.0)
    wall = time.perf_counter() - t0
    new = read_log(log)[n0:]
    runs = [float(x.split()[1]) for x in new if x.startswith("RUN ")]
    return {
        "server_seconds": round(sum(runs), 4),
        "script_runs": len(runs),
        "run_get_periods_calls": sum(1 for x in new if x == "CALL _run_get_periods"),
        # includes the 1 s quiet window used to decide the click is done
        "client_wall_seconds_incl_1s_quiet": round(wall, 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["before", "after"], required=True)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    app = root / "tools" / "calibration_app" / "app.py"
    work = Path(tempfile.mkdtemp(prefix=f"i1_measure_{args.variant}_"))
    log = work / "events.log"

    from playwright.sync_api import sync_playwright

    port = free_port()
    env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
    if args.variant == "after":
        env["CYCLOPHASER_APP_DEV"] = "1"
    srv = subprocess.Popen(
        [sys.executable, "-c", LAUNCHER, str(log), str(app),
         "--server.port", str(port), "--server.headless", "true",
         "--server.fileWatcherType", "none", "--browser.gatherUsageStats", "false"],
        cwd=str(root), env=env, stdout=open(work / "server.log", "w"),
        stderr=subprocess.STDOUT)
    url = f"http://127.0.0.1:{port}/"
    try:
        for _ in range(300):
            try:
                urllib.request.urlopen(url, timeout=2).read()
                break
            except Exception:
                time.sleep(0.4)
        git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                             capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                               cwd=root, capture_output=True, text=True).stdout.strip()
        import streamlit
        result = {"variant": args.variant, "root_head": git,
                  "root_tracked_changes": bool(dirty),
                  "streamlit": streamlit.__version__, "python": sys.version.split()[0],
                  "reps": REPS}
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1600, "height": 1000})
            page.set_default_timeout(RENDER)
            page.goto(url)
            page.wait_for_selector("text=Display mode", timeout=RENDER)
            settle(page)
            page.get_by_text("Load all test cyclones", exact=False).first.click()
            settle(page, 2000)
            wait_log_quiet(log, quiet_s=2.0)
            n_tracks = sum(1 for x in read_log(log) if x == "CALL _run_get_periods")
            result["calls_while_loading_51"] = n_tracks

            # ── Label ──────────────────────────────────────────────────────
            if args.variant == "before":
                page.get_by_text("Label", exact=True).first.click()
            else:
                page.locator('[data-testid="stSidebarNav"]').get_by_text(
                    "Manual labelling", exact=True).click()
            page.wait_for_selector("text=Manual labelling — the", timeout=RENDER)
            settle(page, 1500)
            nxt = page.get_by_role("button", name="Next ▸")
            result["label"] = [one_click(page, log, nxt.click) for _ in range(REPS)]

            # ── Benchmark ──────────────────────────────────────────────────
            if args.variant == "before":
                page.get_by_role("tab", name="Benchmark").click()
            else:
                page.locator('[data-testid="stSidebarNav"]').get_by_text(
                    "Benchmark", exact=True).click()
            page.wait_for_selector("text=1 · Mode", timeout=RENDER)
            settle(page, 1500)
            box = page.get_by_label("Show manual labels as a first column", exact=True)
            lbl = box.locator("xpath=ancestor::label[1]")
            result["benchmark"] = [one_click(page, log, lbl.click) for _ in range(REPS)]
            browser.close()
        for k in ("label", "benchmark"):
            result[f"{k}_median_server_seconds"] = statistics.median(
                r["server_seconds"] for r in result[k])
            result[f"{k}_run_get_periods_calls"] = [r["run_get_periods_calls"]
                                                    for r in result[k]]
        args.out.write_text(json.dumps(result, indent=1) + "\n")
        print(json.dumps(result, indent=1))
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=20)
        except subprocess.TimeoutExpired:
            srv.kill()


if __name__ == "__main__":
    main()
