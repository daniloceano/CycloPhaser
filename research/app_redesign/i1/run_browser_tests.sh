#!/usr/bin/env bash
# I1 second correction: the 34 Chromium tests (tests/test_label_browser.py +
# tests/test_app_pages_browser.py) under one Python, which decides the streamlit
# version (the harness starts `streamlit run` with that same interpreter).
#   bash research/app_redesign/i1/run_browser_tests.sh <python> <label> [out dir, default research/app_redesign/i1]
# Writes research/app_redesign/i1/browser_tests_<label>.txt.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
PY="$1"; OUT="$ROOT/${3:-research/app_redesign/i1}/browser_tests_$2.txt"
{
  echo "python: $PY ($("$PY" --version 2>&1)) | HEAD $(git rev-parse --short HEAD) | tracked changes: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ') | $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "$PY" -c "import streamlit, playwright, importlib.metadata as m; print('streamlit', streamlit.__version__, '| playwright', m.version('playwright'))"
  "$PY" -m pytest -q -p no:cacheprovider -W ignore -p no:logging -rfE \
      tests/test_label_browser.py tests/test_app_pages_browser.py 2>&1 \
    | grep -E "^(FAILED|ERROR)|^E  |passed|failed" | tail -80
  echo "manual_labels.yaml git status lines: $(git status --porcelain research/labels/manual_labels.yaml | wc -l | tr -d ' ')"
} > "$OUT" 2>&1
sed -i '' "s#$HOME#~#g" "$OUT"
cat "$OUT"
