"""Adendo — the Free-plan design (30 000 credits/month), from the logs.

    python cost_free_plan.py <etapa0_dir>

1. Pipelines of the last 30 days by branch class (logs/cost/pipelines_since_*.json):
   permanent = develop, develop-v2.1, master; ci = /^ci\\/.*/; tag; feature = rest.
2. The recommended design: app job (2 legs: streamlit==1.56.0 and newest) only
   on permanent + ci/* branches, resource_class medium (10 credits/min);
   build_test unchanged on every push. Lower / upper bounds as in 0.7, with the
   per-leg minutes of logs/cost/cost_estimate.json.
3. Criterion (f): N = 29 per leg on CircleCI, medium -> 58 one-off jobs.
4. Stop rule for etapa 1: the per-leg duration at which the projected month
   (current CI + app) reaches 25 000 credits.

Assumption A3 (new, not measured): a medium job runs the tests at the speed the
0.7 bounds give for large (pytest runs in one process; medium has 2 vCPU
against 4). Etapa 1's first real job measures it; the stop rule covers it.
"""

import json
import re
import sys
from pathlib import Path

d = Path(sys.argv[1])
pipes = json.loads((d / "logs/cost/pipelines_since_2026-09-13.json").read_text())
cost = json.loads((d / "logs/cost/cost_estimate.json").read_text())

PERMANENT = {"develop", "develop-v2.1", "master"}
classes = {"permanent": {}, "ci": {}, "tag": {}, "feature": {}}
for p in pipes:
    vcs = p.get("vcs") or {}
    br, tag = vcs.get("branch"), vcs.get("tag")
    if tag and not br:
        cls, key = "tag", tag
    elif br in PERMANENT:
        cls, key = "permanent", br
    elif br and re.match(r"^ci/.*", br):
        cls, key = "ci", br
    else:
        cls, key = "feature", br
    classes[cls][key] = classes[cls].get(key, 0) + 1
counts = {k: sum(v.values()) for k, v in classes.items()}

CPM_MEDIUM, FREE, STOP = 10, 30000, 25000
current = cost["current_credits_30d_large"]          # build_test + publish, large
app_pushes = counts["permanent"] + counts["ci"]
legs = ("newest", "floor_st")
out = {"pipelines_total": len(pipes), "by_class": counts, "by_branch": classes,
       "app_pushes_30d(permanent+ci)": app_pushes, "current_credits_30d": current}
for tag in ("lower", "upper"):
    per_push_min = sum(cost[f"{v}_{tag}_min_per_job"] for v in legs)
    app = round(per_push_min * CPM_MEDIUM * app_pushes)
    out[f"{tag}_app_credits_per_push_medium"] = round(per_push_min * CPM_MEDIUM)
    out[f"{tag}_app_credits_30d_medium"] = app
    out[f"{tag}_total_30d"] = current + app
    # criterion (f): 29 jobs per leg, one-off
    f_cost = round(29 * per_push_min * CPM_MEDIUM)
    out[f"{tag}_f_one_off_58_jobs"] = f_cost
    out[f"{tag}_month_with_f"] = current + app + f_cost
    out[f"{tag}_month_with_f_below_free"] = current + app + f_cost < FREE
# stop rule: per-leg minutes (2 equal legs) that make current + app = 25 000
out["stop_rule_max_min_per_push"] = round((STOP - current) / (CPM_MEDIUM * app_pushes), 2)
out["stop_rule_max_min_per_leg"] = round(out["stop_rule_max_min_per_push"] / 2, 2)
print(json.dumps({k: v for k, v in out.items() if k != "by_branch"}, indent=2))
(d / "logs/cost/cost_free_plan.json").write_text(json.dumps(out, indent=2))
