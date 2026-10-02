#!/usr/bin/env bash
# Passo 5, E3 — documentation build in a CLEAN copy of the branch (git worktree at
# a given commit), never the working tree. Mirrors .readthedocs.yml: the docs venv
# (docs/requirements.txt) with the package installed from that copy.
#   DOCS_VENV=<venv> bash research/cleanup/passo5/clean_build.sh <commit> <label>
# Output: research/cleanup/passo5/<label>.txt (masked) and <label>.json (counts).
set -u
REV="$1"; LABEL="$2"
ROOT="$(git rev-parse --show-toplevel)"
WT="$(mktemp -d)/wt"
git -C "$ROOT" worktree add -q --detach "$WT" "$REV"
OUT="$ROOT/research/cleanup/passo5/$LABEL.txt"
{
  echo "worktree at: $(git -C "$WT" rev-parse HEAD) (clean: $(git -C "$WT" status --porcelain | wc -l | tr -d ' ') changed files)"
  ( cd "$WT" && "$DOCS_VENV/bin/python" -m pip install -q --force-reinstall --no-deps . ) && echo "package installed from the worktree"
  "$DOCS_VENV/bin/sphinx-build" -E -b html "$WT/docs" "$WT/docs/_build/html"
  echo "EXIT $?"
} > "$OUT" 2>&1
git -C "$ROOT" worktree remove --force "$WT"
python3 - "$OUT" "$WT" "$DOCS_VENV" <<'PY'
import json, re, sys
from pathlib import Path
out, wt, venv = sys.argv[1:4]
t = Path(out).read_text().replace(venv, "<docs-venv>").replace(str(Path(wt).parent), "<tmp-worktree>")
t = re.sub(r"/(Users|home)/[^/\s]+", r"/\1/<user>", t)
Path(out).write_text(t)
w = [l for l in t.splitlines() if "WARNING:" in l]
e = [l for l in t.splitlines() if "ERROR:" in l or "CRITICAL:" in l]
Path(out).with_suffix(".json").write_text(json.dumps(dict(warnings=len(w), errors=len(e), warning_lines=w, error_lines=e), indent=1))
print(f"{Path(out).name}: errors {len(e)}, warnings {len(w)}")
for l in w + e: print("  ", l[:200])
PY
