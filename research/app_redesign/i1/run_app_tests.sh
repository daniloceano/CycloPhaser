#!/usr/bin/env bash
# I1 correction: the app tests — tests/test_*apptest*.py and tests/test_sidebar_defaults.py,
# as asked, plus the other three files that drive the app through AppTest
# (test_app_passo5_fixes.py, test_app_distance_removed.py, test_sidebar_coverage.py)
# under one Python, which decides the streamlit version.
#   bash research/app_redesign/i1/run_app_tests.sh <python> <label>
# Writes research/app_redesign/i1/app_tests_<label>.txt: interpreter, streamlit and
# cyclophaser versions/paths, then pytest's failures and final count line.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
PY="$1"; OUT="$ROOT/research/app_redesign/i1/app_tests_$2.txt"
{
  echo "python: $PY ($("$PY" --version 2>&1)) | HEAD $(git rev-parse --short HEAD) | tracked changes: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ') | $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "$PY" -c "import streamlit, cyclophaser; print('streamlit', streamlit.__version__, '| cyclophaser', cyclophaser.__file__)"
  "$PY" -m pytest -q -p no:cacheprovider -W ignore -p no:logging \
      tests/test_*apptest*.py tests/test_sidebar_defaults.py \
      tests/test_app_passo5_fixes.py tests/test_app_distance_removed.py \
      tests/test_sidebar_coverage.py 2>&1 \
    | grep -E "^(FAILED|ERROR)|^[0-9]+ (passed|failed)|passed|failed" | grep -v "^E " | tail -25
} > "$OUT" 2>&1
sed -i '' "s#$HOME#~#g" "$OUT"
cat "$OUT"
