#!/usr/bin/env bash
# 0.6 — N consecutive runs of the 0.4 suite in ONE new venv per series.
#
#   stability.sh <variant> <N> <checkout> <wheel>
# Writes logs/stability/<variant>/run_XX.{meta,xml.gz,probe.json,log.tail}
# and a summary JSON. Runs are sequential (never two suites at once: AppTest
# runs have per-run timeouts, and concurrent load would change the measured
# condition).
source "$(dirname "$0")/common.sh"
VARIANT="$1"; N="$2"; CHECKOUT="$3"; WHL="$4"
OUT="$LOGS/stability/$VARIANT"; mkdir -p "$OUT"
VENV="$WORK/venv_stab_$VARIANT"
bash "$(dirname "$0")/make_venv.sh" "$VENV" "$WHL" "$VARIANT"
cp "$VENV.freeze.txt" "$OUT/freeze.txt"
TMP="$WORK/stab_tmp_$VARIANT"; mkdir -p "$TMP"
for i in $(seq -w 1 "$N"); do
  L="run_$i"
  bash "$(dirname "$0")/run_suite.sh" "$VENV" "$CHECKOUT" "$TMP" "$L" \
       "not browser and not source_tree"
  gzip -c "$TMP/$L.xml" > "$OUT/$L.xml.gz"
  cp "$TMP/$L.meta" "$TMP/$L.probe.json" "$OUT/" 2>/dev/null || true
  tail -40 "$TMP/$L.log" > "$OUT/$L.log.tail"
done
"$VENV/bin/python" "$(dirname "$0")/summarize_junit.py" "$OUT/summary.json" "$OUT"/run_*.xml.gz
