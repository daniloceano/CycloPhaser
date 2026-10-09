#!/usr/bin/env bash
# I2 criterion (e1): the NEW browser test file, N times in a row, under one Python.
#   bash research/benchmark_review/i2/run_repeat_browser.sh <python> <label> [N=10]
# One line per run: its pytest count line and the e1 interaction counts.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
PY="$1"; N="${3:-10}"; OUT="$ROOT/research/benchmark_review/i2/browser_repeat_$2.txt"
{
  echo "python: $PY ($("$PY" --version 2>&1)) | streamlit $("$PY" -c 'import streamlit; print(streamlit.__version__)') | HEAD $(git rev-parse --short HEAD) | tracked changes: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ') | $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for i in $(seq 1 "$N"); do
    res="$("$PY" -m pytest -q -p no:cacheprovider -W ignore -p no:logging -rfE -s tests/test_validate_browser.py 2>&1)"
    echo "run $i: $(echo "$res" | grep -E 'passed|failed' | tail -1) | $(echo "$res" | grep 'e1 interactions' | tr '\n' ' ')"
    echo "$res" | grep -E "^(FAILED|ERROR)|^E  " | head -10
  done
} > "$OUT" 2>&1
sed -i '' "s#$HOME#~#g" "$OUT"
cat "$OUT"
