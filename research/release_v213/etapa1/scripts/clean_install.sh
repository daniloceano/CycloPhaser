#!/usr/bin/env bash
# Clean installs for criteria (b) and (c) of release 2.1.3.
#
#   clean_install.sh <case> <artifact> <workdir> <log>
#
# case: B1 | B2 | B3 | SDIST
#   B1    pip picks the newest dependencies
#   B2    uv --resolution lowest-direct --only-binary :all: with the 6 floors
#   B3    cmocean==4.0.1 installed first, then the artifact (pip must upgrade it)
#   SDIST install from the sdist (pip builds it)
# artifact: a local path, or `testpypi:2.1.3` / `pypi:2.1.3` (stages 2/3).
#   testpypi: the package from TestPyPI with --no-deps, its dependencies from PyPI.
#
# Each case is a NEW venv from /opt/homebrew/bin/python3.12, the CWD is <workdir>
# (outside the repository), every python call is `python -I`, and smoke.py
# (etapa 0) asserts cyclophaser.__file__ is in that venv's site-packages.
set -uo pipefail
CASE=$1; ART=$2; WORK=$3; LOG=$4
HERE=$(cd "$(dirname "$0")" && pwd)
SMOKE="$HERE/../../etapa0/scripts/smoke.py"
PY312=/opt/homebrew/bin/python3.12
FLOORS=("cmocean>=4.0.3" "matplotlib>=3.9" "numpy>=2.1" "pandas>=2.2.2" "scipy>=1.14" "xarray>=2024.9")

mkdir -p "$WORK"; cd "$WORK" || exit 1
V="$WORK/venv_$CASE"; rm -rf "$V"
{
echo "# case $CASE  artifact $ART  $(date '+%Y-%m-%d %H:%M:%S')"
echo "# platform: $(uname -srm); cwd: $(pwd)"
"$PY312" -I -m venv "$V"
P="$V/bin/python"
echo "# python: $("$P" -I -c 'import sys;print(sys.version.split()[0], sys.prefix)')"
"$P" -I -m pip install -q --upgrade pip

case "$ART" in
  testpypi:*) SPEC=(--index-url https://test.pypi.org/simple/ --no-deps "cyclophaser==${ART#testpypi:}") ;;
  pypi:*)     SPEC=("cyclophaser==${ART#pypi:}") ;;
  *)          SPEC=("$ART") ;;
esac

if [ "$CASE" = "B3" ]; then
  echo "## pre-install cmocean==4.0.1"
  "$P" -I -m pip install "cmocean==4.0.1" 2>&1 | tail -3
  "$P" -I -m pip show cmocean | grep -E '^(Name|Version)'
fi

if [ "$CASE" = "B2" ]; then
  # uv from a separate tools venv; it installs into $V.
  UVV="$WORK/uv_tools"; [ -x "$UVV/bin/uv" ] || { "$PY312" -I -m venv "$UVV"; "$UVV/bin/python" -I -m pip install -q uv; }
  echo "## uv $("$UVV/bin/uv" --version)"
  if [[ "$ART" == testpypi:* ]]; then
    "$UVV/bin/uv" pip install --python "$P" --index-url https://test.pypi.org/simple/ --no-deps "${SPEC[@]:3}" 2>&1
    "$UVV/bin/uv" pip install --python "$P" --resolution lowest-direct --only-binary :all: "${FLOORS[@]}" 2>&1
  else
    "$UVV/bin/uv" pip install --python "$P" --resolution lowest-direct --only-binary :all: "${FLOORS[@]}" "${SPEC[@]}" 2>&1
  fi
elif [[ "$ART" == testpypi:* ]]; then
  "$P" -I -m pip install "${SPEC[@]}" 2>&1 | tail -3
  # the dependencies, from PyPI only, as declared by the installed metadata
  DEPS=$("$P" -I -c "from importlib.metadata import requires; print('\n'.join(r for r in requires('cyclophaser') if 'extra ==' not in r))")
  echo "## deps from PyPI: $DEPS"
  "$P" -I -m pip install $DEPS 2>&1 | grep -E "Successfully|already satisfied: cmocean|ERROR"
else
  "$P" -I -m pip install "${SPEC[@]}" 2>&1 | grep -E "Successfully|Requirement already satisfied: cmocean|Attempting uninstall|Found existing|ERROR"
fi
echo "## pip freeze"
"$P" -I -m pip freeze
echo "## pip check"
"$P" -I -m pip check
echo "## smoke"
"$P" -I "$SMOKE"
echo "smoke_exit=$?"
} > "$LOG" 2>&1
tail -12 "$LOG"
