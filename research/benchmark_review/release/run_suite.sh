#!/usr/bin/env bash
# I3 gate (c): the whole suite except the browser tests, under one Python, which
# decides the streamlit version.
#   bash research/benchmark_review/release/run_suite.sh <python> <label>
# Writes research/benchmark_review/release/suite_<label>.txt: `which python`, the
# interpreter, streamlit, cyclophaser.__file__ (asserted inside the repo), then
# pytest's failures and final count line.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
PY="$1"; OUT="$ROOT/research/benchmark_review/release/suite_$2.txt"
{
  echo "which python: $(which python) | interpreter used: $PY ($("$PY" --version 2>&1)) | HEAD $(git rev-parse --short HEAD) | tracked changes: $(git status --porcelain --untracked-files=no | wc -l | tr -d ' ') | $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "$PY" -c "import streamlit, cyclophaser, pathlib; f = pathlib.Path(cyclophaser.__file__).resolve(); assert f.is_relative_to(pathlib.Path('$ROOT').resolve()), f; print('streamlit', streamlit.__version__, '| cyclophaser', f)"
  "$PY" -m pytest -q -p no:cacheprovider -W ignore -p no:logging -m "not browser" 2>&1 \
    | grep -E "^(FAILED|ERROR)|^E  |passed|failed" | tail -80
} > "$OUT" 2>&1
sed -i '' "s#$HOME#~#g" "$OUT"
cat "$OUT"
