#!/usr/bin/env bash
# The conda `cyclophaser` env, `-m "not browser"`, from the repo root (the
# working tree, editable install). Records which python and cyclophaser.__file__
# before trusting the count.
#
#   conda_suite.sh <outdir> <label>
source "$(dirname "$0")/common.sh"
OUT="$1"; LABEL="$2"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
PY="$HOME/miniconda3/envs/cyclophaser/bin/python"
cd "$REPO"
unset PYTHONPATH CYCLOPHASER_REQUIRE_INSTALLED CYCLOPHASER_REQUIRE_APP_DEPS || true
export PATH="$(dirname "$PY"):$PATH"
{
  echo "which_python=$(which python)"
  echo "commit=$(git rev-parse HEAD) dirty_tracked=$(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')"
  echo "cyclophaser_file=$(python -c 'import cyclophaser; print(cyclophaser.__file__)')"
  echo "streamlit=$(python -c 'import streamlit; print(streamlit.__version__)')"
  echo "start=$(date -u +%FT%TZ)"
} > "$OUT/$LABEL.meta"
set +e
python -m pytest -m "not browser" -p no:cacheprovider --junitxml="$OUT/$LABEL.xml" -rfE > "$OUT/$LABEL.out.txt" 2>&1
echo "exit_code=$?" >> "$OUT/$LABEL.meta"
echo "end=$(date -u +%FT%TZ)" >> "$OUT/$LABEL.meta"
tail -1 "$OUT/$LABEL.out.txt"
