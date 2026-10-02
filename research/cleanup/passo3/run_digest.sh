#!/usr/bin/env bash
# Passo 3, R7 — default-behaviour digest with the CANONICAL generator, before and after the removals.
#   PY=<cyclophaser env python> bash research/cleanup/passo3/run_digest.sh before   # HEAD = commit 11, clean tree
#   PY=<cyclophaser env python> bash research/cleanup/passo3/run_digest.sh after    # tree of commit 12 (removals staged)
# Same session, same working tree. The generator appends a record to its ledger;
# this script restores the ledger afterwards, since the digest is not expected to
# change (R7). Output, masked by passo2/mask.py-style substitution: passo3/digest_<mode>_raw.txt
set -eu
MODE="$1"
cd "$(git rev-parse --show-toplevel)"
PY="${PY:-python}"
OUT=research/cleanup/passo3/digest_${MODE}_raw.txt
LEDGER=research/labels/diagnostics/front_b/default_behaviour_sha256.txt
if [ "$MODE" = before ]; then
  test -z "$(git status --porcelain -- cyclophaser research tests tools docs ":(exclude)research/cleanup")" || { echo "ABORT: tree not clean"; exit 1; }
fi
{
  echo "mode: $MODE"
  echo "HEAD: $(git rev-parse HEAD)"
  echo "files staged for deletion: $(git diff --cached --name-only --diff-filter=D | wc -l | tr -d ' ')"
  "$PY" -P - <<'PYEOF'
import os, sys
sys.path.insert(0, os.getcwd())
import cyclophaser
root = os.path.realpath(os.getcwd())
assert os.path.basename(sys.prefix) == "cyclophaser", sys.prefix
assert os.path.realpath(cyclophaser.__file__).startswith(root + os.sep), cyclophaser.__file__
print("assert OK: cyclophaser.__file__ =", cyclophaser.__file__, "| sys.prefix =", sys.prefix)
PYEOF
  "$PY" -P research/labels/diagnostics/front_b/default_behaviour_hash.py
} > "$OUT" 2>&1
git checkout -- "$LEDGER"
"$PY" research/cleanup/passo3/mask.py "$OUT"
grep -E "SHA256|assert OK|REFUSING|staged" "$OUT"
