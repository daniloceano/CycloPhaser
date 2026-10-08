#!/usr/bin/env bash
# Repeats the paged-grid Chromium test N times in one session under one Python
# (which decides the streamlit version), with diag_paged_grid_plugin.py
# recording each run's final state. See that plugin's docstring.
#   bash research/app_redesign/i3/run_diag_paged_grid.sh <python> <label> [reps, default 20] [latency ms, default 0] [cpu throttling rate, default 0 = off]
# Writes research/app_redesign/i3/diag/<label>.jsonl, <label>_summary.txt and
# the screenshots of failing runs.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
PY="$1"; LABEL="$2"; N="${3:-20}"; LAT="${4:-0}"; CPU="${5:-0}"; OUT="$ROOT/research/app_redesign/i3/diag"
mkdir -p "$OUT"; rm -f "$OUT/$LABEL.jsonl" "$OUT/${LABEL}"_*.png
{
  echo "python: $PY | HEAD $(git rev-parse --short HEAD) | tracked changes: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ') | $(date -u +%FT%TZ)"
  echo "added latency per HTTP request: ${LAT} ms | browser CPU throttling rate: ${CPU}"
  "$PY" -c "import streamlit, importlib.metadata as m; print('streamlit', streamlit.__version__, '| playwright', m.version('playwright'))"
  PYTHONPATH=research/app_redesign/i3 DIAG_REPEAT="$N" DIAG_OUT="$OUT" DIAG_LABEL="$LABEL" DIAG_LATENCY_MS="$LAT" DIAG_CPU_RATE="$CPU" \
    "$PY" -m pytest -q -p no:cacheprovider -W ignore -p no:logging -p diag_paged_grid_plugin \
    "tests/test_app_pages_browser.py::test_the_paged_grid_keeps_page_size_page_and_marks_in_the_browser" 2>&1 \
    | grep -E "^(FAILED|ERROR)|passed|failed" | tail -30
  python3 - "$OUT/$LABEL.jsonl" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
fails = [r for r in rows if r["outcome"] == "failed"]
print(f"runs {len(rows)} | failed {len(fails)} | runs with console errors "
      f"{sum(1 for r in rows if r['console_errors'])} | runs with a /media 404 "
      f"{sum(1 for r in rows if r.get('media_404'))}")
from collections import defaultdict
per = defaultdict(list)
for r in rows:
    for c in r.get("per_click", []):
        per[c["control"]].append(c["script_runs"])
inter = defaultdict(int)
for r in rows:
    for c in r.get("per_click", []):
        inter[c["control"]] += c.get("interrupted", 0)
for ctl, ns in per.items():
    print(f"  script executions per click — {ctl}: " + ", ".join(
        f"{n}×{ns.count(n)}" for n in sorted(set(ns)))
        + f" | interrupted for a rerun: {inter[ctl]}")
for r in fails:
    print(f"  run {r['run']}: final images {r['final_images']}, not loaded {r['final_not_loaded']}, "
          f"broken (URL not served now) {r['final_broken']} "
          f"-> {'APP' if r['final_broken'] else 'TESTE'} | {r['message']}")
    for e in r["console_errors"][:4]:
        print(f"    {e[:200]}")
PY
} > "$OUT/${LABEL}_summary.txt" 2>&1
sed -i '' "s#$HOME#~#g" "$OUT/${LABEL}_summary.txt"
cat "$OUT/${LABEL}_summary.txt"
