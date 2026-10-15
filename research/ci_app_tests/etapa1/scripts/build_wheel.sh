#!/usr/bin/env bash
# Build sdist + wheel of COMMIT the way the CI does (`python -m build` in the
# checkout), in a temporary clean clone, never from dist/ of the working tree.
# Prints the wheel's path; records its name and sha256 in logs/.
#
#   build_wheel.sh <commit>
source "$(dirname "$0")/common.sh"
SHA="$(git -C "$REPO" rev-parse "$1")"
SRC="$WORK/wheel_src_${SHA:0:7}"; OUT="$WORK/wheel_${SHA:0:7}"; TOOLS="$WORK/venv_buildtools"
rm -rf "$SRC" "$OUT"; mkdir -p "$SRC" "$OUT"
git -C "$REPO" archive "$SHA" | tar -x -C "$SRC"
[ -x "$TOOLS/bin/python" ] || "$PY312" -m venv "$TOOLS"
"$TOOLS/bin/pip" install -q --upgrade pip build
(cd "$SRC" && "$TOOLS/bin/python" -m build --outdir "$OUT" > "$WORK/build_${SHA:0:7}.txt" 2>&1)
WHL="$(ls "$OUT"/*.whl)"
echo "commit $SHA wheel $(basename "$WHL") sha256 $(shasum -a 256 "$WHL" | cut -d' ' -f1)" \
  > "$LOGS/wheel_${SHA:0:7}.txt"
echo "$WHL"
