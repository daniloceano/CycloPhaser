"""0.7 — Credits per push and per month for the proposed app job, from the
measurements of this stage. Every input is read from a log; the two
assumptions are named and printed.

    python cost_estimate.py <etapa0_dir>

Inputs
* CI build 516 (baseline, resource class "large"): time of each step.
* local walls: lean_ci_wheel (the package tests) and newest / floor_st (the
  app selection), from logs/runs/*.meta.
* build_test jobs in the last 30 days (logs/cost/jobs_summary_*.json) = pushes.
* price list (logs/cost/pricing_2026-10-13.md): large 20, medium 10 credits/min.

Assumptions (stated, not measured here)
A1 the app job's fixed part (spin-up, checkout, build, installs) costs the same
   as build_test's fixed part PLUS one more install step of the size of
   "Install package from wheel" for streamlit/plotly.
A2 CI/local speed ratio for the test step: bracketed between 1.0 (lower) and
   the ratio measured on the package tests, CI 516 vs local lean (upper).
"""

import json
import sys
from pathlib import Path


def meta(p):
    return dict(ln.split("=", 1) for ln in Path(p).read_text().splitlines() if "=" in ln)


d = Path(sys.argv[1])
b = json.loads((d / "logs/ci_baseline/summary_ci_app-tests.json").read_text())[0]
steps = {s["name"]: s["run_time_s"] for s in b["steps"]}
test_steps = ["Run tests against the installed wheel",
              "Run source-tree tests against the checkout"]
fixed = sum(v for k, v in steps.items() if k not in test_steps)
ci_pkg = steps["Run tests against the installed wheel"]
local_pkg = float(meta(d / "logs/runs/lean_ci_wheel.meta")["wall_s"])
ratio_hi = ci_pkg / local_pkg
local_app = {v: float(meta(d / f"logs/runs/{v}.meta")["wall_s"])
             for v in ("newest", "floor_st")}
jobs = json.loads((d / "logs/cost/jobs_summary_since_2026-09-13.json").read_text())
pushes = jobs["build_test"]["n"]
current_min = sum(v["total_min"] for k, v in jobs.items() if not k.startswith("_"))

fixed_app = fixed + steps["Install package from wheel"]            # A1
out = {"fixed_build_test_s": round(fixed, 1), "fixed_app_job_s(A1)": round(fixed_app, 1),
       "ci_pkg_test_s": ci_pkg, "local_pkg_test_s": local_pkg,
       "ratio_ci_over_local(A2 upper)": round(ratio_hi, 2),
       "pushes_30d(build_test jobs)": pushes,
       "current_ci_minutes_30d": round(current_min, 1),
       "current_credits_30d_large": round(current_min * 20)}
for v, loc in local_app.items():
    for tag, r in (("lower", 1.0), ("upper", ratio_hi)):
        per_job_min = (fixed_app + loc * r) / 60
        out[f"{v}_{tag}_min_per_job"] = round(per_job_min, 2)
legs = 2   # floor + newest
for tag in ("lower", "upper"):
    per_push_min = sum(out[f"{v}_{tag}_min_per_job"] for v in local_app)
    out[f"{tag}_min_per_push_{legs}legs"] = round(per_push_min, 2)
    for rc, cpm in (("large", 20), ("medium", 10)):
        out[f"{tag}_credits_per_push_{rc}"] = round(per_push_min * cpm)
        out[f"{tag}_credits_30d_{rc}"] = round(per_push_min * cpm * pushes)
        out[f"{tag}_credits_30d_large_plus_current"] = (
            out[f"{tag}_credits_30d_large"] + out["current_credits_30d_large"])
# the package tests the app job would repeat (selection "whole suite"), per leg
out["repeat_pkg_tests_credits_30d_large_2legs"] = round(ci_pkg / 60 * 20 * pushes * legs)
print(json.dumps(out, indent=2))
(d / "logs/cost/cost_estimate.json").write_text(json.dumps(out, indent=2))
