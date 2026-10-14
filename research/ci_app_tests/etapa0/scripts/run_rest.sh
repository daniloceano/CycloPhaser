#!/usr/bin/env bash
# Resume of run_all.sh after it stopped at floors_all_pd222 (INTERNALERROR,
# no junit, and keep() then aborted under set -e). Runs what was left, in the
# same order and the same way, plus the undeclared floors_all_cm403 variant.
#   run_rest.sh <checkout> <wheel>
source "$(dirname "$0")/common.sh"
CHECKOUT="$1"; WHL="$2"; S="$(dirname "$0")"
OUT="$LOGS/runs"; TMP="$WORK/runs"; mkdir -p "$OUT" "$TMP"
keep() {
  [ -f "$TMP/$1.xml" ] && gzip -c "$TMP/$1.xml" > "$OUT/$1.xml.gz"
  gzip -c "$TMP/$1.log" > "$OUT/$1.log.gz"
  cp "$TMP/$1.meta" "$OUT/"; cp "$TMP/$1.probe.json" "$OUT/" 2>/dev/null || true
}
bash "$S/make_venv.sh" "$WORK/venv_floors_all_cm403" "$WHL" floors_all_cm403
cp "$WORK/venv_floors_all_cm403.freeze.txt" "$LOGS/versions/freeze_floors_all_cm403.txt"
for v in pins_local floors_all_cm403; do
  bash "$S/run_suite.sh" "$WORK/venv_$v" "$CHECKOUT" "$TMP" "$v" \
       "not browser and not source_tree" --durations=0
  keep "$v"
done
echo "SINGLE RUNS DONE $(date -u +%FT%TZ)" > "$OUT/_single_done"
for v in floor_st newest; do
  bash "$S/stability.sh" "$v" 29 "$CHECKOUT" "$WHL"
done
echo "ALL DONE $(date -u +%FT%TZ)" > "$OUT/_all_done"
