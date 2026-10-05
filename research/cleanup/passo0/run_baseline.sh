#!/usr/bin/env bash
# Passo 0.1 — linha de base (suíte + digest canônico), mesma máquina, mesma sessão.
#
#   bash research/cleanup/passo0/run_baseline.sh
#
# Previsões declaradas ANTES da medição (do prompt da frente, não ajustadas depois):
#   suíte  -m "not browser" : 1438 passed / 0 failed
#   digest default_behaviour_hash.py : começa por 3a6de265
#
# "Suíte completa" = `-m "not browser"`: CLAUDE.md proíbe rodar
# tests/test_label_browser.py. Só passed/failed são previstos (ver CLAUDE.md).
set -u
cd "$(git rev-parse --show-toplevel)"
# The interpreter of the dedicated `cyclophaser` conda env (fixed rule). Pass it
# explicitly, e.g. PY="$(conda run -n cyclophaser which python)"; asserted below.
PY="${PY:-python}"
OUT=research/cleanup/passo0

{
  echo "HEAD: $(git rev-parse HEAD)"
  echo "python: $PY"
  "$PY" -c "import sys, cyclophaser; print('sys.executable:', sys.executable); print('cyclophaser.__file__:', cyclophaser.__file__)"
} > "$OUT/baseline_env.txt"

# Assert the dedicated env and that the import resolves to THIS working tree.
"$PY" - <<'EOF' || { echo "ABORT: wrong env or cyclophaser not from working tree"; exit 1; }
import os, sys, cyclophaser
assert os.path.basename(sys.prefix) == "cyclophaser", sys.prefix
root = os.path.realpath(os.getcwd())
assert os.path.realpath(cyclophaser.__file__).startswith(root + os.sep), cyclophaser.__file__
EOF

"$PY" -m pytest -m "not browser" -q -p no:cacheprovider > "$OUT/baseline_suite_raw.txt" 2>&1
echo "EXIT $?" >> "$OUT/baseline_suite_raw.txt"

"$PY" research/labels/diagnostics/front_b/default_behaviour_hash.py > "$OUT/baseline_digest_raw.txt" 2>&1
echo "EXIT $?" >> "$OUT/baseline_digest_raw.txt"

# The canonical generator APPENDS a record to its own ledger, a file outside
# research/cleanup/. Passo 0 edits nothing outside research/cleanup/: keep the
# appended record here, then restore the ledger to HEAD.
LEDGER=research/labels/diagnostics/front_b/default_behaviour_sha256.txt
git diff -- "$LEDGER" > "$OUT/baseline_digest_appended_record.diff"
git checkout -- "$LEDGER"

# No machine path in a versioned output (Passo 1 correction): repository root ->
# <repo>, conda env -> <env>, home -> ~. Declared in anonymize_log.json.
"$PY" research/cleanup/passo0/anonymize.py "$OUT"/baseline_env.txt "$OUT"/baseline_suite_raw.txt "$OUT"/baseline_digest_raw.txt
