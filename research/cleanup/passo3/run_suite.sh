#!/usr/bin/env bash
# Passo 3 — suite after the removals (R6), on this tree at a clean HEAD.
#   PY=<cyclophaser env python> bash research/cleanup/passo3/run_suite.sh
# "Full suite" = -m "not browser" (CLAUDE.md forbids running the browser tests).
# Only passed/failed are predicted (CLAUDE.md). Output masked by passo3/mask.py.
set -u
cd "$(git rev-parse --show-toplevel)"
PY="${PY:-python}"
OUT=research/cleanup/passo3/${SUITE_OUT:-suite_raw.txt}
test -z "$(git status --porcelain -- cyclophaser tests tools research/labels/configs)" \
  || { echo "ABORT: tree not clean at HEAD"; exit 1; }
{
  echo "HEAD: $(git rev-parse HEAD)"
  "$PY" - <<'PYEOF'
import os, sys, cyclophaser
root = os.path.realpath(os.getcwd())
assert os.path.basename(sys.prefix) == "cyclophaser", sys.prefix
assert os.path.realpath(cyclophaser.__file__).startswith(root + os.sep), cyclophaser.__file__
print("assert OK: cyclophaser.__file__ =", cyclophaser.__file__, "| sys.prefix =", sys.prefix)
PYEOF
  "$PY" -m pytest -m "not browser" -q -p no:cacheprovider
  echo "EXIT $?"
} > "$OUT" 2>&1
"$PY" research/cleanup/passo3/mask.py "$OUT"
tail -3 "$OUT"
