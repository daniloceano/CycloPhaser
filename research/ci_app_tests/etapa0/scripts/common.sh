# Shared settings for the etapa-0 scripts. Sourced, never run.
#
# WORK holds everything that must live OUTSIDE the repository: the wheel, the
# venvs and the CI-like clone the suites run in. It defaults to a folder under
# $TMPDIR; set CIAPP_WORK to override.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
STAGE="$REPO/research/ci_app_tests/etapa0"
LOGS="$STAGE/logs"
WORK="${CIAPP_WORK:-${TMPDIR:-/tmp}/ci_app_tests_etapa0}"
# CPython 3.12 like the CI image (cimg/python:3.12.3); not the conda one.
PY312="${CIAPP_PY312:-/opt/homebrew/bin/python3.12}"

case "$WORK" in "$REPO"*) echo "WORK must be outside the repo: $WORK" >&2; exit 2;; esac
mkdir -p "$WORK" "$LOGS"
