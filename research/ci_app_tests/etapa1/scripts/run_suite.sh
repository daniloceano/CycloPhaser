#!/usr/bin/env bash
# One run of the suite, CI style: bare `pytest` from the root of a clean clone,
# --import-mode=append, installed-package lock ON, PYTHONPATH unset. Extra
# environment (e.g. CYCLOPHASER_REQUIRE_APP_DEPS=1) is passed through from the
# caller. Records which python, junit XML, the pytest output, exit code, wall time.
#
#   run_suite.sh <venv> <checkout> <outdir> <label> <marker-expr> [extra pytest args...]
source "$(dirname "$0")/common.sh"
VENV="$1"; CHECKOUT="$2"; OUTDIR="$3"; LABEL="$4"; MARK="$5"
shift 5
mkdir -p "$OUTDIR"
cd "$CHECKOUT"
export PATH="$VENV/bin:$PATH"
unset PYTHONPATH PYTHONHOME VIRTUAL_ENV CONDA_PREFIX || true
{
  echo "label=$LABEL"
  echo "which_python=$(which python)"
  echo "which_pytest=$(which pytest)"
  echo "commit=$(git -C "$CHECKOUT" rev-parse HEAD)"
  echo "marker=$MARK"
  echo "CYCLOPHASER_REQUIRE_APP_DEPS=${CYCLOPHASER_REQUIRE_APP_DEPS:-<unset>}"
  echo "start=$(date -u +%FT%TZ)"
} > "$OUTDIR/$LABEL.meta"
T0=$(python -c 'import time; print(time.time())')
set +e
CYCLOPHASER_REQUIRE_INSTALLED=1 CIPROBE_OUT="$OUTDIR/$LABEL.probe.json" \
  pytest --import-mode=append -m "$MARK" -p ci_probe -p no:cacheprovider \
         --junitxml="$OUTDIR/$LABEL.xml" -rfEs "$@" > "$OUTDIR/$LABEL.out.txt" 2>&1
RC=$?
set -e
T1=$(python -c 'import time; print(time.time())')
{
  echo "exit_code=$RC"
  echo "wall_s=$(python -c "print(round($T1-$T0,1))")"
  echo "end=$(date -u +%FT%TZ)"
  echo "git_status_after=$(git -C "$CHECKOUT" status --porcelain | wc -l | tr -d ' ')"
} >> "$OUTDIR/$LABEL.meta"
grep -E "cyclophaser.__file__|CYCLOPHASER_REQUIRE" "$OUTDIR/$LABEL.out.txt" >> "$OUTDIR/$LABEL.meta" || true
tail -1 "$OUTDIR/$LABEL.out.txt"
exit 0
