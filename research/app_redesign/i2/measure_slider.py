"""I2 observation: PNG generations and server time of one slider change, with the
51 sample tracks loaded, in I1 (63f074f) and I2. See PREVISOES.md, written first.

    python research/app_redesign/i2/measure_slider.py --variant before --root <checkout of 63f074f> --out before.json
    python research/app_redesign/i2/measure_slider.py --variant after  --root <checkout of I2>      --out after.json

The app is started from `--root` through a LAUNCHER that changes nothing in the
app and logs, one line per event:
  * `PNG <caller>` for every `matplotlib.figure.Figure.savefig` call, named by the
    nearest calling function defined in the app's directory (a cache hit never
    reaches savefig, so only real renders count);
  * `RUN <seconds>` for every script run (ScriptRunner._run_script).

Steps (Chromium, 1600x1000): open Calibrate; load the 51 sample tracks
(before: tick "Load all test cyclones"; after: press "Sample data (51 TRACK
cyclones)"); settle; then 5 x ArrowRight on the "High cutoff (hours)" slider —
18 -> 19 -> ... -> 23, values not seen before in the session, so every step is
a real cache miss. Per step: PNGs by caller, total PNGs, server seconds.
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
from collections import Counter
from pathlib import Path

LAUNCHER = r'''
import sys, time, inspect, os
log_path, app_dir = sys.argv[1], sys.argv[2]
def _log(line):
    with open(log_path, "a") as f:
        f.write(line + "\n")

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
_orig_savefig = Figure.savefig
def _savefig(self, *a, **k):
    caller = "?"
    for fr in inspect.stack()[1:]:
        if os.path.dirname(os.path.abspath(fr.filename)) == app_dir:
            caller = fr.function
            break
    _log("PNG " + caller)
    return _orig_savefig(self, *a, **k)
Figure.savefig = _savefig

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
sys.argv = ["streamlit", "run", *sys.argv[3:]]
sys.exit(cli.main())
'''

RENDER = 300_000
REPS = 5


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def lines(path: Path) -> list[str]:
    return path.read_text().splitlines() if path.exists() else []


def quiet(path: Path, quiet_s=1.5, timeout_s=900):
    last, since, end = len(lines(path)), time.time(), time.time() + timeout_s
    while time.time() < end:
        time.sleep(0.2)
        n = len(lines(path))
        if n != last:
            last, since = n, time.time()
        elif time.time() - since >= quiet_s:
            return


def settle(page, ms=800):
    page.wait_for_timeout(200)
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached",
                               timeout=RENDER)
    except Exception:
        pass
    page.wait_for_timeout(ms)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["before", "after"], required=True)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    app = root / "tools" / "calibration_app" / "app.py"
    work = Path(tempfile.mkdtemp(prefix=f"i2_measure_{args.variant}_"))
    log = work / "events.log"

    from playwright.sync_api import sync_playwright
    port = free_port()
    env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
    env.pop("CYCLOPHASER_APP_DEV", None)
    srv = subprocess.Popen(
        [sys.executable, "-c", LAUNCHER, str(log), str(app.parent), str(app),
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
        import streamlit
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                               cwd=root, capture_output=True, text=True).stdout.strip()
        result = {"variant": args.variant, "root_head": head,
                  "root_tracked_changes": bool(dirty),
                  "streamlit": streamlit.__version__, "reps": REPS}
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1600, "height": 1000})
            page.set_default_timeout(RENDER)
            page.goto(url)
            page.wait_for_selector('[data-testid="stSidebar"]', timeout=RENDER)
            settle(page, 2000)
            if args.variant == "before":
                page.get_by_text("Load all test cyclones", exact=False).first.click()
            else:
                page.get_by_role("button", name="Sample data (51 TRACK cyclones)").click()
            settle(page, 2000)
            quiet(log, 3.0)
            n0 = len(lines(log))
            slider = page.locator('[data-testid="stSidebar"] [data-testid="stSlider"]').filter(
                has_text="High cutoff").locator('input[type="range"], [role="slider"]').first
            steps = []
            for _ in range(REPS):
                quiet(log, 1.5)
                n0 = len(lines(log))
                slider.press("ArrowRight")
                settle(page, 300)
                quiet(log, 1.5)
                new = lines(log)[n0:]
                pngs = Counter(x.split(" ", 1)[1] for x in new if x.startswith("PNG "))
                runs = [float(x.split()[1]) for x in new if x.startswith("RUN ")]
                steps.append({"png_total": sum(pngs.values()), "png_by_caller": dict(pngs),
                              "script_runs": len(runs), "server_seconds": round(sum(runs), 4)})
            browser.close()
        result["steps"] = steps
        result["median_server_seconds"] = statistics.median(s["server_seconds"] for s in steps)
        result["png_total_per_step"] = [s["png_total"] for s in steps]
        args.out.write_text(json.dumps(result, indent=1) + "\n")
        print(json.dumps({k: result[k] for k in ("variant", "root_head", "png_total_per_step",
                                                  "median_server_seconds")}))
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=20)
        except subprocess.TimeoutExpired:
            srv.kill()


if __name__ == "__main__":
    main()
