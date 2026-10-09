#!/usr/bin/env bash
# I3 gate (c): the browser tests that are NEW or CHANGED in I3 — the five changed
# and the one new test of tests/test_app_pages_browser.py — N times in a row,
# under one Python. tests/test_label_browser.py is NOT run.
#   bash research/benchmark_review/i3/run_repeat_browser.sh <python> <label> [N=10]
# One line per run: its pytest count line.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
PY="$1"; N="${3:-10}"; OUT="$ROOT/research/benchmark_review/i3/browser_repeat_$2.txt"
F=tests/test_app_pages_browser.py
TESTS=("$F::test_the_public_menu_has_calibrate_and_compare_and_no_developer"
       "$F::test_the_developer_menu_has_the_labelling_and_validate_pages"
       "$F::test_the_old_benchmark_address_opens_the_default_page"
       "$F::test_an_uploaded_track_and_an_imported_yaml_survive_a_page_trip"
       "$F::test_sidebar_values_set_in_the_ui_are_shown_after_page_trips"
       "$F::test_the_paged_grid_keeps_page_size_page_and_marks_in_the_browser")
{
  echo "python: $PY ($("$PY" --version 2>&1)) | streamlit $("$PY" -c 'import streamlit; print(streamlit.__version__)') | HEAD $(git rev-parse --short HEAD) | tracked changes: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ') | $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for i in $(seq 1 "$N"); do
    res="$("$PY" -m pytest -q -p no:cacheprovider -W ignore -p no:logging -rfE "${TESTS[@]}" 2>&1)"
    echo "run $i: $(echo "$res" | grep -E 'passed|failed' | tail -1)"
    echo "$res" | grep -E "^(FAILED|ERROR)|^E  " | head -10
  done
  echo "manual_labels.yaml git status lines: $(git status --porcelain research/labels/manual_labels.yaml | wc -l | tr -d ' ')"
} > "$OUT" 2>&1
sed -i '' "s#$HOME#~#g" "$OUT"
cat "$OUT"
