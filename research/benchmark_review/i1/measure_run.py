"""I1 observation: the cost of one Run, Compare vs the current Benchmark.

The procedure is the one fixed in PREVISOES.md (committed before this script was
written):

* AppTest, this interpreter (run it with the conda env `cyclophaser`);
* start: Calibrate with "Sample data" (51 tracks);
* configurations C1..C4, all taken from the Calibrate sidebar: C1 = the initial
  state (package defaults), C2/C3/C4 = C1 with High cutoff 48 / 30 / 24;
  1 column = C1, 2 = C1, C2, 4 = C1..C4. Compare: "Add Current settings";
  Benchmark: "Add column from current sidebar state";
* tracks: Compare, the 51 from Calibrate, all selected; Benchmark, Exploration
  mode, "All real" (the same 51 files);
* layout "Side by side" (both pages' default), Compare's default figure page;
* cold = `st.cache_data.clear()` right before the click on Run; warm = a second
  click right after, nothing changed;
* time = wall clock of the `at.run()` that follows the click;
* 3 repetitions per cell; the median is the value.

    python research/benchmark_review/i1/measure_run.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "tools" / "calibration_app" / "app.py"
CUTOFFS = [None, 48, 30, 24]            # None = C1, the initial sidebar
REPS = 3

import streamlit as st  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402


def _ok(at):
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _w(at, kind, key):
    return next(w for w in getattr(at, kind) if w.key == key)


def _start() -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=1800)
    at.run()
    at.button(key="btn_sample").click()
    at.run()
    return _ok(at)


def _add_columns(at, n, page, add_key):
    for i in range(n):
        if CUTOFFS[i] is not None:
            at.switch_page("app_pages/calibrate.py").run()
            _w(at, "slider", "cutoff_high").set_value(CUTOFFS[i])
            _ok(at.run())
            at.switch_page(page).run()
        at.button(key=add_key).click()
        _ok(at.run())


def setup_compare(n) -> AppTest:
    at = _start()
    at.switch_page("app_pages/compare.py").run()
    _add_columns(at, n, "app_pages/compare.py", "cmp_add_current")
    assert len(at.session_state["cmp_columns"]) == n
    assert len(at.session_state["cmp_tracks"]) == 51
    return at


def setup_benchmark(n) -> AppTest:
    at = _start()
    at.switch_page("app_pages/benchmark.py").run()
    _w(at, "radio", "bench_mode").set_value("Exploration")
    _ok(at.run())
    at.button(key="bench_pick_real").click()
    _ok(at.run())
    _add_columns(at, n, "app_pages/benchmark.py", "bench_add_sidebar")
    assert len(at.session_state["bench_columns"]) == n
    assert len(at.session_state["bench_selected_ids"]) == 51
    return at


def timed_run(at, run_key) -> float:
    at.button(key=run_key).click()
    t0 = time.perf_counter()
    at.run()
    dt = time.perf_counter() - t0
    _ok(at)
    return dt


def measure(page, n) -> dict:
    at = setup_compare(n) if page == "compare" else setup_benchmark(n)
    run_key = "cmp_run" if page == "compare" else "bench_run"
    cold, warm = [], []
    for _ in range(REPS):
        st.cache_data.clear()
        cold.append(timed_run(at, run_key))
        warm.append(timed_run(at, run_key))
    if page == "compare":
        res = at.session_state["_cmp_results"]
        assert len(res["columns"]) == n and len(res["ids"]) == 51
    else:
        assert len(at.session_state["_bench_runs"]) == n
        assert len(at.session_state["_bench_run_ids"]) == 51
    return {"cold_s": cold, "warm_s": warm,
            "cold_median_s": statistics.median(cold),
            "warm_median_s": statistics.median(warm)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    import cyclophaser
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           cwd=ROOT, capture_output=True, text=True).stdout
    out = {"python": sys.executable, "python_version": platform.python_version(),
           "machine": platform.machine(), "streamlit": st.__version__,
           "cyclophaser_file": cyclophaser.__file__, "head": head,
           "tracked_files_changed": len(dirty.splitlines()),
           "procedure": "research/benchmark_review/i1/PREVISOES.md section 2",
           "cells": {}}
    for page in ("compare", "benchmark"):
        for n in (1, 2, 4):
            r = measure(page, n)
            out["cells"][f"{page}_{n}"] = r
            print(page, n, f"cold {r['cold_median_s']:.2f} s", f"warm {r['warm_median_s']:.2f} s",
                  flush=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
