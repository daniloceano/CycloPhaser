"""Passo 3: summarise the (f) matrix from ci_pipeline.py's summary.json.

    python stability_summary.py <summary.json> <out.json>

Per job: status, the pytest line, the skip-check verdict, duration. A job counts
as PASS only if it is `success`, its pytest line says 1507 passed and no
failed/error, and the skip check printed OK. Credits: medium = 10/min, both on
exact seconds and on minutes rounded up per job.
"""
import json, math, re, statistics, sys
s = json.load(open(sys.argv[1]))
rows = []
for j in s["jobs"]:
    py = [st.get("pytest_summary") for st in j.get("steps", []) if st.get("pytest_summary")]
    chk = [st["tail"][-1] for st in j.get("steps", []) if st["name"].startswith("Check ")]
    line = py[0] if py else ""
    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", line)) else None
    bad = bool(re.search(r"\d+ (failed|error)", line))
    ok = (j["status"] == "success" and passed == 1507 and not bad
          and bool(chk) and chk[0].startswith("OK"))
    rows.append({"name": j["name"], "job": j.get("job_number"), "status": j["status"],
                 "build_time_s": j.get("build_time_s"), "pytest": line,
                 "skipcheck": chk[0] if chk else None, "PASS": ok,
                 "tests_by_result": j.get("tests_by_result")})
t = [r["build_time_s"] for r in rows]
out = {"pipeline": s["pipelines"], "n_jobs": len(rows),
       "n_pass": sum(r["PASS"] for r in rows),
       "per_leg": {leg: {"n": len(v), "pass": sum(r["PASS"] for r in v),
                         "min_s": min(x["build_time_s"] for x in v),
                         "median_s": statistics.median(x["build_time_s"] for x in v),
                         "max_s": max(x["build_time_s"] for x in v)}
                   for leg in ("floor", "newest")
                   for v in [[r for r in rows if r["name"].startswith(f"app_test_{leg}_")]]},
       "credits_exact": round(sum(t) / 60 * 10),
       "credits_ceil_min": sum(math.ceil(x / 60) * 10 for x in t),
       "not_pass": [r for r in rows if not r["PASS"]], "jobs": rows}
json.dump(out, open(sys.argv[2], "w"), indent=2)
print({k: out[k] for k in ("n_jobs", "n_pass", "per_leg", "credits_exact", "credits_ceil_min")})
print("not PASS:", [(r["name"], r["status"], r["pytest"]) for r in out["not_pass"]])
