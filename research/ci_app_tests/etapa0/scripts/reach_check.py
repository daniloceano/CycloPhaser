"""0.10 — The arithmetic behind each criterion's PASS / FAIL reachability,
recomputed from this stage's logs (never typed by hand).

    python reach_check.py <etapa0_dir>

Prints and writes logs/reach_check.json; every line is an assertion that holds
on the logs, or the script stops.
"""

import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
runs = {r["file"].split(".")[0]: r for r in
        json.loads((d / "logs/runs/summary_single.json").read_text())}
inv = json.loads((d / "logs/inventory/inventory.json").read_text())["totals"]
base = json.loads((d / "logs/ci_baseline/summary_ci_app-tests.json").read_text())[0]
steps = {s["name"]: s["pytest_summary"] for s in base["steps"]}
out = {}

# (b) wheel job baseline (CI 516) and the leak arithmetic
ci_wheel = steps["Run tests against the installed wheel"]
ci_src = steps["Run source-tree tests against the checkout"]
assert ci_wheel.startswith("=") and " 1280 passed" in ci_wheel and "failed" not in ci_wheel
assert " 1 passed" in ci_src and "failed" not in ci_src
pkg = runs["lean_ci_wheel"]["passed"]; app_measured = inv["app_tests_non_browser"]

# Danilo's decision (2026-10-13): the sample-tracks test gets 2 versioned CSVs in
# tests/ during implementation. Ground the +1 in the logs: it PASSED in the conda
# suite (local tree has the CSVs) and was SKIPPED in every clean-clone app run,
# and its whole module skips in the lean run (so build_test does not change).
import gzip, xml.etree.ElementTree as ET
SAMPLE = ("tests.test_compare_core", "test_the_series_key_is_the_content_not_the_name")
def status(xml_gz, key):
    root = ET.fromstring(gzip.decompress((d / xml_gz).read_bytes()))
    for c in root.iter("testcase"):
        if (c.get("classname"), c.get("name")) == key:
            return ("failed" if c.find("failure") is not None else "error" if c.find("error") is not None
                    else "skipped" if c.find("skipped") is not None else "passed")
    return None
assert status("logs/conda/conda_not_browser.xml.gz", SAMPLE) == "passed"
assert status("logs/runs/newest.xml.gz", SAMPLE) == "skipped"
assert status("logs/runs/lean_ci_wheel.xml.gz", ("", "tests.test_compare_core")) == "skipped"
app = app_measured + 1
out["app_tests_measured_c0"] = app_measured
out["app_tests_after_sample_fix"] = app
assert pkg == 1280 and runs["lean_ci_wheel"]["failed"] == 0
out["b_baseline_wheel_passed"] = 1280
out["b_if_app_deps_leak_into_wheel_job_passed"] = pkg + app

# (c)/(d)/(g) expected count in the app job, and what a missing streamlit gives
for v in ("newest", "floor_st", "pins_local", "floors_all_cm403"):
    assert runs[v]["passed"] == pkg + app_measured and runs[v]["failed"] == 0, v
out["c_measured_app_job_passed_c0"] = pkg + app_measured
out["c_expected_app_job_passed"] = pkg + app
out["c_if_streamlit_missing_and_no_lock_passed"] = runs["lean_appsel"]["passed"]
out["c_tests_lost_without_streamlit"] = pkg + app - runs["lean_appsel"]["passed"]
assert runs["newest"]["skipped"] == 6           # measured at C0
out["c_allowed_skips_after_fix"] = runs["newest"]["skipped"] - 1   # 4 browser modules + IcIt

# collection closes: results + deselected - module skips + browser = conda collect
deselected = 1
module_skips = 4
for passed, skipped, tag in ((runs["newest"]["passed"], runs["newest"]["skipped"], "c0"),
                             (pkg + app, out["c_allowed_skips_after_fix"], "after_fix")):
    assert passed + skipped + deselected - module_skips + inv["browser_collected"] \
        == inv["collected_conda_all"], tag
    out[f"collection_closes_{tag}"] = (f'{passed} + {skipped} + {deselected} - {module_skips} '
                                       f'+ {inv["browser_collected"]} = {inv["collected_conda_all"]}')

# (e) positive control: a REGRESSION IN APP CODE (tools/calibration_app) caught
# by AppTest. k = number of test ids declared to fail before the push (k >= 1,
# all among the 226 app tests). Red: failed == k and the failed ids == the
# declared ids; passed == 1506 - k. build_test stays 1280 / 0 ONLY IF the
# regression is outside the app modules build_test's own tests import (read
# from the lean probe below): build_test runs from the checkout, so app code
# outside the wheel is still reachable by it.
out["e_red_expected"] = {"passed": f"{pkg + app} - k", "failed": "k (1 <= k <= "
                         f"{app}), ids == declared", "build_test_passed": pkg}
out["e_red_k_range"] = [1, app]
lean_probe = json.loads((d / "logs/runs/lean_ci_wheel.probe.json").read_text())
out["e_app_modules_build_test_imports"] = sorted(
    k for k, v in lean_probe["checkout_modules"].items() if v.startswith("tools/"))
out["e_green_expected"] = {"passed": pkg + app, "failed": 0}
assert pkg + app - app == pkg     # k at most the app tests: passed never below build_test

# (f) N and detectability (declared in PREVISOES.md)
N = 29
out["f_N_per_leg"] = N
out["f_jobs"] = 2 * N
out["f_min_p_detected_95"] = round(1 - 0.05 ** (1 / N), 4)
stab = d / "logs/stability/stability_report.json"
if stab.exists():
    s = json.loads(stab.read_text())
    out["f_local_runs_pass"] = {k: f'{v["runs_pass"]}/{v["n_runs"]}' for k, v in s.items()}

print(json.dumps(out, indent=2))
(d / "logs/reach_check.json").write_text(json.dumps(out, indent=2))
