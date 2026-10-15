"""0.7 — every CircleCI job (all branches) since a date: count, duration, and
the resource class / executor the API reports. Read-only, no token.

    python ci_jobs_window.py <since YYYY-MM-DD> <out_dir>
"""
import json, sys, statistics, urllib.request
from pathlib import Path

def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

since, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
rows, offset = [], 0
while True:
    page = get(f"https://circleci.com/api/v1.1/project/github/daniloceano/CycloPhaser?limit=100&offset={offset}&shallow=true")
    if not page: break
    rows += page; offset += 100
    if (page[-1].get("queued_at") or page[-1].get("start_time") or "9")[:10] < since: break
rows = [r for r in rows if (r.get("start_time") or r.get("queued_at") or "")[:10] >= since]
(out / f"jobs_since_{since}.json").write_text(json.dumps(rows, indent=2))
by_job = {}
for r in rows:
    j = (r.get("workflows") or {}).get("job_name")
    by_job.setdefault(j, []).append((r.get("build_time_millis") or 0) / 1000)
summary = {j: {"n": len(v), "total_min": round(sum(v) / 60, 1),
               "mean_s": round(statistics.mean(v), 1), "median_s": round(statistics.median(v), 1),
               "max_s": round(max(v), 1)} for j, v in by_job.items()}
# the shallow listing carries no resource class; it is read from one full
# build (build_516.json, "picard") in the report instead.
summary["_statuses"] = {s: sum(1 for r in rows if r.get("status") == s) for s in {r.get("status") for r in rows}}
(out / f"jobs_summary_since_{since}.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
