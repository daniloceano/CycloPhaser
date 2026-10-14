"""Read one commit's CircleCI pipeline(s) from the public API (no token).

    python ci_pipeline.py <branch> <commit-sha> <out_dir> [--wait]

For every pipeline of <branch> whose revision is <commit-sha>: its workflows,
every job (name, status, number), and for each finished job the v1.1 build
(resource class, duration, steps with run times, the pytest summary line and
the last lines of the skip-check step) plus the /tests endpoint, counted by
result, with the ids of every failure/error/skip. Raw JSON is saved next to
`summary.json`. With --wait, polls every 60 s until no job is still running.

Read-only GETs against circleci.com.
"""

import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SLUG_V1 = "github/daniloceano/CycloPhaser"
SLUG_V2 = "gh/daniloceano/CycloPhaser"
OPEN = {"running", "not_running", "queued", "on_hold", "blocked", "not_run_yet"}


def get(url):
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                       "User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return json.loads(raw)
        except Exception:             # transient API hiccup: retry, then raise
            if attempt == 4:
                raise
            time.sleep(5)


def _step_lines(step):
    lines = []
    for a in step["actions"]:
        if a.get("output_url"):
            for msg in get(a["output_url"]):
                lines += (msg.get("message") or "").splitlines()
    return lines


def _pytest_line(lines):
    hits = [ln for ln in lines if "==" in ln and " in " in ln
            and any(w in ln for w in ("passed", "failed", "skipped", "error", "no tests"))]
    return hits[-1].strip() if hits else None


def pipelines_for(branch, sha):
    b = urllib.parse.quote(branch, safe="")
    page = get(f"https://circleci.com/api/v2/project/{SLUG_V2}/pipeline?branch={b}")
    return [p for p in page["items"] if (p.get("vcs") or {}).get("revision") == sha]


def snapshot(branch, sha, out):
    pls = pipelines_for(branch, sha)
    (out / "pipelines.json").write_text(json.dumps(pls, indent=2))
    jobs_all = []
    for p in pls:
        wfs = get(f"https://circleci.com/api/v2/pipeline/{p['id']}/workflow")["items"]
        (out / f"pipeline_{p['number']}_workflows.json").write_text(json.dumps(wfs, indent=2))
        for w in wfs:
            jobs, token = [], None
            while True:
                url = f"https://circleci.com/api/v2/workflow/{w['id']}/job"
                if token:
                    url += "?page-token=" + urllib.parse.quote(token)
                page = get(url)
                jobs += page["items"]
                token = page.get("next_page_token")
                if not token:
                    break
            (out / f"workflow_{w['id'][:8]}_jobs.json").write_text(json.dumps(jobs, indent=2))
            for j in jobs:
                jobs_all.append({"pipeline": p["number"], "workflow": w["name"],
                                 "workflow_id": w["id"], "workflow_status": w["status"],
                                 **{k: j.get(k) for k in ("name", "status", "job_number",
                                                          "started_at", "stopped_at")}})
    return pls, jobs_all


def detail(job, out):
    num = job["job_number"]
    full = get(f"https://circleci.com/api/v1.1/project/{SLUG_V1}/{num}")
    tests = get(f"https://circleci.com/api/v1.1/project/{SLUG_V1}/{num}/tests")
    (out / f"build_{num}.json").write_text(json.dumps(full, indent=2))
    (out / f"build_{num}_tests.json").write_text(json.dumps(tests, indent=2))
    steps = []
    for s in full.get("steps", []):
        row = {"name": s["name"],
               "run_time_s": round(sum((a.get("run_time_millis") or 0)
                                       for a in s["actions"]) / 1000, 1),
               "status": [a.get("status") for a in s["actions"]]}
        if s["name"].startswith(("Run ", "Check ", "Require ")):
            lines = _step_lines(s)
            row["pytest_summary"] = _pytest_line(lines)
            row["tail"] = lines[-12:]
        steps.append(row)
    by_result, ids = {}, {}
    for t in tests.get("tests", []):
        r = t.get("result")
        by_result[r] = by_result.get(r, 0) + 1
        if r not in ("success",):
            ids.setdefault(r, []).append(
                f"{t.get('classname') or ''}::{t.get('name')}".lstrip(":"))
    return {**job, "build_url": full.get("build_url"),
            "resource_class": (full.get("picard") or {}).get("resource_class"),
            "build_time_s": round((full.get("build_time_millis") or 0) / 1000, 1),
            "outcome": full.get("outcome"), "steps": steps,
            "tests_by_result": by_result, "tests_non_success_ids": ids,
            "n_tests_reported": len(tests.get("tests", []))}


def main():
    branch, sha, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    wait = "--wait" in sys.argv
    out.mkdir(parents=True, exist_ok=True)
    while True:
        pls, jobs = snapshot(branch, sha, out)
        if not wait or (pls and jobs and not any(j["status"] in OPEN for j in jobs)):
            break
        print(time.strftime("%H:%M:%S"), {j["name"]: j["status"] for j in jobs}, flush=True)
        time.sleep(60)
    rows = [detail(j, out) if j.get("job_number") and j["status"] not in OPEN else j
            for j in jobs]
    summary = {"branch": branch, "commit": sha,
               "pipelines": [{"number": p["number"], "id": p["id"],
                              "url": f"https://app.circleci.com/pipelines/{SLUG_V2}/{p['number']}"}
                             for p in pls],
               "jobs": rows}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    for r in rows:
        tests = r.get("tests_by_result")
        pyl = [s.get("pytest_summary") for s in r.get("steps", []) if s.get("pytest_summary")]
        print(r["name"], r.get("job_number"), r["status"], r.get("resource_class"),
              r.get("build_time_s"), tests, pyl)


if __name__ == "__main__":
    main()
