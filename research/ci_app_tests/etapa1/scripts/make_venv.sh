#!/usr/bin/env bash
# A NEW venv outside the repo with the wheel plus one dependency variant, in a
# single pip call, mirroring the CI install commands; the probe plugin is copied
# into its site-packages. Writes <venv>.pip.txt and <venv>.freeze.txt.
#
#   make_venv.sh <venv_dir> <wheel> <variant>
#
#   lean     build_test today: wheel, then `pip install pytest pyyaml`
#   floor    app_test leg floor:  wheel "streamlit==1.56.0" plotly pyyaml pytest
#   newest   app_test leg newest: wheel streamlit plotly pyyaml pytest
source "$(dirname "$0")/common.sh"
VENV="$1"; WHL="$2"; VARIANT="$3"
case "$VARIANT" in
  lean)   DEPS=(pytest pyyaml) ;;
  floor)  DEPS=("streamlit==1.56.0" plotly pyyaml pytest) ;;
  newest) DEPS=(streamlit plotly pyyaml pytest) ;;
  *) echo "unknown variant $VARIANT" >&2; exit 2 ;;
esac
rm -rf "$VENV"
"$PY312" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
set +e
"$VENV/bin/pip" install "$WHL" "${DEPS[@]}" > "$VENV.pip.txt" 2>&1
RC=$?
set -e
"$VENV/bin/pip" freeze > "$VENV.freeze.txt"
SITE="$("$VENV/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
cp "$(dirname "$0")/ci_probe.py" "$SITE/ci_probe.py"
echo "variant=$VARIANT pip_rc=$RC deps=${DEPS[*]}" > "$VENV.variant.txt"
exit $RC
