#!/usr/bin/env bash
# Build the documentation the way Read the Docs does, in a CLEAN checkout.
#
#   SCRATCH=<dir outside the repo> bash research/benchmark_review/release/build_docs_clean.sh <label> [head|worktree]
#
#   head      a detached worktree of HEAD, nothing else
#   worktree  (default) the same, plus the working tree's uncommitted changes
#             (the whole tracked diff — setup.py included — + new untracked
#             files) — how the docs under review are built before they are committed
#
# Steps, mirroring .readthedocs.yaml: a NEW python3.12 venv; pip install -r
# docs/requirements.txt; pip install . (the package from the checkout, not
# editable); sphinx-build -b html -E. Writes, next to this script:
#   docs_build_<label>_warnings.txt   every warning Sphinx printed (paths made relative)
#   docs_build_<label>.txt            HEAD, patch hash, Sphinx version, warning count
# and leaves the HTML at $SCRATCH/docs_<label>/_build/html (index.html to open).
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
LABEL="$1"; MODE="${2:-worktree}"; HERE="$ROOT/research/benchmark_review/release"
WT="$SCRATCH/docs_$LABEL"; VENV="$SCRATCH/docs_venv"
git worktree remove --force "$WT" 2>/dev/null; rm -rf "$WT"
git worktree add -q --detach "$WT" HEAD
PATCH_INFO="none"
if [ "$MODE" = worktree ]; then
  git diff --binary HEAD > "$SCRATCH/docs_$LABEL.patch"
  [ -s "$SCRATCH/docs_$LABEL.patch" ] && ( cd "$WT" && git apply --whitespace=nowarn "$SCRATCH/docs_$LABEL.patch" )
  git ls-files --others --exclude-standard -z | while IFS= read -r -d '' f; do
    mkdir -p "$WT/$(dirname "$f")"; cp "$f" "$WT/$f"; done
  PATCH_INFO="$(wc -l < "$SCRATCH/docs_$LABEL.patch" | tr -d ' ') lines, sha256 $(shasum -a 256 "$SCRATCH/docs_$LABEL.patch" | cut -c1-16)…; untracked copied: $(git ls-files --others --exclude-standard | wc -l | tr -d ' ')"
fi
if [ ! -x "$VENV/bin/python" ]; then
  /opt/homebrew/bin/python3.12 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -r "$WT/docs/requirements.txt"
fi
"$VENV/bin/pip" install -q --force-reinstall --no-deps "$WT"
( cd "$WT" && "$VENV/bin/python" -m sphinx -b html -E -q -w "$SCRATCH/docs_$LABEL.warn" docs docs/_build/html ) > "$SCRATCH/docs_$LABEL.log" 2>&1
RC=$?
sed -e "s#$WT/##g" "$SCRATCH/docs_$LABEL.warn" > "$HERE/docs_build_${LABEL}_warnings.txt"
{
  echo "label: $LABEL | mode: $MODE | HEAD $(git rev-parse --short HEAD) | patch: $PATCH_INFO | $(date -u +%FT%TZ)"
  echo "sphinx: $("$VENV/bin/python" -c 'import sphinx; print(sphinx.__version__)') | exit $RC"
  echo "warnings: $(grep -c . "$HERE/docs_build_${LABEL}_warnings.txt")"
  echo "html: \$SCRATCH/docs_$LABEL/docs/_build/html/index.html"
} > "$HERE/docs_build_$LABEL.txt"
cat "$HERE/docs_build_$LABEL.txt"
