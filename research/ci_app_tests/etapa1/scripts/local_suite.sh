#!/usr/bin/env bash
# Local measurements of one commit (passo 1 Q2-Q5, passo 4 final check):
#   lean    venv: wheel + pytest pyyaml; `pytest -m "not source_tree"` with the
#           lock, then `python -m pytest -m source_tree` without it (both as in
#           build_test)
#   floor   venv: the app_test floor install; the app_test selection with both
#           locks, then .circleci/check_app_skips.py on the junit
#   newest  idem, newest install
# Each venv is new; suites run one after the other, never two at once.
#
#   local_suite.sh <commit> <outdir> [variants...]   (default: lean floor newest)
source "$(dirname "$0")/common.sh"
SHA="$(git -C "$REPO" rev-parse "$1")"; OUT="$2"; shift 2
VARIANTS=("${@:-lean floor newest}"); VARIANTS=(${VARIANTS[@]})
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
WHL="$("$(dirname "$0")/build_wheel.sh" "$SHA" | tail -1)"
CO="$("$(dirname "$0")/clone_at.sh" "$SHA" | tail -1)"
echo "commit=$SHA wheel=$WHL checkout=$CO" | tee "$OUT/_setup.txt"
for v in "${VARIANTS[@]}"; do
  VENV="$WORK/venv_${v}_${SHA:0:7}"
  "$(dirname "$0")/make_venv.sh" "$VENV" "$WHL" "$v" || { echo "pip failed for $v" | tee -a "$OUT/_setup.txt"; continue; }
  cp "$VENV.freeze.txt" "$OUT/$v.freeze.txt"; cp "$VENV.pip.txt" "$OUT/$v.pip.txt"
  if [ "$v" = lean ]; then
    "$(dirname "$0")/run_suite.sh" "$VENV" "$CO" "$OUT" lean_wheel "not source_tree"
    ( cd "$CO" && unset PYTHONPATH CYCLOPHASER_REQUIRE_INSTALLED CYCLOPHASER_REQUIRE_APP_DEPS
      set +e
      "$VENV/bin/python" -m pytest -m source_tree -p no:cacheprovider \
        --junitxml="$OUT/lean_source.xml" > "$OUT/lean_source.out.txt" 2>&1
      echo "exit_code=$?" > "$OUT/lean_source.meta" )
    tail -1 "$OUT/lean_source.out.txt"
  else
    CYCLOPHASER_REQUIRE_APP_DEPS=1 "$(dirname "$0")/run_suite.sh" "$VENV" "$CO" "$OUT" "$v" \
      "not browser and not source_tree"
    set +e
    "$VENV/bin/python" -I "$CO/.circleci/check_app_skips.py" "$OUT/$v.xml" > "$OUT/$v.skipcheck.txt" 2>&1
    echo "skipcheck_exit=$?" >> "$OUT/$v.skipcheck.txt"
    set -e
    tail -2 "$OUT/$v.skipcheck.txt"
  fi
done
echo done > "$OUT/_done"
