#!/usr/bin/env bash
# I2 gate (c): the Chromium tests of the app pages, Compare and Validate, under one
# Python (the harness starts `streamlit run` with that same interpreter).
# tests/test_label_browser.py is NOT run (CLAUDE.md: run by hand only).
#   bash research/benchmark_review/i2/run_browser.sh <python> <label>
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
PY="$1"; OUT="$ROOT/research/benchmark_review/i2/browser_$2.txt"
{
  echo "python: $PY ($("$PY" --version 2>&1)) | HEAD $(git rev-parse --short HEAD) | tracked changes: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ') | $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "$PY" -c "import streamlit, importlib.metadata as m; print('streamlit', streamlit.__version__, '| playwright', m.version('playwright'))"
  "$PY" -m pytest -q -p no:cacheprovider -W ignore -p no:logging -rfE -s \
      tests/test_app_pages_browser.py tests/test_compare_browser.py tests/test_validate_browser.py 2>&1 \
    | grep -E "^(FAILED|ERROR)|^E  |passed|failed|e1 interactions" | tail -80
  echo "manual_labels.yaml git status lines: $(git status --porcelain research/labels/manual_labels.yaml | wc -l | tr -d ' ')"
} > "$OUT" 2>&1
sed -i '' "s#$HOME#~#g" "$OUT"
cat "$OUT"
