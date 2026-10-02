#!/usr/bin/env bash
# Passo 4 — suite (-m "not browser") on THIS working tree.
#   SUITE_OUT=<file> PY=<cyclophaser env python> bash research/cleanup/passo4/run_suite.sh
# Unlike passo3/run_suite.sh the tree need not be clean: commit 16b's suite runs on
# the edited tree before it is committed; the diff of cyclophaser/ against HEAD is
# written in the header so the measured code is on record. Only passed/failed are
# predicted (CLAUDE.md). Output masked by passo4/mask.py.
set -u
cd "$(git rev-parse --show-toplevel)"
PY="${PY:-python}"
OUT=research/cleanup/passo4/${SUITE_OUT:-suite_raw.txt}
{
  echo "HEAD: $(git rev-parse HEAD)"
  echo "cyclophaser/ diff vs HEAD: $(git diff --stat HEAD -- cyclophaser/ | tail -1)"
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
"$PY" research/cleanup/passo4/mask.py "$OUT"
tail -3 "$OUT"
