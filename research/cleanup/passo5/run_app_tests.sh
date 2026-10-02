#!/usr/bin/env bash
# Passo 5, E2 — the app's tests (passo5/app_tests.txt) in one environment.
#   PY=<python of the env> OUT=<label> bash research/cleanup/passo5/run_app_tests.sh
set -u
cd "$(git rev-parse --show-toplevel)"
F=research/cleanup/passo5/$OUT.txt
{
  echo "HEAD: $(git rev-parse HEAD); working-tree changes under tools/ tests/: $(git status --porcelain -- tools tests | wc -l | tr -d ' ')"
  "$PY" -c "import streamlit, pandas, numpy, cyclophaser, sys; print('python', sys.version.split()[0], '| streamlit', streamlit.__version__, '| pandas', pandas.__version__, '| numpy', numpy.__version__); print('cyclophaser from the working tree:', cyclophaser.__file__.startswith('$PWD/'))"
  "$PY" -m pytest -m "not browser" -q -p no:cacheprovider $(cat research/cleanup/passo5/app_tests.txt) -rf
  echo "EXIT $?"
} > "$F" 2>&1
sed -i '' -E "s#$HOME#~#g; s#/private/tmp/[^ ]*/scratchpad#<scratch>#g" "$F"
tail -2 "$F"
