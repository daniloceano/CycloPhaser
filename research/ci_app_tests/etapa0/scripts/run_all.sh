#!/usr/bin/env bash
# Every local measurement of etapa 0, strictly one suite at a time.
#   run_all.sh <checkout> <wheel>
# Venvs for the single runs (0.3, 0.4, 0.5) must already exist (make_venv.sh);
# the stability series (0.6) create their own new venvs.
source "$(dirname "$0")/common.sh"
CHECKOUT="$1"; WHL="$2"; S="$(dirname "$0")"
OUT="$LOGS/runs"; TMP="$WORK/runs"; mkdir -p "$OUT" "$TMP"

keep() {  # keep the raw evidence of one run inside the repo, compressed
  # (a run that dies in INTERNALERROR writes no junit: keep the rest anyway)
  [ -f "$TMP/$1.xml" ] && gzip -c "$TMP/$1.xml" > "$OUT/$1.xml.gz"
  gzip -c "$TMP/$1.log" > "$OUT/$1.log.gz"
  cp "$TMP/$1.meta" "$OUT/"; cp "$TMP/$1.probe.json" "$OUT/" 2>/dev/null || true
}

# 0.3 — the CI recipe, locally: lean venv, step 1 with the lock ...
bash "$S/run_suite.sh" "$WORK/venv_lean" "$CHECKOUT" "$TMP" lean_ci_wheel "not source_tree"
keep lean_ci_wheel
# ... and step 2 exactly as CI: `python -m pytest -m source_tree`, no lock.
( cd "$CHECKOUT"; unset PYTHONPATH
  "$WORK/venv_lean/bin/python" -m pytest -m source_tree -p no:cacheprovider \
      --junitxml="$TMP/lean_ci_source.xml" > "$TMP/lean_ci_source.log" 2>&1
  echo "exit_code=$?" > "$TMP/lean_ci_source.meta" )
gzip -c "$TMP/lean_ci_source.xml" > "$OUT/lean_ci_source.xml.gz"
cp "$TMP/lean_ci_source.log" "$TMP/lean_ci_source.meta" "$OUT/"

# 0.3 — the 0.4 suite in the lean venv as well (same selection as the app job)
bash "$S/run_suite.sh" "$WORK/venv_lean" "$CHECKOUT" "$TMP" lean_appsel
keep lean_appsel

# 0.4 / 0.5 (ii) — newest, with durations
bash "$S/run_suite.sh" "$WORK/venv_newest" "$CHECKOUT" "$TMP" newest \
     "not browser and not source_tree" --durations=0
keep newest
# 0.5 (i), (i'b), (iii)
for v in floor_st floors_all_pd222 pins_local; do
  bash "$S/run_suite.sh" "$WORK/venv_$v" "$CHECKOUT" "$TMP" "$v" \
       "not browser and not source_tree" --durations=0
  keep "$v"
done
echo "SINGLE RUNS DONE $(date -u +%FT%TZ)" > "$OUT/_single_done"

# 0.6 — stability, N = 29 per version (declared in PREVISOES.md)
for v in floor_st newest; do
  bash "$S/stability.sh" "$v" 29 "$CHECKOUT" "$WHL"
done
echo "ALL DONE $(date -u +%FT%TZ)" > "$OUT/_all_done"
