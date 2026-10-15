"""0.6 — Per-series and per-run table of the stability runs, and every failure
by test and by run.

    python stability_report.py <logs/stability>
Reads summary.json, run_XX.meta and run_XX.probe.json of each series.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def meta(p):
    return dict(ln.split("=", 1) for ln in p.read_text().splitlines() if "=" in ln)


root = Path(sys.argv[1])
report = {}
for series in sorted(p for p in root.iterdir() if p.is_dir()):
    runs = json.loads((series / "summary.json").read_text())
    rows, by_test = [], defaultdict(list)
    for r in runs:
        name = r["file"].split(".")[0]
        m = meta(series / f"{name}.meta")
        pr = json.loads((series / f"{name}.probe.json").read_text())
        ok = (r["failed"] == 0 and r["error"] == 0 and m["exit_code"] == "0"
              and pr["all_cyclophaser_in_venv"])
        rows.append({"run": name, "passed": r["passed"], "failed": r["failed"],
                     "error": r["error"], "skipped": r["skipped"],
                     "exit": m["exit_code"], "wall_s": float(m["wall_s"]),
                     "lock_ok": pr["all_cyclophaser_in_venv"],
                     "git_status_after": m["git_status_after"],
                     "streamlit": pr["versions"]["streamlit"], "pass": ok})
        for t in r["failures"] + r["errors"]:
            by_test[t].append(name)
    walls = [x["wall_s"] for x in rows]
    report[series.name] = {
        "n_runs": len(rows), "runs_pass": sum(x["pass"] for x in rows),
        "passed_values": sorted({x["passed"] for x in rows}),
        "failed_total": sum(x["failed"] + x["error"] for x in rows),
        "skipped_values": sorted({x["skipped"] for x in rows}),
        "wall_s_min": min(walls), "wall_s_median": sorted(walls)[len(walls) // 2],
        "wall_s_max": max(walls), "failures_by_test": dict(by_test),
        "streamlit": sorted({x["streamlit"] for x in rows}), "runs": rows,
    }
(root / "stability_report.json").write_text(json.dumps(report, indent=2))
for k, v in report.items():
    print(k, {kk: vv for kk, vv in v.items() if kk != "runs"})
