#!/usr/bin/env bash
# 0.1 — Build sdist + wheel of COMMIT in a temporary directory, the way the CI
# does (`python -m build`, wheel built from the sdist), and list the wheel.
# Never uses dist/ of the working tree (it holds a stale 2.0.0 wheel).
#
#   build_wheel.sh <commit>
# Writes: $WORK/wheel/<files>, logs/wheel_contents.txt, logs/wheel_check.json
source "$(dirname "$0")/common.sh"
COMMIT="$1"

SRC="$WORK/wheel_src"; OUT="$WORK/wheel"; TOOLS="$WORK/venv_buildtools"
rm -rf "$SRC" "$OUT"; mkdir -p "$SRC" "$OUT"
git -C "$REPO" archive "$COMMIT" | tar -x -C "$SRC"

[ -x "$TOOLS/bin/python" ] || "$PY312" -m venv "$TOOLS"
"$TOOLS/bin/pip" install -q --upgrade pip build
(cd "$SRC" && "$TOOLS/bin/python" -m build --outdir "$OUT" > "$WORK/build.log" 2>&1)

WHL="$(ls "$OUT"/*.whl)"
{
  echo "# commit $(git -C "$REPO" rev-parse "$COMMIT")"
  echo "# wheel  $(basename "$WHL")  sha256 $(shasum -a 256 "$WHL" | cut -d' ' -f1)"
  "$TOOLS/bin/python" -m zipfile -l "$WHL"
} > "$LOGS/wheel_contents.txt"

"$TOOLS/bin/python" - "$WHL" "$COMMIT" > "$LOGS/wheel_check.json" <<'EOF'
import json, sys, zipfile
whl, commit = sys.argv[1], sys.argv[2]
names = zipfile.ZipFile(whl).namelist()
tops = sorted({n.split("/")[0] for n in names})
print(json.dumps({
    "wheel": whl.rsplit("/", 1)[-1],
    "commit": commit,
    "n_files": len(names),
    "top_level": tops,
    "has_tools": any(n.startswith("tools/") for n in names),
    "has_research": any(n.startswith("research/") for n in names),
    "has_tests": any(n.startswith("tests/") for n in names),
}, indent=2))
EOF
cat "$LOGS/wheel_check.json"
echo "$WHL"
