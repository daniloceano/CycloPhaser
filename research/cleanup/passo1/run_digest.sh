#!/usr/bin/env bash
# Passo 1 — default-behaviour digest with the CANONICAL generator, pre- and post-C1.
#
#   PY=<cyclophaser env python> bash research/cleanup/passo1/run_digest.sh pre   # worktree at f17d802
#   PY=<cyclophaser env python> bash research/cleanup/passo1/run_digest.sh post  # this tree, clean HEAD
#
# Generator: research/labels/diagnostics/front_b/default_behaviour_hash.py (unmodified).
# It asserts in-process that cyclophaser.__file__ lies inside ITS OWN tree and
# refuses otherwise; this script adds a second, explicit assert of the same fact
# plus the env name (fixed rule), before the generator runs.
#
# pre : a throw-away `git worktree` at f17d802 (the Passo 0 tip, pre-C1 code), under
#       the scratch dir given by $SCRATCH (default: a mktemp dir). Its ledger append
#       dies with the worktree.
# post: the main working tree, which must be clean at HEAD, so the record the
#       generator APPENDS to its ledger names a commit that really contains the
#       code measured. That ledger change is left in the tree on purpose (it is the
#       re-baseline record, committed afterwards).
# Output (machine paths masked by passo1/mask.py): passo1/digest_<mode>_raw.txt
set -eu
MODE="$1"
cd "$(git rev-parse --show-toplevel)"
REPO="$(pwd)"
PY="${PY:-python}"
OUT="$REPO/research/cleanup/passo1/digest_${MODE}_raw.txt"
GEN=research/labels/diagnostics/front_b/default_behaviour_hash.py

case "$MODE" in
  pre)
    REF=f17d802
    SCRATCH="${SCRATCH:-$(mktemp -d)}"
    TREE="$SCRATCH/wt_pre_c1"
    git worktree add -q --detach "$TREE" "$REF"
    trap 'git -C "$REPO" worktree remove --force "$TREE"' EXIT
    ;;
  post)
    test -z "$(git status --porcelain -- cyclophaser research/labels tests)" \
      || { echo "ABORT: tree not clean at HEAD"; exit 1; }
    TREE="$REPO"
    ;;
  *) echo "usage: $0 pre|post"; exit 2 ;;
esac

cd "$TREE"
{
  echo "mode: $MODE"
  echo "HEAD: $(git rev-parse HEAD)"
  echo "cyclophaser/ tree: $(git rev-parse HEAD:cyclophaser)"
  "$PY" -P - <<'EOF'
import os, sys
sys.path.insert(0, os.getcwd())
import cyclophaser
root = os.path.realpath(os.getcwd())
assert os.path.basename(sys.prefix) == "cyclophaser", sys.prefix
assert os.path.realpath(cyclophaser.__file__).startswith(root + os.sep), cyclophaser.__file__
print("assert OK: cyclophaser.__file__ =", cyclophaser.__file__, "| sys.prefix =", sys.prefix)
EOF
  "$PY" -P "$GEN"
} > "$OUT" 2>&1
cd "$REPO"
MASK_AS=()
[ "$TREE" != "$REPO" ] && MASK_AS=(--as "<worktree:${MODE}>=$TREE")
"$PY" research/cleanup/passo1/mask.py "$OUT" "${MASK_AS[@]+"${MASK_AS[@]}"}"
grep -E "SHA256|n_series|assert OK|REFUSING" "$OUT"
