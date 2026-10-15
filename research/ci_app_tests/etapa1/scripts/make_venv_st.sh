#!/usr/bin/env bash
# Passo 3b: a NEW venv with the wheel + one exact streamlit + plotly pyyaml
# pytest (the app_test install, streamlit pinned), probe plugin copied in.
#
#   make_venv_st.sh <venv_dir> <wheel> <streamlit_version>
source "$(dirname "$0")/common.sh"
VENV="$1"; WHL="$2"; ST="$3"
rm -rf "$VENV"
"$PY312" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install "$WHL" "streamlit==$ST" plotly pyyaml pytest > "$VENV.pip.txt" 2>&1
"$VENV/bin/pip" freeze > "$VENV.freeze.txt"
cp "$(dirname "$0")/ci_probe.py" "$("$VENV/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')/"
