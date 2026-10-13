#!/usr/bin/env bash
# Create a NEW venv outside the repo, install the wheel plus one dependency
# variant in a single pip call (so pip resolves them jointly), and install the
# probe plugin into its site-packages.
#
#   make_venv.sh <venv_dir> <wheel> <variant>
#
# Variants (the app's own requirements files: tools/calibration_app/
# requirements.txt = floors, requirements-app.txt = local pins):
#   lean        the CI recipe today: wheel + pytest + pyyaml
#   newest      wheel + streamlit plotly pyyaml pytest, nothing pinned
#   floor_st    as newest, streamlit==1.56.0                       (0.5 i)
#   floors_all  every app requirement at its requirements.txt floor (0.5 i')
#   floors_all_pd222  floors_all with pandas==2.2.2 (extra, declared up front)
#   pins_local  requirements-app.txt pins, wheel instead of `-e ../..` (0.5 iii)
source "$(dirname "$0")/common.sh"
VENV="$1"; WHL="$2"; VARIANT="$3"

case "$VARIANT" in
  lean)       DEPS=(pytest pyyaml) ;;
  newest)     DEPS=(streamlit plotly pyyaml pytest) ;;
  floor_st)   DEPS=("streamlit==1.56.0" plotly pyyaml pytest) ;;
  floors_all) DEPS=("streamlit==1.56.0" "pandas==2.2.0" "matplotlib==3.9.0"
                    "plotly==5.24.0" "xarray==2024.9.0" "numpy==2.1.0"
                    "scipy==1.14.0" "cmocean==4.0" "pyyaml==6.0" pytest) ;;
  floors_all_pd222)
              DEPS=("streamlit==1.56.0" "pandas==2.2.2" "matplotlib==3.9.0"
                    "plotly==5.24.0" "xarray==2024.9.0" "numpy==2.1.0"
                    "scipy==1.14.0" "cmocean==4.0" "pyyaml==6.0" pytest) ;;
  pins_local) DEPS=("streamlit==1.58.0" "pandas==2.3.3" "matplotlib==3.9.2"
                    "plotly==7.0.0" "xarray==2026.1.0" "numpy==2.4.0"
                    "scipy==1.17.1" "cmocean==4.0.3" "pyyaml==6.0.3" pytest) ;;
  *) echo "unknown variant $VARIANT" >&2; exit 2 ;;
esac

rm -rf "$VENV"
"$PY312" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
set +e
"$VENV/bin/pip" install "$WHL" "${DEPS[@]}" > "$VENV.pip.log" 2>&1
RC=$?
set -e
"$VENV/bin/pip" freeze > "$VENV.freeze.txt"
SITE="$("$VENV/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
cp "$(dirname "$0")/ci_probe.py" "$SITE/ci_probe.py"
echo "variant=$VARIANT pip_rc=$RC deps=${DEPS[*]}" > "$VENV.variant.txt"
exit $RC
