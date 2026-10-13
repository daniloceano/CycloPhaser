"""0.2 / 0.7 — Read CircleCI's public API (no token) and save the raw answers.

    python ci_baseline.py builds <branch> <out_dir>
        every build of <branch>: number, job, status, commit, duration, and for
        each the step list with run times, plus the per-test results.
    python ci_baseline.py pipelines <since YYYY-MM-DD> <out_dir>
        every pipeline created since the date (all branches) -> push frequency.

Read-only GETs against circleci.com. Raw JSON is saved next to the summary.
"""

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SLUG_V1 = "github/daniloceano/CycloPhaser"
SLUG_V2 = "gh/daniloceano/CycloPhaser"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def _pytest_summary(step):
    """The pytest '=== N passed, ... in Xs ===' line of a test step's log."""
    if not step["name"].startswith("Run "):
        return None
    lines = []
    for a in step["actions"]:
        if a.get("output_url"):
            for msg in get(a["output_url"]):
                lines += (msg.get("message") or "").splitlines()
    hits = [ln for ln in lines if " in " in ln and ("passed" in ln or "failed" in ln
                                                   or "skipped" in ln) and "==" in ln]
    return hits[-1].strip() if hits else None


def builds(branch, out):
    b = urllib.parse.quote(branch, safe="")
    lst = get(f"https://circleci.com/api/v1.1/project/{SLUG_V1}/tree/{b}?limit=30")
    (out / f"builds_{branch.replace('/', '_')}.json").write_text(json.dumps(lst, indent=2))
    summary = []
    for item in lst:
        num = item["build_num"]
        full = get(f"https://circleci.com/api/v1.1/project/{SLUG_V1}/{num}")
        tests = get(f"https://circleci.com/api/v1.1/project/{SLUG_V1}/{num}/tests")
        (out / f"build_{num}.json").write_text(json.dumps(full, indent=2))
        (out / f"build_{num}_tests.json").write_text(json.dumps(tests, indent=2))
        steps = [{"name": s["name"],
                  "run_time_s": round(sum((a.get("run_time_millis") or 0)
                                          for a in s["actions"]) / 1000, 1),
                  "status": [a.get("status") for a in s["actions"]],
                  "pytest_summary": _pytest_summary(s)}
                 for s in full.get("steps", [])]
        by_file = {}   # junit file the result came from -> result -> count
        for t in tests.get("tests", []):
            key = t.get("source") or t.get("source_type") or "?"
            by_file.setdefault(key, {}).setdefault(t.get("result"), 0)
            by_file[key][t.get("result")] += 1
        summary.append({
            "build_num": num, "job": full.get("workflows", {}).get("job_name"),
            "workflow_id": full.get("workflows", {}).get("workflow_id"),
            "pipeline_url": full.get("build_url"),
            "status": full.get("status"), "commit": full.get("vcs_revision"),
            "start": full.get("start_time"), "stop": full.get("stop_time"),
            "build_time_s": round((full.get("build_time_millis") or 0) / 1000, 1),
            "steps": steps, "test_results_by_source": by_file,
            "n_tests_reported": len(tests.get("tests", [])),
        })
    (out / f"summary_{branch.replace('/', '_')}.json").write_text(json.dumps(summary, indent=2))
    for s in summary:
        print(s["build_num"], s["job"], s["status"], s["commit"][:7],
              s["build_time_s"], s["test_results_by_source"])


def pipelines(since, out):
    items, token = [], None
    while True:
        url = f"https://circleci.com/api/v2/project/{SLUG_V2}/pipeline"
        if token:
            url += "?page-token=" + urllib.parse.quote(token)
        page = get(url)
        items += page["items"]
        token = page.get("next_page_token")
        if not token or page["items"][-1]["created_at"][:10] < since:
            break
    items = [p for p in items if p["created_at"][:10] >= since]
    (out / f"pipelines_since_{since}.json").write_text(json.dumps(items, indent=2))
    by_branch = {}
    for p in items:
        br = (p.get("vcs") or {}).get("branch") or ("tag:" + str((p.get("vcs") or {}).get("tag")))
        by_branch[br] = by_branch.get(br, 0) + 1
    print(len(items), "pipelines since", since, by_branch)


if __name__ == "__main__":
    mode, arg, out = sys.argv[1:4]
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    {"builds": builds, "pipelines": pipelines}[mode](arg, out)
