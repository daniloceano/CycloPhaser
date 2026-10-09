"""I2 observation: the cost of one Run on the Validate page.

The procedure is the one fixed in research/benchmark_review/i2/PREVISOES.md §3
(committed in b197124 before this script was written):

* AppTest, this interpreter (run it with the conda env `cyclophaser`),
  CYCLOPHASER_APP_DEV=1;
* start: Calibrate opened once, no data;
* configurations C1..C6, all "Current settings" taken from Calibrate: C1 = the
  initial state, C2..C6 = C1 with cutoff_high 48, 30, 24, 36, 42;
  2 columns = C1, C2; 6 columns = C1..C6;
* tracks: the 47 train tracks offered, all selected; batch off;
* "Side by side", label panel on, default figure page (12);
* cold = `st.cache_data.clear()` right before the click on Run; warm = a second
  click right after, nothing changed;
* time = wall clock of the `at.run()` that follows the click;
* 3 repetitions per cell; the median is the value.

    python research/benchmark_review/i2/measure_run.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "tools" / "calibration_app" / "app.py"
CUTOFFS = [None, 48, 30, 24, 36, 42]     # None = C1, the initial sidebar
REPS = 3
os.environ["CYCLOPHASER_APP_DEV"] = "1"

import streamlit as st  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

VALIDATE = "app_pages/validate.py"


def _ok(at):
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _w(at, kind, key):
    return next(w for w in getattr(at, kind) if w.key == key)


def setup(n) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=1800)
    _ok(at.run())                                     # Calibrate, opened once
    at.switch_page(VALIDATE).run()
    for i in range(n):
        if CUTOFFS[i] is not None:
            at.switch_page("app_pages/calibrate.py").run()
            _w(at, "slider", "cutoff_high").set_value(CUTOFFS[i])
            _ok(at.run())
            at.switch_page(VALIDATE).run()
        at.button(key="val_add_current").click()
        _ok(at.run())
    assert len(at.session_state["val_columns"]) == n
    assert len(at.session_state["val_tracks"]) == 47
    assert not at.session_state["val_include_batch"]
    assert at.session_state["val_figure_layout"] == "Side by side"
    assert at.session_state["val_show_label"] is True
    keys = {cc["cid"]: cc["doc"]["filter_params"]["cutoff_high"]
            for cc in at.session_state["val_columns"]}
    assert len(set(keys.values())) == n, keys       # n distinct configurations
    return at


def timed_run(at) -> float:
    at.button(key="val_run").click()
    t0 = time.perf_counter()
    at.run()
    dt = time.perf_counter() - t0
    _ok(at)
    return dt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    raw: dict[str, dict[str, list[float]]] = {}
    for n in (2, 6):
        cold, warm = [], []
        for rep in range(REPS):
            at = setup(n)
            st.cache_data.clear()
            cold.append(timed_run(at))
            warm.append(timed_run(at))
            imgs = len(at.get("image")) + len(at.get("imgs"))
            assert imgs == 12 * (n + 1), imgs
            print(f"{n} columns, rep {rep + 1}: cold {cold[-1]:.2f} s, warm "
                  f"{warm[-1]:.2f} s ({imgs} images)", flush=True)
        raw[str(n)] = {"cold": cold, "warm": warm}
    out = {
        "procedure": "research/benchmark_review/i2/PREVISOES.md §3",
        "head": subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip(),
        "tracked_changes": len(subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
            capture_output=True, text=True).stdout.splitlines()),
        "python": sys.version.split()[0], "streamlit": st.__version__,
        "machine": platform.machine(), "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                 time.gmtime()),
        "raw_seconds": raw,
        "median_seconds": {n: {k: round(statistics.median(v), 2) for k, v in d.items()}
                           for n, d in raw.items()},
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["median_seconds"], indent=1))


if __name__ == "__main__":
    main()
